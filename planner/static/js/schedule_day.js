// schedule_day.js - исправленная версия

// Функция для переключения состояния папки
function toggleScheduleFolder(folderId) {
    console.log('toggleScheduleFolder вызвана для:', folderId);

    // Находим переключатель
    const toggleIcon = document.getElementById(`toggle-${folderId}`);
    if (!toggleIcon) {
        console.error('Переключатель не найден:', folderId);
        return;
    }

    // Находим все дочерние строки
    const childRows = document.querySelectorAll(`tr[data-parent="${folderId}"]`);
    console.log('Найдено дочерних строк:', childRows.length);

    // Проверяем текущее состояние - виден ли хоть один ребенок
    let isCollapsed = true;
    if (childRows.length > 0) {
        // Проверяем display первого ребенка
        const firstChild = childRows[0];
        isCollapsed = firstChild.style.display === 'none' || window.getComputedStyle(firstChild).display === 'none';
    }

    console.log('Текущее состояние (collapsed):', isCollapsed);

    if (isCollapsed) {
        // РАЗВОРАЧИВАЕМ - показываем детей
        console.log('РАЗВОРАЧИВАЕМ папку', folderId);
        childRows.forEach(row => {
            row.style.display = '';
        });
        toggleIcon.querySelector('svg').style.transform = 'rotate(0deg)';
        localStorage.setItem(`folder-${folderId}`, 'expanded');
    } else {
        // СВОРАЧИВАЕМ - скрываем детей
        console.log('СВОРАЧИВАЕМ папку', folderId);
        childRows.forEach(row => {
            row.style.display = 'none';
            // Также скрываем внуков, если они есть
            const childId = row.dataset.id;
            if (row.dataset.hasChildren === 'true') {
                hideAllChildren(childId);
            }
        });
        toggleIcon.querySelector('svg').style.transform = 'rotate(-90deg)';
        localStorage.setItem(`folder-${folderId}`, 'collapsed');
    }
}

// Рекурсивно скрывает всех детей
function hideAllChildren(parentId) {
    const childRows = document.querySelectorAll(`tr[data-parent="${parentId}"]`);
    childRows.forEach(row => {
        row.style.display = 'none';
        if (row.dataset.hasChildren === 'true') {
            hideAllChildren(row.dataset.id);
        }
    });
}

// Рекурсивно показывает всех детей (если родитель развернут)
function showAllChildren(parentId) {
    const childRows = document.querySelectorAll(`tr[data-parent="${parentId}"]`);
    childRows.forEach(row => {
        row.style.display = '';
        if (row.dataset.hasChildren === 'true' &&
            localStorage.getItem(`folder-${row.dataset.id}`) === 'expanded') {
            showAllChildren(row.dataset.id);
        }
    });
}

// Восстановление состояния при загрузке
function initScheduleTableState() {
    console.log('Инициализация состояния таблицы');

    // Сначала скроем всех детей
    const allChildRows = document.querySelectorAll('tr[data-parent]');
    allChildRows.forEach(row => {
        row.style.display = 'none';
    });

    // Затем восстановим состояние из localStorage
    const folderRows = document.querySelectorAll('tr[data-has-children="true"]');
    console.log('Найдено папок:', folderRows.length);

    folderRows.forEach(row => {
        const folderId = row.dataset.id;
        const savedState = localStorage.getItem(`folder-${folderId}`);
        const toggleIcon = document.getElementById(`toggle-${folderId}`);

        if (!toggleIcon) return;

        const svgElement = toggleIcon.querySelector('svg');

        if (savedState === 'expanded') {
            console.log('Восстанавливаем РАЗВЕРНУТОЕ состояние для:', folderId);
            // Стрелка должна быть прямой (0deg)
            svgElement.style.transform = 'rotate(0deg)';
            // Показываем детей
            showAllChildren(folderId);
        } else {
            console.log('Восстанавливаем СВЕРНУТОЕ состояние для:', folderId);
            // Стрелка должна быть повернута (-90deg)
            svgElement.style.transform = 'rotate(-90deg)';
            // Дети уже скрыты, ничего делать не нужно
        }
    });

    console.log('Инициализация завершена');
}

// Фильтрация по типам
function setupAdvertFilter() {
    const advertCheckbox = document.getElementById('advert');
    if (advertCheckbox) {
        advertCheckbox.addEventListener('change', function(e) {
            const hideAdverts = e.target.checked;
            const rows = document.querySelectorAll('#schedule_table_body .schedule-row');

            rows.forEach(row => {
                const typeBadge = row.querySelector('td:nth-child(6) .badge');
                if (typeBadge) {
                    const type = typeBadge.textContent.trim();
                    if (hideAdverts && (type === 'block' || type === 'segment')) {
                        row.style.display = 'none';
                        // Также скрываем детей рекурсивно
                        if (row.dataset.hasChildren === 'true') {
                            hideAllChildren(row.dataset.id);
                        }
                    } else {
                        row.style.display = '';
                        // Показываем детей, если они должны быть видны
                        const folderId = row.dataset.id;
                        if (row.dataset.hasChildren === 'true' &&
                            localStorage.getItem(`folder-${folderId}`) === 'expanded') {
                            showAllChildren(folderId);
                        }
                    }
                }
            });
        });
    }
}

// Основная функция инициализации
function initScheduleDay() {
    console.log('=== Инициализация таблицы расписания ===');

    // Восстанавливаем состояние всех папок
    initScheduleTableState();

    // Настраиваем фильтр рекламы
    setupAdvertFilter();

    console.log('=== Инициализация завершена ===');
}

// Экспортируем функции
window.scheduleDay = {
    toggleScheduleFolder: toggleScheduleFolder,
    initScheduleDay: initScheduleDay
};

// Автоматическая инициализация если таблица уже есть
if (document.querySelector('#schedule_table_body')) {
    // Даем время на отрисовку DOM
    setTimeout(() => {
        initScheduleDay();
    }, 100);
}