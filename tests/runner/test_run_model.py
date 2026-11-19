from pipeline.runner.run_model import pending


def test_only_missing_or_changed_prompts_run():
    prompts = [{"prompt_id": "a", "prompt_hash": "new", "repeats": "2"},
               {"prompt_id": "b", "prompt_hash": "same", "repeats": "2"}]
    done = {("a", 1, "old"), ("a", 2, "old"), ("b", 1, "same"), ("b", 2, "same")}
    assert [(p["prompt_id"], k) for p, k in pending(prompts, done)] == [("a", 1), ("a", 2)]
