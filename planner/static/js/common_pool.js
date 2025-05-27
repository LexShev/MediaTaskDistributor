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