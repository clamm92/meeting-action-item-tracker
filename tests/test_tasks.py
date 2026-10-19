import json
import re

import pytest

from action_tracker.tasks import TasksError, save_items


def good_item(**changes):
    """A valid item. Pass keyword arguments to change or remove (None) a field."""
    item = {
        "task": "Send the Q1 report",
        "owner": "Sam",
        "due_date": "2025-01-10",
        "source_file": "planning/kickoff.md",
    }
    item.update(changes)
    return item


# ---------- approval gate ----------

def test_refuses_when_not_approved(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="Not approved"):
        save_items([good_item()], approved=False, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_refuses_when_approved_is_missing(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="Not approved"):
        save_items([good_item()], tasks_file=tasks_file)
    assert not tasks_file.exists()


@pytest.mark.parametrize("not_true", ["true", 1, "yes", None])
def test_refuses_when_approved_is_not_exactly_true(tmp_path, not_true):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="Not approved"):
        save_items([good_item()], approved=not_true, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_refusal_leaves_existing_file_unchanged(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text("[]")
    with pytest.raises(TasksError):
        save_items([good_item()], approved=False, tasks_file=tasks_file)
    assert tasks_file.read_text() == "[]"


# ---------- number of items ----------

@pytest.mark.parametrize("bad_list", [[], "not a list", None, [good_item()] * 51])
def test_rejects_wrong_number_of_items(tmp_path, bad_list):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="between 1 and 50"):
        save_items(bad_list, approved=True, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_accepts_exactly_50_items(tmp_path):
    result = save_items([good_item()] * 50, approved=True, tasks_file=tmp_path / "tasks.json")
    assert result == {"saved": 50, "total_in_file": 50}


# ---------- successful saves ----------

def test_save_creates_new_file_with_right_json(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    result = save_items([good_item()], approved=True, tasks_file=tasks_file)

    assert result == {"saved": 1, "total_in_file": 1}
    data = json.loads(tasks_file.read_text())
    assert len(data) == 1
    saved = data[0]
    assert saved["task"] == "Send the Q1 report"
    assert saved["owner"] == "Sam"
    assert saved["due_date"] == "2025-01-10"
    assert saved["source_file"] == "planning/kickoff.md"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", saved["created_at"])
    assert set(saved) == {"task", "owner", "due_date", "source_file", "created_at"}


def test_save_appends_to_existing_file(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    save_items([good_item(task="First")], approved=True, tasks_file=tasks_file)
    result = save_items(
        [good_item(task="Second"), good_item(task="Third")],
        approved=True,
        tasks_file=tasks_file,
    )

    assert result == {"saved": 2, "total_in_file": 3}
    tasks = [entry["task"] for entry in json.loads(tasks_file.read_text())]
    assert tasks == ["First", "Second", "Third"]


def test_optional_fields_are_saved_as_null(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    save_items(
        [{"task": "Do it", "source_file": "a.md"}],
        approved=True,
        tasks_file=tasks_file,
    )
    saved = json.loads(tasks_file.read_text())[0]
    assert saved["owner"] is None
    assert saved["due_date"] is None


def test_unknown_fields_are_not_saved(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    save_items([good_item(extra="ignore me")], approved=True, tasks_file=tasks_file)
    assert "extra" not in json.loads(tasks_file.read_text())[0]


def test_no_temp_files_left_behind(tmp_path):
    save_items([good_item()], approved=True, tasks_file=tmp_path / "tasks.json")
    assert [p.name for p in tmp_path.iterdir()] == ["tasks.json"]


# ---------- bad items: all or nothing ----------

def test_one_bad_item_means_nothing_is_written(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    items = [good_item(), good_item(task=""), good_item()]
    with pytest.raises(TasksError, match="Item 2 is invalid"):
        save_items(items, approved=True, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_bad_item_leaves_existing_file_unchanged(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    save_items([good_item()], approved=True, tasks_file=tasks_file)
    before = tasks_file.read_text()
    with pytest.raises(TasksError):
        save_items([good_item(), good_item(task="")], approved=True, tasks_file=tasks_file)
    assert tasks_file.read_text() == before


@pytest.mark.parametrize("bad_due_date", [
    "2025-02-30",     # not a real date
    "next Friday",    # free text
    "2025-2-3",       # not zero-padded
    "20250110",       # no dashes
    "2025-01-10T09:00",  # has a time
    20250110,         # not text
])
def test_rejects_bad_due_dates(tmp_path, bad_due_date):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="Item 1 is invalid: due_date"):
        save_items([good_item(due_date=bad_due_date)], approved=True, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_rejects_missing_source_file(tmp_path):
    item = good_item()
    del item["source_file"]
    with pytest.raises(TasksError, match="source_file is required"):
        save_items([item], approved=True, tasks_file=tmp_path / "tasks.json")


@pytest.mark.parametrize("bad_source", ["../secret.md", "/etc/passwd", "a//b.md", "a\\b.md"])
def test_rejects_unsafe_source_file_paths(tmp_path, bad_source):
    with pytest.raises(TasksError, match="source_file is not a valid path"):
        save_items([good_item(source_file=bad_source)], approved=True, tasks_file=tmp_path / "t.json")


def test_rejects_source_file_with_wrong_extension(tmp_path):
    with pytest.raises(TasksError, match=r"must end in \.md or \.txt"):
        save_items([good_item(source_file="x.py")], approved=True, tasks_file=tmp_path / "t.json")


def test_source_file_does_not_need_to_exist(tmp_path):
    result = save_items(
        [good_item(source_file="never/created.md")],
        approved=True,
        tasks_file=tmp_path / "tasks.json",
    )
    assert result["saved"] == 1


@pytest.mark.parametrize("bad_item", [
    "just a string",
    {"owner": "Sam", "source_file": "a.md"},         # no task
    good_item(task="   "),                           # blank task
    good_item(task="x" * 501),                       # task too long
    good_item(owner="x" * 101),                      # owner too long
    good_item(owner=123),                            # owner not text
])
def test_rejects_other_bad_items(tmp_path, bad_item):
    tasks_file = tmp_path / "tasks.json"
    with pytest.raises(TasksError, match="Item 1 is invalid"):
        save_items([bad_item], approved=True, tasks_file=tasks_file)
    assert not tasks_file.exists()


def test_accepts_task_and_owner_at_the_limits(tmp_path):
    result = save_items(
        [good_item(task="x" * 500, owner="y" * 100)],
        approved=True,
        tasks_file=tmp_path / "tasks.json",
    )
    assert result["saved"] == 1


# ---------- broken tasks.json ----------

@pytest.mark.parametrize("broken_content", [
    "this is not json",
    '{"not": "a list"}',
    "",
])
def test_broken_tasks_file_is_refused_and_unchanged(tmp_path, broken_content):
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_text(broken_content)
    with pytest.raises(TasksError, match="Tasks file is unreadable"):
        save_items([good_item()], approved=True, tasks_file=tasks_file)
    assert tasks_file.read_text() == broken_content


def test_tasks_file_with_bad_utf8_is_refused_and_unchanged(tmp_path):
    tasks_file = tmp_path / "tasks.json"
    tasks_file.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(TasksError, match="Tasks file is unreadable"):
        save_items([good_item()], approved=True, tasks_file=tasks_file)
    assert tasks_file.read_bytes() == b"\xff\xfe\x00"
