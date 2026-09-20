# Package and reader format

The ZIP has an outer release envelope and an unchanged `candidate/` directory.
The outer manifest identifies every file's bytes and hash; SHA256SUMS additionally
binds that manifest. The ZIP byte hash lives outside the archive in the public
release manifest. The frozen candidate's own manifest and row hashes remain
unchanged. Candidate, archive and repository hashes identify different objects.

JSON canonicalization is sorted keys, compact separators, UTF-8, no NaN. Each
content hash excludes its own hash field. Legal-passage hashes bind canonical
JSON strings, not raw string bytes. SHA-256 of files binds actual bytes.
`derivative_sha256` identifies the filtered public record;
`private_original_sha256` identifies unavailable private content and is not its
public counterpart. It cannot be used to reconstruct omitted evidence.

The SQLite index stores each published JSONL row without rewriting claim content.
Indexed artifact, instance, process, code and case columns only aid retrieval.
Its content digest binds all stored payload rows in artifact/ordinal order;
byte-identical SQLite files across SQLite versions are not promised. Verification
checks package bytes, row seals, retained graph references and legal bindings,
not scientific correctness or a signature. Citation locators to absent private
evidence are explicitly not treated as supplied text.

Use `record --store STORE ARTIFACT RECORD_ID` to retrieve any indexed row,
including source excerpts, mapping revisions and reference substitutions.
`instance` shows the source exchange/process, saved mechanical projections,
product-identity assessments, both HS experiment layers and exact owner binding.
`case` keeps that experiment's mechanical scope and supplied evidence distinct.
`hs` is exact-code display, not a new classification algorithm. `trace` follows
saved traversable model defaults only; stop reasons and cycles remain visible.

No automatic provider joins, predicate recomputation, missing-property inference,
assessment ranking, HS4 expansion or human acceptance is implemented. Unknown
targets remain unknown. Original catalogue identity bindings remain separate from
the new numeric catalogue's public cross-references. Project measurement units
do not provide missing density/heating-value conversions.
