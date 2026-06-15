#!/usr/bin/env python3
"""Generate and validate Magellan mock data fixtures."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FIXTURE_TIMESTAMP = "2026-06-06T00:00:00Z"
LOG_BASE_TIME = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)

CATEGORY_CONFIGS: dict[str, dict[str, Any]] = {
    "footwear": {
        "count": 300,
        "prefix": "FOOT",
        "description": "Mock footwear catalog data for catalog delta and search simulations.",
        "attributes": {
            "waterproof": [True, False],
            "terrain": ["trail", "road", "casual", "gym"],
            "material": ["leather", "mesh", "synthetic", "canvas"],
            "size_range": ["5-11", "6-12", "6-13", "7-14"],
        },
        "primary_attribute": "size_range",
        "brands": ["TrailForge", "StrideLab", "NorthPeak", "Runway Athletics", "AeroStep", "SummitSole"],
        "title_parts": [
            ("Waterproof Trail Runner", "trail shoe built for wet routes and uneven ground"),
            ("Road Tempo Sneaker", "breathable road trainer with a stable ride"),
            ("Casual Canvas Low Top", "everyday canvas sneaker with clean styling"),
            ("Gym Flex Trainer", "supportive gym shoe for lifting and conditioning"),
            ("Leather Approach Shoe", "durable leather shoe for travel and light trails"),
            ("Mesh Distance Runner", "lightweight mesh runner for long training days"),
        ],
        "price": (69, 219),
    },
    "bags": {
        "count": 200,
        "prefix": "BAGS",
        "description": "Mock bag catalog data for laptop, travel, and outdoor search simulations.",
        "attributes": {
            "capacity_liters": [18, 22, 28, 34, 45, 60],
            "laptop_size": ["13inch", "15inch", "17inch"],
            "material": ["nylon", "canvas", "polyester", "leather", "ripstop"],
            "waterproof": [True, False],
        },
        "primary_attribute": "capacity_liters",
        "brands": ["Packsmith", "UrbanCarry", "RidgeLine", "Nomad Works", "HarborPack", "MetroTrek"],
        "title_parts": [
            ("Commuter Laptop Backpack", "organized backpack for work gear and daily carry"),
            ("Canvas Messenger Bag", "structured messenger bag with quick-access storage"),
            ("Waterproof Travel Duffel", "weather-ready duffel for weekend trips"),
            ("Rolltop City Pack", "expandable rolltop pack for mixed commute loads"),
            ("Trail Hydration Pack", "compact pack shaped for fast outdoor movement"),
            ("Executive Leather Brief", "polished brief with protected laptop storage"),
        ],
        "price": (49, 249),
    },
    "outerwear": {
        "count": 200,
        "prefix": "OUT",
        "description": "Mock outerwear catalog data for jackets, shells, and insulated layers.",
        "attributes": {
            "waterproof": [True, False],
            "material": ["gore-tex", "nylon", "polyester", "down"],
            "size_range": ["XS-XL", "S-XXL", "M-XXL", "XS-3XL"],
            "weight_grams": [240, 310, 420, 560, 780, 920],
        },
        "primary_attribute": "size_range",
        "brands": ["StormVale", "Alpine Thread", "CloudShell", "Northline", "CairnWear", "DriftLayer"],
        "title_parts": [
            ("Gore-Tex Rain Jacket", "technical shell for persistent rain and windy commutes"),
            ("Packable Wind Shell", "lightweight layer that compresses for travel"),
            ("Down Alpine Parka", "warm insulated parka for cold-weather coverage"),
            ("Waterproof Field Jacket", "durable field jacket with sealed weather protection"),
            ("Softshell Trek Hoodie", "stretch softshell for active cool-weather use"),
            ("Urban Insulated Coat", "streamlined insulated coat for everyday winter wear"),
        ],
        "price": (89, 399),
    },
    "electronics": {
        "count": 150,
        "prefix": "ELEC",
        "description": "Mock electronics catalog data for wearables, audio, and portable devices.",
        "attributes": {
            "battery_hours": [8, 12, 18, 24, 36, 72],
            "waterproof": [True, False],
            "display": ["AMOLED", "LCD", "OLED"],
            "gps": [True, False],
        },
        "primary_attribute": "battery_hours",
        "brands": ["PulseBit", "Auralink", "OrbitIQ", "VoltEdge", "SignalPeak", "NimbleTech"],
        "title_parts": [
            ("GPS Fitness Smartwatch", "wearable tracker with route logging and health metrics"),
            ("Waterproof Bluetooth Speaker", "portable speaker tuned for outdoor use"),
            ("OLED Action Camera", "compact camera for travel and trail footage"),
            ("AMOLED Sport Band", "slim fitness band with a bright display"),
            ("Noise Cancelling Earbuds", "wireless earbuds with long battery life"),
            ("Rugged Handheld GPS", "navigation device for hiking and remote trips"),
        ],
        "price": (79, 599),
    },
    "camping": {
        "count": 150,
        "prefix": "CAMP",
        "description": "Mock camping catalog data for sleeping bags, pads, and weather-ready gear.",
        "attributes": {
            "temp_rating_c": [-18, -10, -5, 0, 5, 10],
            "fill_weight_g": [350, 500, 650, 800, 950, 1200],
            "material": ["down", "synthetic"],
            "waterproof": [True, False],
        },
        "primary_attribute": "temp_rating_c",
        "brands": ["BaseCamp Co", "SummitNest", "TrailHaven", "EmberRest", "CanyonLite", "WildPitch"],
        "title_parts": [
            ("Down Mummy Sleeping Bag", "efficient sleeping bag for cold nights on trail"),
            ("Synthetic Camp Quilt", "versatile quilt for damp shoulder-season trips"),
            ("Waterproof Bivy Sack", "minimal shelter layer for fast overnight travel"),
            ("Expedition Sleep System", "warm sleep system for alpine base camps"),
            ("Ultralight Summer Bag", "compact bag for warm-weather backpacking"),
            ("Insulated Camp Blanket", "soft insulated blanket for car camping"),
        ],
        "price": (59, 349),
    },
}

QUALITY_COUNTS = {
    "complete": 0.40,
    "incomplete": 0.30,
    "poor": 0.20,
    "new_arrival": 0.10,
}

OOS_COUNTS = {
    "footwear": 24,
    "bags": 16,
    "outerwear": 16,
    "electronics": 12,
    "camping": 12,
}

LOW_STOCK_COUNTS = {
    "footwear": 32,
    "bags": 22,
    "outerwear": 22,
    "electronics": 13,
    "camping": 13,
}

CATALOG_SCENARIOS = [
    ("Insert incomplete footwear arrival", "INSERT", "FOOT-271", "products/footwear.json", None),
    ("Insert incomplete bag arrival", "INSERT", "BAGS-181", "products/bags.json", None),
    ("Insert incomplete outerwear arrival", "INSERT", "OUT-181", "products/outerwear.json", None),
    ("Insert incomplete electronics arrival", "INSERT", "ELEC-136", "products/electronics.json", None),
    ("Insert incomplete camping arrival", "INSERT", "CAMP-136", "products/camping.json", None),
    (
        "Update footwear title for embedding refresh",
        "UPDATE",
        "FOOT-001",
        "products/footwear.json",
        {"title": {"before": "Waterproof Trail Runner 001", "after": "Waterproof Trail Runner Pro 001"}},
    ),
    (
        "Update bag description for embedding refresh",
        "UPDATE",
        "BAGS-001",
        "products/bags.json",
        {"description": {"before": "original generated description", "after": "expanded product copy for hybrid commute search"}},
    ),
    (
        "Update outerwear title for embedding refresh",
        "UPDATE",
        "OUT-001",
        "products/outerwear.json",
        {"title": {"before": "Gore-Tex Rain Jacket 001", "after": "Gore-Tex Rain Jacket Storm 001"}},
    ),
    (
        "Update electronics description for embedding refresh",
        "UPDATE",
        "ELEC-001",
        "products/electronics.json",
        {"description": {"before": "original generated description", "after": "updated copy emphasizing GPS battery performance"}},
    ),
    (
        "Null footwear waterproof attribute",
        "UPDATE",
        "FOOT-002",
        "products/footwear.json",
        {"attributes.waterproof": {"before": True, "after": None}},
    ),
    (
        "Null footwear terrain attribute",
        "UPDATE",
        "FOOT-003",
        "products/footwear.json",
        {"attributes.terrain": {"before": "trail", "after": None}},
    ),
    (
        "Null outerwear waterproof attribute",
        "UPDATE",
        "OUT-002",
        "products/outerwear.json",
        {"attributes.waterproof": {"before": True, "after": None}},
    ),
    (
        "Null electronics gps attribute",
        "UPDATE",
        "ELEC-002",
        "products/electronics.json",
        {"attributes.gps": {"before": True, "after": None}},
    ),
    ("Update footwear sale price", "UPDATE", "FOOT-004", "products/footwear.json", {"price": {"before": 129, "after": 119}}),
    ("Update bag stock count", "UPDATE", "BAGS-004", "products/bags.json", {"stock": {"before": 88, "after": 64}}),
    ("Update outerwear markdown price", "UPDATE", "OUT-004", "products/outerwear.json", {"price": {"before": 249, "after": 229}}),
    ("Update camping stock count", "UPDATE", "CAMP-004", "products/camping.json", {"stock": {"before": 74, "after": 58}}),
    ("Delete poor quality footwear product", "DELETE", "FOOT-211", "products/footwear.json", None),
    ("Delete OOS electronics product", "DELETE", "ELEC-061", "products/electronics.json", None),
    ("Delete poor quality camping product", "DELETE", "CAMP-106", "products/camping.json", None),
]


def quality_for_index(index: int, count: int) -> str:
    complete = int(count * QUALITY_COUNTS["complete"])
    incomplete = int(count * QUALITY_COUNTS["incomplete"])
    poor = int(count * QUALITY_COUNTS["poor"])
    if index <= complete:
        return "complete"
    if index <= complete + incomplete:
        return "incomplete"
    if index <= complete + incomplete + poor:
        return "poor"
    return "new_arrival"


def attr_value(values: list[Any], index: int, offset: int) -> Any:
    return values[(index + offset) % len(values)]


def complete_attributes(category: str, index: int) -> dict[str, Any]:
    attrs = {}
    for offset, (name, values) in enumerate(CATEGORY_CONFIGS[category]["attributes"].items()):
        attrs[name] = attr_value(values, index, offset)
    return attrs


def stock_for(category: str, index: int) -> int:
    count = CATEGORY_CONFIGS[category]["count"]
    quality = quality_for_index(index, count)
    complete_count = int(count * QUALITY_COUNTS["complete"])
    if quality == "complete":
        return 10 + ((index * 13) % 191)
    if quality == "incomplete":
        local_index = index - complete_count
        if local_index <= OOS_COUNTS[category]:
            return 0
        if local_index <= OOS_COUNTS[category] + LOW_STOCK_COUNTS[category]:
            return 1 + ((local_index - OOS_COUNTS[category] - 1) % 10)
        return 11 + ((index * 7) % 90)
    if quality == "poor":
        return 5 + ((index * 5) % 46)
    return 20 + ((index * 9) % 81)


def price_for(category: str, index: int) -> float:
    low, high = CATEGORY_CONFIGS[category]["price"]
    return round(low + ((index * 17) % (high - low + 1)) + ((index % 4) * 0.25), 2)


def build_product(category: str, index: int) -> dict[str, Any]:
    config = CATEGORY_CONFIGS[category]
    product_id = f"{config['prefix']}-{index:03d}"
    quality = quality_for_index(index, config["count"])
    title_base, description_base = config["title_parts"][(index - 1) % len(config["title_parts"])]
    category_label = category
    attrs = complete_attributes(category, index)

    if quality == "complete":
        title = f"{title_base} {index:03d}"
        description = f"{title} is a {description_base}. It is tuned for realistic Magellan search relevance and merchandising tests."
        brand = config["brands"][(index - 1) % len(config["brands"])]
    elif quality == "incomplete":
        title = f"{title_base} Lite {index:03d}"
        description = f"{title} keeps the core catalog copy but intentionally omits several structured attributes for warning-path tests."
        brand = config["brands"][(index + 1) % len(config["brands"])]
        for name in list(attrs)[:2]:
            attrs[name] = None
        if index % 3 == 0:
            attrs[list(attrs)[2]] = None
    elif quality == "poor":
        title = f"Product {product_id}"
        description = f"{category.title()} item"
        brand = None
        attrs = {name: None for name in config["attributes"]}
    else:
        title = f"New {title_base} {index:03d}"
        description = f"{title} is a fresh catalog arrival awaiting full attribute enrichment."
        brand = config["brands"][(index + 2) % len(config["brands"])]
        primary = config["primary_attribute"]
        attrs = {
            name: (complete_attributes(category, index)[name] if name == primary else None)
            for name in config["attributes"]
        }

    return {
        "id": product_id,
        "title": title,
        "description": description,
        "category": category_label,
        "brand": brand,
        "price": price_for(category, index),
        "stock": stock_for(category, index),
        "attributes": attrs,
        "data_quality": quality,
    }


def build_products() -> dict[str, dict[str, Any]]:
    files = {}
    for category, config in CATEGORY_CONFIGS.items():
        products = [build_product(category, index) for index in range(1, config["count"] + 1)]
        files[category] = {
            "category": category,
            "description": config["description"],
            "products": products,
        }
    return files


def product_map(product_files: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        product["id"]: product
        for category_file in product_files.values()
        for product in category_file["products"]
    }


def build_rules(products_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    boost_targets = [
        ["FOOT-121", "ELEC-061"],
        ["FOOT-122", "BAGS-081"],
        ["OUT-081", "CAMP-061"],
        ["ELEC-062", "FOOT-123"],
        ["BAGS-050", "OUT-050"],
        ["CAMP-050", "FOOT-050"],
        ["ELEC-061", "OUT-080"],
        ["BAGS-080", "CAMP-080"],
    ]
    campaigns = [
        "Summer Trail Sale",
        "Back To Campus",
        "Storm Ready",
        "Outdoor Tech Week",
        "Travel Essentials",
        "Basecamp Bundle",
        "Wearable Refresh",
        "Weekend Carry Event",
    ]
    rules = []
    for index, targets in enumerate(boost_targets, start=1):
        rules.append(
            {
                "rule_id": f"MXP-{index:03d}",
                "rule_type": "boost",
                "target_products": targets,
                "boost_factor": round(1.2 + index * 0.13, 2),
                "campaign": campaigns[index - 1],
                "active": False if index in {7, 8} else True,
                "created_by": f"merchandiser_{['alice', 'ben', 'chandra', 'diego'][index % 4]}",
                "created_at": FIXTURE_TIMESTAMP,
            }
        )

    suppress_targets = [
        ["FOOT-100", "BAGS-070"],
        ["OUT-070"],
        ["ELEC-050"],
        ["CAMP-050"],
        ["FOOT-210"],
        ["BAGS-145"],
    ]
    reasons = ["low margin", "supplier hold", "quality review", "seasonal delist", "duplicate listing", "image compliance"]
    for offset, targets in enumerate(suppress_targets, start=9):
        rules.append(
            {
                "rule_id": f"MXP-{offset:03d}",
                "rule_type": "suppress",
                "target_products": targets,
                "reason": reasons[offset - 9],
                "active": False if offset == 14 else True,
                "created_by": f"merchandiser_{['alice', 'ben', 'chandra', 'diego'][offset % 4]}",
                "created_at": FIXTURE_TIMESTAMP,
            }
        )

    synonym_sets = [
        (["rain shell", "waterproof jacket"], "rain jacket"),
        (["daypack", "rucksack"], "backpack"),
        (["trainers", "sneakers"], "shoes"),
        (["fitness watch", "activity tracker"], "smartwatch"),
        (["sleeping sack", "camp bag"], "sleeping bag"),
        (["gore tex", "gtx"], "gore-tex"),
    ]
    for offset, (terms, canonical) in enumerate(synonym_sets, start=15):
        rules.append(
            {
                "rule_id": f"MXP-{offset:03d}",
                "rule_type": "synonym",
                "target_products": [],
                "terms": terms,
                "canonical": canonical,
                "active": True,
                "created_by": f"merchandiser_{['alice', 'ben', 'chandra', 'diego'][offset % 4]}",
                "created_at": FIXTURE_TIMESTAMP,
            }
        )

    for rule in rules:
        for product_id in rule["target_products"]:
            if product_id in products_by_id:
                product = products_by_id[product_id]
                rule.setdefault("target_product_snapshots", []).append(
                    {
                        "id": product_id,
                        "stock": product["stock"],
                        "data_quality": product["data_quality"],
                    }
                )

    return {"version": 1, "last_updated": FIXTURE_TIMESTAMP, "rules": rules}


def build_benchmark_queries() -> dict[str, Any]:
    happy = [
        "waterproof hiking boots",
        "trail running shoes",
        "road running sneakers",
        "casual canvas shoes",
        "gym training shoes",
        "leather approach shoes",
        "laptop backpack 15 inch",
        "canvas messenger bag",
        "waterproof travel duffel",
        "rolltop city pack",
        "trail hydration pack",
        "executive leather brief",
        "gore-tex rain jacket",
        "packable wind shell",
        "down alpine parka",
        "waterproof field jacket",
        "softshell trek hoodie",
        "urban insulated coat",
        "smartwatch with gps",
        "waterproof bluetooth speaker",
        "oled action camera",
        "amoled sport band",
        "noise cancelling earbuds",
        "rugged handheld gps",
        "down mummy sleeping bag",
        "synthetic camp quilt",
        "waterproof bivy sack",
        "expedition sleep system",
        "ultralight summer sleeping bag",
        "insulated camp blanket",
    ]
    incomplete = [
        "waterproof trail shoe",
        "terrain specific running shoe",
        "mesh road shoe size range",
        "waterproof laptop backpack",
        "messenger bag laptop 15 inch",
        "waterproof gore-tex shell",
        "outerwear weight grams waterproof",
        "smartwatch gps battery display",
        "waterproof oled action camera",
        "camping bag temp rating fill weight",
    ]
    poor = [
        "lightweight trail shoe terrain",
        "unknown footwear material search",
        "bag capacity material lookup",
        "outerwear waterproof size missing",
        "jacket material weight incomplete",
        "electronics display gps missing",
        "speaker battery waterproof missing",
        "camping fill weight material missing",
        "sleeping bag waterproof temp missing",
        "generic product catalog quality",
    ]
    return {
        "description": "Standard queries fired on every batch run",
        "queries": happy + incomplete + poor,
    }


def build_zero_result_queries() -> dict[str, Any]:
    footwear = [
        "waterproof trail shoe extra wide",
        "terrain specific hiking boot vegan",
        "wide fit waterproof trail shoe",
        "carbon plated waterproof hiking boot",
        "barefoot trail shoe gore-tex",
        "orthopedic waterproof gym trainer",
        "reflective road shoe waterproof",
        "insulated trail runner size 15",
        "minimalist leather trail sandal",
        "zero drop waterproof approach shoe",
    ]
    bags = [
        "waterproof canvas messenger bag laptop 15 inch",
        "camera backpack waterproof 17 inch",
        "vegan leather laptop tote 13 inch",
        "solar charging commuter backpack",
        "anti theft rolltop backpack 45 liters",
        "fireproof document laptop backpack",
        "transparent waterproof stadium bag laptop",
        "wheeled hiking backpack 60 liters",
    ]
    outerwear = [
        "lightweight waterproof jacket under 300 grams",
        "gore-tex parka with heated lining",
        "vegan down waterproof trench coat",
        "reflective cycling rain cape",
        "packable snow jacket under 200 grams",
        "waterproof blazer for office commute",
    ]
    general = [
        "vegan hiking boot",
        "solar powered smartwatch",
        "self inflating heated sleeping bag",
        "waterproof drone backpack",
        "avalanche beacon jacket",
        "biometric tent lock",
    ]
    return {
        "description": "Queries designed to return 0 results from OCS",
        "queries": footwear + bags + outerwear + general,
    }


def category_for_query(query: str) -> str:
    query_lower = query.lower()
    if any(term in query_lower for term in ["shoe", "sneaker", "trainer", "boot", "footwear", "runner"]):
        return "footwear"
    if any(term in query_lower for term in ["bag", "backpack", "duffel", "messenger", "brief", "pack", "tote"]):
        return "bags"
    if any(term in query_lower for term in ["jacket", "shell", "parka", "outerwear", "coat", "blazer", "cape"]):
        return "outerwear"
    if any(term in query_lower for term in ["smartwatch", "speaker", "camera", "band", "earbuds", "gps", "electronics", "drone"]):
        return "electronics"
    return "camping"


def products_for_query(product_files: dict[str, dict[str, Any]], query: str, offset: int, count: int = 6) -> list[dict[str, Any]]:
    category = category_for_query(query)
    products = [
        product
        for product in product_files[category]["products"]
        if product["stock"] > 0 and product["data_quality"] in {"complete", "new_arrival"}
    ]
    start = (offset * 7) % max(1, len(products))
    selected = []
    for index in range(count):
        selected.append(products[(start + index) % len(products)])
    return selected


def log_timestamp(index: int) -> str:
    return (LOG_BASE_TIME + timedelta(seconds=index * 10)).isoformat().replace("+00:00", "Z")


def build_search_log(
    *,
    index: int,
    query_text: str,
    tenant: str,
    selected_products: list[dict[str, Any]],
    status_code: int,
    latency_ms: int,
    result_count: int,
    scenario: str,
    is_low_ctr_scenario: bool = False,
    error_type: str | None = None,
) -> dict[str, Any]:
    timestamp = log_timestamp(index)
    request_id = f"req_20260606_{index:04d}"
    session_id = f"sess_{(index % 18) + 1:03d}"
    top_product_ids = [product["id"] for product in selected_products]

    clicked_product_ids = []
    if status_code == 200 and result_count > 0 and not is_low_ctr_scenario:
        if index % 3 != 0:
            clicked_product_ids = top_product_ids[:1]
    
    cart_add_product_ids = clicked_product_ids[:1] if clicked_product_ids and index % 5 == 0 else []

    filters = {}
    if "waterproof" in query_text:
        filters["waterproof"] = "true"
    if "laptop" in query_text:
        filters["laptop_size"] = "15inch"
    sort = "price" if index % 11 == 0 and status_code == 200 else None

    # Query normalization
    import re
    normalized_words = [w for w in re.findall(r"[a-z0-9]+", query_text.lower()) if w not in {"a", "the", "for", "with"}]
    normalized_text = " ".join(normalized_words) if normalized_words else None

    # Results mapping
    results = [
        {
            "product_id": pid,
            "rank": rank_idx + 1,
            "score": round(0.95 - (rank_idx * 0.05) - (index % 5) * 0.01, 2)
        }
        for rank_idx, pid in enumerate(top_product_ids)
    ]

    # Interaction clicks mapping (clicks happen 15s after search)
    from datetime import datetime, timedelta
    search_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    clicks = [
        {
            "product_id": pid,
            "rank": top_product_ids.index(pid) + 1,
            "timestamp": (search_dt + timedelta(seconds=15)).isoformat().replace("+00:00", "Z")
        }
        for pid in clicked_product_ids
        if pid in top_product_ids
    ]

    # Interaction cart adds mapping (cart adds happen 45s after search)
    cart_adds = [
        {
            "product_id": pid,
            "rank": top_product_ids.index(pid) + 1,
            "timestamp": (search_dt + timedelta(seconds=45)).isoformat().replace("+00:00", "Z")
        }
        for pid in cart_add_product_ids
        if pid in top_product_ids
    ]

    return {
        "timestamp": timestamp,
        "source": "gd_ai_search",
        "tenant": tenant,
        "request_id": request_id,
        "session_id": session_id,
        "user_id_hash": f"usr_{(index % 45) + 1:03d}",
        "query": {
            "text": query_text,
            "normalized_text": normalized_text,
            "filters": filters,
            "sort": sort
        },
        "response": {
            "status_code": status_code,
            "latency_ms": latency_ms,
            "result_count": result_count,
            "results": results
        },
        "interaction": {
            "clicks": clicks,
            "cart_adds": cart_adds
        },
        "context": {
            "device_type": ["desktop", "mobile", "tablet"][index % 3],
            "channel": "web",
            "locale": "en-US"
        },
        "error": error_type
    }


def build_search_logs(product_files: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    tenant = "retail_tenant_001"
    benchmark_queries = build_benchmark_queries()["queries"]
    zero_result_queries = build_zero_result_queries()["queries"]
    logs: list[dict[str, Any]] = []

    # Generate ~400 successful searches, some with anomalies
    for i in range(400):
        query_text = benchmark_queries[i % len(benchmark_queries)]
        index = len(logs) + 1
        selected_products = products_for_query(product_files, query_text, index)

        # Inject anomalies
        latency_ms = 30 + ((index * 17) % 150)
        # Latency spike for logs 50-70 -> will trigger in a 5-min window
        is_latency_spike = (50 <= i < 70)
        if is_latency_spike:
            latency_ms += 800

        # Low CTR anomaly - logs 100-150 have no clicks
        is_low_ctr = (100 <= i < 150)

        result_count = 6 + ((index * 19) % 74)

        status_code = 200
        error_type = None

        logs.append(
            build_search_log(
                index=index,
                query_text=query_text,
                tenant=tenant,
                selected_products=selected_products,
                status_code=status_code,
                latency_ms=latency_ms,
                result_count=result_count,
                scenario="successful_search",
                is_low_ctr_scenario=is_low_ctr,
                error_type=error_type,
            )
        )


    # Generate ~50 zero-result searches
    for i in range(50):
        query_text = zero_result_queries[i % len(zero_result_queries)]
        index = len(logs) + 1
        logs.append(
            build_search_log(
                index=index,
                query_text=query_text,
                tenant=tenant,
                selected_products=[],
                status_code=200,
                latency_ms=35 + ((index * 11) % 120),
                result_count=0,
                scenario="zero_result_search",
            )
        )


    # Generate ~50 error searches
    error_queries = [
        ("", 400, "client_error", "empty_query"),
        ("%%%% malformed filter payload", 400, "client_error", "bad_request"),
        ("waterproof hiking boots", 504, "timeout", "search_timeout"),
        ("smartwatch with gps", 503, "provider_error", "search_service_unavailable"),
        ("canvas messenger bag", 500, "provider_error", "search_internal_error"),
    ]
    for i in range(50):
        query_text, status_code, error_type, scenario = error_queries[i % len(error_queries)]
        index = len(logs) + 1
        logs.append(
            build_search_log(
                index=index,
                query_text=query_text,
                tenant=tenant,
                selected_products=[],
                status_code=status_code,
                latency_ms=900 + (index * 23),
                result_count=0,
                scenario=scenario,
                error_type=error_type,
            )
        )

    return logs



def build_catalog_scenarios() -> dict[str, Any]:
    scenarios = []
    for name, operation, product_id, source_file, changes in CATALOG_SCENARIOS:
        scenario = {
            "name": name,
            "operation": operation,
            "product_id": product_id,
            "source_file": source_file,
        }
        if changes is not None:
            scenario["changes"] = changes
        scenarios.append(scenario)
    return {
        "description": "Catalog changes to simulate for catalog_delta signals",
        "scenarios": scenarios,
    }


def build_rule_scenarios(products_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    def snapshot(product_id: str) -> dict[str, Any]:
        product = products_by_id[product_id]
        return {"id": product_id, "stock": product["stock"], "data_quality": product["data_quality"]}

    scenarios: list[dict[str, Any]] = []
    for rule_id, before, after, target in [
        ("MXP-001", 1.33, 2.1, "FOOT-121"),
        ("MXP-002", 1.46, 2.2, "FOOT-122"),
        ("MXP-003", 1.59, 2.3, "OUT-081"),
        ("MXP-004", 1.72, 2.4, "ELEC-062"),
    ]:
        scenarios.append(
            {
                "name": f"Increase boost for OOS target on {rule_id}",
                "rule_id": rule_id,
                "operation": "UPDATE",
                "changes": {"boost_factor": {"before": before, "after": after}},
                "before_state": {"boost_factor": before, "target_products": [target], "target_product_snapshots": [snapshot(target)]},
                "after_state": {"boost_factor": after, "target_products": [target], "target_product_snapshots": [snapshot(target)]},
            }
        )
    for rule_id, before, after in [("MXP-005", 1.85, 1.5), ("MXP-006", 1.98, 1.6)]:
        scenarios.append(
            {
                "name": f"Decrease boost factor on {rule_id}",
                "rule_id": rule_id,
                "operation": "UPDATE",
                "changes": {"boost_factor": {"before": before, "after": after}},
                "before_state": {"boost_factor": before},
                "after_state": {"boost_factor": after},
            }
        )
    for rule_id, before_terms, after_terms in [
        ("MXP-015", ["rain shell", "waterproof jacket"], ["rain shell", "waterproof jacket", "hard shell"]),
        ("MXP-016", ["daypack", "rucksack"], ["daypack", "rucksack", "commuter pack"]),
    ]:
        scenarios.append(
            {
                "name": f"Add synonym term to {rule_id}",
                "rule_id": rule_id,
                "operation": "UPDATE",
                "changes": {"terms": {"before": before_terms, "after": after_terms}},
                "before_state": {"terms": before_terms},
                "after_state": {"terms": after_terms},
            }
        )

    inserted_rules = [
        {
            "rule_id": "MXP-021",
            "rule_type": "boost",
            "target_products": ["FOOT-121"],
            "boost_factor": 2.3,
            "campaign": "Emergency Trail Promo",
            "active": True,
            "created_by": "merchandiser_alice",
            "created_at": FIXTURE_TIMESTAMP,
            "target_product_snapshots": [snapshot("FOOT-121")],
        },
        {
            "rule_id": "MXP-022",
            "rule_type": "boost",
            "target_products": ["ELEC-061"],
            "boost_factor": 2.4,
            "campaign": "Wearable Doorbuster",
            "active": True,
            "created_by": "merchandiser_ben",
            "created_at": FIXTURE_TIMESTAMP,
            "target_product_snapshots": [snapshot("ELEC-061")],
        },
        {
            "rule_id": "MXP-023",
            "rule_type": "suppress",
            "target_products": ["BAGS-070"],
            "reason": "margin protection",
            "active": True,
            "created_by": "merchandiser_chandra",
            "created_at": FIXTURE_TIMESTAMP,
            "target_product_snapshots": [snapshot("BAGS-070")],
        },
        {
            "rule_id": "MXP-024",
            "rule_type": "synonym",
            "target_products": [],
            "terms": ["raincoat", "rain wear"],
            "canonical": "rain jacket",
            "active": True,
            "created_by": "merchandiser_diego",
            "created_at": FIXTURE_TIMESTAMP,
        },
    ]
    for rule in inserted_rules:
        scenarios.append(
            {
                "name": f"Insert {rule['rule_type']} rule {rule['rule_id']}",
                "rule_id": rule["rule_id"],
                "operation": "INSERT",
                "rule": rule,
            }
        )

    scenarios.extend(
        [
            {
                "name": "Delete active suppress rule",
                "rule_id": "MXP-009",
                "operation": "DELETE",
                "before_state": {"active": True, "rule_type": "suppress", "target_products": ["FOOT-100", "BAGS-070"]},
                "after_state": {},
            },
            {
                "name": "Delete inactive boost rule",
                "rule_id": "MXP-008",
                "operation": "DELETE",
                "before_state": {"active": False, "rule_type": "boost", "target_products": ["BAGS-080", "CAMP-080"]},
                "after_state": {},
            },
            {
                "name": "Activate OOS boost rule",
                "rule_id": "MXP-007",
                "operation": "UPDATE",
                "changes": {"active": {"before": False, "after": True}},
                "before_state": {"active": False, "target_products": ["ELEC-061"], "target_product_snapshots": [snapshot("ELEC-061")]},
                "after_state": {"active": True, "target_products": ["ELEC-061"], "target_product_snapshots": [snapshot("ELEC-061")]},
            },
            {
                "name": "Activate suppress rule",
                "rule_id": "MXP-014",
                "operation": "UPDATE",
                "changes": {"active": {"before": False, "after": True}},
                "before_state": {"active": False, "rule_type": "suppress", "target_products": ["BAGS-145"]},
                "after_state": {"active": True, "rule_type": "suppress", "target_products": ["BAGS-145"]},
            },
        ]
    )

    return {
        "description": "Rule changes to simulate for rule_diff signals",
        "scenarios": scenarios,
    }


def build_index(product_files: dict[str, dict[str, Any]]) -> dict[str, Any]:
    products = [
        {
            "id": product["id"],
            "category": product["category"],
            "stock": product["stock"],
            "data_quality": product["data_quality"],
        }
        for category_file in product_files.values()
        for product in category_file["products"]
    ]
    return {
        "description": "Flat index of all product IDs for quick lookup",
        "total": len(products),
        "products": products,
        "oos_products": [product["id"] for product in products if product["stock"] == 0],
        "low_stock_products": [product["id"] for product in products if 1 <= product["stock"] <= 10],
        "incomplete_products": [product["id"] for product in products if product["data_quality"] == "incomplete"],
        "poor_products": [product["id"] for product in products if product["data_quality"] == "poor"],
        "new_arrivals": [product["id"] for product in products if product["data_quality"] == "new_arrival"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(payload + "\n", encoding="utf-8")


def generate(output: Path) -> None:
    if output.exists():
        for child in output.iterdir():
            if child.name == ".DS_Store":
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    product_files = build_products()
    products_by_id = product_map(product_files)
    for category, payload in product_files.items():
        write_json(output / "products" / f"{category}.json", payload)

    write_json(output / "rules" / "rules.json", build_rules(products_by_id))
    write_json(output / "queries" / "benchmark_queries.json", build_benchmark_queries())
    write_json(output / "queries" / "zero_result_queries.json", build_zero_result_queries())
    write_jsonl(output / "logs" / "search_events.jsonl", build_search_logs(product_files))
    write_json(output / "scenarios" / "catalog_scenarios.json", build_catalog_scenarios())
    write_json(output / "scenarios" / "rule_scenarios.json", build_rule_scenarios(products_by_id))
    write_json(output / "index" / "product_index.json", build_index(product_files))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_quality_counts(total: int) -> dict[str, int]:
    complete = int(total * QUALITY_COUNTS["complete"])
    incomplete = int(total * QUALITY_COUNTS["incomplete"])
    poor = int(total * QUALITY_COUNTS["poor"])
    return {
        "complete": complete,
        "incomplete": incomplete,
        "poor": poor,
        "new_arrival": total - complete - incomplete - poor,
    }


def collect_product_files(root: Path) -> dict[str, dict[str, Any]]:
    files = {}
    for category in CATEGORY_CONFIGS:
        path = root / "products" / f"{category}.json"
        require(path.exists(), f"missing product file {path}")
        files[category] = read_json(path)
    return files


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(root: Path) -> dict[str, Any]:
    product_files = collect_product_files(root)
    products_by_id = product_map(product_files)

    require(len(products_by_id) == 1000, f"expected 1000 unique products, found {len(products_by_id)}")
    for category, config in CATEGORY_CONFIGS.items():
        payload = product_files[category]
        require(payload["category"] == category, f"{category} category mismatch")
        products = payload["products"]
        require(len(products) == config["count"], f"{category} expected {config['count']} products, found {len(products)}")
        require(Counter(product["data_quality"] for product in products) == expected_quality_counts(config["count"]), f"{category} quality count mismatch")
        for index, product in enumerate(products, start=1):
            require(product["id"] == f"{config['prefix']}-{index:03d}", f"{category} product id mismatch at position {index}")
            require(product["category"] == category, f"{product['id']} category mismatch")
            require(set(product["attributes"]) == set(config["attributes"]), f"{product['id']} attributes mismatch")
            quality = product["data_quality"]
            null_count = sum(value is None for value in product["attributes"].values())
            if quality == "complete":
                require(null_count == 0, f"{product['id']} complete product has null attributes")
                require(10 <= product["stock"] <= 200, f"{product['id']} complete stock must be 10-200")
            elif quality == "incomplete":
                require(null_count >= 2, f"{product['id']} incomplete product needs 2+ null attributes")
                require(0 <= product["stock"] <= 100, f"{product['id']} incomplete stock must be 0-100")
            elif quality == "poor":
                require(product["title"] == f"Product {product['id']}", f"{product['id']} poor title mismatch")
                require(product["brand"] is None, f"{product['id']} poor brand must be null")
                require(null_count == len(product["attributes"]), f"{product['id']} poor attributes must all be null")
                require(5 <= product["stock"] <= 50, f"{product['id']} poor stock must be 5-50")
            elif quality == "new_arrival":
                require(null_count == len(product["attributes"]) - 1, f"{product['id']} new arrival needs exactly 1 populated attribute")
                require(20 <= product["stock"] <= 100, f"{product['id']} new arrival stock must be 20-100")
            else:
                raise ValueError(f"{product['id']} has invalid data_quality {quality}")

    index = read_json(root / "index" / "product_index.json")
    indexed = index["products"]
    require(index["total"] == 1000, "product_index total must be 1000")
    require(index["total"] == len(indexed), "product_index total does not match products length")
    require({item["id"] for item in indexed} == set(products_by_id), "product_index product ids mismatch")
    actual_oos = [item["id"] for item in indexed if item["stock"] == 0]
    actual_low = [item["id"] for item in indexed if 1 <= item["stock"] <= 10]
    actual_incomplete = [item["id"] for item in indexed if item["data_quality"] == "incomplete"]
    actual_poor = [item["id"] for item in indexed if item["data_quality"] == "poor"]
    actual_new = [item["id"] for item in indexed if item["data_quality"] == "new_arrival"]
    require(index["oos_products"] == actual_oos, "oos_products list mismatch")
    require(index["low_stock_products"] == actual_low, "low_stock_products list mismatch")
    require(index["incomplete_products"] == actual_incomplete, "incomplete_products list mismatch")
    require(index["poor_products"] == actual_poor, "poor_products list mismatch")
    require(index["new_arrivals"] == actual_new, "new_arrivals list mismatch")
    require(len(actual_oos) >= 80, "expected at least 80 OOS products")
    require(sum(pid.startswith("FOOT-") for pid in actual_oos) >= 10, "expected at least 10 OOS footwear products")
    require(sum(pid.startswith("ELEC-") for pid in actual_oos) >= 10, "expected at least 10 OOS electronics products")
    require(len(actual_low) >= 100, "expected at least 100 low-stock products")

    rules_payload = read_json(root / "rules" / "rules.json")
    require(rules_payload["version"] == 1, "rules version must reset to 1")
    require(rules_payload["last_updated"] == FIXTURE_TIMESTAMP, "rules last_updated timestamp mismatch")
    rules = rules_payload["rules"]
    require(len(rules) == 20, "expected 20 rules")
    type_counts = Counter(rule["rule_type"] for rule in rules)
    require(type_counts == {"boost": 8, "suppress": 6, "synonym": 6}, f"rule type counts mismatch: {type_counts}")
    require([rule["rule_id"] for rule in rules] == [f"MXP-{index:03d}" for index in range(1, 21)], "rule ids must be MXP-001..MXP-020")
    for rule in rules:
        for product_id in rule["target_products"]:
            require(product_id in products_by_id, f"rule {rule['rule_id']} references missing product {product_id}")
    boost_rules_with_oos = [
        rule
        for rule in rules
        if rule["rule_type"] == "boost" and any(products_by_id[product_id]["stock"] == 0 for product_id in rule["target_products"])
    ]
    require(len(boost_rules_with_oos) >= 4, "expected at least 4 boost rules targeting OOS products")
    inactive_boosts = [rule for rule in rules if rule["rule_type"] == "boost" and not rule["active"]]
    require(len(inactive_boosts) >= 2, "expected at least 2 inactive boost rules")
    risky_suppresses = [
        rule
        for rule in rules
        if rule["rule_type"] == "suppress" and any(products_by_id[product_id]["stock"] > 50 for product_id in rule["target_products"])
    ]
    require(len(risky_suppresses) >= 2, "expected at least 2 suppress rules targeting stock > 50")

    benchmark = read_json(root / "queries" / "benchmark_queries.json")
    zero_result = read_json(root / "queries" / "zero_result_queries.json")
    require(len(benchmark["queries"]) == 50, "benchmark_queries must contain exactly 50 queries")
    require(len(zero_result["queries"]) == 30, "zero_result_queries must contain exactly 30 queries")

    logs_path = root / "logs" / "search_events.jsonl"
    require(logs_path.exists(), "missing search_events.jsonl")
    search_logs = [
        json.loads(line)
        for line in logs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(search_logs) == 500, f"expected 500 search logs, found {len(search_logs)}")
    request_ids = [log["request_id"] for log in search_logs]
    require(len(set(request_ids)) == len(request_ids), "search log request_ids must be unique")
    required_log_fields = {
        "timestamp",
        "source",
        "tenant",
        "request_id",
        "session_id",
        "user_id_hash",
        "query",
        "response",
        "interaction",
        "context",
        "error"
    }
    for log in search_logs:
        require(required_log_fields.issubset(log), f"search log {log.get('request_id')} missing required fields")
        require(log["tenant"] == "retail_tenant_001", f"search log {log['request_id']} tenant mismatch")
        require(isinstance(log["query"], dict), f"search log {log['request_id']} query block is not dict")
        require(isinstance(log["response"], dict), f"search log {log['request_id']} response block is not dict")
        require("text" in log["query"], f"search log {log['request_id']} missing query text")
        require("status_code" in log["response"], f"search log {log['request_id']} missing status_code")
    require(sum(1 for log in search_logs if log["response"]["result_count"] == 0 and log["response"]["status_code"] == 200) >= 30, "expected at least 30 zero-result logs")
    require(any(log["response"]["status_code"] >= 500 for log in search_logs), "expected at least one server/provider error log")
    require(any(log["response"]["status_code"] == 400 for log in search_logs), "expected at least one client error log")
    require(any(log["interaction"]["clicks"] for log in search_logs), "expected at least one click log")
    require(any(log["interaction"]["cart_adds"] for log in search_logs), "expected at least one cart-add log")

    catalog_scenarios = read_json(root / "scenarios" / "catalog_scenarios.json")["scenarios"]
    require(len(catalog_scenarios) == 20, "catalog_scenarios must contain exactly 20 scenarios")
    require(Counter(scenario["operation"] for scenario in catalog_scenarios) == {"INSERT": 5, "UPDATE": 12, "DELETE": 3}, "catalog scenario operation distribution mismatch")
    for scenario in catalog_scenarios:
        require(scenario["product_id"] in products_by_id, f"catalog scenario references missing product {scenario['product_id']}")

    rule_scenarios = read_json(root / "scenarios" / "rule_scenarios.json")["scenarios"]
    require(len(rule_scenarios) == 16, "rule_scenarios must contain exactly 16 scenarios")
    require(Counter(scenario["operation"] for scenario in rule_scenarios) == {"UPDATE": 10, "INSERT": 4, "DELETE": 2}, "rule scenario operation distribution mismatch")
    require(all(scenario["operation"] != "ACTIVATE" for scenario in rule_scenarios), "ACTIVATE must be encoded as UPDATE")
    for scenario in rule_scenarios:
        for state_name in ("before_state", "after_state"):
            for product_id in scenario.get(state_name, {}).get("target_products", []):
                require(product_id in products_by_id, f"rule scenario {scenario['rule_id']} references missing product {product_id}")
        for product_id in scenario.get("rule", {}).get("target_products", []):
            require(product_id in products_by_id, f"insert rule scenario {scenario['rule_id']} references missing product {product_id}")
    activation_updates = [
        scenario
        for scenario in rule_scenarios
        if scenario["operation"] == "UPDATE" and scenario.get("changes", {}).get("active", {}).get("before") is False and scenario.get("changes", {}).get("active", {}).get("after") is True
    ]
    require(len(activation_updates) == 2, "expected exactly 2 activation updates")

    return {
        "products": len(products_by_id),
        "oos_products": len(actual_oos),
        "low_stock_products": len(actual_low),
        "benchmark_queries": len(benchmark["queries"]),
        "zero_result_queries": len(zero_result["queries"]),
        "search_logs": len(search_logs),
        "catalog_scenarios": len(catalog_scenarios),
        "rule_scenarios": len(rule_scenarios),
        "boost_rules_with_oos": len(boost_rules_with_oos),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and validate Magellan mock data fixtures.")
    parser.add_argument("--output", type=Path, help="Directory to generate mock-data into.")
    parser.add_argument("--validate-only", type=Path, help="Validate an existing mock-data directory without regenerating.")
    parser.add_argument("--skip-validation", action="store_true", help="Generate without the automatic validation pass.")
    args = parser.parse_args()

    if args.output and args.validate_only:
        parser.error("--output and --validate-only cannot be used together")
    if not args.output and not args.validate_only:
        parser.error("provide either --output or --validate-only")
    if args.skip_validation and not args.output:
        parser.error("--skip-validation only applies with --output")

    target = args.output or args.validate_only
    if args.output:
        generate(target)
        if args.skip_validation:
            print(f"Generated mock data at {target}")
            return

    summary = validate(target)
    action = "Generated and validated" if args.output else "Validated"
    print(f"{action} mock data at {target}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
