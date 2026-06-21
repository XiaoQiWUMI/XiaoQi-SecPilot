"""Core search & matching engine — multi-strategy lookup with fuzzy scoring."""

import re
from typing import List, Tuple, Optional
from thefuzz import fuzz, process

from .knowledge.loader import KnowledgeBase, KnowledgeEntry


class SearchResult:
    """A single search result with relevance score."""

    def __init__(self, entry: KnowledgeEntry, score: float, strategy: str):
        self.entry = entry
        self.score = score
        self.strategy = strategy

    def __repr__(self):
        return f"SearchResult(title={self.entry.title!r}, score={self.score:.1f}, strategy={self.strategy!r})"


class SecPilotEngine:
    """Multi-strategy security knowledge search engine."""

    # Strategy keywords for quick intent detection
    CATEGORY_KEYWORDS = {
        "waf_bypass": ["waf", "bypass", "绕过", "防火墙", "cloudflare", "akamai", "阿里云waf", "modsecurity"],
        "auth_attack": ["auth", "认证", "login", "登录", "jwt", "oauth", "sso", "session", "cookie", "token", "鉴权", "otp", "mfa", "2fa"],
        "injection": ["sqli", "xss", "注入", "ssti", "模板注入", "命令注入", "rce", "xxe", "ldap", "crlf", "injection"],
        "recon": ["recon", "信息收集", "子域名", "subdomain", "port", "端口", "目录", "directory", "fuzz", "js分析", "指纹", "fingerprint"],
        "default_creds": ["默认口令", "default password", "admin", "弱口令", "weak password", "默认密码"],
        "methodology": ["方法论", "methodology", "流程", "checklist", "测试顺序", "checklist", "报告", "report"],
        "exploitation": ["利用", "exploit", "poc", "rce链", "反弹shell", "reverse shell", "payload", "文件上传", "upload", "webshell", "权限提升", "privilege"],
    }

    # Common Chinese-English keyword mapping
    LANG_MAP = {
        "注入": "injection",
        "绕过": "bypass",
        "绕过技术": "bypass",
        "上传": "upload",
        "文件上传": "file upload",
        "反序列化": "deserialization",
        "反序列": "deserialization",
        "包含": "lfi",
        "文件包含": "lfi",
        "文件读取": "file read",
        "路径穿越": "path traversal",
        "目录遍历": "directory traversal",
        "重定向": "open redirect",
        "开放重定向": "open redirect",
        "csrf": "csrf",
        "跨站请求伪造": "csrf",
        "ssrf": "ssrf",
        "服务器端请求伪造": "ssrf",
        "竞态条件": "race condition",
        "竞态": "race condition",
        "批量分配": "mass assignment",
        "批量": "mass assignment",
        "idor": "idor",
        "越权": "idor",
        "水平越权": "idor",
        "垂直越权": "privilege escalation",
        "信息泄露": "information disclosure",
        "敏感信息": "information disclosure",
        "口令": "password",
        "弱密码": "weak password",
        "默认密码": "default password",
        "ssti": "ssti",
        "模板注入": "ssti",
        "命令注入": "command injection",
        "命令执行": "command injection",
        "代码执行": "code execution",
        "xss": "xss",
        "跨站脚本": "xss",
        "sql注入": "sql injection",
        "sqli": "sql injection",
        "xxe": "xxe",
        "xml外部实体": "xxe",
        "ldap注入": "ldap injection",
        "ldap": "ldap injection",
        "crlf": "crlf",
        "换行注入": "crlf",
        "响应分割": "response splitting",
        "cors": "cors",
        "跨域": "cors",
        "jsonp": "jsonp",
        "websocket": "websocket",
        "graphql": "graphql",
        "403": "403 bypass",
        "401": "auth bypass",
        "登录框": "login",
        "登录": "login",
        "注册": "register",
        "密码重置": "password reset",
        "忘记密码": "password reset",
        "验证码": "captcha",
        "短信": "sms",
        "邮件": "email",
    }

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 30.0,
        category: Optional[str] = None,
    ) -> List[SearchResult]:
        """Multi-strategy search: keyword → tag → fuzzy. Returns top_k results."""

        query_lower = query.lower().strip()
        seen_ids = set()
        results: List[SearchResult] = []

        # Strategy 1: Keyword match in tags/index (exact)
        tag_results = self._search_by_tags(query_lower)
        for entry, score in tag_results:
            if id(entry) not in seen_ids:
                seen_ids.add(id(entry))
                results.append(SearchResult(entry, score, "tag_match"))

        # Strategy 2: Keyword in content (substring)
        substr_results = self._search_by_substring(query_lower)
        for entry, score in substr_results:
            if id(entry) not in seen_ids:
                seen_ids.add(id(entry))
                results.append(SearchResult(entry, score, "substring_match"))

        # Strategy 3: Fuzzy matching on searchable text
        fuzzy_results = self._search_by_fuzzy(query_lower)
        for entry, score in fuzzy_results:
            if id(entry) not in seen_ids:
                seen_ids.add(id(entry))
                results.append(SearchResult(entry, score, "fuzzy_match"))

        # Filter by category if specified
        if category:
            results = [r for r in results if r.entry.category.lower() == category.lower()]

        # Filter by min score, sort, return top_k
        results = [r for r in results if r.score >= min_score]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _detect_categories(self, query: str) -> List[str]:
        """Detect which categories the query likely targets."""
        matched = []
        query_lower = query.lower()
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                matched.append(cat)
        return matched

    def _expand_query(self, query: str) -> str:
        """Expand Chinese terms to English equivalents for broader matching."""
        expanded = query
        for cn, en in self.LANG_MAP.items():
            if cn in query.lower():
                expanded += " " + en
        return expanded

    def _search_by_tags(self, query: str) -> List[Tuple[KnowledgeEntry, float]]:
        """Exact/prefixed tag matching."""
        results = []
        query_tokens = set(query.lower().split())
        for tag, indices in self.kb._index.items():
            # If query contains the tag, or tag contains query tokens
            if tag in query or any(token in tag or tag in token for token in query_tokens):
                for idx in indices:
                    if idx < len(self.kb.entries):
                        results.append((self.kb.entries[idx], 90.0))
        return results

    def _search_by_substring(self, query: str) -> List[Tuple[KnowledgeEntry, float]]:
        """Substring match in content and title."""
        results = []
        query_tokens = query.split()
        for entry in self.kb.entries:
            text = entry.searchable_text()
            # Score based on how many tokens match
            matched = sum(1 for t in query_tokens if t in text)
            if matched > 0:
                score = 60.0 + (matched / max(len(query_tokens), 1)) * 30.0
                results.append((entry, score))
        return results

    def _search_by_fuzzy(self, query: str) -> List[Tuple[KnowledgeEntry, float]]:
        """Fuzzy match using Levenshtein distance against entry titles and keywords."""
        results = []
        expanded = self._expand_query(query)

        # Collect all titles for fuzzy matching
        titles = [entry.title.lower() for entry in self.kb.entries]

        # Use thefuzz to extract top matches
        title_matches = process.extract(
            query, titles, scorer=fuzz.token_sort_ratio, limit=min(10, len(titles))
        )

        for matched_title, score in title_matches:
            if score < 35:
                continue
            for entry in self.kb.entries:
                if entry.title.lower() == matched_title:
                    results.append((entry, score))
                    break

        # Also fuzzy match on expanded query against all searchable text
        for entry in self.kb.entries:
            text = entry.searchable_text()
            score = fuzz.token_sort_ratio(expanded, text)
            if score >= 50:
                results.append((entry, score))

        return results

    def search_by_category(self, category: str) -> List[SearchResult]:
        """Return all entries in a given category."""
        entries = self.kb.get_by_category(category)
        return [SearchResult(e, 100.0, "category") for e in entries]

    def list_categories(self) -> List[str]:
        """List all available knowledge categories."""
        return self.kb.get_categories()

    def get_hot_topics(self, limit: int = 10) -> List[str]:
        """Return trending/popular topics based on tag frequency."""
        tag_counts = {}
        for tag, indices in self.kb._index.items():
            if len(tag) > 2:  # skip very short tags
                tag_counts[tag] = len(indices)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in sorted_tags[:limit]]
