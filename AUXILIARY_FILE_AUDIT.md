# Auxiliary file audit

This note records auxiliary files that were preserved during Git
initialization and finalization.

## Preserved backup files

- `tests/test_statistical_backtesting.py.bak`
- `reports/statistical_backtesting/selection/STAGE_REPORT.md.bak`
- `data/metadata/solar_cycle_reference_provenance.backup.json`

These files were retained because they contain historical or backup
material. Their existence alone does not establish that they should
replace the active files. Do not restore or overwrite active files
without a separate content comparison and explicit decision.

## Unusual root file

`tstest_statistical_backtesting.py'` has an unusual filename and was
observed to contain command-help text rather than a normal test module.
It remains on disk but is not tracked in the initial Git commit.
It was intentionally excluded from staging and was not deleted.

## Safety rule

No auxiliary file was deleted as part of this audit. Any future cleanup
should first record the file hash, compare contents with related files,
and confirm whether the file is needed for recovery or provenance.
