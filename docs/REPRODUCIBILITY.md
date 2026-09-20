# Reproduction: five separate meanings

1. **Public package verification:** verify the ZIP against the separately
   distributed SHA-256, then verify envelope, frozen manifest, artifact hashes,
   row seals and retained references. This checks identity/integrity, not truth.
2. **Public software/tests:** Python 3.10+ standard library suffices. Synthetic
   tests, public JSONL indexing and documented queries require no private files,
   model account, network service or AI agent. Repeated indexing gives the same
   logical payload digest. Source-record ordering and IDs are preserved.
3. **Source rebuild:** requires independently obtained exact historical USLCI,
   catalogue and legal inputs, their terms/pins and the applicable transformation
   configuration. This minimal public reader is not the complete private research
   pipeline. Full source reconstruction is not claimed from this package alone;
   mutable/versioned upstream URLs may no longer return the historical bytes.
4. **Private model-response replay:** original response bodies, prompts and
   operational events are withheld. External original-run replay is unavailable.
   Parsed public assessment records and hashes do not remove this limitation.
5. **Fresh model generation:** nondeterministic; not performed by this reader
   and not required to use or test HSGraph. Never label it deterministic replay.

There is no fresh human review or independent benchmark implied by these checks.
The release keeps its development failures, concerns and historical states.
Package correction, if necessary, requires a new outer hash or separately
documented derivative; do not silently replace the frozen candidate or move a
published tag. DOI metadata will be finalized only after an actual reservation
and before the final immutable release tag.
