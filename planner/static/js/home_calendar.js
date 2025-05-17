document.addEventListener('DOMContentLoaded', function() {
    fetch(`/home_calendar/`)
        .then(response => response.json())
        .then(data => {
            let calendarContainer = document.getElementById('calendar-container');
            calendarContainer.innerHTML = data.html;
        })
        .catch(error => {
            document.getElementById('calendar-container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки календаря</div>
            `;
        });
});