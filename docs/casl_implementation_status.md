# CASL Implementation Status Matrix

This matrix is based on the current parser and runtime behavior in:
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/parser/casl.py`
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/app.py`
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/generators/harmonic_voice.py`
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/generators/fixed_interval.py`
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/rules/engine.py`
- `/tmp/workspace/binyominzeev/choir-generator/choirgen/rules/range.py`
- `/tmp/workspace/binyominzeev/choir-generator/docs/casl_language.md`

| CASL field | Parsed | Affects generation | Where used in code | Only documented but not implemented |
|---|---|---|---|---|
| `project.name` | Yes | Yes | `parser/casl.py:102-104`, `app.py:62` | No |
| `project.version` | Yes | Yes | `parser/casl.py:104`, `models/spec.py:205-206`, `app.py:33-36,56,73-78` | No |
| `melody.source` | Yes | No | `parser/casl.py:106-108` | Yes |
| `melody.file` | Yes | No | `parser/casl.py:106-109` | Yes |
| `analysis.key_detection` | Yes | Yes (triggers harmony analysis) | `parser/casl.py:110-114`, `app.py:44-45` | No |
| `analysis.chord_inference` | Yes | Yes (triggers harmony analysis) | `parser/casl.py:110-114`, `app.py:44-45` | No |
| `analysis.phrase_detection` | Yes | Yes (triggers phrase detection) | `parser/casl.py:110-114`, `app.py:40-41` | No |
| `arrangement.type` | Yes | No | `parser/casl.py:115-117` | Yes |
| `harmony.mode` | Yes | Yes (triggers harmony analysis) | `parser/casl.py:118-120`, `app.py:44-45` | No |
| `harmony.roman_numerals.enabled` | Yes | No | `parser/casl.py:120-122` | Yes |
| `harmony.chord_preference.diatonic` | Yes | No | `parser/casl.py:123-125` | Yes |
| `harmony.chord_preference.secondary_dominants` | Yes | No | `parser/casl.py:123-126` | Yes |
| `harmony.cadence_model.authentic` | Yes | No | `parser/casl.py:127-129` | Yes |
| `harmony.cadence_model.plagal` | Yes | No | `parser/casl.py:127-130` | Yes |
| `voices.<name>.role` | Yes | Yes (selects original/generated voices) | `parser/casl.py:203,217`, `models/spec.py:213-214,221-222` | No |
| `voices.<name>.source` | Yes | Yes (selects original voice) | `parser/casl.py:209,217`, `models/spec.py:210-211` | No |
| `voices.<name>.generate` | Yes | Yes (selects generated voices) | `parser/casl.py:204,210,217`, `models/spec.py:221` | No |
| `voices.<name>.range.low` | Yes | Yes (candidate generation + range rule) | `parser/casl.py:202,227-229`, `generators/harmonic_voice.py:18-19`, `rules/range.py:12-17` | No |
| `voices.<name>.range.high` | Yes | Yes (candidate generation + range rule) | `parser/casl.py:202,227-229`, `generators/harmonic_voice.py:18-19`, `rules/range.py:13-17` | No |
| `voices.<name>.range.strict` | Yes | No | `parser/casl.py:230` | Yes |
| `voices.<name>.strategy.type` | Yes | Yes (strategy selection) | `parser/casl.py:192-200`, `app.py:56,73-78`, `generators/factory.py:8-13` | No |
| `voices.<name>.strategy.*` (config) | Yes | Yes for strategy-specific keys | `parser/casl.py:199`, `generators/fixed_interval.py:12` | No |
| `voices.<name>.<other keys>` (stored in `config`) | Yes | No (currently) | `parser/casl.py:214-218` | Yes |
| `ranges.<voice>` (`[low, high]`) | Yes | Yes (default voice range) | `parser/casl.py:69-72,79,202` | No |
| `ranges.<voice>.low` (mapping form) | Yes | Yes | `parser/casl.py:227-229`, `generators/harmonic_voice.py:18-19`, `rules/range.py:12-17` | No |
| `ranges.<voice>.high` (mapping form) | Yes | Yes | `parser/casl.py:227-229`, `generators/harmonic_voice.py:18-19`, `rules/range.py:13-17` | No |
| `ranges.<voice>.strict` (mapping form) | Yes | No | `parser/casl.py:230` | Yes |
| `voice_assignment.<voice>.priority.melody` | Yes | No | `parser/casl.py:80,239` | Yes |
| `voice_assignment.<voice>.priority.chord_tones` | Yes | No | `parser/casl.py:80,240` | Yes |
| `voice_assignment.<voice>.priority.passing_tones` | Yes | No | `parser/casl.py:80,241` | Yes |
| `voice_assignment.<voice>.priority.root_motion` | Yes | Yes (scoring bonus) | `parser/casl.py:80,242`, `generators/harmonic_voice.py:74-75,145` | No |
| `voice_leading.forbid.parallel_fifths` | Yes | Yes | `parser/casl.py:151-153`, `generators/harmonic_voice.py:38,165-166` | No |
| `voice_leading.forbid.parallel_octaves` | Yes | Yes | `parser/casl.py:151-154`, `generators/harmonic_voice.py:39,167-168` | No |
| `voice_leading.forbid.voice_crossing` | Yes | Yes | `parser/casl.py:151-155`, `generators/harmonic_voice.py:37,142-143` | No |
| `voice_leading.prefer.stepwise_motion` | Yes | Yes | `parser/casl.py:156-158`, `generators/harmonic_voice.py:24-27`, `rules/engine.py:42-45` | No |
| `voice_leading.prefer.common_tone_retention` | Yes | Yes | `parser/casl.py:156-159`, `generators/harmonic_voice.py:28-31,159-160`, `rules/engine.py:42-45` | No |
| `voice_leading.prefer.small_leaps` | Yes | Yes | `parser/casl.py:156-160`, `generators/harmonic_voice.py:32-35,156-157`, `rules/engine.py:42-45` | No |
| `rules.<rule>.value` | Yes | Yes for rules read by runtime (`max_leap`) | `parser/casl.py:162,246-252`, `rules/engine.py:33-40`, `generators/harmonic_voice.py:22` | No |
| `rules.<rule>.weight` | Yes | Yes for rules read by runtime (`max_leap`, `stepwise_preference`) | `parser/casl.py:162,246-252`, `rules/engine.py:27-31`, `generators/harmonic_voice.py:23-27` | No |
| `phrases.detect` | Yes | Yes (triggers phrase detection) | `parser/casl.py:163-165`, `app.py:40-41` | No |
| `phrases.behavior.start.dynamics` | Yes | Yes (expression shaping) | `parser/casl.py:166,259`, `generators/harmonic_voice.py:231` | No |
| `phrases.behavior.start.cadence_strength` | Yes | No | `parser/casl.py:166,260` | Yes |
| `phrases.behavior.climax.dynamics` | Yes | Yes (expression shaping) | `parser/casl.py:167,259`, `generators/harmonic_voice.py:232` | No |
| `phrases.behavior.climax.cadence_strength` | Yes | No | `parser/casl.py:167,260` | Yes |
| `phrases.behavior.end.dynamics` | Yes | Yes (expression shaping) | `parser/casl.py:168,259`, `generators/harmonic_voice.py:233,256-260` | No |
| `phrases.behavior.end.cadence_strength` | Yes | No | `parser/casl.py:168,260` | Yes |
| `randomization.seed` | Yes | Yes (RNG seed) | `parser/casl.py:134-136`, `app.py:49`, `generators/harmonic_voice.py:207` | No |
| `randomization.variation.note_choice_probability` (legacy CASL 1.0) | Yes | Yes (legacy weighted choice) | `parser/casl.py:136-138,141-143`, `generators/harmonic_voice.py:191-196` | No |
| `randomization.voice_variation.enabled` | Yes | Yes | `parser/casl.py:139-143`, `generators/harmonic_voice.py:190-196` | No |
| `randomization.voice_variation.intensity` | Yes | Yes | `parser/casl.py:139-144`, `generators/harmonic_voice.py:193-204` | No |
| `randomization.rhythm_variation.enabled` | Yes | No | `parser/casl.py:145-147` | Yes |
| `randomization.rhythm_variation.intensity` | Yes | No | `parser/casl.py:145-148` | Yes |
| `expression.dynamics.enabled` | Yes | Yes | `parser/casl.py:172-174`, `generators/harmonic_voice.py:223-224` | No |
| `expression.dynamics.base` | Yes | Yes | `parser/casl.py:172-175`, `generators/harmonic_voice.py:231` | No |
| `expression.shaping.crescendo_towards_climax` | Yes | Yes | `parser/casl.py:176-178`, `generators/harmonic_voice.py:242-244` | No |
| `expression.shaping.phrase_decay` | Yes | Yes | `parser/casl.py:176-179`, `generators/harmonic_voice.py:233,245-247` | No |
| `extensions[].name` | Yes | No | `parser/casl.py:181,264-274` | Yes |

## Notes

- No CASL 2.0 field listed in `docs/casl_language.md` is completely unparsed.
- Several fields are parsed and carried in the model but currently have no runtime effect (marked as documentation-only in this matrix).
- Legacy CASL 1.0 random variation (`randomization.variation.note_choice_probability`) is implemented for backward compatibility.
