from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from manuscript_placeholders.epub import read_epub

CONTAINER = (
    '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="OPS/package.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)


def book(
    tmp_path: Path, manifest: str, spine: str, resources: dict[str, str | bytes]
) -> Path:
    path = tmp_path / "book.epub"
    package = (
        f'<package xmlns="http://www.idpf.org/2007/opf"><manifest>{manifest}'
        f"</manifest><spine>{spine}</spine></package>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", CONTAINER)
        archive.writestr("OPS/package.opf", package)
        for name, value in resources.items():
            archive.writestr(name, value)
    return path


def item(
    identifier: str, href: str, media: str = "application/xhtml+xml", extra: str = ""
) -> str:
    return f'<item id="{identifier}" href="{href}" media-type="{media}" {extra}/>'


def test_semantic_content_order_without_duplicate_paragraphs(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "a.xhtml"),
        '<itemref idref="a"/>',
        {
            "OPS/a.xhtml": "<html><head><title>not body</title></head><body><h1>Chapter</h1>"
            "<div>direct [TODO direct]<p>[NAME nested]</p>tail [CHECK tail]</div>"
            "<table><tr><td>[TODO cell]</td><td>[NAME cell]</td></tr></table>"
            "<ul><li>outer<p>[TODO list]</p><ul><li>[NAME inner]</li></ul></li></ul>"
            "<script>[TODO invisible]</script><style>[TODO css]</style></body></html>",
        },
    )
    coverage: dict[str, object] = {}
    blocks = read_epub(path, coverage)
    text = "\n".join(b[1] for b in blocks)
    assert text.count("[NAME nested]") == 1
    assert "direct [TODO direct]" in text
    assert "tail [CHECK tail]" in text
    assert "[TODO cell]\t[NAME cell]" in text
    assert "[TODO list]" in text and "[NAME inner]" in text
    assert "invisible" not in text and "not body" not in text and "css" not in text
    assert blocks[0][2] == "Chapter"
    assert all(b[2] == "Chapter" for b in blocks)
    assert coverage["epub_status"] == "complete"
    assert all("OPS/a.xhtml/spine[1]/block[" in b[3] for b in blocks)


def test_explicit_line_break_and_preformatted_tabs(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "a.xhtml"),
        '<itemref idref="a"/>',
        {
            "OPS/a.xhtml": "<html><body><p>[TODO first<br/>second]</p>"
            "<pre>[NAME\tkept\nline]</pre></body></html>",
        },
    )
    blocks = read_epub(path, {})
    assert blocks[0][1] == "[TODO first\nsecond]"
    assert blocks[1][1] == "[NAME\tkept\nline]"


def test_spine_order_declared_encoding_and_safe_parent_path(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "../text/a.xhtml") + item("b", "b.xhtml"),
        '<itemref idref="b"/><itemref idref="a" linear="no"/>',
        {
            "text/a.xhtml": (
                '<?xml version="1.0" encoding="iso-8859-1"?>'
                "<html><body><div>[NAME café]</div></body></html>"
            ).encode("iso-8859-1"),
            "OPS/b.xhtml": "<html><body><p>[TODO first]</p></body></html>",
        },
    )
    coverage: dict[str, object] = {}
    blocks = read_epub(path, coverage)
    assert [b[1] for b in blocks] == ["[TODO first]", "[NAME café]"]
    assert "text/a.xhtml/spine[2]" in blocks[1][3]
    assert coverage["epub_status"] == "complete"


def test_text_html_fallback_honors_charset(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "a.html", "text/html"),
        '<itemref idref="a"/>',
        {
            "OPS/a.html": b'<html><head><meta charset="iso-8859-1"></head><body><div>[NAME caf\xe9]<br>[TODO later]</div></body></html>',
        },
    )
    assert read_epub(path, {})[0][1] == "[NAME café]\n[TODO later]"


def test_supported_fallback_and_explicit_partial_coverage(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("image", "image.svg", "image/svg+xml", 'fallback="text"')
        + item("text", "a.xhtml")
        + item("audio", "song.mp3", "audio/mpeg"),
        '<itemref idref="image"/><itemref idref="audio"/>',
        {
            "OPS/a.xhtml": "<html><body><p>[TODO fallback]</p></body></html>",
        },
    )
    coverage: dict[str, object] = {}
    assert read_epub(path, coverage)[0][1] == "[TODO fallback]"
    assert coverage["epub_status"] == "partial"
    assert "audio" in str(coverage["epub_omissions"])
    assert "resolved_id" in str(coverage["epub_resources"])


@pytest.mark.parametrize(
    "manifest,spine,message",
    [
        (
            item("a", "a.xhtml") + item("a", "b.xhtml"),
            '<itemref idref="a"/>',
            "duplicate ID",
        ),
        (item("a", "a.xhtml"), '<itemref idref="missing"/>', "missing manifest ID"),
        (
            item("a", "a.bin", "other", 'fallback="missing"'),
            '<itemref idref="a"/>',
            "missing manifest ID",
        ),
        (
            item("a", "a.bin", "other", 'fallback="b"')
            + item("b", "b.bin", "other", 'fallback="a"'),
            '<itemref idref="a"/>',
            "cycle",
        ),
    ],
)
def test_invalid_manifest_and_fallbacks(
    tmp_path: Path, manifest: str, spine: str, message: str
) -> None:
    path = book(tmp_path, manifest, spine, {})
    with pytest.raises(ValueError, match=message):
        read_epub(path, {})


@pytest.mark.parametrize(
    "href",
    [
        "../../escape.xhtml",
        "https://example.org/a.xhtml",
        "/absolute.xhtml",
        "%2e%2e/%2e%2e/escape.xhtml",
        "a.xhtml?download=1",
        r"dir\a.xhtml",
    ],
)
def test_unsafe_reading_resources_rejected(tmp_path: Path, href: str) -> None:
    path = book(tmp_path, item("a", href), '<itemref idref="a"/>', {})
    with pytest.raises(ValueError, match="EPUB"):
        read_epub(path, {})


def test_duplicate_zip_entries_preflight(tmp_path: Path) -> None:
    path = book(tmp_path, item("a", "a.xhtml"), '<itemref idref="a"/>', {})
    with zipfile.ZipFile(path, "a") as archive, pytest.warns(UserWarning):
        archive.writestr("OPS/package.opf", "<package/>")
    with pytest.raises(ValueError, match="duplicate"):
        read_epub(path, {})


def test_expanded_package_limit_precedes_xml_read(tmp_path: Path) -> None:
    path = tmp_path / "oversized.epub"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("payload.bin", b"\x00" * (100 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="expanded safety limit"):
        read_epub(path, {})


def test_utf16_xhtml_and_percent_encoded_local_reference(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "text%20file.xhtml#chapter"),
        '<itemref idref="a"/>',
        {
            "OPS/text file.xhtml": (
                '<?xml version="1.0" encoding="UTF-16"?>'
                "<html><body><div>[NAME café]</div></body></html>"
            ).encode("utf-16"),
        },
    )
    assert read_epub(path, {})[0][1] == "[NAME café]"


def test_empty_spine_is_an_actionable_error(tmp_path: Path) -> None:
    path = book(tmp_path, item("a", "a.xhtml"), "", {})
    with pytest.raises(ValueError, match="reading-order spine"):
        read_epub(path, {})


def test_missing_corrupt_and_encrypted_reading_parts(tmp_path: Path) -> None:
    path = book(tmp_path, item("a", "a.xhtml"), '<itemref idref="a"/>', {})
    with pytest.raises(ValueError, match="intact, unencrypted"):
        read_epub(path, {})
    path = book(
        tmp_path,
        item("a", "a.xhtml"),
        '<itemref idref="a"/>',
        {
            "OPS/a.xhtml": "<html><body>",
        },
    )
    with pytest.raises(ValueError, match="XML cannot be read"):
        read_epub(path, {})
    path = book(
        tmp_path,
        item("a", "a.xhtml"),
        '<itemref idref="a"/>',
        {
            "OPS/a.xhtml": "<html><body/></html>",
            "META-INF/encryption.xml": '<encryption><CipherReference URI="OPS/a.xhtml"/></encryption>',
        },
    )
    with pytest.raises(ValueError, match="reading resource is encrypted"):
        read_epub(path, {})


def test_entity_expansion_is_not_interpreted(tmp_path: Path) -> None:
    path = book(
        tmp_path,
        item("a", "a.xhtml"),
        '<itemref idref="a"/>',
        {
            "OPS/a.xhtml": '<!DOCTYPE html [<!ENTITY note "[TODO hidden]">]>'
            "<html><body><p>&note;</p></body></html>",
        },
    )
    with pytest.raises(ValueError, match="entities"):
        read_epub(path, {})
