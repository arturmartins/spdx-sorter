# Development Plan

## Outcome

Create a small package whose dependency-free canonicalization, optional
validation, file handling, and CLI behavior can be understood and tested
independently.

## Package structure

The implementation will use a `src/` layout:

```text
src/spdx_sorter/
├── __init__.py       # supported public API
├── __main__.py       # python -m spdx_sorter
├── cli.py            # argument parsing, messages, exit codes
├── sorting.py        # pure canonicalization rules and implementation
├── validation.py     # optional adapter around spdx-tools
├── version.py        # package version and SPDX-version detection
├── io.py             # UTF-8 reads and safe atomic replacement
└── py.typed           # typed-package marker
```

`sort_spdx.py` will be removed when the package entry point is introduced. The
repository has no published compatibility contract, so no forwarding shim is
required.

## Public Python API

`spdx_sorter.__init__` will expose only:

```python
def sort_document(value: JSONValue) -> JSONValue: ...
def sort_json(text: str) -> str: ...
def validate_document(value: JSONValue) -> tuple[ValidationIssue, ...]: ...
```

`JSONValue` represents JSON primitives, lists, and string-keyed dictionaries.
`ValidationIssue` is an immutable project-owned dataclass containing a message,
an optional JSON location, and an optional SPDX element identifier. Upstream
`spdx-tools` model and error types are not part of this package's API.

`sort_document` returns a new structure and never mutates its argument. The
sorting path uses only the Python standard library: it parses JSON into JSON
values, applies the project-owned rules, and renders those values directly.
It must never deserialize into, or serialize output through, `spdx-tools`.
That preserves fields and values that a validator model may not represent.

`sort_json` emits UTF-8-compatible JSON with two-space indentation,
non-ASCII characters preserved, and exactly one trailing newline.

Installed distributions resolve `__version__` with `importlib.metadata`. An
uninstalled source checkout uses the current package version as a development
fallback; release changes must keep that fallback aligned with
`project.version` even though published installations use metadata.

## Canonicalization contract

The algorithm processes children before their parent:

1. Recursively normalize every dictionary value and list member.
2. Reconstruct dictionaries with lexicographically ordered keys.
3. Sort known set-semantic string arrays.
4. Sort recognized SPDX object arrays using their configured identity fields.
5. Use normalized, type-aware JSON as the final tie-breaker.

Sort keys must distinguish missing values, `null`, booleans, numbers, and
strings. They must not use `value or ""` or untyped `str(value)` conversions,
which collapse distinct JSON values.

A recognized object array is reordered only when every member is an object and
matches at least one configured identity field. Mixed, malformed, or unknown
arrays retain their input order. Exact duplicate objects are allowed because
their relative order is unobservable.

The stable rule registry covers SPDX 2.2 and 2.3 arrays such as packages,
files, relationships, checksums, annotations, external references, snippets,
external document references, extracted license information, and documented
set-semantic string properties. Experimental 3.x rules live in a visibly
separate registry and are not described as stable support.

Version detection is pure library logic. Normal successful runs remain quiet;
the CLI warns only for unsupported or experimental versions.

## Validation boundary

`validation.py` adapts `spdx-tools>=0.8.5,<0.9`, supplied only by the
`validation` optional dependency extra. The base install has no runtime
dependency on `spdx-tools`. Validation is deliberately independent from
sorting:

- Sorting stays tolerant of incomplete producer output.
- `--validate` rejects parsing or conformance failures before writing output.
- Unsupported and experimental versions produce a clear diagnostic instead of
  being silently treated as validated.
- Validation messages are mapped into `ValidationIssue` instances in stable,
  deterministic order.

If `--validate` is requested without the extra installed, the CLI reports an
actionable installation diagnostic and performs no write. A successful
validation does not authorize a different rendering path: output always comes
from the lossless stdlib sorter.

Replacing or upgrading the validator must require changes only in this adapter
and its contract tests.

## CLI contract

```text
spdx-sort [--check | --in-place] [--validate] [INPUT]
```

- With no input, read stdin and write stdout.
- With `INPUT`, read the file and write stdout.
- `--in-place INPUT` atomically replaces that file.
- `--check` compares the canonical rendering without writing.
- `--validate` validates before output, comparison, or replacement.
- `--check` and `--in-place` are mutually exclusive.
- `--in-place` requires a real file path and rejects stdin.
- `python -m spdx_sorter` behaves exactly like `spdx-sort`.

Exit codes are stable public behavior:

| Code | Meaning |
|---|---|
| `0` | Sorting or validation succeeded; check input was already canonical |
| `1` | `--check` found a document that needs normalization |
| `2` | Usage, JSON parsing, validation, or I/O failure |

Routine output contains JSON only on stdout. Diagnostics and warnings go to
stderr, never include a traceback, and identify the relevant input path.

## Safe in-place writes

In-place mutation follows these rules:

1. Resolve a symlink to its target so the link itself remains intact.
2. Read the target's permission bits before creating a temporary file.
3. Create the temporary file in the target directory.
4. Write UTF-8 text, flush it, apply the original permission bits, and `fsync`.
5. Replace the target atomically with `os.replace`.
6. Best-effort `fsync` the containing directory on platforms that support it.
7. Remove the temporary file after every pre-replacement failure.

Atomic replacement intentionally breaks hard-link identity. That trade-off is
documented because preserving hard links would require non-atomic overwriting.
Ownership and extended-attribute preservation are outside the 0.1.0 contract;
normal operation assumes the caller owns the destination.

## Acceptance criteria

- The confirmed nested-array example is canonical after one pass.
- Sorting is deterministic across repeated processes and input permutations.
- All public functions are typed and documented.
- Validation dependency types cannot escape the adapter.
- Base-install sorting works without third-party runtime dependencies, and
  validated output is byte-rendered only by the project sorter.
- No normal CLI failure prints a traceback or partially replaces a file.
- Symlink targets and ordinary file permission bits behave as documented.
