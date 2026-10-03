from pathlib import Path

import pytest

from prism import cli
from prism.pr_loader import PrFile, PrFileType, PrLoadError, load_pr, tree_lines

EXAMPLE_PR = Path(__file__).parent.parent / "skills/fetch-pr/example/pr-pallets-click-1582"


def make_pr_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name in ("meta.json", "description.md", "commits.json"):
        (root / name).write_text("{}")
    return root


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


def test_load_pr_example():
    pr_files = load_pr(EXAMPLE_PR)

    assert pr_files["meta"].type == PrFileType.META
    assert [f.name for f in pr_files["diffs"]] == [
        "001-cb37854.diff",
        "002-81ff0ae.diff",
        "003-b38cb0e.diff",
    ]
    assert len(pr_files["discussion"]) == 15
    assert pr_files["discussion"][0].name == "001-issue_comment-0x1za.md"
    assert all(f.type == PrFileType.COMMENT for f in pr_files["discussion"])
    singles = [pr_files["meta"], pr_files["description"], pr_files["commits"]]
    assert not any(f.loaded for f in singles + pr_files["diffs"] + pr_files["discussion"])


def test_load_pr_without_diffs_and_discussion(tmp_path):
    pr_files = load_pr(make_pr_dir(tmp_path))

    assert pr_files["diffs"] == []
    assert pr_files["discussion"] == []


def test_load_pr_requires_meta(tmp_path):
    make_pr_dir(tmp_path)
    (tmp_path / "meta.json").unlink()

    with pytest.raises(PrLoadError, match="missing meta.json"):
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
    for name in ("001-cb37854.diff", "002-81ff0ae.diff", "003-b38cb0e.diff"):
        assert name in out
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
