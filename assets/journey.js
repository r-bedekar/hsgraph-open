/* A short reading journey with working deep links and a complete no-JS document. */
(() => {
  'use strict';
  const steps=[...document.querySelectorAll('.journey-step')];
  if(!steps.length)return;
  const picker=document.getElementById('example-picker');
  const cases=[...document.querySelectorAll('.record-cases .case')];
  function chooseCase(id){
    const selected=cases.find(c=>c.id===id)||cases[0];
    cases.forEach(c=>c.hidden=c!==selected);
    if(selected)picker.value=selected.id;
  }
  function reveal(hash,move=false){
    let name;try{name=decodeURIComponent(hash.replace(/^#/,''));}catch{name='overview';}
    const target=document.getElementById(name)||steps[0];
    const active=target.closest('.journey-step')||steps[0];
    steps.forEach(s=>s.hidden=s!==active);
    document.querySelectorAll('[data-step-link]').forEach(link=>{
      if(link.dataset.stepLink===active.id)link.setAttribute('aria-current','step');
      else link.removeAttribute('aria-current');
    });
    const record=target.closest('.case');if(record)chooseCase(record.id);
    for(let parent=target;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
    document.dispatchEvent(new CustomEvent('hsgraph:step',{detail:{id:active.id}}));
    if(move){
      const focus=target===active?active.querySelector('h1,h2'):target;
      if(focus){if(!focus.hasAttribute('tabindex'))focus.setAttribute('tabindex','-1');focus.focus({preventScroll:true});}
      (target===active?document.getElementById('journey-main'):target).scrollIntoView({block:'start'});
    }
  }
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href^="#"]');
    if(!link||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button!==0)return;
    const hash=link.getAttribute('href');if(hash==='#'||!document.getElementById(hash.slice(1)))return;
    event.preventDefault();if(location.hash!==hash)history.pushState(null,'',hash);reveal(hash,true);
  });
  picker.addEventListener('change',()=>{chooseCase(picker.value);history.pushState(null,'','#'+picker.value);});
  addEventListener('popstate',()=>reveal(location.hash));
  addEventListener('hashchange',()=>reveal(location.hash));
  chooseCase(cases[0]?.id);document.documentElement.classList.add('journey-ready');reveal(location.hash);
})();
