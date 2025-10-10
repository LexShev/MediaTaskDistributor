document.addEventListener('DOMContentLoaded', function() {
    const scheduleId = document.getElementById('channel_dropdown').value || '';
    const dayButtons = document.querySelectorAll('.loading-day');
    const controllers = new Map();

    dayButtons.forEach(button => {
        const controller = new AbortController();
        controllers.set(button, controller);

        const date = button.value;
        fetch(`/on-air-report/load_on_air_calendar_info/?date=${date}&schedule_id=${scheduleId}`, {
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
//            button.title = `Выполнено: ${dayInfo.ready}\nОсталось: ${dayInfo.not_ready}`;
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
                readyOplan3: dayInfo.ready_oplan3,
                notDistr: dayInfo.not_distr,
                totalPrograms: dayInfo.total_programs,
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
    const date = new Date(selectedDay.value);
    const calYear = date.getFullYear();
    const calMonth = date.getMonth() + 1;
    const calDay = date.getDate();

    const scheduleSelector = document.getElementById('channel_dropdown');
    const scheduleId = scheduleSelector.value
    const scheduleName = scheduleSelector.options[scheduleSelector.selectedIndex].text || '';
    const activeButtons = document.querySelectorAll('button[name="cal_day"].active');
    activeButtons.forEach(button => {
        button.classList.remove('active');
    });
    selectedDay.classList.add('active');
    const dayLink = document.getElementById('day_link');
    const reportDate = document.getElementById('report_date');
    reportDate.innerText = `Статистика за: ${selectedDay.value}`
    if (scheduleId) {
        const channelName = document.getElementById('channel_name');
        channelName.innerText = `По каналу: ${scheduleName}`
        dayLink.href = `/on-air-report/${calYear}/${calMonth}/${calDay}/${scheduleId}`;
    }
    else {
    dayLink.href = `/on-air-report/${calYear}/${calMonth}/${calDay}`;
    };
    dayLink.style.display = ''

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
        notDistr: document.getElementById('not_distr'),
        totalPrograms: document.getElementById('total_programs'),
    };

    Object.entries(elementsMap).forEach(([key, element]) => {
        if (element && selectedDay.dataset[key]) {
            element.innerHTML = selectedDay.dataset[key];
        }
    });
    const notDistrLine = document.getElementById('not_distr_line');
    if (selectedDay.dataset.notDistr > 0) {
        notDistrLine.style.display = '';
    }
    else {
        notDistrLine.style.display = 'none';
    };
    const noMaterialLine = document.getElementById('no_material_line');
    const noMaterialCells = noMaterialLine.querySelectorAll('td');
    if (selectedDay.dataset.noMaterial > 0) {
        noMaterialLine.classList.add('border-danger-subtle');
        noMaterialLine.classList.add('border-2');
        noMaterialCells.forEach((cell) => {
            cell.classList.add('text-danger-emphasis');
            cell.classList.add('bg-danger-subtle');
        });
    }
    else {
        noMaterialLine.classList.remove('border-danger-subtle');
        noMaterialLine.classList.remove('border-2');
        noMaterialCells.forEach((cell) => {
            cell.classList.remove('text-danger-emphasis');
            cell.classList.remove('bg-danger-subtle');
        });
    };
};
