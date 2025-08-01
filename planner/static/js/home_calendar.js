//document.addEventListener('DOMContentLoaded', function() {
//    fetch(`/home_calendar/`)
//        .then(response => response.json())
//        .then(data => {
//            let calendarContainer = document.getElementById('calendar-container');
//            calendarContainer.innerHTML = data.html;
//        })
//        .catch(error => {
//            document.getElementById('calendar-container').innerHTML = `
//                <div class="alert alert-danger">Ошибка загрузки календаря</div>
//            `;
//        });
//});
document.addEventListener('DOMContentLoaded', function() {
    const dayButtons = document.querySelectorAll('.loading-day');
    dayButtons.forEach(button => {
        const date = button.value;
        fetch(`/load_calendar_info/?date=${date}`)
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
            })
            .catch(error => {
                console.error('Error loading day data:', error);
            });
    })
});