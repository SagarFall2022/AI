from __future__ import annotations
import re
from html import escape

# Minimal allowlist sanitizer (safe for POC). If you want: use "bleach" library.
_ALLOWED_TAGS = {
    "div","span","p","br","hr",
    "h1","h2","h3","h4",
    "ul","ol","li",
    "table","thead","tbody","tr","th","td",
    "code","pre",
    "strong","em","b","i",
    "a",
}
_ALLOWED_ATTRS = {
    "class","href","target","rel"
}

def sanitize_html(html: str) -> str:
    """
    Very small sanitizer:
      - strips <script>, <style>, <iframe>, event handlers, and disallowed tags/attrs
    For stronger sanitization, replace this with `bleach.clean`.
    """
    # drop script/style/iframe entirely
    html = re.sub(r"(?is)<(script|style|iframe).*?>.*?</\1>", "", html)

    # remove event handler attrs like onclick=
    html = re.sub(r'(?i)\son\w+\s*=\s*(".*?"|\'.*?\'|[^\s>]+)', "", html)

    # naive tag filter: remove disallowed tags but keep content
    def _strip_tag(m):
        tag = m.group(1).lower()
        if tag in _ALLOWED_TAGS:
            return m.group(0)
        return ""  # removes the tag marker

    html = re.sub(r"</?([a-zA-Z0-9]+)(\s[^>]*)?>", _strip_tag, html)

    # strip disallowed attributes
    def _filter_attrs(m):
        tag = m.group(1)
        attrs = m.group(2) or ""
        kept = []
        for am in re.finditer(r'([a-zA-Z_:][\w:.-]*)\s*=\s*(".*?"|\'.*?\')', attrs):
            k = am.group(1).lower()
            v = am.group(2)
            if k in _ALLOWED_ATTRS:
                kept.append(f"{k}={v}")
        return f"<{tag}" + ((" " + " ".join(kept)) if kept else "") + ">"

    html = re.sub(r"<([a-zA-Z0-9]+)\s([^>]*)>", _filter_attrs, html)

    # enforce safe links
    html = re.sub(r'(?i)<a([^>]*?)>', lambda m: _ensure_safe_anchor(m.group(0)), html)
    return html

def _ensure_safe_anchor(a_tag: str) -> str:
    # add rel/target if href present
    if "href=" not in a_tag.lower():
        return a_tag
    if "target=" not in a_tag.lower():
        a_tag = a_tag[:-1] + ' target="_blank">'
    if "rel=" not in a_tag.lower():
        a_tag = a_tag[:-1] + ' rel="noopener noreferrer">'
    return a_tag


FORMATTER_SYSTEM = """
You are an HTML formatter for a Hendrickson catalog assistant UI.

You will be given:
- The user's question
- A verified RAG answer with citations like: (doc_id p.page_no)

Your job:
- Convert the answer into BEAUTIFUL, readable HTML that looks like a modern dashboard.
- Do NOT change facts. Do NOT add new claims.
- Preserve all citations exactly, but wrap them in <span class="cite">( ... )</span>.
- Use sections:
  - <div class="section"><h3>Answer</h3>...</div>
  - <div class="section"><h3>Graph reasoning</h3>...</div>
  - <div class="section"><h3>Results</h3>...</div>
  - <div class="section"><h3>Evidence</h3>...</div>
  - <div class="section"><h3>Confidence & gaps</h3>...</div>
- If the answer contains lists or tables, render as <ul> or <table>.
- Output ONLY HTML (no markdown fences).
"""

def basic_fallback_html(question: str, answer_text: str) -> str:
    # in case formatter fails, return safe preformatted HTML
    return f"""
<div class="section">
  <h3>Answer</h3>
  <pre>{escape(answer_text)}</pre>
</div>
""".strip()
