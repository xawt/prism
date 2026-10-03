import pytest

from prism import cli
from prism.pr_loader import tree_lines


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


def test_list_prints_tree(tmp_path, capsys):
    (tmp_path / "meta.json").touch()

    cli.main(["--path", str(tmp_path), "--list"])

    assert capsys.readouterr().out == f"{tmp_path.name}/\n└── meta.json\n"


def test_path_must_be_a_directory(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--path", str(tmp_path / "missing")])

    assert exc.value.code == 2
    assert "not a directory" in capsys.readouterr().err
