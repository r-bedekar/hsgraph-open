#!/usr/bin/env python3
"""Build production graph and classification reading views from the published ZIP."""
import argparse
from collections import Counter
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True

try:
    from .production_graph import select_records, project_graph, graph_section
    from .production_workbook import workbook_bytes
    from .journey_view import render_journey
except ImportError:
    from production_graph import select_records, project_graph, graph_section
    from production_workbook import workbook_bytes
    from journey_view import render_journey

SOURCE_SHA = 'f73a7d457ef69be4848e0d169bafc157d0faa3b15b3b56eac43d6fdc17a38803'
INNER_SHA = '78b9a1f0afbad1ae0b7ef81e63af5d03c49cc79eb99a09ac853840e23bdca710'
DOI = 'https://doi.org/10.5281/zenodo.22857372'
SMOKE_CASES = ('stainless-steel-coil', 'cement', 'lldpe', 'quicklime', 'ethylene-glycol-proxy')
EXTRA_MAPPINGS = ('pilot-aluminium-r3', 'pilot-abs-r3', 'pilot-fertilizer_mix-r2',
                  'pilot-concrete-r2', 'pilot-caustic-r2')
COPIED = ('LICENSE', 'LICENSE-DATA', 'candidate/NOTICE-USLCI', 'candidate/NOTICE-CC0',
          'candidate/NOTICE-FEDEFL', 'candidate/NOTICE-OGL-CANADA',
          'candidate/NOTICE-REFERENCE-STANDARDS', 'candidate/source-use-decisions.json',
          'candidate/DATA-LICENSE.txt', 'candidate/EXCLUSIONS.json',
          'candidate/EXCLUSIONS.md', 'candidate/MODIFICATIONS.md',
          'candidate/manifest.json', 'candidate/usitc-legal-excerpts.jsonl')

README = '''# HSGraph: a map of how products connect

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
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def archive_path(output):
    return Path(str(output) + '.zip')


def load_records(bundle, filename):
    return [{'source_artifact': filename, 'source_line': i,
             'source_line_sha256': digest(line), 'record': json.loads(line)}
            for i, line in enumerate(bundle.read('candidate/' + filename).splitlines(keepends=True), 1)]


def review_state(decisions, instance, mapping, target):
    return 'owner_accepted_exact_original_binding' if any(
        d['decision'] == 'accept' and instance in d['binding']['exchange_ids']
        and d['mapping_id'] == mapping and d['target_code'] == target.get('code')
        and d['target_edition'] == target.get('edition') for d in decisions
    ) else 'no_owner_acceptance'


def row_summary(number, records):
    def of(name):
        return [x['record'] for x in records if x['source_artifact'] == name + '.jsonl']
    exchange, projection, revision, identity = (of(name)[0] for name in
        ('exchanges', 'mapping-projections', 'mapping-revisions', 'identity-assessments'))
    target = projection.get('target') or {}
    smoke = [(name, r) for name in ('smoke1', 'smoke2') for r in of(name)]
    accepted = [d for d in of('owner-decisions') if d['decision'] == 'accept'
                and exchange['id'] in d['binding']['exchange_ids']]
    owner = ('owner_accepted_original_revision_only: ' + '; '.join(d['mapping_id'] for d in accepted)
             + '; not acceptance of rebased identities, smoke views or chains') if accepted else 'no_owner_acceptance'
    saved_cases, facts, concerns = [], [], []
    for suite, r in smoke:
        a, c = r['assessor'], r['challenger']
        saved_cases.append(f"{suite}/{r['case_id']}: assessor={a.get('outcome', a.get('hs_resolution'))}; "
                           f"challenger={c.get('recommended_outcome', c.get('recommended_hs_resolution', 'see evidence'))}")
        for role, actor in (('assessor', a), ('challenger', c)):
            for key in ('missing_facts', 'additional_missing_facts'):
                for fact in actor.get(key, []):
                    text = (fact.get('fact', json.dumps(fact)) + ' Effect: ' + fact.get('effect', 'not separately stated')) if isinstance(fact, dict) else str(fact)
                    facts.append(f"{suite}/{r['case_id']} {role}: " + text)
        concerns.extend(f"{suite}/{r['case_id']}: {x}" for x in r.get('post_run_concerns', []))
    if not smoke:
        facts.append('Public pre-Smoke condition/rationale text withheld; no missing-fact explanation reconstructed. See retained identity assumptions and withheld-material fields.')
    return {
        'row_id': f'R{number:02}', 'source_declared_product': exchange['native']['flow']['name'],
        'instance_id': exchange['id'], 'source_locator': exchange['locator'],
        'mapping_revision_id': projection['mapping_id'],
        'saved_projection_target': target.get('code', 'none'),
        'saved_revision_alternatives': '; '.join(t['code'] for t in revision.get('alternatives', [])) or 'none listed',
        'mechanical_outcome': projection['mechanical_outcome'],
        'product_identity_outcome_NOT_HS': identity['automated_outcome'],
        'saved_HS_case_outcomes_NOT_validation': ' | '.join(saved_cases) or 'No saved Smoke HS assessment for this instance',
        'owner_review': owner,
        'displayed_projection_owner_review': review_state(of('owner-decisions'), exchange['id'], projection['mapping_id'], target),
        'specialist_validation': 'none',
        'recorded_missing_facts': ' | '.join(dict.fromkeys(facts)) or 'None listed in saved cases; not proof of complete information',
        'post_run_concerns': ' | '.join(concerns) or 'None recorded here; not proof of correctness',
        'evidence_file': f'evidence/R{number:02}.json',
        'use_limit': 'Evidence inspection only; not a verified classification, customs ruling or complete LCA',
    }


def csv_cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


_STYLE = '''/* Layout: one reading column (prose max 72ch); the example figure, the layer grid and the table may widen to 1080px.
   Sections are separated by space and small uppercase eyebrows; only status chips, the two figures and the ask box are styled as objects. */
:root{color-scheme:light;
--bg:#f3f5f8;--surface:#ffffff;--surface-2:#e9edf3;--ink:#1a2230;--ink-2:#4d5768;--line:#d2d8e2;
--accent:#1d4f91;--accent-ink:#ffffff;
--pass:#1b6f47;--pass-bg:#e0f2e8;--multi:#54489e;--multi-bg:#eae7f7;--gap:#8a5600;--gap-bg:#fbefd3;--conflict:#ab2118;--conflict-bg:#fbe6e3;
--font-display:"Iowan Old Style","Palatino Linotype",Palatino,Charter,Georgia,"Times New Roman",serif;
--font-body:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
--font-mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#12161d;--surface:#1a2029;--surface-2:#242c38;--ink:#e6e9ee;--ink-2:#a4adbc;--line:#333c4a;--accent:#8fb7f1;--accent-ink:#0e1a2c;--pass:#6fc796;--pass-bg:#173525;--multi:#b3a4f2;--multi-bg:#2a2649;--gap:#e8b94f;--gap-bg:#3a2e12;--conflict:#f08c82;--conflict-bg:#43201d}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#12161d;--surface:#1a2029;--surface-2:#242c38;--ink:#e6e9ee;--ink-2:#a4adbc;--line:#333c4a;--accent:#8fb7f1;--accent-ink:#0e1a2c;--pass:#6fc796;--pass-bg:#173525;--multi:#b3a4f2;--multi-bg:#2a2649;--gap:#e8b94f;--gap-bg:#3a2e12;--conflict:#f08c82;--conflict-bg:#43201d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 var(--font-body)}
.wrap{max-width:1080px;margin:0 auto;padding:0 clamp(16px,4vw,40px) 56px}
h1,h2,h3{font-family:var(--font-display);font-weight:600;line-height:1.15;text-wrap:balance;margin:0 0 .5em}
h1{font-size:clamp(2.1rem,4.6vw,3.2rem);max-width:20ch}
h2{font-size:clamp(1.55rem,2.8vw,2.05rem)}
h3{font-size:1.3rem}
p,li,dd,dt{max-width:72ch}
a{color:var(--accent)}
a:focus-visible,summary:focus-visible,textarea:focus-visible,.scroll:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.eyebrow{font-size:.8rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-2);font-weight:600;margin:0 0 .6em}
header{padding-block:40px 8px}
.lede{font-size:1.15rem;max-width:64ch}
.ask{border-left:4px solid var(--accent);background:var(--surface);padding:14px 20px;margin:24px 0;max-width:72ch}
.ask p{margin:0}
nav.top{display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center;margin:26px 0 10px}
.button{display:inline-block;background:var(--accent);color:var(--accent-ink);padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:600}
.terms{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px 40px;margin:18px 0 0}
.terms p{margin:0;font-size:.98rem;color:var(--ink-2)}
.terms b{color:var(--ink)}
section{border-top:1px solid var(--line);padding-block:40px;scroll-margin-top:16px}
section.case{border-top:1px dashed var(--line);padding-block:28px}
section.case:target{background:var(--surface);box-shadow:0 0 0 12px var(--surface)}
ol.steps{padding-left:1.3em}ol.steps li{margin-bottom:.5em}
.muted{color:var(--ink-2)}
small{font-size:.86rem}
.chip{display:inline-block;padding:2px 11px;border-radius:999px;font-size:.86rem;font-weight:650;line-height:1.5;border:1px solid transparent}
td .chip{white-space:nowrap}
.chip.pass{color:var(--pass);background:var(--pass-bg)}
.chip.multi{color:var(--multi);background:var(--multi-bg)}
.chip.gap{color:var(--gap);background:var(--gap-bg)}
.chip.conflict{color:var(--conflict);background:var(--conflict-bg)}
.chip.plain{color:var(--ink-2);background:var(--surface-2)}
.chip.other{color:var(--ink);background:var(--surface-2);border-color:var(--line)}
figure{margin:24px 0}
figcaption{margin-top:14px;color:var(--ink-2);font-size:.95rem;max-width:72ch}
.flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:10px;align-items:stretch}
.node{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;min-width:0}
.node .k{font-size:.76rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);font-weight:650}
.node .v{font-weight:650;line-height:1.35}
.node .d{font-size:.92rem;color:var(--ink-2);line-height:1.45}
.node.result{border-color:var(--accent);border-width:2px}
.node a{overflow-wrap:anywhere;font-size:.92rem}
.arrow{align-self:center;color:var(--ink-2);font-size:1.6rem;line-height:1;padding:0 2px}
.codes{display:grid;gap:6px;margin:2px 0}
.codes span{display:flex;gap:10px;align-items:baseline;font-size:.95rem}
.codes b{font-family:var(--font-mono);font-size:1.05rem;font-variant-numeric:tabular-nums}
.layers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:22px 0}
.layer{border-top:3px solid var(--accent);padding-top:12px;min-width:0;display:flex;flex-direction:column}
.layer .ex{margin-top:auto}
.layer h3{font-size:1.1rem;margin:0 0 .4em;font-family:var(--font-body);font-weight:700}
.layer p{font-size:.95rem;margin:0 0 .6em;color:var(--ink-2)}
.layer .ex{font-size:.9rem;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:8px 10px}
.layer .ex .k{display:block;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);font-weight:650;margin-bottom:2px}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px 24px;margin:16px 0 0;padding:0;list-style:none}
.legend li{display:flex;flex-direction:column;align-items:flex-start;gap:6px;max-width:none;font-size:.95rem}
.legend .n{color:var(--ink-2);font-size:.86rem}
.scroll{overflow-x:auto;margin:16px 0}
table{border-collapse:collapse;width:100%;font-size:.95rem;min-width:760px}
caption{text-align:left;caption-side:bottom;padding-top:10px;color:var(--ink-2);font-size:.9rem}
th,td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}
thead th{font-size:.78rem;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-2);font-weight:650;border-bottom:2px solid var(--line)}
tbody th{font-weight:650;white-space:nowrap}
td.code{font-family:var(--font-mono);font-variant-numeric:tabular-nums;white-space:nowrap}
td.short{color:var(--ink-2)}
.case-head{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:0 0 10px}
.case-head h3{margin:0;font-size:1.35rem}
details{margin:12px 0;border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:0 16px}
details[open]{padding-bottom:10px}
summary{font-weight:650;cursor:pointer;padding:10px 0}
ul.facts{padding-left:1.2em;margin:6px 0}ul.facts li{margin-bottom:10px;max-width:80ch}
.who{display:inline-block;font-family:var(--font-mono);font-size:.78rem;color:var(--ink-2);background:var(--surface-2);border-radius:4px;padding:0 6px;margin-right:6px;vertical-align:middle}
.effect{color:var(--ink-2)}
dl.tech{margin:0 0 6px}dl.tech dt{font-weight:650;margin-top:10px;font-size:.9rem}dl.tech dd{margin:2px 0 0;font-family:var(--font-mono);font-size:.84rem;overflow-wrap:anywhere;white-space:pre-wrap;max-width:none}
.links{font-size:.95rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:20px 0;padding:0;list-style:none}
.stats li{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;max-width:none}
.stats b{display:block;font-family:var(--font-display);font-size:1.9rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}
.stats span{font-size:.9rem;color:var(--ink-2)}
ul.limits{padding-left:1.2em}ul.limits li{margin-bottom:.4em}
textarea{box-sizing:border-box;width:100%;max-width:72ch;min-height:200px;padding:14px;font:15px/1.6 var(--font-mono);color:var(--ink);border:1px solid var(--line);border-radius:6px;background:var(--surface)}
footer{padding:22px 0;font-size:.86rem;color:var(--ink-2);border-top:1px solid var(--line)}
@media (max-width:820px){.layers{grid-template-columns:1fr 1fr}}
@media (max-width:900px){.flow{grid-template-columns:1fr}.arrow{transform:rotate(90deg);justify-self:center;padding:0}}
@media (max-width:720px){.layers{grid-template-columns:1fr}section{padding-block:30px}h1{max-width:none}.scroll{overflow:visible}table{min-width:0;display:block}thead{display:none}tbody,tr,th,td{display:block}tr{border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:10px 14px;margin-bottom:12px}th,td{border:0;padding:3px 0}tbody th{font-size:1.05rem;padding-bottom:0}td.code{white-space:normal}td .chip{white-space:normal}td::before{content:attr(data-label);display:block;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-2);font-weight:650;margin-top:8px}caption{display:block;width:auto;padding:0 0 10px}}
'''


def render_html(rows, graph=None):
    esc = lambda x: html.escape(str(x), quote=True)
    status = {
        'ambiguous': ('More than one candidate', 'multi', 'The saved rules leave two or more codes possible; no single code is established.'),
        'applicable': ('Recorded conditions pass', 'pass', 'The saved rule checks pass for the proposed code. This is not specialist validation.'),
        'insufficient_information': ('Information missing', 'gap', 'The record lacks facts the saved checks need to settle the proposal.'),
        'conflicting': ('Recorded conflict', 'conflict', 'The saved checks flag a conflict. Do not treat the proposed code as settled.'),
    }
    # Plain-language notes are keyed by the saved mapping revision, not the row number, so they stay attached to the record they describe.
    # Every statement below restates a saved finding in the row's evidence file; none adds a classification.
    notes = {
        'pilot-steel_coil-r2': (
            'Width not recorded; 7219 or 7220 both possible',
            'The source names the product exactly: stainless 304, flat-rolled coil. Two headings remain possible, 7219 and 7220, and the saved assessment says the fact that would decide between them, coil width, is not in the record. Both codes are kept and nothing is invented.',
            'Can you tell what information to ask for next?', 'Start here'),
        'pilot-cement-r4': (
            'Checks pass; owner accepted an earlier revision only',
            'The rule checks pass for heading 2523 and both saved model passes agree. The project owner accepted 2523 for this exact record on 13 September 2026, but under an earlier revision of the mapping (r3). That acceptance does not carry over to the revision shown here (r4), and it is not specialist validation. The record gives no cement subtype, so nothing finer than the four-digit heading is supported.',
            'Is that limited acceptance clearly distinguished from a validated classification?', 'Compare: the one owner decision'),
        'pilot-lldpe-r3': (
            'Checks pass; physical form and density not recorded',
            'The rule checks pass for heading 3901 and both saved model passes agree. The record does not state the physical form (granules, powder or liquid) or the density and comonomer details, so a six-digit code is not supported.',
            None, None),
        'pilot-lime-r3': (
            'Composition not recorded; 2522 or 2825 unsettled',
            'Heading 2522 is proposed, but the saved checks could not settle it. The record gives no composition or purity, so the saved assessment cannot rule out 2825 (chemically defined calcium oxide) or confirm that the product is unslaked lime rather than calcium hydroxide. The two model passes also disagree: the assessor says conditional, the challenger says supported.',
            None, None),
        'pilot-glycol-r2': (
            'Names one chemical, stands in for another; conflict kept',
            'This record is a small ethylene glycol input to a chlorine-making process, and the source note says it stands in for propylene glycol. So the record names one chemical and represents another. The saved passes agreed on 290531 for ethylene glycol, but the record keeps a concern that they classified the stand-in rather than the product it represents; the rule check records a conflict and the product identity is marked disputed. Two passes agreeing is not correctness, and this row shows why.',
            'Does keeping this concern visible help you avoid trusting an unsuitable proposal?', 'Compare: agreement is not correctness'),
    }
    thresholds = {'7219': '600 mm wide or more', '7220': 'narrower than 600 mm'}

    def chip(outcome, extra=''):
        label, cls, _ = status.get(outcome, (outcome, 'other', ''))
        return f'<span class="chip {cls}">{esc(label)}{extra}</span>'

    def codes(r):
        target = r.get('saved_projection_target', 'none')
        alts = r.get('saved_revision_alternatives', 'none listed')
        if target != 'none':
            return target
        return ' / '.join(alts.split('; ')) if alts != 'none listed' else 'none'

    def withheld(r):
        return 'withheld' in r.get('recorded_missing_facts', '')

    def summarise(r):
        note = notes.get(r.get('mapping_revision_id'))
        if note:
            return note
        outcome, code = r['mechanical_outcome'], codes(r)
        alts = ' or '.join(r.get('saved_revision_alternatives', 'none listed').split('; '))
        short, plain = {
            'applicable': (f'Rule checks pass for {code}',
                           f'The saved rule checks pass for code {code}. This is a saved proposal, not specialist validation.'),
            'ambiguous': (f'No single code: {alts}',
                          f'The saved rules leave more than one code possible ({alts}); no single code is established.'),
            'insufficient_information': (f'{code} proposed; facts missing to settle it',
                                         f'Code {code} is proposed, but the record lacks facts the saved checks need to settle it.'),
            'conflicting': (f'{code} proposed; the checks flag a conflict',
                            f'Code {code} is proposed, but the saved checks flag a conflict, so the code is not settled.'),
        }.get(outcome, (f'{code}: {outcome}', f'Code {code}; saved outcome {outcome}. See the saved evidence.'))
        if withheld(r):
            short += '; reasons not public'
            plain += ' No saved model assessment exists for this exact record, and the rule text behind the check is not part of the public release, so the outcome is shown without its reasons.'
        return short, plain, None, None

    def fact_item(text):
        if 'withheld' in text and 'reconstructed' in text:
            return '<li>The reasoning text behind this check is not part of the public release, and nothing has been reconstructed from private files.</li>'
        who, sep, rest = text.partition(': ')
        if sep and '/' in who and len(who) < 60:
            fact, sep2, effect = rest.partition(' Effect: ')
            item = f'<li><span class="who">{esc(who)}</span>{esc(fact)}'
            if sep2:
                item += f' <span class="effect">Effect: {esc(effect)}</span>'
            return item + '</li>'
        return f'<li>{esc(text)}</li>'

    steel = next((r for r in rows if r['row_id'] == 'R01'
                  and {'7219', '7220'} <= set(r.get('saved_revision_alternatives', '').split('; '))), None)
    with_model = sum(1 for r in rows if not withheld(r))
    counts = Counter(r['mechanical_outcome'] for r in rows)

    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<meta name="color-scheme" content="light dark">',
             '<title>HSGraph — a map of how products connect</title>',
             '<style>' + _STYLE + '</style>' + ('<link rel="stylesheet" href="assets/production-graph.css?v=5">' if graph else '') + '</head><body><div class="wrap"><header>',
             '<div class="brand"><a href="#">HSGraph</a><span>A shared map of production</span></div>',
             '<h1>See how products connect.</h1>',
             '<p class="lede">What goes into a product? Which process makes it? Where is it used next? HSGraph connects materials, production processes and products, with HS codes and evidence attached.</p>',
             '<p class="hero-note">The graph is the project. This page is one way to explore it.</p>',
             '<p class="concept-path" aria-label="Concept: materials feed a process, which makes a product that can enter another process">Materials <span aria-hidden="true">→</span> Process <span aria-hidden="true">→</span> Product <span aria-hidden="true">→</span> Next process</p>',
             '<nav class="top" aria-label="Page navigation"><a class="button" href="#graph">Explore the production graph</a><a href="#uses">Who can use it</a><a href="#examples">Check the code matches</a><a href="#downloads">Get the data</a></nav>',
             '<div class="terms"><p><b>HS code.</b> The Harmonized System is the international numbering used on customs declarations to say what a product is. Four digits name a heading, six a subheading.</p>',
             '<p><b>USLCI record.</b> The U.S. Life Cycle Inventory Database describes industrial processes and the products flowing into and out of them. A record here is one such flow in one documented process, not every product with that name.</p></div>',
             '</header><main>',
             graph_section(graph) if graph else '',
             '<section id="code-tree"><h2>Where do the HS codes fit?</h2><p>There are two kinds of links. The production graph shows how things are made. The HS tree groups products into categories: chapter → heading → subheading. A product record links to its proposed category, with the evidence and open questions kept beside it.</p><p>For example, the film record above has three possible headings in chapter 39. Those are alternative classifications for that record; they do not create three production routes.</p></section>' if graph else '',
             '<section id="uses"><h2>One graph. Different ways to use it.</h2><p>The data can be a starting point for company software. These are uses we are building towards; the examples below show the evidence we have today.</p><div class="use-columns"><div><h3>ERP and procurement</h3><p>Connect product records to their documented inputs and classifications.</p></div><div><h3>RFPs and supplier discussions</h3><p>See what needs to be specified, and ask for the missing information.</p></div><div><h3>Manufacturing planning</h3><p>Explore recorded processes, their inputs and outputs, and the gaps that need checking.</p></div></div><p>A shared HS code does not make two products interchangeable. Each connection belongs to the exact records behind it.</p></section>',
             '<section id="guide"><h2>Five minutes, one record</h2><ol class="steps">',
             '<li>Explore a production branch above. Then look at how one product connects to its possible HS codes below.</li>',
             '<li>Open <a href="#R01">record R01</a> and check that the saved findings say what is missing. We did not fill the gap or choose a code.</li>',
             '<li>Tell us whether that would help you, using the <a href="#feedback">reply template</a>. No specialist credentials are needed to comment on clarity.</li></ol>',
             '<p>Have five more minutes? <a href="#R02">R02</a> shows the one owner decision in the dataset and its limits. <a href="#R05">R05</a> shows two model passes agreeing while the record still carries a conflict.</p></section>']
    if steel:
        code_lines = ''.join(f'<span><b>{esc(c)}</b>{esc(thresholds.get(c, ""))}</span>'
                             for c in steel['saved_revision_alternatives'].split('; '))
        parts.append(f'''<section id="example"><h2>One example: a stainless-steel coil</h2>
<p>The production graph needs product-to-code links too. This coil shows why one of those links can remain open: the record has no width, so two headings are still possible.</p>
<figure><div class="flow" role="group" aria-label="Steel coil: source record, two candidate codes, the deciding fact, and what HSGraph records">
<div class="node"><span class="k">1 · Source record</span><span class="v">{esc(steel['source_declared_product'])}</span><span class="d">Product output of a USLCI process. Copied unchanged from the published release.</span><a href="{esc(steel['evidence_file'])}">Open the saved evidence (JSON)</a></div>
<div class="arrow" aria-hidden="true">→</div>
<div class="node"><span class="k">2 · Candidate codes</span><div class="codes">{code_lines}</div><span class="d">Width thresholds as stated in the saved assessment.</span></div>
<div class="arrow" aria-hidden="true">→</div>
<div class="node"><span class="k">3 · Deciding fact</span><span class="v">Coil width</span><span><span class="chip gap">Not in the source record</span></span><span class="d">Nor are measured carbon and chromium percentages, which would let the stainless definition be checked independently.</span></div>
<div class="arrow" aria-hidden="true">→</div>
<div class="node result"><span class="k">4 · Recorded result</span><span>{chip(steel['mechanical_outcome'])}</span><span class="d">Both codes kept. The missing facts are saved with the record. No width is guessed and no code is chosen.</span></div>
</div><figcaption>This is an evidence diagram, not a material-flow or supplier network. It shows what is recorded for one product record; it adds no classification and no supplier link.</figcaption></figure></section>''')
    model_line = 'No saved model assessment'
    if steel and steel.get('saved_HS_case_outcomes_NOT_validation', '').split(' | ')[0].count(': '):
        model_line = steel['saved_HS_case_outcomes_NOT_validation'].split(' | ')[0].partition(': ')[2].replace('_', ' ').replace('=', ': ')
    owner_line = 'None' if not steel or steel.get('owner_review', 'no_owner_acceptance') == 'no_owner_acceptance' else 'Owner decision recorded'
    example = (lambda text: f'<div class="ex"><span class="k">Steel example</span>{text}</div>') if steel else (lambda text: '')
    parts.append(f'''<section id="how"><h2>How HSGraph keeps evidence, checks and opinions apart</h2>
<p>Each record carries up to four layers. They are stored separately. A later layer never rewrites an earlier one, and agreement between layers is not proof.</p>
<div class="layers">
<div class="layer"><h3>1. Source record</h3><p>What the USLCI process says about the product: its name, direction (input or output) and amount.</p>{example(esc(steel['source_declared_product']) if steel else '')}</div>
<div class="layer"><h3>2. Rule check</h3><p>Recorded classification rules applied to the record. Ends in one of the four outcomes below.</p>{example(chip(steel['mechanical_outcome']) if steel else '')}</div>
<div class="layer"><h3>3. Model assessment</h3><p>Two saved AI passes, an assessor and a challenger, each with an outcome, the facts it found missing and any concerns. Saved once; never re-run for this page.</p>{example(esc(model_line))}</div>
<div class="layer"><h3>4. Human review</h3><p>An owner decision by the project owner, or a specialist validation by a classification expert. Across the whole dataset: one owner decision, zero specialist validations.</p>{example(esc(owner_line))}</div>
</div><h3>The four rule-check outcomes</h3><ul class="legend">''')
    for outcome, (label, cls, explanation) in status.items():
        parts.append(f'<li>{chip(outcome)}<span>{esc(explanation)}</span><span class="n">{counts.get(outcome, 0)} of these {len(rows)} records</span></li>')
    parts.append('</ul></section>')
    parts.append(f'<section id="examples"><h2>The ten records</h2><p>Chosen by hand to show different outcomes, not drawn at random. Codes are saved candidates; “conditions pass” does not mean validated. {with_model} of the {len(rows)} records have saved model assessments; the others have only the rule-check outcome.</p>'
                 '<div class="scroll" tabindex="0" role="region" aria-label="Ten records; scroll sideways on small screens"><table><caption>Rule-check outcome per record. No specialist-validated classifications.</caption>'
                 '<thead><tr><th scope="col">Record</th><th scope="col">Product, as named in the source</th><th scope="col">Candidate code(s)</th><th scope="col">Rule check</th><th scope="col">In short</th></tr></thead><tbody>')
    for r in rows:
        short = summarise(r)[0]
        parts.append(f'<tr><th scope="row"><a href="#{r["row_id"]}">{r["row_id"]}</a></th><td data-label="Product, as named in the source">{esc(r["source_declared_product"])}</td><td class="code" data-label="Candidate code(s)">{esc(codes(r))}</td><td data-label="Rule check">{chip(r["mechanical_outcome"])}</td><td class="short" data-label="In short">{esc(short)}</td></tr>')
    parts.append('</tbody></table></div>')
    for r in rows:
        short, plain, question, kicker = summarise(r)
        question = question or 'Would this help your task, and what would you need next?'
        owner_chip = '<span class="chip plain">Owner decision: earlier revision only</span>' if r.get('owner_review', '').startswith('owner_accepted') else ''
        parts.append(f'<section class="case" id="{r["row_id"]}"><p class="eyebrow">Record {r["row_id"]}{" · " + esc(kicker) if kicker else ""}</p>'
                     f'<div class="case-head"><h3>{esc(r["source_declared_product"])}</h3>{chip(r["mechanical_outcome"])}<span class="chip plain">No specialist validation</span>{owner_chip}</div>'
                     f'<p>{esc(plain)}</p><p><strong>Your question:</strong> {esc(question)}</p>')
        parts.append('<details><summary>Missing facts recorded with this row</summary><p class="muted">Quoted from the saved model findings, with the pass that made each one. A short list does not mean the record is complete.</p><ul class="facts">')
        parts.extend(fact_item(fact) for fact in r.get('recorded_missing_facts', 'See retained evidence').split(' | '))
        parts.append('</ul></details>')
        concerns = r.get('post_run_concerns', 'See retained evidence')
        if concerns.startswith('None recorded'):
            body = '<p>None recorded. This is not proof of correctness.</p>'
        else:
            body = '<ul class="facts">' + ''.join(fact_item(c) for c in concerns.split(' | ')) + '</ul>'
        parts.append(f'<details><summary>Warnings and disagreements kept in the record</summary>{body}</details>')
        parts.append('<details><summary>Technical details: IDs, locators and review states</summary><dl class="tech">')
        for key, value in r.items():
            if key not in ('row_id', 'source_declared_product', 'evidence_file'):
                parts.append(f'<dt>{esc(key.replace("_", " "))}</dt><dd>{esc(value).replace(" | ", chr(10))}</dd>')
        parts.append(f'</dl></details><p class="links"><a href="{esc(r["evidence_file"])}">Full saved evidence (JSON)</a> · <a href="#feedback">Give feedback on {r["row_id"]}</a> · <a href="#examples">Back to the list</a></p></section>')
    parts.append('''</section>
<section id="dataset"><h2>What the full dataset contains</h2>
<p>The ten records above come from HSGraph v0.1.0, published on Zenodo with a DOI. Counts are taken from its data card.</p>
<ul class="stats"><li><b>6,936</b><span>HS codes (HS 2022)</span></li><li><b>1,422</b><span>USLCI processes</span></li><li><b>76,211</b><span>recorded inputs and outputs</span></li><li><b>670</b><span>product records assessed</span></li><li><b>1</b><span>owner-accepted mapping</span></li><li><b>0</b><span>specialist validations</span></li></ul>
<p>Every assessment in the dataset is an automated proposal with its evidence attached. The one owner acceptance is the cement record shown in R02.</p></section>
<section id="limits"><h2>What this is not</h2><ul class="limits">
<li>Not a customs ruling or classification advice. Codes here are saved candidates.</li>
<li>Not a verified supply chain or bill of materials. No supplier link is claimed.</li>
<li>Not a complete life-cycle inventory. The full dataset keeps most rows but leaves conversions and formulas unresolved.</li>
<li>Ten hand-picked records, not representative of the dataset.</li>
<li>Zero specialist validations so far. Saved AI findings are recorded outputs, not verification, and one owner acceptance is not expert review.</li></ul></section>
<section id="feedback"><h2>What we need back from you</h2><p>One short reply is enough. “I cannot see a use for this” is useful feedback too. You do not need to classify the product, validate all ten rows, or endorse the project.</p>
<label for="reply"><strong>Copy this into your reply and fill in whichever lines you can:</strong></label>
<textarea id="reply" readonly>Record I looked at: R__
My role / task:
This would help me to… / would not help because…
I would otherwise look up…
The missing or confusing part is…
The next piece of evidence I would need is…</textarea>
<p>Reply to the person who sent you this page, or email <a href="mailto:rbedekar@zeroinsec.com?subject=HSGraph%20sample%20feedback">rbedekar@zeroinsec.com</a>. The link opens your own mail app; this page does not submit or store anything. Please do not send confidential product data.</p>
<p>We will use replies to decide whether evidence inspection is useful and what to improve. We will not treat a reply as specialist acceptance of a code.</p></section>
<section id="downloads"><h2>Data, source and terms</h2><p><a href="production-graph.xlsx">Production graph in Excel</a> · <a href="production-graph.json">Production graph (JSON)</a> · <a href="samples.csv">Classification examples (CSV)</a> · <a href="samples.json">Classification examples (JSON)</a> · <a href="README.md">Selection and verification guide</a> · <a href="LICENSE-DATA">Component-specific terms</a> · <a href="https://doi.org/10.5281/zenodo.22857372">Full dataset on Zenodo</a> · <a href="https://github.com/r-bedekar/hsgraph-open">Code on GitHub</a></p>
<p>The graph adds a view of existing production records. The ten classification rows and their saved findings are unchanged. Share the whole package with its notices. No new model runs were made for this page.</p></section></main>
<footer>Credit: Rizwan Bedekar / HSGraph; DOE / NREL / Alliance for Sustainable Energy; USLCI contributors and other credited sources. No endorsement. See the included notices for component-specific terms.</footer></div></body></html>''')
    document = '\n'.join(parts)
    return render_journey(document, rows, graph_section(graph)) if graph else document.encode()


def build(source_zip, output):
    source_zip, output = Path(source_zip), Path(output)
    source = source_zip.read_bytes()
    if digest(source) != SOURCE_SHA:
        raise ValueError('Source ZIP differs from the approved published v0.1.0 bytes')
    archive = archive_path(output)
    if output.exists() or archive.exists() or Path(str(archive) + '.SHA256SUMS').exists():
        raise FileExistsError('Use fresh output paths; existing files will not be replaced')
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        names = ('exchanges', 'processes', 'supporting-records', 'mapping-projections',
                 'mapping-revisions', 'identity-assessments', 'smoke1', 'smoke2', 'owner-decisions', 'provider-links')
        tables = {name: load_records(z, name + '.jsonl') for name in names}
        by_id = {name: {x['record']['id']: x for x in tables[name]}
                 for name in ('exchanges', 'processes', 'mapping-revisions')}
        projections = {x['record']['exchange_id']: x for x in tables['mapping-projections']}
        identities = {x['record']['scope']['exchange_ids'][0]: x for x in tables['identity-assessments']}
        cases = {x['record']['case_id']: x for x in tables['smoke1']}
        selected = [cases[c]['record']['scope']['instance_id'] for c in SMOKE_CASES]
        for mid in EXTRA_MAPPINGS:
            selected.append(min(x['record']['exchange_id'] for x in tables['mapping-projections']
                                if x['record']['mapping_id'] == mid))
        if len(set(selected)) != 10:
            raise ValueError('Selection must have ten unique instances')
        files = {name: z.read(name) for name in COPIED}
        files['source-release-DATA_CARD.md'] = z.read('DATA_CARD.md')
        files['source-release-CITATION.cff'] = z.read('CITATION.cff')
    rows = []
    for number, eid in enumerate(selected, 1):
        projection = projections[eid]; p = projection['record']; e = by_id['exchanges'][eid]
        records = [e, by_id['processes'][p['process_id']], projection,
                   by_id['mapping-revisions'][p['mapping_id']], identities[eid]]
        records += [x for x in tables['supporting-records']
                    if x['record']['source_id'] == p['definition']['source_id']
                    and x['record']['native'].get('@id') == p['definition']['native_id']]
        for name in ('smoke1', 'smoke2'):
            records += [x for x in tables[name] if x['record']['scope']['instance_id'] == eid]
        records += [x for x in tables['owner-decisions'] if eid in x['record']['binding']['exchange_ids']]
        for decision in (x['record'] for x in records if x['source_artifact'] == 'owner-decisions.jsonl'):
            original = by_id['mapping-revisions'][decision['mapping_id']]
            if original not in records:
                records.append(original)
        row = row_summary(number, records); rows.append(row)
        files[row['evidence_file']] = json_bytes({'row_id': row['row_id'], 'source_release': DOI,
                                                 'source_records': records})
    files['samples.json'] = json_bytes(rows)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows({k: csv_cell(v) for k, v in r.items()} for r in rows)
    files['samples.csv'] = stream.getvalue().encode('utf-8-sig')
    graph_records = select_records(tables)
    graph = project_graph(graph_records)
    files['production-evidence.json'] = json_bytes({'source_release': DOI, 'source_records': graph_records})
    files['production-graph.json'] = json_bytes(graph)
    notices = {n: files[n] for n in COPIED if n != 'candidate/usitc-legal-excerpts.jsonl'}
    files['production-graph.xlsx'] = workbook_bytes(graph, rows, notices)
    files['START_HERE.html'] = render_html(rows, graph)
    files['index.html'] = files['START_HERE.html']
    files['.nojekyll'] = b''
    files['README.md'] = README.encode()
    asset_dir = Path(__file__).with_name('production_assets')
    if not asset_dir.exists():
        asset_dir = Path(__file__).parent.parent / 'assets'
    for asset in ('production-graph.js', 'production-graph.css', 'journey.js', 'Manrope.ttf', 'OFL-Manrope.txt'):
        files['assets/' + asset] = (asset_dir / asset).read_bytes()
    for tool in ('build_review_sample.py', 'verify_review_sample.py', 'production_graph.py', 'production_workbook.py', 'journey_view.py'):
        files['tools/' + tool] = Path(__file__).with_name(tool).read_bytes()
    manifest = {'sample_version': 'discussion-sample-5-guided-journey', 'source_release_doi': DOI,
                'production_graph': graph['counts'],
                'source_zip_sha256': SOURCE_SHA, 'frozen_inner_sha256': INNER_SHA,
                'row_count': 10, 'distinct_instances': 10,
                'distinct_definitions': len({projections[e]['record']['definition']['native_id'] for e in selected}),
                'mechanical_outcomes': dict(Counter(r['mechanical_outcome'] for r in rows)),
                'owner_accepted_exact_instances': sum(r['owner_review'].startswith('owner_accepted') for r in rows),
                'specialist_validations': 0, 'not_representative': True, 'new_model_runs': 0,
                'selection': {'smoke1_cases_in_order': SMOKE_CASES, 'additional_revision_ids': EXTRA_MAPPINGS,
                              'additional_instance_rule': 'lexicographically first exchange ID per revision'},
                'files': {n: {'sha256': digest(b), 'bytes': len(b)} for n, b in sorted(files.items())}}
    files['sample-manifest.json'] = json_bytes(manifest)
    files['SHA256SUMS'] = ''.join(f'{digest(b)}  {n}\n' for n, b in sorted(files.items())).encode()
    output.mkdir(parents=True)
    for name, data in files.items():
        path = output / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(output.name + '/' + name, (2026, 9, 20, 0, 0, 0))
            info.create_system = 3; info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)
    result = {'archive': str(archive), 'bytes': archive.stat().st_size,
              'sha256': digest(archive.read_bytes()), 'rows': len(rows)}
    Path(str(archive) + '.SHA256SUMS').write_text(result['sha256'] + '  ' + archive.name + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-zip', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source_zip, args.output), indent=2))
