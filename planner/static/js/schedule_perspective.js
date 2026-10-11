(function () {
  'use strict';

  document.documentElement.setAttribute('data-bs-theme', 'dark');

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
    pending: null, // {day, position, card}
  };

  const els = {
    channel: document.getElementById('sp-channel'),
    start: document.getElementById('sp-start'),
    days: document.getElementById('sp-days-select'),
    prev: document.getElementById('sp-prev'),
    next: document.getElementById('sp-next'),
    searchOpen: document.getElementById('sp-search-open'),
    approve: document.getElementById('sp-approve'),
    finalize: document.getElementById('sp-finalize'),
    reopen: document.getElementById('sp-reopen'),
    downloads: document.getElementById('sp-downloads'),
    targetHours: document.getElementById('sp-target-hours'),
    daysBox: document.getElementById('sp-days'),
    modalEl: document.getElementById('sp-search-modal'),
    modal: null,
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

  const STATUS_LABEL = {
    draft: 'Черновик',
    chief_approved: 'Утв. главным',
    final_approved: 'Финал',
  };

  // --- Рендер окна ----------------------------------------------------------

  function loadWindow() {
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
    const data = state.current;
    els.daysBox.innerHTML = '';
    data.day_list.forEach((day) => {
      els.daysBox.appendChild(renderDay(day, data));
    });
    bindSortable();
  }

  function renderDay(day, data) {
    const col = document.createElement('div');
    col.className = 'sp-day';
    col.dataset.day = day.date;

    const header = document.createElement('div');
    header.className = 'sp-day-header';
    const statusClass = 'sp-status sp-status-' + day.status;
    header.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span class="sp-day-date">${humanDate(day.date)}</span>
        <span class="${statusClass}">${STATUS_LABEL[day.status] || day.status}</span>
      </div>
      <div class="sp-day-meta">
        <span>${framesToTime(day.total_frames)}</span>
        <span class="float-end">цель ${state.targetHours}:00:00</span>
      </div>`;
    col.appendChild(header);

    const slots = document.createElement('div');
    slots.className = 'sp-slots';
    slots.dataset.day = day.date;
    day.slots.forEach((slot) => slots.appendChild(renderSlot(slot)));
    col.appendChild(slots);

    if (state.canEdit) {
      const placeholders = document.createElement('div');
      placeholders.className = 'sp-placeholders';
      placeholders.dataset.day = day.date;
      const nextPos = day.slots.reduce((m, s) => Math.max(m, s.position), -1) + 1;
      for (let i = 0; i < 4; i++) {
        const pos = nextPos + i;
        const ph = document.createElement('div');
        ph.className = 'sp-placeholder my-1';
        ph.textContent = '+ слот';
        ph.addEventListener('click', () => openSearch(day.date, pos));
        placeholders.appendChild(ph);
      }
      col.appendChild(placeholders);
    }
    return col;
  }

  function renderSlot(slot) {
    const el = document.createElement('div');
    el.className = 'sp-slot' + (slot.in_base ? '' : ' sp-missing');
    el.dataset.slotId = slot.id;
    el.dataset.day = slot.day_date;

    const episode = slot.kind === 3
      ? `S${pad(slot.season_num || 1)}E${pad(slot.episode_num || 1)} `
      : '';
    const repeat = slot.is_repeat ? '<span class="sp-badge-repeat ms-1">повтор</span>' : '';
    const status = slot.in_base ? '' : ' <span class="text-danger">скачать</span>';

    el.innerHTML = `
      <span class="sp-slot-title">${episode}${escapeHtml(slot.title)}${repeat}</span>
      <span class="sp-slot-meta">${framesToTime(slot.duration_frames)}${status}</span>
      <span class="sp-slot-actions">
        <button class="btn btn-sm btn-outline-danger py-0 px-1" data-action="delete" title="Удалить">×</button>
      </span>`;

    if (state.canEdit) {
      el.querySelector('[data-action="delete"]').addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('Удалить слот?')) {
          apiPost(URLs.slotDelete, { slot_id: slot.id }).then(loadWindow);
        }
      });
    }
    el.addEventListener('mouseenter', (e) => showTooltip(slot, e));
    el.addEventListener('mouseleave', hideTooltip);
    return el;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : text;
    return div.innerHTML;
  }

  // --- Sortable -------------------------------------------------------------

  function bindSortable() {
    document.querySelectorAll('.sp-slots').forEach((container) => {
      if (container._sortable) container._sortable.destroy();
      if (!state.canEdit) return;
      container._sortable = new Sortable(container, {
        group: 'sp',
        animation: 150,
        ghostClass: 'sp-ghost',
        onEnd(evt) {
          const toDay = evt.to.dataset.day;
          const newIndex = evt.newIndex;
          apiPost(URLs.slotMove, {
            slot_id: evt.item.dataset.slotId,
            day: toDay,
            position: newIndex,
          }).then(loadWindow);
        },
      });
    });
  }

  // --- Поиск ----------------------------------------------------------------

  function openSearch(day, position, card) {
    if (!state.canEdit) return;
    state.pending = { day, position, card: card || null };
    document.getElementById('sp-target-date').textContent = humanDate(day);
    showStep('search');
    const input = document.getElementById('sp-search-input');
    input.value = '';
    document.getElementById('sp-search-results').innerHTML = '';
    if (!els.modal) els.modal = new bootstrap.Modal(els.modalEl);
    els.modal.show();
    setTimeout(() => input.focus(), 200);

    if (card) selectResult(card);
  }

  function showStep(step) {
    document.getElementById('sp-search-step').classList.toggle('d-none', step !== 'search');
    document.getElementById('sp-series-step').classList.toggle('d-none', step !== 'series');
  }

  let searchTimer = null;
  function onSearchInput() {
    clearTimeout(searchTimer);
    const q = this.value.trim();
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
      el.className = 'list-group-item sp-result';
      const badge = card.in_base
        ? '<span class="sp-result-badge base">в базе</span>'
        : '<span class="sp-result-badge missing">нужно скачать</span>';
      const kind = card.kind === 'series' ? 'сериал' : 'фильм';
      el.innerHTML = `
        <img src="${URLs.poster}?kp_id=${card.kinopoisk_id}" onerror="this.src='/static/img/no_poster.jpg'">
        <div class="flex-grow-1">
          <div class="sp-result-title">${escapeHtml(card.title)}</div>
          <div class="sp-result-meta">${card.year || ''} · ${kind} · ${escapeHtml(card.director || '')}</div>
        </div>
        ${badge}`;
      el.addEventListener('click', () => selectResult(card));
      box.appendChild(el);
    });
  }

  function selectResult(card) {
    state.pending.card = card;
    if (card.kind === 'series') {
      openSeriesStep(card);
    } else {
      addFilm(card);
    }
  }

  function addFilm(card) {
    const p = state.pending;
    const payload = {
      channel: state.channel,
      day: p.day,
      position: p.position,
      kind: 'film',
      kinopoisk_id: card.kinopoisk_id,
      oplan_program_id: card.oplan_program_id || null,
      title: card.title,
    };
    apiPost(URLs.slotAdd, payload).then((res) => {
      if (res.status === 'success') { els.modal.hide(); loadWindow(); }
      else alert(res.message || 'Ошибка');
    });
  }

  function openSeriesStep(card) {
    showStep('series');
    document.getElementById('sp-series-title').textContent = card.title;
    const structure = card._structure;
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

    if (structure) { applyStructure(structure); }
    else {
      apiGet(URLs.structure.replace('/0/', `/${card.kinopoisk_id}/`)).then((data) => {
        applyStructure(data.structure);
      });
    }
  }

  function addSeries() {
    const card = state.pending.card;
    const seasonNum = parseInt(document.getElementById('sp-season-num').value, 10);
    const payload = {
      channel: state.channel,
      day: state.pending.day,
      position: state.pending.position,
      kind: 'series',
      kinopoisk_id: card.kinopoisk_id,
      title: card.title,
    };
    const struct = card._structure;
    if (struct && struct.seasons && struct.seasons.length) {
      const seasonIndex = parseInt(document.getElementById('sp-season-select').value, 10) || 0;
      payload.season_num = seasonIndex + 1;
      payload.episode_from = parseInt(document.getElementById('sp-ep-from').value, 10) || 1;
      payload.episode_to = parseInt(document.getElementById('sp-ep-to').value, 10) || payload.episode_from;
    } else {
      payload.season_num = seasonNum || 1;
      payload.episode_from = parseInt(document.getElementById('sp-manual-from').value, 10) || 1;
      payload.episode_to = parseInt(document.getElementById('sp-manual-to').value, 10) || payload.episode_from;
    }
    apiPost(URLs.slotAdd, payload).then((res) => {
      if (res.status === 'success') { els.modal.hide(); loadWindow(); }
      else alert(res.message || 'Ошибка');
    });
  }

  // --- Тултип ---------------------------------------------------------------

  let tooltipCache = {};
  function showTooltip(slot, evt) {
    const pop = document.getElementById('sp-popover');
    const info = slot.oplan_program_id
      ? (tooltipCache['o' + slot.oplan_program_id] || null)
      : (tooltipCache['k' + slot.kinopoisk_id] || null);
    if (info) { renderTooltip(pop, slot, info); positionTooltip(pop, evt); return; }

    const params = slot.oplan_program_id
      ? `oplan_ids=${slot.oplan_program_id}`
      : `kp_ids=${slot.kinopoisk_id}`;
    apiGet(`${URLs.filmInfo}?${params}`).then((data) => {
      const map = slot.oplan_program_id ? data.oplan : data.kinopoisk;
      const key = slot.oplan_program_id ? 'o' + slot.oplan_program_id : 'k' + slot.kinopoisk_id;
      const info = map ? Object.values(map)[0] : null;
      if (info) tooltipCache[key] = info;
      renderTooltip(pop, slot, info || {});
      positionTooltip(pop, evt);
    });
  }

  function renderTooltip(pop, slot, info) {
    const countries = Array.isArray(info.countries) ? info.countries.join(', ') : (info.countries || '');
    const genres = Array.isArray(info.genres) ? info.genres.join(', ') : (info.genres || '');
    const poster = slot.kinopoisk_id
      ? `<img src="${URLs.poster}?kp_id=${slot.kinopoisk_id}" onerror="this.style.display='none'">`
      : '';
    pop.innerHTML = `
      ${poster}
      <div class="fw-bold">${escapeHtml(info.title || slot.title)}</div>
      ${info.original_title ? `<div class="text-muted small">${escapeHtml(info.original_title)}</div>` : ''}
      <div class="small mt-1">
        ${info.year ? `Год: ${info.year}<br>` : ''}
        ${countries ? `Страна: ${escapeHtml(countries)}<br>` : ''}
        ${genres ? `Жанры: ${escapeHtml(genres)}<br>` : ''}
        ${info.director ? `Режиссёр: ${escapeHtml(info.director)}<br>` : ''}
        ${info.rating ? `Рейтинг: ${info.rating}<br>` : ''}
        ${slot.in_base ? '<span class="text-success">В базе</span>' : '<span class="text-danger">Нужно скачать</span>'}
      </div>`;
    pop.classList.remove('d-none');
  }

  function positionTooltip(pop, evt) {
    pop.style.left = Math.min(evt.clientX + 14, window.innerWidth - 340) + 'px';
    pop.style.top = Math.min(evt.clientY + 14, window.innerHeight - 220) + 'px';
  }

  function hideTooltip() {
    document.getElementById('sp-popover').classList.add('d-none');
  }

  // --- Тулбар ---------------------------------------------------------------

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
    apiPost(URLs.dayStatus, {
      channel: state.channel, dates,
    }).then((res) => {
      if (res.status !== 'success') { alert(res.message || 'Ошибка'); return; }
      // Список скачивания формируется утверждением дня.
      let pending = 0;
      const tasks = dates.map((day) =>
        apiPost(URLs.downloads, { channel: state.channel, day }).then((r) => {
          pending += (r.items || []).length;
          return r;
        }));
      Promise.all(tasks).then(() => {
        alert(`Утверждено дней: ${dates.length}. Позиций в списке скачивания: ${pending}.`);
        loadWindow();
      });
    });
  }

  function generateDownloads() {
    const dates = state.current.day_list.map((d) => d.date);
    let pending = 0;
    Promise.all(dates.map((day) =>
      apiPost(URLs.downloads, { channel: state.channel, day }).then((r) => {
        pending += (r.items || []).length;
        return r;
      }))).then(() => {
      alert(`Список скачивания (имитация). Позиций: ${pending}.`);
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
    els.searchOpen.addEventListener('click', () => {
      const first = state.current.day_list[0];
      const nextPos = first.slots.reduce((m, s) => Math.max(m, s.position), -1) + 1;
      openSearch(first.date, nextPos);
    });
    if (els.approve) els.approve.addEventListener('click', approvePeriod);
    if (els.finalize) els.finalize.addEventListener('click', () => changeStatus('finalize'));
    if (els.reopen) els.reopen.addEventListener('click', () => changeStatus('reopen'));
    if (els.downloads) els.downloads.addEventListener('click', generateDownloads);

    document.getElementById('sp-search-input').addEventListener('input', onSearchInput);
    document.getElementById('sp-series-back').addEventListener('click', () => showStep('search'));
    document.getElementById('sp-series-add').addEventListener('click', addSeries);
    document.getElementById('sp-season-select').addEventListener('change', () => {});
  }

  // --- Инициализация --------------------------------------------------------

  els.start.value = state.start;
  bindToolbar();
  loadWindow();
})();
