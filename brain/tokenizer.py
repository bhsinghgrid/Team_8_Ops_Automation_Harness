"""
Tokenizer for Recursive Language Model.
Handles text tokenization, encoding, and preprocessing.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import json


class Token:
    """Represents a single token."""

    def __init__(self, text: str, token_type: str, position: int):
        self.text = text
        self.token_type = token_type  # 'word', 'punctuation', 'number', 'special'
        self.position = position

    def __repr__(self):
        return f"Token('{self.text}', {self.token_type}, {self.position})"


class Vocabulary:
    """Manages vocabulary for tokenization."""

    def __init__(self, min_frequency: int = 1):
        self.min_frequency = min_frequency
        self.word_to_id: Dict[str, int] = {}
        self.id_to_word: Dict[int, str] = {}
        self.word_freq: Counter = Counter()
        self.special_tokens = {
            "[PAD]": 0,
            "[UNK]": 1,
            "[CLS]": 2,
            "[SEP]": 3,
            "[MASK]": 4,
        }
        self._initialize_special_tokens()

    def _initialize_special_tokens(self):
        """Initialize special tokens in vocabulary."""
        current_id = 0
        for token, token_id in self.special_tokens.items():
            self.word_to_id[token] = token_id
            self.id_to_word[token_id] = token
            current_id = max(current_id, token_id + 1)
        self.next_id = current_id

    def add_word(self, word: str) -> int:
        """Add word to vocabulary, return its ID."""
        if word in self.word_to_id:
            return self.word_to_id[word]

        if word in self.special_tokens:
            return self.special_tokens[word]

        self.word_freq[word] += 1

        if self.word_freq[word] >= self.min_frequency:
            word_id = self.next_id
            self.word_to_id[word] = word_id
            self.id_to_word[word_id] = word
            self.next_id += 1
            return word_id

        return self.special_tokens["[UNK]"]

    def get_id(self, word: str) -> int:
        """Get ID for word, return [UNK] if not found."""
        return self.word_to_id.get(word, self.special_tokens["[UNK]"])

    def get_word(self, word_id: int) -> str:
        """Get word for ID."""
        return self.id_to_word.get(word_id, "[UNK]")

    def build_from_tokens(self, tokens: List[str]):
        """Build vocabulary from list of tokens."""
        for token in tokens:
            self.add_word(token)

    def size(self) -> int:
        """Get vocabulary size."""
        return len(self.word_to_id)

    def __repr__(self):
        return f"Vocabulary(size={self.size()})"


class Tokenizer:
    """Base tokenizer class."""

    def __init__(self, vocabulary: Optional[Vocabulary] = None):
        self.vocabulary = vocabulary or Vocabulary()
        self.token_patterns = {
            "number": r"\d+(?:\.\d+)?",
            "word": r"\b\w+\b",
            "punctuation": r"[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]",
            "whitespace": r"\s+",
        }

    def tokenize(self, text: str) -> List[Token]:
        """Tokenize text into tokens."""
        tokens = []
        position = 0

        # Simple regex-based tokenization
        pattern = r"\w+|[^\w\s]"
        matches = re.finditer(pattern, text)

        for match in matches:
            token_text = match.group()
            token_type = self._classify_token(token_text)

            token = Token(token_text, token_type, match.start())
            tokens.append(token)

        return tokens

    def _classify_token(self, token: str) -> str:
        """Classify token type."""
        if re.match(r"^\d+(?:\.\d+)?$", token):
            return "number"
        elif re.match(r"^\w+$", token):
            return "word"
        elif re.match(r"^[!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]+$", token):
            return "punctuation"
        else:
            return "special"

    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        tokens = self.tokenize(text)
        token_ids = []

        for token in tokens:
            if token.token_type == "word":
                token_id = self.vocabulary.get_id(token.text.lower())
            else:
                token_id = self.vocabulary.get_id(token.text)
            token_ids.append(token_id)

        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs back to text."""
        words = []
        for token_id in token_ids:
            word = self.vocabulary.get_word(token_id)
            if word not in ["[PAD]", "[UNK]"]:
                words.append(word)
        return " ".join(words)

    def get_vocabulary_size(self) -> int:
        """Get vocabulary size."""
        return self.vocabulary.size()


class BPETokenizer(Tokenizer):
    """Byte Pair Encoding Tokenizer."""

    def __init__(self, vocabulary: Optional[Vocabulary] = None, num_merges: int = 1000):
        super().__init__(vocabulary)
        self.num_merges = num_merges
        self.merges: List[Tuple[str, str]] = []
        self.merge_cache: Dict[Tuple[str, str], int] = {}

    def train(self, texts: List[str]):
        """Train BPE tokenizer on texts."""
        # Build initial vocabulary
        for text in texts:
            tokens = self.tokenize(text)
            for token in tokens:
                if token.token_type == "word":
                    self.vocabulary.add_word(token.text.lower())

        # Learn merges (simplified BPE)
        for _ in range(self.num_merges):
            # In practice, would find most frequent pair and merge
            pass

    def encode(self, text: str) -> List[int]:
        """Encode using BPE."""
        # Use parent implementation as base
        return super().encode(text)


class SubwordTokenizer(Tokenizer):
    """Subword tokenizer for better vocabulary coverage."""

    def __init__(self, vocabulary: Optional[Vocabulary] = None):
        super().__init__(vocabulary)
        self.subword_cache: Dict[str, List[int]] = {}

    def tokenize_subword(self, word: str) -> List[str]:
        """Break word into subwords."""
        if word in self.subword_cache:
            return self.subword_cache[word]

        # Simple heuristic-based subword splitting
        subwords = []
        current = ""

        for i, char in enumerate(word):
            current += char

            # Split at common boundaries
            if i > 0 and len(current) > 3:
                if self._is_boundary(word, i):
                    subwords.append(current[:-1])
                    current = char

        if current:
            subwords.append(current)

        self.subword_cache[word] = subwords
        return subwords

    def _is_boundary(self, word: str, position: int) -> bool:
        """Determine if position is a word boundary."""
        if position >= len(word):
            return False

        # Check for vowel-consonant boundary
        vowels = "aeiouAEIOU"
        curr_is_vowel = word[position] in vowels
        prev_is_vowel = word[position - 1] in vowels

        return curr_is_vowel != prev_is_vowel

    def encode(self, text: str) -> List[int]:
        """Encode using subword tokenization."""
        tokens = self.tokenize(text)
        token_ids = []

        for token in tokens:
            if token.token_type == "word":
                subwords = self.tokenize_subword(token.text.lower())
                for subword in subwords:
                    token_id = self.vocabulary.get_id(subword)
                    token_ids.append(token_id)
            else:
                token_id = self.vocabulary.get_id(token.text)
                token_ids.append(token_id)

        return token_ids

    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs, joining subwords."""
        words = []
        current_word = ""

        for token_id in token_ids:
            word = self.vocabulary.get_word(token_id)

            if word in ["[PAD]", "[UNK]", "[SEP]", "[CLS]"]:
                if current_word:
                    words.append(current_word)
                    current_word = ""
            elif word.startswith("##"):
                current_word += word[2:]
            else:
                if current_word:
                    words.append(current_word)
                current_word = word

        if current_word:
            words.append(current_word)

        return " ".join(words)


class TokenizerFactory:
    """Factory for creating tokenizers."""

    @staticmethod
    def create_tokenizer(
        tokenizer_type: str = "standard",
        vocabulary: Optional[Vocabulary] = None,
        **kwargs,
    ) -> Tokenizer:
        """Create tokenizer of specified type."""
        if tokenizer_type == "standard":
            return Tokenizer(vocabulary)
        elif tokenizer_type == "bpe":
            return BPETokenizer(vocabulary, num_merges=kwargs.get("num_merges", 1000))
        elif tokenizer_type == "subword":
            return SubwordTokenizer(vocabulary)
        else:
            raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")

    @staticmethod
    def create_vocabulary(min_frequency: int = 1) -> Vocabulary:
        """Create new vocabulary."""
        return Vocabulary(min_frequency=min_frequency)
