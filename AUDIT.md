# GOAL.txt hostile audit - 2026-08-14

Independent multi-agent audit against `GOAL.txt` (V1-V12), each verdict
backed by a check the auditor ran itself (clean clones, live renders,
strace, curl). Initial tally: 8 PASS, 4 FAIL. All FAILs fixed the same day;
the fixes and their regression tests are in the second commit wave.

| V | First audit | After fixes |
|---|---|---|
| V1 pipeline (clean clone, ~58s wall) | PASS | PASS |
| V2 Speko text is what renders | FAIL - captions showed aligner words | FIXED: `project_transcript` maps the API transcript onto the timings (tests: `test_project_transcript_*`) |
| V3 karaoke render | PASS | PASS |
| V4 config schema documented | FAIL - `caption.y`/`font` undocumented | FIXED: full defaults table in README Config |
| V5 SKILL.md drives a fresh agent | FAIL - no clone step, no overrides shape, cited engine source | FIXED: step 0 clone, overrides semantics + example, `frames` command in QA, source citation removed |
| V6 tests offline (strace: zero connect) | PASS | PASS (17 tests now) |
| V7 CI green + badge | PASS | PASS |
| V8 public repo, MIT, 6-step quickstart | PASS | PASS |
| V9 landing serves correctly | FAIL - Pages cname 301'd every asset into a dead domain | FIXED: cname cleared until DNS lands; all assets 200 from github.io |
| V10 no slop | PASS | PASS |
| V11 one factual Speko credit | PASS | PASS |
| V12 synthetic sample only | PASS | PASS |

Code-review findings fixed alongside (all reproduced by the auditor first):

- ffmpeg filtergraph breakage on filenames with `'` `,` `:` - two-level
  escaper `escape_filter_path`, verified against live ffmpeg 6.1, unit
  tested.
- `apply_overrides` corrupted neighbors on expanding rules, raised at
  end-of-list, and only replaced the first occurrence - rewritten to rebuild
  the list and redistribute timing; unit tested.
- Fonts missing from the wheel, so `uvx` installs silently lost Geist -
  `fonts/` force-included into the wheel, `_fonts_dir()` resolves packaged
  first and errors instead of silently substituting.
- 401/403 from the API now fail fast instead of retrying six times.
- Inputs without an audio stream get a clear error instead of a traceback.
- Windows documented as unsupported (WSL).

EXTERNAL (out of the build's hands): the Cloudflare CNAME for
captions.speko.ai. Until it exists, the site lives at
https://spekoai.github.io/captions/ and the repo's Pages custom domain
stays unset (setting it early is what broke V9 the first time).
