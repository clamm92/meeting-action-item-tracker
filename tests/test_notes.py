import pytest
from action_tracker.notes import read_note, NoteError

# tmp_path is a throwaway test folder given by pytest
def test_reads_normal_note(tmp_path):
    (tmp_path / "hello.md"). write_text("hi")
    result = read_note("hello.md", notes_dir=tmp_path)
    assert result["content"] == "hi"


def test_reads_subfolder(tmp_path):
    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "kickoff.md").write_text("hi")
    result = read_note("planning/kickoff.md", notes_dir=tmp_path)
    assert result["content"] == "hi"
    assert result["filename"] == "planning/kickoff.md"


def test_missing_file(tmp_path):
    with pytest.raises(NoteError, match="Note not found"):
        read_note("nope.md", notes_dir=tmp_path)


def test_rejects_dotdot_escape(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")  # outside the notes folder
    with pytest.raises(NoteError, match="Invalid filename"):
        read_note("../secret.txt", notes_dir=notes)


@pytest.mark.parametrize("bad_name", [
    "/etc/passwd",
    "planning/../../secret.txt",
    "a\\b.md",
    "a//b.md",
])
def test_rejects_bad_names(tmp_path, bad_name):
    with pytest.raises(NoteError, match="Invalid filename"):
        read_note(bad_name, notes_dir=tmp_path)


def test_rejects_wrong_extension(tmp_path):
    (tmp_path / "x.py").write_text("print('hi')")
    with pytest.raises(NoteError, match="Only .md and .txt"):
        read_note("x.py", notes_dir=tmp_path)


def test_rejects_file_over_1mb(tmp_path):
    (tmp_path / "big.md").write_text("x" * 1_000_001)
    with pytest.raises(NoteError, match="too large"):
        read_note("big.md", notes_dir=tmp_path)


def test_rejects_non_utf8(tmp_path):
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe\x00")
    with pytest.raises(NoteError, match="not valid UTF-8"):
        read_note("bad.md", notes_dir=tmp_path)


def test_rejects_symlinked_file(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("top secret")
    (notes / "link.md").symlink_to(outside)  # link inside notes, target outside
    with pytest.raises(NoteError, match="Invalid filename"):
        read_note("link.md", notes_dir=notes)


def test_rejects_symlinked_folder(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "secret.md").write_text("top secret")
    (notes / "linked").symlink_to(outside_dir, target_is_directory=True)
    with pytest.raises(NoteError, match="Invalid filename"):
        read_note("linked/secret.md", notes_dir=notes)
