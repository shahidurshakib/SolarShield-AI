# SolarShield-AI — Data Sources and Data Governance

This document records the principal datasets, their intended roles, known processing activities, and integration status within SolarShield-AI.

To preserve research integrity, every source is classified as one of the following:

- **Primary / Used:** Recorded as an input to completed research.
- **Exploratory:** Inspected or downloaded for research, but not established as an integrated model input.
- **Candidate:** Identified for future development.
- **Unverified:** Requires additional provenance or integration evidence.

---

## 1. Primary Dataset: WDC-SILSO International Sunspot Number

**Provider:** World Data Center SILSO, Royal Observatory of Belgium  
**Dataset:** International Sunspot Number — Monthly Total  
**Official download:** https://www.sidc.be/SILSO/datafiles  
**Dataset information:** https://www.sidc.be/SILSO/infosnmtot

### Research Role

The SILSO monthly sunspot-number series is the primary historical dataset used for SolarShield-AI's solar-cycle characterization and forecasting research.

### Recorded Dataset Coverage

| Property | Recorded Value |
|---|---|
| Start | January 1749 |
| End | September 2026 |
| Total records | 3,333 |
| Frequency | Monthly |
| Solar cycles | Completed cycles 1–24; ongoing cycle 25 |
| Dataset version | Version 2.0 |
| Recent observations | July–September 2026 provisional |

### Relevant Variables

The monthly data product includes:

- Year
- Month
- Decimal date
- Monthly mean total sunspot number
- Standard deviation
- Number of observations
- Provisional-observation indicator

### Processing and Quality Controls

Recorded processing included:

1. Date parsing and chronological validation.
2. Monthly record-count verification.
3. Historical solar-cycle boundary handling.
4. Completed-cycle segmentation.
5. Cycle phase normalization.
6. Provisional suffix identification.
7. Source-integrity and hash verification.

Completed cycles 1–24 were processed into normalized cycle curves containing 121 phase points each.

The cycle-boundary convention used the published minimum as inclusive and the next minimum as exclusive.

Cycle 25 was treated separately because it remains ongoing.

### Provenance and Integrity

The latest recorded source hashes are represented in the project notes as:

- Monthly SILSO source: `8920e24…d194`
- Native cycle summary: `3f2a85…33ac`

These are abbreviated identifiers, not complete SHA-256 values. The full values must be retrieved from the frozen project manifests before being used for independent verification.

### Important Data Considerations

- Provisional observations must not be treated as final definitive values.
- Published cycle boundaries must not be replaced by arbitrary model-derived boundaries without documentation.
- Revised source releases should be versioned and revalidated.
- Historical model comparisons must use consistent source snapshots.

**Classification:** Primary / Used.

---

## 2. Solar Dynamics Observatory — HMI

**Mission:** NASA Solar Dynamics Observatory (SDO)  
**Instrument:** Helioseismic and Magnetic Imager (HMI)  
**JSOC:** https://jsoc.stanford.edu/  
**HMI SHARP guide:** http://jsoc.stanford.edu/doc/data/hmi/sharp/sharp.htm

### Candidate Data Products

#### A. `hmi.M_720s`

A line-of-sight magnetogram data product with a native 720-second cadence.

Potential research use:

- Solar magnetic-field characterization.
- Magnetic-field evolution.
- Magnetic activity indicators.
- Future feature extraction.

#### B. `hmi.sharp_cea_720s`

An active-region data product containing Space-weather HMI Active Region Patch (SHARP) measurements in cylindrical equal-area coordinates.

Potential research use:

- Active-region magnetic properties.
- Magnetic-field complexity.
- Active-region evolution.
- Candidate flare-related predictors.

### Recorded Exploration

The project recorded:

- 9 FITS files in an export test.
- 219,686 rows in a HARP CSV dataset.

The proposed daily sampling strategy is a project-side sampling decision. The original data products have a 720-second cadence; they should not be described as native daily products.

### Integration Status

These files are exploratory artifacts. Their use as inputs to the main forecasting pipeline has not been established.

Before integration, the project must document:

- Exact JSOC series and query parameters.
- Observation timestamps.
- Active-region identifiers.
- Missing-data handling.
- FITS metadata and quality flags.
- Sampling and aggregation rules.
- Feature definitions.
- Train/test temporal separation.
- Reproducible source manifests.

**Classification:** Exploratory.

---

## 3. NASA OMNI Solar-Wind and Geomagnetic Data

**Provider:** NASA Space Physics Data Facility  
**OMNIWeb:** https://omniweb.gsfc.nasa.gov/ow.html  
**Data coverage and metadata:** https://omniweb.gsfc.nasa.gov/html/ow_data.html  
**NASA Open Data:** https://data.nasa.gov/dataset/omni-hourly-data-set

### Potential Research Role

OMNI data may support the future connection between solar activity and near-Earth space-weather conditions.

Candidate variables include:

- Solar-wind speed.
- Solar-wind density.
- Interplanetary magnetic field.
- IMF Bz.
- Plasma parameters.
- Geomagnetic indices.
- Kp and ap.
- Dst.
- AE, AU and AL.
- F10.7 and other solar activity indicators, where available in the relevant product.

### Proposed Use

These observations may help investigate:

1. Solar activity and solar-wind conditions.
2. Solar-wind conditions and geomagnetic response.
3. Geomagnetic conditions and possible infrastructure impacts.
4. Time-lagged relationships between solar events and Earth response.

### Integration Status

The project has identified OMNI as a candidate data source. The current documentation does not establish that OMNI variables have been integrated into the completed V2/V3 model experiments.

**Classification:** Candidate.

---

## 4. Historical Sunspot-Group Records

### Research Purpose

Historical sunspot-group observations may provide additional information about solar-cycle structure and active-region behavior.

### Recorded Audit

| Property | Recorded Value |
|---|---:|
| Coverage | 1874–2025 |
| Files | 152 |
| Records | 257,852 |
| Record length | 74 characters |
| Identified schema-change years | 1977 and 1982 |
| Forensic-filtered targets | 57 |

### Data Challenges

- Historical record formats changed over time.
- Schema changes require version-aware parsing.
- Missing-day information needs separate provenance.
- An official MissingDays download attempt encountered an anti-bot page.

### Integration Status

The archive was audited and investigated, but it is not established as an integrated model input.

The exact source endpoint and complete download provenance must be recovered before this dataset can be treated as a reproducible project dependency.

**Classification:** Exploratory / Provenance completion required.

---

## 5. Candidate Solar and Space-Weather Event Data

The following data categories are relevant to the long-term SolarShield-AI architecture.

| Data Category | Potential Variables | Intended Research Role | Status |
|---|---|---|---|
| Solar flares | Flare class, peak time, duration | Solar eruption characterization | Candidate |
| Coronal Mass Ejections | Speed, direction, angular width | Eruption and propagation analysis | Candidate |
| Solar Energetic Particles | Particle flux and energy channels | Radiation-environment assessment | Candidate |
| Solar wind | Speed, density, temperature | Near-Earth solar-wind conditions | Candidate |
| Interplanetary magnetic field | Bz and total field | Geoeffectiveness investigation | Candidate |
| Geomagnetic indices | Kp, Dst, AE | Geomagnetic response | Candidate |
| Radio flux | F10.7 | Solar activity context | Candidate |

These categories describe the proposed data architecture. They should not be interpreted as evidence that every data stream has already been acquired, processed, or integrated.

---

## 6. Data Governance Principles

### 6.1 Source Traceability

Every dataset used in a reported experiment should have:

- Provider name.
- Official source URL.
- Dataset or product identifier.
- Retrieval timestamp.
- Coverage period.
- Version or release information.
- File-level integrity hashes.
- Processing and transformation records.

### 6.2 Temporal Integrity

For forecasting research:

- Training data must precede evaluation observations.
- Future observations must not leak into historical features.
- Temporal alignment must be explicit.
- Resampling and aggregation must be documented.
- Forecast origins and target horizons must be preserved.

### 6.3 Quality Control

The pipeline should explicitly handle:

- Missing observations.
- Provisional values.
- Duplicate timestamps.
- Invalid records.
- Instrument quality flags.
- Changes in source schema.
- Revised historical data.

### 6.4 Data Versioning

Source updates must not silently replace frozen experiment inputs.

Every new source snapshot should be recorded separately, with its own manifest and integrity checks.

---

## 7. Current Data Integration Summary

| Source | Status | Main Role |
|---|---|---|
| WDC-SILSO monthly sunspot number | Primary / Used | Historical solar-cycle modeling |
| SILSO native cycle metadata | Used | Cycle boundaries and preprocessing |
| SDO/HMI magnetograms | Exploratory | Solar magnetic-field research |
| SDO/HMI SHARP | Exploratory | Active-region feature research |
| NASA OMNI | Candidate | Solar-wind and geomagnetic analysis |
| Historical sunspot-group archive | Exploratory | Historical solar observations |
| Flare/CME/SEP event streams | Candidate | Future space-weather modeling |

---

## 8. Scientific Limitations

A solar-activity forecast is not automatically an Earth-impact forecast.

A scientifically defensible SolarShield-AI system must separately validate:

1. Solar activity forecasting.
2. Space-weather condition estimation.
3. Near-Earth response modeling.
4. Sector-specific risk estimation.
5. Alert thresholds and uncertainty.
6. Operational warning performance.

Until these components are integrated and independently validated, SolarShield-AI should be described as a developing research prototype rather than a validated operational warning service.

---

**Documentation principle:** Every data source must be traceable, every transformation reproducible, and every integration claim supported by evidence.