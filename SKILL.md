---
name: evidence-bound-nanopublications
description: Extract atomic scoped scientific claims from actual papers, bind exact evidence and versioned source metadata, validate provenance and export local unsigned four-graph Nanopublications as TriG and JSON-LD.
---

# Evidence-bound Nanopublications

Produce independently checkable knowledge units from the actual supplied literature. Each unit makes one qualified claim, binds its minimum sufficient evidence and retains the chain to paper/version/author. The executing agent reads and extracts; the helper validates ledgers and serializes RDF. It does not establish scientific truth or semantic entailment.

## Runtime and initial checkpoint

Read `/input/case.json`, actual `task.md` and `environment/resources.yaml` (locate the manifest if needed). Resolve bundled resources relative to that manifest. Inventory actual papers, supplements, questions and **every original output_contract field/type/artifact**. Preserve real `case_id`. Work under `/app/work`, save final deliverables under `/app/output`. Save an early honest partial result.json using the actual contract and update incrementally.

This Skill normally resides at `/skills/weekly-skill`. `scripts/nanopub_guard.py check` uses Python 3.10+ standard library only. RDF export/parse verification additionally requires RDFLib 7.x; prefer the pinned runtime, otherwise install `rdflib==7.1.4` with the available package manager if allowed. No remote model, signing key or publication service is required. If RDFLib is unavailable, still deliver checked JSON and an explicit export limitation rather than claiming RDF was generated. Discover PDF extraction/render/OCR tools from the runtime manifest and verify actual availability.

## Read, locate and separate claims

Read actual material, not labels or abstract alone. Inspect relevant main-text sections, figures, tables, captions, footnotes, methods and supplements. Verify native PDF extraction order and numeric/symbol fidelity against rendered pages; use page/crop OCR when needed and retain original evidence. Missing/inaccessible source is different from absent evidence or conflicting evidence. Do not reconstruct unreadable scientific text from expectations.

Create `/app/work/claims.json` following `references/formats.md`: actual document identities/hashes and metadata, exact source blocks with stable locators, and scoped assertions. Retain positive 1-based PDF page numbers, printed labels separately, section/paragraph/bbox or table/figure/panel/cell/equation coordinates. For joined cross-page evidence retain all original fragments. Use short exact quotes that jointly support the complete qualified statement, not an entire abstract. A figure result often requires its panel, caption and method context; preserve crop paths and the associated textual observation/transcription rather than assuming caption text proves an effect size.

Use this atomicity test: could one part be false while another remained true? If yes, split independent findings. Each assertion has one subject, one relation, one object/outcome and its necessary scope. Preserve comparator, population/material, experimental state, time, uncertainty, negation and modality. Do not split a condition away from its conclusion or turn a numerical interval into unrelated claims. A causal mechanism and an observed correlation are distinct assertions. `references/atomicity.md` gives 20 synthetic decomposition patterns, not formal case answers.

## Bind evidence and preserve epistemic limits

- Classify each claim as directly reported, author interpretation or extractor inference. Direct evidence supports the wording, not universal scientific truth. An inference cites premises and explains the inferential step; do not call it a verbatim author conclusion.
- Distinguish source roles: the cited prior study is not automatically the current paper's own experiment. Record which source/version actually asserts the statement and which fragment supports it. Preserve contradictory evidence separately with a conflict explanation.
- Preserve raw values, units, sign, precision, uncertainty, sample size, denominator and experiment. Quantitative claims must be supported by the corresponding table/cell/text, not only a general caption. Approximate digitization and derived calculations need explicit method/input/code and uncertainty; do not invent missing parameters.
- Map relations conservatively using `resources/relations.json`. Association/prediction is not causation. Keep relation direction explicit; do not reverse treatment/outcome or part/whole. If no controlled relation fits, use `related_to` with an exact textual explanation and flag review, or extend the local vocabulary explicitly. Do not invent official ontology terms. External entity IDs are optional and must be verified; otherwise retain a local labelled entity.
- Keep polarity (`affirmed`/`negated`) and modality (`observed`/`suggested`/`hypothesis`) as explicit qualifiers. “No significant difference” is not equivalence, and absence of evidence is not evidence of absence. A negative/tentative statement must not become a positive unconditional RDF triple.
- Confidence is an auditable category with a reason (evidence directness, OCR fidelity, subject resolution, scope and conflicts), not an invented calibrated probability. Label supported, uncertain, unsupported and conflicted candidates separately. Unsupported/conflicted candidates remain in JSON for review and are not silently exported as supported nanopublications.

## Keep assertion provenance separate from publication information

Record paper title, author list, year, persistent identifier if present, version and actual source hash. Unknown metadata is null/empty with a specific missing-metadata reason, never fabricated. A DOI is not a version identifier; distinguish preprint/journal/supplement and revisions. Do not mint an ORCID or entity URI from a person's name. Preserve source URL/identifier when actually known.

The original source/author provenance describes where the assertion came from. The creator/time in publication information describes the current extraction/export, and must not impersonate the paper's authors. Use the actual extractor identity description and actual timezone-aware creation timestamp; `publication.created_at` is recorded once in the input ledger so reruns are reproducible. A source license does not automatically authorize a new nanopublication license; preserve license as unknown unless actually specified for reuse. Keep quotations minimal.

## Validate before export

```bash
python /skills/weekly-skill/scripts/nanopub_guard.py check \
  --input /app/work/claims.json --out /app/output/qa.json
```

Resolve invalid/duplicate IDs, broken document/block references, source hash mismatches, quotes absent from cited text, missing qualifiers/metadata reasons and unsupported numerical tokens. The helper flags potentially compound assertions, uncertain confidence, duplicate scoped content and indirect evidence. Check subject identity, relation direction, polarity, causal strength, minimal evidence sufficiency and numerical conditions manually against the source. A quote match or numeric overlap does not establish entailment. Preserve actual findings and an evidence-based resolution/change log rather than deleting inconvenient warnings.

Deduplicate only when subject, relation, object, conditions, polarity, modality and source/version are equivalent. Merge supporting evidence links rather than discarding them. Similar wording across different cohorts, times, endpoints or versions stays separate. A partial result identifies exact candidates/fields/material still unresolved and why.

## Export machine-readable local drafts

```bash
python /skills/weekly-skill/scripts/nanopub_guard.py export \
  --input /app/work/claims.json --out /app/output/nanopublications
python /skills/weekly-skill/scripts/nanopub_guard.py validate-rdf \
  --input /app/output/nanopublications.trig --out /app/output/rdf-qa.json
```

Exporter writes one four-graph nanopublication per `supported` claim, a TriG dataset, JSON-LD, readable review Markdown and a manifest retaining skipped candidates/reasons. Each has separate head, assertion, provenance and publication-info graph URIs. Provenance refers to the assertion graph and concrete evidence/source; publication info refers to the nanopublication and actual extractor/time.

The assertion uses a **scoped RDF statement resource** with subject/predicate/object plus polarity/modality/conditions. Reification does not assert its underlying triple unconditionally. This deliberate representation preserves uncertain and negated relations. The local relation vocabulary is explicitly custom, not an external scientific ontology. JSON-LD is a lossless alternate serialization of the same RDF dataset. Independently parse both formats and verify quad/graph equality; the helper performs this round-trip check during export. Do not treat JSON alone as standards-compliant RDF.

IDs are deterministic local UUID URNs derived from canonical claim/source/publication input; they are **not Trusty URIs**, signatures, globally registered or dereferenceable publications. Do not claim cryptographic signing or public publication occurred. The challenge requires exported artifacts, not deployment to the public nanopublication network. Signing/publishing would require an explicitly requested separate workflow and real validated tools/identity.

## Deliver the actual requested result

Map reviewed assertions/evidence/source metadata into all original contract fields in `/app/output/result.json` with real case_id, honest status, sources, uncertainty and change records. Preserve editable claims.json, QA findings/resolutions, RDF/JSON-LD and readable review notes as requested. Reopen JSON and exported RDF, validate artifact existence and check required coverage against task.md and the original document. Structural validity is separate from completed scientific review or claim coverage.

No official cases, prepared formal answers, fabricated figures, benchmark gains, scores or native traces are supplied. Formal comparisons are platform-run. Figure recreation is unnecessary for claim extraction alone; use actual evidence anchors/crops. If the actual task requests reproduction, use actual data/methods and retain code plus numerical comparisons, labelling missing data and approximations.

Specification references: [Nanopublication guidelines](https://nanopub.net/docs/guidelines/) and [provenance versus publication info](https://nanopub.net/docs/handbook/nanopublication/), checked 2026-11-20. Version 1.0.0; details/examples in references/formats.md and README.md.
