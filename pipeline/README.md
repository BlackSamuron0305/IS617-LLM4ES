# Pipeline

One folder per step, in the order they run. Run every command from the repository root.

| Step | Command | Reads | Writes |
|---|---|---|---|
| 1. Build prompts | `python -m pipeline.prompt_builder.build_prompts` | `experiment/prompts/` (prompt files, `run_plan.csv`), `experiment/applicants/` (`application_template.txt`, `applicants.csv`), `experiment/countries/nationalities.csv` | `experiment/prompts/prompts.csv` |
| 2. Run a model (cluster) | `python -m pipeline.runner.run_model --model qwen3-32b` | `prompts.csv`, `experiment/config/` | `results/raw/<model>.jsonl` |
| 3. Read the answers | `python -m pipeline.answers.parse_answers` | `results/raw/*.jsonl` | `results/processed/answers.csv` |
| 4. Build judge prompts | `python -m pipeline.judge.build_judge_prompts` | `answers.csv`, `experiment/judge/judge_prompt.txt` | `results/processed/judge_prompts.csv` |
| 5. Run the judge (cluster) | `python -m pipeline.runner.run_model --model <judge> --judge` | `judge_prompts.csv` | `results/raw/judge/<judge>.jsonl` |
| 6. Read the judge codes | `python -m pipeline.judge.parse_judge --judge <judge>` | `results/raw/judge/<judge>.jsonl` | `results/processed/judge_codes.csv` |
| 7. Analysis | the notebooks in `pipeline/analysis/notebooks/` | `results/processed/` | `results/figures/` |

## Notes

- **Prompt fields.** Only the fields the application template names (`{{applicant.name}}`, `{{nationality.demonym}}`, ...) reach the model. Every column of `applicants.csv` stays available for the analysis.
- **Changing prompts.** Every answer stores the fingerprint of the prompt it answered. The runner skips only answers whose fingerprint still matches, so a changed or new prompt runs again and nothing else does. How to add or change one: `experiment/prompts/README.md`.
- **The runner** needs the server address in `BASE_URL`; `cluster/serve_and_run.sbatch` sets it. It skips answers that are already saved, so a job that stops can simply be started again. Each repetition gets its own seed (`seed` + repetition number).
- **The runner refuses to start** when the server serves other weights than the model in `models.csv` (the weight folder must be named like the alias, for example `qwen3-32b`), when `max_tokens` does not fit the server's context length, or when `--temperature 0` is asked for without `--repeats 1`. It stops with an error after 50 failed calls in a row (for example when the server dies), skips a half-written last line left by a killed job, and saves the weights, the revision and the token counts with every answer.
- **One job per model and tag at a time.** Two jobs on the same file would send the same calls twice.
- **Runs with other settings:** `--tag NAME` plus any of `--temperature`, `--top-p`, `--top-k`, `--repeats`, `--variant`. Each tag gets its own raw file, and `answers.csv` keeps the tag and the settings; the analysis uses `run == "main"` unless it compares runs. Which runs and why: `experiment/config/README.md`.
- **Statistics** live in `pipeline/analysis/stats.py`. The notebooks only load, call and plot.
- **Tests:** `python -m pytest tests`, one subfolder per step.
- Libraries: the steps 1 to 6 need only Python 3.10 or newer; the analysis needs `requirements.txt`.

## Running on the cluster

The `cluster/` folder is not in git; copy it to the cluster clone by hand. `prompts.csv` is not in git either: build it there.

```
git clone <repo> && cd IS617-LLM4ES
python3 -m pipeline.prompt_builder.build_prompts
python3 -m pytest tests                        # optional, needs pytest
```

Download each model once, at the revision in `experiment/config/models.csv`, into a folder named like the alias:

```
sbatch cluster/download_model.sbatch Qwen/Qwen3-32B qwen3-32b 9216db5781bf21249d130ec9da846c4624c16137
```

Run one model as a chain of 30-minute jobs. Each job ends at once when nothing is left (`--check-done`):

```
M=qwen3-32b
cluster/submit_chain.sh 16 --partition=gpu_h100_short --time=00:30:00     --export=ALL,MODEL_PATH=$WS/models/$M,MODEL_NAME=$M,ALLOW_REAL_CALLS=yes,SKIP_IF="python3 -m pipeline.runner.run_model --model $M --check-done"     cluster/serve_and_run.sbatch python3 -m pipeline.runner.run_model --model $M
```

Models with a `vllm_args` entry in `models.csv` need it passed to the server, for example Mistral:

```
M=mistral-small-3.2-24b-instruct
... --export=ALL,MODEL_PATH=$WS/models/$M,MODEL_NAME=$M,VLLM_ARGS="--tokenizer-mode mistral --config-format mistral --load-format mistral",ALLOW_REAL_CALLS=yes,SKIP_IF=...
```

The thinking run uses the weights of `qwen3-32b` with `VLLM_ARGS="--max-model-len 20480"` and `--model qwen3-32b-think`.

Time on one H100 for the 175,000 calls of a model (estimate from the earlier runs): Mistral about 3.5 hours, Qwen3 32B about 5.5, Gemma about 10. With 30-minute jobs, of which a few minutes go to loading the model, that is about 10, 15 and 25 jobs. Before the full run, do a smoke test of a few calls per model: `--limit 50`, then `python -m pipeline.answers.parse_answers` and look at the answers.

### Faster: split a model into parts that run at the same time

When the queue is full, a chain waits again before every job. Instead, split a model's prompts into parts (`--part i --parts n`): every prompt with all its repeats belongs to exactly one part, each part writes its own file `results/raw/<model>.part<i>of<n>.jsonl`, and all parts can run at once on different GPUs. Answers already in the main file or in any part file count as done, and `parse_answers` reads all files of a model together. Never run a chain and parts of the same model at the same time.

Size the parts so one part fits into one 30-minute job (Mistral 12, Qwen3 32B 18, Gemma 36), and submit them as a job array, plus a second array as a backup that only starts after the first and skips every finished part:

```
M=qwen3-32b; N=18
RUN="python3 -m pipeline.runner.run_model --model $M --parts $N --part \$SLURM_ARRAY_TASK_ID"
O="--partition=gpu_h100_short --time=00:30:00 --array=1-$N --export=ALL,MODEL_PATH=$WS/models/$M,MODEL_NAME=$M,ALLOW_REAL_CALLS=yes"
A=$(SKIP_IF="$RUN --check-done" sbatch --parsable $O cluster/serve_and_run.sbatch bash -c "$RUN")
SKIP_IF="$RUN --check-done" sbatch --parsable $O --dependency=afterany:$A cluster/serve_and_run.sbatch bash -c "$RUN"
```

`python3 -m pipeline.runner.run_model --model $M --check-done` (without `--part`) still prints the calls left for the whole model.
