(function () {
  'use strict';

  const root = document.getElementById('film-index');
  if (!root) return;

  const URLS = {
    queue: root.dataset.queueUrl,
    item: root.dataset.itemUrl,
    search: root.dataset.searchUrl,
    poster: root.dataset.posterUrl,
    decide: root.dataset.decideUrl,
  };
  const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';

  const el = {
    bucket: document.getElementById('filter-bucket'),
    kind: document.getElementById('filter-kind'),
    status: document.getElementById('filter-status'),
    name: document.getElementById('filter-name'),
    reload: document.getElementById('btn-reload'),
    itemPane: document.getElementById('item-pane'),
    queueList: document.getElementById('queue-list'),
    queueCount: document.getElementById('queue-count'),
    progress: document.getElementById('progress'),
    stats: document.getElementById('stats'),
    revert: document.getElementById('btn-revert'),
    reject: document.getElementById('btn-reject'),
  };

  const state = {
    items: [],
    index: 0,
    candidates: [],
    selected: 0,
    material: null,
    decided: [],
    busy: false,
  };

  const SERIES_TYPES = [4, 12, 16];

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function kindLabel(material) {
    return SERIES_TYPES.includes(material.program_type_id) ? 'Сериал' : 'Фильм';
  }

  function itemUrl(programId) {
    return URLS.item.replace(/\/0\/$/, `/${programId}/`);
  }

  async function getJson(url) {
    const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF,
      },
      body: JSON.stringify(payload),
    });
    return response.json();
  }

  function filters() {
    const params = new URLSearchParams();
    if (el.bucket.value) params.set('bucket', el.bucket.value);
    if (el.kind.value) params.set('kind', el.kind.value);
    if (el.status.value) params.set('status', el.status.value);
    if (el.name.value.trim()) params.set('name', el.name.value.trim());
    return params;
  }

  async function loadQueue() {
    el.queueList.innerHTML = '<div class="p-3 text-muted">Загрузка…</div>';
    const data = await getJson(`${URLS.queue}?${filters().toString()}`);
    state.items = data.items || [];
    state.index = 0;
    state.decided = [];
    renderQueue();
    updateProgress();
    if (state.items.length) {
      await loadItem(0);
    } else {
      el.itemPane.innerHTML = '<div class="card"><div class="card-body text-muted">Нет материалов по фильтру.</div></div>';
    }
  }

  function renderQueue() {
    el.queueCount.textContent = state.items.length;
    if (!state.items.length) {
      el.queueList.innerHTML = '<div class="p-3 text-muted">Пусто</div>';
      return;
    }
    el.queueList.innerHTML = state.items.map((item, i) => `
      <button type="button" class="list-group-item list-group-item-action ${i === state.index ? 'active' : ''}"
              data-index="${i}">
        <div class="d-flex justify-content-between">
          <span class="text-truncate me-2">${esc(item.name)}</span>
          <small class="text-nowrap">${esc(item.production_year || '')}</small>
        </div>
        <small class="text-truncate d-block opacity-75">${esc(item.bucket)}</small>
      </button>`).join('');
    el.queueList.querySelectorAll('[data-index]').forEach((node) => {
      node.addEventListener('click', () => loadItem(Number(node.dataset.index)));
    });
    const active = el.queueList.querySelector('.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  async function loadItem(i) {
    if (i < 0 || i >= state.items.length) return;
    state.index = i;
    state.selected = 0;
    renderQueue();
    updateProgress();

    const programId = state.items[i].oplan_program_id;
    el.itemPane.innerHTML = '<div class="card"><div class="card-body text-muted">Загрузка…</div></div>';
    try {
      const data = await getJson(itemUrl(programId));
      state.material = data.material;
      state.candidates = data.candidates || [];
      renderItem(data);
    } catch (error) {
      el.itemPane.innerHTML = `<div class="card"><div class="card-body text-danger">Ошибка загрузки: ${esc(error.message)}</div></div>`;
    }
  }

  function renderItem(data) {
    const m = data.material;
    const review = data.review || {};
    const statusBadge = {
      resolved: '<span class="badge bg-success">принято вручную</span>',
      rejected: '<span class="badge bg-danger">отклонено</span>',
      pending: '<span class="badge bg-secondary">не решено</span>',
    }[review.status] || '';

    const header = `
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <h5 class="mb-1">${esc(m.name)}</h5>
          <div class="text-muted">${esc(m.orig_name || '')}</div>
          <div class="mt-1">
            <span class="badge bg-secondary">${kindLabel(m)}</span>
            <span class="badge bg-light text-dark">${esc(m.production_year || 'год ?')}</span>
            <span class="badge bg-light text-dark">${esc(m.production_country || 'страна ?')}</span>
            ${m.has_file ? '<span class="badge bg-success">есть файл</span>' : '<span class="badge bg-warning text-dark">нет файла</span>'}
            ${statusBadge}
          </div>
          <div class="mt-1 small"><b>Режиссёр:</b> ${esc(m.director || '—')}</div>
        </div>
        <div class="text-end small text-muted">id ${m.program_id} · kind ${m.program_kind}</div>
      </div>
      ${data.description ? `<div class="mt-2 small text-body-secondary">${esc(data.description)}</div>` : ''}
      <hr>
      <div class="d-flex justify-content-between align-items-center">
        <b>Кандидаты Кинопоиска</b>
        <div class="input-group input-group-sm" style="max-width: 26rem;">
          <input class="form-control" id="kp-search" placeholder="Не нашёл — поиск на Кинопоиске…">
          <button class="btn btn-outline-secondary" id="kp-search-btn">Найти</button>
        </div>
      </div>
      <div id="candidates" class="mt-2"></div>
      <div id="search-results" class="mt-2"></div>
    `;
    el.itemPane.innerHTML = `<div class="card"><div class="card-body">${header}</div></div>`;

    document.getElementById('kp-search-btn').addEventListener('click', doSearch);
    document.getElementById('kp-search').addEventListener('keydown', (event) => {
      if (event.key === 'Enter') { event.preventDefault(); doSearch(); }
    });
    renderCandidates();
  }

  function candidateCard(candidate, index) {
    const selected = index === state.selected ? 'border-primary shadow-sm' : '';
    const dirFlag = candidate.director_match ? '<span class="badge bg-info text-dark">режиссёр+</span>' : '';
    return `
      <div class="candidate card mb-2 ${selected}" data-candidate="${index}">
        <div class="card-body d-flex gap-3 py-2">
          <img class="candidate-poster" loading="lazy"
               src="${URLS.poster}?kp_id=${candidate.kp_id}"
               onerror="this.style.visibility='hidden'">
          <div class="flex-grow-1">
            <div class="d-flex justify-content-between">
              <div>
                <div class="fw-bold">${esc(candidate.title)}
                  <a class="small" target="_blank" rel="noopener"
                     href="https://www.kinopoisk.ru/film/${candidate.kp_id}/">КП ↗</a>
                </div>
                <div class="text-muted small">${esc(candidate.original_title || '')}</div>
                <div class="small">${esc(candidate.year || '—')} · ${esc((candidate.countries || []).join(', '))}
                  · ${esc(candidate.type || '')}</div>
                <div class="small"><b>Реж:</b> ${esc(candidate.director || '—')} ${dirFlag}</div>
              </div>
              <div class="text-end">
                <div class="fs-5">${(candidate.score ?? 0).toFixed(3)}</div>
                <div class="small text-muted">t=${(candidate.title_score ?? 0).toFixed(2)}
                  y=${candidate.year_score ?? 0} c=${(candidate.country_score ?? 0).toFixed(2)}
                  d=${(candidate.director_score ?? 0).toFixed(2)}</div>
              </div>
            </div>
          </div>
          <div class="d-flex align-items-center">
            <button class="btn btn-sm btn-success" data-accept="${candidate.kp_id}">Принять</button>
          </div>
        </div>
      </div>`;
  }

  function renderCandidates() {
    const container = document.getElementById('candidates');
    if (!container) return;
    if (!state.candidates.length) {
      container.innerHTML = '<div class="text-muted">Кандидатов нет — воспользуйтесь ручным поиском.</div>';
      return;
    }
    container.innerHTML = state.candidates.map(candidateCard).join('');
    container.querySelectorAll('[data-candidate]').forEach((node) => {
      node.addEventListener('click', () => selectCandidate(Number(node.dataset.candidate)));
      node.addEventListener('dblclick', () => {
        const candidate = state.candidates[Number(node.dataset.candidate)];
        if (candidate) accept(candidate.kp_id);
      });
    });
    container.querySelectorAll('[data-accept]').forEach((node) => {
      node.addEventListener('click', (event) => {
        event.stopPropagation();
        accept(node.dataset.accept);
      });
    });
  }

  function selectCandidate(index) {
    if (index < 0 || index >= state.candidates.length) return;
    state.selected = index;
    renderCandidates();
    const node = document.querySelector(`[data-candidate="${index}"]`);
    if (node) node.scrollIntoView({ block: 'nearest' });
  }

  async function doSearch() {
    const input = document.getElementById('kp-search');
    const container = document.getElementById('search-results');
    const query = input.value.trim();
    if (!query) return;
    container.innerHTML = '<div class="text-muted">Поиск…</div>';
    try {
      const data = await getJson(`${URLS.search}?q=${encodeURIComponent(query)}`);
      const items = data.items || [];
      if (!items.length) {
        container.innerHTML = '<div class="text-muted">Ничего не найдено.</div>';
        return;
      }
      container.innerHTML = `<div class="small text-muted mb-1">Результаты ручного поиска</div>` +
        items.map((item) => `
          <div class="search-result card mb-1" data-kp="${item.kp_id}">
            <div class="card-body py-1 d-flex justify-content-between">
              <div>
                <div class="fw-bold">${esc(item.title)} <span class="text-muted small">${esc(item.original_title || '')}</span></div>
                <div class="small">${esc(item.year || '—')} · ${esc((item.countries || []).join(', '))} · ${esc(item.type || '')}</div>
              </div>
              <button class="btn btn-sm btn-success" data-accept="${item.kp_id}">Принять</button>
            </div>
          </div>`).join('');
      container.querySelectorAll('[data-accept]').forEach((node) => {
        node.addEventListener('click', () => accept(node.dataset.accept));
      });
    } catch (error) {
      container.innerHTML = `<div class="text-danger">Ошибка поиска: ${esc(error.message)}</div>`;
    }
  }

  async function accept(kpId) {
    if (state.busy || !state.material) return;
    await decide({ action: 'accept', program_id: state.material.program_id, kp_id: Number(kpId) });
  }

  async function reject() {
    if (state.busy || !state.material) return;
    await decide({ action: 'reject', program_id: state.material.program_id });
  }

  async function decide(payload) {
    state.busy = true;
    try {
      const result = await postJson(URLS.decide, payload);
      if (result.status !== 'success') {
        alert(result.message || 'Ошибка');
        return;
      }
      state.decided.push({ program_id: payload.program_id, action: payload.action });
      state.items.splice(state.index, 1);
      if (state.index >= state.items.length) state.index = Math.max(0, state.items.length - 1);
      renderQueue();
      updateProgress();
      if (state.items.length) {
        await loadItem(state.index);
      } else {
        el.itemPane.innerHTML = '<div class="card"><div class="card-body text-success">Очередь по фильтру разобрана.</div></div>';
        state.material = null;
      }
    } finally {
      state.busy = false;
    }
  }

  async function revert() {
    if (state.busy) return;
    const last = state.decided.pop();
    if (!last) { return; }
    state.busy = true;
    try {
      const result = await postJson(URLS.decide, { action: 'revert', program_id: last.program_id });
      if (result.status !== 'success') { alert(result.message || 'Ошибка'); return; }
      await loadQueue();
      const position = state.items.findIndex((item) => item.oplan_program_id === last.program_id);
      state.decided = [];
      if (position >= 0) await loadItem(position);
    } finally {
      state.busy = false;
    }
  }

  function updateProgress() {
    const total = state.items.length;
    el.progress.textContent = total ? `${state.index + 1} / ${total}` : '0 / 0';
  }

  function isTyping() {
    const tag = document.activeElement?.tagName;
    return tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA';
  }

  document.addEventListener('keydown', (event) => {
    if (isTyping()) return;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectCandidate(state.selected + 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        selectCandidate(state.selected - 1);
        break;
      case 'ArrowRight':
        event.preventDefault();
        loadItem(state.index + 1);
        break;
      case 'ArrowLeft':
        event.preventDefault();
        loadItem(state.index - 1);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (state.candidates[state.selected]) accept(state.candidates[state.selected].kp_id);
        break;
      case 'Backspace':
        event.preventDefault();
        revert();
        break;
      case 'r':
      case 'R':
        event.preventDefault();
        reject();
        break;
      default:
        break;
    }
  });

  el.reload.addEventListener('click', loadQueue);
  el.name.addEventListener('keydown', (event) => { if (event.key === 'Enter') loadQueue(); });
  el.revert.addEventListener('click', revert);
  el.reject.addEventListener('click', reject);

  loadQueue();
})();
