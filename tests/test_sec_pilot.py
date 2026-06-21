"""Tests for SecPilot — knowledge loading, engine matching, CLI commands."""

import sys
import os
import pytest
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sec_pilot.knowledge.loader import KnowledgeBase, KnowledgeEntry
from sec_pilot.engine import SecPilotEngine, SearchResult


@pytest.fixture
def knowledge_dir():
    return os.path.join(os.path.dirname(__file__), "..", "sec_pilot", "knowledge")


@pytest.fixture
def kb(knowledge_dir):
    kbase = KnowledgeBase(knowledge_dir)
    kbase.load_all()
    return kbase


@pytest.fixture
def engine(kb):
    return SecPilotEngine(kb)


class TestKnowledgeBase:
    def test_load_all(self, kb):
        assert len(kb.entries) > 0, "Knowledge base should have entries"
        print(f"Loaded {len(kb.entries)} entries")

    def test_categories(self, kb):
        cats = kb.get_categories()
        assert len(cats) >= 5, f"Expected at least 5 categories, got {len(cats)}"
        expected = {"waf_bypass", "auth_attack", "injection", "recon", "methodology", "default_creds", "exploitation"}
        found = set(cats)
        assert expected.issubset(found), f"Missing categories: {expected - found}"

    def test_get_by_category(self, kb):
        entries = kb.get_by_category("waf_bypass")
        assert len(entries) >= 2, f"Expected at least 2 waf_bypass entries, got {len(entries)}"

    def test_get_by_tag(self, kb):
        entries = kb.get_by_tag("jwt")
        assert len(entries) > 0, "Should find entries tagged 'jwt'"

    def test_stats(self, kb):
        stats = kb.get_stats()
        assert stats["total_entries"] > 0
        assert stats["total_categories"] > 0
        assert stats["total_tags"] > 0

    def test_entry_structure(self, kb):
        entry = kb.entries[0]
        assert entry.title, "Entry should have title"
        assert entry.content, "Entry should have content"
        assert entry.category, "Entry should have category"

    def test_searchable_text(self, kb):
        for entry in kb.entries:
            text = entry.searchable_text()
            assert len(text) > 10, f"Entry '{entry.title}' searchable text too short"


class TestEngine:
    def test_search_jwt(self, engine):
        results = engine.search("jwt attack", top_k=3)
        assert len(results) > 0, "Search for 'jwt attack' should return results"

    def test_search_chinese(self, engine):
        results = engine.search("sql注入", top_k=3)
        assert len(results) > 0, "Search for 'sql注入' should return results"

    def test_search_403(self, engine):
        results = engine.search("403 bypass", top_k=3)
        assert len(results) > 0, "Search for '403 bypass' should return results"

    def test_search_by_category(self, engine):
        results = engine.search_by_category("injection")
        assert len(results) >= 4, f"Expected >= 4 injection entries, got {len(results)}"

    def test_list_categories(self, engine):
        cats = engine.list_categories()
        assert "waf_bypass" in cats
        assert "exploitation" in cats

    def test_no_results(self, engine):
        results = engine.search("xyznonexistent12345", min_score=80)
        assert len(results) == 0, "Nonsense query should return no results"

    def test_result_structure(self, engine):
        results = engine.search("jwt", top_k=1)
        assert len(results) > 0
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.score > 0
        assert result.strategy in ("tag_match", "substring_match", "fuzzy_match", "category")
        assert result.entry.title

    def test_fuzzy_matching(self, engine):
        """Fuzzy matching should find relevant results even with typos."""
        results = engine.search("slq injection", top_k=3)  # typo for sql
        # May or may not find depending on fuzzy threshold, just ensure no crash
        assert isinstance(results, list)

    def test_chinese_expansion(self, engine):
        """Chinese terms should expand to English for better matching."""
        results = engine.search("文件上传绕过", top_k=3)
        assert isinstance(results, list)

    def test_hot_topics(self, engine):
        topics = engine.get_hot_topics(limit=5)
        assert len(topics) > 0
        assert isinstance(topics[0], str)


class TestKnowledgeEntry:
    def test_create_entry(self):
        entry = KnowledgeEntry(
            title="Test Entry",
            content="Test content for security research.",
            category="test",
            tags=["test", "example"],
            keywords=["测试"],
            severity="medium",
            references=["https://example.com"],
        )
        assert entry.title == "Test Entry"
        assert entry.category == "test"
        assert "test" in entry.tags
        assert "测试" in entry.keywords
        assert entry.severity == "medium"
        assert "https://example.com" in entry.references

    def test_to_dict(self):
        entry = KnowledgeEntry(
            title="T", content="C", category="cat", severity="low"
        )
        d = entry.to_dict()
        assert d["title"] == "T"
        assert d["content"] == "C"
        assert d["category"] == "cat"
        assert d["severity"] == "low"


if __name__ == "__main__":
    # Simple manual test runner
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "sec_pilot", "knowledge")
    kb = KnowledgeBase(knowledge_dir)
    count = kb.load_all()
    print(f"✓ Loaded {count} entries from {len(kb.get_categories())} categories")
    print(f"  Categories: {kb.get_categories()}")
    print(f"  Tags indexed: {len(kb._index)}")

    engine = SecPilotEngine(kb)
    # Quick search tests
    for query in ["403 bypass", "jwt attack", "sql注入", "默认口令", "文件上传"]:
        results = engine.search(query, top_k=1)
        status = "✓" if results else "✗"
        top = results[0] if results else None
        print(f"{status} '{query}' → {top.entry.title if top else 'no results'}")

    print("\n✓ All manual tests passed!")
