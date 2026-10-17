import pytest

from manuscript_placeholders.collector import collect


@pytest.mark.parametrize(
    "text",
    [
        "Tkinter creates a window.",
        "Chapter XXXV describes the ending.",
        "Todoist is an application.",
        "FIXMEsuffix is ordinary text.",
    ],
)
def test_bare_tokens_do_not_match_word_prefixes(tmp_path, text):
    source = tmp_path / "chapter.txt"
    source.write_text(text)
    assert collect(source) == ()


@pytest.mark.parametrize(
    "token", ["TODO", "FIXME", "TK", "TKTK", "TKTKTK", "XXX", "XXXX"]
)
def test_bare_marker_conventions_remain_available(tmp_path, token):
    source = tmp_path / "chapter.txt"
    source.write_text(token + ": choose final wording")
    found = collect(source)
    assert len(found) == 1
    assert found[0].marker == token + ": choose final wording"
