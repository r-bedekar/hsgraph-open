# HSGraph: a map of how products connect

Discussion sample 5 (guided production journey), derived from published v0.1.0.
Prepared for Rizwan Bedekar / HSGraph on 2026-10-01. Materials and products
connect through documented processes. HS classifications form a separate layer.
The website and Excel are reading views of that graph. The ten original
classification rows and their evidence are unchanged. This is not a new release
of the underlying classification dataset.
Source release: https://doi.org/10.5281/zenodo.22857372
Code: https://github.com/r-bedekar/hsgraph-open/tree/v0.1.0
Contact: rbedekar@zeroinsec.com

## Start here

Unzip into a new folder and open index.html (or START_HERE.html) in a browser. No server,
installation, AI account or network connection is needed. The table has exactly
10 distinct exchange instances from 10 flow definitions; they are not 10 verified
HS classifications. samples.csv is for spreadsheet inspection; samples.json is
the structured summary. Each row links to its underlying evidence JSON.
Follow four short steps: understand the map, follow a chain, inspect the HS
link, then use the data. Each step has a next/previous link; the top navigation
lets readers jump to a step. Deep links to the original ten records still work.
The graph fits the screen without an inner scroll box. It starts with up to
three inputs and two outputs on desktop, one of each on narrow screens. Clear
counts and expansion buttons expose every retained input/output on request.
The ten original example records can be selected one at a time; full evidence
remains available in expandable details. Without JavaScript all four steps and
all ten records remain readable as a normal document.

Start with the interactive production diagram, or open production-graph.xlsx.
Select stretch film, Portland cement or aluminium casting. Select a product to
inspect its proposed codes; select a linked process to explore its inputs. The
detail panel also lists included downstream uses of an exact output. JavaScript
enables graph interaction; a text branch and the complete JSON remain available
without it. The font and all scripts are local. No network requests are needed.

The graph selects these three roots plus their direct explicit providers and
direct consumers. All direct product, service and waste exchanges for those
processes are retained. Environmental exchanges are counted separately. This is
a bounded sample, not the whole production graph. A missing link stays unknown.
HS-code matches never create links. Default providers describe inventory models,
not actual suppliers, and the models can cover different historical periods.
Quantities and formulas are preserved in the evidence, not multiplied along paths.
The film model's description and waste record disagree on the disposal route;
their original wording is retained rather than silently reconciled.

production-graph.json is the structured view. production-evidence.json contains
unchanged source records and line hashes used to build it. The workbook includes
the diagram, links, processes, products, original ten cases, references and notices.
No HS catalogue wording is added to this public package. The separately generated
local review workbook can include wording from a pinned local catalogue.

Follow the short guide, inspect one case, and use the feedback template.
You are being asked about usefulness and clarity, not to certify an HS code.
The steel evidence diagram shows recorded proposal relationships, not material
flows or verified supply-chain connections. No form collects or sends data.

## What this tests

Could this help someone inspect a proposed USLCI-to-HS relationship, understand
the saved evidence and identify what remains to be established? It does not
decide the classification for them. Start with R01 (steel): the saved case has
competing headings and missing width. Compare R02 (one exact owner decision)
and R05 (a recorded proxy/product failure). A saved 'supported' label is an
automated outcome, not our assurance that the classification is correct.

Please tell us: (1) what task you would use this for; (2) what you would otherwise
look up; (3) what is missing or misleading; (4) whether it is useful without
validated classifications. Feedback is not treated as expert approval. Do not
send confidential product information without agreeing a private route first.

## Selection and interpretation

Purposive, not random or representative: the five original Smoke-1 instances,
followed by one instance for each of aluminium, ABS, fertilizer mixture,
concrete and sodium hydroxide. For those five, the lexicographically first
exchange ID in the specified published mapping revision is selected. Selection
is fixed by the pinned source ZIP; no new classification reasoning is generated.

All 17 saved smoke case views are attached to their five corresponding rows,
not counted as additional products. Smoke-2 experimental evidence omissions,
claim objects, assessor/challenger findings and post-run concerns remain intact.
The other five rows have product-identity assessments and mechanical projections,
but no Smoke HS assessment for that exact instance. Product identity is not HS
support. Missing public condition text is not reconstructed from private files.

One exact cement-instance OWNER acceptance is shown separately; there are zero
specialist validations. That decision does not accept siblings, a rebased claim,
Smoke-2 views, production chains, suppliers, compatibility or HS6. Historical
'classified' or 'accepted' labels within source records do not override this.
Targets and alternatives are retained as candidates with their source role.
Nothing here is a customs ruling, complete LCA, verified BOM or supplier claim.

## Evidence and provenance

evidence/R01.json through R10.json contain unchanged parsed records selected
from the published exchange, process, flow-definition, mapping revision,
projection, product-identity, smoke and owner-decision files. Each record has
its original JSONL filename, one-based line number and SHA-256 of the original
line INCLUDING its newline. JSON whitespace in these wrapper files is new;
the record objects, original derivative seals and original bindings are retained.
The selected rows include their declared flow definitions, not the full graph.

This is NOT a closed graph package. Provider references, revision ancestors,
catalogue entries and other unselected IDs must be looked up in the full source
release. Private evidence/response hashes are locators, not included payloads or
a claim that model runs can be replayed. Legal excerpts and source decisions
are retained under candidate/. Citation matching is not semantic verification.

candidate/manifest.json, candidate/MODIFICATIONS.md and candidate/EXCLUSIONS.*
are unchanged FULL SOURCE RELEASE records, not manifests/counts for this subset.
Use sample-manifest.json for this sample's inventory. Historical candidate
metadata does not describe current publication or recovery status.

## Modifications and licensing

New work consists of selection, record wrappers, graph projection and HTML/Excel/CSV
presentation. No source facts, mechanical predicates, assessment outcomes,
decisions or original release bytes were changed; no models were run. All
missing-fact text displayed from a model is attributed to that saved model pass.
Empty fact lists mean 'none listed in that record', NOT 'all facts established'.

Keep this whole package together when sharing. LICENSE-DATA and all five source
notices accompany it, including the entire NOTICE-USLCI. Original project
annotations/documentation: CC BY 4.0 only to the extent rights are held. Imported
content retains its component terms. Original software: Apache-2.0. Credit
Rizwan Bedekar / HSGraph and DOE / NREL / Alliance for Sustainable Energy,
USLCI contributors, USITC, EPA/FEDEFL, NIST and BIPM as applicable. No endorsement
or new source-rights clearance is implied. See candidate/source-use-decisions.json.
Manrope font: SIL Open Font License 1.1, retained in assets/OFL-Manrope.txt.

## Verification / reproduction (optional, Python 3.10+)

From the unpacked sample directory:

    python3 tools/verify_review_sample.py .

To additionally compare every embedded source record with the original release:

    python3 tools/verify_review_sample.py . --source-zip /path/to/hsgraph-v0.1.0-dataset.zip

To rebuild this sample into a NEW destination:

    python3 tools/build_review_sample.py --source-zip /path/to/hsgraph-v0.1.0-dataset.zip --output /path/to/new-sample

On Windows, use `py -3` instead of `python3`. Nothing downloads automatically.
The source ZIP hash is pinned in the tools. The adjacent ZIP checksum protects
transport bytes; internal hashes check consistency, not scientific truth or
authenticity against a malicious replacement of both data and checksum.
