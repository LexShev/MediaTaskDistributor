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

    // Создаем кастомное управление dropdown
    searchQuery.addEventListener('focus', function() {
    });

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
    let oplanResults = document.getElementById('oplan_results')
    oplanResults.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="min-height: inherit;">
            <div class="spinner-border text-primary spinner-border-sm align-items-center" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>`;

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
            oplanResults.innerHTML = '';
            if (data.search_list.length > 0) {
                data.search_list.forEach(program => {
                    let listItem = document.createElement("div");
                    listItem.classList.add('program', 'd-flex', 'rounded', 'my-2');
                    listItem.dataset.oplanProgramId = program.Progs_program_id;
                    listItem.dataset.duration = program.Progs_duration;

                    let imageContainer = document.createElement("div");
                    imageContainer.classList.add('poster-container', 'align-items-center', 'm-2')
                    imageContainer.style = "flex: 0 0 12%; max-width: 12%; height: 100%;"

                    let image = document.createElement('img');
                    let imgSrc = `/media/posters/${program.Progs_program_id}.jpg`;
                    // let imgSrc = `https://www.kinopoisk.ru//images/sm_film/1115407.jpg`;
                    image.onerror = function() {
                        this.onerror = null;
                        this.src = '/static/img/no_poster.jpg';
                    };
                    image.src = imgSrc;
                    image.classList.add('img-fluid', 'rounded', 'm-0', 'w-100', 'h-100', 'object-fit-cover');
                    imageContainer.appendChild(image);

                    listItem.appendChild(imageContainer);

                    let nameContainer = document.createElement("div");
                    listItem.appendChild(nameContainer);

                    let header = document.createElement("h6");
                    header.classList.add('my-1', 'p-1')
                    header.innerText = program.Progs_name;
                    nameContainer.appendChild(header);

                    let footer = document.createElement("small");
                    footer.classList.add('production-year')
                    footer.innerText = program.Progs_production_year;
                    nameContainer.appendChild(footer);

                    oplanResults.appendChild(listItem);
                    }
                )
            }
            else {
                oplanResults.innerHTML = 'По вашему запросу ничего не найдено'
            }
        } else {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
}

function moveData(evt) {
    console.log(evt.item)
    return {
        oplanProgramId: evt.item.dataset.oplanProgramId,
        fromContainer: evt.from.id,
        toContainer: evt.to.id,
        oldIndex: evt.oldIndex,
        newIndex: evt.newIndex,
        isSameContainer: evt.from === evt.to
    }
}
const oplanResultsContainer = document.getElementById('oplan_results');

new Sortable(oplanResultsContainer, {
    group: {
            name: 'schedule',
            pull: true,    // Можно забирать
            put: false      // Нельзя добавлять
        },
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    sort: false,
    onEnd: function(evt) {
            // Получаем всю информацию о перемещении
            const data = moveData(evt);

            saveMoveToServer(data);
            calculateDuration();
        }
});

const containers = document.querySelectorAll('.schedule_container');

containers.forEach(container => {
    new Sortable(container, {
        group: {
            name: 'schedule',
            pull: true,    // Можно забирать
            put: true      // Можно добавлять
        },
        animation: 200,
        ghostClass: "custom-ghost",
        chosenClass: "custom-chosen",
        dragClass: "custom-drag",

        onEnd: function(evt) {
            // Получаем всю информацию о перемещении
            const data = moveData(evt);

            saveMoveToServer(data);
            calculateDuration();
        }
    });
});

function saveMoveToServer(data) {
    console.log('Отправка данных:', data);

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