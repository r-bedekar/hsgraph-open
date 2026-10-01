"""A graph-first Excel reading view, built with the Python standard library.

All data cells are literal strings, including codes and untrusted source text.
Optional catalogue wording is for a separate local review copy only.
"""
import io
import math
import textwrap
from xml.sax.saxutils import escape, quoteattr
import zipfile

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
OUTCOMES = {'applicable': 'Saved checks pass; needs specialist review',
            'ambiguous': 'More than one code remains possible',
            'insufficient_information': 'Information is missing',
            'conflicting': 'A conflict needs review'}


def col(number):
    result = ''
    while number:
        number, rem = divmod(number - 1, 26)
        result = chr(65 + rem) + result
    return result


def cell(address, value, style=0):
    text = '' if value is None else str(value)
    if len(text) > 32767:
        raise ValueError('Excel cell exceeds the text limit; split it explicitly')
    return f'<c r="{address}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'


def worksheet(rows, widths, merges=(), frozen=0, filtered=False, print_area=False):
    end = col(len(widths)); last = max(rows)
    pane = f'<pane ySplit="{frozen}" topLeftCell="A{frozen+1}" activePane="bottomLeft" state="frozen"/>' if frozen else ''
    body = [f'<worksheet xmlns="{NS}"><sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>',
            f'<dimension ref="A1:{end}{last}"/><sheetViews><sheetView showGridLines="0" zoomScale="85" workbookViewId="0">{pane}</sheetView></sheetViews>',
            '<sheetFormatPr defaultRowHeight="21"/><cols>',
            ''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, 1)),
            '</cols><sheetData>']
    for r, (height, cells) in sorted(rows.items()):
        body.append(f'<row r="{r}" ht="{height}" customHeight="1">')
        body.extend(cell(f'{col(c)}{r}', value, style) for c, (value, style) in sorted(cells.items()))
        body.append('</row>')
    body.append('</sheetData>')
    if filtered and last > 4:
        body.append(f'<autoFilter ref="A4:{end}{last}"/>')
    if merges:
        body.append(f'<mergeCells count="{len(merges)}">'+''.join(f'<mergeCell ref="{m}"/>' for m in merges)+'</mergeCells>')
    body.append('<pageMargins left="0.25" right="0.25" top="0.4" bottom="0.4" header="0.2" footer="0.2"/>')
    body.append(f'<pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="{1 if print_area else 0}"/></worksheet>')
    return ''.join(body)


def table(title, subtitle, headers, values, widths):
    end = col(len(headers))
    rows = {1: (36, {1: (title, 1)}), 2: (45, {1: (subtitle, 0)}),
            4: (32, {i: (v, 2) for i, v in enumerate(headers, 1)})}
    for r, values_row in enumerate(values, 5):
        lines = max(sum(max(1, math.ceil(len(line) / max(8, width-4)))
                        for line in str(value or '').split('\n')) for value, width in zip(values_row, widths))
        rows[r] = (min(400, max(36, lines * 15 + 14)),
                   {i: (v, 0 if r % 2 else 3) for i, v in enumerate(values_row, 1)})
    return worksheet(rows, widths, [f'A1:{end}1', f'A2:{end}2'], frozen=4, filtered=True)


def code_values(flow):
    return sorted({t['code'] for m in flow['mappings']
                   for t in ([m['target']] if m['target'] else m['alternatives'])})


def start_sheet(graph):
    root = graph['processes'][graph['roots'][0]['id']]
    rows = {r: (23, {}) for r in range(1, 36)}
    merges = []

    def box(r1, c1, r2, c2, text, style=0):
        for r in range(r1, r2+1):
            for c in range(c1, c2+1):
                rows[r][1][c] = ('', style)
        rows[r1][1][c1] = (text, style)
        merges.append(f'{col(c1)}{r1}:{col(c2)}{r2}')

    box(1, 1, 2, 18, 'HSGraph | See how products connect', 1)
    box(3, 1, 4, 18, 'A shared map of materials, the processes that use them, and the products they make. HS codes and evidence sit beside the product records.')
    box(5, 1, 6, 18, 'The graph is the project. Excel and the website are two ways to read it. Start with this real example: making plastic stretch film.')
    for start, end, name in [(1,4,'Linked process'), (6,9,'Input'), (11,13,'Process'), (15,18,'Output')]:
        box(7, start, 7, end, name, 2)
    inputs = [graph['flows'][eid] for eid in root['inputs']]
    outputs = [graph['flows'][eid] for eid in root['outputs']]
    if len(inputs) != 2 or len(outputs) != 2:
        raise ValueError('Revisit the introductory film diagram when source selection changes')
    outputs.sort(key=lambda f: not f['reference_output'])
    for i, f in enumerate(inputs):
        r = 8 + i*5
        provider = f['provider']
        name = graph['processes'][provider['process_id']]['name'] if provider and provider['can_follow'] else 'No followable provider in this view'
        box(r,1,r+3,4,name,4)
        box(r,5,r+3,5,'⇢',7)
        box(r,6,r+3,9,f['name'],5)
        box(r,10,r+3,10,'→',7)
    box(10,11,14,13,'Make stretch film\n\nProduction process',4)
    for i, f in enumerate(outputs):
        r = 8 + i*5
        box(r,14,r+3,14,'→',7)
        codes = code_values(f)
        label = f['name'] + ('\nHS ' + ' / '.join(codes) + '\nMore than one code' if codes else '\nNo HS proposal for this record')
        box(r,15,r+3,18,label,6 if codes else 3)
    downstream = sorted({graph['processes'][c['process_id']]['name'] for f in outputs for c in f['consumers'] if f['reference_output']})
    next_step = 'Where the film is used next: Stretch film → ' + '; '.join(downstream) if downstream else 'No further use of this film is included in this sample.'
    box(18,1,19,18,next_step,5)
    box(20,1,21,18,'Read left to right. Blue boxes are processes. Green boxes are inputs. The amber output has an open HS match. ⇢ means the source explicitly links a process model to this input; → means a recorded input or output.')
    box(23,1,23,18,'What companies could use this for',2)
    box(24,1,25,6,'ERP / procurement\nConnect products to inputs and classification evidence.',5)
    box(24,7,25,12,'RFPs / supplier discussions\nFind the specifications and questions to ask.',5)
    box(24,13,25,18,'Manufacturing planning\nExplore recorded process routes and their gaps.',5)
    box(27,1,28,18,'Next: read “Production links” for connected processes, “Processes” for what each process does, and “Product examples” for the classification questions. “Products” holds all visible input and output records.')
    box(30,1,31,18,'A recorded process model is not an actual supplier or a verified bill of materials. A matching HS code alone never creates a production link. Proposed classifications still need specialist review before being relied on.')
    box(33,1,34,18,f"This sample: {graph['counts']['processes']} processes; {graph['counts']['provider_links']} explicit provider links. Source: HSGraph v0.1.0, doi.org/10.5281/zenodo.22857372. Source dates and full descriptions are on the Processes sheet.")
    return worksheet(rows, [8]*18, merges, print_area=True)


def workbook_bytes(graph, examples, notices, names=None, reading_sheets=(), extra_codes=()):
    """names, if supplied, maps HS codes to wording from a separately pinned source."""
    pids = {pid: f'P{i:03}' for i, pid in enumerate(graph['processes'], 1)}
    fids = {fid: f'F{i:04}' for i, fid in enumerate(graph['flows'], 1)}

    def named(codes):
        return '\n'.join(c + (' — ' + names[c] if names and c in names else '') for c in codes) or 'No code proposed'

    processes, products, links, refs = [], [], [], []
    for pid, p in graph['processes'].items():
        processes.append([pids[pid], p['name'], p['description'] or 'No description supplied',
                          f"{p['valid_from'] or 'unknown'} to {p['valid_until'] or 'unknown'}",
                          len(p['inputs']), len(p['outputs']), p['environmental_exchanges']])
        refs.append([pids[pid], pid, p['source']['source_artifact'], p['source']['source_line'], p['source']['source_line_sha256']])
    for fid, f in graph['flows'].items():
        provider = f['provider']
        state = 'No provider recorded'
        if provider:
            state = ('Follow ' + pids[provider['process_id']] if provider['can_follow']
                     else 'Outside sample' if provider['traversable'] else 'Stops: '+', '.join([provider['status'], *provider['stops']]))
        products.append([fids[fid], pids[f['process_id']], f['name'], 'Input' if f['is_input'] else 'Output',
                         f['flow_type'].replace('_', ' ').lower(), named(code_values(f)),
                         '\n'.join(OUTCOMES.get(m['outcome'], m['outcome']) for m in f['mappings']) or 'Not assessed here', state])
        refs.append([fids[fid], fid, f['source']['source_artifact'], f['source']['source_line'], f['source']['source_line_sha256']])
    for e in graph['edges']:
        if e['kind'] != 'modeled_provider':
            continue
        f = graph['flows'][e['to']]
        links.append([pids[e['from']], graph['processes'][e['from']]['name'], f['name'],
                      pids[f['process_id']], graph['processes'][f['process_id']]['name'],
                      ', '.join(fids[x] for x in e['provider_output_ids']), fids[f['id']],
                      f"{e['source']['source_artifact']}:{e['source']['source_line']}"])
    example_rows = []
    for r in examples:
        codes = [r['saved_projection_target']] if r['saved_projection_target'] != 'none' else r['saved_revision_alternatives'].split('; ')
        example_rows.append([r['row_id'], r['source_declared_product'], named([c for c in codes if c != 'none listed']),
                             OUTCOMES.get(r['mechanical_outcome'], r['mechanical_outcome']),
                             r.get('recorded_missing_facts', 'See saved evidence'), ''])
    sheets = [('Start here', start_sheet(graph)),
              ('Production links', table('Follow the production links', 'Each row is an explicit source link. The linked processes are inventory models, not actual supplier claims. Read from left to right.',
                 ['From process','Process name','Input supplied in the model','To process','Process that uses it','Matching output record','Input record','Evidence'], links, [14,44,40,14,44,22,18,38])),
              ('Processes', table('What each process does', 'These are source descriptions. Historical source dates matter; a connection does not establish compatibility between models.',
                 ['Process','Name','Description from source','Source dates','Inputs','Outputs','Environmental records'], processes, [14,48,100,30,12,12,20])),
              ('Product examples', table('Why a product-to-code match can stay open', 'Ten original saved examples. Codes are proposals; none has specialist validation. The last column is yours to fill in.',
                 ['Example','Product description','Possible HS code(s)','Saved result in plain words','Missing facts from saved assessments','Your comments'], example_rows, [12,44,55 if names else 24,38,100,36])),
              ('Products', table('Inputs and outputs with proposed HS codes', 'Products belong to exact process records. A code on one record is never copied to another just because its name matches.',
                 ['Record','Process','Product / service / waste','Direction','Source type','Proposed HS code(s)','Saved result','Provider boundary'], products, [14,14,55,14,20,55 if names else 24,40,38]))]
    if reading_sheets:
        replacements = {s[0] for s in reading_sheets}
        sheets = [(name, xml) for name, xml in sheets if name not in replacements]
        sheets[3:3] = [(name, table(title, subtitle, headers, values, widths))
                       for name, title, subtitle, headers, values, widths in reading_sheets]
    if names:
        codes = {c for f in graph['flows'].values() for c in code_values(f)}
        codes.update(c for r in examples for c in ([r['saved_projection_target']] if r['saved_projection_target'] != 'none' else r['saved_revision_alternatives'].split('; ')) if c != 'none listed')
        codes.update(extra_codes)
        def required(code):
            if code not in names:
                raise ValueError('Missing catalogue wording: ' + code)
            return names[code]
        code_rows = [[c, required(c), 'Heading (4 digits)' if len(c)==4 else 'Subheading (6 digits)',
                      c[:2], required(c[:2]), c[:4], required(c[:4]), 'HS 2022'] for c in sorted(codes)]
        sheets.append(('Code names', table('Code, heading and chapter names', 'Local review wording from the pinned UNSD H6 catalogue. Full wording is reference material; it does not validate a product mapping.',
                       ['Code','Full code name','Level','Chapter','Chapter name','Heading','Heading name','Edition'], code_rows, [12,95,24,12,65,12,80,15])))
    guide = [
        ['The project', 'HSGraph links materials, processes and products. HS codes classify product records; they are one layer of the graph.'],
        ['The website and Excel', 'Two reading views of the same data. Company software could consume the structured data directly.'],
        ['Explore more', 'The website lets you select a product, open its linked process, and follow included inputs or downstream uses. This workbook keeps the same links in tables.'],
        ['Scope', graph['scope']], ['What the links mean', graph['meaning']],
        ['Coverage', 'This is a sample of 1,422 published process models, not a map of every industry. Missing connections stay unknown.'],
        ['HS hierarchy', 'Chapter (2 digits) → heading (4 digits) → subheading (6 digits). This is a category tree. Production links come from separate source evidence.'],
        ['Countries', 'The examples use HS 2022 international categories. Country-specific tariff extensions and filing decisions require their own evidence.'],
        ['Human review', 'Published v0.1.0 has zero specialist validations. Its one owner acceptance belongs to an exact original cement revision and instance; it does not accept the chain or later revisions.'],
        ['CHA involvement', 'A CHA or other classification specialist can review the exact product, country rules and supporting documents. A clear graph or agreement that the problem exists does not validate a code.'],
        ['Quantities', 'Native units, formulas and model boundaries remain in the accompanying JSON. No quantities have been multiplied into a bill of materials.'],
        ['Reading source descriptions', 'Descriptions retain source wording and may contain unresolved inconsistencies. For example, the film description and its waste record name different disposal routes.'],
        ['Data files', 'production-graph.json holds the view; production-evidence.json retains unchanged source records, source line numbers and hashes. The ten example JSON files retain their full assessments.'],
        ['Review copy' if names else 'Wording', 'Local review only: the optional catalogue descriptions do not have new public redistribution approval.' if names else 'This public workbook retains the release’s description-free HS catalogue boundary. Product and process names are included under the source terms.'],
        ['Credits', 'Rizwan Bedekar / HSGraph. DOE / NREL / Alliance for Sustainable Energy and USLCI contributors; other credits and complete terms appear in Source notices.'],
        ['Release', graph['source_release']], ['Project', 'https://github.com/r-bedekar/hsgraph-open']]
    if reading_sheets:
        guide.append(['Product examples', 'The previous 15 simple examples and their suggested next checks are retained, along with the blank limit-switch / slit-coil case forms and original evidence. These do not add production links.'])
    sheets.append(('How to read', table('Read the graph in plain language', 'Start with the diagram, then use the process and link sheets. Keep source terms with this workbook when sharing.', ['Topic','Explanation'], guide, [28,125])))
    sheets.append(('Source references', table('Trace each record to the source', 'The short record numbers are navigation aids in this workbook. Full IDs and source line hashes below preserve traceability.',
                    ['Workbook record','Full source ID','Source file','Line','SHA-256 of original line'], refs, [20,110,32,12,75])))
    notice_rows = []
    for name, text in sorted(notices.items()):
        text = text.decode() if isinstance(text, bytes) else text
        # Preserve exact concatenated text while keeping each cell and row readable.
        for offset in range(0, len(text), 1200):
            notice_rows.append([name, str(offset), text[offset:offset+1200]])
    sheets.append(('Source notices', table('Source terms and attribution', 'Full text retained in ordered chunks. Join the chunks for a file without adding separators. Original files are also supplied with the HTML package.',
                   ['File','Character offset','Original notice text'], notice_rows, [45,18,145])))
    return package(sheets)


def package(sheets):
    fonts = [('<sz val="11"/><color rgb="FF172A3A"/>'),
             ('<b/><sz val="24"/><color rgb="FF172A3A"/>'),
             ('<b/><sz val="11"/><color rgb="FFFFFFFF"/>'),
             ('<b/><sz val="12"/><color rgb="FFFFFFFF"/>'),
             ('<sz val="24"/><color rgb="FF506474"/>')]
    fills = ['<patternFill patternType="none"/>','<patternFill patternType="gray125"/>'] + [f'<patternFill patternType="solid"><fgColor rgb="FF{c}"/><bgColor indexed="64"/></patternFill>' for c in ['EDF2F6','355A74','E7F3EE','FFF1D8']]
    pairs = [(0,0),(1,0),(2,3),(0,2),(3,3),(0,4),(0,5),(4,0)]
    styles = f'<styleSheet xmlns="{NS}"><fonts count="{len(fonts)}">' + ''.join('<font><name val="Aptos"/>'+f+'</font>' for f in fonts) + f'</fonts><fills count="{len(fills)}">' + ''.join('<fill>'+f+'</fill>' for f in fills) + '</fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    styles += f'<cellXfs count="{len(pairs)}">' + ''.join(f'<xf numFmtId="49" fontId="{font}" fillId="{fill}" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment wrapText="1" vertical="center" horizontal="{ "center" if i==7 else "left"}" indent="{0 if i==7 else 1}"/></xf>' for i,(font,fill) in enumerate(pairs)) + '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'
    files = {
        'xl/styles.xml': styles,
        'xl/workbook.xml': f'<workbook xmlns="{NS}" xmlns:r="{REL}"><bookViews><workbookView activeTab="0"/></bookViews><sheets>' + ''.join(f'<sheet name={quoteattr(name)} sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1)) + '</sheets></workbook>',
        'xl/_rels/workbook.xml.rels': f'<Relationships xmlns="{PKG}">' + ''.join(f'<Relationship Id="rId{i}" Type="{REL}/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1)) + f'<Relationship Id="styles" Type="{REL}/styles" Target="styles.xml"/></Relationships>',
        '_rels/.rels': f'<Relationships xmlns="{PKG}"><Relationship Id="main" Type="{REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1)) + '</Types>'}
    files.update({f'xl/worksheets/sheet{i}.xml': xml for i,(_,xml) in enumerate(sheets,1)})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026,10,1,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data.encode())
    return stream.getvalue()
