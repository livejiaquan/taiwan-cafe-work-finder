from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Iterable


class AtomicDurabilityError(OSError):
    """The target was replaced atomically, but directory durability is uncertain."""

    def __init__(self, path: Path, cause: OSError) -> None:
        super().__init__(f"target replaced; directory durability uncertain for {path}: {cause}")
        self.path = path


def display_path(path: Path, root: Path) -> str:
    """Return a readable path without assuming the target lives below the repo."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
    return records


def target_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644


def fsync_parent_directory(path: Path) -> None:
    """Persist a completed atomic rename when the platform supports directory fsync."""
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        directory_fd = os.open(path.parent, flags)
    except OSError as exc:
        raise OSError(f"cannot open parent directory for fsync: {path.parent}: {exc}") from exc
    try:
        try:
            os.fsync(directory_fd)
        except OSError as exc:
            unsupported_errors = {errno.EINVAL}
            if hasattr(errno, "ENOTSUP"):
                unsupported_errors.add(errno.ENOTSUP)
            if exc.errno not in unsupported_errors:
                raise OSError(f"cannot fsync parent directory for {path}: {exc}") from exc
    finally:
        os.close(directory_fd)


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = target_mode(path)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
        try:
            fsync_parent_directory(path)
        except OSError as exc:
            raise AtomicDurabilityError(path, exc) from exc
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = target_mode(path)
    count = 0
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
        try:
            fsync_parent_directory(path)
        except OSError as exc:
            raise AtomicDurabilityError(path, exc) from exc
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return count
