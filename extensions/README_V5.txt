Supplementary Code and Data 6: exploratory strengthening analyses
Anonymous offline reproduction package, 5 November 2026.

This package contains public national presentation-month aggregates, the 40-month analytical inputs, numerical scripts, anonymous scientific configuration, verified published-value transcription/citation and generated output. It contains no patient or practice records, author identity files, publisher article PDF/full text, portal credentials or original investigators' code.

Run from the extracted package directory:
  python verify_inputs.py
  python run_all.py
  python verify_inputs.py

Required Python packages: numpy, pandas, scipy, statsmodels. Exact tested versions are recorded in REPLAY_EXECUTION.json. No Word, R, matplotlib, network access or credentials are needed for the numerical modules. The frozen primary GLS model results are supplied for bridge comparison; they are not refitted by this package. The primary-analysis code/data are provided separately with the manuscript.

Modules: paired log-ratio interrupted time-series contrasts; exact symmetric within-presentation/item-share decomposition; four source-aligned Prais-Winsten comparisons; descriptive NIC/Actual Cost accounting with fixed 2022-price decomposition; independent numerical checks. All additions are exploratory, following the already-known original and frozen primary findings. See the anonymous amendment and cost analysis definition under WORKING/strengthening_20261105/.

Original article citation: Galloway J et al. Mandatory specialist approval requirements reduce valproate prescribing: population-based evaluation of a National Patient Safety Alert. BMJ Quality & Safety. doi:10.1136/bmjqs-2025-019415. Verified numerical transcription is supplied in WORKING/strengthening_20261105/reproduction_bridge/published_values_verified.json. Original source article files and original code are absent; these are transparent reconstructions, not exact original-code replication. Optional full-text/PDF path references in the bridge are provenance placeholders only.

Raw cost responses are public NHSBSA national aggregates. WORKING/strengthening_20261105/cost/full_source_manifest.json preserves source SQL/URLs, dates and response hashes. Offline preparation validates all 40 raw hashes and matching quantities/items before cost calculation. The three pilot evidence files in the same directory preserve acquisition-stage matching validation for five months. Their raw responses are already included within the 40-month set. The pilot is not a separate outcome analysis; offline cost analyses use the full 40-month inputs. PILOT_EVIDENCE_CHECK.json confirms the pilot table matches the corresponding full-data subset.

No cost sums are multiplied again by item counts. Actual Cost reporting changed in April 2024; NIC is a basic drug-price measure, not total health-service expenditure. No policy savings, cost effectiveness or QALYs are estimated.

Read PORTABLE_ADAPTATIONS.json for explicit changes from research-workspace scripts. All numerical calculations are retained; author/manuscript hash dependencies and optional plotting were removed. Filesystem paths and runtime timestamps may differ on rerun. Numerical outputs should be compared with stated tolerances, not timestamp-sensitive JSON bytes.

The executed replay is recorded in RUN_LOGS and REPLAY_EXECUTION.json. ORIGINAL_OUTPUT_COMPARISON.json records comparison of 13 output tables with the reviewed working results. INPUT_MANIFEST_SHA256.csv lists immutable analytical/provenance inputs; verify_inputs.py checks them. PACKAGE_MANIFEST_SHA256.csv records the initial package files. Rerunning may update generated logs/output timestamps without changing inputs. The post-replay addition of pilot evidence and this README did not alter or rerun the numerical analyses.

Optional Figure S2 regeneration:
  python WORKING/strengthening_20261105/make_supplement_figure.py
This optional step additionally requires matplotlib and Pillow. It creates FIGURES automatically and reads only the reproduced measurement tables. The tested library versions, CSV comparisons and image hash are in OPTIONAL_FIGURE_REPLAY.json. Figure binaries are supplied separately with the manuscript and omitted from this ZIP; the two figure-source CSVs are included. Exact fonts/rasterization can vary across environments.
