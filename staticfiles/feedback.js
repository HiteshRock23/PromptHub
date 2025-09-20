(function(){
  function $(id){ return document.getElementById(id); }

  function open(){ var m=$('fb-modal'); if(m){ m.classList.add('open'); m.setAttribute('aria-hidden','false'); } }
  function close(){ var m=$('fb-modal'); if(m){ m.classList.remove('open'); m.setAttribute('aria-hidden','true'); } }

  function setStars(value){
    var wrap = $('fb-stars'); if(!wrap) return;
    Array.prototype.forEach.call(wrap.querySelectorAll('.fb-star'), function(el){
      var v = Number(el.getAttribute('data-val')||0);
      el.classList.toggle('is-active', v <= value);
    });
    wrap.setAttribute('data-current', String(value||''));
  }

  function getStars(){ var wrap=$('fb-stars'); if(!wrap) return null; var v=Number(wrap.getAttribute('data-current')||0); return v>0?v:null; }

  function wire(){
    var fab = $('fb-fab');
    var modal = $('fb-modal');
    var closeBtn = $('fb-close');
    var stars = $('fb-stars');
    var form = $('fb-form');
    var hint = $('fb-hint');

    if(fab) fab.addEventListener('click', open);
    if(closeBtn) closeBtn.addEventListener('click', close);
    if(modal) modal.addEventListener('click', function(e){ if(e.target===modal) close(); });
    document.addEventListener('keydown', function(e){ if(e.key==='Escape') close(); });

    if(stars){
      stars.addEventListener('click', function(e){
        var t = e.target;
        if(t && t.classList.contains('fb-star')){
          var val = Number(t.getAttribute('data-val')||0);
          setStars(val);
        }
      });
      setStars(0);
    }

    var quick = document.querySelectorAll('#fb-modal .fb-quick button');
    quick.forEach(function(btn){
      btn.addEventListener('click', function(){
        try{ localStorage.setItem('quick_feedback_reaction', btn.getAttribute('data-reaction')||''); }catch(_e){}
        if(hint){ hint.textContent = 'Reaction recorded. You can also leave a detailed note.'; }
      });
    });

    if(form){
      form.addEventListener('submit', async function(e){
        e.preventDefault();
        var payload = {
          name: $('fb-name')?.value || '',
          email: $('fb-email')?.value || '',
          category: $('fb-category')?.value || 'experience',
          rating: getStars(),
          comments: $('fb-comments')?.value || '',
          // promptId removed from UI; keep empty for compatibility
          promptId: '',
          reaction: (function(){ try{ return localStorage.getItem('quick_feedback_reaction')||''; }catch(_e){ return ''; } })()
        };
        var btn = $('fb-submit');
        if(btn){ btn.disabled = true; btn.textContent = 'Submitting...'; }
        try{
          var res = await fetch('/api/feedback/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
          var ok = res.ok; var data = ok ? await res.json() : null;
          if(ok && data && data.ok){
            if(hint){ hint.textContent = 'Thank you for your feedback!'; }
            setStars(0);
            try{ localStorage.removeItem('quick_feedback_reaction'); }catch(_e){}
            $('fb-form').reset();
            setTimeout(close, 600);
          }else{
            if(hint){ hint.textContent = 'Something went wrong. Please try again.'; }
          }
        }catch(_e){ if(hint){ hint.textContent='Network error. Please try later.'; } }
        finally{ if(btn){ btn.disabled=false; btn.textContent = 'Submit'; } }
      });
    }

    // Keep FAB above the footer (don't cover it)
    function repositionFab(){
      if(!fab) return;
      try{
        var siteFooter = document.querySelector('.site-footer') || document.querySelector('footer');
        var btnMargin = 18; // matches CSS bottom spacing
        var btnHeight = 44; // approx button height incl. padding
        if(!siteFooter){ fab.style.bottom = btnMargin + 'px'; return; }
        var rect = siteFooter.getBoundingClientRect();
        var overlap = (window.innerHeight - rect.top);
        if(overlap > 0){
          // Push up by the overlap so it stops right above the footer
          fab.style.bottom = (btnMargin + overlap) + 'px';
        }else{
          fab.style.bottom = btnMargin + 'px';
        }
      }catch(_e){ /* noop */ }
    }
    repositionFab();
    window.addEventListener('scroll', repositionFab, { passive: true });
    window.addEventListener('resize', repositionFab);
  }

  document.addEventListener('DOMContentLoaded', wire);
})();

















