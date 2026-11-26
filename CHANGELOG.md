# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-11-25

### Added

- `spillcheck` CLI: snapshot the working tree, run a command, then print a
  receipt of everything that changed on disk.
- `--allow PATH` allowlist (repeatable). Changes outside it are flagged with
  `[outside allowlist]` and the process exits with code `3`.
- `--ignore PATH` to skip subtrees entirely (repeatable).
- `-C / --root DIR` to choose the directory to scan and run in.
- Detects new, modified and deleted files, **including paths Git ignores**
  (`.gitignore` entries, logs, caches).
- 4 unit tests, run on Linux, macOS and Windows in CI.

[Unreleased]: https://github.com/roma36637-alt/spillcheck/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/roma36637-alt/spillcheck/releases/tag/v1.0.0
