"""Project a bounded production view from unchanged public source records.

HS mappings decorate exact exchange instances; they never create a process link.
"""
from collections import defaultdict

PREFIX = 'uslci-1.2026-06.0:processes:'
ROOTS = (
    ('film', 'Stretch film', PREFIX + '26f39b7c-389c-4903-8f09-6ef5e95876cc'),
    ('cement', 'Portland cement', PREFIX + '62993671-574c-3fc5-b66a-6be3bb21ad3d'),
    ('casting', 'Aluminium casting', PREFIX + 'f61ecd3b-fdba-3739-8051-1d4bb0c2d98e'),
)


def select_records(tables):
    """All direct flows of roots, their direct providers and direct consumers."""
    root_ids = {p for _, _, p in ROOTS}
    processes = {x['record']['id']: x for x in tables['processes']}
    if not root_ids <= processes.keys():
        raise ValueError('Production demonstration roots missing from source')
    selected = set(root_ids)
    for item in tables['provider-links']:
        r = item['record']
        if r['traversable']:
            if r['process_id'] in root_ids and r.get('target_process_id') in processes:
                selected.add(r['target_process_id'])
            if r.get('target_process_id') in root_ids and r['process_id'] in processes:
                selected.add(r['process_id'])
    records = [processes[p] for p in sorted(selected)]
    exchanges = [x for x in tables['exchanges'] if x['record']['process_id'] in selected]
    records += exchanges
    exchange_ids = {x['record']['id'] for x in exchanges}
    records += [x for x in tables['provider-links'] if x['record']['id'] in exchange_ids]
    mappings = [x for x in tables['mapping-projections'] if x['record']['exchange_id'] in exchange_ids]
    records += mappings
    revision_ids = {x['record']['mapping_id'] for x in mappings}
    decisions = [x for x in tables['owner-decisions']
                 if set(x['record']['binding']['exchange_ids']) & exchange_ids]
    records += decisions
    revision_ids.update(x['record']['mapping_id'] for x in decisions)
    records += [x for x in tables['mapping-revisions'] if x['record']['id'] in revision_ids]
    return sorted(records, key=lambda x: (x['source_artifact'], x['source_line']))


def project_graph(records, roots=ROOTS):
    by_type = defaultdict(dict)
    for item in records:
        by_type[item['source_artifact']][item['record'].get('id', f"line:{item['source_line']}")] = item
    processes = by_type['processes.jsonl']
    exchanges = by_type['exchanges.jsonl']
    revisions = by_type['mapping-revisions.jsonl']
    providers = by_type['provider-links.jsonl']
    projections = defaultdict(list)
    for item in by_type['mapping-projections.jsonl'].values():
        projections[item['record']['exchange_id']].append(item)

    def evidence(item):
        return {k: item[k] for k in ('source_artifact', 'source_line', 'source_line_sha256')}

    nodes, flows, edges = {}, {}, []
    for pid, item in processes.items():
        native = item['record']['native']; doc = native.get('processDocumentation', {})
        nodes[pid] = {'id': pid, 'name': native['name'], 'description': native.get('description', ''),
                      'type': native.get('processType', 'not supplied'),
                      'valid_from': doc.get('validFrom'), 'valid_until': doc.get('validUntil'),
                      'technology': doc.get('technologyDescription', ''),
                      'completeness': doc.get('completenessDescription', ''),
                      'inputs': [], 'outputs': [], 'environmental_exchanges': 0,
                      'source': evidence(item)}
    for eid, item in exchanges.items():
        r = item['record']; n = r['native']; pid = r['process_id']
        if pid not in nodes:
            raise ValueError('Exchange refers to absent process')
        flow = n['flow']; flow_type = flow.get('flowType', 'unknown')
        if flow_type == 'ELEMENTARY_FLOW':
            nodes[pid]['environmental_exchanges'] += 1
            continue
        mappings = []
        for projection in projections[eid]:
            p = projection['record']; revision = revisions[p['mapping_id']]['record']
            mappings.append({'target': p.get('target'), 'alternatives': revision.get('alternatives', []),
                             'outcome': p['mechanical_outcome'], 'revision': p['mapping_id'],
                             'saved_review_status': p['review_status'],
                             'specialist_validation': 'none in published v0.1.0',
                             'source': evidence(projection)})
        owner = [x['record'] for x in by_type['owner-decisions.jsonl'].values()
                 if eid in x['record']['binding']['exchange_ids']]
        provider = providers.get(eid)
        provider_view = None
        if provider:
            p = provider['record']; target = p.get('target_process_id')
            can_follow = (p['traversable'] is True and target in nodes)
            if can_follow:
                if p.get('native_direction') != 'input' or n.get('isInput') is not True or p.get('avoided'):
                    raise ValueError('Invalid traversable input provider link')
                outputs = p.get('provider_exchange_ids', [])
                if not outputs:
                    raise ValueError('Provider link without explicit output references')
                for output in outputs:
                    if output not in exchanges:
                        raise ValueError('Referenced provider output absent')
                    pr = exchanges[output]['record']; pn = pr['native']
                    if (pr['process_id'] != target or pn.get('isInput') is not False
                            or pn['flow']['@id'] != flow['@id'] or p['flow_id'] != flow['@id']):
                        raise ValueError('Provider output is not the exact same-flow output')
                edges.append({'kind': 'modeled_provider', 'from': target, 'to': eid,
                              'provider_output_ids': outputs, 'source': evidence(provider)})
            provider_view = {'process_id': target, 'status': p['status'], 'can_follow': can_follow,
                             'traversable': p['traversable'], 'stops': p.get('traversal_stops', []),
                             'output_ids': p.get('provider_exchange_ids', []),
                             'meaning': p.get('meaning', ''), 'source': evidence(provider)}
        f = {'id': eid, 'process_id': pid, 'name': flow['name'], 'flow_type': flow_type,
             'flow_id': flow['@id'], 'is_input': n.get('isInput'),
             'reference_output': n.get('isQuantitativeReference', False),
             'interpretation': r['interpretation'], 'amount': n.get('amount'),
             'unit': n.get('unit', {}).get('name'), 'formula': n.get('amountFormula'),
             'quantity_status': r.get('quantity_status'), 'mappings': mappings,
             'owner_decisions': owner, 'provider': provider_view, 'source': evidence(item),
             'locator': r['locator'], 'consumers': []}
        flows[eid] = f
        direction = 'inputs' if n.get('isInput') is True else 'outputs'
        nodes[pid][direction].append(eid)
        edges.append({'kind': 'recorded_input' if direction == 'inputs' else 'recorded_output',
                      'from': eid if direction == 'inputs' else pid,
                      'to': pid if direction == 'inputs' else eid, 'source': evidence(item)})
    for edge in edges:
        if edge['kind'] == 'modeled_provider':
            for eid in edge['provider_output_ids']:
                if eid not in flows:
                    raise ValueError('Cross-process provider output excluded from visible flow types')
                flows[eid]['consumers'].append({'process_id': flows[edge['to']]['process_id'],
                                               'exchange_id': edge['to'], 'source': edge['source']})
    return {'schema': 'hsgraph-production-view-1',
            'source_release': 'https://doi.org/10.5281/zenodo.22857372',
            'roots': [{'key': key, 'label': label, 'id': pid} for key, label, pid in roots],
            'scope': 'Three example roots, one explicit provider step upstream and one consumer step downstream. All retained direct product, service and waste exchanges for included processes. Environmental exchanges counted separately.',
            'meaning': 'Recorded inventory relationships; modeled defaults are not actual suppliers. No quantities multiplied, no compatibility inferred, no links created from matching HS codes.',
            'processes': nodes, 'flows': flows, 'edges': edges,
            'counts': {'processes': len(nodes), 'flows': len(flows), 'edges': len(edges),
                       'provider_links': sum(e['kind'] == 'modeled_provider' for e in edges),
                       'environmental_exchanges': sum(p['environmental_exchanges'] for p in nodes.values())}}


def graph_section(graph):
    """Static accessible entry plus progressive enhancement from graph.js."""
    import html
    import json
    esc = html.escape
    root = graph['processes'][graph['roots'][0]['id']]
    def labels(ids):
        return ', '.join(graph['flows'][eid]['name'] for eid in ids)
    buttons = ''.join(f'<button type="button" data-root="{esc(r["id"], quote=True)}">{esc(r["label"])}</button>' for r in graph['roots'])
    data = json.dumps(graph, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('&', '\\u0026')
    return f'''<section id="graph" class="production-section"><p class="eyebrow">Explore a real production branch</p>
<h2>Follow the inputs. See the process. Find the output.</h2>
<p>Start with stretch film. Its source model links resin production and an extrusion service to film production. Select a product to see its proposed HS codes; select a connected process to keep exploring.</p>
<div class="graph-roots" aria-label="Production examples">{buttons}</div>
<div class="graph-toolbar"><button id="graph-back" type="button" disabled>← Previous process</button><label><input type="checkbox" id="graph-all"> Show every input in this process</label><span id="graph-count" aria-live="polite"></span></div>
<div id="graph-context"></div>
<div id="graph-canvas" class="graph-canvas" role="region" aria-label="Interactive production graph" tabindex="0"></div>
<p class="graph-key"><span class="key-process">■ Process</span> <span class="key-product">■ Product / service</span> <span class="key-waste">■ Waste</span> <span>→ Recorded input or output</span> <span>⇢ Explicit modeled provider</span></p>
<div id="graph-detail" class="graph-detail" aria-live="polite"><h3>Select a product or process</h3><p>Its source record, classification state and available next steps appear here.</p></div>
<details class="graph-fallback"><summary>Read the first branch as text</summary><p><strong>Inputs:</strong> {esc(labels(root['inputs']))}</p><p><strong>Process:</strong> {esc(root['name'])}</p><p><strong>Outputs:</strong> {esc(labels(root['outputs']))}</p><p>This text stays available without JavaScript. The full view is also available in <a href="production-graph.json">graph JSON</a>.</p></details>
<p class="muted">This sample includes {graph['counts']['processes']} processes and {graph['counts']['provider_links']} links explicitly named in the source. A linked process is a model, not an actual supplier. Source dates can differ between models. Missing and blocked links stay visible. Natural resources and emissions are counted separately and retained in the source records.</p>
<p><a href="production-graph.json">Download the graph (JSON)</a> · <a href="production-evidence.json">Inspect the source records</a> · <a href="#example">See why a product’s HS match can stay open</a></p>
<script id="production-data" type="application/json">{data}</script><script src="assets/production-graph.js" defer></script></section>'''
