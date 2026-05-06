"""Helpers for loading the synthetic policy packet used by demos and tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_POLICY_DOCUMENT_SUFFIXES = frozenset({".md", ".txt"})
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SYNTHETIC_POLICY_PACKET_DIR = _REPOSITORY_ROOT / "data" / "synthetic" / "policy_packet"


@dataclass(frozen=True, slots=True)
class SyntheticPolicyDocument:
    """A loaded synthetic policy document."""

    path: Path
    title: str
    text: str


def load_synthetic_policy_packet(
    packet_dir: str | Path = DEFAULT_SYNTHETIC_POLICY_PACKET_DIR,
) -> tuple[SyntheticPolicyDocument, ...]:
    """Load synthetic policy documents from a packet directory.

    Files are returned in filename order so tests and demos have deterministic
    behavior across Windows, macOS, and Linux.
    """

    directory = Path(packet_dir)
    if not directory.exists():
        msg = f"Synthetic policy packet directory does not exist: {directory}"
        raise FileNotFoundError(msg)
    if not directory.is_dir():
        msg = f"Synthetic policy packet path is not a directory: {directory}"
        raise NotADirectoryError(msg)

    documents = tuple(
        _load_policy_document(path)
        for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_POLICY_DOCUMENT_SUFFIXES
    )
    if not documents:
        msg = f"No synthetic policy documents found in: {directory}"
        raise FileNotFoundError(msg)

    return documents


def _load_policy_document(path: Path) -> SyntheticPolicyDocument:
    text = path.read_text(encoding="utf-8")
    return SyntheticPolicyDocument(path=path, title=_extract_title(path, text), text=text)


def _extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("#"):
            return stripped_line.lstrip("#").strip()
        if stripped_line:
            return stripped_line
    return path.stem.replace("_", " ").title()
