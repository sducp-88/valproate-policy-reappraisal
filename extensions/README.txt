Supplementary reproducibility package 17: patient-indicator context and all prior strengthening modules
Anonymous offline package, acquired/assembled 5 November 2026.

Run from the extracted directory:
  python verify_inputs.py
  python run_all.py
  python verify_inputs.py

Python dependencies: numpy, pandas, scipy, statsmodels, matplotlib, Pillow. Install these before offline replay. Package execution does not contact websites, require credentials or download data. Tested versions are written to REPLAY_EXECUTION_17.json and the separate package acceptance report. Font/raster differences can occur across operating systems; scientific tables must reproduce within stated tolerances.

The scientific modules from supplementary ZIP16 are retained. run_strengthening.py runs its numerical modules; Figure S2 is also regenerated. Frozen primary GLS results are supplied for comparison, not refitted here; primary-analysis R code/data remain separately supplied with the manuscript. README_V5.txt describes inherited modules and costs. Bundled legacy replay records describe ZIP16; the new run_all.py writes patient-inclusive records to RUN_LOGS_17 and REPLAY_EXECUTION_17.json.

NEW PATIENT MODULE
Source: official public NHSBSA national VPA1 dashboard, females aged 13–54. The 94 raw visible UI text rows were acquired on 5 November 2026, preserved as acquisition/vpa1_raw_ui_rows.json and converted locally to CSV. This is UI_TEXT_EXTRACTION, NOT an original provider CSV export. It is a current historical snapshot, not a contemporaneously downloaded 2022–2025 release. Source URLs and boundaries appear in PATIENT_SOURCE_AND_SCOPE.json. No private account information, usernames, passwords or individual records are included.

Only 38 three-month rolling windows entirely within January 2022–April 2025 are analysed. The 13 complete calendar quarters span Q1 2022–Q1 2025. February–April 2025 is separately labelled as the last eligible rolling window: it overlaps Q1 2025 and is not a 14th independent quarter. The acquisition-only 40-endmonth file includes two early windows extending into 2021 and must not replace the analytic 38-window file. Repeated people may occur in different quarters even when reference periods do not overlap.

VPA1 counts are deduplicated within practices and aggregated nationally, not guaranteed nationally unique people. The rate uses the published GP-registered female denominator. These indicators differ in age/sex and potential formulation scope from all-age/all-sex oral EPD supply. No DDD-per-person ratio, patient dose, treatment duration or causal policy effect is estimated. VPA4/VPA5 data and effects are excluded because live tooltip definitions conflict with the linked specification; a brief exclusion reason is retained without those numerical series.

The dated amendment is exploratory, not preregistered. Original and V5 findings plus four patient example rows were known before the extension. The full sequence and new calculations were not analysed at that point. Direction and significance were not inclusion gates.

REPLAY AND VALIDATION
1. Validate unchanged scientific inputs.
2. Replay all prior paired-ratio, decomposition, reproduction-bridge and descriptive-cost modules, then Figure S2.
3. Parse preserved VPA1 raw UI rows; rebuild the 94-row history and acquisition 40-endmonth CSV.
4. Recreate 38 aligned windows, 13 quarters, rates and predeclared Q1 2022 to Q1 2025 descriptive changes from frozen month data.
5. Independently check all 94 raw rows/rates, all 38/13 output rows and endpoint changes using Decimal and actual calendar days, including February 2024 = 29 days and Q1 2024 = 91 days.
6. Regenerate Figure S3 and Table S9, retaining separate units and differing population labels.
7. Revalidate immutable inputs. Reruns update timestamps/logs; compare numerical values and immutable hashes, not timestamp-sensitive output JSON bytes.

INPUT_MANIFEST_SHA256.csv identifies immutable inputs/scripts. PACKAGE_MANIFEST_SHA256.csv identifies initially delivered files. V5_PACKAGE_MANIFEST_SHA256.csv preserves the previous manifest. The exact delivered ZIP17 is separately extracted to an empty directory and executed with Python networking disabled; its external acceptance report records SHA256 and numerical comparisons. ZIP16 remains unchanged.
