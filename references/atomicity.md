# Twenty synthetic atomicity patterns

All entities and statements below are abstract teaching examples, not factual scientific findings or official case answers. Apply the rules to actual paper content and evidence at runtime.

| # | Synthetic source pattern | Extraction decision |
|---|---|---|
| 1 | A correlates with B and C. | Separate A–B and A–C associations, preserving shared cohort/conditions. |
| 2 | A increased B, whereas C decreased D. | Separate observations with correct subjects and directions. |
| 3 | Under dry conditions, A increased B. | Keep dry conditions attached; no unconditional A–B claim. |
| 4 | A may inhibit B. | One suggested inhibition, not observed established inhibition. |
| 5 | A did not inhibit B in assay X. | Retain negated polarity and assay scope; do not assert positive inhibition. |
| 6 | A was associated with B; therefore it may cause B. | Separate observed association from tentative author causal interpretation. |
| 7 | A predicted B in training data but failed in validation. | Separate dataset-specific claims and retain the validation limitation. |
| 8 | No significant difference between A and B. | Do not convert to equality/equivalence or absence of any effect. |
| 9 | The study found no evidence that A causes B. | Represent absence of evidence, not proven non-causation. |
| 10 | A increased B only in population P. | Restrict to P; do not generalize to all populations. |
| 11 | A increased B at time T but not earlier. | Separate time-specific positive/negative claims where independently testable. |
| 12 | A is part of B. | Preserve part-to-whole direction, not B part-of A. |
| 13 | A and B jointly increased C. | Do not attribute the effect to A or B independently without evidence. |
| 14 | The A/B ratio increased. | One ratio outcome; do not infer individual component changes. |
| 15 | A was measured as value V in unit U. | Preserve value, precision, unit, definition and measurement conditions together. |
| 16 | A lay within interval L–H. | Preserve one interval-valued claim, not unrelated endpoint findings. |
| 17 | Prior work reported A; this paper measured B. | Attribute A to prior work and B to the actual present source. |
| 18 | Figure X shows B under method M. | Bind panel/caption/method evidence; do not infer a numerical effect from caption alone. |
| 19 | Sources X and Y disagree about A. | Retain both source/version-specific claims and an explicit conflict record. |
| 20 | A follows from premises B and C. | Mark extractor inference if not author-reported; cite both premises and explain the step. |

Atomicity is semantic, not sentence length or number of conjunctions. A coordinated subject may denote a single intervention; a short sentence may hide multiple independently testable outcomes. A heuristic warning is a review request, never a splitting command.
