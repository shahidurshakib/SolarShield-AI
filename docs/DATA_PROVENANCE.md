# Data Provenance Record

## Scope

This record documents the known source and processing context for
SolarShield-AI. It does not claim that missing source metadata has
been recovered.

## Source data

- Raw SILSO monthly sunspot data are retained under `data/raw/`.
- NOAA source JSON files are retained under `data/raw/`.
- The raw SILSO monthly series was audited as spanning January 1749
  through September 2026 (3333 rows).
- The processed monthly data and cycle summaries are retained under
  `data/processed/`.
- The processed cycle identifiers cover cycles 1 through 25.
  Cycles 1–24 were treated as complete and Cycle 25 as ongoing in
  the recorded audit.

## Known provenance limitations

The exact SILSO download URL and retrieval date were not recorded
in the existing provenance metadata. They are therefore unresolved
and must not be invented.

An unresolved discrepancy about the Cycle 25 maximum between SILSO
pages was also identified. Do not silently choose one value without
recording the source, access date, and rationale.

The existing provenance files and raw source files have been
preserved. No data were regenerated for this record.

## Integrity and version control

The repository-level SHA-256 manifest is
`data/metadata/workspace_sha256_manifest.csv`.

The recorded manifest recheck reported that all 92 listed file hashes
matched at the time of verification. The frozen selection snapshot
contained 12 files, all matching their same-name workspace copies
at that verification.

The Git revision before this documentation update was
`7532b6b30934b62739da1bfcf76a88bc5e085f04`
(`Add reproducibility documentation and integrity manifest`).

## Selection reproducibility boundary

The frozen statistical selection result remains
`selected_candidate: null` and `selection_passed: false`.

Its saved predictions, metrics, manifest, and report must remain
unchanged. Any future model-selection experiment must use a separate
output location and preserve the original snapshot.
