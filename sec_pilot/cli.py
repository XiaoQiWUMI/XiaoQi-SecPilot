"""CLI — interactive command-line interface for SecPilot."""

import os
import sys
import click
from pathlib import Path
from typing import Optional

from .knowledge.loader import KnowledgeBase
from .engine import SecPilotEngine
from .utils.formatter import (
    banner,
    format_results,
    format_entry,
    format_category_list,
    console,
)


# Global instances (lazy init)
_kb: Optional[KnowledgeBase] = None
_engine: Optional[SecPilotEngine] = None


def get_knowledge_dir() -> Path:
    """Resolve knowledge directory: env var > built-in > cwd."""
    env_dir = os.environ.get("SECPILOT_KNOWLEDGE_DIR")
    if env_dir:
        return Path(env_dir)

    builtin = Path(__file__).parent / "knowledge"
    if builtin.exists():
        return builtin

    return Path.cwd()


def init_engine() -> SecPilotEngine:
    """Initialize knowledge base and engine (cached)."""
    global _kb, _engine
    if _engine is not None:
        return _engine

    knowledge_dir = get_knowledge_dir()
    _kb = KnowledgeBase(str(knowledge_dir))
    count = _kb.load_all()

    if count == 0:
        console.print(
            f"[yellow]⚠  No knowledge files found in {knowledge_dir}[/yellow]\n"
            "Run [cyan]secpilot --init[/cyan] to create example knowledge files."
        )

    _engine = SecPilotEngine(_kb)
    return _engine


@click.group()
@click.version_option(version="1.0.0", prog_name="SecPilot")
@click.pass_context
def cli(ctx):
    """XiaoQi SecPilot — AI-driven security knowledge copilot.

    Instant lookup of penetration testing techniques, bypass methods,
    WAF fingerprints, default credentials, and attack methodologies.

    \b
    Examples:
      secpilot search "403 bypass"
      secpilot search "sql注入"
      secpilot search "jwt attack"
      secpilot list
      secpilot category waf_bypass
    """
    ctx.ensure_object(dict)


@cli.command()
@click.argument("query")
@click.option("-k", "--top", default=5, help="Number of results (default: 5)")
@click.option("-c", "--category", default=None, help="Limit to specific category")
@click.option(
    "-m", "--min-score", default=30.0, help="Minimum relevance score (default: 30)"
)
def search(query: str, top: int, category: Optional[str], min_score: float):
    """Search the security knowledge base.

    QUERY can be in Chinese or English. Multi-strategy matching combines
    keyword, tag, substring, and fuzzy matching for best results.
    """
    engine = init_engine()
    banner()

    console.print(f"[dim]Searching for:[/dim] [bold]{query}[/bold]\n")

    results = engine.search(
        query=query,
        top_k=top,
        min_score=min_score,
        category=category,
    )

    format_results(results, query)


@cli.command()
@click.argument("category_name")
@click.option("-k", "--top", default=20, help="Max entries to show (default: 20)")
def category(category_name: str, top: int):
    """Browse all entries in a CATEGORY.

    Available categories: waf_bypass, auth_attack, injection, recon,
    default_creds, methodology, exploitation
    """
    engine = init_engine()
    banner()

    categories = engine.list_categories()
    if category_name not in categories:
        console.print(
            f"[yellow]Unknown category: {category_name}[/yellow]\n"
            f"Available: {', '.join(categories)}"
        )
        return

    results = engine.search_by_category(category_name)

    if not results:
        console.print(f"[dim]No entries in category: {category_name}[/dim]")
        return

    console.print(
        f"\n[bold]📂 {category_name}[/bold] [dim]({len(results)} entries)[/dim]\n"
    )

    for result in results[:top]:
        console.print(format_entry(result.entry))
        console.print()

    if len(results) > top:
        console.print(
            f"[dim]... and {len(results) - top} more entries. "
            f"Use [cyan]-k {len(results)}[/cyan] to show all.[/dim]"
        )


@cli.command()
def list():
    """List all knowledge categories and statistics."""
    engine = init_engine()
    banner()

    stats = engine.kb.get_stats()
    format_category_list(engine.list_categories(), stats)

    console.print("\n[dim]Use [cyan]secpilot category <name>[/cyan] to browse entries[/dim]")


@cli.command()
@click.option("-d", "--dir", "target_dir", default=None, help="Output directory")
def init(target_dir: Optional[str]):
    """Initialize example knowledge files in the given directory."""
    if target_dir is None:
        target_dir = os.getcwd()

    target = Path(target_dir) / "knowledge"
    target.mkdir(parents=True, exist_ok=True)

    # Create example knowledge files
    examples = {
        "waf_bypass": """# WAF Bypass Techniques
# Add your WAF bypass knowledge entries below

- title: "Cloudflare WAF Bypass — Chunked Transfer"
  content: |
    ## Technique
    Use chunked transfer encoding to split payload across chunks,
    making signature-based detection harder.

    ## Steps
    1. Enable chunked transfer encoding in Burp (uncheck 'Content-Length' auto-update)
    2. Split the payload across multiple chunks
    3. Add comments or whitespace between chunks

    ## Example
    ```
    POST /api HTTP/1.1
    Transfer-Encoding: chunked

    3
    sel
    5
    ect+1
    1
    ,
    ...
    ```

    ## Applicable WAFs
    - Cloudflare (certain configs)
    - ModSecurity (older versions)
    - Some Alibaba Cloud WAF configs
  tags: [waf, bypass, cloudflare, chunked, http]
  keywords: [waf绕过, 分块传输, cloudflare绕过]
  severity: high
  references:
    - https://book.hacktricks.xyz/pentesting-web/waf-bypass
""",
        "default_creds": """# Default Credentials Database
# Add default passwords for common systems

- title: "Tomcat Manager Default Credentials"
  content: |
    ## Default Credentials

    | Username | Password |
    |----------|----------|
    | admin | admin |
    | tomcat | tomcat |
    | both | tomcat |
    | role1 | role1 |
    | root | root |

    ## Attack Path
    1. Visit `/manager/html`
    2. Try default credentials
    3. If successful, deploy WAR file for RCE

    ## Mitigation
    - Remove/restrict manager app in production
    - Change default credentials
    - Use strong passwords
  tags: [tomcat, default-password, manager, rce, java]
  keywords: [tomcat默认口令, tomcat弱密码, manager登录]
  severity: high
  references:
    - https://tomcat.apache.org/tomcat-9.0-doc/manager-howto.html
""",
        "methodology": """# Penetration Testing Methodology

- title: "Web Application Testing Checklist"
  content: |
    ## Recon Phase
    1. Subdomain enumeration (subfinder, amass, crt.sh)
    2. Port scanning (nmap, masscan)
    3. Technology fingerprinting (Wappalyzer, WhatWeb)
    4. Directory brute-forcing (ffuf, dirsearch)
    5. JS endpoint extraction (LinkFinder, katana)

    ## Attack Phase
    1. Authentication testing (default creds, weak passwords, JWT attacks)
    2. Injection testing (SQLi, XSS, SSTI, XXE, command injection)
    3. Access control testing (IDOR, privilege escalation, CORS)
    4. File handling (upload bypass, path traversal, LFI/RFI)
    5. Business logic testing (race conditions, mass assignment)

    ## Post-Exploitation
    1. Report findings with reproduction steps
    2. CVSS scoring
    3. Provide remediation advice
  tags: [methodology, checklist, pentesting, workflow, recon, attack]
  keywords: [渗透测试流程, 挖洞流程, 测试顺序, checklist]
  severity: info
""",
    }

    for category_name, content in examples.items():
        cat_dir = target / category_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        filepath = cat_dir / "entries.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]✓[/green] Created {filepath}")

    console.print(f"\n[bold cyan]Knowledge files created in {target}[/bold cyan]")
    console.print("Edit the YAML files to add your own knowledge entries.")
    console.print(
        f"Set [dim]SECPILOT_KNOWLEDGE_DIR={target}[/dim] to use custom knowledge dir."
    )


def main():
    """Entry point for console_scripts."""
    # Show banner on bare invocation
    if len(sys.argv) == 1:
        banner()
        console.print(
            "\n[dim]Usage:[/dim] [cyan]secpilot [command] [options][/cyan]\n"
            "\n[bold]Commands:[/bold]\n"
            "  [cyan]search[/cyan]  <query>    Search the knowledge base\n"
            "  [cyan]category[/cyan] <name>    Browse a category\n"
            "  [cyan]list[/cyan]               List all categories\n"
            "  [cyan]init[/cyan]                Create example knowledge files\n"
            "\n[bold]Examples:[/bold]\n"
            "  secpilot search \"403 bypass\"\n"
            "  secpilot search \"sql注入绕过\"\n"
            "  secpilot category waf_bypass\n"
            "\n[dim]Run [cyan]secpilot --help[/cyan] for full options.[/dim]"
        )
        return
    cli()


if __name__ == "__main__":
    main()
