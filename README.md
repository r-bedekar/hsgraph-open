# HSGraph v0.1.0

HSGraph connects HS classification identities to documented product/process
instances and their explicitly recorded inventory dependencies. It helps you
inspect the evidence, see saved automated findings and find where support stops.

Version **v0.1.0** contains 6,936 HS2022 identities, 1,422
USLCI processes, 76,211 primary exchanges, 670 product-identity assessments,
670 mapping projections and two small HS-mapping development experiments.
One exact cement-instance mapping has owner acceptance; none has specialist
validation. Evidence, automated assessment and human review are separate.

**No AI agent, model service, API key or private database is required to use,
query or test this release.** Python 3.10+ and its standard library suffice.
Retaining 99.3974% of primary exchange rows **does not make this a fully closed,
computable LCA bundle**. See [DATA_CARD.md](DATA_CARD.md) for missing factors,
unevaluated formulas, exclusions and known assessment failures.

## Status and obtaining the package

Repository destination: https://github.com/r-bedekar/hsgraph-open.
Dataset DOI: https://doi.org/10.5281/zenodo.22857372.
Project contact: rbedekar@zeroinsec.com.

The DOI was reserved before publication. Reservation alone does not make the
record or repository public; check the destinations for actual availability.
After publication, obtain `hsgraph-v0.1.0-dataset.zip` from the DOI's Zenodo record.
Before publication, use only the separately supplied release-review package.
Preparation status in the manifest records the build checkpoint, not live
publication status. No published tag or release date is inferred from that status.

After obtaining this repository checkout and the separately supplied
`hsgraph-v0.1.0-dataset.zip`, place the ZIP in `work/`. The ZIP is not stored
in Git. `release-manifest.json` and `SHA256SUMS` give its exact byte size/hash,
the frozen candidate content hash and the outer-envelope hash. These hashes
identify different objects; none establishes scientific truth or legal clearance.
The nested `candidate/` documents retain their historical version and recovery
wording unchanged. Outer v0.1.0 metadata governs this release; the inner documents
are not a current publication or recovery-status declaration.

## Offline setup and verification

Run from this checkout; no installation or dependency download is required.

```sh
python3 --version
python3 -m unittest discover -s tests -v
python3 -c "import json,subprocess,sys; m=json.load(open('release-manifest.json')); subprocess.run([sys.executable,'hsgraph_release.py','unpack','work/'+m['package_filename'],'work/package','--sha256',m['package_sha256']],check=True)"
python3 hsgraph_release.py verify work/package
python3 hsgraph_release.py load work/package --store work/hsgraph.sqlite
python3 hsgraph_release.py verify-store --store work/hsgraph.sqlite
```

Extraction and loading refuse to overwrite existing destinations. For another
run, choose fresh paths. The SQLite file is a disposable deterministic index of
published JSONL—not a reconstruction of the internal research databases.

## Three retained examples

These display **actual saved case records**, including the assessor, challenger,
citations, uncertainty, original scope/hash and separate owner binding. They do
not generate new answers or require human acceptance to view automated work.

```sh
python3 hsgraph_release.py case --store work/hsgraph.sqlite smoke1 cement
python3 hsgraph_release.py case --store work/hsgraph.sqlite smoke1 stainless-steel-coil
python3 hsgraph_release.py case --store work/hsgraph.sqlite smoke1 lldpe
```

- Cement: recorded mechanical `applicable`, automated HS4 **2523 supported**,
  with the one exact owner acceptance shown separately. No chain acceptance.
- Stainless-steel coil: mechanical `ambiguous`, automated `competing_targets`;
  width is missing for selecting **7219 versus 7220**.
- LLDPE: mechanical `applicable`, automated HS4 **3901 supported**. This is not
  an HS6 conclusion; finer classification and any missing facts stay in the record.

Do not interpret assessment agreement as correctness. Smoke-1's glycol proxy
scope failure, quicklime disagreement and Smoke-2's S2-03 concern remain visible.

## Browse mappings and explicit dependencies

```sh
python3 hsgraph_release.py hs --store work/hsgraph.sqlite 2523
python3 hsgraph_release.py hs --store work/hsgraph.sqlite 2523 --mode owner
python3 hsgraph_release.py hs --store work/hsgraph.sqlite 3901 --mode automated
python3 hsgraph_release.py trace --store work/hsgraph.sqlite uslci-1.2026-06.0:processes:62993671-574c-3fc5-b66a-6be3bb21ad3d --depth 2
```

The default is specialist-only and returns no validated mappings in v0.1.0.
Owner mode checks exact decision bindings. Automated mode lists retained HS
assessment cases, including concerns—not product-identity findings promoted to
classification support. Exploratory mode also displays saved mapping projections.
Codes are exact: an HS4 query does not classify its HS6 children. The original
claim catalogue identities remain unchanged alongside public cross-references.

Traversal follows only existing `traversable` provider links, retaining stop
reasons, cycles and gaps. Starting-mapping support is **not** evidence for
downstream relationships. Providers are model defaults, not verified suppliers.
No quantities, formulas, compatibility or local manufacturing capability are
calculated. Use `instance`, `record` and `--help` for exact record inspection.

## Provenance, licensing and concerns

Read [FORMAT.md](docs/FORMAT.md), [reproduction limits](docs/REPRODUCIBILITY.md),
[LICENSE-DATA](LICENSE-DATA) and the package's complete source notices. Original
code is Apache-2.0; original annotations are CC BY 4.0 only to the extent rights
are held. Third-party terms remain separate. Credits: DOE / NREL / Alliance
for Sustainable Energy; USLCI contributors; USITC; EPA/FEDEFL; NIST; BIPM.
No endorsement is implied.

Project contact: [rbedekar@zeroinsec.com](mailto:rbedekar@zeroinsec.com), selected
by the owner for public use. Once the repository is published, use its Rights/Data
Concern and Correction issue templates for nonsensitive reports. Send sensitive
rights/security concerns to the email address, not public issues.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
