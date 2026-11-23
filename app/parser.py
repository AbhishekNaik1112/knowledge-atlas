"""OKF frontmatter parsing — the one place the OKF spec rules live.

Splits a Markdown file into validated metadata + body. `type` is the only required field;
everything else is optional. Concept IDs are derived from the file path (spec: path minus `.md`).
`index.md` / `log.md` are structural navigation files, not concepts.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

import frontmatter
import yaml

KNOWN_FIELDS = {"type", "title", "description", "resource", "tags", "timestamp"}
STRUCTURAL_FILES = {"index.md", "log.md"}


class MissingTypeError(ValueError):
    """Raised when a concept file lacks the required non-empty `type` field."""


class InvalidFrontmatterError(ValueError):
    """Raised when a concept file has malformed YAML frontmatter."""


def _opt_str(val: object) -> str | None:
    return val if isinstance(val, str) else None


@dataclass(frozen=True)
class ParsedConcept:
    id: str
    bundle: str
    type: str
    title: str | None
    description: str | None
    resource: str | None
    timestamp: dt.datetime | None
    tags: list[str]
    body: str
    extra: dict[str, Any] = field(default_factory=dict)


def _normalize_path(rel_path: str) -> str:
    p = rel_path.replace("\\", "/").strip()
    if p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def is_structural_file(rel_path: str) -> bool:
    """True for index.md / log.md in any directory — grouping/log files, not concepts."""
    basename = _normalize_path(rel_path).rsplit("/", 1)[-1].lower()
    return basename in STRUCTURAL_FILES


def derive_id(rel_path: str) -> str:
    """'tables/users.md' -> 'tables/users'. Normalizes separators, strips leading ./ and /."""
    p = _normalize_path(rel_path)
    if p.lower().endswith(".md"):
        p = p[:-3]
    return p


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = raw.split(",")
    elif isinstance(raw, (list, tuple)):
        parts = list(raw)
    else:
        parts = [raw]

    out: list[str] = []
    for part in parts:
        tag = str(part).strip().lower()
        if tag and tag not in out:
            out.append(tag)
    return out


def _coerce_timestamp(raw: Any) -> dt.datetime | None:
    if raw is None:
        return None
    if isinstance(raw, dt.datetime):
        return raw
    if isinstance(raw, dt.date):
        return dt.datetime(raw.year, raw.month, raw.day, tzinfo=dt.timezone.utc)
    if isinstance(raw, str):
        try:
            return dt.datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def parse_concept(rel_path: str, raw_text: str, bundle: str) -> ParsedConcept:
    """Parse a single OKF Markdown file. Raises MissingTypeError if `type` is absent/blank."""
    try:
        post = frontmatter.loads(raw_text)
    except yaml.YAMLError as exc:
        raise InvalidFrontmatterError(f"{rel_path!r} has invalid YAML frontmatter: {exc}") from exc
    meta = post.metadata

    type_ = meta.get("type")
    if not isinstance(type_, str) or not type_.strip():
        raise MissingTypeError(f"{rel_path!r} is missing a non-empty `type` field")

    extra = {k: v for k, v in meta.items() if k not in KNOWN_FIELDS}

    return ParsedConcept(
        id=derive_id(rel_path),
        bundle=bundle,
        type=type_.strip(),
        title=_opt_str(meta.get("title")),
        description=_opt_str(meta.get("description")),
        resource=_opt_str(meta.get("resource")),
        timestamp=_coerce_timestamp(meta.get("timestamp")),
        tags=normalize_tags(meta.get("tags")),
        body=post.content,
        extra=extra,
    )
