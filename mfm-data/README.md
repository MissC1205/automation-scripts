# MFM Football Data (experimental)
This isolated directory contains a free ESPN soccer scoreboard collector and GitHub Actions workflow.
The repository is PUBLIC: never commit API keys, credentials, private betting records, or identifiable user information.
Run: `python mfm-data/mfm_espn.py --date 2026-10-12 --out mfm_data`.
The scheduled workflow stores 45-day artifacts, not permanent raw-data history. GitHub Actions runs on schedule or Python/workflow code changes, not every odds snapshot commit.
ESPN is an unofficial, potentially rate-limited source. It does not provide Chinese lottery JC numbers, official SP, official integer handicaps, calibrated probabilities, or guaranteed xG.
Workflow success must be verified in GitHub Actions before claiming a working connection. An automated `YYYY-MM-DD_data_quality_gate.json` audit states counts, scope, youth-fixture contamination, form coverage, and **betting_eligibility=BLOCKED** until official JC identity/SP, team crosswalk, and calibrated EV gates are truly implemented. This status is a data-quality gate, not a prediction. MFM betting recommendations remain PASS until independent data and EV gates are satisfied.


## Operational Caidao collector (added 2026-10-14)

The repository now includes a scheduled, on-demand operational Caidao collector in `mfm_caidao_service.py`; its workflow is `.github/workflows/mfm-caidao-service.yml`. It runs about 10:05/15:05/18:05/21:05/23:05 Beijing, supports GitHub workflow_dispatch and explicit chat-trigger file updates, and archives full date-stamped snapshots. Read `mfm-data/CAIDAO_RUNBOOK.md` for invocation, outputs and validation.

For quick analysis retrieve `mfm-data/caidao-live/latest-summary.json`, inspect its collected-at timestamp and quality gate, then use `latest-football-only.json` BEFORE `latest-market-only.json`. Provider probabilities and commentary are never independent model evidence. Verified code and field access **do not** establish official SP, positive EV, match outcome calibration, or completeness of the full MFM independent model.
