// Глобальные переменные для состояния сортировки
let currentSort = {
    order: document.getElementById('order').value || 'progs_name',
    order_type: document.getElementById('order_type').value || 'ASC'
};


function updateSortIndicators(selectedOrder) {
    const sortedHeaders = document.querySelectorAll('[data-order]');

    sortedHeaders.forEach(header => {
        const sortedIcon = header.querySelector('.sort-icon use');
        const order = header.dataset.order;

        if (!sortedIcon) {
            console.warn('Sort icon not found for header:', header);
            return; // Пропускаем если иконка не найдена
        }

        if (order === selectedOrder) {
            // Определяем направление сортировки
            if (currentSort.order === selectedOrder) {
                // Меняем направление если кликнули на ту же колонку
                currentSort.order_type = currentSort.order_type === 'ASC' ? 'DESC' : 'ASC';
            } else {
                // Новая колонка - сортируем по возрастанию
                currentSort.order = selectedOrder;
                currentSort.order_type = 'ASC';
            }

            // Активный индикатор
            sortedIcon.setAttribute('xlink:href', `#${currentSort.order_type}_active`);
        } else {
            // Неактивный индикатор - сбрасываем к базовому состоянию
            sortedIcon.setAttribute('xlink:href', '#sort');
        }
    });

    // Сохраняем в hidden inputs
    const orderInput = document.getElementById('order');
    const orderTypeInput = document.getElementById('order_type');

    orderInput.setAttribute('value', currentSort.order);
    orderTypeInput.setAttribute('value', currentSort.order_type);
};

// Основная функция сортировки
function sortTable(selectedOrder) {
    const tbody = document.getElementById('tableBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Обновляем состояние сортировки
    updateSortIndicators(selectedOrder);

    // Сортируем строки
    rows.sort((a, b) => {
        const aValue = getCellValue(a, selectedOrder);
        const bValue = getCellValue(b, selectedOrder);

        return compareValues(aValue, bValue, selectedOrder);
    });

    // Если сортировка по убыванию - разворачиваем массив
    if (currentSort.order_type === 'DESC') {
        rows.reverse();
    }

    // Очищаем и перезаполняем tbody
    tbody.innerHTML = '';
    rows.forEach((row, index) => {
        // Обновляем номер в названии (первая колонка)
        updateRowNumber(row, index + 1);
        tbody.appendChild(row);
    });
};

// Получение значения ячейки в зависимости от поля
function getCellValue(row, order) {
    const cells = row.querySelectorAll('td');
    
    switch (order) {
        case 'progs_name':
            // Берем текст из второй ячейки (название)
            return cells[1].querySelector('.orig_name').textContent.trim();
        
        case 'clip_id':
            // Значение из input в третьей ячейке
            return cells[2].querySelector('input').value.trim();
        
        case 'directory':
            // Текст четвертой ячейки (директория)
            return cells[3].textContent.trim();
        
        case 'file_name':
            // Текст пятой ячейки (имя файла)
            return cells[4].textContent.trim();
        
        case 'channel':
            // Текст шестой ячейки (канал)
            return cells[5].textContent.trim();
        
        case 'worker':
            // Текст седьмой ячейки (исполнитель)
            return cells[6].textContent.trim();
        
        case 'date_time':
            // Текст восьмой ячейки (дата эфира)
            return new Date(cells[7].dataset.datetime);

        case 'duration':
            // Текст десятой ячейки (длительность)
            return cells[8].dataset.duration.trim();
        
        case 'status':
            // Текст одиннадцатой ячейки (статус)
            return cells[9].textContent.trim();

        case 'cenz':
            // cenz
            const noCenz = cells[10].dataset.noCenz.trim();
            // Возвращаем true если есть иконка (не Task_noCENZ), false если нет
            return noCenz === 'False' || noCenz === 'false' || noCenz === null || noCenz === 'None';
        
        default:
            return '';
    }
}

// Сравнение значений с учетом типа данных
function compareValues(a, b, order) {
    // Для булевых значений (CENZ)
    if (order === 'cenz') {
        // true (есть иконка) > false (нет иконки)
        if (a === true && b === false) return 1;
        if (a === false && b === true) return -1;
        return 0;
    }

    // Для числовых полей
    if (order === 'duration' && !isNaN(a) && !isNaN(b)) {
        return parseInt(a) - parseInt(b);
    }
    
    // Для дат
    if (order === 'date_time') {
        return a - b;
    }

    
    // Для Clip ID (может быть числом)
    if (order === 'clip_id' && !isNaN(a) && !isNaN(b)) {
        return parseInt(a) - parseInt(b);
    }
    
    // Для текстовых полей
    return a.localeCompare(b, 'ru');
}

// Вспомогательные функции для парсинга
function parseTimeToSeconds(timeStr) {
    const parts = timeStr.split(':');
    if (parts.length === 3) {
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    }
    return 0;
}

function parseDate(dateStr) {
    const parts = dateStr.split('.');
    if (parts.length === 3) {
        return new Date(parts[2], parts[1] - 1, parts[0]).getTime();
    }
    return 0;
}

function parseTime(timeStr) {
    const parts = timeStr.split(':');
    if (parts.length === 3) {
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    }
    return 0;
}

// Обновление номера строки
function updateRowNumber(row, number) {
    const counterElement = row.querySelector('.counter');
    counterElement.textContent = `${number}.`;
}

//// Обновление индикаторов сортировки
//function updateSortIndicators(currentHeader, currentField) {
//    // Сбрасываем все индикаторы
//    const allHeaders = document.querySelectorAll('[data-order]');
//    allHeaders.forEach(header => {
//        const icon = header.querySelector('.sort-icon use');
//        const order = header.dataset.order;
//
//        if (order === currentField) {
//            // Активный индикатор
//            icon.setAttribute('xlink:href', `#${currentSort.order_type}_active`);
//        } else {
//            // Неактивный индикатор
//            icon.setAttribute('xlink:href', `#${currentSort.order_type}`);
//        }
//    });
//}