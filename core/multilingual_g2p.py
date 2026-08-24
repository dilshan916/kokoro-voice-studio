"""
Kokoro Studio — Multilingual G2P Preprocessor & Language Routing Engine
========================================================================
Provides high-accuracy language identification, Unicode-safe text normalizers,
morphological Japanese POS & particle G2P (Janome + M2P table: は -> wa, へ -> e, を -> o),
language-specific G2P phonemizers, and CJK-to-Kokoro unified IPA token harmonization.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import unicodedata
from typing import Dict, List, Optional, Set, Tuple

# Lazy placeholder for Tokenizer and phonemizer
phonemizer = None
DEFAULT_VOCAB = None
Tokenizer = None

def _ensure_g2p_base():
    global phonemizer, DEFAULT_VOCAB, Tokenizer
    if DEFAULT_VOCAB is None:
        import phonemizer as _ph
        from kokoro_onnx.tokenizer import DEFAULT_VOCAB as _DV, Tokenizer as _TK
        phonemizer = _ph
        DEFAULT_VOCAB = _DV
        Tokenizer = _TK

logger = logging.getLogger(__name__)

# Canonical language code mappings
CANONICAL_LANG_MAP: Dict[str, str] = {
    # English
    "en": "en-us",
    "en-us": "en-us",
    "en-gb": "en-gb",
    "en_us": "en-us",
    "en_gb": "en-gb",
    "english": "en-us",
    "english (us)": "en-us",
    "english (uk)": "en-gb",
    # French
    "fr": "fr-fr",
    "fr-fr": "fr-fr",
    "fr_fr": "fr-fr",
    "fra": "fr-fr",
    "fre": "fr-fr",
    "french": "fr-fr",
    # Spanish
    "es": "es",
    "es-es": "es",
    "es_es": "es",
    "spa": "es",
    "spanish": "es",
    # Italian
    "it": "it",
    "it-it": "it",
    "ita": "it",
    "italian": "it",
    # Portuguese
    "pt": "pt-br",
    "pt-br": "pt-br",
    "pt_br": "pt-br",
    "pt-pt": "pt-br",
    "por": "pt-br",
    "portuguese": "pt-br",
    "portuguese (br)": "pt-br",
    # German
    "de": "de",
    "de-de": "de",
    "ger": "de",
    "deu": "de",
    "german": "de",
    # Hindi
    "hi": "hi",
    "hin": "hi",
    "hindi": "hi",
    # Japanese
    "ja": "ja",
    "jp": "ja",
    "jpn": "ja",
    "japanese": "ja",
    # Korean
    "ko": "ko",
    "kor": "ko",
    "korean": "ko",
    # Chinese (Mandarin)
    "zh": "cmn",
    "zh-cn": "cmn",
    "zh-tw": "cmn",
    "zh_cn": "cmn",
    "cmn": "cmn",
    "zho": "cmn",
    "chi": "cmn",
    "chinese": "cmn",
    "mandarin": "cmn",
}

# Unicode Script Block Regex Patterns for Fast, Deterministic Detection
_HANGUL_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")
_KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_HANZI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097f]")

# Tone conversion map for Mandarin phonemes in Kokoro IPA vocabulary
_MANDARIN_TONE_MAP = {
    "1": "→",
    "2": "↗",
    "3": "↓",
    "4": "↘",
    "5": "",  # Neutral tone has no arrow marker
}

# Character harmonizations for European / Asian phonemes
_IPA_SUBSTITUTIONS = {
    "ä": "a",
    "o̞": "o",
    "e̞": "e",
    "a̠": "a",
    "ɯᵝ": "ɯ",
    "g": "ɡ",  # Ensure ASCII 'g' is mapped to Kokoro token 92 ('ɡ')
    "\u031e": "",  # Down tack diacritic
    "\u0320": "",  # Minus sign below
    "\u0308": "",  # Combining diaeresis
}

# Kokoro Native Japanese Mora-to-Phoneme (M2P) Conversion Table (Hexgrad Standard)
_JA_M2P: Dict[str, str] = {
    chr(12449): 'a', chr(12450): 'a', chr(12451): 'i', chr(12452): 'i', chr(12453): 'u',
    chr(12454): 'u', chr(12455): 'e', chr(12456): 'e', chr(12457): 'o', chr(12458): 'o',
    chr(12459): 'ka', chr(12460): 'ɡa', chr(12461): 'ki', chr(12462): 'ɡi', chr(12463): 'ku',
    chr(12464): 'ɡu', chr(12465): 'ke', chr(12466): 'ɡe', chr(12467): 'ko', chr(12468): 'ɡo',
    chr(12469): 'sa', chr(12470): 'za', chr(12471): 'ɕi', chr(12472): 'ʥi', chr(12473): 'su',
    chr(12474): 'zu', chr(12475): 'se', chr(12476): 'ze', chr(12477): 'so', chr(12478): 'zo',
    chr(12479): 'ta', chr(12480): 'da', chr(12481): 'ʨi', chr(12482): 'ʥi', chr(12484): 'ʦu',
    chr(12485): 'zu', chr(12486): 'te', chr(12487): 'de', chr(12488): 'to', chr(12489): 'do',
    chr(12490): 'na', chr(12491): 'ni', chr(12492): 'nu', chr(12493): 'ne', chr(12494): 'no',
    chr(12495): 'ha', chr(12496): 'ba', chr(12497): 'pa', chr(12498): 'hi', chr(12499): 'bi',
    chr(12500): 'pi', chr(12501): 'fu', chr(12502): 'bu', chr(12503): 'pu', chr(12504): 'he',
    chr(12505): 'be', chr(12506): 'pe', chr(12507): 'ho', chr(12508): 'bo', chr(12509): 'po',
    chr(12510): 'ma', chr(12511): 'mi', chr(12512): 'mu', chr(12513): 'me', chr(12514): 'mo',
    chr(12515): 'ja', chr(12516): 'ja', chr(12517): 'ju', chr(12518): 'ju', chr(12519): 'jo',
    chr(12520): 'jo', chr(12521): 'ra', chr(12522): 'ri', chr(12523): 'ru', chr(12524): 're',
    chr(12525): 'ro', chr(12526): 'wa', chr(12527): 'wa', chr(12528): 'i', chr(12529): 'e',
    chr(12530): 'o', chr(12532): 'vu', chr(12533): 'ka', chr(12534): 'ke', chr(12535): 'va',
    chr(12536): 'vi', chr(12537): 've', chr(12538): 'vo',
}

# Digraphs / Compound Moras
_JA_M2P.update({
    chr(12452) + chr(12455): 'je',
    chr(12454) + chr(12451): 'wi',
    chr(12454) + chr(12453): 'wu',
    chr(12454) + chr(12455): 'we',
    chr(12454) + chr(12457): 'wo',
    chr(12461) + chr(12451): 'kʲi',
    chr(12461) + chr(12455): 'kʲe',
    chr(12461) + chr(12515): 'kʲa',
    chr(12461) + chr(12517): 'kʲu',
    chr(12461) + chr(12519): 'kʲo',
    chr(12462) + chr(12451): 'ɡʲi',
    chr(12462) + chr(12455): 'ɡʲe',
    chr(12462) + chr(12515): 'ɡʲa',
    chr(12462) + chr(12517): 'ɡʲu',
    chr(12462) + chr(12519): 'ɡʲo',
    chr(12463) + chr(12449): 'kwa',
    chr(12463) + chr(12451): 'kwi',
    chr(12463) + chr(12453): 'kwu',
    chr(12463) + chr(12455): 'kwe',
    chr(12463) + chr(12457): 'kwo',
    chr(12464) + chr(12449): 'ɡwa',
    chr(12471) + chr(12455): 'ɕe',
    chr(12471) + chr(12515): 'ɕa',
    chr(12471) + chr(12517): 'ɕu',
    chr(12471) + chr(12519): 'ɕo',
    chr(12472) + chr(12455): 'ʥe',
    chr(12472) + chr(12515): 'ʥa',
    chr(12472) + chr(12517): 'ʥu',
    chr(12472) + chr(12519): 'ʥo',
    chr(12473) + chr(12451): 'si',
    chr(12474) + chr(12451): 'zi',
    chr(12481) + chr(12455): 'ʨe',
    chr(12481) + chr(12515): 'ʨa',
    chr(12481) + chr(12517): 'ʨu',
    chr(12481) + chr(12519): 'ʨo',
    chr(12484) + chr(12449): 'ʦa',
    chr(12484) + chr(12451): 'ʦi',
    chr(12484) + chr(12455): 'ʦe',
    chr(12484) + chr(12457): 'ʦo',
    chr(12486) + chr(12451): 'ti',
    chr(12487) + chr(12451): 'di',
    chr(12488) + chr(12453): 'tu',
    chr(12489) + chr(12453): 'du',
    chr(12491) + chr(12455): 'ɲe',
    chr(12491) + chr(12515): 'ɲa',
    chr(12491) + chr(12517): 'ɲu',
    chr(12491) + chr(12519): 'ɲo',
    chr(12498) + chr(12455): 'çe',
    chr(12498) + chr(12515): 'ça',
    chr(12498) + chr(12517): 'çu',
    chr(12498) + chr(12519): 'ço',
    chr(12499) + chr(12515): 'bʲa',
    chr(12499) + chr(12517): 'bʲu',
    chr(12499) + chr(12519): 'bʲo',
    chr(12500) + chr(12515): 'pʲa',
    chr(12500) + chr(12517): 'pʲu',
    chr(12500) + chr(12519): 'pʲo',
    chr(12501) + chr(12449): 'fa',
    chr(12501) + chr(12451): 'fi',
    chr(12501) + chr(12455): 'fe',
    chr(12501) + chr(12457): 'fo',
    chr(12511) + chr(12515): 'mʲa',
    chr(12511) + chr(12517): 'mʲu',
    chr(12511) + chr(12519): 'mʲo',
    chr(12522) + chr(12515): 'ɾʲa',
    chr(12522) + chr(12517): 'ɾʲu',
    chr(12522) + chr(12519): 'ɾʲo',
})

# Special Kokoro Japanese markers
_JA_M2P['ッ'] = 'ʔ'
_JA_M2P['ン'] = 'ɴ'
_JA_M2P['ー'] = 'ː'

_JA_PUNCT: Dict[str, str] = {
    '、': ',', '。': '.', '！': '!', '？': '?', ' ': ' ', '　': ' ',
    '「': '"', '」': '"', '『': '"', '』': '"', '（': '(', '）': ')',
    '：': ':', '；': ';', '・': ' ', '…': '…'
}

# Known Japanese words starting with は or へ where the initial mora is part of the root (not a particle)
_KNOWN_HA_ROOT_WORDS = {
    'はい', 'はじめ', 'はじめて', 'はじまる', 'はしる', 'はな', 'はなす', 'はなし', 'はやい',
    'はやく', 'はる', 'はれ', 'はれる', 'はは', 'はこ', 'はたらく', 'はらう', 'はげしい',
    'はん', 'はんぶん', 'はず', 'はずかしい', 'はっきり', 'はく', 'はし', 'はた', 'はだ',
    'はて', 'はなれる', 'はね', 'はば', 'はまる', 'はやす', 'はるか', 'はんたい',
    'はんだん', 'はっけん', 'はっぴょう', 'はってん', 'はいゆう', 'はいけい', 'はいし'
}

_KNOWN_HE_ROOT_WORDS = {
    'へや', 'へび', 'へた', 'へん', 'へいわ', 'へる', 'へんじ', 'へんこう', 'へいき',
    'へいぼん', 'へいじつ', 'へいてん', 'へいさ', 'へいこう', 'へいし'
}


class MultilingualG2P:
    """
    Multilingual Grapheme-to-Phoneme Preprocessor & Router for Kokoro TTS.
    """

    def __init__(self, tokenizer: Optional[Any] = None):
        _ensure_g2p_base()
        self.tokenizer = tokenizer or Tokenizer()
        self.vocab: Set[str] = set(DEFAULT_VOCAB.keys())
        self._init_langdetect()
        self._init_japanese_g2p()

    def _init_langdetect(self) -> None:
        """Seed langdetect for deterministic, consistent language predictions."""
        try:
            import langdetect
            langdetect.DetectorFactory.seed = 0
            self._has_langdetect = True
        except ImportError:
            self._has_langdetect = False
            logger.warning("langdetect not installed; script heuristics will be used.")

    def _init_japanese_g2p(self) -> None:
        """Initialize Japanese morphological analyzer (Janome) or fallback (pykakasi)."""
        self._janome_tagger = None
        self._kakasi = None
        self._jaconv = None

        # Priority 1: Janome (full POS morphological analyzer with phonetic particle resolution)
        try:
            from janome.tokenizer import Tokenizer as JanomeTokenizer
            self._janome_tagger = JanomeTokenizer()
            logger.debug("Janome Japanese morphological analyzer initialized.")
        except ImportError:
            self._janome_tagger = None

        # Priority 2: pykakasi + jaconv (morphological fallback)
        try:
            import pykakasi
            import jaconv
            self._kakasi = pykakasi.kakasi()
            self._jaconv = jaconv
            logger.debug("pykakasi + jaconv Japanese G2P fallback initialized.")
        except ImportError:
            logger.warning("Neither janome nor pykakasi found; Japanese will use basic fallback.")

    @staticmethod
    def canonicalize_lang_code(lang_str: Optional[str], fallback: str = "en-us") -> str:
        """Convert arbitrary language identifiers or names to canonical eSpeak/Kokoro codes."""
        if not lang_str:
            return fallback
        clean = lang_str.strip().lower()
        if clean in ("auto", "auto-detect", "all", "all languages", "🌐 auto-detect language"):
            return "auto"
        return CANONICAL_LANG_MAP.get(clean, clean)

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize input text safely while preserving all international diacritics,
        accents (â, é, è, ê, à, ç, etc.), French contractions (l', d', qu', c', j'),
        and Asian/Devanagari scripts.
        """
        if not text:
            return ""

        # Normalize unicode to NFC form (composed characters so â, é, è are single unified codepoints)
        normalized = unicodedata.normalize("NFC", text)

        # Standardize all apostrophe variants to ASCII single quote (') for perfect French/English elision
        normalized = re.sub(r"[’‘ʼ`´ʹꞌ\u2019\u2018\u02bc]", "'", normalized)

        # Standardize smart quotes and guillemets (« » “ ”)
        normalized = re.sub(r"[“”«»\u201c\u201d\u00ab\u00bb]", '"', normalized)

        # Standardize dashes and hyphens
        normalized = normalized.replace("—", " - ").replace("–", " - ").replace("−", "-")

        # Standardize whitespace while preserving punctuation
        normalized = re.sub(r"[\r\t\f\v]+", " ", normalized)
        normalized = re.sub(r" +", " ", normalized)

        return normalized.strip()

    def _preprocess_japanese_particles(self, text: str) -> str:
        """
        Morphological Japanese text preprocessor that resolves grammatical particles:
        - Topic marker 'は' -> phonetic 'わ' (/wa/)
        - Direction marker 'へ' -> phonetic 'え' (/e/)
        - Compound particles: 'では' -> 'でわ', 'ては' -> 'てわ', 'には' -> 'にわ', 'からは' -> 'からわ', etc.
        - Fixed greetings: 'こんにちは' -> 'こんにちわ', 'こんばんは' -> 'こんばんわ'
        Preserves all word-internal 'ha' and 'he' moras (e.g., 母 haha, 花 hana, 部屋 heya).
        """
        if not text:
            return ""

        processed = text.replace("こんにちは", "こんにち_WA_").replace("こんばんは", "こんばん_WA_")
        processed = re.sub(r"ではありません", "でわありません", processed)
        processed = re.sub(r"ではない", "でわない", processed)
        processed = re.sub(r"ではなかっ", "でわなかっ", processed)
        processed = re.sub(r"では", "でわ", processed)
        processed = re.sub(r"ては", "てわ", processed)
        processed = re.sub(r"には", "にわ", processed)
        processed = re.sub(r"からは", "からわ", processed)
        processed = re.sub(r"までは", "までわ", processed)
        processed = re.sub(r"とは", "とわ", processed)
        processed = re.sub(r"へは", "えわ", processed)
        processed = re.sub(r"よりは", "よりわ", processed)

        return processed

    def japanese_text_to_kokoro_ipa(self, text: str) -> str:
        """
        Direct native Japanese Kanji/Kana to Kokoro IPA G2P conversion with full
        grammatical particle analysis (は -> wa, へ -> e, を -> o).
        Uses Janome POS morphological tagging for phonetic reading extraction,
        and maps directly to Kokoro's IPA vocabulary using the official M2P table.
        Completely eliminates eSpeak-NG English character name leakage.
        """
        if not text:
            return ""

        tokens: List[str] = []

        # 1. Primary Engine: Janome POS Morphological Analyzer
        if self._janome_tagger is not None:
            try:
                for token in self._janome_tagger.tokenize(text):
                    phonetic = token.phonetic
                    if not phonetic or phonetic == "*":
                        phonetic = token.reading if (token.reading and token.reading != "*") else token.surface

                    i = 0
                    while i < len(phonetic):
                        if i + 1 < len(phonetic) and phonetic[i:i+2] in _JA_M2P:
                            tokens.append(_JA_M2P[phonetic[i:i+2]])
                            i += 2
                        elif phonetic[i] in _JA_M2P:
                            tokens.append(_JA_M2P[phonetic[i]])
                            i += 1
                        elif phonetic[i] in _JA_PUNCT:
                            tokens.append(_JA_PUNCT[phonetic[i]])
                            i += 1
                        else:
                            i += 1
                    tokens.append(" ")
                ipa_raw = "".join(tokens)
            except Exception as e:
                logger.warning(f"Janome Japanese G2P error: {e}. Falling back to rule engine.")
                ipa_raw = ""
        else:
            ipa_raw = ""

        # 2. Fallback Engine: pykakasi with rule-based particle preprocessor
        if not ipa_raw and self._kakasi and self._jaconv:
            try:
                processed_text = self._preprocess_japanese_particles(text)
                converted = self._kakasi.convert(processed_text)
                fallback_tokens = []
                for item in converted:
                    orig = item.get("orig", "")
                    hira = item.get("hira", "")

                    if "_WA_" in orig or "_WA_" in hira:
                        hira = hira.replace("_WA_", "わ")
                    elif orig == "は" or hira == "は":
                        hira = "わ"
                    elif orig == "へ" or hira == "へ":
                        hira = "え"
                    elif hira.startswith("は") and len(hira) > 1 and hira not in _KNOWN_HA_ROOT_WORDS and not any(hira.startswith(w) for w in ["はな", "はや", "はじ", "はし", "はる", "はた", "はは"]):
                        hira = "わ" + hira[1:]
                    elif hira.startswith("へ") and len(hira) > 1 and hira not in _KNOWN_HE_ROOT_WORDS and not any(hira.startswith(w) for w in ["へや", "へび", "へた", "へん", "へい", "へる"]):
                        hira = "え" + hira[1:]
                    elif hira.endswith("は") and len(hira) > 1 and hira not in _KNOWN_HA_ROOT_WORDS and orig.endswith("は"):
                        hira = hira[:-1] + "わ"
                    elif hira.endswith("へ") and len(hira) > 1 and hira not in _KNOWN_HE_ROOT_WORDS and orig.endswith("へ"):
                        hira = hira[:-1] + "え"

                    kata = self._jaconv.hira2kata(hira)
                    i = 0
                    while i < len(kata):
                        if i + 1 < len(kata) and kata[i:i+2] in _JA_M2P:
                            fallback_tokens.append(_JA_M2P[kata[i:i+2]])
                            i += 2
                        elif kata[i] in _JA_M2P:
                            fallback_tokens.append(_JA_M2P[kata[i]])
                            i += 1
                        elif kata[i] in _JA_PUNCT:
                            fallback_tokens.append(_JA_PUNCT[kata[i]])
                            i += 1
                        else:
                            i += 1
                    fallback_tokens.append(" ")
                ipa_raw = "".join(fallback_tokens)
            except Exception as e:
                logger.warning(f"Fallback Japanese G2P error: {e}")
                ipa_raw = text

        if not ipa_raw:
            ipa_raw = text

        # Japanese IPA phoneme adjustments: 'u' -> 'ɯ', 'f' -> 'ɸ', 'g' -> 'ɡ'
        ipa_raw = ipa_raw.replace("u", "ɯ").replace("f", "ɸ").replace("g", "ɡ")

        # Strictly filter against Kokoro's DEFAULT_VOCAB
        valid_ipa = "".join(p for p in ipa_raw if p in self.vocab)
        valid_ipa = re.sub(r" +", " ", valid_ipa).strip()
        return valid_ipa

    def detect_language(self, text: str, default_lang: str = "en-us") -> str:
        """
        Identify the primary language of the input text using a fast two-tier architecture:
        1. Fast deterministic Unicode script detection (Korean, Japanese, Chinese, Hindi).
        2. Statistical NLP language identification (French, Spanish, Italian, German, English, etc.).
        """
        clean_text = self.normalize_text(text)
        if not clean_text:
            return default_lang

        # Tier 1: Fast Unicode Script Analysis
        hangul_matches = len(_HANGUL_RE.findall(clean_text))
        kana_matches = len(_KANA_RE.findall(clean_text))
        hanzi_matches = len(_HANZI_RE.findall(clean_text))
        devanagari_matches = len(_DEVANAGARI_RE.findall(clean_text))

        total_chars = max(1, len(re.sub(r"\s+", "", clean_text)))

        # Korean Check
        if hangul_matches / total_chars > 0.15 or hangul_matches >= 3:
            return "ko"

        # Japanese Check (Kana takes precedence over Hanzi)
        if kana_matches / total_chars > 0.1 or kana_matches >= 2:
            return "ja"

        # Chinese Check (Hanzi without Kana)
        if hanzi_matches / total_chars > 0.2 and kana_matches == 0:
            return "cmn"

        # Hindi Check
        if devanagari_matches / total_chars > 0.15 or devanagari_matches >= 3:
            return "hi"

        # Tier 2: Statistical Latin Script Detection via langdetect
        if self._has_langdetect:
            try:
                import langdetect
                # Strip out punctuation and numbers for cleaner detection
                alpha_text = re.sub(r"[^\w\s]", " ", clean_text).strip()
                if len(alpha_text) >= 3:
                    detected = langdetect.detect(alpha_text)
                    canonical = self.canonicalize_lang_code(detected, fallback=default_lang)
                    if canonical != "auto":
                        return canonical
            except Exception as e:
                logger.debug(f"langdetect error: {e}")

        # Fallback to provided default
        return default_lang

    def harmonize_ipa_for_kokoro(self, raw_phonemes: str, lang: str) -> str:
        """
        Harmonize raw eSpeak-NG IPA output with Kokoro-82M vocabulary.
        - Strips eSpeak language tags and fallback character spells (e.g. (en)...(hi)...).
        - Maps Mandarin tone digits (1-4) to Kokoro arrow symbols (→, ↗, ↓, ↘).
        - Replaces unsupported IPA vowels and non-spacing marks with valid equivalents.
        - Filters through Kokoro 114-token DEFAULT_VOCAB.
        """
        phonemes = raw_phonemes

        # 1. Scrub eSpeak language tags and fallback character spelling artifacts
        phonemes = re.sub(r"\([a-zA-Z]{2,4}\)[^\s,.:;!?\"()]*", "", phonemes)

        # 2. Mandarin Tone Mapping
        if lang in ("cmn", "zh", "zh-cn", "zh-tw"):
            for digit, arrow in _MANDARIN_TONE_MAP.items():
                phonemes = phonemes.replace(digit, arrow)

        # 3. General IPA substitutions
        for old_char, new_char in _IPA_SUBSTITUTIONS.items():
            phonemes = phonemes.replace(old_char, new_char)

        # 4. Filter characters through Kokoro's supported vocabulary
        valid_phonemes = "".join(p for p in phonemes if p in self.vocab)
        valid_phonemes = re.sub(r" +", " ", valid_phonemes)
        return valid_phonemes.strip()

    def phonemize(
        self,
        text: str,
        lang: str = "auto",
        default_lang: str = "en-us",
    ) -> Tuple[str, str]:
        """
        Convert multilingual text into Kokoro-compatible IPA phonemes.
        Returns: (harmonized_phonemes, resolved_language_code)
        """
        clean_text = self.normalize_text(text)
        if not clean_text:
            return "", default_lang

        # Resolve language if set to auto
        canonical_lang = self.canonicalize_lang_code(lang, fallback=default_lang)
        if canonical_lang == "auto":
            resolved_lang = self.detect_language(clean_text, default_lang=default_lang)
        else:
            resolved_lang = canonical_lang

        # Japanese: Use direct native Japanese Mora-to-IPA converter with POS particle disambiguation
        if resolved_lang == "ja":
            ja_ipa = self.japanese_text_to_kokoro_ipa(clean_text)
            return ja_ipa, "ja"

        # Other languages: Use Kokoro tokenizer phonemize or language-specific backend
        try:
            raw_phonemes = self.tokenizer.phonemize(clean_text, lang=resolved_lang)
        except Exception as e:
            try:
                raw_phonemes = phonemizer.phonemize(
                    clean_text,
                    language=resolved_lang,
                    backend="espeak",
                    preserve_punctuation=True,
                    with_stress=True,
                )
            except Exception as err2:
                logger.warning(f"Phonemization failed for lang '{resolved_lang}': {err2}. Falling back to '{default_lang}'")
                resolved_lang = default_lang
                raw_phonemes = self.tokenizer.phonemize(clean_text, lang=default_lang)

        harmonized = self.harmonize_ipa_for_kokoro(raw_phonemes, lang=resolved_lang)
        return harmonized, resolved_lang

    @staticmethod
    def parse_dialogue_line(raw_line: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Parse multi-speaker script line with optional language annotations.
        Examples:
            "[Bella]: Hello everyone!" -> speaker="Bella", lang=None, text="Hello everyone!"
            "[Bella (fr)]: Bonjour à tous!" -> speaker="Bella", lang="fr-fr", text="Bonjour à tous!"
            "[Alpha (ja)]: 日本語の勉強" -> speaker="Alpha", lang="ja", text="日本語の勉強"
            "[Alpha [ja]]: 日本語の勉強" -> speaker="Alpha", lang="ja", text="日本語の勉強"
            "[Alpha - ja]: 日本語の勉強" -> speaker="Alpha", lang="ja", text="日本語の勉強"
            "Camille (fr): Bonjour" -> speaker="Camille", lang="fr-fr", text="Bonjour"
            "Just normal narration" -> speaker=None, lang=None, text="Just normal narration"
        """
        line = raw_line.strip()
        if not line:
            return None, None, ""

        # 1. Match bracketed speaker tag: [Speaker (lang)]: Text, [Speaker [lang]]: Text, or [Speaker]: Text
        bracket_match = re.match(r"^\[(.+?)\]\s*:\s*(.*)$", line, re.DOTALL)
        if bracket_match:
            speaker_raw = bracket_match.group(1).strip()
            text = bracket_match.group(2).strip()

            # Parse speaker_raw for language qualifier: e.g. "Alpha (ja)", "Alpha [ja]", "Alpha - ja", "Alpha, ja"
            qual_match = re.search(r"[\(\[\-,]\s*([a-zA-Z_\-]+)\s*[\)\]]?$", speaker_raw)
            if qual_match:
                potential_lang = qual_match.group(1).strip()
                canonical_lang = MultilingualG2P.canonicalize_lang_code(potential_lang, fallback="")
                if canonical_lang and canonical_lang != "auto":
                    speaker_clean = speaker_raw[:qual_match.start()].strip(" ([- ,")
                    return (speaker_clean if speaker_clean else speaker_raw, canonical_lang, text)

            return speaker_raw, None, text

        # 2. Match unbracketed speaker tag: Speaker (lang): Text or Speaker: Text
        colon_match = re.match(
            r"^([a-zA-Z0-9_\u00C0-\u017F\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]{2,30}(?:\s*[\(\[][a-zA-Z_\-]+[\)\]])?)\s*:\s+(.*)$",
            line,
            re.DOTALL,
        )
        if colon_match:
            speaker_raw = colon_match.group(1).strip()
            text = colon_match.group(2).strip()

            qual_match = re.search(r"[\(\[\-,]\s*([a-zA-Z_\-]+)\s*[\)\]]?$", speaker_raw)
            if qual_match:
                potential_lang = qual_match.group(1).strip()
                canonical_lang = MultilingualG2P.canonicalize_lang_code(potential_lang, fallback="")
                if canonical_lang and canonical_lang != "auto":
                    speaker_clean = speaker_raw[:qual_match.start()].strip(" ([- ,")
                    return (speaker_clean if speaker_clean else speaker_raw, canonical_lang, text)

            return speaker_raw, None, text

        return None, None, line
