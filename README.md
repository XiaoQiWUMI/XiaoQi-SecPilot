<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-lightgrey.svg" alt="Platform">
</p>

# 🛡️ XiaoQi SecPilot
### People with evil intent can do evil things without lying. And not all liars are evil.

**AI-Driven Security Knowledge Copilot — Instant lookup of pentesting techniques, bypass methods, and attack methodologies.**

SecPilot is an offline-first CLI tool that puts a comprehensive security knowledge base at your fingertips. When you're in the middle of a penetration test and need to recall a bypass technique, default credential, or attack vector — just ask SecPilot.

---

## ✨ Features

- 🔍 **Multi-Strategy Search** — Keyword, tag, substring, and fuzzy matching (Chinese + English)
- 📚 **Curated Knowledge Base** — 20+ hand-crafted knowledge entries covering real-world pentesting workflows
- 🏷 **7 Searchable Categories** — WAF bypass, auth attacks, injection, recon, default creds, methodology, exploitation
- 🎨 **Rich Terminal Output** — Syntax-highlighted panels with severity badges and references
- ⚡ **Offline-First** — No API calls, no internet required; all knowledge is local YAML
- 🔧 **Extensible** — Add your own knowledge via simple YAML files
- 🐍 **Python 3.9+** — Single `pip install`

---

## 📦 Installation

```bash
# Clone
git clone https://github.com/XiaoQiWUMI/XiaoQi-SecPilot.git
cd XiaoQi-SecPilot

# Install
pip install -e .

# Or from PyPI (coming soon)
# pip install xiaoqi-sec-pilot
```

---

## 🚀 Quick Start

```bash
# Search the knowledge base
secpilot search "403 bypass"
secpilot search "jwt attack"
secpilot search "sql注入绕过"

# Browse a category
secpilot category waf_bypass
secpilot category auth_attack
secpilot category exploitation

# List all categories
secpilot list

# Create your own knowledge files
secpilot init
```

---

## 📂 Knowledge Categories

| Category | Description | Entries |
|----------|-------------|---------|
| `waf_bypass` | WAF bypass: 403, SQLi encoding, XSS event handlers | 3 |
| `auth_attack` | JWT (10 vectors), OAuth (10 vectors), session/cookie | 3 |
| `injection` | SQLi, SSTI, XXE, Command Injection, CRLF | 5 |
| `recon` | Subdomain, JS analysis, parameter discovery, directory brute | 4 |
| `exploitation` | File upload (7-layer), deserialization, SSRF, IDOR, race condition, CORS, WebSocket | 7 |
| `default_creds` | Web servers, databases, network devices, educational systems | 3 |
| `methodology` | 6-phase workflow, scoring standards, report template | 3 |

---

## 🎯 Usage Examples

### Find a WAF bypass technique
```bash
$ secpilot search "403绕过"

#1  score: 90  (tag_match)
┌─ 403 Bypass — Path Confusion Techniques [HIGH] ───────────────────┐
│ 📂 waf_bypass  🏷  #403 #bypass #path-traversal #http-headers     │
│                                                                    │
│ ## Path Obfuscation (30+ methods)                                  │
│ ### URL Encoding Tricks                                            │
│ /admin → /%61dmin                                                  │
│ /admin → /admin/. (trailing dot)                                   │
│ /admin → /admin;/ (semicolon suffix)                               │
│ ...                                                                │
│ 🔗 https://book.hacktricks.xyz/.../403-and-401-bypasses           │
└────────────────────────────────────────────────────────────────────┘
```

### Look up default credentials
```bash
$ secpilot search "默认口令 tomcat"

#1  score: 92  (substring_match)
┌─ Web Server Management Defaults [HIGH] ───────────────────────────┐
│ 📂 default_creds                                                   │
│                                                                    │
│ ### Tomcat                                                         │
│ | admin | admin |                                                  │
│ | tomcat | tomcat |                                                │
│ ...                                                                │
└────────────────────────────────────────────────────────────────────┘
```

### Browse all exploitation techniques
```bash
$ secpilot category exploitation
# Shows all 7 entries: file upload, deserialization, SSRF, IDOR, etc.
```

---

## 🔧 Adding Your Own Knowledge

Create a YAML file in the `knowledge/` directory:

```yaml
# knowledge/custom/ssh_tricks.yaml
- title: "SSH Lateral Movement Techniques"
  content: |
    ## SSH Tunneling
    - Local forward: ssh -L 8080:internal:80 user@jump
    - Dynamic SOCKS: ssh -D 1080 user@jump
    - Remote forward: ssh -R 8080:localhost:80 user@jump

    ## SSH Key Hijacking
    - Look for ~/.ssh/id_rsa
    - Forward SSH agent: ssh -A user@jump
    - Agent socket hijacking: /tmp/ssh-*/agent.*
  tags: [ssh, lateral-movement, tunneling, pivoting]
  keywords: [ssh隧道, 横向移动, 端口转发, 内网穿透]
  severity: medium
  references:
    - https://book.hacktricks.xyz/network-services-pentesting/pentesting-ssh

- title: "Your Second Entry"
  content: |
    More knowledge here...
  tags: [example]
  severity: info
```

Then:
```bash
# Use custom knowledge dir
export SECPILOT_KNOWLEDGE_DIR=/path/to/your/knowledge
secpilot search "ssh tunneling"
```

---

## 🏗 Architecture

```
sec_pilot/
├── __init__.py
├── cli.py              # Click-based CLI (search, category, list, init)
├── engine.py           # Multi-strategy search engine (tag + substring + fuzzy)
├── knowledge/
│   ├── __init__.py
│   ├── loader.py       # YAML knowledge loader & index builder
│   ├── waf_bypass/     # 30+ bypass techniques
│   ├── auth_attack/    # JWT, OAuth, session attacks
│   ├── injection/      # SQLi, SSTI, XXE, CMDi, CRLF
│   ├── recon/          # Subdomain, JS analysis, param discovery
│   ├── default_creds/  # Common default passwords
│   ├── methodology/    # Workflows, scoring, report templates
│   └── exploitation/   # Upload, deser, SSRF, IDOR, CORS, WebSocket
└── utils/
    ├── __init__.py
    └── formatter.py    # Rich terminal output formatting
```

---

## 🤝 Contributing

Contributions welcome! Especially:

- **New knowledge entries** — PR your favorite bypass/technique via YAML
- **New categories** — Open an issue to discuss
- **Improved matching** — Help make the search engine smarter
- **Translations** — English ↔ Chinese refinement

---

## 📜 License

MIT © 2026 [XiaoQiWUMI](https://github.com/XiaoQiWUMI)

---

## 🙏 Acknowledgments

Built with:
- [Rich](https://github.com/Textualize/rich) — Beautiful terminal rendering
- [Click](https://click.palletsprojects.com/) — CLI framework
- [TheFuzz](https://github.com/seatgeek/thefuzz) — Fuzzy string matching
- Years of real-world pentesting experience distilled into knowledge

---

<p align="center">
  <sub>Made with ❤️ by XiaoQiWUMI | "代码放松，生活温和"</sub>
</p>
