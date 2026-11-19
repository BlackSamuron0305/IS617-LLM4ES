# Run settings

`run_settings.csv` holds the settings of the main run. Each value is either backed by a source or our own data, or tested with extra runs. Sources checked on 2026-11-18; F = full text read, A = only the abstract or a summarising tool.

## What the model makers recommend

| Model | temperature | top_p | top_k | Max output | Source and exact wording |
|---|---|---|---|---|---|
| Qwen3 (32B and smaller), no thinking | 0.7 | 0.8 | 20 | 32,768 | Card, "Best Practices > 1. Sampling Parameters": "For non-thinking mode, we suggest using `Temperature=0.7`, `TopP=0.8`, `TopK=20`, and `MinP=0`." |
| Qwen3, thinking | 0.6 | 0.95 | 20 | 32,768 | Same section: "For thinking mode, use `Temperature=0.6`, `TopP=0.95`, `TopK=20`, and `MinP=0` ... **DO NOT use greedy decoding**". "2. Adequate Output Length": "We recommend using an output length of 32,768 tokens for most queries." |
| Gemma 4 31B | 1.0 | 0.95 | 64 | none | Card, "Best Practices > 1. Sampling Parameters": "Use the following standardized sampling configuration across all use cases: `temperature=1.0`, `top_p=0.95`, `top_k=64`". |
| Mistral Small 3.2 24B | 0.15 | none | none | none | Card, "Usage > Note 1": "We recommend using a relatively low temperature, such as `temperature=0.15`." |
| OLMo 3.1 32B | none | none | none | none | The card gives no recommendation; its inference example uses `top_k=50, top_p=0.95`. |

vLLM applies these defaults by itself unless a request sets them: "By default, the server applies `generation_config.json` from the Hugging Face model repository if it exists" (vLLM docs, OpenAI-compatible server). That is why `top_k` is in `run_settings.csv` and the runner sends every value explicitly.

## What audit studies use

| Study | Setting | Exact wording |
|---|---|---|
| Bowen et al. 2025, mortgage underwriting (F) | temperature 0, robustness at 0.3; seed 42 | Footnote 14, p. 13: "all experiments are conducted with LLM temperature parameters set to zero to reduce randomness in its replies. We show robustness to setting a higher temperature in Table A2." Appendix, pp. 56-57: "where possible, set seeds in the API calls"; "LLM providers do not guarantee strictly identical outputs." |
| An et al. 2025, PNAS Nexus, resume scoring (F) | temperature 0.0 (0.01 for Llama-3-70b), one pass | "conducted separately for each LLM at a temperature setting of 0.0" |
| Armstrong et al. 2024, Silicon Ceiling (F) | 50 repetitions; temperature not reported | Section 3.2.3: "the variance stabilizes after around 40 trials for each prompt; we therefore decided to run 50 trials in our audit." |
| Salinas et al. 2025, What's in a Name (F) | 100 repetitions, default parameters | Section 3.1: "we repeat our prompting for each combination of names and templates 100 times." |
| Tamkin et al. 2023 (F) | no sampling | Reads the probability of "yes" directly. |
| Gaebler et al. 2024 (F) | not reported | |
| Zheng et al. 2023, MT-Bench judge (F; code on GitHub) | judge temperature 0 | Not in the paper text; the FastChat code calls the judge with `temperature=0`. |
| Renze & Guven 2024 (A) | 0.0 to 1.0, 10 answers per question | Temperature changes from 0.0 to 1.0 "do not have a statistically significant impact on LLM performance for problem-solving tasks." |
| Atil et al. 2024 (A) | temperature 0, fixed seed, 10 runs | "accuracy variations up to 15%" between runs with the same settings. |

## Our data (earlier design, old repo `IS617-LLM4ES-WORK`)

- Answer length: in the main run of Qwen3 32B, Gemma 4 and Mistral Small (98,280 answers, limit 800) every answer ended by itself; the longest was 180 tokens, the median 67 to 83.
- Thinking runs: about 600 tokens per answer for Qwen3, never 8,000.
- Temperature: the gap among the 21 was about the same at 0, 0.3, 0.7 and 1.0 for Qwen3 32B and Gemma 4; for Mistral Small it grew with temperature (0.9 at 0, 3.7 at 0.7).

## Decision per setting

| Setting | Value | Backed by | Tested? |
|---|---|---|---|
| temperature | 0.7 | nothing common: audits use 0, makers 0.15 to 1.0 | yes: 0.0, 1.0, makers' setting |
| top_p | 0.95 | Gemma 4; Qwen3 with thinking | yes: makers' setting |
| top_k | off | same for every model (vLLM would otherwise use each model's default) | yes: makers' setting |
| max_tokens | 1,024 | our data (longest answer 180 tokens) | no; cut-off answers are counted |
| max_tokens_think | 16,384 | our data (about 600 used); Qwen3 recommends 32,768 | no |
| seed | 42 + repetition | Bowen et al. | no; exact repeats are not guaranteed |
| repeats | 5 | below audit practice (50 to 100) | yes: gap from the first k repetitions; 20 repetitions if it has not settled |
| judge_temperature | 0 | MT-Bench judge code; An et al. | no |

## The extra runs

Base prompt only, one repetition, the three main models. Commands (with the server running, see `cluster/README.md`):

```
python -m pipeline.runner.run_model --model qwen3-32b --variant base --repeats 1 --tag t0 --temperature 0
python -m pipeline.runner.run_model --model qwen3-32b --variant base --repeats 1 --tag t1 --temperature 1.0
python -m pipeline.runner.run_model --model qwen3-32b --variant base --repeats 1 --tag maker --temperature 0.7 --top-p 0.8 --top-k 20
python -m pipeline.runner.run_model --model gemma-4-31b-it --variant base --repeats 1 --tag maker --temperature 1.0 --top-p 0.95 --top-k 64
python -m pipeline.runner.run_model --model mistral-small-3.2-24b-instruct --variant base --repeats 1 --tag maker --temperature 0.15
python -m pipeline.runner.run_model --model qwen3-32b --variant base --tag r20 --repeats 20
```

The last line only if the gap has not settled after five repetitions (notebook `05_run_settings`). Each run lands in its own file, `results/raw/<model>__<tag>.jsonl`, and in `answers.csv` with its `run` tag and settings.
