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
  const SERIES_TYPES = [4, 12, 16];
  const FPS = Number(root.dataset.fps) || 25;

  const el = {
    bucket: document.getElementById('filter-bucket'),
    kind: document.getElementById('filter-kind'),
    status: document.getElementById('filter-status'),
    name: document.getElementById('filter-name'),
    reload: document.getElementById('btn-reload'),
    materialPane: document.getElementById('material-pane'),
    candidates: document.getElementById('candidates'),
    queueList: document.getElementById('queue-list'),
    queueCounts: document.querySelectorAll('.js-queue-count'),
    queueTotal: document.querySelector('.js-queue-total'),
    queuePrev: document.getElementById('queue-prev'),
    queueNext: document.getElementById('queue-next'),
    progress: document.getElementById('progress'),
    revert: document.getElementById('btn-revert'),
    reject: document.getElementById('btn-reject'),
    searchInput: document.getElementById('kp-search'),
    searchBtn: document.getElementById('kp-search-btn'),
    searchResults: document.getElementById('search-results'),
  };

  const searchModalEl = document.getElementById('search-modal');
  const getSearchModal = () => bootstrap.Modal.getOrCreateInstance(searchModalEl);

  const PAGE_SIZE = 500;

  const state = {
    items: [],
    index: 0,
    offset: 0,
    limit: PAGE_SIZE,
    total: 0,
    candidates: [],
    selected: 0,
    material: null,
    decided: [],
    busy: false,
  };

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function pct(value) {
    return `${Math.round((Number(value) || 0) * 100)}%`;
  }

  function scoreClass(score) {
    if (score >= 0.85) return 'text-success';
    if (score >= 0.70) return 'text-warning';
    return 'text-secondary';
  }

  function kindLabel(material) {
    return SERIES_TYPES.includes(material.program_type_id) ? 'Сериал' : 'Фильм';
  }

  function durationLabel(frames) {
    const total = Math.round((Number(frames) || 0) / FPS);
    if (total <= 0) return '';
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const seconds = total % 60;
    const pad = (value) => String(value).padStart(2, '0');
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
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

  function setQueueCount(count) {
    el.queueCounts.forEach((node) => { node.textContent = count; });
  }

  function setQueueTotal(total) {
    if (el.queueTotal) el.queueTotal.textContent = total;
  }

  function updatePager() {
    if (el.queuePrev) el.queuePrev.disabled = state.offset <= 0;
    if (el.queueNext) {
      el.queueNext.disabled = state.offset + state.items.length >= state.total;
    }
  }

  // --- Очередь -------------------------------------------------------------

  async function loadQueue(offset = 0, selectIndex = 0, keepDecided = false) {
    const decided = state.decided;
    el.queueList.innerHTML = '<div class="p-3 text-muted">Загрузка…</div>';
    const params = filters();
    params.set('limit', String(state.limit));
    params.set('offset', String(Math.max(0, offset)));
    const data = await getJson(`${URLS.queue}?${params.toString()}`);
    state.items = data.items || [];
    state.total = Number(data.total) || 0;
    state.offset = Number(data.offset) || 0;
    state.index = 0;
    state.decided = keepDecided ? decided : [];
    renderQueue();
    updateProgress();
    if (!state.items.length && state.offset > 0 && state.total > 0) {
      await loadQueue(Math.max(0, Math.min(state.offset - state.limit, state.total - 1)),
                      selectIndex, keepDecided);
      return;
    }
    if (state.items.length) {
      await loadItem(Math.min(Math.max(0, selectIndex), state.items.length - 1));
    } else {
      showEmptyState();
    }
  }

  function renderQueue() {
    setQueueCount(state.items.length);
    setQueueTotal(state.total);
    updatePager();
    if (!state.items.length) {
      el.queueList.innerHTML = '<div class="p-3 text-muted">Нет материалов по фильтру.</div>';
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
      node.addEventListener('click', () => {
        loadItem(Number(node.dataset.index));
      });
    });
    const active = el.queueList.querySelector('.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  async function changePage(delta, atEnd = false) {
    const offset = state.offset + delta * state.limit;
    if (offset < 0 || offset >= state.total) return;
    await loadQueue(offset);
    if (atEnd && state.items.length) await loadItem(state.items.length - 1);
  }

  async function loadItem(i) {
    if (i < 0 || i >= state.items.length) return;
    state.index = i;
    state.selected = 0;
    renderQueue();
    updateProgress();

    const programId = state.items[i].oplan_program_id;
    el.materialPane.innerHTML = '<div class="card"><div class="card-body text-muted">Загрузка…</div></div>';
    el.candidates.innerHTML = '';
    try {
      const data = await getJson(itemUrl(programId));
      state.material = data.material;
      state.candidates = data.candidates || [];
      renderMaterial(data);
      renderCandidates();
    } catch (error) {
      el.materialPane.innerHTML = `<div class="card"><div class="card-body text-danger">Ошибка загрузки: ${esc(error.message)}</div></div>`;
    }
  }

  function showEmptyState() {
    state.material = null;
    state.candidates = [];
    el.materialPane.innerHTML =
      '<div class="card"><div class="card-body text-muted">Очередь пуста. Настройте фильтры в правой панели.</div></div>';
    el.candidates.innerHTML = '<div class="text-muted">Выберите материал в очереди.</div>';
  }

  // --- Карточка материала --------------------------------------------------

  function renderMaterial(data) {
    const m = data.material;
    const review = data.review || {};
    const statusBadge = {
      resolved: '<span class="badge text-bg-success">принято вручную</span>',
      rejected: '<span class="badge text-bg-danger">отклонено</span>',
      pending: '<span class="badge text-bg-secondary">не решено</span>',
    }[review.status] || '';

    const fileLine = m.has_file && m.file_name
      ? `<div class="mt-1 small text-muted fi-file">${esc(m.file_name)}</div>`
      : '';
    const duration = durationLabel(m.duration);
    const castLine = m.cast
      ? `<div class="mt-1 small"><b>В ролях:</b> ${esc(m.cast)}</div>`
      : '';

    el.materialPane.innerHTML = `
      <div class="card fi-material">
        <div class="card-body py-2">
          <div class="d-flex justify-content-between align-items-start gap-3">
            <div>
              <h5 class="mb-1">${esc(m.name)}</h5>
              <div class="text-muted">${esc(m.orig_name || '')}</div>
              <div class="mt-1 d-flex flex-wrap gap-1">
                <span class="badge text-bg-secondary">${kindLabel(m)}</span>
                <span class="badge text-bg-light text-dark">${esc(m.production_year || 'год ?')}</span>
                <span class="badge text-bg-light text-dark">${esc(m.production_country || 'страна ?')}</span>
                ${duration ? `<span class="badge text-bg-light text-dark">${esc(duration)}</span>` : ''}
                ${m.has_file
                  ? '<span class="badge text-bg-success">есть файл</span>'
                  : '<span class="badge text-bg-warning text-dark">нет файла</span>'}
                ${statusBadge}
              </div>
              <div class="mt-1 small"><b>Режиссёр:</b> ${esc(m.director || '—')}</div>
              ${castLine}
            </div>
            <div class="text-end small text-muted text-nowrap">oplan id: ${m.program_id}<br>kind: ${m.program_kind}</div>
          </div>
          ${fileLine}
          ${data.description
            ? `<div class="mt-2 small text-body-secondary fi-description">${esc(data.description)}</div>`
            : ''}
        </div>
      </div>`;
  }

  // --- Кандидаты -----------------------------------------------------------

  function candidateCard(candidate, index) {
    const selected = index === state.selected ? ' border-primary shadow-sm' : '';
    const dirFlag = candidate.director_match
      ? '<span class="badge text-bg-info text-dark">Режиссёр совпал</span>' : '';
    const typeLabel = candidate.type === 'series'
      ? 'сериал'
      : candidate.type === 'film' ? 'фильм' : (candidate.type || '');
    const typeFlag = candidate.type_known && candidate.type_match === false
      ? '<span class="badge text-bg-warning text-dark">Тип не совпадает</span>' : '';
    const metrics = [
      ['Название', candidate.title_score],
      ['Год', candidate.year_score],
      ['Страна', candidate.country_score],
      ['Режиссёр', candidate.director_score],
    ].map(([label, value]) => `<span class="fi-metric">${label} <b>${pct(value)}</b></span>`).join('');

    return `
      <div class="candidate card mb-2${selected}" data-candidate="${index}">
        <div class="card-body d-flex gap-3 py-2">
          <img class="candidate-poster" loading="lazy"
               src="${URLS.poster}?kp_id=${candidate.kp_id}"
               onerror="this.style.visibility='hidden'">
          <div class="flex-grow-1">
            <div class="d-flex justify-content-between gap-3">
              <div>
                <div class="fw-bold">${esc(candidate.title)}
                  <a class="kp-link" target="_blank" rel="noopener" title="Открыть на Кинопоиске"
                     href="https://www.kinopoisk.ru/film/${candidate.kp_id}/">
                    <img class="kp-logo" src="/static/img/kinopoisk.png" alt="Кинопоиск">
                  </a>
                </div>
                <div class="text-muted small">${esc(candidate.original_title || '')}</div>
                <div class="small">${esc(candidate.year || '—')} · ${esc((candidate.countries || []).join(', '))}
                  · ${esc(typeLabel)} ${typeFlag}</div>
                <div class="small"><b>Реж:</b> ${esc(candidate.director || '—')} ${dirFlag}</div>
              </div>
              <div class="fi-score text-end">
                <div class="fi-overall ${scoreClass(candidate.score)}">${pct(candidate.score)}</div>
                <div class="small text-muted">совпадение</div>
                <div class="fi-metrics mt-1 justify-content-end">${metrics}</div>
              </div>
            </div>
          </div>
          <button class="btn btn-sm btn-success" data-accept="${candidate.kp_id}">Принять</button>
        </div>
      </div>`;
  }

  function renderCandidates() {
    if (!state.candidates.length) {
      el.candidates.innerHTML =
        '<div class="text-muted">Кандидатов нет — воспользуйтесь кнопкой «Ручной поиск».</div>';
      return;
    }
    el.candidates.innerHTML = state.candidates.map(candidateCard).join('');
    el.candidates.querySelectorAll('[data-candidate]').forEach((node) => {
      node.addEventListener('click', () => selectCandidate(Number(node.dataset.candidate)));
      node.addEventListener('dblclick', () => {
        const candidate = state.candidates[Number(node.dataset.candidate)];
        if (candidate) accept(candidate.kp_id);
      });
    });
    el.candidates.querySelectorAll('[data-accept]').forEach((node) => {
      node.addEventListener('click', (event) => {
        event.stopPropagation();
        accept(node.dataset.accept);
      });
    });
    el.candidates.querySelectorAll('.kp-link').forEach((node) => {
      node.addEventListener('click', (event) => event.stopPropagation());
    });
  }

  function selectCandidate(index) {
    if (index < 0 || index >= state.candidates.length) return;
    state.selected = index;
    renderCandidates();
    const node = el.candidates.querySelector(`[data-candidate="${index}"]`);
    if (node) node.scrollIntoView({ block: 'nearest' });
  }

  // --- Ручной поиск --------------------------------------------------------

  async function doSearch() {
    const query = el.searchInput.value.trim();
    if (!query) return;
    el.searchResults.innerHTML = '<div class="text-muted">Поиск…</div>';
    try {
      const data = await getJson(`${URLS.search}?q=${encodeURIComponent(query)}`);
      const items = data.items || [];
      if (!items.length) {
        el.searchResults.innerHTML = '<div class="text-muted">Ничего не найдено.</div>';
        return;
      }
      el.searchResults.innerHTML = items.map((item) => `
        <div class="search-result card mb-1" data-kp="${item.kp_id}">
          <div class="card-body py-2 d-flex gap-2 align-items-center">
            <img class="search-poster" loading="lazy"
                 src="${URLS.poster}?kp_id=${item.kp_id}"
                 onerror="this.style.visibility='hidden'">
            <div class="flex-grow-1">
              <div class="fw-bold">
                <a class="search-title" target="_blank" rel="noopener"
                   href="https://www.kinopoisk.ru/film/${item.kp_id}/">${esc(item.title)}</a>
                <span class="text-muted small">${esc(item.original_title || '')}</span>
              </div>
              <div class="small">${esc(item.year || '—')} · ${esc((item.countries || []).join(', '))} · ${esc(item.type || '')}</div>
            </div>
            <button class="btn btn-sm btn-success" data-accept="${item.kp_id}">Принять</button>
          </div>
        </div>`).join('');
      el.searchResults.querySelectorAll('[data-accept]').forEach((node) => {
        node.addEventListener('click', () => accept(node.dataset.accept));
      });
    } catch (error) {
      el.searchResults.innerHTML = `<div class="text-danger">Ошибка поиска: ${esc(error.message)}</div>`;
    }
  }

  // --- Решения -------------------------------------------------------------

  async function accept(kpId) {
    if (state.busy || !state.material) return;
    getSearchModal().hide();
    await decide({ action: 'accept', program_id: state.material.program_id, kp_id: Number(kpId) });
  }

  async function reject() {
    if (state.busy || !state.material) return;
    await decide({ action: 'reject', program_id: state.material.program_id });
  }

  function leavesFilter(action) {
    const status = el.status.value;
    if (!status) return false;
    if (status === 'pending') return true;
    if (status === 'resolved') return action === 'reject';
    if (status === 'rejected') return action === 'accept';
    return false;
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
      if (!leavesFilter(payload.action)) {
        await loadItem(Math.min(state.index + 1, state.items.length - 1));
        return;
      }
      state.items.splice(state.index, 1);
      state.total = Math.max(0, state.total - 1);
      if (state.index >= state.items.length) state.index = Math.max(0, state.items.length - 1);
      renderQueue();
      updateProgress();
      if (state.items.length) {
        await loadItem(state.index);
      } else if (state.total > state.offset) {
        await loadQueue(state.offset, 0, true);
      } else if (state.offset > 0) {
        await loadQueue(Math.max(0, state.offset - state.limit), 0, true);
      } else {
        showEmptyState();
      }
    } finally {
      state.busy = false;
    }
  }

  async function revert() {
    if (state.busy) return;
    const last = state.decided.pop();
    if (!last) return;
    state.busy = true;
    try {
      const result = await postJson(URLS.decide, { action: 'revert', program_id: last.program_id });
      if (result.status !== 'success') { alert(result.message || 'Ошибка'); return; }
      await loadQueue(state.offset);
      let position = state.items.findIndex((item) => item.oplan_program_id === last.program_id);
      if (position < 0 && state.offset > 0) {
        await loadQueue(0);
        position = state.items.findIndex((item) => item.oplan_program_id === last.program_id);
      }
      state.decided = [];
      if (position >= 0) await loadItem(position);
    } finally {
      state.busy = false;
    }
  }

  function updateProgress() {
    if (!state.total) {
      el.progress.textContent = '0 / 0';
      return;
    }
    el.progress.textContent = `${state.offset + state.index + 1} / ${state.total}`;
  }

  async function step(delta) {
    const next = state.index + delta;
    if (next >= 0 && next < state.items.length) {
      await loadItem(next);
      return;
    }
    if (delta > 0) {
      await changePage(1);
    } else {
      await changePage(-1, true);
    }
  }

  // --- Полноэкранная раскладка (без скролла страницы) ----------------------

  function fitHeight() {
    const top = root.getBoundingClientRect().top;
    const height = Math.max(320, window.innerHeight - top - 12);
    root.style.setProperty('--fi-height', `${height}px`);
  }

  // --- Клавиатура ----------------------------------------------------------

  function isTyping() {
    const tag = document.activeElement?.tagName;
    return tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA';
  }

  document.addEventListener('keydown', (event) => {
    if (isTyping()) return;
    if (searchModalEl.classList.contains('show')) return;
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
        step(1);
        break;
      case 'ArrowLeft':
        event.preventDefault();
        step(-1);
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

  el.reload.addEventListener('click', () => loadQueue(0));
  el.name.addEventListener('keydown', (event) => { if (event.key === 'Enter') loadQueue(0); });
  el.queuePrev.addEventListener('click', () => changePage(-1));
  el.queueNext.addEventListener('click', () => changePage(1));
  el.revert.addEventListener('click', revert);
  el.reject.addEventListener('click', reject);
  el.searchBtn.addEventListener('click', doSearch);
  el.searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') { event.preventDefault(); doSearch(); }
  });

  window.addEventListener('resize', fitHeight);
  window.addEventListener('load', fitHeight);
  fitHeight();
  loadQueue();
})();
