(function () {
  'use strict';

  const root = document.getElementById('schedule-perspective');
  if (!root) return;

  const URLs = {
    window: root.dataset.windowUrl,
    search: root.dataset.searchUrl,
    structure: root.dataset.structureUrl,
    filmInfo: root.dataset.filmInfoUrl,
    poster: root.dataset.posterUrl,
    slotAdd: root.dataset.slotAddUrl,
    slotMove: root.dataset.slotMoveUrl,
    slotDelete: root.dataset.slotDeleteUrl,
    downloads: root.dataset.downloadUrl,
    dayStatus: root.dataset.dayStatusUrl,
    export: root.dataset.exportUrl,
  };

  const state = {
    channel: parseInt(root.dataset.defaultChannel, 10) || 3,
    start: root.dataset.defaultStart,
    days: parseInt(root.dataset.defaultDays, 10) || 7,
    canEdit: root.dataset.canEdit === '1',
    fps: 25,
    defaultFrames: 90 * 60 * 25,
    targetHours: 8,
    current: null,
    pending: null, // {day, position}
    selectedCard: null,
  };

  const els = {
    channel: document.getElementById('sp-channel'),
    start: document.getElementById('sp-start'),
    days: document.getElementById('sp-days-select'),
    prev: document.getElementById('sp-prev'),
    next: document.getElementById('sp-next'),
    approve: document.getElementById('sp-approve'),
    finalize: document.getElementById('sp-finalize'),
    reopen: document.getElementById('sp-reopen'),
    export: document.getElementById('sp-export'),
    targetHours: document.getElementById('sp-target-hours'),
    daysBox: document.getElementById('sp-days'),
    searchInput: document.getElementById('sp-search-input'),
    searchPanel: document.getElementById('sp-search-panel'),
    searchWrap: document.querySelector('.sp-search-wrap'),
    searchHint: document.getElementById('sp-search-hint'),
  };

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[2]) : '';
  }

  function apiPost(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'same-origin',
      body: JSON.stringify(data || {}),
    }).then((r) => r.json());
  }

  function apiGet(url) {
    return fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    }).then((r) => r.json());
  }

  // --- Подтверждение через Bootstrap-модалку (вместо window.confirm) ---------

  let confirmModal = null;
  let confirmCallback = null;

  function askConfirm(text, callback) {
    document.getElementById('sp-confirm-text').textContent = text;
    confirmCallback = callback;
    if (!confirmModal) {
      confirmModal = new bootstrap.Modal(document.getElementById('sp-confirm-modal'));
      document.getElementById('sp-confirm-ok').addEventListener('click', () => {
        const cb = confirmCallback;
        confirmCallback = null;
        confirmModal.hide();
        if (cb) cb();
      });
    }
    confirmModal.show();
  }

  // --- Форматирование -------------------------------------------------------

  function pad(n) { return String(n).padStart(2, '0'); }

  function framesToTime(frames) {
    frames = parseInt(frames, 10) || 0;
    const sec = frames / state.fps;
    const hh = Math.floor(sec / 3600);
    const mm = Math.floor((sec % 3600) / 60);
    const ss = Math.floor(sec % 60);
    return `${pad(hh)}:${pad(mm)}:${pad(ss)}`;
  }

  function humanDate(iso) {
    const [y, m, d] = iso.split('-');
    return `${d}.${m}.${y}`;
  }

  // Счётчик дня: пока пусто — отрицательный остаток, при переполнении — плюс.
  function dayCounter(totalFrames, targetHours) {
    const target = (targetHours || 0) * 3600 * state.fps;
    const diff = (parseInt(totalFrames, 10) || 0) - target;
    const sign = diff > 0 ? '+' : (diff < 0 ? '-' : '');
    return {
      text: sign + framesToTime(Math.abs(diff)),
      cls: diff > 0 ? 'over' : (diff < 0 ? 'left' : 'done'),
    };
  }

  function kpUrl(kpId, kind) {
    if (!kpId) return null;
    const section = kind === 'series' ? 'series' : 'film';
    return `https://www.kinopoisk.ru/${section}/${kpId}/`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : text;
    return div.innerHTML;
  }

  const STATUS_LABEL = {
    draft: 'Черновик',
    chief_approved: 'Утв. главным',
    final_approved: 'Финал',
  };

  // --- Рендер окна ----------------------------------------------------------

  function loadWindow() {
    hideTooltip();
    const url = `${URLs.window}?channel=${state.channel}&start=${state.start}&days=${state.days}`;
    apiGet(url).then((data) => {
      if (data.status !== 'success') { console.error(data); return; }
      state.current = data;
      state.canEdit = data.can_edit;
      state.fps = data.fps || 25;
      state.defaultFrames = data.default_duration_frames || state.defaultFrames;
      state.targetHours = data.target_hours || 8;
      els.targetHours.textContent = `${state.targetHours}:00:00`;
      render();
    });
  }

  function render() {
    els.daysBox.innerHTML = '';
    state.current.day_list.forEach((day) => els.daysBox.appendChild(renderDay(day)));
    bindSortable();
    fitHeight();
  }

  // Подгоняем высоту так, чтобы страница не скроллилась: модуль занимает
  // ровно оставшееся место под шапкой сайта.
  function fitHeight() {
    const top = root.getBoundingClientRect().top;
    root.style.height = Math.max(320, window.innerHeight - top) + 'px';
  }

  function renderDay(day) {
    const col = document.createElement('div');
    col.className = 'sp-day';
    col.dataset.day = day.date;

    // Правка разрешена только в черновике (и только senior_editor).
    const editable = state.canEdit && day.status === 'draft';
    const counter = dayCounter(day.total_frames, state.targetHours);
    const header = document.createElement('div');
    header.className = 'sp-day-header';
    header.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span class="sp-day-date">${humanDate(day.date)}</span>
        <span class="sp-status sp-status-${day.status}">${STATUS_LABEL[day.status] || day.status}</span>
      </div>
      <div class="sp-day-meta d-flex justify-content-between">
        <span>${framesToTime(day.total_frames)}</span>
        <span class="sp-day-counter ${counter.cls}">${counter.text}</span>
      </div>`;
    col.appendChild(header);

    const slots = document.createElement('div');
    slots.className = 'sp-slots';
    slots.dataset.day = day.date;
    slots.dataset.editable = editable ? '1' : '0';

    // Позиции явные: рисуем каждый индекс как слот или пустую ячейку,
    // чтобы можно было бросить/добавить материал в любую из них.
    const byPosition = new Map();
    let maxPos = -1;
    day.slots.forEach((s) => {
      byPosition.set(s.position, s);
      if (s.position > maxPos) maxPos = s.position;
    });
    // Защитный потолок: не рисуем больше 100 ячеек на день, чтобы мусорная
    // (слишком большая) позиция не подвесила браузер. Пустых «хвостовых»
    // ячеек добавляем ровно одну.
    const MAX_CELLS = 100;
    const lastPos = Math.min(editable ? maxPos + 1 : maxPos, MAX_CELLS - 1);
    for (let p = 0; p <= lastPos; p++) {
      if (byPosition.has(p)) {
        slots.appendChild(renderSlot(byPosition.get(p), editable));
      } else {
        slots.appendChild(renderCell(day.date, p, editable));
      }
    }
    col.appendChild(slots);
    return col;
  }

  function renderCell(dayId, position, editable) {
    const cell = document.createElement('div');
    cell.className = 'sp-cell';
    cell.dataset.position = position;
    if (editable) {
      cell.textContent = '+';
      cell.addEventListener('click', (e) => {
        e.stopPropagation();
        openForSlot(dayId, position);
      });
    }
    return cell;
  }

  function renderSlot(slot, editable) {
    const el = document.createElement('div');
    el.className = 'sp-slot' + (slot.in_base ? '' : ' sp-missing');
    el.dataset.slotId = slot.id;
    el.dataset.day = slot.day_date;

    // Высота пропорциональна хронометражу (1 минута ≈ 1px, в разумных пределах).
    const frames = parseInt(slot.duration_frames, 10) || state.defaultFrames;
    const minutes = frames / state.fps / 60;
    el.style.height = Math.max(55, Math.min(240, Math.round(minutes))) + 'px';

    const episode = slot.kind === 3
      ? `S${pad(slot.season_num || 1)}E${pad(slot.episode_num || 1)} `
      : '';
    const repeat = slot.is_repeat ? '<span class="sp-badge-repeat ms-1">повтор</span>' : '';
    const warn = slot.in_base ? '' : ' <span class="sp-slot-warn">скачать</span>';
    const link = kpUrl(slot.kinopoisk_id, slot.kind === 3 ? 'series' : 'film');

    const actions = [];
    if (link) {
      actions.push(`<a class="sp-kp-link" href="${link}" target="_blank" rel="noopener"
                      title="Открыть на Кинопоиске">
                      <img class="kp-logo" src="/static/img/kinopoisk.png" alt="Кинопоиск">
                    </a>`);
    }
    if (editable) {
      actions.push('<button class="btn btn-sm btn-outline-danger" data-action="delete" title="Удалить">×</button>');
    }

    el.innerHTML = `
      <div class="sp-slot-head">
        <span class="sp-slot-title">${episode}${escapeHtml(slot.title)}${repeat}</span>
        <span class="sp-slot-actions">${actions.join('')}</span>
      </div>
      <span class="sp-slot-meta">${framesToTime(slot.duration_frames)}${warn}</span>`;

    const del = el.querySelector('[data-action="delete"]');
    if (del) {
      del.addEventListener('click', (e) => {
        e.stopPropagation();
        askConfirm('Удалить слот из сетки?', () => {
          apiPost(URLs.slotDelete, { slot_id: slot.id }).then((res) => {
            if (res.status === 'success') { loadWindow(); }
            else { alert(res.message || 'Ошибка'); }
          });
        });
      });
    }
    el.addEventListener('mouseenter', (e) => showTooltip(slot, e));
    el.addEventListener('mouseleave', hideTooltip);
    return el;
  }

  function bindSortable() {
    document.querySelectorAll('.sp-slots').forEach((container) => {
      if (container._sortable) container._sortable.destroy();
      if (container.dataset.editable !== '1') return;
      container._sortable = new Sortable(container, {
        group: 'sp',
        animation: 150,
        ghostClass: 'sp-ghost',
        // Пустые ячейки — якоря для вставки (не перетаскиваются, но участвуют
        // в определении позиции). Слоты перетаскиваются.
        filter: '.sp-cell',
        preventOnFilter: false,
        onEnd(evt) {
          // Позиция = индекс слота среди ячеек целевого дня.
          const position = Array.from(evt.to.children).indexOf(evt.item);
          apiPost(URLs.slotMove, {
            slot_id: evt.item.dataset.slotId,
            day: evt.to.dataset.day,
            position: position,
          }).then(loadWindow);
        },
      });
    });
  }

  // --- Поиск (панель прямо под строкой) -------------------------------------

  function defaultTarget() {
    const first = state.current.day_list[0];
    const nextPos = first.slots.reduce((m, s) => Math.max(m, s.position), -1) + 1;
    return { day: first.date, position: nextPos };
  }

  function updateHint() {
    if (state.pending) {
      els.searchHint.textContent = `Добавить в: ${humanDate(state.pending.day)}`;
    } else {
      els.searchHint.textContent = '';
    }
  }

  function openForSlot(day, position) {
    if (!state.canEdit) return;
    state.pending = { day, position };
    updateHint();
    els.searchInput.focus();
    els.searchPanel.classList.remove('d-none');
  }

  function openPanel() {
    if (!state.pending) state.pending = defaultTarget();
    updateHint();
    els.searchPanel.classList.remove('d-none');
  }

  function closePanel() {
    els.searchPanel.classList.add('d-none');
    showStep('search');
  }

  function showStep(step) {
    document.getElementById('sp-search-step').classList.toggle('d-none', step !== 'search');
    document.getElementById('sp-series-step').classList.toggle('d-none', step !== 'series');
  }

  let searchTimer = null;
  function onSearchInput() {
    openPanel();
    clearTimeout(searchTimer);
    const q = els.searchInput.value.trim();
    if (q.length < 2) { document.getElementById('sp-search-results').innerHTML = ''; return; }
    searchTimer = setTimeout(() => {
      apiGet(`${URLs.search}?q=${encodeURIComponent(q)}`).then((data) => {
        renderResults(data.items || []);
      });
    }, 250);
  }

  function renderResults(items) {
    const box = document.getElementById('sp-search-results');
    box.innerHTML = '';
    if (!items.length) {
      box.innerHTML = '<div class="text-muted small p-2">Ничего не найдено</div>';
      return;
    }
    items.forEach((card) => {
      const el = document.createElement('div');
      el.className = 'sp-result';
      const badge = card.in_base
        ? '<span class="sp-result-badge base">в базе</span>'
        : '<span class="sp-result-badge missing">нет в базе</span>';
      const kind = card.kind === 'series' ? 'сериал' : 'фильм';
      const link = kpUrl(card.kinopoisk_id, card.kind);
      el.innerHTML = `
        <img src="${URLs.poster}?kp_id=${card.kinopoisk_id}" onerror="this.src='/static/img/no_poster.jpg'">
        <div class="flex-grow-1">
          <div class="sp-result-title">${escapeHtml(card.title)}</div>
          <div class="sp-result-meta">${card.year || ''} · ${kind} · ${escapeHtml(card.director || '')}</div>
        </div>
        <div class="d-flex flex-column align-items-end gap-1">
          ${badge}
          <a class="sp-kp-link" href="${link}" target="_blank" rel="noopener">Кинопоиск ↗</a>
        </div>`;
      el.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        selectResult(card);
      });
      box.appendChild(el);
    });
  }

  function selectResult(card) {
    state.selectedCard = card;
    if (card.kind === 'series') {
      openSeriesStep(card);
    } else {
      addFilm(card);
    }
  }

  function addFilm(card) {
    const p = state.pending || defaultTarget();
    apiPost(URLs.slotAdd, {
      channel: state.channel, day: p.day, position: p.position, kind: 'film',
      kinopoisk_id: card.kinopoisk_id,
      oplan_program_id: card.oplan_program_id || null,
      title: card.title,
    }).then((res) => {
      if (res.status === 'success') { finishAdd(); }
      else alert(res.message || 'Ошибка');
    });
  }

  function openSeriesStep(card) {
    showStep('series');
    document.getElementById('sp-series-title').textContent = card.title;
    const oplanBox = document.getElementById('sp-series-oplan');
    const manualBox = document.getElementById('sp-series-manual');

    const applyStructure = (struct) => {
      card._structure = struct;
      if (struct && struct.seasons && struct.seasons.length) {
        oplanBox.classList.remove('d-none');
        manualBox.classList.add('d-none');
        const select = document.getElementById('sp-season-select');
        select.innerHTML = '';
        struct.seasons.forEach((season, idx) => {
          const opt = document.createElement('option');
          opt.value = idx;
          opt.textContent = season.label || `Сезон ${idx + 1}`;
          select.appendChild(opt);
        });
        const first = struct.seasons[0];
        if (first.episodes.length) {
          document.getElementById('sp-ep-from').value = first.episodes[0].episode_num || 1;
          document.getElementById('sp-ep-to').value =
            first.episodes[first.episodes.length - 1].episode_num || 1;
        }
      } else {
        oplanBox.classList.add('d-none');
        manualBox.classList.remove('d-none');
      }
    };

    if (card._structure) { applyStructure(card._structure); }
    else {
      apiGet(URLs.structure.replace('/0/', `/${card.kinopoisk_id}/`)).then((data) => {
        applyStructure(data.structure);
      });
    }
  }

  function addSeries() {
    const card = state.selectedCard;
    const p = state.pending || defaultTarget();
    const payload = {
      channel: state.channel, day: p.day, position: p.position, kind: 'series',
      kinopoisk_id: card.kinopoisk_id, title: card.title,
    };
    const struct = card._structure;
    if (struct && struct.seasons && struct.seasons.length) {
      const seasonIndex = parseInt(document.getElementById('sp-season-select').value, 10) || 0;
      payload.season_num = seasonIndex + 1;
      payload.episode_from = parseInt(document.getElementById('sp-ep-from').value, 10) || 1;
      payload.episode_to = parseInt(document.getElementById('sp-ep-to').value, 10) || payload.episode_from;
    } else {
      payload.season_num = parseInt(document.getElementById('sp-season-num').value, 10) || 1;
      payload.episode_from = parseInt(document.getElementById('sp-manual-from').value, 10) || 1;
      payload.episode_to = parseInt(document.getElementById('sp-manual-to').value, 10) || payload.episode_from;
    }
    apiPost(URLs.slotAdd, payload).then((res) => {
      if (res.status === 'success') { finishAdd(); }
      else alert(res.message || 'Ошибка');
    });
  }

  function finishAdd() {
    els.searchInput.value = '';
    document.getElementById('sp-search-results').innerHTML = '';
    state.pending = null;
    state.selectedCard = null;
    closePanel();
    loadWindow();
  }

  // --- Тултип ---------------------------------------------------------------

  let tooltipCache = {};
  let tooltipSeq = 0;
  function showTooltip(slot, evt) {
    const pop = document.getElementById('sp-popover');
    const seq = ++tooltipSeq;
    const key = slot.oplan_program_id ? 'o' + slot.oplan_program_id : 'k' + slot.kinopoisk_id;
    const cached = tooltipCache[key];
    if (cached) {
      renderTooltip(pop, slot, cached);
      positionTooltip(pop, evt);
      return;
    }

    const params = slot.oplan_program_id
      ? `oplan_ids=${slot.oplan_program_id}`
      : `kp_ids=${slot.kinopoisk_id}`;
    apiGet(`${URLs.filmInfo}?${params}`).then((data) => {
      if (seq !== tooltipSeq) return;  // курсор уже ушёл или окно перестроено
      const map = slot.oplan_program_id ? data.oplan : data.kinopoisk;
      const info = map ? Object.values(map)[0] : null;
      if (info) tooltipCache[key] = info;
      renderTooltip(pop, slot, info || {});
      positionTooltip(pop, evt);
    });
  }

  function renderTooltip(pop, slot, info) {
    const countries = Array.isArray(info.countries) ? info.countries.join(', ') : (info.countries || '');
    const genres = Array.isArray(info.genres) ? info.genres.join(', ') : (info.genres || '');
    const posterParams = new URLSearchParams();
    if (slot.oplan_program_id) posterParams.set('program_id', slot.oplan_program_id);
    if (slot.kinopoisk_id) posterParams.set('kp_id', slot.kinopoisk_id);
    const poster = posterParams.toString()
      ? `<img src="${URLs.poster}?${posterParams.toString()}" onerror="this.style.display='none'">`
      : '';
    // Имя файла (Oplan orig_name) здесь не показываем — только данные Кинопоиска.
    pop.innerHTML = `
      <div class="sp-popover-inner">
        ${poster}
        <div class="sp-popover-text">
          ${info.title ? `<div class="fw-bold">${escapeHtml(info.title)}</div>` : ''}
          <div class="small mt-1">
            ${info.year ? `Год: ${info.year}<br>` : ''}
            ${countries ? `Страна: ${escapeHtml(countries)}<br>` : ''}
            ${genres ? `Жанры: ${escapeHtml(genres)}<br>` : ''}
            ${info.director ? `Режиссёр: ${escapeHtml(info.director)}<br>` : ''}
            ${info.rating ? `Рейтинг: ${info.rating}<br>` : ''}
            ${slot.in_base ? '<span class="text-success">В базе</span>' : '<span class="text-danger">Нужно скачать</span>'}
          </div>
        </div>
      </div>`;
    pop.classList.remove('d-none');
  }

  function positionTooltip(pop, evt) {
    pop.style.left = Math.min(evt.clientX + 14, window.innerWidth - 340) + 'px';
    pop.style.top = Math.min(evt.clientY + 14, window.innerHeight - 240) + 'px';
  }

  function hideTooltip() {
    tooltipSeq++;
    document.getElementById('sp-popover').classList.add('d-none');
  }

  // Глобальные страховки: тултип не должен «зависать» при уходе курсора
  // на модалку/пустое место, прокрутке, смене окна, Esc, alt-tab.
  function bindTooltipSafety() {
    const pop = document.getElementById('sp-popover');
    const isOpen = () => !pop.classList.contains('d-none');

    document.addEventListener('scroll', hideTooltip, true);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideTooltip();
    });
    window.addEventListener('blur', hideTooltip);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) hideTooltip();
    });
    document.addEventListener('show.bs.modal', hideTooltip, true);
    const confirmModal = document.getElementById('sp-confirm-modal');
    if (confirmModal) confirmModal.addEventListener('show.bs.modal', hideTooltip);
    document.addEventListener('pointermove', (e) => {
      if (isOpen() && !e.target.closest('.sp-slot')) hideTooltip();
    });
  }

  // --- Тулбар / статусы -----------------------------------------------------

  function shiftPeriod(deltaDays) {
    const [y, m, d] = state.start.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    dt.setDate(dt.getDate() + deltaDays);
    state.start = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
    els.start.value = state.start;
    loadWindow();
  }

  function dayStatusUrl(action) {
    return URLs.dayStatus.replace(/approve\/$/, action + '/');
  }

  function changeStatus(action) {
    const dates = state.current.day_list.map((d) => d.date);
    apiPost(dayStatusUrl(action), { channel: state.channel, dates }).then((res) => {
      if (res.status !== 'success') { alert(res.message || 'Ошибка'); return; }
      loadWindow();
    });
  }

  function approvePeriod() {
    const dates = state.current.day_list.map((d) => d.date);
    apiPost(URLs.dayStatus, { channel: state.channel, dates }).then((res) => {
      if (res.status !== 'success') { alert(res.message || 'Ошибка'); return; }
      // Список скачивания формируется утверждением дня.
      let pending = 0;
      Promise.all(dates.map((day) =>
        apiPost(URLs.downloads, { channel: state.channel, day }).then((r) => {
          pending += (r.items || []).length;
          return r;
        }))).then(() => {
        alert(`Утверждено дней: ${dates.length}. Позиций в списке скачивания: ${pending}.`);
        loadWindow();
      });
    });
  }

  function bindToolbar() {
    els.channel.addEventListener('change', () => {
      state.channel = parseInt(els.channel.value, 10);
      loadWindow();
    });
    els.start.addEventListener('change', () => {
      state.start = els.start.value;
      loadWindow();
    });
    els.days.addEventListener('change', () => {
      state.days = parseInt(els.days.value, 10);
      loadWindow();
    });
    els.prev.addEventListener('click', () => shiftPeriod(-state.days));
    els.next.addEventListener('click', () => shiftPeriod(state.days));
    if (els.export) {
      els.export.addEventListener('click', () => {
        window.location.href =
          `${URLs.export}?channel=${state.channel}&start=${state.start}&days=${state.days}`;
      });
    }
    if (els.approve) els.approve.addEventListener('click', approvePeriod);
    if (els.finalize) els.finalize.addEventListener('click', () => changeStatus('finalize'));
    if (els.reopen) els.reopen.addEventListener('click', () => changeStatus('reopen'));

    els.searchInput.addEventListener('focus', openPanel);
    els.searchInput.addEventListener('input', onSearchInput);
    document.getElementById('sp-series-back').addEventListener('click', () => showStep('search'));
    document.getElementById('sp-series-add').addEventListener('click', addSeries);

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.sp-search-wrap')) closePanel();
    });
  }

  // --- Инициализация --------------------------------------------------------

  els.start.value = state.start;
  bindToolbar();
  bindTooltipSafety();
  fitHeight();
  window.addEventListener('resize', fitHeight);
  loadWindow();
})();
