/* Responsive process neighbourhood. Only explicit source links are navigable. */
(() => {
  'use strict';
  const payload=document.getElementById('production-data');if(!payload)return;
  const graph=JSON.parse(payload.textContent);
  const canvas=document.getElementById('graph-canvas'),panel=document.getElementById('graph-detail');
  const back=document.getElementById('graph-back'),history=[graph.roots[0].id];
  const narrow=matchMedia('(max-width: 800px)');
  let allInputs=false,allOutputs=false,scene=null,frame;
  const names=Object.fromEntries(graph.roots.map(r=>[r.id,r.label==='Stretch film'?'Make stretch film':r.label==='Portland cement'?'Make Portland cement':'Precision sand casting']));
  const states={ambiguous:'More than one code remains possible',applicable:'The saved checks pass for this proposal',insufficient_information:'Information is missing',conflicting:'A conflict needs review'};
  function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
  function short(name){return name.replace(/; at (plant|mine|mill|refinery|extraction|manufacturer)$/,'').replace(/; production mix(ture)?/,'');}
  function processName(id){return names[id]||short(graph.processes[id].name);}
  function codes(f){return [...new Set(f.mappings.flatMap(m=>m.target?[m.target.code]:m.alternatives.map(t=>t.code)))];}
  function sourceDetail(parent,source,content=[]){
    const d=el('details','source-detail');d.append(el('summary','','Source details'));
    content.forEach(text=>{if(text)d.append(el('p','',text));});
    d.append(el('p','graph-source',`${source.source_artifact}, record ${source.source_line}.`));
    const a=el('a','','Open the saved source records');a.href='production-evidence.json';d.append(a);parent.append(d);
  }
  function action(label,id,cls='graph-action'){
    const button=el('button',cls,label);button.type='button';button.dataset.processId=id;
    button.onclick=()=>openProcess(id);return button;
  }
  function showProcess(id,scroll=false){
    const p=graph.processes[id];panel.replaceChildren(el('p','graph-kind','Selected process'),el('h3','',processName(id)));
    const facts=el('div','detail-facts');
    for(const [value,label] of [[p.inputs.length,'recorded inputs'],[p.outputs.length,'recorded outputs']]){
      const item=el('span');item.append(el('strong','',String(value)),document.createTextNode(' '+label));facts.append(item);
    }
    panel.append(facts,el('p','muted','Open an input to see its source process, or an output to see where it is used next.'));
    sourceDetail(panel,p.source,[p.description||'No description supplied.',
      `Source dates: ${p.valid_from||'unknown start'} to ${p.valid_until||'unknown end'}.`,p.completeness,
      `${p.environmental_exchanges} natural-resource and emission records are counted separately. Linked models do not identify actual suppliers.`]);
    if(scroll)panel.scrollIntoView({block:'nearest'});
  }
  function showFlow(id){
    const f=graph.flows[id];panel.replaceChildren(el('p','graph-kind',f.is_input?'Selected input':'Selected output'),el('h3','',f.name));
    const columns=el('div','detail-columns'),classification=el('div'),connections=el('div');
    classification.append(el('h4','','HS link'));
    if(!f.mappings.length)classification.append(el('p','','No HS proposal is recorded for this exact product record.'));
    for(const m of f.mappings){
      const targets=m.target?[m.target]:m.alternatives;
      classification.append(el('strong','detail-code',targets.length?'HS '+targets.map(t=>t.code).join(' / '):'No code selected'),el('p','',states[m.outcome]||m.outcome));
      for(const t of targets)classification.append(el('p','category-caption',`Chapter ${t.code.slice(0,2)} → heading ${t.code.slice(0,4)}`+(t.code.length===6?` → subheading ${t.code}`:'')+` (HS ${t.edition||'2022'}).`));
    }
    classification.append(el('p','muted','No specialist validation is recorded.'));
    for(const d of f.owner_decisions)classification.append(el('p','muted',`An owner decision applies to original revision ${d.mapping_id} only, not later versions or the chain.`));
    connections.append(el('h4','',f.is_input?'Where this input comes from':'Where this output is used'));
    if(f.is_input){
      const p=f.provider;
      if(p?.can_follow)connections.append(el('p','','The source explicitly links this input to a process model and its matching output.'),action('Explore '+processName(p.process_id),p.process_id));
      else connections.append(el('p','graph-stop-note',!p?'No provider link is recorded.':p.traversable?'The linked process is outside this sample.':'The link stops here: '+[p.status,...p.stops].join('; ').replaceAll('_',' ')+'.'));
    }else{
      const consumers=[...new Set(f.consumers.map(c=>c.process_id))];
      if(consumers.length)consumers.forEach(pid=>connections.append(action(processName(pid),pid)));
      else connections.append(el('p','','No further use is included in this sample. Other uses may exist.'));
    }
    columns.append(classification,connections);panel.append(columns);
    const quantity=f.amount===null||f.amount===undefined?'':`Source amount: ${f.amount} ${f.unit||'(unit unavailable)'}. This uses the source process’s own reference amount. Quantities have not been combined along the chain.`;
    sourceDetail(panel,f.source,[`${f.is_input?'Input to':'Output of'} ${graph.processes[f.process_id].name}.`,quantity,f.formula?'Unevaluated source formula: '+f.formula:'']);
    panel.scrollIntoView({block:'nearest'});
  }
  function processCard(id){
    const button=el('button','graph-node graph-process');button.type='button';button.setAttribute('aria-controls','graph-detail');
    button.append(el('span','graph-kind','Production process'),el('strong','',processName(id)),el('span','graph-node-hint','View process details'));
    button.onclick=()=>showProcess(id,true);return button;
  }
  function flowCard(id){
    const f=graph.flows[id],bundle=el('div','flow-bundle');
    const button=el('button','graph-node graph-product'+(f.flow_type==='WASTE_FLOW'?' graph-waste':''));
    button.type='button';button.dataset.flowId=id;button.setAttribute('aria-controls','graph-detail');button.setAttribute('aria-pressed','false');
    button.append(el('span','graph-kind',f.flow_type==='WASTE_FLOW'?'Waste':f.is_input?'Material or service':'Product'),el('strong','',short(f.name)));
    const cs=codes(f);button.append(el('span','graph-code',cs.length?'HS '+cs.join(' / ')+' · proposed':'HS link not recorded'));
    button.onclick=()=>{canvas.querySelectorAll('[data-flow-id]').forEach(n=>n.setAttribute('aria-pressed',String(n===button)));showFlow(id);};
    bundle.append(button);
    if(f.is_input){
      if(f.provider?.can_follow){
        const link=action('From: '+processName(f.provider.process_id),f.provider.process_id,'graph-provider');
        link.setAttribute('aria-label','Explore source process: '+processName(f.provider.process_id));bundle.append(link);
      }else bundle.append(el('p','graph-boundary',!f.provider?'No provider link recorded':f.provider.traversable?'Linked process outside this sample':'Source link stops here · select for details'));
    }else{
      const consumers=[...new Set(f.consumers.map(c=>c.process_id))];
      if(consumers.length){bundle.append(action('Next use: '+processName(consumers[0]),consumers[0],'graph-provider graph-consumer'));if(consumers.length>1)bundle.append(el('span','graph-node-hint',`Select the product to see all ${consumers.length} linked uses.`));}
    }
    return bundle;
  }
  function expandButton(kind,total){
    const expanded=kind==='inputs'?allInputs:allOutputs;
    const button=el('button','graph-expand',expanded?'Show fewer '+kind:`Show all ${total} ${kind}`);button.type='button';button.dataset.expand=kind;button.setAttribute('aria-expanded',String(expanded));
    button.onclick=()=>{if(kind==='inputs')allInputs=!allInputs;else allOutputs=!allOutputs;draw();canvas.querySelector(`[data-expand="${kind}"]`)?.focus();};return button;
  }
  function draw(){
    const id=history[history.length-1],p=graph.processes[id];back.disabled=history.length===1;
    document.querySelectorAll('[data-root]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.root===id)));
    const heading=el('h3','',processName(id));heading.tabIndex=-1;
    document.getElementById('graph-context').replaceChildren(heading,el('p','graph-context-note',history.length>1?'Following: '+history.slice(-3).map(processName).join(' → '):(narrow.matches?'Read top to bottom.':'Read left to right.')+' “From” and “Next use” follow explicit links in the source.'));
    const inputs=[...p.inputs].sort((a,b)=>Number(graph.flows[b].mappings.length>0)-Number(graph.flows[a].mappings.length>0)||Number(!!graph.flows[b].provider?.can_follow)-Number(!!graph.flows[a].provider?.can_follow)||graph.flows[a].name.localeCompare(graph.flows[b].name));
    const outputs=[...p.outputs].sort((a,b)=>Number(graph.flows[b].reference_output)-Number(graph.flows[a].reference_output)||Number(graph.flows[a].flow_type==='WASTE_FLOW')-Number(graph.flows[b].flow_type==='WASTE_FLOW'));
    const inputLimit=narrow.matches?1:3,outputLimit=narrow.matches?1:2;
    const visibleInputs=allInputs?inputs:inputs.slice(0,inputLimit),visibleOutputs=allOutputs?outputs:outputs.slice(0,outputLimit);
    document.getElementById('graph-count').textContent=`Showing ${visibleInputs.length} of ${inputs.length} inputs · ${visibleOutputs.length} of ${outputs.length} outputs`;
    canvas.replaceChildren();scene=el('div','graph-scene');
    const inputLane=el('div','graph-lane graph-inputs'),middle=el('div','graph-middle'),outputLane=el('div','graph-lane graph-outputs');
    inputLane.append(el('h4','graph-column-label','What goes in'));visibleInputs.forEach(eid=>inputLane.append(flowCard(eid)));
    if(!inputs.length)inputLane.append(el('p','graph-boundary','No product or service inputs recorded.'));
    if(inputs.length>inputLimit)inputLane.append(expandButton('inputs',inputs.length));
    middle.append(el('span','mobile-connector','↓ used in this process'),processCard(id),el('span','mobile-connector','↓ produces these outputs'));
    outputLane.append(el('h4','graph-column-label','What comes out'));visibleOutputs.forEach(eid=>outputLane.append(flowCard(eid)));
    if(!outputs.length)outputLane.append(el('p','graph-boundary','No product or waste outputs recorded.'));
    if(outputs.length>outputLimit)outputLane.append(expandButton('outputs',outputs.length));
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.classList.add('graph-lines');svg.setAttribute('aria-hidden','true');
    scene.append(svg,inputLane,middle,outputLane);canvas.append(scene);scheduleLines();
  }
  function scheduleLines(){cancelAnimationFrame(frame);frame=requestAnimationFrame(drawLines);}
  function drawLines(){
    if(!scene||!scene.clientWidth)return;
    const svg=scene.querySelector('svg'),rect=scene.getBoundingClientRect(),central=scene.querySelector('.graph-process').getBoundingClientRect();
    svg.setAttribute('viewBox',`0 0 ${rect.width} ${rect.height}`);svg.replaceChildren();
    const NS='http://www.w3.org/2000/svg';const defs=document.createElementNS(NS,'defs'),marker=document.createElementNS(NS,'marker'),tip=document.createElementNS(NS,'path');
    marker.setAttribute('id','graph-arrow');marker.setAttribute('viewBox','0 0 10 10');marker.setAttribute('refX','9');marker.setAttribute('refY','5');marker.setAttribute('markerWidth','5');marker.setAttribute('markerHeight','5');marker.setAttribute('orient','auto');tip.setAttribute('d','M 0 0 L 10 5 L 0 10 z');tip.setAttribute('fill','currentColor');marker.append(tip);defs.append(marker);svg.append(defs);
    function line(from,to){
      const x1=from.right-rect.left,y1=from.top+from.height/2-rect.top,x2=to.left-rect.left,y2=to.top+to.height/2-rect.top;
      const bend=Math.max(12,(x2-x1)/2),path=document.createElementNS(NS,'path');path.setAttribute('d',`M ${x1} ${y1} C ${x1+bend} ${y1}, ${x2-bend} ${y2}, ${x2} ${y2}`);path.setAttribute('class','flow-line');path.setAttribute('marker-end','url(#graph-arrow)');svg.append(path);
    }
    scene.querySelectorAll('.graph-inputs .graph-product').forEach(n=>line(n.getBoundingClientRect(),central));
    scene.querySelectorAll('.graph-outputs .graph-product').forEach(n=>line(central,n.getBoundingClientRect()));
  }
  function openProcess(id,reset=false){
    if(!graph.processes[id])return;
    if(reset)history.splice(0,history.length,id);else if(history.at(-1)!==id)history.push(id);
    allInputs=false;allOutputs=false;draw();showProcess(id);
    if(!reset){const heading=document.querySelector('#graph-context h3');heading.focus({preventScroll:true});heading.scrollIntoView({block:'nearest'});}
  }
  document.querySelectorAll('[data-root]').forEach(b=>b.onclick=()=>openProcess(b.dataset.root,true));
  back.onclick=()=>{history.pop();allInputs=false;allOutputs=false;draw();showProcess(history.at(-1));};
  new ResizeObserver(scheduleLines).observe(canvas);
  narrow.addEventListener('change',draw);
  document.addEventListener('hsgraph:step',scheduleLines);addEventListener('resize',scheduleLines);
  draw();document.fonts?.ready.then(scheduleLines);
})();
