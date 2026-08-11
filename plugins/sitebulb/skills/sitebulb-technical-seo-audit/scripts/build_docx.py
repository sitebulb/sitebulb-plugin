#!/usr/bin/env python3
"""Build the audit Word document (.docx) from a JSON spec — Python stdlib only.

No packages, no network, no host document tooling: any environment that can
run `python3` can produce the full deliverable, including native Word review
comments anchored to the passages they concern.

Usage:
    python3 scripts/build_docx.py spec.json "Technical SEO Audit - Client.docx"
    ... | python3 scripts/build_docx.py - audit.docx      # spec on stdin

Spec format (JSON object):

{
  "title": "Technical SEO Audit - Example & Co",   # document metadata title
  "comment_author": "Audit draft",                 # optional Word comment author
  "blocks": [
    {"type": "title",   "text": "Technical SEO Audit - Example & Co"},
    {"type": "heading", "level": 1, "text": "Executive summary"},
    {"type": "paragraph", "text": "Plain text paragraph."},
    {"type": "paragraph", "runs": [
        "Runs mix plain strings and formatted pieces: ",
        {"text": "bold", "bold": true}, ", ",
        {"text": "italic", "italic": true}, ", and ",
        {"text": "a link", "link": "https://sitebulb.com/hints/..."}, "."
    ]},
    {"type": "bullets", "items": [
        "Plain item",
        {"runs": ["Formatted item with ", {"text": "emphasis", "bold": true}]}
    ]},
    {"type": "table", "header": ["Issue", "Priority"],
     "rows": [["Broken internal links", "High"],
              ["Missing alt text", "Medium"]]},
    {"type": "page_break"}
  ]
}

Headings take level 1-3 (default 1). Any block except page_break may carry
"comment": a consultant-facing review note attached to that block as a native
anchored Word comment. A string makes one comment (blank-line-separated
paragraphs); a list of strings makes several separate comments on the same
block. On a bullets block the anchor spans the whole list; on a table it
anchors in the first cell.

The structural contract for what goes in the spec (section order, per-item
anatomy, where comments belong) is references/document-template.md.
"""
from __future__ import annotations

import json
import sys
import zipfile
from xml.sax.saxutils import escape, quoteattr

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
ALLOWED_BLOCKS = ("title", "heading", "paragraph", "bullets", "table", "page_break")
DEFAULT_AUTHOR = "Audit draft"


class SpecError(Exception):
    pass


def _norm_runs(value, block_type):
    """Normalise a runs value (string | list of string/dict) to a list of dicts."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise SpecError(f"{block_type}: runs must be a string or a list")
    runs = []
    for item in value:
        if isinstance(item, str):
            runs.append({"text": item})
        elif isinstance(item, dict):
            runs.append(item)
        else:
            raise SpecError(f"{block_type}: run must be a string or an object")
    return runs


def _comment_ref_run(cid):
    return (
        '<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>'
        f'<w:commentReference w:id="{cid}"/></w:r>'
    )


class Builder:
    def __init__(self):
        self.hyperlinks = {}  # url -> rId
        self.comments = []  # list of comment texts, id = index

    # -- inline content -----------------------------------------------------

    def _link_rid(self, url):
        if url not in self.hyperlinks:
            self.hyperlinks[url] = f"rId{100 + len(self.hyperlinks)}"
        return self.hyperlinks[url]

    def run_xml(self, run):
        text = str(run.get("text", ""))
        props = []
        if run.get("link"):
            props.append('<w:rStyle w:val="Hyperlink"/>')
        if run.get("bold"):
            props.append("<w:b/>")
        if run.get("italic"):
            props.append("<w:i/>")
        rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
        r = f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
        if run.get("link"):
            return f'<w:hyperlink r:id="{self._link_rid(str(run["link"]))}">{r}</w:hyperlink>'
        return r

    def para_xml(self, runs, style=None, bullet=False, open_ids=(), close_ids=()):
        ppr = []
        if style:
            ppr.append(f'<w:pStyle w:val="{style}"/>')
        if bullet:
            ppr.append('<w:pStyle w:val="ListParagraph"/>')
            ppr.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
        p_pr = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
        opens = "".join(f'<w:commentRangeStart w:id="{i}"/>' for i in open_ids)
        closes = "".join(
            f'<w:commentRangeEnd w:id="{i}"/>{_comment_ref_run(i)}' for i in close_ids
        )
        body = "".join(self.run_xml(r) for r in runs)
        return f"<w:p>{p_pr}{opens}{body}{closes}</w:p>"

    # -- blocks -------------------------------------------------------------

    def _comment_ids(self, block):
        value = block.get("comment")
        if value is None:
            return []
        texts = [value] if isinstance(value, str) else value
        if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
            raise SpecError("comment must be a string or a list of strings")
        ids = []
        for text in texts:
            ids.append(len(self.comments))
            self.comments.append(text)
        return ids

    def block_xml(self, block):
        btype = block.get("type")
        if btype not in ALLOWED_BLOCKS:
            raise SpecError(
                f"unknown block type {btype!r} — allowed: {', '.join(ALLOWED_BLOCKS)}"
            )
        if btype == "page_break":
            return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

        cids = self._comment_ids(block)

        if btype in ("title", "heading", "paragraph"):
            runs = _norm_runs(block.get("runs", block.get("text", "")), btype)
            if btype == "title":
                style = "Title"
            elif btype == "heading":
                level = block.get("level", 1)
                if level not in (1, 2, 3):
                    raise SpecError(f"heading level must be 1, 2 or 3, got {level!r}")
                style = f"Heading{level}"
            else:
                style = None
            return self.para_xml(runs, style=style, open_ids=cids, close_ids=cids)

        if btype == "bullets":
            items = block.get("items")
            if not isinstance(items, list) or not items:
                raise SpecError("bullets: items must be a non-empty list")
            out = []
            last = len(items) - 1
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    runs = _norm_runs(item.get("runs", item.get("text", "")), "bullets")
                else:
                    runs = _norm_runs(item, "bullets")
                out.append(
                    self.para_xml(
                        runs,
                        bullet=True,
                        open_ids=cids if i == 0 else (),
                        close_ids=cids if i == last else (),
                    )
                )
            return "".join(out)

        # table
        rows = list(block.get("rows") or [])
        header = block.get("header")
        if not rows and not header:
            raise SpecError("table: needs header and/or rows")
        ncols = len(header) if header else len(rows[0])
        edges = "".join(
            f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
            for e in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        tbl = [
            "<w:tbl><w:tblPr>"
            '<w:tblW w:w="0" w:type="auto"/>'
            f"<w:tblBorders>{edges}</w:tblBorders>"
            "</w:tblPr>",
            "<w:tblGrid>" + f'<w:gridCol w:w="{9026 // ncols}"/>' * ncols + "</w:tblGrid>",
        ]

        def cell_xml(value, bold, open_ids=(), close_ids=()):
            if isinstance(value, dict):
                runs = _norm_runs(value.get("runs", value.get("text", "")), "table")
            else:
                runs = _norm_runs(value, "table")
            if bold:
                runs = [dict(r, bold=True) for r in runs]
            p = self.para_xml(runs, open_ids=open_ids, close_ids=close_ids)
            return f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>{p}</w:tc>'

        first = True
        if header:
            cells = []
            for value in header:
                cells.append(cell_xml(value, True, cids if first else (), cids if first else ()))
                first = False
            tbl.append(f"<w:tr><w:trPr><w:tblHeader/></w:trPr>{''.join(cells)}</w:tr>")
        for row in rows:
            if len(row) != ncols:
                raise SpecError(f"table: row has {len(row)} cells, expected {ncols}")
            cells = []
            for value in row:
                cells.append(cell_xml(value, False, cids if first else (), cids if first else ()))
                first = False
            tbl.append(f"<w:tr>{''.join(cells)}</w:tr>")
        tbl.append("</w:tbl>")
        return "".join(tbl)

    # -- parts --------------------------------------------------------------

    def document_xml(self, blocks):
        body = "".join(self.block_xml(b) for b in blocks)
        sect = (
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        )
        return (
            f"{XML_DECL}<w:document xmlns:w={quoteattr(W_NS)} xmlns:r={quoteattr(R_NS)}>"
            f"<w:body>{body}{sect}</w:body></w:document>"
        )

    def comments_xml(self, author):
        initials = "".join(w[0] for w in author.split()[:3]).upper() or "AD"
        items = []
        for cid, text in enumerate(self.comments):
            paras = "".join(
                '<w:p><w:pPr><w:pStyle w:val="CommentText"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">{escape(p)}</w:t></w:r></w:p>'
                for p in text.split("\n\n")
            )
            items.append(
                f'<w:comment w:id="{cid}" w:author={quoteattr(author)} '
                f"w:initials={quoteattr(initials)}>{paras}</w:comment>"
            )
        return f"{XML_DECL}<w:comments xmlns:w={quoteattr(W_NS)}>{''.join(items)}</w:comments>"

    def document_rels_xml(self):
        rel_base = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        rels = [
            f'<Relationship Id="rId1" Type="{rel_base}/styles" Target="styles.xml"/>',
            f'<Relationship Id="rId2" Type="{rel_base}/numbering" Target="numbering.xml"/>',
        ]
        if self.comments:
            rels.append(
                f'<Relationship Id="rId3" Type="{rel_base}/comments" Target="comments.xml"/>'
            )
        for url, rid in self.hyperlinks.items():
            rels.append(
                f'<Relationship Id="{rid}" Type="{rel_base}/hyperlink" '
                f'Target={quoteattr(url)} TargetMode="External"/>'
            )
        return (
            f"{XML_DECL}<Relationships xmlns={quoteattr(REL_NS)}>{''.join(rels)}</Relationships>"
        )


STYLES_XML = f"""{XML_DECL}<w:styles xmlns:w={quoteattr(W_NS)}>
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="240"/></w:pPr><w:rPr><w:sz w:val="52"/><w:szCs w:val="52"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="CommentText"><w:name w:val="annotation text"/><w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>
<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>
<w:style w:type="character" w:styleId="CommentReference"><w:name w:val="annotation reference"/><w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr></w:style>
</w:styles>"""

NUMBERING_XML = f"""{XML_DECL}<w:numbering xmlns:w={quoteattr(W_NS)}>
<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""

ROOT_RELS_XML = f"""{XML_DECL}<Relationships xmlns={quoteattr(REL_NS)}>
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

APP_XML = (
    f"{XML_DECL}<Properties "
    'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    "<Application>Sitebulb audit builder</Application></Properties>"
)


def content_types_xml(has_comments):
    overrides = [
        ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
    ]
    if has_comments:
        overrides.append(
            ("/word/comments.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml")
        )
    parts = "".join(
        f'<Override PartName="{name}" ContentType="{ctype}"/>' for name, ctype in overrides
    )
    return (
        f'{XML_DECL}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{parts}</Types>"
    )


def core_xml(title):
    return (
        f"{XML_DECL}<cp:coreProperties "
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f"<dc:title>{escape(title)}</dc:title></cp:coreProperties>"
    )


def build(spec):
    """Return {zip part name: xml string} for the given spec."""
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    blocks = spec.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise SpecError("spec.blocks must be a non-empty list")
    b = Builder()
    document = b.document_xml(blocks)  # populates hyperlinks + comments
    parts = {
        "[Content_Types].xml": content_types_xml(bool(b.comments)),
        "_rels/.rels": ROOT_RELS_XML,
        "docProps/core.xml": core_xml(str(spec.get("title", "Technical SEO Audit"))),
        "docProps/app.xml": APP_XML,
        "word/document.xml": document,
        "word/styles.xml": STYLES_XML,
        "word/numbering.xml": NUMBERING_XML,
        "word/_rels/document.xml.rels": b.document_rels_xml(),
    }
    if b.comments:
        parts["word/comments.xml"] = b.comments_xml(
            str(spec.get("comment_author", DEFAULT_AUTHOR))
        )
    return parts, len(b.comments)


def write_docx(path, parts):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)


def main(argv):
    if len(argv) != 3:
        print(__doc__.split("Spec format")[0], file=sys.stderr)
        return 2
    spec_arg, out_path = argv[1], argv[2]
    try:
        if spec_arg == "-":
            spec = json.load(sys.stdin)
        else:
            with open(spec_arg, encoding="utf-8") as fh:
                spec = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"could not read spec: {exc}", file=sys.stderr)
        return 2
    try:
        parts, n_comments = build(spec)
    except SpecError as exc:
        print(f"spec error: {exc}", file=sys.stderr)
        return 2
    write_docx(out_path, parts)
    n_blocks = len(spec["blocks"])
    print(f"Wrote {out_path} — {n_blocks} blocks, {n_comments} review comments.")
    if n_comments == 0:
        print(
            "warning: no review comments — the deliverable spec "
            "(references/document-template.md) expects at least one.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
