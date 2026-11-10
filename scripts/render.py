#!/usr/bin/env python3
"""Render flows.json to a standalone HTML review page, optionally Mermaid markdown.

usage: render.py flows.json [-o review.html] [--md review.md] [--root REPO]
"""
import argparse
import html
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
STATUSES = {"added", "modified", "removed", "unchanged"}
SHAPES = {"step": '["{}"]', "decision": '{{"{}"}}', "entry": '(["{}"])', "store": '[("{}")]'}
EDGES = {"unchanged": ("-->", "-- {} -->"), "added": ("==>", "== {} ==>"), "removed": ("-.->", "-. {} .->")}
# markdown needs literal colors; the html page styles thick/dotted edges from css instead
EDGE_COLOR = {"added": "#059669", "removed": "#e11d48"}
SIGN = {"added": "+ ", "modified": "~ ", "removed": "- ", "unchanged": ""}
SEVERITIES = ("high", "medium", "low")
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
SEQ_RECT = {"added": "rgb(209,250,229)", "removed": "rgb(255,228,230)"}
CLASSDEFS = [
    "classDef added fill:#d1fae5,stroke:#059669,color:#064e3b",
    "classDef modified fill:#fef3c7,stroke:#d97706,color:#78350f",
    "classDef removed fill:#ffe4e6,stroke:#e11d48,color:#881337,stroke-dasharray:6 4",
    "classDef unchanged fill:#f1f5f9,stroke:#64748b,color:#334155",
]


def circled(n):
    return CIRCLED[n - 1] if n <= len(CIRCLED) else f"({n})"


def marks(x, flow):
    """Circled numbers of the risks a node, function or edge points at, with a leading space."""
    nums = {r["id"]: r["_n"] for r in flow.get("risks") or []}
    return "".join(" " + circled(nums[i]) for i in x.get("risks") or [])


def esc(s):
    return str(s).replace('"', "#quot;").replace("\n", " ")


def validate(doc):
    errs = []
    flows = doc.get("flows") or []
    if not flows:
        errs.append("flows is empty")
    for f in flows:
        fid = f.get("id") or f.get("title") or "?"
        nodes = f.get("nodes") or []
        seq = f.get("type", "flowchart") == "sequence"
        if f.get("type", "flowchart") not in ("flowchart", "sequence"):
            errs.append(f"{fid}: type must be flowchart or sequence")
        ids = [n.get("id") for n in nodes]
        if not nodes:
            errs.append(f"{fid}: no nodes")
        if len(ids) != len(set(ids)):
            errs.append(f"{fid}: duplicate node ids")
        for n in nodes:
            if not n.get("id") or not n.get("label"):
                errs.append(f"{fid}: node needs id and label: {n}")
            if n.get("status", "unchanged") not in STATUSES:
                errs.append(f"{fid}/{n.get('id')}: status must be one of {sorted(STATUSES)}")
            if n.get("shape", "step") not in SHAPES:
                errs.append(f"{fid}/{n.get('id')}: shape must be one of {sorted(SHAPES)}")
            if seq and n.get("shape") == "decision":
                errs.append(f"{fid}/{n.get('id')}: sequence flows have no decision nodes; put the condition in the edge label")
            if n.get("functions") and not seq:
                errs.append(f"{fid}/{n.get('id')}: functions is for sequence participants; a flowchart node is one function")
            # a participant with a functions list is a component; its functions carry the callers
            for x in n.get("functions") or [n]:
                st = x.get("status", "unchanged")
                if not x.get("label") or st not in STATUSES:
                    errs.append(f"{fid}/{n.get('id')}: function needs a label and a valid status: {x.get('label')!r}")
                if st != "unchanged" and n.get("shape", "step") != "decision" and not isinstance(x.get("callers"), list):
                    errs.append(f"{fid}/{n.get('id')}: changed function {x.get('label')!r} needs a callers list ([] if every caller is drawn)")
        rids = [r.get("id") for r in f.get("risks") or []]
        if len(rids) != len(set(rids)):
            errs.append(f"{fid}: duplicate risk ids")
        for r in f.get("risks") or []:
            if not r.get("id") or not r.get("title") or r.get("severity") not in SEVERITIES:
                errs.append(f"{fid}: risk needs id, title and severity in {SEVERITIES}: {r.get('id')!r}")
        refs = [x for n in nodes for x in [n] + (n.get("functions") or [])] + (f.get("edges") or [])
        for x in refs:
            for i in x.get("risks") or []:
                if i not in rids:
                    errs.append(f"{fid}: {x.get('label') or x.get('id') or x} points at unknown risk {i!r}")
        for e in f.get("edges") or []:
            for k in ("from", "to"):
                if e.get(k) not in ids:
                    errs.append(f"{fid}: edge {e} references unknown node {e.get(k)!r}")
            if e.get("status", "unchanged") not in EDGES:
                errs.append(f"{fid}: edge {e} status must be one of {sorted(EDGES)}")
    return errs


def sequence(flow, target, mid):
    lines = ["sequenceDiagram"]
    for n in flow["nodes"]:
        st = n.get("status", "unchanged")
        tag = f"<br/>{st}" if target == "md" and st != "unchanged" and not n.get("functions") else ""
        tag += "".join(f"<br/>{SIGN[x.get('status', 'unchanged')]}{esc(x['label'])}" for x in n.get("functions") or [])
        # risk numbers go on messages only; participant boxes stay clean
        lines.append(f"  participant {mid[n['id']]} as {esc(n['label'])}{tag}")
    for e in flow.get("edges") or []:
        st = e.get("status", "unchanged")
        msg = f"  {mid[e['from']]}{'--x' if st == 'removed' else '->>'}{mid[e['to']]}: {esc(e.get('label') or 'call')}{marks(e, flow)}"
        # markdown cannot be styled from css, so tint the changed message's background
        lines += [f"  rect {SEQ_RECT[st]}", "  " + msg, "  end"] if target == "md" and st in SEQ_RECT else [msg]
    return "\n".join(lines), {v: k for k, v in mid.items()}


def mermaid(flow, target):
    """target "html": rich labels, styling left to page css. "md": plain labels, self-contained styling."""
    mid = {n["id"]: f"n{i}" for i, n in enumerate(flow["nodes"])}
    if flow.get("type") == "sequence":
        return sequence(flow, target, mid)
    lines = ["flowchart " + flow.get("direction", "TD")]
    for n in flow["nodes"]:
        if target == "html":
            label = f"<b>{esc(n['label'])}</b>" + marks(n, flow) + (f"<br/><small>{esc(n['change'])}</small>" if n.get("change") else "")
        else:
            label = esc(n["label"]) + marks(n, flow) + (f"<br/>{esc(n['change'])}" if n.get("change") else "")
        shape = SHAPES[n.get("shape", "step")].format(label)
        lines.append(f"  {mid[n['id']]}{shape}:::{n.get('status', 'unchanged')}")
    styles = []
    for i, e in enumerate(flow.get("edges") or []):
        st = e.get("status", "unchanged")
        plain, labeled = EDGES[st]
        text = (esc(e.get("label") or "") + marks(e, flow)).strip()
        arrow = labeled.format(f'"{text}"') if text else plain
        lines.append(f"  {mid[e['from']]} {arrow} {mid[e['to']]}")
        if target == "md" and st in EDGE_COLOR:
            styles.append(f"  linkStyle {i} stroke:{EDGE_COLOR[st]},stroke-width:2px")
    lines += styles + (["  " + c for c in CLASSDEFS] if target == "md" else [])
    return "\n".join(lines), {v: k for k, v in mid.items()}


def markdown(doc):
    out = [f"# {doc.get('title', 'Diff flowchart')}", "", doc.get("summary", ""), ""]
    for f in doc["flows"]:
        out += [f"## {f['title']}", "", f.get("description", ""), "", "```mermaid", f["_md"], "```", ""]
        # changed functions, plus unchanged ones a reviewer left a note on
        items = [x for n in f["nodes"] for x in ([n] if not n.get("functions") else [n] * bool(n.get("notes")) + n["functions"])]
        changed = [n for n in items if n.get("status", "unchanged") != "unchanged" or n.get("notes")]
        for n in changed:
            loc = f" (`{n['file']}`)" if n.get("file") else ""
            out.append(f"- **{n['label']}** {n.get('status', 'unchanged')}{loc}: {n.get('change', '')}".rstrip(": "))
            for note in [n["notes"]] if isinstance(n.get("notes"), str) else n.get("notes") or []:
                out.append(f"  - ⚠ {note}")
            if n.get("callers"):
                out.append(f"  - also called from: {', '.join(n['callers'])}")
        if f.get("risks"):
            out += ["", "**Risks**", ""]
        for r in f.get("risks") or []:
            fix = f" Fix: {r['fix']}" if r.get("fix") else ""
            out.append(f"- {circled(r['_n'])} **{r['severity']}** · **{r['title']}**: {r.get('detail', '')}{fix}".rstrip(": "))
        out.append("")
    if doc.get("other"):
        out += ["## Other changes", ""] + [f"- {o}" for o in doc["other"]] + [""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("flows")
    ap.add_argument("-o", "--out", default="review.html")
    ap.add_argument("--md", help="also write Mermaid markdown (for PR comments)")
    ap.add_argument("--root", default=".", help="directory holding the post-change source, so diffs can expand to the full function")
    a = ap.parse_args()

    doc = json.loads(Path(a.flows).read_text())
    errs = validate(doc)
    if errs:
        print("flows.json invalid:\n  " + "\n  ".join(errs), file=sys.stderr)
        sys.exit(1)
    # embed the changed files so the page can expand a hunk's context, like github
    # ponytail: whole files inline, capped at 200 KB each; switch to line windows if pages get heavy
    files = {}
    for f in doc["flows"]:
        for x in [x for n in f["nodes"] for x in [n] + (n.get("functions") or [])]:
            src = Path(a.root) / x["file"] if x.get("diff") and x.get("file") else None
            if src and src.is_file() and src.stat().st_size < 200_000:
                files[x["file"]] = src.read_text(errors="replace")
    doc["_files"] = files
    count = 0
    for f in doc["flows"]:
        for r in f.get("risks") or []:  # numbered across the whole review, in the order written
            count += 1
            r["_n"] = count
        for n in f["nodes"]:
            if n.get("functions"):  # a component is modified when any of its functions changed
                n.setdefault("status", "modified" if any(x.get("status", "unchanged") != "unchanged" for x in n["functions"]) else "unchanged")
        f["_mermaid"], f["_ids"] = mermaid(f, "html")
        f["_md"], _ = mermaid(f, "md")

    page = TEMPLATE.read_text()
    page = page.replace("__TITLE__", html.escape(doc.get("title", "Diff flowchart")))
    page = page.replace("__FLOWS_JSON__", json.dumps(doc).replace("</", "<\\/"))
    Path(a.out).write_text(page)
    print(f"wrote {a.out}")
    if a.md:
        Path(a.md).write_text(markdown(doc))
        print(f"wrote {a.md}")


if __name__ == "__main__":
    main()
