# MFM Football Data (experimental)
This isolated directory contains a free ESPN soccer scoreboard collector and GitHub Actions workflow.
The repository is PUBLIC: never commit API keys, credentials, private betting records, or identifiable user information.
Run: `python mfm-data/mfm_espn.py --date 2026-10-12 --out mfm_data`.
The scheduled workflow stores 14-day artifacts, not permanent raw-data history.
ESPN is an unofficial, potentially rate-limited source. It does not provide Chinese lottery JC numbers, official SP, official integer handicaps, calibrated probabilities, or guaranteed xG.
Workflow success must be verified in GitHub Actions before claiming a working connection. MFM betting recommendations remain PASS until independent data and EV gates are satisfied.
