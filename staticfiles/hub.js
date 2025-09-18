async function fetchPrompts(){
  try{
    const res = await fetch('/api/prompts/').then(r=>r.json()).catch(()=>({prompts:[]}));
    const all = res.prompts || [];
    window.__ALL_PROMPTS__ = all;
    renderGrid('prompts-grid', all);
    // Load image prompts alongside
    loadImagePrompts();
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
    // navigate by database id
    const pid = Number(prompt.id||0) || 1;
    window.location.href = `/hub/p/${pid}/`;
  });

  wrap.appendChild(title);
  wrap.appendChild(meta);
  wrap.appendChild(content);
  // no voting controls on cards – voting available on detail page only
  return wrap;
}

function renderGrid(targetId, prompts){
  const grid = document.getElementById(targetId);
  grid.innerHTML = '';
  prompts.forEach(p => grid.appendChild(createCard(p)));
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
  renderGrid('prompts-grid', filtered);
}

document.addEventListener('DOMContentLoaded', () => {
  fetchPrompts();
  const input = document.getElementById('hub-search');
  if(input){ input.addEventListener('input', handleSearch); }
  const tabPrompts = document.getElementById('tab-prompts');
  const tabImages = document.getElementById('tab-images');
  const sectionPrompts = document.getElementById('prompts-section');
  const sectionImages = document.getElementById('images-section');
  function switchTab(target){
    const isPrompts = target === 'prompts';
    tabPrompts.classList.toggle('active', isPrompts);
    tabPrompts.setAttribute('aria-selected', String(isPrompts));
    tabImages.classList.toggle('active', !isPrompts);
    tabImages.setAttribute('aria-selected', String(!isPrompts));
    sectionPrompts.classList.toggle('hidden', !isPrompts);
    sectionImages.classList.toggle('hidden', isPrompts);
    handleSearch();
  }
  if(tabPrompts){ tabPrompts.addEventListener('click', () => switchTab('prompts')); }
  if(tabImages){ tabImages.addEventListener('click', () => switchTab('images')); }
  wireModal();
});

// ----- Image prompts -----
async function loadImagePrompts(){
  try{
    const res = await fetch('/api/image-prompts/').then(r=>r.json());
    const items = res.items || [];
    const grid = document.getElementById('images-grid');
    if(!grid) return;
    grid.innerHTML = '';
    items.forEach(item => grid.appendChild(createImageCard(item)));
  }catch(e){ console.error('Failed to load image prompts', e); }
}

function createImageCard(item){
  const wrap = document.createElement('div');
  wrap.className = 'img-card clickable';
  const img = document.createElement('img');
  img.className = 'img-card-img';
  img.src = item.imageUrl || '';
  img.alt = item.title || 'Image Prompt';

  const overlay = document.createElement('div');
  overlay.className = 'img-card-overlay';
  const title = document.createElement('h3');
  title.className = 'img-card-title';
  title.textContent = item.title || 'Image Prompt';
  overlay.appendChild(title);

  const copyIcon = document.createElement('button');
  copyIcon.className = 'icon-btn copy-top';
  copyIcon.setAttribute('aria-label','Copy prompt');
  copyIcon.innerHTML = '📋';
  copyIcon.addEventListener('click', async (e)=>{
    e.stopPropagation();
    try{ await navigator.clipboard.writeText(String(item.prompt||'')); copyIcon.innerHTML='✔️'; setTimeout(()=>copyIcon.innerHTML='📋', 900);}catch(_e){}
  });

  wrap.appendChild(copyIcon);
  wrap.appendChild(img);
  wrap.appendChild(overlay);
  wrap.addEventListener('click', ()=> openImagePrompt(item));
  return wrap;
}

function openImagePrompt(item){
  const modal = document.getElementById('prompt-modal');
  const title = document.getElementById('prompt-modal-title');
  const content = document.getElementById('prompt-modal-content');
  const img = document.getElementById('prompt-modal-image');
  const copyBtn = document.getElementById('prompt-modal-copy');
  const editBtn = document.getElementById('prompt-modal-edit');
  const editorWrap = document.getElementById('prompt-modal-editor-wrap');
  const editor = document.getElementById('prompt-modal-editor');
  const lines = document.getElementById('prompt-modal-lines');
  const editorCopy = document.getElementById('prompt-modal-editor-copy');
  title.textContent = item.title || 'Image Prompt';
  content.textContent = String(item.prompt || '');
  if(img){ img.src = item.imageUrl || ''; img.style.display = item.imageUrl ? 'block' : 'none'; }
  if(editorWrap){ editorWrap.style.display = 'none'; }
  if(editor){ editor.value = ''; }

  if(copyBtn){
    copyBtn.onclick = async ()=>{
      try{ await navigator.clipboard.writeText(content.textContent); copyBtn.textContent = 'Copied!'; setTimeout(()=>copyBtn.textContent='Copy', 900);}catch(_e){}
    };
  }
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
  if(editBtn){
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
  }
  modal.classList.add('open');
  modal.setAttribute('aria-hidden','false');
}

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


