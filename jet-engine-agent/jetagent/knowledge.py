"""Recherche documentaire locale dans la base de connaissances (BM25 simplifié).

Sans dépendance externe : les fichiers Markdown du dossier `knowledge/` sont
découpés en sections (titres `#`/`##`), indexés par mots, et interrogés par un
score BM25. Suffisant pour une base de quelques dizaines de documents ; pour
une base volumineuse, remplacer par un index vectoriel.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_\-\.]*")
_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "a", "au", "aux",
    "pour", "par", "sur", "dans", "est", "sont", "que", "qui", "ce", "ces", "se",
    "ou", "ne", "pas", "plus", "avec", "the", "of", "and", "to", "in", "is", "d", "l",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(_normalize(text))
    return [t.strip(".-") for t in tokens if t.strip(".-") and t not in _STOPWORDS]


@dataclass
class Section:
    source: str
    title: str
    text: str

    def preview(self, limit: int = 1500) -> str:
        return self.text if len(self.text) <= limit else self.text[:limit] + " […]"


class KnowledgeBase:
    def __init__(self, directory: Path = KNOWLEDGE_DIR):
        self.directory = directory
        self.sections: list[Section] = []
        self._tf: list[Counter] = []
        self._df: Counter = Counter()
        self._avg_len = 1.0
        self.reload()

    # ---- indexation --------------------------------------------------------
    def reload(self) -> None:
        self.sections = []
        for path in sorted(self.directory.glob("*.md")):
            self.sections.extend(_split_sections(path))
        self._tf = [Counter(tokenize(s.title + " " + s.text)) for s in self.sections]
        self._df = Counter()
        for tf in self._tf:
            self._df.update(tf.keys())
        lengths = [sum(tf.values()) for tf in self._tf]
        self._avg_len = (sum(lengths) / len(lengths)) if lengths else 1.0

    # ---- recherche -----------------------------------------------------------
    def search(self, query: str, top_k: int = 3) -> list[tuple[float, Section]]:
        q = tokenize(query)
        if not q or not self.sections:
            return []
        n = len(self.sections)
        k1, b = 1.5, 0.75
        scored: list[tuple[float, Section]] = []
        for section, tf in zip(self.sections, self._tf):
            dl = sum(tf.values())
            score = 0.0
            for term in q:
                if term not in tf:
                    continue
                idf = math.log(1 + (n - self._df[term] + 0.5) / (self._df[term] + 0.5))
                freq = tf[term]
                score += idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * dl / self._avg_len))
            if score > 0:
                scored.append((score, section))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]

    def list_documents(self) -> list[str]:
        return sorted({s.source for s in self.sections})


def _split_sections(path: Path) -> list[Section]:
    sections: list[Section] = []
    current_title = path.stem
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            sections.append(Section(source=path.name, title=current_title, text=body))

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            flush()
            buffer = []
            current_title = line.lstrip("#").strip()
        else:
            buffer.append(line)
    flush()
    return sections
