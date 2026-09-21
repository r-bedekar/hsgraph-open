#!/usr/bin/env python3
"""Build a ten-instance discussion sample from the exact published ZIP only."""
import argparse
from collections import Counter
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import zipfile

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

README = '''# HSGraph: ten-instance evidence-inspection sample

Discussion sample 2 (guided presentation), derived from published v0.1.0.
Not v0.2.0 and not a new classification dataset. Prepared for Rizwan Bedekar /
HSGraph on 2026-09-21. The ten rows and embedded evidence are unchanged from
discussion sample 1; only presentation, guide and packaging tools changed.
Source release: https://doi.org/10.5281/zenodo.22857372
Code: https://github.com/r-bedekar/hsgraph-open/tree/v0.1.0
Contact: rbedekar@zeroinsec.com

## Start here

Unzip into a new folder and open index.html (or START_HERE.html) in a browser. No server,
installation, AI account or network connection is needed. The table has exactly
10 distinct exchange instances from 10 flow definitions; they are not 10 verified
HS classifications. samples.csv is for spreadsheet inspection; samples.json is
the structured summary. Each row links to its underlying evidence JSON.
Follow the five-minute guide, inspect one case, and use the feedback template.
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

New work consists of selection, record wrappers, field projection and HTML/CSV
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


def render_html(rows):
    esc = lambda x: html.escape(str(x), quote=True)
    status = {
        'ambiguous': ('More than one candidate', 'The saved rules leave competing candidates; no single code is established.'),
        'applicable': ('Recorded conditions pass', 'The saved mechanical checks pass for this proposal. This is not specialist validation.'),
        'insufficient_information': ('Information missing', 'The saved checks lack information needed to settle the proposal.'),
        'conflicting': ('Recorded conflict', 'The saved checks flag a conflict. Do not treat the proposed code as settled.'),
    }
    prompts = {
        'R01': ('Start here: what is missing?', 'The saved steel case retains 7219 and 7220 as alternatives. Its assessor lists missing coil width and measured carbon/chromium information. We have not filled those gaps.', 'Can you tell what information the reviewer would need next?'),
        'R02': ('Compare: what did the owner accept?', 'One owner decision applies to the original cement revision r3 and exact instance. It does not approve the later r4 projection shown here, and it is not specialist validation.', 'Is that limited acceptance clearly distinguished from a validated classification?'),
        'R05': ('Compare: why keep a failure?', 'The saved glycol case includes a proxy/product mismatch concern. Model agreement is retained alongside that concern, not presented as proof of correctness.', 'Does preserving this concern help you avoid trusting an inappropriate proposal?'),
    }
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>HSGraph — a five-minute evidence walkthrough</title>',
             '''<style>
body{font:17px/1.6 system-ui,sans-serif;color:#182638;max-width:1120px;margin:32px auto;padding:0 22px;background:#f6f8fa}h1,h2,h3{line-height:1.2}h1{font-size:clamp(2rem,4vw,3rem);max-width:850px}a{color:#125a89}a:focus-visible,summary:focus-visible,textarea:focus-visible{outline:3px solid #b15b00;outline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:18px;margin:22px 0}.button{display:inline-block;background:#135d65;color:white;padding:10px 18px;border-radius:6px;text-decoration:none}.notice{border-left:5px solid #b15b00;background:#fff3de;padding:14px 18px}.panel,section.case{margin:24px 0;padding:24px;border:1px solid #cbd5df;border-radius:8px;background:white;overflow-wrap:anywhere}section.case:target{border:2px solid #135d65}section{scroll-margin-top:18px}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.cards>div{padding:16px;background:#edf3f5;border-radius:6px}.cards h3{margin-top:0}table{border-collapse:collapse;width:100%;font-size:15px}caption{text-align:left;margin-bottom:12px}th,td{border:1px solid #cbd5df;padding:12px;text-align:left;vertical-align:top}th{background:#e7eef4}.scroll{overflow-x:auto}details{margin:16px 0;border-top:1px solid #d6dfe6;padding-top:12px}summary{font-weight:650;cursor:pointer}dt{font-weight:650;margin-top:12px}dd{margin-left:0;white-space:pre-wrap}small,.muted{color:#455568}.badge{display:inline-block;background:#edf3f5;border:1px solid #cbd5df;padding:3px 9px;border-radius:5px}.trail{display:grid;grid-template-columns:2fr 1fr 2fr 1fr 2fr;gap:8px;align-items:center}.node{border:2px solid #658391;border-radius:6px;padding:15px;background:#f1f6f7}.proposal{border-style:dashed;background:#fff9ef}.edge{text-align:center;font-size:14px}.edge span{display:block;font-size:26px}textarea{box-sizing:border-box;width:100%;min-height:215px;padding:14px;font:15px/1.6 system-ui;border:1px solid #879baa;border-radius:6px;background:#f8fafb}.facts li{margin-bottom:12px}footer{padding:22px 0;font-size:14px}@media(max-width:720px){.cards{grid-template-columns:1fr}.trail{grid-template-columns:1fr}.edge span{transform:rotate(90deg)}.panel,section.case{padding:18px}body{padding:0 14px}table{min-width:680px}}
</style></head><body><header><p class="muted">HSGraph · Guided sample 2 · Based on the published v0.1.0 dataset</p>
<h1>Can you see the evidence behind a proposed HS code?</h1>
<p>This sample lets you inspect ten product records, the codes proposed for them, and the information still missing.</p>
<p><strong>What we need from you:</strong> spend five minutes on one example and tell us whether this would help with a real task. You are not being asked to certify a classification or review all ten rows.</p>
<nav aria-label="Page navigation"><a class="button" href="#guide">Start the guide</a><a href="#examples">Browse ten examples</a><a href="#graph">See the evidence diagram</a><a href="#feedback">Give feedback</a></nav>
<p class="notice"><strong>Zero specialist validations.</strong> This is a discussion sample, not a customs ruling, verified supply chain or complete life-cycle assessment. It is not representative of all products. One original owner decision is retained with its limited scope.</p></header><main>
<section class="panel" id="guide"><h2>A five-minute guide</h2>
<div class="cards"><div><h3>1. Open the steel case</h3><p>Start with <a href="#R01">R01: steel coil</a>. Notice that two HS headings remain possible.</p></div><div><h3>2. Look for the gap</h3><p>Read “What is missing?” The saved assessor says coil width is missing. We do not invent it or choose a heading.</p></div><div><h3>3. Tell us if this helps</h3><p>Could you identify the next information to request? Use the <a href="#feedback">short reply template</a>; no specialist credentials are needed to comment on clarity.</p></div></div>
<p>Have another five minutes? Compare <a href="#R02">R02: a limited owner decision</a> and <a href="#R05">R05: why model agreement can still be wrong</a>. Full evidence and technical fields are optional expandable sections.</p></section>
<section class="panel" id="key"><h2>How to read this page</h2>
<p><strong>HS</strong> is the Harmonized System of product classification. <strong>USLCI</strong> is the U.S. Life Cycle Inventory source used here. A row is one recorded product exchange in a documented process—not every product with that name.</p>
<p>A <strong>candidate code</strong> is a saved proposal, not a recommendation. A <strong>mechanical check</strong> applies recorded rules; a <strong>model assessment</strong> is a saved AI finding; an <strong>owner decision</strong> records this project owner’s limited acceptance. None substitutes for specialist review.</p><dl>''']
    for label, explanation in status.values():
        parts.append(f'<dt>{esc(label)}</dt><dd>{esc(explanation)}</dd>')
    parts.append('</dl></section>')
    steel = next((r for r in rows if r['row_id'] == 'R01'), None)
    if steel:
        parts.append(f'''<section class="panel" id="graph"><h2>A small graph demo: follow the evidence</h2>
<p>This is an <strong>evidence relationship diagram</strong> for R01, not a material-flow or supplier network. Read the connection labels; a proposed relationship is not established identity.</p>
<div class="trail" role="group" aria-label="R01 record linked to a saved proposal and its unresolved alternatives">
<a class="node" href="{esc(steel['evidence_file'])}"><strong>Source record</strong><br>{esc(steel['source_declared_product'])}<br><small>Open the retained evidence</small></a>
<div class="edge">is the subject of<span aria-hidden="true">→</span></div>
<a class="node" href="#R01"><strong>Saved proposal</strong><br>{esc(steel.get('mapping_revision_id', 'See evidence'))}<br>{esc(status.get(steel['mechanical_outcome'], (steel['mechanical_outcome'], ''))[0])}</a>
<div class="edge">lists alternatives<span aria-hidden="true">⇢</span></div>
<div class="node proposal"><strong>HS candidates, not an accepted code</strong><br>{esc(steel['saved_revision_alternatives'])}</div></div>
<p><strong>Why no final connection?</strong> The saved assessor lists missing width and measured composition information. See <a href="#R01">the exact saved findings</a>. Dashed styling marks the unresolved proposal, not a physical dependency.</p>
<p class="muted">The ten sampled records do not form a complete connected production graph. A broader explorer would require a separate, source-backed selection of actual process/exchange relationships.</p></section>''')
    parts.append('<section class="panel" id="examples"><h2>Choose an example</h2><p>Start with one row. Codes below are saved candidates only; “conditions pass” does not mean validated.</p><div class="scroll" tabindex="0" role="region" aria-label="Ten examples; scroll horizontally on small screens"><table><caption>Ten distinct records — no specialist-validated classifications</caption><thead><tr><th scope="col">Example</th><th scope="col">Candidate code(s)</th><th scope="col">What the saved check says</th><th scope="col">Owner decision</th></tr></thead><tbody>')
    for r in rows:
        code = 'No single target' if r['saved_projection_target'] == 'none' else 'Proposed: ' + r['saved_projection_target']
        if r['saved_revision_alternatives'] != 'none listed':
            code += '; alternatives: ' + r['saved_revision_alternatives']
        owner = 'Original revision only; not the displayed later projection' if r['owner_review'].startswith('owner_accepted') else 'None for this instance'
        parts.append(f'<tr><td><a href="#{r["row_id"]}">{r["row_id"]} · {esc(r["source_declared_product"])}</a></td><td>{esc(code)}</td><td>{esc(status.get(r["mechanical_outcome"], (r["mechanical_outcome"], ""))[0])}</td><td>{esc(owner)}</td></tr>')
    parts.append('</tbody></table></div></section>')
    for r in rows:
        label, explanation = status.get(r['mechanical_outcome'], (r['mechanical_outcome'], 'See the saved evidence.'))
        title, takeaway, question = prompts.get(r['row_id'], ('Inspect another source record', explanation, 'Would this evidence help your task, and what additional information would you need?'))
        parts.append(f'<section class="case" id="{r["row_id"]}"><p class="muted">{esc(title)}</p><h2>{r["row_id"]} · {esc(r["source_declared_product"])}</h2><p><span class="badge">{esc(label)}</span> · No specialist validation</p><p>{esc(takeaway)}</p><p><strong>Your question:</strong> {esc(question)}</p>')
        parts.append('<details><summary>What is missing? Read the saved findings</summary><p>These are attributed saved model findings, not newly verified facts. No listed gap does not prove the information is complete.</p><ul class="facts">')
        for fact in r.get('recorded_missing_facts', 'See retained evidence').split(' | '):
            parts.append(f'<li>{esc(fact)}</li>')
        parts.append('</ul></details>')
        parts.append(f'<details><summary>Warnings and disagreements retained in the record</summary><p>{esc(r.get("post_run_concerns", "See retained evidence")).replace(" | ", "<br><br>")}</p></details>')
        parts.append('<details><summary>Technical details: codes, review states, IDs and locators</summary><dl>')
        for key, value in r.items():
            if key not in ('row_id', 'source_declared_product', 'evidence_file'):
                parts.append(f'<dt>{esc(key.replace("_", " "))}</dt><dd>{esc(value).replace(" | ", "<br><br>")}</dd>')
        parts.append(f'</dl></details><p><a href="{esc(r["evidence_file"])}">Full original evidence (JSON)</a> · <a href="#feedback">Give feedback on {r["row_id"]}</a> · <a href="#examples">Back to examples</a></p></section>')
    parts.append('''<section class="panel" id="feedback"><h2>What we need back from you</h2><p>One short reply is enough. “I cannot see a use for this” is useful feedback too. You do not need to classify the product, validate all ten rows, or endorse the project.</p>
<label for="reply"><strong>Copy this into your reply and fill in whichever lines you can:</strong></label>
<textarea id="reply" readonly>Example I looked at: R__
My role / task:
This would help me to… / would not help because…
I would otherwise look up…
The missing or confusing part is…
The next piece of evidence I would need is…</textarea>
<p>Reply to the person who sent you this sample, or email <a href="mailto:rbedekar@zeroinsec.com?subject=HSGraph%20sample%20feedback">rbedekar@zeroinsec.com</a>. The email link opens your own mail app; this page does not submit or store a response. Please do not send confidential product data.</p>
<p>We will use feedback to decide whether evidence inspection is useful and what to improve. We will not treat it as specialist acceptance of a code.</p></section>
<section class="panel" id="downloads"><h2>Data, source and terms</h2><p><a href="samples.csv">Spreadsheet CSV</a> · <a href="samples.json">Summary JSON</a> · <a href="README.md">Selection and verification guide</a> · <a href="LICENSE-DATA">Component-specific terms</a> · <a href="https://doi.org/10.5281/zenodo.22857372">Published full dataset</a></p><p>The same ten rows and saved findings are retained; only this guide and presentation changed. Share the complete package with its source notices. No new models were run.</p></section></main>
<footer>Credit: Rizwan Bedekar / HSGraph; DOE / NREL / Alliance for Sustainable Energy; USLCI contributors and other credited sources. No endorsement. See the included notices for component-specific terms.</footer></body></html>''')
    return '\n'.join(parts).encode()


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
                 'mapping-revisions', 'identity-assessments', 'smoke1', 'smoke2', 'owner-decisions')
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
    files['START_HERE.html'] = render_html(rows)
    files['index.html'] = files['START_HERE.html']
    files['.nojekyll'] = b''
    files['README.md'] = README.encode()
    for tool in ('build_review_sample.py', 'verify_review_sample.py'):
        files['tools/' + tool] = Path(__file__).with_name(tool).read_bytes()
    manifest = {'sample_version': 'discussion-sample-2-guided', 'source_release_doi': DOI,
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
