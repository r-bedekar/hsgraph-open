/* Local, dependency-free reader of the published graph projection. */
(() => {
  'use strict';
  const payload = document.getElementById('production-data');
  if (!payload) return;
  const graph = JSON.parse(payload.textContent);
  const canvas = document.getElementById('graph-canvas');
  const panel = document.getElementById('graph-detail');
  const all = document.getElementById('graph-all');
  const back = document.getElementById('graph-back');
  const history = [graph.roots[0].id];
  const processNames = Object.fromEntries(graph.roots.map(r => [r.id, r.label === 'Stretch film' ? 'Make stretch film' : r.label === 'Portland cement' ? 'Make Portland cement' : 'Precision sand casting']));
  const status = {ambiguous:'More than one code', applicable:'Proposal passes saved checks', insufficient_information:'Information missing', conflicting:'Conflict needs review'};
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function shortName(name) { return name.replace(/; at (plant|mine|mill|refinery|extraction)$/, '').replace(/; production mix(ture)?/, ''); }
  function processName(id) { return processNames[id] || shortName(graph.processes[id].name); }
  function codes(flow) {
    return [...new Set(flow.mappings.flatMap(m => m.target ? [m.target.code] : m.alternatives.map(t => t.code)))];
  }
  function sourceLine(parent, source) {
    const p=el('p','graph-source',`Source: ${source.source_artifact}, record ${source.source_line}. `);
    const a=el('a','', 'Open the saved records'); a.href='production-evidence.json'; p.append(a); parent.append(p);
  }
  function openProcess(id, reset=false) {
    if (!graph.processes[id]) return;
    if (reset) history.splice(0,history.length,id); else if (history[history.length-1] !== id) history.push(id);
    all.checked=false; draw(); showProcess(id);
  }
  function showProcess(id, scroll=false) {
    const p=graph.processes[id]; panel.replaceChildren(el('p','graph-kind','Production process'),el('h3','',processName(id)));
    panel.append(el('p','',p.description || 'The source does not supply a description.'));
    const dates=p.valid_from || p.valid_until ? `${p.valid_from || 'unknown start'} to ${p.valid_until || 'unknown end'}` : 'Not supplied';
    panel.append(el('p','muted',`Source dates: ${dates}. This is a recorded process model; its links do not identify actual suppliers.`));
    if(p.completeness) { const d=el('details'); d.append(el('summary','','What the source says about coverage'),el('p','',p.completeness));panel.append(d); }
    sourceLine(panel,p.source);
    if(scroll)panel.scrollIntoView({block:'nearest'});
  }
  function action(text, id) { const b=el('button','graph-action',text); b.type='button'; b.onclick=()=>openProcess(id); return b; }
  function showFlow(id) {
    const f=graph.flows[id]; panel.replaceChildren(el('p','graph-kind',f.is_input?'Recorded input':'Recorded output'),el('h3','',f.name));
    panel.append(el('p','',f.is_input ? `This record is an input to ${processName(f.process_id)}.` : `This record is an output of ${processName(f.process_id)}.`));
    if (!f.mappings.length) panel.append(el('p','','No HS code has been proposed for this exact record.'));
    for (const m of f.mappings) {
      const cs=m.target ? m.target.code : m.alternatives.map(t=>t.code).join(' or ');
      panel.append(el('p','',`HS ${cs || 'not selected'} — ${status[m.outcome] || m.outcome}. No specialist validation is recorded.`));
      for(const t of (m.target ? [m.target] : m.alternatives)) {
        const path=`Chapter ${t.code.slice(0,2)} → heading ${t.code.slice(0,4)}`+(t.code.length===6?` → subheading ${t.code}`:'');
        panel.append(el('p','graph-code',`${path} (HS ${t.edition || '2022'}).`));
      }
    }
    for(const d of f.owner_decisions) panel.append(el('p','',`An owner decision exists for original revision ${d.mapping_id} only. It does not accept later versions or the production chain.`));
    const p=f.provider;
    if(p && p.can_follow) {
      panel.append(el('p','','The source names a process model for this input and identifies its matching output.'));
      panel.append(action(`Explore ${processName(p.process_id)}`,p.process_id));
    } else if(f.is_input) {
      const message=!p?'No provider link is recorded for this input.':p.traversable?'Its linked process is outside this sample.':`The link stops here: ${[p.status,...p.stops].join('; ').replaceAll('_',' ')}.`;
      panel.append(el('p','graph-stop-note',message));
    }
    const consumers=[...new Set(f.consumers.map(c=>c.process_id))];
    if(consumers.length){ panel.append(el('h4','','Where this output is used in the sample')); for(const id of consumers)panel.append(action(processName(id),id)); }
    else if(!f.is_input)panel.append(el('p','muted','No further use is included in this view. That does not mean no use exists.'));
    if(f.amount!==null && f.amount!==undefined)panel.append(el('p','muted',`Source amount: ${f.amount} ${f.unit || '(unit unavailable)'}. This belongs to the source process’s own reference amount; quantities have not been combined along the graph.${f.formula ? ' The source has an unevaluated formula: '+f.formula+'.' : ''}`));
    sourceLine(panel,f.source);
    panel.scrollIntoView({block:'nearest'});
  }
  function processCard(id, provider=false) {
    const b=el('button','graph-node graph-process'+(provider?' graph-provider':''));b.type='button';
    b.append(el('span','graph-kind',provider?'Linked process':'Production process'),el('strong','',processName(id)),el('span','graph-node-hint',provider?'Explore its inputs':'View the source description'));
    b.onclick=()=>provider?openProcess(id):showProcess(id,true);return b;
  }
  function flowCard(id) {
    const f=graph.flows[id], b=el('button','graph-node graph-product'+(f.flow_type==='WASTE_FLOW'?' graph-waste':''));b.type='button';b.dataset.flowId=id;
    b.append(el('span','graph-kind',f.flow_type==='WASTE_FLOW'?'Waste output':f.is_input?'Input: material or service':'Product output'),el('strong','',shortName(f.name)));
    const cs=codes(f);b.append(el('span','graph-code',cs.length?'HS '+cs.join(' / ')+' · proposed':'HS link not recorded'));
    if(f.consumers.length)b.append(el('span','graph-node-hint',`Used in ${new Set(f.consumers.map(c=>c.process_id)).size} linked process(es) · view next steps`));
    b.onclick=()=>{canvas.querySelectorAll('.graph-node').forEach(n=>n.classList.remove('selected'));b.classList.add('selected');showFlow(id);};return b;
  }
  function draw(){
    const id=history[history.length-1],p=graph.processes[id];back.disabled=history.length===1;
    document.querySelectorAll('[data-root]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.root===id)));
    document.getElementById('graph-context').replaceChildren(el('h3','',processName(id)),el('p','muted',`${p.inputs.length} recorded inputs · ${p.outputs.length} outputs · ${p.environmental_exchanges} environmental exchanges counted separately`));
    let inputs=[...p.inputs].sort((a,b)=>Number(graph.flows[b].mappings.length>0)-Number(graph.flows[a].mappings.length>0)||Number(!!graph.flows[b].provider?.can_follow)-Number(!!graph.flows[a].provider?.can_follow)||graph.flows[a].name.localeCompare(graph.flows[b].name));
    const visible=all.checked?inputs:inputs.slice(0,6);
    document.getElementById('graph-count').textContent=visible.length<inputs.length?`Showing ${visible.length} of ${inputs.length} inputs`:'All recorded inputs shown';
    canvas.replaceChildren();
    const outputs=[...p.outputs].sort((a,b)=>Number(graph.flows[b].reference_output)-Number(graph.flows[a].reference_output)||Number(graph.flows[a].flow_type==='WASTE_FLOW')-Number(graph.flows[b].flow_type==='WASTE_FLOW'));
    if(matchMedia('(max-width: 760px)').matches){
      canvas.classList.add('graph-mobile');
      canvas.append(el('h4','','Inputs to this process'));
      for(const eid of visible){const f=graph.flows[eid],group=el('div','mobile-input');if(f.provider?.can_follow){group.append(processCard(f.provider.process_id,true),el('span','mobile-connector','↓ supplies this input'));}group.append(flowCard(eid));canvas.append(group);}
      canvas.append(el('div','mobile-connector','↓ inputs feed the process'),processCard(id),el('div','mobile-connector','↓ recorded outputs'));
      for(const eid of outputs)canvas.append(flowCard(eid));return;
    }
    canvas.classList.remove('graph-mobile');
    const scene=el('div','graph-scene');
    const SVG='http://www.w3.org/2000/svg'; const svg=document.createElementNS(SVG,'svg');svg.setAttribute('aria-hidden','true');svg.setAttribute('class','graph-lines');
    svg.innerHTML='<defs><marker id="graph-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>';
    scene.append(svg);canvas.append(scene);
    function place(node,x,y,w=250){node.style.left=x+'px';node.style.top=y+'px';node.style.width=w+'px';scene.append(node);return {node,x,y,w};}
    function line(a,b,provider=false){const path=document.createElementNS(SVG,'path'),ay=a.y+a.node.offsetHeight/2,by=b.y+b.node.offsetHeight/2;path.setAttribute('d',`M ${a.x+a.w} ${ay} C ${a.x+a.w+35} ${ay}, ${b.x-35} ${by}, ${b.x} ${by}`);path.setAttribute('class',provider?'provider-line':'flow-line');path.setAttribute('marker-end','url(#graph-arrow)');svg.append(path);}
    [['Linked processes',12],['Inputs',295],['Production process',590],['Outputs',895]].forEach(([name,x])=>{const l=el('div','graph-column-label',name);l.style.left=x+'px';scene.append(l);});
    const center=place(processCard(id),590,Math.min(210,58+Math.max(visible.length,outputs.length)*40),240);
    let inputY=58,outputY=58;
    visible.forEach(eid=>{const f=graph.flows[eid],card=place(flowCard(eid),295,inputY,260);line(card,center);let rowHeight=card.node.offsetHeight;
      if(f.provider?.can_follow){const provider=place(processCard(f.provider.process_id,true),12,inputY,240);line(provider,card,true);rowHeight=Math.max(rowHeight,provider.node.offsetHeight);}
      else{const text=!f.provider?'No provider link recorded':f.provider.traversable?'Linked process is outside this view':'Provider link stops here';place(el('div','graph-boundary',text),12,inputY+30,230);}
      inputY+=rowHeight+25;
    });
    outputs.forEach(eid=>{const card=place(flowCard(eid),895,outputY,270);line(center,card);outputY+=card.node.offsetHeight+25;});
    const height=Math.max(400,inputY,outputY)+20;scene.style.height=height+'px';svg.setAttribute('viewBox',`0 0 1180 ${height}`);
  }
  document.querySelectorAll('[data-root]').forEach(b=>b.onclick=()=>openProcess(b.dataset.root,true));
  all.onchange=draw;back.onclick=()=>{history.pop();all.checked=false;draw();showProcess(history[history.length-1]);};
  let resize;addEventListener('resize',()=>{clearTimeout(resize);resize=setTimeout(draw,100);});
  draw();document.fonts?.ready.then(draw);
})();
