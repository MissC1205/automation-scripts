# MFM Mandatory Prediction Output Contract

Effective: 2026-10-12

For every requested match, always give a concrete provisional prediction for 90-minute 1X2 (one of H/D/A), exact total goals, half-time/full-time, and one exact score. Include evidence, counterevidence, missing fields, confidence and prediction timestamp/version. No skipping matches or replacing a prediction with PASS.

For official Chinese JC handicap 1X2, give a concrete handicap outcome only after confirming the actual official integer handicap. If unavailable, provide a clearly labeled hypothetical outcome at an explicitly assumed line (e.g. home -1), NEVER misrepresent it as the official JC result. The assumed line may differ from the actual offered line.

Keep prediction distinct from betting recommendation: a low-confidence match can have a prediction and still be NO BET. Do not fabricate prices, probabilities, xG, injuries or official lines. Track revisions with timestamp and reasons; do not overwrite historical predictions. If a match identity itself cannot be verified, explicitly flag unverified identity and refrain from presenting it as an official JC fixture.

## Two-direction output rule (user update 2026-10-12)
For EVERY match give EXACTLY TWO ordered candidate outcomes for each: (1) 90-minute 1X2 (H/D/A), (2) official integer-handicap 1X2 (handicap H/D/A), (3) exact total goals (two distinct integers), (4) half-time/full-time (two distinct valid outcomes), and (5) exact score (two distinct scorelines, to keep the score market consistent). Mark first choice primary and second choice backup. Never automatically insert a draw as backup: both must be supported by independent estimated probabilities and evidence, or clearly marked provisional if not estimated. Official handicap outcomes require the actual official line; if missing, give two outcomes for an explicitly stated hypothetical line, NOT mislabeled official picks. For each market include supporting and contrary evidence, confidence and coverage. These are forecasts, not necessarily bets; do not automatically recommend combining both selections, and do not assert a two-choice bet is profitable without prices and cost analysis.

## Evidence-first model architecture — mandatory correction (2026-10-12)
1. Predict match outcome using non-market football evidence FIRST: verified recent 5/10 completed matches, opponent-adjusted strength, home/away attack and defense, rest/travel, lineups and absences when available, schedule incentives, xG/xGA when validated. Record exact raw sources and as-of timestamps.
2. Fit independent goals/score distribution and draw calibration from historical matches; evaluate 1X2, exact goals, half/full time, scorelines and handicap separately. Do not infer every market mechanically from one guessed score.
3. Only AFTER freezing the evidence-only forecast, read market odds to calculate vig-free market probabilities, disagreement, EV and risk. Market odds must not determine the evidence-only first-choice outcome; keep separate market-only benchmark and report divergence.
4. Never fabricate missing football inputs or probabilities; if evidence threshold fails, show missing-data status rather than claiming a fully validated forecast. Preserve user-required two ordered directions per market when estimates can be supported; distinguish prediction from bet recommendation.
5. Backtest against historical matches with Brier score, log loss, calibration and source leakage checks. Any weighting changes must pass shadow evaluation before production promotion.
6. Audit output must include evidence-only model result, market benchmark (if available), disagreement, field coverage, and timestamped source links.
