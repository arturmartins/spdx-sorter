# SPDX JSON Sorter

Sort SPDX JSON files deterministically for meaningful git diffs.

## Overview

When working with SPDX Software Bill of Materials (SBOM) files in JSON format, changes can often lead to large, unhelpful diffs due to unordered keys and arrays. This script sorts SPDX JSON files in a consistent manner, ensuring that only meaningful changes are highlighted in git.




## Features

- **Version compatibility checking** - Validates SPDX 2.x and 3.x formats
- **Sorts object keys** alphabetically at all levels
- **Version-aware sorting** - Handles differences between SPDX 2.x and 3.x
- **Sorts arrays** by their identifying fields:
  - `packages` → by SPDXID/spdxId, then name
  - `files` → by SPDXID/spdxId, then fileName
  - `relationships` → by spdxElementId, relationshipType, relatedSpdxElement
  - `externalRefs` → by referenceCategory, referenceType, referenceLocator
  - `checksums` → by algorithm, checksumValue
  - `annotations` → by annotationDate, annotator
  - `elements` (SPDX 3.x) → by spdxId, type, name
  - And more...

## Supported SPDX Versions

- **SPDX 2.x**: 2.0, 2.1, 2.2, 2.3
- **SPDX 3.x**: 3.0, 3.0.0, 3.0.1

The script will warn you if it encounters an unsupported version but will attempt to sort anyway.

## Usage

### Basic usage

```bash
# Sort in-place
python3 sort_spdx.py input.spdx.json

# Sort to a different file
python3 sort_spdx.py input.spdx.json output.spdx.json

# Use with pipes
cat input.spdx.json | python3 sort_spdx.py > output.spdx.json
```

### Batch processing

Sort all SPDX files in a directory:

```bash
for file in *.spdx.json; do
    python3 sort_spdx.py "$file"
done
```

### Git integration

#### Option 1: Pre-commit hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.spdx\.json$'); do
    python3 sort_spdx.py "$file"
    git add "$file"
done
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

#### Option 2: Git filter (automatic normalization)

Add to `.gitattributes`:
```
*.spdx.json filter=spdx-sort
```

Configure in `.git/config` or `~/.gitconfig`:
```
[filter "spdx-sort"]
    clean = python3 /path/to/sort_spdx.py
    smudge = cat
```

This automatically sorts files on commit while keeping your working directory unchanged.

## Installation

1. Make the script executable:
```bash
chmod +x sort_spdx.py
```

2. Optionally, move to a directory in your PATH:
```bash
sudo cp sort_spdx.py /usr/local/bin/
```

## Examples

### Version checking

The script automatically detects and validates the SPDX version:

```bash
$ python3 sort_spdx.py my-sbom.spdx.json
Detected SPDX version: SPDX-2.3
Sorted SPDX file written to: my-sbom.spdx.json
```

If an unsupported version is detected:
```bash
$ python3 sort_spdx.py unknown-version.json
Warning: SPDX version 1.2 may not be fully supported.
Supported versions: 2.0, 2.1, 2.2, 2.3, 3.0, 3.0.0, 3.0.1
Attempting to sort anyway...
```

### Sorting example

Before sorting:
```json
{
  "packages": [
    {"spdxId": "SPDXRef-Package-Z", "name": "zzz"},
    {"spdxId": "SPDXRef-Package-A", "name": "aaa"}
  ],
  "version": "SPDX-2.3",
  "name": "My SBOM"
}
```

After sorting:
```json
{
  "name": "My SBOM",
  "packages": [
    {"name": "aaa", "spdxId": "SPDXRef-Package-A"},
    {"name": "zzz", "spdxId": "SPDXRef-Package-Z"}
  ],
  "version": "SPDX-2.3"
}
```

Now `git diff` will show meaningful changes!

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
