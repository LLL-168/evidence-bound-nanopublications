# Internal JSON interface

This schema is a runtime ledger; preserve the original case output_contract independently. The example is synthetic interface documentation only, not an official case answer.

```json
{
  "case_id": "illustrative-only",
  "publication": {"creator": "actual extractor identity or truthful agent description", "created_at": "actual timezone-aware ISO-8601 creation time"},
  "documents": [{
    "id": "d1", "path": "/input/actual-paper.pdf", "sha256": "actual 64-character file SHA-256",
    "title": "Actual title", "authors": [], "year": null, "version": null, "identifier": null,
    "metadata_missing": {"authors": "Not recoverable in supplied material", "year": "Not shown", "version": "Not identified"}
  }],
  "blocks": [{"id": "b1", "document_id": "d1", "text": "Synthetic source: A was associated with B in cohort P.", "locator": {"page": 1, "paragraph": 1}}],
  "claims": [{
    "id": "c1", "document_id": "d1", "text": "A was associated with B in cohort P.",
    "subject": {"label": "A"}, "relation": "associated_with", "object": {"label": "B"},
    "polarity": "affirmed", "modality": "observed", "conditions": ["cohort P"],
    "origin": "reported", "status": "supported",
    "confidence": {"level": "medium", "basis": "Direct wording and cohort scope checked; identity remains local."},
    "evidence": [{"block_id": "b1", "quote": "A was associated with B in cohort P", "support": "direct"}]
  }],
  "uncertainties": [], "changes": []
}
```

Compute actual hash and timestamp; the explanatory strings above are not valid runtime values. Document `title` is nonempty; `authors` is a list of actual names, `year` is a positive integer or null, `version`/`identifier` are known strings or null. Unknown authors/year/version need reasons in metadata_missing. Keep paper creators separate from the nanopublication extractor. Preserve DOI/URL/source version and additional metadata if known; do not invent identifiers.

Blocks need exact text and a document reference; locators include a positive 1-based PDF page or plain-text paragraph/offsets/fragments. Add original section, bbox, figure/panel/table/cell/equation fields as appropriate. Multiple blocks may jointly support a claim; evidence may come from another document, but that must be reviewed explicitly. Each quote must occur in its own block after whitespace normalization.

Claim statuses: supported, uncertain, unsupported, conflicted. Non-supported candidates require `reason` and remain in JSON/manifest; they are excluded from RDF export. They may lack evidence if none is available, but this is a partial result. Supported claims need one or more evidence items with `support` direct or indirect. Claim origins: reported, author_interpretation, inference. Inferences need `inference_basis`; the helper flags them for review. Conditions is a list of nonempty strings (including an explicit source-not-reported/not-applicable explanation if appropriate). Confidence levels high/medium/low/undetermined need an actual basis, not a made-up probability.

Subject/object use a nonempty label and optional actual verified absolute `iri`; otherwise the exporter mints a local claim-scoped URI for the subject and uses a literal for the object. Polarity and modality are required. Relation keys come from resources/relations.json, whose URIs are explicitly local. Any stronger external ontology mapping needs independent evidence and is not silently inferred.

One four-graph nanopublication is exported per supported claim. It represents a qualified RDF statement without adding the unqualified underlying S–P–O triple. The provenance graph retains source title/authors/year/version/identifier/hash, evidence quote/locator and support classification. Publication info retains actual extractor/time. No source author is falsely represented as creator of this extraction.

Commands:

```bash
python /skills/weekly-skill/scripts/nanopub_guard.py check --input /app/work/claims.json --out /app/output/qa.json
python /skills/weekly-skill/scripts/nanopub_guard.py export --input /app/work/claims.json --out /app/output/nanopublications
python /skills/weekly-skill/scripts/nanopub_guard.py validate-rdf --input /app/output/nanopublications.trig --out /app/output/rdf-qa.json
```

Check exit 0: structurally valid with all candidates supported (semantic review may remain). Exit 1: invalid or partial candidate status. Exit 2: malformed files/dependency/runtime error. Export allows explicit partial input while retaining excluded IDs/reasons; broken references/quotes/schema are refused. It emits .trig, .jsonld, .md and .manifest.json. Both RDF serializations are independently parsed and their quad sets compared. validate-rdf checks basic four-graph guideline invariants, not signatures, Trusty URIs, ontology correctness or scientific validity. Input/outputs are local; no network calls or public publication occur.
