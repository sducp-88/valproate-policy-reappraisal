# Valproate dispensing measurement and policy reappraisal

Reproducible code and public national aggregates for the England study covering January 2022 to April 2025.

## What the study measures

Prescription items, strength-standardised medicine supply and a separate female-recipient indicator are distinct measures. This aggregate study does not identify a causal effect of an individual policy or establish reproductive benefit. Female counts are practice-aggregated, not guaranteed nationally unique people, and have a broader formulation scope than the oral supply series.

## Repository contents

- `primary/`: five public aggregate/provenance CSVs, primary R models, independent Python checks, reconstruction and figure scripts. The original numbered filenames are retained so the verified scripts run without changing their calculations.
- `extensions/`: the previously validated, self-contained reproduction bridge, presentation decomposition, paired ratios, descriptive cost analysis and female-indicator context. This supersedes the separate strengthening package; there is no need to download that earlier package as well.
- `MANIFEST_SHA256.csv`: initial file checksums.

The repository contains no manuscript drafts, author declarations, private correspondence, account credentials, individual patient records or original investigators' proprietary code. Historical execution reports inside `extensions/` describe the validated earlier package, not a new execution of this repository.

## Run

Install Python dependencies listed in `requirements.txt`; R additionally requires `nlme` and `jsonlite`. See `primary/15_Supplementary_Code_README.txt` for tested versions and full methods. From the repository root run:

```text
python verify_manifest.py
python run_reproduction.py --rscript /path/to/Rscript
```

If Rscript is on PATH, omit `--rscript`. Scripts use local public aggregates and do not download data. Generated output and timestamp-bearing reports can change after execution; compare scientific values and immutable-input hashes rather than regenerated PDF bytes. `extensions/verify_inputs.py` separately verifies its frozen scientific inputs. Figure appearance can vary with fonts and library versions.

## Data provenance and reuse

Source: NHS Business Services Authority English Prescribing Data and parallel SNOMED release, and the public national Valproate Safety Dashboard. EPD aggregates were acquired on 2 November 2026; the female dashboard table was acquired on 5 November 2026. The latter is a preserved visible-table text extraction of historical values, not an original provider CSV export. Query/resource manifests, dates and source hashes are retained in the relevant folders.

NHSBSA public data attribution and Open Government Licence v3.0 details are retained in the component documentation: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ . This independent reanalysis is not endorsed by NHSBSA. No licence to third-party papers or original investigators' code is implied. This repository does not add a blanket software licence; reuse beyond applicable legal permissions requires the relevant rights holder's permission.

## Review and versions

The journal receives an anonymised, equivalent snapshot without the account URL or Git history. The repository URL is provided separately to the editor to support anonymised review. A version tag and full commit identify the exact code cited; no DOI or journal acceptance is claimed.
