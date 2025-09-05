document.addEventListener('DOMContentLoaded', function() {
    const dayButtons = document.querySelectorAll('.loading-day');
    const controllers = new Map();

    dayButtons.forEach(button => {
        const controller = new AbortController();
        controllers.set(button, controller);

        const date = button.value;
        fetch(`/on-air-report/load_on_air_calendar_info/?date=${date}`, {
            signal: controller.signal // передаем сигнал отмены
        })
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
            Object.assign(button.dataset, {
                noMaterial: dayInfo.no_material,
                notReady: dayInfo.not_ready,
                fix: dayInfo.fix,
                fixReady: dayInfo.fix_ready,
                ready: dayInfo.ready,
                otk: dayInfo.otk,
                otkFail: dayInfo.otk_fail,
                final: dayInfo.final,
                readyFail: dayInfo.final_fail,
                readyOplan3: dayInfo.ready_oplan3
            });
            const badgeInfo = button.querySelector('span.total-otk');
            otkInfo = button.dataset.otk;
            if (otkInfo && otkInfo > 0) {
                badgeInfo.innerText = otkInfo;
                badgeInfo.style.display = '';
            };

        })
        .catch(error => {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted:', date);
            } else {
                console.error('Error loading day data:', error);
            }
        });
        window.addEventListener('beforeunload', () => {
            controllers.forEach(controller => {
                controller.abort();
            });
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

    const elementsMap = {
        noMaterial: document.getElementById('no_material'),
        notReady: document.getElementById('not_ready'),
        fix: document.getElementById('fix'),
        fixReady: document.getElementById('fix_ready'),
        ready: document.getElementById('ready'),
        otk: document.getElementById('otk'),
        otkFail: document.getElementById('otk_fail'),
        final: document.getElementById('final'),
        readyFail: document.getElementById('final_fail'),
        readyOplan3: document.getElementById('ready_oplan3'),
    };

    Object.entries(elementsMap).forEach(([key, element]) => {
        if (element && selectedDay.dataset[key]) {
            element.innerHTML = selectedDay.dataset[key];
        }
    });
    dayLink.style.display = ''
    dayLink.href = `/on-air-report/${calYear}/${calMonth}/${calDay}`;
};
