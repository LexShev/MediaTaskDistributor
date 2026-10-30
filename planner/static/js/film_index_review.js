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
    lock: root.dataset.lockUrl,
    unlock: root.dataset.unlockUrl,
  };
  const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const SERIES_TYPES = [4, 12, 16];
  const FPS = Number(root.dataset.fps) || 25;
  const ME = Number(root.dataset.userId) || null;
  const IS_CHIEF = root.dataset.isChief === '1';
  const HEARTBEAT_MS = Number(root.dataset.heartbeat) || 4 * 60 * 1000;

  const el = {
    bucket: document.getElementById('filter-bucket'),
    channel: document.getElementById('filter-channel'),
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
    errorModal: document.getElementById('errorModal'),
    errorTitle: document.getElementById('error_modal_title'),
    errorMessage: document.getElementById('error_message'),
    errorTake: document.getElementById('error-modal-take'),
  };

  const searchModalEl = document.getElementById('search-modal');
  const getSearchModal = () => bootstrap.Modal.getOrCreateInstance(searchModalEl);
  const getErrorModal = () => bootstrap.Modal.getOrCreateInstance(el.errorModal);

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
    lockedId: null,
    heartbeatTimer: null,
    lockedProgramId: null,
    lockedAutoSkip: false,
    loadToken: 0,
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

  function typeName(value) {
    if (value === 'film') return 'фильм';
    if (value === 'series') return 'сериал';
    return value || '';
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

  function withProgramId(template, programId) {
    return template.replace(/\/0\/$/, `/${programId}/`);
  }

  function itemUrl(programId) {
    return withProgramId(URLS.item, programId);
  }

  function lockUrl(programId) {
    return withProgramId(URLS.lock, programId);
  }

  function unlockUrl(programId) {
    return withProgramId(URLS.unlock, programId);
  }

  function isBusy(item) {
    return Boolean(item && item.locked_by && Number(item.locked_by) !== ME);
  }

  function findAvailableIndex(items, start, direction) {
    for (let i = start; i >= 0 && i < items.length; i += direction) {
      if (!isBusy(items[i])) return i;
    }
    return -1;
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
      body: JSON.stringify(payload || {}),
    });
    return response.json();
  }

  function filters() {
    const params = new URLSearchParams();
    if (el.bucket.value) params.set('bucket', el.bucket.value);
    if (el.channel?.value) params.set('channel', el.channel.value);
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

  // --- Модальное окно (стандартное для Планера) ---------------------------

  function showError(message, title = 'Ошибка!') {
    if (!el.errorModal) { alert(message); return; }
    state.lockedProgramId = null;
    state.lockedAutoSkip = false;
    el.errorTitle.textContent = title;
    el.errorMessage.textContent = message;
    if (el.errorTake) el.errorTake.classList.add('d-none');
    getErrorModal().show();
  }

  function showLockedWarning(programId, editorName, autoSkip = false) {
    const message = editorName
      ? `Материал занят ${editorName}`
      : 'Материал занят другим редактором';
    if (!el.errorModal) {
      alert(message);
      if (autoSkip) openAvailable(state.index + 1, 1);
      return;
    }
    state.lockedProgramId = programId;
    state.lockedAutoSkip = autoSkip;
    el.errorTitle.textContent = 'Материал занят';
    el.errorMessage.textContent = message;
    if (el.errorTake) el.errorTake.classList.toggle('d-none', !IS_CHIEF);
    getErrorModal().show();
  }

  function onErrorModalHidden() {
    const programId = state.lockedProgramId;
    state.lockedProgramId = null;
    if (!state.lockedAutoSkip || !programId) return;
    state.lockedAutoSkip = false;
    openAvailable(state.index + 1, 1);
  }

  async function takeLockedCard() {
    const programId = state.lockedProgramId;
    if (!programId) return;
    state.lockedProgramId = null;
    state.lockedAutoSkip = false;
    getErrorModal().hide();
    const result = await postJson(lockUrl(programId), { force: true });
    if (result.status !== 'success') {
      showError(result.message || 'Не удалось забрать карточку');
      return;
    }
    const index = state.items.findIndex(
      (item) => Number(item.oplan_program_id) === Number(programId));
    if (index >= 0) {
      state.items[index].locked_by = null;
      state.items[index].locked_by_name = null;
    }
    await loadItem(index >= 0 ? index : state.index, { manual: true, hops: 0 });
  }

  // --- Аренда карточки -----------------------------------------------------

  async function claimCard(programId, force = false) {
    return postJson(lockUrl(programId), force ? { force: true } : {});
  }

  function stopHeartbeat() {
    if (state.heartbeatTimer) {
      clearInterval(state.heartbeatTimer);
      state.heartbeatTimer = null;
    }
  }

  function startHeartbeat() {
    stopHeartbeat();
    state.heartbeatTimer = setInterval(renewLock, HEARTBEAT_MS);
  }

  function releaseLock(programId) {
    if (!programId) return;
    try {
      fetch(unlockUrl(programId), {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': CSRF,
        },
        keepalive: true,
      }).catch(() => {});
    } catch (error) {
      // ignore
    }
    if (Number(state.lockedId) === Number(programId)) {
      state.lockedId = null;
      stopHeartbeat();
    }
  }

  function markBusy(programId, lockData) {
    const item = state.items.find(
      (candidate) => Number(candidate.oplan_program_id) === Number(programId));
    if (!item) return;
    item.locked_by = lockData.editor_id ?? ME;
    item.locked_by_name = lockData.editor_name || '';
    renderQueue();
  }

  async function renewLock() {
    if (!state.lockedId || document.hidden) return;
    const programId = state.lockedId;
    try {
      const result = await claimCard(programId);
      if (result.status === 'locked') {
        markBusy(programId, result);
        if (Number(state.lockedId) === Number(programId)) {
          state.lockedId = null;
          stopHeartbeat();
        }
        showLockedWarning(programId, result.editor_name, true);
      } else if (result.status !== 'success') {
        stopHeartbeat();
      }
    } catch (error) {
      // сеть моргнула — попробуем на следующем тике
    }
  }

  // --- Очередь -------------------------------------------------------------

  async function loadQueue(offset = 0, selectIndex = 0, keepDecided = false,
                           preferLast = false, hops = 0) {
    state.loadToken += 1;
    const decided = state.decided;
    el.queueList.innerHTML = '<div class="p-3 text-muted">Загрузка…</div>';
    const params = filters();
    params.set('limit', String(state.limit));
    params.set('offset', String(Math.max(0, offset)));
    let data;
    try {
      data = await getJson(`${URLS.queue}?${params.toString()}`);
    } catch (error) {
      el.queueList.innerHTML =
        `<div class="p-3 text-danger">Ошибка загрузки очереди: ${esc(error.message)}</div>`;
      showError(`Не удалось загрузить очередь: ${error.message}`);
      return;
    }
    state.items = data.items || [];
    state.total = Number(data.total) || 0;
    state.offset = Number(data.offset) || 0;
    state.index = 0;
    state.decided = keepDecided ? decided : [];
    renderQueue();
    updateProgress();

    if (!state.items.length) {
      if (state.total > 0 && state.offset > 0 && hops < 3) {
        await loadQueue(0, 0, keepDecided, false, hops + 1);
        return;
      }
      showEmptyState();
      return;
    }

    const start = preferLast
      ? state.items.length - 1
      : Math.min(Math.max(0, selectIndex), state.items.length - 1);
    const direction = preferLast ? -1 : 1;
    const index = findAvailableIndex(state.items, start, direction);
    if (index >= 0) {
      await loadItem(index, { hops });
      return;
    }

    if (!preferLast && hops < 10
        && state.offset + state.limit < state.total) {
      await loadQueue(state.offset + state.limit, 0, keepDecided, false, hops + 1);
      return;
    }
    if (preferLast && hops < 10 && state.offset > 0) {
      await loadQueue(Math.max(0, state.offset - state.limit), 0, keepDecided, true, hops + 1);
      return;
    }
    showEmptyState('Все материалы на этой странице заняты другими редакторами.');
  }

  function renderQueue() {
    setQueueCount(state.items.length);
    setQueueTotal(state.total);
    updatePager();
    if (!state.items.length) {
      el.queueList.innerHTML = '<div class="p-3 text-muted">Нет материалов по фильтру.</div>';
      return;
    }
    el.queueList.innerHTML = state.items.map((item, i) => {
      const busy = isBusy(item);
      const classes = [
        'list-group-item', 'list-group-item-action',
        i === state.index ? 'active' : '',
        busy ? 'fi-busy' : '',
      ].filter(Boolean).join(' ');
      const lockLine = busy
        ? `<small class="d-block text-warning">🔒 ${esc(item.locked_by_name || 'занято')}</small>`
        : '';
      return `
      <button type="button" class="${classes}" data-index="${i}">
        <div class="d-flex justify-content-between">
          <span class="text-truncate me-2">${esc(item.name)}</span>
          <small class="text-nowrap">${esc(item.production_year || '')}</small>
        </div>
        ${lockLine}
      </button>`;
    }).join('');
    el.queueList.querySelectorAll('[data-index]').forEach((node) => {
      node.addEventListener('click', () => {
        loadItem(Number(node.dataset.index), { manual: true, hops: 0 });
      });
    });
    const active = el.queueList.querySelector('.active');
    if (active) active.scrollIntoView({ block: 'nearest' });
  }

  async function changePage(delta, atEnd = false) {
    const offset = state.offset + delta * state.limit;
    if (offset < 0 || offset >= state.total) return;
    await loadQueue(offset, 0, false, atEnd, 0);
  }

  async function openAvailable(startIndex, direction = 1, hops = 0) {
    if (hops > 20) {
      showEmptyState('Не удалось найти свободный материал.');
      return;
    }
    const index = findAvailableIndex(state.items, startIndex, direction);
    if (index >= 0) {
      await loadItem(index, { hops });
      return;
    }
    if (direction > 0) {
      if (state.offset + state.limit < state.total) {
        await loadQueue(state.offset + state.limit, 0, true, false, hops + 1);
        return;
      }
      showEmptyState('Все материалы на этой странице заняты другими редакторами.');
      return;
    }
    if (state.offset > 0) {
      await loadQueue(Math.max(0, state.offset - state.limit), 0, true, true, hops + 1);
      return;
    }
    // Начало очереди — просто остаёмся на текущей карточке.
  }

  async function loadItem(i, options = {}) {
    if (i < 0 || i >= state.items.length) return;
    const token = ++state.loadToken;
    const hops = options.hops || 0;
    const item = state.items[i];
    const programId = Number(item.oplan_program_id);

    let claim;
    try {
      claim = await claimCard(programId);
    } catch (error) {
      showError(`Не удалось заблокировать карточку: ${error.message}`);
      return;
    }
    if (token !== state.loadToken) {
      if (claim.status === 'success' && claim.locked !== false) {
        releaseLock(programId);
      }
      return;
    }
    if (claim.status === 'locked') {
      markBusy(programId, claim);
      if (options.manual) {
        showLockedWarning(programId, claim.editor_name, false);
      } else {
        openAvailable(i + 1, 1, hops + 1);
      }
      return;
    }
    if (claim.status !== 'success') {
      showError(claim.message || 'Не удалось заблокировать карточку');
      return;
    }

    if (state.lockedId && Number(state.lockedId) !== programId) {
      releaseLock(state.lockedId);
    }
    if (claim.locked === false) {
      // История (resolved/rejected) не блокируется.
      state.lockedId = null;
      stopHeartbeat();
    } else {
      state.lockedId = programId;
      startHeartbeat();
    }

    state.index = i;
    state.selected = 0;
    renderQueue();
    updateProgress();

    el.materialPane.innerHTML = '<div class="card"><div class="card-body text-muted">Загрузка…</div></div>';
    el.candidates.innerHTML = '';
    try {
      const data = await getJson(itemUrl(programId));
      if (token !== state.loadToken) {
        releaseLock(programId);
        return;
      }
      state.material = data.material;
      state.candidates = data.candidates || [];
      renderMaterial(data);
      renderCandidates();
    } catch (error) {
      if (token !== state.loadToken) {
        releaseLock(programId);
        return;
      }
      el.materialPane.innerHTML = `<div class="card"><div class="card-body text-danger">Ошибка загрузки: ${esc(error.message)}</div></div>`;
    }
  }

  function showEmptyState(message) {
    if (state.lockedId) releaseLock(state.lockedId);
    state.material = null;
    state.candidates = [];
    el.materialPane.innerHTML =
      `<div class="card"><div class="card-body text-muted">${esc(message || 'Очередь пуста. Настройте фильтры в правой панели.')}</div></div>`;
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
    const typeLabel = typeName(candidate.type);
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
    if (query.length < 3) {
      el.searchResults.innerHTML = '<div class="text-muted">Введите минимум 3 символа.</div>';
      return;
    }
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
              <div class="small">${esc(item.year || '—')} · ${esc((item.countries || []).join(', '))} · ${esc(typeName(item.type))}</div>
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
      if (result.status === 'locked') {
        markBusy(payload.program_id, result);
        showLockedWarning(payload.program_id, result.editor_name, true);
        return;
      }
      if (result.status !== 'success') {
        showError(result.message || 'Ошибка');
        return;
      }
      state.decided.push({ program_id: payload.program_id, action: payload.action });
      // Сервер снимает аренду при решении.
      if (Number(state.lockedId) === Number(payload.program_id)) {
        state.lockedId = null;
        stopHeartbeat();
      }
      if (!leavesFilter(payload.action)) {
        await openAvailable(state.index + 1, 1);
        return;
      }
      state.items.splice(state.index, 1);
      state.total = Math.max(0, state.total - 1);
      if (state.index >= state.items.length) {
        state.index = Math.max(0, state.items.length - 1);
      }
      renderQueue();
      updateProgress();
      if (state.items.length) {
        await openAvailable(state.index, 1);
      } else if (state.total > state.offset) {
        await loadQueue(state.offset, 0, true);
      } else if (state.offset > 0) {
        await loadQueue(Math.max(0, state.offset - state.limit), 0, true, true);
      } else {
        showEmptyState();
      }
    } catch (error) {
      showError(`Ошибка сохранения решения: ${error.message}`);
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
      if (result.status === 'locked') {
        showLockedWarning(last.program_id, result.editor_name, false);
        return;
      }
      if (result.status !== 'success') { showError(result.message || 'Ошибка'); return; }
      await loadQueue(state.offset);
      let position = state.items.findIndex((item) => item.oplan_program_id === last.program_id);
      if (position < 0 && state.offset > 0) {
        await loadQueue(0);
        position = state.items.findIndex((item) => item.oplan_program_id === last.program_id);
      }
      state.decided = [];
      if (position >= 0) await loadItem(position, { manual: false, hops: 0 });
    } catch (error) {
      showError(`Ошибка отмены решения: ${error.message}`);
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
    await openAvailable(state.index + delta, delta > 0 ? 1 : -1);
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
    if (el.errorModal && el.errorModal.classList.contains('show')) return;
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
  if (el.errorTake) el.errorTake.addEventListener('click', takeLockedCard);
  if (el.errorModal) el.errorModal.addEventListener('hidden.bs.modal', onErrorModalHidden);

  window.addEventListener('resize', fitHeight);
  window.addEventListener('load', fitHeight);
  window.addEventListener('pagehide', () => {
    if (state.lockedId) releaseLock(state.lockedId);
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && state.lockedId) renewLock();
  });
  fitHeight();
  loadQueue();
})();
