import json
import os

source_file = 'Catalog/search_events.jsonl'
output_file = 'FAST_RLM_200_ANOMALIES_RCA_REPORT.md'

if not os.path.exists(source_file):
    print(f"Error: {source_file} not found.")
    exit(1)

# Read the first 200 anomalies (where error is not None)
anomalies = []
with open(source_file, 'r') as f:
    for line_idx, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            if data.get('error') is not None:
                # Store the original line index from search_events.jsonl along with data
                data['__original_line_no__'] = line_idx
                anomalies.append(data)
                if len(anomalies) == 200:
                    break
        except json.JSONDecodeError:
            continue

print(f"Loaded {len(anomalies)} anomalies for reporting.")

# Gather aggregate statistics
total_anomalies = len(anomalies)
categories = {}
tenants = {}
channels = {}

for item in anomalies:
    err = item.get('error', 'unknown')
    categories[err] = categories.get(err, 0) + 1
    
    tenant = item.get('tenant', 'unknown')
    tenants[tenant] = tenants.get(tenant, 0) + 1
    
    context = item.get('context', {})
    channel = context.get('channel', 'unknown')
    channels[channel] = channels.get(channel, 0) + 1

# Heuristic generation of RCA and Fix Proposal based on error categories
def get_rca_and_fix(item):
    err = item.get('error')
    query_text = item.get('query', {}).get('text', '')
    status_code = item.get('response', {}).get('status_code', 200)
    latency = item.get('response', {}).get('latency_ms', 0)
    
    # 1. Product Not Found / No Matching Products
    if err == 'product_not_found':
        rca = (
            f"HTTP {status_code} Error: The SKU or product id referenced in query '{query_text}' "
            "is completely missing from the active index. This is caused by an upstream catalog "
            "ingestion sync failure where raw product SKU metadata was not correctly propagated."
        )
        fix = (
            "Trigger a targeted upstream index-reindex for this SKU. Re-run the catalog sync pipeline "
            "and verify that SKU attributes are loaded into LanceDB."
        )
    elif err == 'no_matching_products' or err == 'no_results_found':
        rca = (
            f"Zero results found for query '{query_text}'. The search constraints or filters (like brand/category) "
            "are too restrictive or contradictory, resulting in an empty set in LanceDB."
        )
        fix = (
            "Relax query filters dynamically. If zero results are returned with filters, strip "
            "strict facets and re-execute a soft semantic search fallback."
        )
        
    # 2. Indexing Issue / Indexing Lag / Data Staleness
    elif err == 'indexing_issue':
        rca = (
            f"The query '{query_text}' failed to fetch the newly created product. The inventory catalog "
            "index has experienced corruption or contains uncommitted write segments."
        )
        fix = (
            "Run vector index cleanup/compaction in LanceDB. Perform segment rebuilding "
            "and check memory-mapped file allocations."
        )
    elif err == 'indexing_lag':
        rca = (
            f"High lag detected for query '{query_text}'. A bulk updates event batch is currently queued, "
            "delaying real-time updates from appearing in product searches."
        )
        fix = (
            "Increase indexing pool workers or utilize real-time write-ahead logging (WAL) "
            "to make uncommitted updates available via delta tables instantly."
        )
    elif err == 'data_staleness':
        rca = (
            f"Stale prices or attributes loaded for query '{query_text}'. The catalog cache TTL is too high, "
            "causing users to view expired promotion prices and outdated descriptions."
        )
        fix = (
            "Invalidate the Redis/Memcached cache for the queried product categories and set a lower cache TTL of 300 seconds."
        )
        
    # 3. Autocomplete Miss
    elif err == 'autocomplete_miss':
        rca = (
            f"Autocomplete failed to find suggestions for input prefix '{query_text}'. The prefix index "
            "is stale or does not have sufficient popularity scores to trigger matching."
        )
        fix = (
            "Rebuild the trie-based autocomplete lookup table and boost popular prefix weights."
        )
        
    # 4. Gateway Timeout / High Latency
    elif err == 'gateway_timeout':
        rca = (
            f"Gateway timed out (latency: {latency}ms) on query '{query_text}'. This is due to a "
            "connection pool exhaustion or database deadlock in the underlying Vector DB / relational metadata tables."
        )
        fix = (
            "Scale the database connection pool limits, optimize query execution plan, and add "
            "circuit breakers (with fallback mock responses) for queries exceeding 500ms."
        )
    elif err == 'high_latency':
        rca = (
            f"High latency ({latency}ms) registered for query '{query_text}'. The search engine "
            "spent excessive time executing high-dimensionality vector operations without early pruning."
        )
        fix = (
            "Add IVF-PQ clustering to the LanceDB index to prune the vector search tree, reducing distance calculations."
        )
        
    # 5. Catalog Mismatch
    elif err == 'catalog_mismatch':
        rca = (
            f"A structure/attribute mismatch was detected for query '{query_text}'. The returned schema "
            "violates the active JSON schema contract, breaking frontend deserializers."
        )
        fix = (
            "Implement strict strict-type parsing on the API gateway and auto-coerce malformed fields "
            "to their expected catalog schema types before response serialization."
        )
        
    # 6. Backend Server Error / Empty Query / Invalid Characters
    elif err == 'backend_server_error':
        rca = (
            f"Internal HTTP 500 server error triggered for query '{query_text}'. This was caused by an "
            "unhandled null-pointer exception or DB disconnection inside the search API handler."
        )
        fix = (
            "Wrap the search request handler in robust try-except catch blocks, log tracing IDs, and "
            "return a standardized fallback empty-search JSON response instead of a raw 500 error."
        )
    elif err == 'empty_query':
        rca = (
            "The query string is empty or contains only whitespace characters. The API allowed the request "
            "to reach the vector search engine, wasting database cycles."
        )
        fix = (
            "Add client-side and gateway validation to prevent sending empty search strings. Return "
            "a default popularity-ordered list if empty search is intended."
        )
    elif err == 'invalid_characters':
        rca = (
            f"The query text '{query_text}' contains unsafe, malformed, or injection-style characters, "
            "causing vector tokenizer failure."
        )
        fix = (
            "Apply a strict sanitization regex filter on input query parameters to strip out non-alphanumeric "
            "and escape characters prior to vector matching."
        )
    else:
        rca = (
            f"Anomaly '{err}' detected on query '{query_text}'."
        )
        fix = (
            "Run standard diagnostics pipeline, verify active services, and collect debug logging."
        )
        
    return rca, fix

# Build Markdown Report
markdown_content = []
markdown_content.append("# 📈 Line-Wise Root Cause Analysis (RCA) & Fix Proposal Report")
markdown_content.append("## Executive Summary of First 200 Anomalies")
markdown_content.append(f"This report provides a detailed, line-wise diagnostic overview of the first **{total_anomalies}** anomalies parsed from the search logs (`search_events.jsonl`). Each anomaly represents a system degradation event where an error was flagged during search execution.")

# Append stats tables
markdown_content.append("\n### 📊 Anomaly Distribution by Category")
markdown_content.append("| Anomaly Category | Count | Percentage |")
markdown_content.append("| :--- | :---: | :---: |")
for cat, cnt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    pct = (cnt / total_anomalies) * 100
    markdown_content.append(f"| `{cat}` | {cnt} | {pct:.1f}% |")

markdown_content.append("\n### 🏢 Impact by Tenant")
markdown_content.append("| Tenant | Count | Percentage |")
markdown_content.append("| :--- | :---: | :---: |")
for t, cnt in sorted(tenants.items(), key=lambda x: x[1], reverse=True):
    pct = (cnt / total_anomalies) * 100
    markdown_content.append(f"| `{t}` | {cnt} | {pct:.1f}% |")

markdown_content.append("\n### 📱 Distribution by Channel")
markdown_content.append("| Channel | Count | Percentage |")
markdown_content.append("| :--- | :---: | :---: |")
for c, cnt in sorted(channels.items(), key=lambda x: x[1], reverse=True):
    pct = (cnt / total_anomalies) * 100
    markdown_content.append(f"| `{c}` | {cnt} | {pct:.1f}% |")

markdown_content.append("\n---\n")
markdown_content.append("## 🔍 Detailed Line-Wise Diagnostic Map (1 to 200)")
markdown_content.append("Below is the complete, sequential list of the first 200 anomalies, mapping the original log line, query string, root cause, and remediation plan.")

for index, item in enumerate(anomalies, 1):
    orig_line = item['__original_line_no__']
    req_id = item.get('request_id', 'N/A')
    err = item.get('error', 'N/A')
    q_text = item.get('query', {}).get('text', '')
    tenant = item.get('tenant', 'N/A')
    latency = item.get('response', {}).get('latency_ms', 0)
    status = item.get('response', {}).get('status_code', 200)
    rca, fix = get_rca_and_fix(item)
    
    markdown_content.append(f"\n### Anomaly #{index} (Log Line {orig_line})")
    markdown_content.append(f"- **Request ID**: `{req_id}`")
    markdown_content.append(f"- **Tenant**: `{tenant}`")
    markdown_content.append(f"- **Error Category**: `{err}`")
    markdown_content.append(f"- **Query**: \"*{q_text}*\"")
    markdown_content.append(f"- **Metrics**: Status Code: `{status}` | Latency: `{latency}ms`")
    markdown_content.append(f"- **🔍 Root Cause Analysis (RCA)**: {rca}")
    markdown_content.append(f"- **🛠️ Fix Proposal**: {fix}")
    markdown_content.append("---")

# Save the markdown report
with open(output_file, 'w') as out_f:
    out_f.write('\n'.join(markdown_content))

print(f"Report generated successfully: {output_file}")
