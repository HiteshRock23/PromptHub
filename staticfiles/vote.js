// Shared voting module to keep like/dislike behavior consistent across UI
// Exposes: window.wireVoteControls(opts)
// opts: { pid, upBtn, downBtn, upCountEl, downCountEl }

(function(){
	function coerceNumber(value){
		var n = Number(value || 0);
		if (!isFinite(n) || isNaN(n)) return 0;
		return n;
	}

	function makeKeys(pid){
		var id = String(pid || '');
		return {
			state: 'prompt_feedback_' + id,
			counts: 'prompt_feedback_counts_' + id
		};
	}

	function readCounts(key){
		try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch(_e){ return {}; }
	}

	function writeCounts(key, value){
		try { localStorage.setItem(key, JSON.stringify(value)); } catch(_e){}
	}

	function setState(key, value){
		try { if(value){ localStorage.setItem(key, value); } else { localStorage.removeItem(key); } } catch(_e){}
	}

	function getState(key){
		try { return localStorage.getItem(key) || ''; } catch(_e){ return ''; }
	}

	function stopAll(e){
		if(!e) return;
		if(typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
		if(typeof e.stopPropagation === 'function') e.stopPropagation();
		if(typeof e.preventDefault === 'function') e.preventDefault();
	}

	function attachGuards(el){
		// Guard early pointer events to avoid triggering parent behaviors
		['pointerdown','mousedown','touchstart'].forEach(function(ev){
			el.addEventListener(ev, function(e){ stopAll(e); }, true);
		});
		// Do NOT capture 'click' here; the actual click handler will stop propagation
	}

	function animate(btn){
		if(!btn) return;
		btn.classList.add('pulse');
		setTimeout(function(){ btn.classList.remove('pulse'); }, 220);
	}

	function syncUI(keys, upBtn, downBtn, upCountEl, downCountEl){
		var st = getState(keys.state);
		var c = readCounts(keys.counts);
		var up = coerceNumber(c.up);
		var down = coerceNumber(c.down);
		if(upCountEl) upCountEl.textContent = String(up);
		if(downCountEl) downCountEl.textContent = String(down);
		if(upBtn){
			upBtn.classList.toggle('is-active', st === 'up');
			upBtn.setAttribute('aria-pressed', String(st === 'up'));
		}
		if(downBtn){
			downBtn.classList.toggle('is-active', st === 'down');
			downBtn.setAttribute('aria-pressed', String(st === 'down'));
		}
	}

	function applyVote(keys, kind){
		var st = getState(keys.state);
		var c = readCounts(keys.counts);
		c.up = coerceNumber(c.up);
		c.down = coerceNumber(c.down);
		if(kind === 'up'){
			if(st === 'up'){
				setState(keys.state, '');
				c.up = Math.max(0, c.up - 1);
			}else{
				setState(keys.state, 'up');
				c.up += 1;
				if(st === 'down') c.down = Math.max(0, c.down - 1);
			}
		}else{
			if(st === 'down'){
				setState(keys.state, '');
				c.down = Math.max(0, c.down - 1);
			}else{
				setState(keys.state, 'down');
				c.down += 1;
				if(st === 'up') c.up = Math.max(0, c.up - 1);
			}
		}
		writeCounts(keys.counts, c);
		return { state: getState(keys.state) || '', counts: c };
	}

	function postVote(pid, nextState){
		return fetch('/api/prompts/' + encodeURIComponent(String(pid)) + '/vote', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ vote: nextState || 'clear' })
		}).then(function(r){ return r.json(); });
	}

	function seedCounts(pid, keys){
		var hasLocalCounts = false;
		try { hasLocalCounts = !!localStorage.getItem(keys.counts); } catch(_e){ hasLocalCounts = false; }
		if(hasLocalCounts) return Promise.resolve();
		return fetch('/api/prompts/' + encodeURIComponent(String(pid)) + '/vote', { method: 'GET' })
			.then(function(r){ return r.ok ? r.json() : null; })
			.then(function(res){
				if(res && typeof res.upCount === 'number' && typeof res.downCount === 'number'){
					try { localStorage.setItem(keys.counts, JSON.stringify({ up: res.upCount, down: res.downCount })); } catch(_e){}
					try { if(res.userVote){ localStorage.setItem(keys.state, res.userVote); } else { localStorage.removeItem(keys.state); } } catch(_e){}
				}
			}).catch(function(){});
	}

	window.wireVoteControls = function(opts){
		var pid = String(opts && opts.pid || '');
		var upBtn = opts && opts.upBtn;
		var downBtn = opts && opts.downBtn;
		var upCountEl = opts && opts.upCountEl;
		var downCountEl = opts && opts.downCountEl;
		var keys = makeKeys(pid);

		// Default visible zeros for stability before sync
		if(upCountEl && !upCountEl.textContent) upCountEl.textContent = '0';
		if(downCountEl && !downCountEl.textContent) downCountEl.textContent = '0';

		// Initial sync (after optional seed)
		seedCounts(pid, keys).finally(function(){ syncUI(keys, upBtn, downBtn, upCountEl, downCountEl); });

		function handle(kind){
			return function(e){
				stopAll(e);
				var next = applyVote(keys, kind);
				syncUI(keys, upBtn, downBtn, upCountEl, downCountEl);
				animate(kind === 'up' ? upBtn : downBtn);
				var pendingBtn = kind === 'up' ? upBtn : downBtn;
				if(pendingBtn) pendingBtn.classList.add('is-loading');
				postVote(pid, next.state).then(function(res){
					if(pendingBtn) pendingBtn.classList.remove('is-loading');
					if(res && typeof res.upCount === 'number' && typeof res.downCount === 'number'){
						try { localStorage.setItem(keys.counts, JSON.stringify({ up: res.upCount, down: res.downCount })); } catch(_e){}
						try { if(res.userVote){ localStorage.setItem(keys.state, res.userVote); } else { localStorage.removeItem(keys.state); } } catch(_e){}
						syncUI(keys, upBtn, downBtn, upCountEl, downCountEl);
					}
				}).catch(function(){ if(pendingBtn) pendingBtn.classList.remove('is-loading'); });
			};
		}

		if(upBtn){
			attachGuards(upBtn);
			upBtn.addEventListener('click', handle('up'));
		}
		if(downBtn){
			attachGuards(downBtn);
			downBtn.addEventListener('click', handle('down'));
		}

		// Keep in sync if localStorage is updated (from another tab/window)
		window.addEventListener('storage', function(e){
			if(!e) return;
			if(e.key === keys.state || e.key === keys.counts){
				syncUI(keys, upBtn, downBtn, upCountEl, downCountEl);
			}
		});

		return {
			sync: function(){ syncUI(keys, upBtn, downBtn, upCountEl, downCountEl); }
		};
	};
})();


