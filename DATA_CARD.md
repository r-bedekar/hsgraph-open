# HSGraph v0.1.0 data card

Version: v0.1.0. Metadata prepared 2026-09-20.
Dataset DOI: https://doi.org/10.5281/zenodo.22857372 (reserved before publication).
The DOI record establishes publication availability; reservation alone does not.
Owner/author: Rizwan Bedekar. Project contact:
[rbedekar@zeroinsec.com](mailto:rbedekar@zeroinsec.com), owner-selected for public
use and sensitive rights/security reports. Selected repository destination:
https://github.com/r-bedekar/hsgraph-open.
Use its issue templates for nonsensitive corrections/rights concerns once live.

**The release retains 76,211 of 76,673 primary exchange rows (99.3974%), but it
is not a fully closed, computable LCA bundle.** Row retention is not measurement
accuracy, rights certainty, classification accuracy or validated chain coverage.

## What the numbers describe

All frozen counts refer to candidate content hash
`78b9a1f0afbad1ae0b7ef81e63af5d03c49cc79eb99a09ac853840e23bdca710`.
Outer-package counts below are explicit read-only aggregates of that candidate.

| Component | Retained |
| --- | ---: |
| HS2022 identities: chapters / headings / subheadings | 96 / 1,228 / 5,612 = 6,936 |
| USLCI primary processes | 1,422 |
| Primary exchanges | 76,211 of 76,673 |
| Supporting records | 6,293 |
| Provider/gap records; traversable subset | 6,804; 3,495 |
| Flow-definition pilot / exact instances | 41 / 670 |
| Mapping revisions / projections | 88 / 670 |
| Product-identity assessments | 670 |
| Smoke-1 cases / Smoke-2 case views of the same five instances | 5 / 12 |
| Owner acceptances / specialist validations | 1 / 0 |
| Project quantity/unit-group records; nested used units | 10; 13 |
| Explicit native-to-project reference substitutions | 23 |
| D6 additions: definitions / elementary exchange rows | 1,235 / 45,015 |
| Selected USITC legal excerpts | 22 |

The frozen candidate has 32 artifacts plus its manifest, totalling 99,170 JSONL
records across its record files. The final archive adds an outer documentation
and licensing envelope; its exact byte size and checksum are in the public
release manifest, not inferred from the roughly 194 MB uncompressed payload.

## Missing information and exclusions

- Within D6, **121 definitions have multiple native physical properties**;
  the flow-specific density/heating-value and other cross-property factors are
  omitted. **783 added/retained D6 exchanges use a nonreference property**.
  Their expressed measurements remain, but conversion across properties does not.
- **208 D6-added exchanges retain unevaluated amount formulas.** A separate
  whole-candidate count finds **1,442 formula-bearing retained exchanges**.
  Neither number means a calculation engine or all parameter dependencies exist.
- **199 D6 exchanges use area × native year**. No year duration or conversion
  to seconds is invented. Hectare/m2 scaling only is supported.
- **462 primary exchanges on five unattributed definitions remain excluded**.
  **21 flow-type conflicts are a subset of those 462**, flagged, not normalized.
- **947 electricity-library processes and reference exchanges**, plus all
  matrices, remain excluded. The retained boundary record is a count-only
  statement, not 947 public graph nodes. Total exchange omissions relative to
  the 77,620-row primary-plus-library snapshot are 1,409.
- **1,258 original library supporting records** remain excluded, including the
  ten property/unit-group records replaced by project-authored records.
- Three GaBi-restricted processes and 3,699 exchanges were already excluded
  before the pinned private inventory; they are not counted again as new losses.
- Contact fields/text and operational material are filtered. WCO/UNSD-origin
  descriptive wording and pre-Smoke legal prose/conditions are omitted. Public
  mechanical outcomes therefore cannot all be independently recomputed.

Missing context is unknown, not evidence of absence. Units, formulas, uncertainty,
dates, scope and provider stops are retained where allowed; they are not repaired
through HS/name joins. Public package inspection does not establish LCA closure.

## Evidence, assessment and review

Keep product identity, HS mapping, production relationships, provider-model
adequacy and human acceptance separate. Mechanical applicability is a saved
predicate outcome; automated support is an interpretation of cited source
material within an exact claim scope. Neither is independently verified
manufacturing truth. Evidence hash/citation matching does not prove semantic
support. Assessor/challenger agreement is not expert validation or a vote.

The **one owner acceptance** applies only to the cement exchange
`uslci-1.2026-06.0:processes:62993671-574c-3fc5-b66a-6be3bb21ad3d:exchange:66`,
HS4 2523, original mapping `pilot-cement-r3`, dated 2026-09-13. It does not
accept sibling instances, a rebased claim identity, its production chain, HS6,
suppliers or compatibility. Some saved projection labels inherit an accepted
definition revision; they are not additional human decisions. The reader checks
the exact owner-decision binding rather than counting those labels as acceptance.

Smoke-1 and Smoke-2 are development material, not independent benchmarks.
The 670 product-identity outcomes are 608 automated supported, 43 automated
conditional and 19 disputed (zero insufficient evidence). Their separate
mechanical outcomes are 396 applicable, 161 insufficient information, 80
ambiguous and 33 conflicting. Smoke-1's raw assessor outcomes are three supported,
one conditional and one competing targets; Smoke-2's are two supported, two
conditional, four competing targets and four insufficient information. These
are saved labels, not measured accuracy or independent-product sample counts.
Smoke-1's glycol case classified the proxy instead of the represented product;
its saved supported outcome remains visible with that warning. Its quicklime
disagreement and Smoke-2's S2-03 composition concern remain unresolved. Omitted
evidence, alternate claim objects and deliberately restricted experiment scopes
remain labelled. No accuracy, calibrated-confidence or specialist-equivalence
claim is made. Automated results can be inspected without human acceptance.

## Sources and release decisions

USLCI release 1.2026-06.0 and its separately scoped electricity library provide
historical source-declared inventory data, not actual current supplier facts.
Public numeric HS identity is a new USITC 2022 HTSA Basic-derived snapshot with
the retained reconciliation dependency disclosed. Original UNSD-bound mapping
and assessment identities are not relabelled; cross-references do not rebind them.
Legal excerpts are independently acquired USITC HTS2022 files, not WCO extracts.
Exact locators, hashes and source dates are retained in package records.

New D1–D6 owner readings authorize specified derivatives, not blanket third-party
clearance. See `candidate/source-use-decisions.json`, original record rights,
all five source notices and `LICENSE-DATA`. Territorial limitations, reliance on
native FEDEFL attribution and uninspected upstream chemical-database rights are
not relabelled as resolved. Public takedown practice is not a redistribution basis
and cannot recall downstream copies. No source institution endorses the release.

## Intended use and limits

Use for evidence inspection, exact scoped mapping exploration and traversal of
explicit modeled defaults with gaps visible. Do not use it as a customs ruling,
complete BOM, verified supplier directory, procurement guarantee, engineering
recipe or localization/investment decision. No LCA characterization is supplied.

Package hashes and public software/tests are independently usable offline.
Source reconstruction needs exact independently acquired inputs. Original
private model-response replay is unavailable publicly; fresh model generations
are nondeterministic and unnecessary. See docs/REPRODUCIBILITY.md.

Preparation and publication are separate: final metadata/content validation,
actual off-machine recovery and owner approval are prerequisites to publication.
Nested candidate documents are preserved historical metadata; their earlier
version and recovery language does not supersede this outer v0.1.0 card.
The frozen private regression result is 258 passing tests;
public-reader testing is a separate software check, not an accuracy measure.
