# Spillcheck

**Get a receipt for what your command changed — even files Git ignores.**

Use it to check that a generator, formatter, or build only changes the files
you expect. No Git repository or pip install required. Python 3.10+.

## Try it

Run this from the directory containing `spillcheck.py`, with a fresh `demo/`:

```sh
mkdir demo
python spillcheck.py -C demo --allow dist -- python -c "from pathlib import Path as P; P('dist').mkdir(); P('dist/report.txt').write_bytes(b'ok'); P('debug.log').write_bytes(b'oops')"
```

```text
Spillcheck receipt:
+ 'debug.log'  [outside allowlist]
+ 'dist/report.txt'
```

The command succeeded, but Spillcheck exits with `3` because `debug.log`
is outside `dist/`.

## Why not just `git status`?

Because the interesting spills are often **ignored**. A generator that updates
`debug.log`, a cache directory, or a `.env` file won't show up in
`git status` once it's in `.gitignore`. Spillcheck compares raw filesystem
snapshots, so it sees them anyway — and it can fail CI when a command
writes somewhere it shouldn't.

## Use it in a project

```sh
python spillcheck.py --ignore .venv --allow generated -- python tools/generate.py
```

- `+` added, `~` changed, `-` removed. The receipt goes to stderr.
- Without `--allow`, Spillcheck only reports changes.
- Repeat `--allow` or `--ignore` for multiple paths. These are literal,
  case-sensitive paths relative to the scan root, not globs.
- `.git` and explicitly ignored paths are skipped. `.gitignore` is not applied.
- If both scans succeed, a failing command keeps its exit code. Otherwise,
  Spillcheck returns `3` for an allowlist violation, `0` for success, or `2`
  for a tool or usage error.

## Use it in CI

```yaml
- name: Check the generator stayed in its lane
  run: python spillcheck.py --allow dist -- python tools/generate.py
```

A non-zero exit fails the job exactly when the command wrote outside `dist/`.

## Scope

Spillcheck compares two snapshots. It doesn't block writes, track changes
outside the scan root, or see files created and deleted between snapshots.
Concurrent changes can appear in the receipt too. Regular file contents
are read twice, but only paths are printed. Empty directories and timestamp-only
changes aren't reported, and symlinks aren't followed.

Run only commands you trust. This is a check, not a sandbox.

## Tests

```sh
python -m unittest -v
```

## More small tools

- **[envspy](https://github.com/roma36637-alt/envspy)** — run a command and see which environment variables it really reads (Python + Node).
- **[repo-rpg](https://github.com/roma36637-alt/repo-rpg)** — turn a GitHub profile into an RPG character card (SVG).
- **[smeta-delta](https://github.com/roma36637-alt/smeta-delta)** — explain *why* an estimate total changed (volume / unit price / composition).

All of them: no dependencies, MIT, tested on Linux, macOS and Windows.

## License

MIT.
