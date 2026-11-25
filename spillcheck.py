#!/usr/bin/env python3
import argparse
import hashlib
import os
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

FileState = tuple[str, int, bytes | str]
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)


def relative_prefix(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or PureWindowsPath(value).drive
    ):
        raise argparse.ArgumentTypeError("use a relative path like dist or docs/index.md")
    return path.as_posix()


def under(path: str, prefixes: list[str]) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


def content_hash(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.digest()


def snapshot(root: Path, ignored: list[str]) -> dict[str, FileState]:
    files: dict[str, FileState] = {}
    pending = [root]

    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                path = Path(entry.path)
                name = path.relative_to(root).as_posix()

                if entry.name == ".git" or under(name, ignored):
                    continue

                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    files[name] = ("link", 0, os.readlink(path))
                elif getattr(info, "st_file_attributes", 0) & REPARSE_POINT:
                    # Don't descend into Windows junctions.
                    continue
                elif stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    files[name] = ("file", stat.S_IMODE(info.st_mode), content_hash(path))

    return files


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        description="Show what changed on disk after a command.",
        usage="%(prog)s [-C DIR] [--allow PATH] [--ignore PATH] -- COMMAND [ARG ...]",
        allow_abbrev=False,
    )
    parser.add_argument("-C", "--root", type=Path, default=Path("."),
                        help="directory to scan and run the command in")
    parser.add_argument("--allow", action="append", type=relative_prefix, default=[],
                        help="allow changes at this path or below it (repeatable)")
    parser.add_argument("--ignore", action="append", type=relative_prefix, default=[],
                        help="skip this path and everything below it (repeatable)")

    if "--" not in argv:
        parser.parse_args(argv)  # Handle --help before requiring a command.
        parser.error("put -- before the command")

    split = argv.index("--")
    options = parser.parse_args(argv[:split])
    command = argv[split + 1:]
    if not command:
        parser.error("missing command after --")

    stage = "before scan"
    try:
        root = options.root.resolve(strict=True)
        before = snapshot(root, options.ignore)
        stage = "running command"
        status = subprocess.run(command, cwd=root, check=False).returncode
        stage = "after scan"
        after = snapshot(root, options.ignore)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"spillcheck: {stage}: {error}", file=sys.stderr)
        return 2

    print("Spillcheck receipt:", file=sys.stderr)
    changed = violated = False

    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue

        changed = True
        mark = "+" if old is None else "-" if new is None else "~"
        unexpected = bool(options.allow) and not under(name, options.allow)
        violated = violated or unexpected
        suffix = "  [outside allowlist]" if unexpected else ""
        print(f"{mark} {name!r}{suffix}", file=sys.stderr)

    if not changed:
        print("(no file changes)", file=sys.stderr)

    if status:
        return status if status > 0 else 128 - status

    return 3 if violated else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nspillcheck: interrupted; receipt incomplete", file=sys.stderr)
        sys.exit(130)
