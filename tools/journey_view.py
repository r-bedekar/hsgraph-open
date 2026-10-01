"""Progressively enhanced reading journey; original classification evidence stays intact."""
from html import escape
from html.parser import HTMLParser


def extract_sections(document):
    """Retain exact section markup, including nested record sections and escaping."""
    offsets = [0]
    for line in document.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    class Sections(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.stack, self.sections = [], {}

        def index(self):
            line, column = self.getpos()
            return offsets[line-1] + column

        def handle_starttag(self, tag, attrs):
            if tag == 'section':
                self.stack.append((dict(attrs).get('id'), self.index()))

        def handle_endtag(self, tag):
            if tag == 'section':
                name, start = self.stack.pop()
                if name:
                    self.sections[name] = document[start:self.index()+len('</section>')]

    parser = Sections(); parser.feed(document)
    if parser.stack:
        raise ValueError('Unclosed source presentation section')
    return parser.sections


def render_journey(document, rows, graph_html):
    """Keep long-form source details available while giving each reading step one job."""
    source = extract_sections(document)
    head = document.split('</head>',1)[0]
    options = ''.join(f'<option value="{escape(r["row_id"])}">{escape(r["row_id"]+" · "+r["source_declared_product"])}</option>' for r in rows)
    records = ''.join(source[r['row_id']] for r in rows)

    def next_link(target, label, previous=None):
        back = f'<a class="quiet-link" href="#{previous}">Previous step</a>' if previous else '<span>Take it one step at a time, or jump ahead above.</span>'
        return f'<div class="journey-actions">{back}<a class="button" href="#{target}">{label} <span aria-hidden="true">→</span></a></div>'

    return (head + '''</head><body><div class="wrap journey-page">
<header class="site-header"><a class="brand-mark" href="#overview">HSGraph<span>A shared map of production</span></a><a class="header-download" href="production-graph.xlsx">Get the Excel file <span aria-hidden="true">↗</span></a></header>
<nav class="journey-nav" aria-label="Your journey through HSGraph">
<a href="#overview" data-step-link="overview"><span class="step-number">1</span><span>Understand the map<small>What HSGraph connects</small></span></a>
<a href="#graph" data-step-link="graph"><span class="step-number">2</span><span>Follow a chain<small>Inputs, process, outputs</small></span></a>
<a href="#classification" data-step-link="classification"><span class="step-number">3</span><span>Check the HS link<small>See what is still open</small></span></a>
<a href="#use-data" data-step-link="use-data"><span class="step-number">4</span><span>Put it to use<small>For people and software</small></span></a>
</nav><main id="journey-main">
<section id="overview" class="journey-step" data-step="overview" aria-labelledby="overview-title">
<div class="overview-grid"><div id="guide" class="overview-copy"><p class="step-caption">Step 1 of 4 · The idea</p><h1 id="overview-title" tabindex="-1">See how products connect.</h1><p class="lede">HSGraph connects <strong>materials, the processes that use them, and the products they make.</strong> Each product can also link to an HS code and the evidence behind it.</p><div class="purpose-note"><strong>The graph is the project.</strong><p>This website and Excel help people read it. Company software can build on the same structured data.</p></div></div>
<div class="map-primer" role="group" aria-label="The idea: materials enter a process, which makes a product. Products can feed a next process and have HS links.">
<p class="primer-title">Read the map like this</p><div class="primer-chain"><div class="primer-node"><span>Materials</span><small>What goes in</small></div><span class="primer-arrow" aria-hidden="true">→</span><div class="primer-node primer-process"><span>Process</span><small>What happens</small></div><span class="primer-arrow" aria-hidden="true">→</span><div class="primer-node"><span>Product</span><small>What comes out</small></div></div>
<div class="primer-fork"><div class="primer-next"><span aria-hidden="true">↳</span><strong>Next process</strong><small>Where the product is used</small></div><div class="primer-code"><strong>HS code + evidence</strong><small>Attached to the product record</small></div></div><p class="primer-foot">Every connection needs a source. A matching name or code alone does not create a link.</p></div></div>
<div class="question-strip"><div><strong>What goes into it?</strong><span>Follow the recorded inputs.</span></div><div><strong>How is it made?</strong><span>Open the process behind it.</span></div><div><strong>What needs checking?</strong><span>See the code, evidence and missing facts.</span></div></div>
''' + next_link('graph','Explore a real chain') + '''</section>
''' + graph_html + '''
<section id="classification" class="journey-step" data-step="classification" aria-labelledby="classification-title">
<div class="step-heading"><div><p class="step-caption">Step 3 of 4 · The classification link</p><h2 id="classification-title" tabindex="-1">A product’s code can stay open.</h2></div><p>A production record tells us what was used or made. Choosing its HS category may need more facts.</p></div>
<div class="classification-intro"><div id="code-tree" class="info-block"><h3>How the HS tree works</h3><div class="category-path"><span>Chapter<small>2 digits</small></span><b aria-hidden="true">→</b><span>Heading<small>4 digits</small></span><b aria-hidden="true">→</b><span>Subheading<small>6 digits</small></span></div><p>The production links show how things are made. The HS tree groups products into categories.</p></div><div class="info-block question-block"><h3>What happens when facts are missing?</h3><p>Keep the possible codes, show the missing fact, and leave the match open for review.</p><strong>A clear question helps the next conversation with a CHA or other specialist.</strong></div></div>
''' + source.get('example','') + '''
<details class="read-more"><summary>How the evidence and review states are kept separate</summary>''' + source['how'] + '''</details>
<section id="examples" class="record-browser"><div class="record-browser-heading"><div><h3>Explore another saved record</h3><p>Ten selected examples. Their codes are proposals, with no specialist validation.</p></div><label for="example-picker">Choose a product<select id="example-picker">''' + options + '''</select></label></div><div class="record-cases">''' + records + '''</div></section>
''' + next_link('use-data','See how to use the data','graph') + '''</section>
<section id="use-data" class="journey-step" data-step="use-data" aria-labelledby="use-title"><div class="step-heading"><div><p class="step-caption">Step 4 of 4 · Your next step</p><h2 id="use-title" tabindex="-1">One graph. Different ways to use it.</h2></div><p>These are uses we are building towards. The downloads show the records and connections available today.</p></div>
<div id="uses" class="use-columns"><article><span class="use-symbol" aria-hidden="true">▦</span><h3>ERP and procurement</h3><p>Connect product records to their documented inputs and classification evidence.</p></article><article><span class="use-symbol" aria-hidden="true">≡</span><h3>RFPs and supplier discussions</h3><p>Find the specifications to ask for and make the open questions clear.</p></article><article><span class="use-symbol" aria-hidden="true">⇄</span><h3>Manufacturing planning</h3><p>Explore recorded production routes, what they use, and where the evidence stops.</p></article></div>
<section id="downloads" class="download-section"><h3>Choose how you want to explore</h3><div class="download-grid"><a class="download-card" href="production-graph.xlsx"><span class="download-type">For people</span><strong>Open the Excel workbook <span aria-hidden="true">↗</span></strong><span>Start with the diagram, then read the processes, links and examples.</span></a><a class="download-card" href="production-graph.json"><span class="download-type">For software</span><strong>Get the graph as JSON <span aria-hidden="true">↗</span></strong><span>Use the structured processes, product records and source links.</span></a></div><div class="resource-links"><a href="samples.csv">Classification examples (CSV)</a><a href="samples.json">Examples (JSON)</a><a href="production-evidence.json">Graph source records</a><a href="https://doi.org/10.5281/zenodo.22857372">Full dataset</a><a href="https://github.com/r-bedekar/hsgraph-open">Project on GitHub</a></div></section>
<div class="scope-note"><strong>Use the evidence within its scope.</strong><p>Process models describe recorded relationships. They do not identify actual suppliers or establish that products are interchangeable. Proposed codes still need specialist review before being relied on.</p></div>
<details class="read-more"><summary>What is in the full dataset, and what are its limits?</summary>''' + source['dataset'] + source['limits'] + '''</details>
<details class="read-more"><summary>Share feedback on a record</summary>''' + source['feedback'] + '''</details>
<details class="read-more"><summary>Source terms and verification</summary><p>Share the data with its source notices. The underlying records and saved findings are unchanged.</p><div class="resource-links"><a href="README.md">Selection and verification guide</a><a href="LICENSE-DATA">Component-specific terms</a><a href="sample-manifest.json">Package manifest</a></div></details>
''' + next_link('graph','Return to the graph','classification') + '''</section></main>
<footer>HSGraph · A graph of documented production relationships.<span>Credit: Rizwan Bedekar / HSGraph; DOE / NREL / Alliance for Sustainable Energy; USLCI contributors and other credited sources. See the included notices.</span></footer></div>
<script src="assets/journey.js?v=5" defer></script></body></html>''').encode()
