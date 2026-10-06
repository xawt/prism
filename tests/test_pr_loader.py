import json
from pathlib import Path

import pytest

from prism import cli
from prism.pr_loader import PrCommit, PrFile, PrFileType, PrLoadError, load_pr, tree_lines

EXAMPLE_PR = Path(__file__).parent.parent / "skills/fetch-pr/example/pr-pallets-click-1582"


def commit_row(oid: str, headline: str = "headline", body: str = "") -> dict:
    return {
        "oid": oid,
        "messageHeadline": headline,
        "messageBody": body,
        "authors": [{"name": "Ada", "login": "ada"}],
        "authoredDate": "2020-06-10T22:33:34Z",
        "committedDate": "2020-06-24T21:03:29Z",
    }


def make_pr_dir(root: Path, commits: list[dict] | None = None) -> Path:
    """A minimal PR directory; each commit gets its matching diffs/NNN-<sha7>.diff."""
    commits = commits or []
    root.mkdir(parents=True, exist_ok=True)
    (root / "meta.json").write_text("{}")
    (root / "description.md").write_text("")
    (root / "commits.json").write_text(json.dumps(commits))
    if commits:
        (root / "diffs").mkdir()
    for i, row in enumerate(commits, start=1):
        (root / "diffs" / f"{i:03d}-{row['oid'][:7]}.diff").write_text(f"diff {i}")
    return root


def make_commit(tmp_path, headline: str = "fix bug", body: str = "") -> PrCommit:
    diff = tmp_path / "001-abc1234.diff"
    diff.write_text("+added")
    return PrCommit(
        index=1,
        oid="abc1234def",
        headline=headline,
        body=body,
        authors=["Ada"],
        authored_at="2020-06-10T22:33:34Z",
        committed_at="2020-06-24T21:03:29Z",
        diff=PrFile(type=PrFileType.DIFF, name=diff.name, path=diff),
    )


def test_tree_lines(tmp_path):
    root = tmp_path / "pr"
    (root / "diffs").mkdir(parents=True)
    (root / "diffs" / "001-a.diff").touch()
    (root / "diffs" / "002-b.diff").touch()
    (root / "meta.json").touch()
    (root / ".DS_Store").touch()

    assert tree_lines(root) == [
        "pr/",
        "├── diffs/",
        "│   ├── 001-a.diff",
        "│   └── 002-b.diff",
        "└── meta.json",
    ]


def test_pr_file_reads_text_on_first_use(tmp_path):
    path = tmp_path / "001-a.diff"
    path.write_text("first")
    pr_file = PrFile(type=PrFileType.DIFF, name=path.name, path=path)

    assert not pr_file.loaded
    assert pr_file.text == "first"
    assert pr_file.loaded


def test_pr_file_unload_reads_file_again(tmp_path):
    path = tmp_path / "001-a.diff"
    path.write_text("first")
    pr_file = PrFile(type=PrFileType.DIFF, name=path.name, path=path)
    assert pr_file.text == "first"

    path.write_text("second")
    assert pr_file.text == "first"

    pr_file.unload()
    assert not pr_file.loaded
    assert pr_file.text == "second"


def test_pr_file_does_not_cache_text_above_limit(tmp_path):
    path = tmp_path / "001-a.diff"
    path.write_text("0123456789")
    pr_file = PrFile(type=PrFileType.DIFF, name=path.name, path=path, cache_limit=5)

    assert pr_file.text == "0123456789"
    assert not pr_file.loaded


def test_pr_file_context_wraps_text_in_tag(tmp_path):
    path = tmp_path / "001-a.diff"
    path.write_text("+added")
    pr_file = PrFile(type=PrFileType.DIFF, name=path.name, path=path)

    assert pr_file.context() == '<diff name="001-a.diff">\n+added\n</diff>'


def test_commit_message_with_body(tmp_path):
    commit = make_commit(tmp_path, headline="fix bug", body="details")

    assert commit.message() == "fix bug\n\ndetails"


def test_commit_message_without_body(tmp_path):
    commit = make_commit(tmp_path, headline="fix bug")

    assert commit.message() == "fix bug"


def test_commit_context_has_message_but_no_diff(tmp_path):
    commit = make_commit(tmp_path, headline="fix bug", body="details")

    assert commit.context() == '<commit sha="abc1234" index="1">\nfix bug\n\ndetails\n</commit>'
    assert not commit.diff.loaded


def test_load_pr_example():
    pr_files = load_pr(EXAMPLE_PR)
    commits = pr_files["commits"]

    assert [c.short_oid for c in commits] == ["cb37854", "81ff0ae", "b38cb0e"]
    assert [c.diff.name for c in commits] == [
        "001-cb37854.diff",
        "002-81ff0ae.diff",
        "003-b38cb0e.diff",
    ]
    assert commits[1].index == 2
    assert commits[1].headline == "refactor version_option"
    assert commits[1].body.startswith("option() returns a decorator")
    assert commits[1].authors == ["David Lord"]
    assert len(pr_files["discussion"]) == 15
    assert pr_files["discussion"][0].name == "001-issue_comment-0x1za.md"
    assert all(f.type == PrFileType.COMMENT for f in pr_files["discussion"])
    files = [pr_files["meta"], pr_files["description"], *pr_files["discussion"]]
    assert not any(f.loaded for f in files + [c.diff for c in commits])


def test_load_pr_without_commits_and_discussion(tmp_path):
    pr_files = load_pr(make_pr_dir(tmp_path))

    assert pr_files["commits"] == []
    assert pr_files["discussion"] == []


def test_load_pr_requires_meta(tmp_path):
    make_pr_dir(tmp_path)
    (tmp_path / "meta.json").unlink()

    with pytest.raises(PrLoadError, match="missing meta.json"):
        load_pr(tmp_path)


def test_load_pr_requires_diff_for_each_commit(tmp_path):
    make_pr_dir(tmp_path, [commit_row("aaaaaaa1"), commit_row("bbbbbbb2")])
    (tmp_path / "diffs" / "002-bbbbbbb.diff").unlink()

    with pytest.raises(PrLoadError, match="missing diffs/002-bbbbbbb.diff for commit bbbbbbb2"):
        load_pr(tmp_path)


def test_load_pr_rejects_diff_with_wrong_sha(tmp_path):
    make_pr_dir(tmp_path, [commit_row("aaaaaaa1")])
    (tmp_path / "diffs" / "001-aaaaaaa.diff").rename(tmp_path / "diffs" / "001-ccccccc.diff")

    with pytest.raises(PrLoadError, match="missing diffs/001-aaaaaaa.diff"):
        load_pr(tmp_path)


def test_load_pr_rejects_diff_without_commit(tmp_path):
    make_pr_dir(tmp_path, [commit_row("aaaaaaa1")])
    (tmp_path / "diffs" / "002-ddddddd.diff").write_text("extra")

    with pytest.raises(PrLoadError, match="diffs/002-ddddddd.diff has no matching commit"):
        load_pr(tmp_path)


def test_load_pr_rejects_invalid_commits_json(tmp_path):
    make_pr_dir(tmp_path)
    (tmp_path / "commits.json").write_text("[{")

    with pytest.raises(PrLoadError, match="commits.json: invalid JSON"):
        load_pr(tmp_path)


def test_load_pr_rejects_commit_without_oid(tmp_path):
    make_pr_dir(tmp_path)
    (tmp_path / "commits.json").write_text(json.dumps([{"messageHeadline": "x"}]))

    with pytest.raises(PrLoadError, match="commits.json: commit 1 has no oid"):
        load_pr(tmp_path)


def test_list_prints_tree(tmp_path, capsys):
    make_pr_dir(tmp_path)

    cli.main(["--path", str(tmp_path), "--list"])

    assert capsys.readouterr().out == (
        f"{tmp_path.name}/\n├── commits.json\n├── description.md\n└── meta.json\n"
    )


def test_print_pr_files(capsys):
    cli.main(["--path", str(EXAMPLE_PR), "--print-pr-files"])

    out = capsys.readouterr().out
    assert out.startswith("{'meta': PrFile(type='meta', name='meta.json'")
    assert "'commits': [PrCommit(index=1, oid='cb37854'" in out
    for name in ("001-cb37854.diff", "002-81ff0ae.diff", "003-b38cb0e.diff"):
        assert name in out
    assert "'diffs'" not in out
    assert "loaded=True" not in out


def test_path_must_be_a_directory(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--path", str(tmp_path / "missing")])

    assert exc.value.code == 2
    assert "not a directory" in capsys.readouterr().err


def test_path_must_contain_pr_files(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--path", str(tmp_path)])

    assert exc.value.code == 2
    assert "missing meta.json" in capsys.readouterr().err
