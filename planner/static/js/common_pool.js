document.addEventListener('DOMContentLoaded', function() {
    fetch('/total-count/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-count').textContent = thousands(data.total_count);
        });

    fetch('/film-stats/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('film-count').textContent = `${thousands(data.film_count)} (${convertFramesToTime(data.film_dur)})`;
        });

    fetch('/season-stats/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('season-count').textContent = `${thousands(data.season_count)} (${convertFramesToTime(data.season_dur)})`;
        });
});

document.addEventListener('DOMContentLoaded', function() {
    fetch(`/load_pool_table/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('pool-table-container').innerHTML = data.html;
        })
        .catch(error => {
            document.getElementById('pool-table-container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
});

document.getElementById('tableFilter').addEventListener('keyup', function() {
    let filter = this.value.toLowerCase();
    let tableBody = document.getElementById('tableBody');
    let rows = tableBody.getElementsByTagName('tr');
    let searchSettings = document.getElementById('search_type').value;

    for (let i = 0; i < rows.length; i++) {
        let nameCell = rows[i].getElementsByTagName('td')[searchSettings];
        if (nameCell) {
            let textValue = nameCell.textContent || nameCell.innerText;
            rows[i].style.display = textValue.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
        }
    }
});

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

function thousands(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
};