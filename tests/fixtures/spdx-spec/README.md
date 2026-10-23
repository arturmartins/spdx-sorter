# SPDX specification corpus

This directory contains a small offline conformance corpus built from pinned
official SPDX organization sources. Runtime package code does not read these
files; they are test fixtures only.

`schemas/` contains official JSON Schemas from `spdx/spdx-spec`. `valid/`
contains representative upstream SPDX JSON documents. `invalid/` contains
project-local negative mutations of the upstream valid documents because no
official invalid JSON examples were found in the pinned upstream sources.

Producer compatibility fixtures live in `../producers/` and are deliberately
non-normative.

## Vendored files

| Local path | Source URL | Tag | Commit | Upstream path | License | SHA-256 | Expected outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `schemas/2.2/spdx-schema.json` | <https://github.com/spdx/spdx-spec/blob/v2.2.2/schemas/spdx-schema.json> | `v2.2.2` | `a05c12a2dd4652b1396fd2659f2cd3ea1f37faba` | `schemas/spdx-schema.json` | CC-BY-3.0 | `c8328d14c33621a6be917569ad4c323d370220412edbaddc37ccf1e93e3ca88a` | Official schema for SPDX-2.2 validation |
| `schemas/2.3/spdx-schema.json` | <https://github.com/spdx/spdx-spec/blob/v2.3/schemas/spdx-schema.json> | `v2.3` | `aadf3b0b8dbbabdb4d880b0fc714255fea436ff7` | `schemas/spdx-schema.json` | CC-BY-3.0 | `239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b` | Official schema for SPDX-2.3 validation |
| `valid/2.2-spdx-spec-SPDXJSONExample-v2.2.spdx.json` | <https://github.com/spdx/spdx-spec/blob/v2.2.2/examples/SPDXJSONExample-v2.2.spdx.json> | `v2.2.2` | `a05c12a2dd4652b1396fd2659f2cd3ea1f37faba` | `examples/SPDXJSONExample-v2.2.spdx.json` | CC-BY-3.0 source repository; document `dataLicense` is CC0-1.0 | `e05bacc90d72d9f530bbe68b76ca68afd76ea0b073b945c7bc975f522051acec` | Valid SPDX-2.2 upstream fixture |
| `valid/2.3-spdx-examples-example11-sbom.spdx.json` | <https://github.com/spdx/spdx-examples/blob/2181917ef6ff74de89252ee785583c27a38d6199/software/example11/spdx2.3/sbom.spdx.json> | none | `2181917ef6ff74de89252ee785583c27a38d6199` | `software/example11/spdx2.3/sbom.spdx.json` | CC0-1.0 for SPDX documents per `spdx/spdx-examples` README | `e38ee905f9c006755e4facc4691af57d4e637a7ef97c3468887c94e0c0f46060` | Valid SPDX-2.3 upstream fixture |
| `invalid/local-2.2-spdx-spec-SPDXJSONExample-v2.2-missing-creation-info.json` | Derived locally from <https://github.com/spdx/spdx-spec/blob/v2.2.2/examples/SPDXJSONExample-v2.2.spdx.json> | `v2.2.2` | `a05c12a2dd4652b1396fd2659f2cd3ea1f37faba` | `examples/SPDXJSONExample-v2.2.spdx.json` with top-level `creationInfo` removed | Local negative mutation of CC-BY-3.0 source repository fixture; document `dataLicense` is CC0-1.0 | `6edf57f113bf91714a8fd31dc4e769bbeaa5528a113deb8c6dc9356b40a47180` | Invalid SPDX-2.2 schema fixture |
| `invalid/local-2.3-spdx-examples-example11-sbom-missing-creation-info.json` | Derived locally from <https://github.com/spdx/spdx-examples/blob/2181917ef6ff74de89252ee785583c27a38d6199/software/example11/spdx2.3/sbom.spdx.json> | none | `2181917ef6ff74de89252ee785583c27a38d6199` | `software/example11/spdx2.3/sbom.spdx.json` with top-level `creationInfo` removed | Local negative mutation of CC0-1.0 SPDX document | `630a3fd025cfbdc09a2b691ae91397cb06320141b10533d7528aec9784821924` | Invalid SPDX-2.3 schema fixture |

## Source notes

The official `spdx/spdx-spec` `v2.3` release tree contains the SPDX-2.3 JSON
Schema but not a same-version SPDX-2.3 JSON example. The SPDX-2.3 fixture
therefore comes from the official `spdx/spdx-examples` repository at the
commit above. That repository has no tags in `git ls-remote --tags` as of this
corpus update, so the commit SHA is the pin.
