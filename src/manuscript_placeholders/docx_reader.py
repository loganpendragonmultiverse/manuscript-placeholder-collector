"""Bounded, read-only WordprocessingML story traversal."""

from __future__ import annotations

import posixpath
import re
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"


def preflight(archive: zipfile.ZipFile, label: str) -> None:
    infos = archive.infolist()
    names = [i.filename for i in infos]
    if len(infos) > 10000 or sum(i.file_size for i in infos) > 100 * 1024 * 1024:
        raise ValueError(f"{label} exceeds 10,000-entry or 100 MB uncompressed limit")
    if len(set(names)) != len(names):
        raise ValueError(f"{label} contains duplicate package entries")
    if any(i.flag_bits & 1 for i in infos):
        raise ValueError(f"{label} encrypted entries are unsupported")


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        raw = archive.read(name)
        if (
            b"<!DOCTYPE" in raw.replace(b"\x00", b"").upper()
            or b"<!ENTITY" in raw.replace(b"\x00", b"").upper()
        ):
            raise ValueError("DOCX XML declarations with entities are unsupported")
        return ET.fromstring(raw)
    except (KeyError, ET.ParseError) as exc:
        raise ValueError(f"DOCX XML part missing or malformed: {name}") from exc


def _target(target: str) -> str:
    parsed = urlsplit(target)
    name = posixpath.normpath(
        unquote(target).lstrip("/")
        if target.startswith("/")
        else posixpath.join("word", unquote(target))
    )
    if (
        not target
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or "\\" in target
        or name in (".", "..")
        or name.startswith("../")
    ):
        raise ValueError("DOCX has an unsafe part path")
    return name


def read_docx(
    path: Path,
    options: dict[str, bool],
    coverage: dict[str, Any],
    *,
    revisions: str = "current",
) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(path) as archive:
        preflight(archive, "DOCX")
        document = _xml(archive, "word/document.xml")
        if document.tag != W + "document" or len(document.findall(W + "body")) != 1:
            raise ValueError("DOCX main part must contain one document body")
        relname = "word/_rels/document.xml.rels"
        relations = (
            list(_xml(archive, relname)) if relname in archive.namelist() else []
        )
        ids = [r.get("Id") for r in relations]
        if None in ids or len(set(ids)) != len(ids):
            raise ValueError("DOCX relationship IDs must be unique and present")
        by_id = {r.get("Id"): r for r in relations}
        stories: list[tuple[str, ET.Element, str]] = [
            ("word/document.xml", document, "")
        ]
        states: dict[str, Any] = {}
        unsupported = []
        anchors: dict[str, list[str]] = {}
        for index, paragraph in enumerate(document.iter(W + "p"), 1):
            for node in paragraph.iter():
                if node.tag in {
                    W + name + "Reference"
                    for name in ("footnote", "endnote", "comment")
                }:
                    anchors.setdefault(
                        node.tag[len(W) :] + ":" + node.get(W + "id", ""), []
                    ).append(f"word/document.xml/paragraph[{index}]")
        for kind in (
            "tables",
            "textboxes",
            "comments",
            "footnotes",
            "endnotes",
            "headers",
            "footers",
        ):
            enabled = options.get(kind, False)
            if kind in ("tables", "textboxes"):
                tag = "tbl" if kind == "tables" else "txbxContent"
                count = len(list(document.iter(W + tag)))
                states[kind] = {
                    "status": ("scanned" if enabled else "skipped")
                    if count
                    else "absent",
                    "count": count,
                }
                continue
            singular = {
                "comments": "comment",
                "footnotes": "footnote",
                "endnotes": "endnote",
                "headers": "header",
                "footers": "footer",
            }[kind]
            matches = [
                r
                for r in relations
                if r.get("Type", "").endswith(
                    "/" + kind
                    if kind in ("comments", "footnotes", "endnotes")
                    else "/" + singular
                )
            ]
            references = list(document.iter(W + singular + "Reference"))
            if not enabled:
                states[kind] = {
                    "status": "skipped" if matches or references else "absent",
                    "count": len(matches),
                }
                continue
            if references and not matches:
                raise ValueError(
                    f"DOCX {singular} references have no {kind} relationship"
                )
            if kind not in ("headers", "footers") and len(matches) > 1:
                raise ValueError(f"DOCX must declare a single {kind} relationship")
            if kind in ("headers", "footers"):
                selected = []
                for ref in references:
                    rel = by_id.get(ref.get(R + "id"))
                    if rel is None or rel not in matches:
                        raise ValueError(
                            f"DOCX {singular} relationship missing or has wrong type"
                        )
                    if rel not in selected:
                        selected.append(rel)
                matches = selected
            names: set[str] = set()
            normal_ids: set[int] = set()
            for rel in matches:
                if rel.get("TargetMode", "Internal") != "Internal":
                    raise ValueError(f"DOCX {kind} must reference a local XML part")
                name = _target(rel.get("Target", ""))
                if name in names:
                    continue
                names.add(name)
                root = _xml(archive, name)
                expected = {"headers": "hdr", "footers": "ftr"}.get(kind, kind)
                if root.tag != W + expected:
                    raise ValueError(f"DOCX {kind} part has the wrong root")
                if kind in ("headers", "footers"):
                    stories.append((name, root, ""))
                else:
                    seen: set[int] = set()
                    for record in root.findall(W + singular):
                        raw = record.get(W + "id", "")
                        if not re.fullmatch(r"[+-]?[0-9]+", raw):
                            raise ValueError(f"DOCX {singular} needs an integer ID")
                        identifier = int(raw)
                        if identifier in seen:
                            raise ValueError(
                                f"DOCX has duplicate {singular} ID: {identifier}"
                            )
                        seen.add(identifier)
                        kind_value = record.get(W + "type", "normal")
                        if kind_value in (
                            "separator",
                            "continuationSeparator",
                            "continuationNotice",
                        ):
                            continue
                        if kind_value != "normal":
                            raise ValueError(
                                f"DOCX {singular} has an unknown type: {kind_value}"
                            )
                        normal_ids.add(identifier)
                        stories.append((name, record, f"/{singular}[{identifier}]"))
                    for ref in references:
                        raw = ref.get(W + "id", "")
                        if (
                            not re.fullmatch(r"[+-]?[0-9]+", raw)
                            or int(raw) not in normal_ids
                        ):
                            raise ValueError(
                                f"DOCX {singular} reference has no normal {singular}: {raw}"
                            )
            states[kind] = {
                "status": "scanned" if names else "absent",
                "count": len(names),
                "parts": sorted(names),
            }
        for rel in relations:
            if rel.get("Type", "").rsplit("/", 1)[-1] in (
                "aFChunk",
                "glossaryDocument",
                "subDocument",
            ):
                unsupported.append(
                    {
                        "type": rel.get("Type", "").rsplit("/", 1)[-1],
                        "status": "unsupported",
                        "external": rel.get("TargetMode") == "External",
                    }
                )
        for kind, tag in (("tables", "tbl"), ("textboxes", "txbxContent")):
            count = sum(len(list(story.iter(W + tag))) for _, story, _ in stories)
            states[kind] = {
                "status": ("scanned" if options.get(kind) else "skipped")
                if count
                else "absent",
                "count": count,
                "scope": "selected stories",
            }
        for name, root, prefix in stories:
            parents = {child: parent for parent in root.iter() for child in parent}
            paragraphs = list(root.iter(W + "p"))
            section = (
                "Document"
                if not prefix and name == "word/document.xml"
                else "DOCX optional structure"
            )
            for index, paragraph in enumerate(paragraphs, 1):
                ancestors = []
                node = paragraph
                while node in parents:
                    node = parents[node]
                    ancestors.append(node)
                unselected = False
                for ancestor in ancestors:
                    if (
                        ancestor.tag in (MC + "Choice", MC + "Fallback")
                        and ancestor in parents
                    ):
                        alternate = parents[ancestor]
                        chosen = alternate.find(MC + "Choice")
                        if chosen is None:
                            chosen = alternate.find(MC + "Fallback")
                        if ancestor is not chosen:
                            unselected = True
                if unselected:
                    continue
                if not options.get("tables") and any(
                    n.tag == W + "tbl" for n in ancestors
                ):
                    continue
                if not options.get("textboxes") and any(
                    n.tag == W + "txbxContent" for n in ancestors
                ):
                    continue
                if revisions == "current" and any(
                    n.tag in (W + "del", W + "moveFrom") for n in ancestors
                ):
                    continue
                text = _paragraph_text(paragraph, revisions)
                if not text.strip():
                    continue
                style = paragraph.find(W + "pPr/" + W + "pStyle")
                if style is not None and style.get(W + "val", "").casefold().startswith(
                    "heading"
                ):
                    section = text.strip()
                labels = sorted(
                    {
                        n.tag[len(W) :]
                        for n in ancestors
                        if n.tag
                        in {W + x for x in ("ins", "del", "moveFrom", "moveTo")}
                    }
                )
                labels.extend(
                    sorted(
                        {
                            n.tag[len(W) :]
                            for n in paragraph.iter()
                            if n.tag
                            in {W + x for x in ("ins", "del", "moveFrom", "moveTo")}
                        }
                    )
                )
                if any(n.tag == W + "vanish" for n in paragraph.iter()):
                    labels.append("hidden")
                if any(
                    n.tag in (W + "fldChar", W + "fldSimple") for n in paragraph.iter()
                ):
                    labels.append("cached field results; not evaluated")
                label = section + (" [" + ", ".join(labels) + "]" if labels else "")
                container = ""
                if name == "word/document.xml" and not prefix:
                    for ancestor in reversed(ancestors):
                        if ancestor.tag in (W + "tbl", W + "tr", W + "tc"):
                            kind_tag = {
                                W + "tbl": "table",
                                W + "tr": "row",
                                W + "tc": "cell",
                            }[ancestor.tag]
                            siblings = (
                                list(parents[ancestor])
                                if ancestor in parents
                                else [ancestor]
                            )
                            same = [n for n in siblings if n.tag == ancestor.tag]
                            container += f"/{kind_tag}[{same.index(ancestor) + 1}]"
                result.append(
                    (f"{name}{prefix}{container}/paragraph[{index}]", text, label)
                )
        coverage.update(
            {
                "format": "docx",
                "anchors": anchors,
                "stories": states,
                "unsupported": unsupported,
                "revision_policy": revisions,
                "field_policy": "cached results only; never evaluated",
                "hidden_policy": "included and labelled",
                "blocks": len(result),
                "complete_selected_scope": not unsupported,
            }
        )
    return result


def _paragraph_text(paragraph: ET.Element, revisions: str) -> str:
    output: list[str] = []
    field_stack: list[bool] = []

    def walk(node: ET.Element) -> None:
        if node is not paragraph and node.tag in (W + "p", W + "txbxContent"):
            return
        if revisions == "current" and node.tag in (W + "del", W + "moveFrom"):
            return
        if node.tag == MC + "AlternateContent":
            chosen = node.find(MC + "Choice")
            if chosen is None:
                chosen = node.find(MC + "Fallback")
            if chosen is not None:
                walk(chosen)
            return
        if node.tag == W + "fldChar":
            state = node.get(W + "fldCharType")
            if state == "begin":
                field_stack.append(False)
            elif state == "separate" and field_stack:
                field_stack[-1] = True
            elif state == "end" and field_stack:
                field_stack.pop()
        elif not field_stack or all(field_stack):
            if node.tag in (W + "t", W + "delText"):
                output.append(node.text or "")
            elif node.tag == W + "tab":
                output.append("\t")
            elif node.tag in (W + "br", W + "cr"):
                output.append("\n")
        for child in node:
            walk(child)

    walk(paragraph)
    return "".join(output)
