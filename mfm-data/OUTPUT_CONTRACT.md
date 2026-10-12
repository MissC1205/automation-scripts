# MFM Mandatory Prediction Output Contract

Effective: 2026-10-12

For every requested match, always give a concrete provisional prediction for 90-minute 1X2 (one of H/D/A), exact total goals, half-time/full-time, and one exact score. Include evidence, counterevidence, missing fields, confidence and prediction timestamp/version. No skipping matches or replacing a prediction with PASS.

For official Chinese JC handicap 1X2, give a concrete handicap outcome only after confirming the actual official integer handicap. If unavailable, provide a clearly labeled hypothetical outcome at an explicitly assumed line (e.g. home -1), NEVER misrepresent it as the official JC result. The assumed line may differ from the actual offered line.

Keep prediction distinct from betting recommendation: a low-confidence match can have a prediction and still be NO BET. Do not fabricate prices, probabilities, xG, injuries or official lines. Track revisions with timestamp and reasons; do not overwrite historical predictions. If a match identity itself cannot be verified, explicitly flag unverified identity and refrain from presenting it as an official JC fixture.

## Two-direction output rule (user update 2026-10-12)
For EVERY match give EXACTLY TWO ordered candidate outcomes for each: (1) 90-minute 1X2 (H/D/A), (2) official integer-handicap 1X2 (handicap H/D/A), (3) exact total goals (two distinct integers), (4) half-time/full-time (two distinct valid outcomes), and (5) exact score (two distinct scorelines, to keep the score market consistent). Mark first choice primary and second choice backup. Never automatically insert a draw as backup: both must be supported by independent estimated probabilities and evidence, or clearly marked provisional if not estimated. Official handicap outcomes require the actual official line; if missing, give two outcomes for an explicitly stated hypothetical line, NOT mislabeled official picks. For each market include supporting and contrary evidence, confidence and coverage. These are forecasts, not necessarily bets; do not automatically recommend combining both selections, and do not assert a two-choice bet is profitable without prices and cost analysis.
