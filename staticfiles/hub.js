async function fetchPrompts(){
  try{
    const xmlRes = await fetch('/api/xml-prompts/').then(r=>r.json()).catch(()=>({prompts:[]}));
    const all = xmlRes.prompts || [];
    window.__ALL_PROMPTS__ = all;
    const {prompts, templates} = splitByType(all);
    renderGrid('prompts-grid', prompts);
    renderGrid('templates-grid', templates);
  }catch(err){
    console.error('Failed to load prompts', err);
  }
}

function createCard(prompt){
  const wrap = document.createElement('div');
  wrap.className = 'card clickable';

  const title = document.createElement('h3');
  title.textContent = prompt.title || 'Prompt';

  // Removed inline preview/description under title as requested

  const meta = document.createElement('div');
  meta.className = 'meta';
  if(prompt.category){
    const cat = document.createElement('span');
    cat.className = 'pill category';
    cat.textContent = prompt.category;
    meta.appendChild(cat);
  }
  if(Array.isArray(prompt.tags)){
    prompt.tags.slice(0,4).forEach(t => {
      const tag = document.createElement('span');
      tag.className = 'pill';
      tag.textContent = String(t);
      meta.appendChild(tag);
    });
  }
  if(prompt.role){
    const role = document.createElement('span');
    role.className = 'pill';
    role.textContent = prompt.role;
    meta.appendChild(role);
  }

  const content = document.createElement('pre');
  content.className = 'content';
  content.textContent = (prompt.preview || prompt.content || '');

  // Top-right copy icon
  const copyIcon = document.createElement('button');
  copyIcon.className = 'icon-btn copy-top';
  copyIcon.setAttribute('aria-label','Copy prompt');
  copyIcon.innerHTML = '📋';
  copyIcon.addEventListener('click', async (e)=>{
    e.stopPropagation();
    try{ await navigator.clipboard.writeText(String(prompt.content||'')); copyIcon.innerHTML='✔️'; setTimeout(()=>copyIcon.innerHTML='📋', 900);}catch(_e){}
  });
  wrap.appendChild(copyIcon);

  // Open modal on click
  wrap.addEventListener('click', ()=> {
    // navigate to dedicated page for a cleaner focus view
    const idx = Number(prompt.id||0) || 1;
    window.location.href = `/hub/p/${idx}/`;
  });

  wrap.appendChild(title);
  wrap.appendChild(meta);
  wrap.appendChild(content);

  // Rating controls (bottom-right)
  const ratingRow = document.createElement('div');
  ratingRow.className = 'rating-actions';

  function createRatingBtn(kind){
    const btn = document.createElement('button');
    btn.className = `rating-btn rating-btn--${kind}`;
    btn.setAttribute('aria-label', kind === 'up' ? 'Helpful' : 'Not Helpful');
    btn.title = kind === 'up' ? 'Helpful' : 'Not Helpful';
    const icon = document.createElement('span');
    icon.className = 'rating-icon';
    icon.textContent = kind === 'up' ? '👍' : '👎';
    const count = document.createElement('span');
    count.className = 'rating-count';
    btn.appendChild(icon);
    btn.appendChild(count);
    return {btn, count};
  }

  const {btn: upBtn, count: upCountEl} = createRatingBtn('up');
  const {btn: downBtn, count: downCountEl} = createRatingBtn('down');

  // Storage helpers per prompt
  const keyState = `prompt_feedback_${String(prompt.id||'')}`;
  const keyCounts = `prompt_feedback_counts_${String(prompt.id||'')}`;
  function readCounts(){
    try{ return JSON.parse(localStorage.getItem(keyCounts)||'{}'); }catch(_e){ return {}; }
  }
  function writeCounts(v){ try{ localStorage.setItem(keyCounts, JSON.stringify(v)); }catch(_e){} }
  function setState(v){ try{ if(v){ localStorage.setItem(keyState, v); } else { localStorage.removeItem(keyState); } }catch(_e){} }
  function getState(){ try{ return localStorage.getItem(keyState)||''; }catch(_e){ return ''; } }

  function syncUI(){
    const st = getState();
    const c = readCounts();
    const up = Number(c.up||0);
    const down = Number(c.down||0);
    upCountEl.textContent = String(up);
    downCountEl.textContent = String(down);
    upBtn.classList.toggle('is-active', st==='up');
    downBtn.classList.toggle('is-active', st==='down');
  }
  syncUI();

  function animate(btn){
    btn.classList.add('pulse');
    setTimeout(()=>btn.classList.remove('pulse'), 220);
  }

  function handleClick(kind){
    return (e)=>{
      e.stopPropagation();
      const st = getState();
      const c = readCounts();
      c.up = Number(c.up||0);
      c.down = Number(c.down||0);
      if(kind==='up'){
        if(st==='up'){ setState(''); c.up = Math.max(0, c.up-1); }
        else { setState('up'); c.up += 1; if(st==='down') c.down = Math.max(0, c.down-1); }
        writeCounts(c); syncUI(); animate(upBtn);
      }else{
        if(st==='down'){ setState(''); c.down = Math.max(0, c.down-1); }
        else { setState('down'); c.down += 1; if(st==='up') c.up = Math.max(0, c.up-1); }
        writeCounts(c); syncUI(); animate(downBtn);
      }
    };
  }

  upBtn.addEventListener('click', handleClick('up'));
  downBtn.addEventListener('click', handleClick('down'));

  ratingRow.appendChild(upBtn);
  ratingRow.appendChild(downBtn);
  wrap.appendChild(ratingRow);

  // no expandable detail – keep it simple per latest direction
  return wrap;
}

function renderGrid(targetId, prompts){
  const grid = document.getElementById(targetId);
  grid.innerHTML = '';
  prompts.forEach(p => grid.appendChild(createCard(p)));
}

function splitByType(items){
  const isTemplate = (item) => {
    const cat = (item.category || '').toLowerCase();
    const role = (item.role || '').toLowerCase();
    return cat === 'template' || cat === 'templates' || role === 'template';
  };
  const templates = items.filter(isTemplate);
  const prompts = items.filter(i => !isTemplate(i));
  return {prompts, templates};
}

function handleSearch(){
  const term = (document.getElementById('hub-search').value || '').toLowerCase();
  const all = window.__ALL_PROMPTS__ || [];
  const filtered = all.filter(p =>
    (p.title||'').toLowerCase().includes(term) ||
    (p.description||p.preview||'').toLowerCase().includes(term) ||
    (p.category||'').toLowerCase().includes(term) ||
    (p.role||'').toLowerCase().includes(term)
  );
  const {prompts, templates} = splitByType(filtered);
  renderGrid('prompts-grid', prompts);
  renderGrid('templates-grid', templates);
}

document.addEventListener('DOMContentLoaded', () => {
  fetchPrompts();
  const input = document.getElementById('hub-search');
  if(input){ input.addEventListener('input', handleSearch); }
  const tabPrompts = document.getElementById('tab-prompts');
  const tabTemplates = document.getElementById('tab-templates');
  const sectionPrompts = document.getElementById('prompts-section');
  const sectionTemplates = document.getElementById('templates-section');
  function switchTab(target){
    const isPrompts = target === 'prompts';
    tabPrompts.classList.toggle('active', isPrompts);
    tabPrompts.setAttribute('aria-selected', String(isPrompts));
    tabTemplates.classList.toggle('active', !isPrompts);
    tabTemplates.setAttribute('aria-selected', String(!isPrompts));
    sectionPrompts.classList.toggle('hidden', !isPrompts);
    sectionTemplates.classList.toggle('hidden', isPrompts);
    handleSearch();
  }
  if(tabPrompts){ tabPrompts.addEventListener('click', () => switchTab('prompts')); }
  if(tabTemplates){ tabTemplates.addEventListener('click', () => switchTab('templates')); }
  wireModal();
});

// removed expandable/tabs fetch logic per simplification

// ---- Modal helpers ----
function wireModal(){
  const modal = document.getElementById('prompt-modal');
  const closeBtn = document.getElementById('prompt-modal-close');
  if(closeBtn){ closeBtn.addEventListener('click', () => closePromptModal()); }
  if(modal){ modal.addEventListener('click', (e)=>{ if(e.target===modal) closePromptModal(); }); }
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') closePromptModal(); });
}

function openPromptModal(prompt){
  const modal = document.getElementById('prompt-modal');
  const title = document.getElementById('prompt-modal-title');
  const content = document.getElementById('prompt-modal-content');
  const copyBtn = document.getElementById('prompt-modal-copy');
  const editBtn = document.getElementById('prompt-modal-edit');
  const editorWrap = document.getElementById('prompt-modal-editor-wrap');
  const editor = document.getElementById('prompt-modal-editor');
  const lines = document.getElementById('prompt-modal-lines');
  const editorCopy = document.getElementById('prompt-modal-editor-copy');
  title.textContent = prompt.title || 'Prompt';
  content.textContent = String(prompt.content || prompt.preview || '');
  if(editorWrap){ editorWrap.style.display = 'none'; }
  editor.value = '';
  copyBtn.onclick = async ()=>{
    try{ await navigator.clipboard.writeText(content.textContent); copyBtn.textContent = 'Copied!'; setTimeout(()=>copyBtn.textContent='Copy', 900);}catch(_e){}
  };
  if(editorCopy){
    editorCopy.onclick = async ()=>{
      try{ await navigator.clipboard.writeText(editor.value); editorCopy.textContent='✔️'; setTimeout(()=>editorCopy.textContent='📋', 900);}catch(_e){}
    };
  }
  function updateLineNumbers(){
    const count = (editor.value.match(/\n/g) || []).length + 1;
    let out = '';
    for(let i=1;i<=count;i++){ out += i + (i===count?'':'\n'); }
    if(lines){ lines.textContent = out; }
  }
  if(editor){
    editor.addEventListener('input', updateLineNumbers);
    editor.addEventListener('scroll', ()=>{ if(lines){ lines.style.transform = `translateY(${-editor.scrollTop}px)`; } });
  }
  editBtn.onclick = ()=>{
    const isHidden = !editorWrap || editorWrap.style.display==='none';
    if(isHidden){
      editor.value = content.textContent;
      if(editorWrap){ editorWrap.style.display='block'; }
      editBtn.textContent='Close Edit';
      updateLineNumbers();
      try{ editor.setSelectionRange(0,0); }catch(_e){}
      editor.scrollTop = 0;
    }else{
      if(editorWrap){ editorWrap.style.display='none'; }
      editBtn.textContent='Edit';
    }
  };
  modal.classList.add('open');
  modal.setAttribute('aria-hidden','false');
}

function closePromptModal(){
  const modal = document.getElementById('prompt-modal');
  if(modal){ modal.classList.remove('open'); modal.setAttribute('aria-hidden','true'); }
}


