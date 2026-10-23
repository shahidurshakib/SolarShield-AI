# SolarShield-AI data-preparation report

Generated: 2026-10-22 20:41:57 | Python 3.12.3 | pandas 3.0.2 | numpy 2.4.4

Pipeline: `python scripts/prepare_data.py`. No model was trained; no forecasting was done.

## Result

Automated checks: **25 PASS, 4 INFO, 1 WARN, 0 FAIL**.

## Inputs (read only, SHA-256 verified before and after the run)

- `data/raw/NOAA_Observed_Solar_Cycle.json` sha256 `0bfebcb61d7a6a09...`
- `data/raw/NOAA_Predicted_Solar_Cycle.json` sha256 `a2bbb69d58e2b653...`
- `data/raw/NOAA_Solar_Cycle_25_Prediction.json` sha256 `aab719a82022c1dd...`
- `data/raw/SILSO_Monthly_Sunspot_Data.csv` sha256 `4749cc16c68e0673...`
- `data/metadata/SILSO_solar_cycle_min_max_native.csv` sha256 `7dfb1e9debb42719...`
- `data/metadata/solar_cycle_reference.csv` (standardized reference; derived from the native table, provenance in `solar_cycle_reference_provenance.json`)
- The two NOAA prediction JSON files above are used only for the separate predictions file; the NOAA observed JSON only for `noaa_f107`, `noaa_swpc_ssn` and cross-checks.

## Transformations, in order

1. Read SILSO monthly CSV (semicolon, no header) with the existing sentinel-aware loader; it is the only source of `ssn`.
2. Parsed year + month into `month_start` (first of month); kept `year`, `month`, `decimal_year`, `ssn`, `ssn_std`, `n_obs`.
3. Converted `-1` to missing, in memory only, in `ssn_std` and `n_obs` (ssn_std=828, n_obs=828 masked; `ssn` has no -1). The raw file still contains the -1 values.
4. Mapped SILSO's definitive flag to `is_provisional` (0 -> True). 3 provisional month(s) are kept and flagged, not dropped or treated as final.
5. Assigned `cycle_number` from published minimum months: cycle k covers [minimum_k, minimum_k+1); the minimum month starts the new cycle. 73 month(s) before 1755-02 stay unassigned. Cycle 25's end is undefined.
6. Added NOAA observed `f10.7` and `observed_swpc_ssn` as `noaa_f107` and `noaa_swpc_ssn` (-1 -> missing: observed_swpc_ssn=2976, f10.7=3069). Joined one-to-one on month; NOAA `ssn` is NOT added (identical to SILSO, same lineage).
7. NOAA smoothed columns are used only inside checks: they are centred 13-month means (use 6 future months) and are not written as features.
8. NOAA predicted and Cycle 25 prediction files were written to a separate file with `pred_`/`c25_` prefixes and an `is_prediction` flag; they are never joined to observations.
9. Built the per-cycle summary (published minima/maxima + computed counts and raw peaks).

## Outputs

| file | rows | sha256 (first 16) |
|---|---|---|
| `data/processed/sunspot_monthly_clean.csv` | 3333 | `8920e24e6d0ed0c4` |
| `data/processed/solar_cycle_summary.csv` | 25 | `3f2a85859dc1df2a` |
| `data/processed/noaa_predictions_separate.csv` | 248 | `685693870531b85c` |
| `data/processed/DATA_DICTIONARY.md` |  | `a3fb3682d5574a3d` |

Clean dataset: 3333 months, 1749-01 to 2026-09; 3260 assigned to a cycle, 73 unassigned.

## Solar-cycle summary

`raw_monthly_peak_*` is the highest single month in the SILSO monthly data (noisy). `official_smoothed_max_*` is the SILSO-published maximum of the 13-month smoothed series. They are different quantities and are not interchangeable.

| cycle_number | status | published_minimum_month | months_available | available_duration_years | coverage_complete | raw_monthly_peak_ssn | raw_monthly_peak_month | official_smoothed_max_sn | official_smoothed_max_month | raw_peak_minus_official_max_sn |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | completed | 1755-02 | 136 | 11.33 | True | 178.7 | 1761-05 | 144.1 | 1761-06 | 34.6 |
| 2 | completed | 1766-06 | 108 | 9.0 | True | 263.7 | 1769-10 | 193.0 | 1769-09 | 70.7 |
| 3 | completed | 1775-06 | 111 | 9.25 | True | 398.2 | 1778-05 | 264.2 | 1778-05 | 134.0 |
| 4 | completed | 1784-09 | 163 | 13.58 | True | 290.0 | 1787-12 | 235.3 | 1788-02 | 54.7 |
| 5 | completed | 1798-04 | 147 | 12.25 | True | 103.8 | 1804-10 | 82.0 | 1805-02 | 21.8 |
| 6 | completed | 1810-07 | 154 | 12.83 | True | 160.3 | 1817-03 | 81.2 | 1816-05 | 79.1 |
| 7 | completed | 1823-05 | 126 | 10.5 | True | 177.3 | 1830-04 | 119.2 | 1829-11 | 58.1 |
| 8 | completed | 1833-11 | 116 | 9.67 | True | 343.8 | 1836-12 | 244.9 | 1837-03 | 98.9 |
| 9 | completed | 1843-07 | 149 | 12.42 | True | 300.6 | 1847-10 | 219.9 | 1848-02 | 80.7 |
| 10 | completed | 1855-12 | 135 | 11.25 | True | 221.9 | 1860-07 | 186.2 | 1860-02 | 35.7 |
| 11 | completed | 1867-03 | 141 | 11.75 | True | 293.6 | 1870-05 | 234.0 | 1870-08 | 59.6 |
| 12 | completed | 1878-12 | 135 | 11.25 | True | 159.6 | 1882-04 | 124.4 | 1883-12 | 35.2 |
| 13 | completed | 1890-03 | 142 | 11.83 | True | 215.4 | 1893-08 | 146.5 | 1894-01 | 68.9 |
| 14 | completed | 1902-01 | 138 | 11.5 | True | 180.3 | 1907-02 | 107.1 | 1906-02 | 73.2 |
| 15 | completed | 1913-07 | 121 | 10.08 | True | 257.7 | 1917-08 | 175.7 | 1917-08 | 82.0 |
| 16 | completed | 1923-08 | 121 | 10.08 | True | 179.9 | 1929-12 | 130.2 | 1928-04 | 49.7 |
| 17 | completed | 1933-09 | 125 | 10.42 | True | 275.6 | 1938-07 | 198.6 | 1937-04 | 77.0 |
| 18 | completed | 1944-02 | 122 | 10.17 | True | 285.0 | 1947-05 | 218.7 | 1947-05 | 66.3 |
| 19 | completed | 1954-04 | 126 | 10.5 | True | 359.4 | 1957-10 | 285.0 | 1958-03 | 74.4 |
| 20 | completed | 1964-10 | 137 | 11.42 | True | 192.3 | 1969-03 | 156.6 | 1968-11 | 35.7 |
| 21 | completed | 1976-03 | 126 | 10.5 | True | 266.9 | 1979-09 | 232.9 | 1979-12 | 34.0 |
| 22 | completed | 1986-09 | 119 | 9.92 | True | 284.5 | 1989-06 | 212.5 | 1989-11 | 72.0 |
| 23 | completed | 1996-08 | 148 | 12.33 | True | 244.3 | 2000-07 | 180.3 | 2001-11 | 64.0 |
| 24 | completed | 2008-12 | 132 | 11.0 | True | 146.1 | 2014-02 | 116.4 | 2014-04 | 29.7 |
| 25 | ongoing | 2019-12 | 82 | 6.83 |  | 216.0 | 2024-08 |  |  |  |

Cycle 25: raw monthly peak to date is 216.0 (2024-08); no official smoothed maximum exists in the source file, so none is reported.

## Automated checks

| level | check | detail |
|---|---|---|
| PASS | Date continuity | every month from 1749-01 to 2026-09 is present exactly once in sequence (3333 months) |
| PASS | year/month vs month_start | year and month columns agree with month_start |
| PASS | decimal_year | max deviation from the simple mid-month fractional year = 0.0057 yr (SILSO uses day-based mid-month positions) |
| PASS | Duplicate months | no duplicated months; one row per month |
| PASS | Cycle assignment | cycle_number equals an independent half-open-interval recomputation from published minima |
| PASS | Missing cycle assignments | 0 month(s) on/after 1755-02 have no cycle |
| PASS | Months before Cycle 1 | 73 month(s) before 1755-02, all unassigned |
| PASS | Cycle-boundary consistency | each cycle starts at its published minimum, ends the month before the next minimum, no gaps/overlaps; Cycle 25 end undefined |
| PASS | Sentinel -> missing (ssn_std) | 828 raw -1 value(s) -> 828 missing in memory; counts agree |
| PASS | Sentinel -> missing (n_obs) | 828 raw -1 value(s) -> 828 missing in memory; counts agree |
| PASS | No -1 left in output | no -1 values remain in any numeric column |
| PASS | Raw file keeps its -1 values | the raw SILSO file still contains its -1 sentinels (not edited) |
| PASS | ssn values | ssn has no negative or missing values |
| PASS | Provisional flag | is_provisional matches SILSO's definitive marker for every month |
| INFO | Provisional months | 3 provisional month(s), all at the end of the series; kept and flagged |
| PASS | NOAA month coverage | NOAA observed covers exactly the same 3333 months as SILSO |
| WARN | NOAA ssn vs SILSO ssn | identical in all 3333 shared months: same lineage, so NOAA ssn is not an independent sample and was not added; agreement is not independent validation |
| PASS | No duplicated sunspot observations | clean dataset has a single ssn column (SILSO) |
| PASS | NOAA smoothed ssn = centred 13-month mean of SILSO ssn | max /difference/ 0.050 over 3321 months (rounding level): the smoothed series is derived from the same SILSO data |
| INFO | Smoothed series is non-causal | smoothed value ends 6 months before the last observation, so each smoothed value uses 6 future months; smoothed columns are excluded from the output to prevent leakage |
| INFO | SWPC ssn vs SILSO ssn | correlation 0.993 over 357 overlapping months; related products, not independent ground truth |
| PASS | No predictions or smoothed (non-causal) columns in clean data | clean dataset has no prediction or centred-smoothing columns |
| PASS | No future months | clean dataset ends at the last SILSO month 2026-09 |
| PASS | Predictions kept separate | prediction file has only prefixed prediction columns and is_prediction=True |
| INFO | Prediction overlap | 77 prediction month(s) overlap observed months and 171 are future; no issue dates in the source, so vintage is unknown |
| PASS | Summary row counts | months in summary (3260) = assigned months in clean data (3260) |
| PASS | Completed cycles fully covered | all 24 completed cycles have every month with an ssn value |
| PASS | Ongoing cycle | exactly one ongoing cycle (the last); no official maximum or end invented |
| PASS | Raw monthly peaks | raw_monthly_peak_ssn equals the maximum monthly ssn in each cycle |
| PASS | Source files preserved | all 5 source files match the SHA-256 manifest before and after the run |

## Unresolved issues and limitations

1. SILSO and NOAA observed `ssn` are identical in every shared month (same lineage). NOAA is used only for extra variables and cross-checks; agreement between them is **not** independent validation.
2. 3 provisional month(s) (2026-07 to 2026-09) may be revised by SILSO. Anything that uses them as labels should decide explicitly how to treat them.
3. `ssn_std` and `n_obs` do not exist for 1749-01 to 1817-12 in the source; they are missing, not zero.
4. `noaa_f107` starts 2004-10 and `noaa_swpc_ssn` starts 1997-01; earlier months are missing.
5. The cycle-boundary convention (minimum month starts the new cycle) is this project's convention. SILSO publishes minimum months and durations, not a month-assignment rule; counts can differ by one month at boundaries under another rule.
6. NOAA prediction files have no issue date, so their vintage is unknown. Rows overlapping observed months must not be used as leak-free hindcasts.
7. Official smoothed maxima exist only for Cycles 1-24 in the source file. A different SILSO page lists a Cycle 25 maximum of 2024-10; it was not added (see provenance open items).
8. Provenance open item [cycle25_maximum]: Cycle 25 maximum_date is blank because the native source file has none. A different SILSO page (https://www.sidc.be/SILSO/cyclesminmax), as returned by a web search on 2026-10-23, lists a Cycle 25 maximum of 2024-10 (SN 160.9), while the cyclesmm page snapshot lists none. The two could not be reconciled here; the value was NOT added. Re-download the native table from SILSO and re-run scripts/build_solar_cycle_reference.py if you want it. Consistent with that page, the local NOAA 13-month smoothed series (through 2026-03) has its Cycle 25 high at 2024-10 (160.9); this is an observation from same-lineage data, not a declared SILSO maximum.
9. Provenance open item [retrieval_date]: Retrieval date of the native source file is unrecorded.
10. Provenance open item [download_url]: Exact download URL/export of the native source file is unrecorded.

The data dictionary is in `data/processed/DATA_DICTIONARY.md`.