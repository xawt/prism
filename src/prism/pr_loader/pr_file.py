"""A single file from a PR directory, read lazily and wrapped as tagged context."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

CACHE_LIMIT_BYTES = 256 * 1024


class PrFileType(StrEnum):
    META = "meta"
    DESCRIPTION = "description"
    COMMITS = "commits"
    DIFF = "diff"
    COMMENT = "comment"


@dataclass
class PrFile:
    """A PR file whose text is read on first use.

    Text is cached only up to `cache_limit` bytes; bigger files are read again on every access.
    `unload()` drops the cached text, and the next access reads the file again.
    """

    type: PrFileType
    name: str
    path: Path
    cache_limit: int = CACHE_LIMIT_BYTES
    _text: str | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def loaded(self) -> bool:
        return self._text is not None

    @property
    def text(self) -> str:
        if self._text is not None:
            return self._text
        text = self.path.read_text(encoding="utf-8")
        if self.size <= self.cache_limit:
            self._text = text
        return text

    def context(self) -> str:
        """The text wrapped in a tag naming its type and file, for use in a prompt."""
        return f'<{self.type} name="{self.name}">\n{self.text.rstrip("\n")}\n</{self.type}>'

    def unload(self) -> None:
        self._text = None

    def __repr__(self) -> str:
        return (
            f"PrFile(type={self.type.value!r}, name={self.name!r}, "
            f"size={self.size}, loaded={self.loaded})"
        )
