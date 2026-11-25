# Evidence-bound Nanopublications 1.0.0

Reusable Skill for atomic qualified scientific claims, exact evidence/source binding and local unsigned Nanopublication export. The agent reads/extracts from actual materials; the helper checks provenance and serialization. Follow SKILL.md and the original case contract, not only the internal JSON schema.

Python >=3.10 standard library for JSON checks. RDF export/verification needs RDFLib 7.x (tested with 7.1.4; install `python -m pip install rdflib==7.1.4` if the pinned runtime lacks it). RDFLib is upstream BSD-3-Clause and is not bundled; no personal files/keys, external inference API or publication network is used. PDF extraction/OCR/rendering tools are selected from the actual runtime manifest.

SKILL.md describes reading, atomicity, metadata, uncertainty, review and final contract mapping. references/formats.md defines fields and a labelled synthetic interface example; references/atomicity.md provides 20 synthetic decomposition patterns. resources/relations.json is a local controlled relation vocabulary, not a domain ontology. scripts/nanopub_guard.py checks JSON, exports TriG/JSON-LD/review Markdown and independently parses RDF to verify graph invariants and lossless round-trip equivalence.

Limits: evidence exactness is not semantic entailment, numeric overlap does not prove correct variables/units, and conjunction detection does not prove non-atomicity. Source completeness, entity identities, causal direction, confidence grounds, figure interpretation and scientific correctness need agent/visual review. Unknown metadata stays explicit. Unsupported/conflicted candidates remain in JSON and are excluded from supported RDF output. No scientific scores or official answers are supplied.

Exported IDs are deterministic local UUID URNs, not Trusty URIs; no signatures or public network publication are performed. Source author attribution and extraction creator are separate. Source licenses are not invented or transferred. Supported means faithful evidence-backed extraction within its qualifiers, not proof of universal truth. Semantic QA is mandatory before claiming task completion.

Version 1.0.0. Original code/documentation MIT; see LICENSE.txt. Maintain by recording source/candidate corrections and validating actual failure modes. Formal benchmark cases and comparisons are platform-owned; local validation artifacts stay outside the submitted Skill.
