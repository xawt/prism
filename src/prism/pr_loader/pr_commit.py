"""A commit of the PR with its message and its diff file."""

from dataclasses import dataclass

from prism.pr_loader.pr_file import PrFile


@dataclass
class PrCommit:
    """A commit from `commits.json`, paired with its file in `diffs/`.

    `index` is the 1-based position in `commits.json`, which is also the `NNN` in the diff name.
    """

    index: int
    oid: str
    headline: str
    body: str
    authors: list[str]
    authored_at: str
    committed_at: str
    diff: PrFile

    @property
    def short_oid(self) -> str:
        return self.oid[:7]

    def message(self) -> str:
        """The headline, then the body after a blank line if there is one."""
        return f"{self.headline}\n\n{self.body}" if self.body else self.headline

    def context(self) -> str:
        """The message wrapped in a tag naming the commit, for use in a prompt. No diff."""
        return f'<commit sha="{self.short_oid}" index="{self.index}">\n{self.message()}\n</commit>'

    def __repr__(self) -> str:
        return (
            f"PrCommit(index={self.index}, oid={self.short_oid!r}, "
            f"headline={self.headline!r}, diff={self.diff!r})"
        )
