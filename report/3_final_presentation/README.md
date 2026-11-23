# Final presentation

**9-10.12.2026.** 12 minutes for each team + 15 minutes of Q&A. 25 points.

Criteria, copied from the course
[grading rubric](https://github.com/dess-mannheim/LLM4ESS/blob/main/grading_rubric.md)
(read 2026-10-04):

- [ ] Brief research question and motivation [1]
- [ ] Data and methods [2]
- [ ] Results [5]
- [ ] Conclusion and critique [2]
- [ ] Q&A [15]

Not every member has to present, but all members should be prepared to answer questions.
Keep to the allocated time.

The slides (PowerPoint) go in this folder.

## The deck

`final.pptx` is built by `build_final.py` (run from the repo root: `python report/3_final_presentation/build_final.py`).
Template and design: the pitch (`report/1_first_presentation/pitch.pptx`), as for the midterm. Wording drafted by
Claude Code at Laith's request (2026-11-19): rewrite it or declare it. Facts and sources are in the speaker notes.

Design slides (1-9) and backup (17-22) are filled from `experiment/`. The result slides (10-15) and the conclusion
are slots: fill `FILL`, `FOUND` and `MEANS` at the top of the script, save each figure as `figures/<name>.png`
(names in `FILL`) and rebuild. Do not edit `final.pptx` by hand until the results are in, or a rebuild overwrites it.

Timing (12 min): slides 2-4 about 2 min, 5-9 about 3 min, 10-15 about 5.5 min, 16 about 1.5 min.
Open point: RQ4 is the cost question (paper, notebook 03); the midterm's RQ4 was the reasons, now an exploratory slide.
