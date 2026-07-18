from pathlib import Path

from docx import Document

from manuscript_placeholders.collector import collect


def test_markdown_sections_and_categories(tmp_path: Path) -> None:
    source = tmp_path / "story.md"
    source.write_text("# Chapter One\nMara entered [NAME THIS TAVERN].\nTODO: improve this exchange\n# Chapter Two\n[RESEARCH inheritance law]\n", encoding="utf-8")
    items = collect(source)
    assert [item.category for item in items] == ["Missing names", "Revision notes", "Research"]
    assert items[0].section == "Chapter One"
    assert items[2].section == "Chapter Two"


def test_docx_headings_are_preserved(tmp_path: Path) -> None:
    source = tmp_path / "story.docx"
    document = Document()
    document.add_heading("Chapter Seven", level=1)
    document.add_paragraph("The room was cold. <insert argument here>")
    document.save(source)
    items = collect(source)
    assert len(items) == 1
    assert items[0].section == "Chapter Seven"
    assert items[0].category == "Insertions"


def test_overlapping_bracket_patterns_are_not_duplicated(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("[RESEARCH THIS CUSTOM]\n", encoding="utf-8")
    assert len(collect(source)) == 1


def test_custom_pattern(tmp_path: Path) -> None:
    source = tmp_path / "story.txt"
    source.write_text("FLAGME later\n", encoding="utf-8")
    items = collect(source, (r"FLAGME",))
    assert items[0].category == "Custom"
