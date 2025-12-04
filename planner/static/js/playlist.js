document.addEventListener('DOMContentLoaded', load_schedule_table());
document.addEventListener('DOMContentLoaded', function() {
    let scheduleDate = document.getElementById('schedule_date');
    scheduleDate.addEventListener('change', load_schedule_table())
});

function load_schedule_table() {
    console.log('updating');
    fetch('/playlist/load_schedule_table/')
        .then(response => response.json())
        .then(data => {
            let scheduleTable = document.getElementById('schedule_table_container')
            if (scheduleTable) {
                scheduleTable.innerHTML = data.html;
            }

        })
        .catch(error => {
            console.log(document.getElementById('schedule_table_container'));
            document.getElementById('schedule_table_container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
};