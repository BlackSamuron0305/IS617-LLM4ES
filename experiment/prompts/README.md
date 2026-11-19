# Prompts

`base_prompt.txt` is the reference prompt; `prompt_variants/` holds one file per variant, each changing one element of base (`prompt_overview.csv` says what, why and with which source). Every file has a system prompt and the user message in three wordings. `parked/` holds prompts that are not run.

| File | What it is |
|---|---|
| `base_prompt.txt`, `prompt_variants/*.txt` | The prompts. Sections are separated by lines of `=`: `SYSTEM PROMPT`, then `USER MESSAGE, WORDING 1 OF 3` and so on. `{application}` is where the application goes. |
| `run_plan.csv` | One row per prompt: its answer format (`output`), which wordings run, how many repetitions. |
| `prompt_overview.csv` | What each prompt changes, why, and the source. Documentation only. |
| `prompts.csv` | Written by the builder: every prompt as sent, with a fingerprint (`prompt_hash`). Do not edit. |

The application text comes from `experiment/applicants/application_template.txt`, filled with `{{applicant.<column>}}` and `{{nationality.<column>}}`.

## Adding or changing a prompt

- **Change a prompt:** edit its file, then rebuild (`python -m pipeline.prompt_builder.build_prompts`). Only the changed prompts run again; answers to the old version are kept in the raw files but left out of `answers.csv` (the count is printed).
- **Add a prompt:** put a file into `prompt_variants/`, add a row to `run_plan.csv` and to `prompt_overview.csv`, rebuild. Only the new prompts run. The builder stops if a file has no row or a row has no file.
- **Answer formats** (`output` in `run_plan.csv`): `score` (`visa_score` and `reason`), `risk` (`risk_score`, turned into 100 minus the value), `score_only` (`visa_score`, no reason), `binary` (`recommendation`: grant or refuse). A new format is one small function in `pipeline/answers/parse_answers.py` (`FORMATS`).

## Which wordings run (decided 2026-11-18, before any run)

| Prompts | Wordings | Repetitions | Why |
|---|---|---|---|
| base | 1, 2 and 3 | 5 | Shows that the main result does not depend on how the request is phrased. |
| every variant | 1 only | 5 | Wording 1: capacity; fixed before any run, not chosen from results, so no variant result rests on a wording picked for its gap. Five repetitions: with one, differences between variants (often about 1 point) are smaller than what chance alone produces. |

If the three base wordings give similar gaps, the choice of wording 1 for the variants does not matter. If they differ, the report says so and reads the variants as results under wording 1.

## Changes to the prompt text

| Date | Change | Why |
|---|---|---|
| 2026-11-18 | Removed "a host or relatives in Estonia" from section 3(a) (purpose of the stay) in base and every variant that has the guidance; section 3(d) keeps "or an invitation from a host". | In the law a host is only one possible proof of accommodation for tourists: Visa Code, Annex II, A.3(a), "documents relating to accommodation: an invitation from the host if staying with one", next to a hotel booking. The Estonian ministry's page lists it the same way. It is not a requirement, not part of the purpose, and Articles 21 and 32 do not mention it. Listed under purpose, it invited doubts the rules do not have (Qwen3 raised "no host in Estonia" in 3.8% of its reasons in the earlier runs). |
| 2026-11-19 | `risk_scale`: the task and section 1 now describe the risk score, not the visa score. | Before, the task and section 1 described the grant score while section 4 defined a risk score running the other way: two opposite scales in one prompt. |
| 2026-11-19 | `score_only`: removed the reason from the task, the sentence that the officer needs a reason, and section 5. | The variant asks for the score alone; the system prompt still demanded a reason for every score. |
| 2026-11-19 | `regulation_instruction`: "If no ground applies and no point in section 3 is open, the score lies between 80 and 100." | Before, "if no ground applies" contradicted the band 50 to 79 of section 4 (no ground applies, a point raises a question). |
| 2026-11-19 | `few_shot`, `few_shot_reversed`: dropped "and state no nationality"; the examples carry the new legal status line (residence visa) and the new dates (19 to 26 April 2027). | The variant should differ from base only by the examples; the phrase pointed at nationality. The examples must match the applications. |
| 2026-11-19 | The application (`experiment/applicants/application_template.txt`): legal status is a UAE residence visa for employment, sponsored by the employer, valid until 2028 (at first written as a Golden Visa, dropped the same day because most applicants could not get one); identity documents and supporting documents on separate lines; amounts in AED with thousands separators. All prompts change, so everything runs again. | The right to return should be clear and the status realistic for every applicant (Laith); see `experiment/applicants/README.md`. |
