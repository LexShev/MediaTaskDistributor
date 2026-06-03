document.addEventListener('DOMContentLoaded', function() {
  calculateDuration();
  const dropdownMenu = document.getElementById('search_results');
  const searchQuery = document.getElementById('search_query');

  if (searchQuery && dropdownMenu) {
      ['input', 'click'].forEach(event => {
          searchQuery.addEventListener(event, function () {
              if (this.value.length > 0) {
                  searchProgram(this.value);
                  setTimeout(() => {
                      dropdownMenu.classList.add('show');
                  }, 300);
              }

          })
      })

    // Закрываем при клике вне области
    document.addEventListener('click', function(event) {
      if (!event.target.closest('.dropdown')) {
        dropdownMenu.classList.remove('show');
      }
    });

    // Скрываем при пустом вводе
    searchQuery.addEventListener('input', function() {
      if (this.value.length === 0) {
        setTimeout(() => {
            dropdownMenu.classList.remove('show');
        }, 300);
      }
    });

    // Предотвращаем закрытие при клике внутри меню
    dropdownMenu.addEventListener('click', function(event) {
      event.stopPropagation();
    });
  }
});

function searchProgram(query) {
    let oplanResults = document.getElementById('oplan_results');
    let kinopoiskResults = document.getElementById('kinopoisk_results');

    // Показываем загрузку в обоих контейнерах
    const spinnerHtml = `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 200px;">
            <div class="spinner-border text-primary spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>`;
    oplanResults.innerHTML = '<small class="text-muted fw-bold">Oplan</small>' + spinnerHtml;
    kinopoiskResults.innerHTML = '<small class="text-muted fw-bold">Kinopoisk</small>' + spinnerHtml;

    // Загружаем данные
    fetch('/schedule-perspective/search_program/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(query),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Очищаем контейнеры (оставляем только заголовок)
            oplanResults.innerHTML = '<small class="text-muted fw-bold">Oplan</small>';
            kinopoiskResults.innerHTML = '<small class="text-muted fw-bold">Kinopoisk</small>';

            // Отображаем результаты OPLAN
            if (data.search_list.length > 0) {
                data.search_list.forEach(program => {
                    let listItem = createProgramCard(program, 'oplan');
                    oplanResults.appendChild(listItem);
                });
            } else {
                oplanResults.innerHTML += '<div class="text-muted small mt-2">Ничего не найдено</div>';
            }

            // Отображаем результаты Kinopoisk
            if (data.kinopoisk_list.length > 0) {
                data.kinopoisk_list.forEach(program => {
                    let listItem = createKinopoiskCard(program);
                    kinopoiskResults.appendChild(listItem);
                });
            } else {
                kinopoiskResults.innerHTML += '<div class="text-muted small mt-2">Ничего не найдено</div>';
            }
        } else {
            console.log('error', data.message);
            oplanResults.innerHTML = '<small class="text-muted fw-bold">Oplan</small><div class="text-muted small mt-2">Ошибка поиска</div>';
            kinopoiskResults.innerHTML = '<small class="text-muted fw-bold">Kinopoisk</small><div class="text-muted small mt-2">Ошибка поиска</div>';
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
        oplanResults.innerHTML = '<small class="text-muted fw-bold">Oplan</small><div class="text-muted small mt-2">Ошибка соединения</div>';
        kinopoiskResults.innerHTML = '<small class="text-muted fw-bold">Kinopoisk</small><div class="text-muted small mt-2">Ошибка соединения</div>';
    });
}

function createProgramCard(program, source) {
    let listItem = document.createElement("div");
    listItem.classList.add('program', 'd-flex', 'rounded', 'my-2', 'align-items-center');
    listItem.dataset.oplanProgramId = program.Progs_program_id;
    listItem.dataset.duration = program.Progs_duration;
    listItem.dataset.source = source;

    let titleText = '';
    let tooltipText = '';

    if (source === 'oplan') {
        titleText = program.Progs_name || '';
        tooltipText = buildTooltip(program);
    }

    let imageContainer = document.createElement("div");
    imageContainer.classList.add('poster-container', 'align-items-center', 'm-2');
    imageContainer.style = "flex: 0 0 50px; max-width: 50px; height: 70px;";

    let image = document.createElement('img');
    let imgSrc = `/media/posters/${program.Progs_program_id}.jpg`;
    image.onerror = function() {
        this.onerror = null;
        this.src = '/static/img/no_poster.jpg';
    };
    image.src = imgSrc;
    image.classList.add('img-fluid', 'rounded', 'm-0', 'w-100', 'h-100', 'object-fit-cover');
    imageContainer.appendChild(image);
    listItem.appendChild(imageContainer);

    let nameContainer = document.createElement("div");
    // nameContainer.classList.add('flex-grow-1', 'overflow-hidden');
    listItem.appendChild(nameContainer);

    let header = document.createElement("h6");
    header.classList.add('my-0', 'p-1', 'text-truncate');
    header.innerText = titleText;
    if (tooltipText) {
        header.title = tooltipText;
    }
    nameContainer.appendChild(header);

    let footer = document.createElement("small");
    footer.classList.add('production-year', 'px-1', 'text-muted');
    if (program.Progs_production_year) {
        footer.innerText = program.Progs_production_year;
    }
    nameContainer.appendChild(footer);

    return listItem;
}

function createKinopoiskCard(program) {
    let listItem = document.createElement("div");
    listItem.classList.add('program', 'd-flex', 'rounded', 'my-2', 'align-items-center');
    listItem.dataset.kinopoiskId = program.kinopoisk_id;
    listItem.dataset.duration = program.duration * 25 || 0; // конвертируем минуты в кадры (25fps)
    listItem.dataset.source = 'kinopoisk';

    // Собираем tooltip
    let tooltipLines = [];
    if (program.year) tooltipLines.push(`- Год: ${program.year}`);
    if (program.countries && program.countries.length > 0) tooltipLines.push(`- Страна: ${program.countries.join(', ')}`);
    if (program.director) tooltipLines.push(`- Режиссёр: ${program.director}`);
    if (program.duration) tooltipLines.push(`- Длительность: ${program.duration} мин.`);
    if (program.rating) tooltipLines.push(`- Рейтинг: ${program.rating}`);
    if (program.genres && program.genres.length > 0) tooltipLines.push(`- Жанры: ${program.genres.join(', ')}`);
    let tooltipText = tooltipLines.join('\n');

    listItem.title = tooltipText;

    let imageContainer = document.createElement("div");
    imageContainer.classList.add('poster-container', 'align-items-center', 'm-2');
    imageContainer.style = "flex: 0 0 50px; max-width: 50px; height: 70px;";

    let image = document.createElement('img');
    // Кидаем запрос на кинопоисковый постер (заглушка)
    let imgSrc = `https://www.kinopoisk.ru//images/sm_film/${program.kinopoisk_id}.jpg`;
    image.onerror = function() {
        this.onerror = null;
        this.src = '/static/img/no_poster.jpg';
    };
    image.src = imgSrc;
    image.classList.add('img-fluid', 'rounded', 'm-0', 'w-100', 'h-100', 'object-fit-cover');
    imageContainer.appendChild(image);
    listItem.appendChild(imageContainer);

    let nameContainer = document.createElement("div");
    // nameContainer.classList.add('flex-grow-1', 'overflow-hidden');
    listItem.appendChild(nameContainer);

    let header = document.createElement("h6");
        header.classList.add('my-0', 'p-1', 'text-truncate');

        // Создаем ссылку на Кинопоиск
        let link = document.createElement("a");
        link.href = `https://www.kinopoisk.ru/film/${program.kinopoisk_id}/` || '#';
        link.target = '_blank';
        link.rel = 'noreferrer noopener';
        link.classList.add('link-body-emphasis', 'link-offset-3-hover', 'link-underline', 'link-underline-opacity-0', 'link-underline-opacity-75-hover');
        link.innerText = program.title || program.original_title || 'Без названия';

        header.appendChild(link);
        nameContainer.appendChild(header);

    let footer = document.createElement("small");
    footer.classList.add('production-year', 'px-1', 'text-muted');
    if (program.year) {
        footer.innerText = program.year + (program.rating ? ` | ${program.rating}` : '');
    } else if (program.rating) {
        footer.innerText = `Рейтинг: ${program.rating}`;
    }
    nameContainer.appendChild(footer);

    return listItem;
}

function buildTooltip(program) {
    let lines = [];
    if (program.Progs_production_year) lines.push(`- Год: ${program.Progs_production_year}`);
    if (program.Progs_production_country) lines.push(`- Страна: ${program.Progs_production_country}`);
    if (program.Progs_Director) lines.push(`- Режиссёр: ${program.Progs_Director}`);
    if (program.Progs_duration) lines.push(`- Длительность: ${convertFramesToTime(program.Progs_duration)}`);
    return lines.join('\n');
}

function moveData(evt) {
    console.log(evt.item);
    return {
        oplanProgramId: evt.item.dataset.oplanProgramId || null,
        kinopoiskId: evt.item.dataset.kinopoiskId || null,
        fromContainer: evt.from.id,
        toContainer: evt.to.id,
        oldIndex: evt.oldIndex,
        newIndex: evt.newIndex,
        isSameContainer: evt.from === evt.to
    }
}

function setupSortableForContainer(container, options = {}) {
    new Sortable(container, {
        group: {
            name: 'schedule',
            pull: options.pull !== undefined ? options.pull : true,
            put: options.put !== undefined ? options.put : true
        },
        animation: 200,
        ghostClass: "custom-ghost",
        chosenClass: "custom-chosen",
        dragClass: "custom-drag",
        sort: options.sort !== undefined ? options.sort : true,
        onEnd: function(evt) {
            const data = moveData(evt);
            saveMoveToServer(data);
            applyKinopoiskStyle(evt.item);
            calculateDuration();
        }
    });
}

function applyKinopoiskStyle(element) {
    // Если карточка из kinopoisk (нет oplanProgramId, есть kinopoiskId) - красим в красный
    if (!element.dataset.oplanProgramId && element.dataset.kinopoiskId) {
        element.classList.add('kinopoisk-card');
    } else {
        element.classList.remove('kinopoisk-card');
    }
}

const oplanResultsContainer = document.getElementById('oplan_results');
const kinopoiskResultsContainer = document.getElementById('kinopoisk_results');

// OPLAN - можно только забирать
if (oplanResultsContainer) {
    setupSortableForContainer(oplanResultsContainer, { put: false, sort: false });
}

// Kinopoisk - можно только забирать
if (kinopoiskResultsContainer) {
    setupSortableForContainer(kinopoiskResultsContainer, { put: false, sort: false });
}

const containers = document.querySelectorAll('.schedule_container');

containers.forEach(container => {
    setupSortableForContainer(container, { pull: true, put: true });
});

function saveMoveToServer(data) {
    fetch('/schedule-perspective/update-program-position/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('Обновление успешно');
            // После успешного сохранения пересчитываем стили
            document.querySelectorAll('.schedule_container .program').forEach(applyKinopoiskStyle);
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
}

function calculateDuration() {
    const schedules = document.querySelectorAll('.schedule_day');
    schedules.forEach(schedule => {
        const totalDurationCounter = schedule.querySelector('.schedule_duration');
        const programs = schedule.querySelectorAll('.program');

        const durations = Array.from(programs).map(program => parseInt(program.dataset.duration) || 0);
        const totalDuration = durations.reduce((sum, duration) => sum + duration, 0);

        totalDurationCounter.innerText = convertFramesToTime(totalDuration);
    })
}

function convertFramesToTime(frames, fps = 25) {
    const sec = parseInt(frames) / fps;
    const yy = Math.floor(Math.floor(sec / 3600 / 24) / 365);
    const dd = Math.floor(Math.floor(sec / 3600 / 24) % 365);
    const hh = Math.floor((sec / 3600) % 24);
    const mm = Math.floor((sec % 3600) / 60);
    const ss = Math.floor((sec % 3600) % 60);
    const ff = Math.floor((sec % 1) * fps);

    const formatNum = num => num.toString().padStart(2, '0');

    if (yy < 1) {
        if (dd < 1) {
            return `${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        } else {
            return `${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        }
    } else {
        if (0 < yy % 10 && yy % 10 < 5) {
            return `${formatNum(yy)}г. ${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        } else {
            return `${formatNum(yy)}л. ${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        }
    }
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};