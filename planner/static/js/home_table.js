document.addEventListener('DOMContentLoaded', sortTable);

function sortTable() {
    const tbodies = document.querySelectorAll('.deadline-table-body');
    let rows = [];

    tbodies.forEach(tbody => {
        rows = rows.concat(Array.from(tbody.querySelectorAll('tr')));
    });
    const noMaterialFilter = document.getElementById('no_material_filter');
    const myTasksFilter = document.getElementById('my_tasks_filter');

    let counter = 1;

    rows.forEach(row => {
        let showRow = true;

        // Фильтр "Материал отсутствует"
        // Если чекбокс ОТЖАТ (false) - скрываем no_material
        if (!noMaterialFilter.checked) {
            showRow = showRow && (row.dataset.taskStatus != 'no_material');
            noMaterialFilter.title = 'Показать задачи без материала';
        }
        else {
            noMaterialFilter.title = 'Скрыть задачи без материала';
        }

        // Фильтр "Мои задачи"
        // Если чекбокс ОТЖАТ (false) - скрываем задачи с schedId == 99
        if (!myTasksFilter.checked) {
            showRow = showRow && (row.dataset.schedId != '99');
            myTasksFilter.title = 'Показать Мои задачи';
        }
        else {
            myTasksFilter.title = 'Скрыть Мои задачи';
        }

        if (showRow) {
            // Показываем строку и обновляем счетчик
            row.style.display = '';
            let counterElement = row.querySelector('.counter');
            if (counterElement) {
                counterElement.textContent = counter++;
            }
        } else {
            // Скрываем строку
            row.style.display = 'none';
        }
    });

    // Обновляем счетчик "Всего"
    const totalElement = document.getElementById('total_tasks');
    if (totalElement) {
        totalElement.textContent = `Всего: ${counter - 1}`;
    }
}