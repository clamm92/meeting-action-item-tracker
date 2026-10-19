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
