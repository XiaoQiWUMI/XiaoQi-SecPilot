"""Knowledge base loader — reads YAML knowledge files and builds searchable index."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


class KnowledgeEntry:
    """A single knowledge entry with metadata for matching."""

    def __init__(
        self,
        title: str,
        content: str,
        category: str,
        tags: List[str] = None,
        keywords: List[str] = None,
        severity: str = "info",
        references: List[str] = None,
    ):
        self.title = title
        self.content = content
        self.category = category
        self.tags = tags or []
        self.keywords = keywords or []
        self.severity = severity
        self.references = references or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "keywords": self.keywords,
            "severity": self.severity,
            "references": self.references,
        }

    def searchable_text(self) -> str:
        """Return all searchable text for fuzzy matching."""
        parts = [
            self.title,
            self.content,
            self.category,
            " ".join(str(t) for t in self.tags),
            " ".join(str(k) for k in self.keywords),
        ]
        return " ".join(part.lower() for part in parts if part)


class KnowledgeBase:
    """In-memory knowledge base with fast lookup capabilities."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.entries: List[KnowledgeEntry] = []
        self._index: Dict[str, List[int]] = {}  # tag/keyword → entry indices
        self._category_index: Dict[str, List[int]] = {}

        if knowledge_dir is None:
            # loader.py lives inside the knowledge/ directory itself
            knowledge_dir = os.path.dirname(__file__)
        self.knowledge_dir = Path(knowledge_dir)

    def load_all(self) -> int:
        """Load all YAML knowledge files from the knowledge directory."""
        self.entries.clear()
        self._index.clear()
        self._category_index.clear()

        yaml_files = list(self.knowledge_dir.rglob("*.yaml")) + list(
            self.knowledge_dir.rglob("*.yml")
        )

        for yaml_file in sorted(yaml_files):
            self._load_file(yaml_file)

        self._rebuild_index()
        return len(self.entries)

    def _load_file(self, filepath: Path):
        """Load a single YAML knowledge file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: failed to load {filepath}: {e}")
            return

        if not data:
            return

        # Determine category from file path relative to knowledge dir
        try:
            rel = filepath.relative_to(self.knowledge_dir)
            category = str(rel.parent) if rel.parent != Path(".") else "general"
        except ValueError:
            category = "general"

        entries = data if isinstance(data, list) else [data]

        for item in entries:
            if not item or not isinstance(item, dict):
                continue
            if "title" not in item or "content" not in item:
                continue

            entry = KnowledgeEntry(
                title=item.get("title", ""),
                content=item.get("content", ""),
                category=item.get("category", category),
                tags=item.get("tags", []),
                keywords=item.get("keywords", []),
                severity=item.get("severity", "info"),
                references=item.get("references", []),
            )
            self.entries.append(entry)

    def _rebuild_index(self):
        """Rebuild the keyword/tag index for fast lookup."""
        for idx, entry in enumerate(self.entries):
            # Index by category
            cat = entry.category.lower()
            if cat not in self._category_index:
                self._category_index[cat] = []
            self._category_index[cat].append(idx)

            # Index by tags and keywords
            for token in entry.tags + entry.keywords:
                token_lower = str(token).lower().strip()
                if not token_lower:
                    continue
                if token_lower not in self._index:
                    self._index[token_lower] = []
                if idx not in self._index[token_lower]:
                    self._index[token_lower].append(idx)

    def get_categories(self) -> List[str]:
        """Return all available categories."""
        return sorted(self._category_index.keys())

    def get_stats(self) -> Dict[str, int]:
        """Return statistics about the knowledge base."""
        return {
            "total_entries": len(self.entries),
            "total_categories": len(self._category_index),
            "total_tags": len(self._index),
        }

    def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Return all entries in a category."""
        indices = self._category_index.get(category.lower(), [])
        return [self.entries[i] for i in indices]

    def get_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        """Return all entries matching a tag."""
        indices = self._index.get(tag.lower().strip(), [])
        return [self.entries[i] for i in indices]
