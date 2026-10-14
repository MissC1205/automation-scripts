# MFM Mandatory Prediction Output Contract

Effective: 2026-10-12

For every verified requested match, give a single concrete provisional 90-minute 1X2 direction and analyze other applicable markets independently, labeling uncalibrated exact-goals, half/full-time or score hypotheses as research only. Include evidence, counterevidence, missing fields, confidence and prediction timestamp/version. A low-confidence research forecast must not be mistaken for a qualifying bet; unsupported bet markets may be PASS.

For official Chinese JC handicap 1X2, give a concrete handicap outcome only after confirming the actual official integer handicap. If unavailable, provide a clearly labeled hypothetical outcome at an explicitly assumed line (e.g. home -1), NEVER misrepresent it as the official JC result. The assumed line may differ from the actual offered line.

Keep prediction distinct from betting recommendation: a low-confidence match can have a prediction and still be NO BET. Do not fabricate prices, probabilities, xG, injuries or official lines. Track revisions with timestamp and reasons; do not overwrite historical predictions. If a match identity itself cannot be verified, explicitly flag unverified identity and refrain from presenting it as an official JC fixture.

## Primary-first output rule — supersedes legacy forced two-direction rule (2026-10-14)
Give ONE clearly labeled 90-minute Primary H/D/A for each verified match, even if provisional and low confidence. A second candidate is OPTIONAL only where independent match evidence actually supports it; never add draw as generic insurance. For every match explicitly report draw risk, reasoned hedge/no-hedge decision, and upset counterevidence. Distinguish match prediction from betting eligibility: insufficient official odds or calibrated model probabilities means betting PASS, not pretending there was no research direction.

Assess each applicable market separately (official integer handicap 1X2, exact total goals, half/full time, score); provide ordered provisional candidates only if independently justified. If exact total/score/HT-FT lacks sufficient evidence, clearly label it hypothetical/low-confidence; do not manufacture precise probabilities, EV, or official handicap lines. Exact integer JC handicap outcomes cannot be asserted before the official handicap is verified.

Every match and every forecast image must show at least 3 independent and traceable supporting facts (or conspicuous EVIDENCE_INSUFFICIENT), 1 strongest contrary fact, as-of source times, model and version, data gaps, and whether SHADOW or FINAL. An odds-only or score-only poster is not compliant. For official betting recommendations each selected leg must have verified JC SP >= 1.70 and independently justified positive EV. Two-leg parlays only, never three-leg. FINAL status must be explicit and timestamped before the sales cutoff; keep prior snapshots immutable.

## Evidence-first model architecture — mandatory correction (2026-10-12)
1. Predict match outcome using non-market football evidence FIRST: verified recent 5/10 completed matches, opponent-adjusted strength, home/away attack and defense, rest/travel, lineups and absences when available, schedule incentives, xG/xGA when validated. Record exact raw sources and as-of timestamps.
2. Fit independent goals/score distribution and draw calibration from historical matches; evaluate 1X2, exact goals, half/full time, scorelines and handicap separately. Do not infer every market mechanically from one guessed score.
3. Only AFTER freezing the evidence-only forecast, read market odds to calculate vig-free market probabilities, disagreement, EV and risk. Market odds must not determine the evidence-only first-choice outcome; keep separate market-only benchmark and report divergence.
4. Never fabricate missing football inputs or probabilities; if evidence threshold fails, show missing-data status rather than claiming a fully validated forecast. Preserve user-required two ordered directions per market when estimates can be supported; distinguish prediction from bet recommendation.
5. Backtest against historical matches with Brier score, log loss, calibration and source leakage checks. Any weighting changes must pass shadow evaluation before production promotion.
6. Audit output must include evidence-only model result, market benchmark (if available), disagreement, field coverage, and timestamped source links.
