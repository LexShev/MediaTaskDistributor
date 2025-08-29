document.addEventListener('DOMContentLoaded', function() {
    const dayButtons = document.querySelectorAll('.loading-day');
    dayButtons.forEach(button => {
        const date = button.value;
        fetch(`/on-air-report/load_on_air_calendar_info/?date=${date}`)
            .then(response => response.json())
            .then(dayInfo => {
                if (dayInfo.error) {
                    console.error(dayInfo.error);
                    return;
                }

                // Обновляем статус кнопки
                button.classList.remove('loading-day');
                if (dayInfo.color) {
                    button.classList.add(dayInfo.color);
                }

                // Обновляем title с информацией о задачах
                button.title = `Выполнено: ${dayInfo.ready}\nОсталось: ${dayInfo.not_ready}`;
                button.dataset.ready = dayInfo.ready;
                button.dataset.notReady = dayInfo.not_ready;
            })
            .catch(error => {
                console.error('Error loading day data:', error);
            });
    })
});

function selectDay(selectedDay) {
    const activeButtons = document.querySelectorAll('button[name="cal_day"].active');
    activeButtons.forEach(button => {
        button.classList.remove('active');
    });
    selectedDay.classList.add('active');
    const dayLink = document.getElementById('day_link');
    const reportDate = document.getElementById('report_date');
    reportDate.innerText = `Статистика по: ${selectedDay.value}`
    const date = new Date(selectedDay.value);
    const calYear = date.getFullYear();
    const calMonth = date.getMonth() + 1;
    const calDay = date.getDate();

    const readyInfo = document.getElementById('ready')
    const notReadyInfo = document.getElementById('not_ready')
    readyInfo.innerHTML = selectedDay.dataset.ready
    notReadyInfo.innerHTML = selectedDay.dataset.notReady

    dayLink.style.display = ''
    dayLink.href = `/on-air-report/${calYear}/${calMonth}/${calDay}`;
};
