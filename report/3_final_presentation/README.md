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

Design slides (1-9) and backup (18-24) are filled from `experiment/`. The result slides (10-16) and the conclusion (17) are filled from
the analysis notebooks (`pipeline/analysis/notebooks/`, 2026-11-24): `FILL`, `FOUND` and `MEANS` at the top of the script hold the
titles, key numbers and speaker notes, and the notebooks copy their figures to `figures/`. After a new analysis run, rerun the
notebooks, update `FILL` and rebuild. Do not edit `final.pptx` by hand, or a rebuild overwrites it.

Timing (12 min): slides 2-4 about 2 min, 5-9 about 3 min, 10-16 about 5.5 min (about 45 s each), 17 about 1.5 min.
RQ4 is the cost question: refusals and fees for borderline applicants, and what an earlier refusal does to the next application
(notebook 06_consequences). The judge slide is in the backup (slide 19).
