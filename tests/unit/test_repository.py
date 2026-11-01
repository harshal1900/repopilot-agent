from repopilot.tools.repository import list_files, read_file, search_code


def make_repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\ny = 2\nTARGET = 3\n")
    (tmp_path / "data.bin").write_bytes(b"\x00\x01binary")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("secret git config")
    return tmp_path


def test_read_file_returns_text(tmp_path):
    repo = make_repo(tmp_path)
    ok, text = read_file(repo, "pkg/a.py")
    assert ok and "x = 1" in text


def test_missing_file_gives_clear_message(tmp_path):
    ok, message = read_file(make_repo(tmp_path), "nope.py")
    assert not ok and message.startswith("not found")


def test_binary_file_is_refused(tmp_path):
    ok, message = read_file(make_repo(tmp_path), "data.bin")
    assert not ok and "binary" in message


def test_search_reports_correct_line_number(tmp_path):
    hits = search_code(make_repo(tmp_path), "TARGET")
    assert hits == [("pkg/a.py", 3, "TARGET = 3")]


def test_list_files_never_lists_git(tmp_path):
    files = list_files(make_repo(tmp_path))
    assert not any(name.startswith(".git/") for name in files)
    assert "pkg/a.py" in files
