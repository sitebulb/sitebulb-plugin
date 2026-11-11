#!/usr/bin/env python3
"""
Unit tests for build_docx.py. Pure, deterministic, stdlib only. Builds a spec
exercising every block type, then structurally validates the resulting OOXML
package: well-formed parts, matched comment anchors, resolvable hyperlink and
style references. Run: python3 scripts/test_build_docx.py
"""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "build_docx.py"

sys.path.insert(0, str(HERE))
import build_docx as bd  # noqa: E402

W = bd.W_NS
R = bd.R_NS
NS = {"w": W, "r": R, "rel": bd.REL_NS}

passed = failed = 0


def check(name, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {name}\n        got:  {got!r}\n        want: {want!r}")


SPEC = {
    "title": "Technical SEO Audit — Fish & Chips Ltd",
    "comment_author": "Audit draft",
    "blocks": [
        {"type": "title", "text": "Technical SEO Audit — Fish & Chips Ltd"},
        {"type": "paragraph", "text": "Based on a Sitebulb crawl completed 14 July 2026."},
        {"type": "page_break"},
        {"type": "heading", "level": 1, "text": "Executive summary"},
        {
            "type": "paragraph",
            "runs": [
                "Plain, ",
                {"text": "bold", "bold": True},
                ", ",
                {"text": "italic", "italic": True},
                ", and ",
                {"text": "a guide", "link": "https://sitebulb.com/hints/example/?a=1&b=2"},
                ".",
            ],
            "comment": "Assumption made under the refusal default — revisit.\n\nSecond paragraph of the same comment.",
        },
        {
            "type": "table",
            "header": ["Issue", "Priority"],
            "rows": [["Broken internal links", "High"], ["Missing alt text <img>", "Medium"]],
        },
        {"type": "heading", "level": 2, "text": "Broken internal links"},
        {
            "type": "bullets",
            "items": [
                "https://example.com/a",
                {"runs": ["https://example.com/b — ", {"text": "template page", "italic": True}]},
                "https://example.com/c",
            ],
            "comment": ["Spot-check this sample before it goes out.", "Mix will prompt client questions."],
        },
        {"type": "heading", "level": 3, "text": "Recommendation"},
        {
            "type": "paragraph",
            "runs": [{"text": "Repeat link", "link": "https://sitebulb.com/hints/example/?a=1&b=2"}],
        },
    ],
}

parts, n_comments = bd.build(SPEC)
check("comment count returned", n_comments, 3)

# every part is well-formed XML
roots = {}
for name, data in parts.items():
    try:
        roots[name] = ET.fromstring(data)
        passed += 1
    except ET.ParseError as exc:
        failed += 1
        print(f"  FAIL well-formed {name}: {exc}")

doc = roots["word/document.xml"]

# --- comments: anchors, references and definitions all agree ---------------
starts = [e.get(f"{{{W}}}id") for e in doc.iter(f"{{{W}}}commentRangeStart")]
ends = [e.get(f"{{{W}}}id") for e in doc.iter(f"{{{W}}}commentRangeEnd")]
refs = [e.get(f"{{{W}}}id") for e in doc.iter(f"{{{W}}}commentReference")]
defined = [e.get(f"{{{W}}}id") for e in roots["word/comments.xml"].iter(f"{{{W}}}comment")]
check("commentRangeStart ids", sorted(starts), ["0", "1", "2"])
check("commentRangeEnd matches starts", sorted(ends), sorted(starts))
check("commentReference matches starts", sorted(refs), sorted(starts))
check("comments.xml defines every anchor", sorted(defined), sorted(starts))
check("multi-paragraph comment body", len(roots["word/comments.xml"].findall(f".//{{{W}}}comment[@{{{W}}}id='0']/{{{W}}}p")), 2)
authors = {e.get(f"{{{W}}}author") for e in roots["word/comments.xml"].iter(f"{{{W}}}comment")}
check("comment author", authors, {"Audit draft"})

# --- hyperlinks resolve to external rels, deduped by URL -------------------
link_ids = [e.get(f"{{{R}}}id") for e in doc.iter(f"{{{W}}}hyperlink")]
check("hyperlink count in body", len(link_ids), 2)
check("same URL reuses one rel", len(set(link_ids)), 1)
rels = {
    e.get("Id"): e
    for e in roots["word/_rels/document.xml.rels"].iter(f"{{{bd.REL_NS}}}Relationship")
}
for rid in set(link_ids):
    rel = rels.get(rid)
    check(f"rel {rid} exists", rel is not None, True)
    if rel is not None:
        check(f"rel {rid} target", rel.get("Target"), "https://sitebulb.com/hints/example/?a=1&b=2")
        check(f"rel {rid} external", rel.get("TargetMode"), "External")

# --- every style referenced in the body exists in styles.xml ---------------
style_ids = {e.get(f"{{{W}}}styleId") for e in roots["word/styles.xml"].iter(f"{{{W}}}style")}
used = {e.get(f"{{{W}}}val") for e in doc.iter(f"{{{W}}}pStyle")} | {
    e.get(f"{{{W}}}val") for e in doc.iter(f"{{{W}}}rStyle")
}
check("styles referenced but undefined", sorted(used - style_ids), [])
for expected in ("Title", "Heading1", "Heading2", "Heading3", "ListParagraph", "Hyperlink", "CommentReference"):
    check(f"style {expected} used", expected in used, True)

# --- bullets use the numbering definition ----------------------------------
num_ids = {e.get(f"{{{W}}}val") for e in doc.iter(f"{{{W}}}numId")}
defined_nums = {e.get(f"{{{W}}}numId") for e in roots["word/numbering.xml"].iter(f"{{{W}}}num")}
check("numId resolves", num_ids <= defined_nums, True)
check("bullet paragraph count", len(doc.findall(f".//{{{W}}}numPr")), 3)

# --- table structure -------------------------------------------------------
check("table rows", len(doc.findall(f".//{{{W}}}tbl/{{{W}}}tr")), 3)
check("header repeat marker", len(doc.findall(f".//{{{W}}}tblHeader")), 1)
header_bold = doc.findall(f".//{{{W}}}tbl/{{{W}}}tr[1]//{{{W}}}b")
check("header cells bold", len(header_bold), 2)

# --- escaping round-trips --------------------------------------------------
texts = [e.text for e in doc.iter(f"{{{W}}}t")]
check("ampersand round-trip", any(t == "Technical SEO Audit — Fish & Chips Ltd" for t in texts), True)
check("angle brackets round-trip", any(t == "Missing alt text <img>" for t in texts), True)

# --- content types cover every part ----------------------------------------
ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
declared = {e.get("PartName") for e in roots["[Content_Types].xml"].iter(f"{{{ct_ns}}}Override")}
for name in parts:
    if name.endswith(".xml") and not name.endswith(".rels") and name != "[Content_Types].xml":
        check(f"content type declared for {name}", f"/{name}" in declared, True)

# --- comment-free spec omits the comments part, builder warns via CLI ------
plain_parts, plain_count = bd.build({"blocks": [{"type": "paragraph", "text": "hi"}]})
check("no comments part when uncommented", "word/comments.xml" in plain_parts, False)
check("no comment rel when uncommented", "rId3" in plain_parts["word/_rels/document.xml.rels"], False)
check("plain comment count", plain_count, 0)

# --- spec errors are caught, not emitted -----------------------------------
for bad, label in [
    ({"blocks": []}, "empty blocks"),
    ({"blocks": [{"type": "wat"}]}, "unknown block"),
    ({"blocks": [{"type": "heading", "level": 5, "text": "x"}]}, "bad heading level"),
    ({"blocks": [{"type": "table", "header": ["a", "b"], "rows": [["only-one"]]}]}, "ragged table"),
    ({"blocks": [{"type": "bullets", "items": []}]}, "empty bullets"),
]:
    try:
        bd.build(bad)
        check(f"SpecError raised for {label}", "no error", "SpecError")
    except bd.SpecError:
        passed += 1

# --- CLI end-to-end: writes a readable zip ---------------------------------
with tempfile.TemporaryDirectory() as tmp:
    spec_path = Path(tmp) / "spec.json"
    out_path = Path(tmp) / "audit.docx"
    spec_path.write_text(__import__("json").dumps(SPEC), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(spec_path), str(out_path)],
        capture_output=True, text=True,
    )
    check("CLI exit code", proc.returncode, 0)
    check("CLI summary mentions comments", "3 review comments" in proc.stdout, True)
    with zipfile.ZipFile(out_path) as z:
        check("zip integrity", z.testzip(), None)
        check("zip parts", sorted(z.namelist()), sorted(parts))

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
