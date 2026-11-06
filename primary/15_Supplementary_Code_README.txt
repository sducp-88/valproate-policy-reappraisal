Reproducibility instructions

Study: A national reproducibility study of valproate dispensing measures and safety policy interpretation in England
Design: National aggregate reproducibility study, January 2022-April 2025.
Data retrieved: 2 November 2026. No patient-level or practice-level records are supplied.

Data files
1 Monthly: 40 monthly analysis rows, including every derived outcome and calendar-day divisor.
2 Mapping: 64 presentations; 58 oral included, six non-oral excluded. g_per_unit is grams per solid unit or per mL of liquid. Missing strength for an excluded product is not zero.
3 Aggregates: 2,393 national valproate presentation-month cells. n_rows counts underlying administrative records; items counts prescription items; total_quantity is the additive supplied quantity. quantity_unweighted is a diagnostic non-additive quantity sum. No column is a count of distinct patients.
4 Release comparison: 4,044 paired national cells for two valproate descriptors, lamotrigine and levetiracetam. The valproate-only subset has 2,393 cells. These releases share the underlying NHSBSA source.
5 Source manifest: 80 resource identifiers, actual SQL queries, retrieval date, response hashes and URLs. It records the frozen responses; a later response can change and need not have the same hash. Terms: Open Government Licence v3.0; https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/

Software used
R 4.5.2, nlme 3.1-168, jsonlite 2.0.0; Python 3 with numpy 2.3.5, pandas 3.0.1, scipy 1.18.0 and matplotlib 3.11.2. Plotting also uses Pillow. No original investigators' Stata code is included or implied to have been reproduced exactly.

Run in a clean local directory containing these five CSVs and four code files
python 11_Supplementary_Code_Reconstruct.py
Rscript 12_Supplementary_Code_Models.R .
python 13_Supplementary_Code_Verify.py
python 14_Supplementary_Code_Figures.py

R requires nlme and jsonlite in its normal library paths. VALPROATE_R_LIB may optionally point to a separately installed R package library. Python requires the packages listed above. Install packages separately if needed; none of the supplied analysis scripts downloads data or modifies system configuration.

Outputs are written under ANALYSIS/data, ANALYSIS/results and FIGURES relative to the code files. These are generated outputs, not extra inputs. Model coefficients, covariance matrices, contrasts, residuals and all sensitivity estimates are retained. Vector PDF/SVG figures, preview PNGs and figure source CSVs are regenerated. Exact plot-file bytes may depend on font availability, package versions and PDF timestamps; numerical outputs are the reproducibility target.

Checks and interpretation
Reconstruction checks all 40 months, the 2,200 oral cells, the quantity-times-items identity, the complete strength map, ADQ conversion and both coding releases. Direct matrix GLS independently verifies the R coefficient solution; finite differences check the ratio gradient. Prais-Winsten and HAC are separate sensitivity estimators. Model intervals are conditional on the fitted covariance structure; they do not resolve concurrent policies or absent patient variables. All 31 specified primary and sensitivity results are retained. The near-zero November terminal volume contrast coexists with a declining post-break slope and a more negative February contrast.

Planning chronology
The local plan preceded aggregate extraction but followed knowledge of the published results. Source-format checks and independent computations were added after initial results; calendar-day count checks, formulation restrictions, the December date and simpler seasonal models were documented at manuscript stage. AR(2) was added after inspecting residual correlation. This is exploratory, not prospectively registered research.

Data provenance
NHS Business Services Authority English Prescribing Data and its parallel SNOMED release, from the NHSBSA Open Data Portal. Data are reproduced/adapted under the Open Government Licence. This is an independent reanalysis; NHSBSA does not endorse the findings.
