# Harmonization Engine

## Current scoring model

The harmonic engine now evaluates chord candidates per melodic event and selects a progression by maximizing:

`score = harmony_score * cadence_score * phrase_score`

Generated voice notes are then selected with:

`score = harmony_score * voice_leading_score * cadence_score * phrase_score * voice_assignment_score`

### Harmonic scoring

- `harmony_score`: melody/chord fit plus `harmony.chord_preference` weighting.
- `cadence_score`: phrase-end cadence weighting from `harmony.cadence_model`.
- `phrase_score`: phrase-region cadence pressure from `phrases.behavior.*.cadence_strength`.

### Voice-note scoring

- `harmony_score`: chord-tone fit and common-tone retention.
- `voice_leading_score`: stepwise motion, leap control, crossing/parallels constraints.
- `cadence_score`: tonic/dominant/subdominant behavior near cadence points.
- `phrase_score`: cadence-strength pressure by phrase region.
- `voice_assignment_score`: `voice_assignment.<voice>.priority.*` weighting for melody proximity, chord tones, passing tones, and root motion.

## Implemented CASL fields influencing harmony

The following parsed CASL 2.0 fields now materially affect harmonic output:

- `harmony.chord_preference.diatonic`
- `harmony.chord_preference.secondary_dominants`
- `harmony.cadence_model.authentic`
- `harmony.cadence_model.plagal`
- `voice_assignment.<voice>.priority.melody`
- `voice_assignment.<voice>.priority.chord_tones`
- `voice_assignment.<voice>.priority.passing_tones`
- `voice_assignment.<voice>.priority.root_motion`
- `phrases.behavior.start.cadence_strength`
- `phrases.behavior.climax.cadence_strength`
- `phrases.behavior.end.cadence_strength`

## Explain mode

`--explain` now exports:

- detected key
- detected phrase profile
- inferred chord stream (with candidates)
- selected chord progression
- score breakdown (harmonic and per-generated-voice)

## Future roadmap

- Improve phrase segmentation beyond a single-profile phrase model.
- Expand cadence templates by style and meter.
- Add broader non-diatonic candidate families (mixture, borrowed chords) without changing CASL syntax.
- Add optional machine-readable explain export targets (file output formats).
