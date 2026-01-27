// schedule_day.js - исправленная версия с правильной логикой сворачивания

// Функция для переключения состояния папки
function toggleScheduleFolder(folderId) {
    console.log('toggleScheduleFolder вызвана для:', folderId);

    // Проверяем, включен ли фильтр рекламы
    const advertCheckbox = document.getElementById('advert');
    const hideAdverts = advertCheckbox ? advertCheckbox.checked : false;

    // Находим папку
    const folderRow = document.querySelector(`tr[data-id="${folderId}"]`);
    if (!folderRow) return;

    // Проверяем, не скрыта ли папка как реклама
    if (hideAdverts) {
        const typeBadge = folderRow.querySelector('td:nth-child(5) .badge');
        if (typeBadge) {
            const type = typeBadge.textContent.trim().toLowerCase();
            if (type === 'block' || type === 'segment') {
                // Папка - реклама, не даем ее развернуть
                return;
            }
        }
    }

    // Находим переключатель
    const toggleIcon = document.getElementById(`toggle-${folderId}`);
    if (!toggleIcon) {
        console.error('Переключатель не найден:', folderId);
        return;
    }

    // Находим все дочерние строки
    const childRows = document.querySelectorAll(`tr[data-parent="${folderId}"]`);
    console.log('Найдено дочерних строк:', childRows.length);

    // Смотрим на сохраненное состояние в localStorage
    const savedState = localStorage.getItem(`folder-${folderId}`);
    console.log('Сохраненное состояние:', savedState);

    // Проверяем текущее состояние по иконке (повороту стрелки)
    const svgElement = toggleIcon.querySelector('svg');
    const currentRotation = svgElement.style.transform;
    const isCurrentlyExpanded = currentRotation === 'rotate(0deg)' || currentRotation === '';

    console.log('Текущее состояние (развернуто?):', isCurrentlyExpanded);

    if (isCurrentlyExpanded) {
        // СВОРАЧИВАЕМ - скрываем детей
        console.log('СВОРАЧИВАЕМ папку', folderId);
        childRows.forEach(row => {
            row.style.display = 'none';
            // Также скрываем внуков, если они есть
            if (row.dataset.hasChildren === 'true') {
                hideAllChildren(row.dataset.id);
            }
        });
        svgElement.style.transform = 'rotate(-90deg)';
        localStorage.setItem(`folder-${folderId}`, 'collapsed');
    } else {
        // РАЗВОРАЧИВАЕМ - показываем детей
        console.log('РАЗВОРАЧИВАЕМ папку', folderId);

        // Если есть сохраненное состояние, используем его
        const shouldShowAllChildren = savedState === 'expanded';

        childRows.forEach(row => {
            // При показе детей учитываем фильтр рекламы
            if (hideAdverts) {
                const typeBadge = row.querySelector('td:nth-child(5) .badge');
                if (typeBadge) {
                    const type = typeBadge.textContent.trim().toLowerCase();
                    // Показываем только нерекламные строки
                    if (type !== 'block' && type !== 'segment') {
                        row.style.display = '';

                        // Если это папка и была развернута, показываем ее детей
                        if (row.dataset.hasChildren === 'true' &&
                            localStorage.getItem(`folder-${row.dataset.id}`) === 'expanded') {
                            showNonAdvertChildren(row.dataset.id);
                        }
                    } else {
                        // Рекламные строки остаются скрытыми
                        row.style.display = 'none';
                    }
                } else {
                    row.style.display = '';
                }
            } else {
                // Без фильтра показываем всех
                row.style.display = '';

                // Если это папка и была развернута, показываем всех детей
                if (row.dataset.hasChildren === 'true' &&
                    localStorage.getItem(`folder-${row.dataset.id}`) === 'expanded') {
                    showAllChildren(row.dataset.id);
                }
            }
        });
        svgElement.style.transform = 'rotate(0deg)';
        localStorage.setItem(`folder-${folderId}`, 'expanded');
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

// Вспомогательная функция: показывает только нерекламных детей
function showNonAdvertChildren(parentId) {
    const childRows = document.querySelectorAll(`tr[data-parent="${parentId}"]`);
    childRows.forEach(row => {
        // Проверяем тип строки
        const typeBadge = row.querySelector('td:nth-child(5) .badge');
        if (typeBadge) {
            const type = typeBadge.textContent.trim().toLowerCase();
            // Показываем только нерекламные строки
            if (type !== 'block' && type !== 'segment') {
                row.style.display = '';

                // Если это папка и она была развернута, показываем ее детей
                if (row.dataset.hasChildren === 'true' &&
                    localStorage.getItem(`folder-${row.dataset.id}`) === 'expanded') {
                    showNonAdvertChildren(row.dataset.id);
                }
            } else {
                // Скрываем рекламные строки и всех их детей
                row.style.display = 'none';
                if (row.dataset.hasChildren === 'true') {
                    hideAllChildren(row.dataset.id);
                }
            }
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
//    console.log('Найдено папок:', folderRows.length);

    folderRows.forEach(row => {
        const folderId = row.dataset.id;
        const savedState = localStorage.getItem(`folder-${folderId}`);
        const toggleIcon = document.getElementById(`toggle-${folderId}`);

        if (!toggleIcon) return;

        const svgElement = toggleIcon.querySelector('svg');

        if (savedState === 'expanded') {
//            console.log('Восстанавливаем РАЗВЕРНУТОЕ состояние для:', folderId);
            // Стрелка должна быть прямой (0deg)
            svgElement.style.transform = 'rotate(0deg)';
            // Показываем детей
            showAllChildren(folderId);
        } else {
//            console.log('Восстанавливаем СВЕРНУТОЕ состояние для:', folderId);
            // Стрелка должна быть повернута (-90deg)
            svgElement.style.transform = 'rotate(-90deg)';
            // Дети уже скрыты, ничего делать не нужно
        }
    });

    console.log('Инициализация завершена');
}

// Фильтрация по типам - исправленная версия
function setupAdvertFilter() {
    const advertCheckbox = document.getElementById('advert');
    if (advertCheckbox) {
        advertCheckbox.addEventListener('change', function(e) {
            const hideAdverts = e.target.checked;
            console.log('Фильтр рекламы:', hideAdverts ? 'скрыть рекламу' : 'показать всё');

            // Получаем ВСЕ строки таблицы
            const allRows = document.querySelectorAll('#schedule_table_body tr');

            if (hideAdverts) {
                // СКРЫВАЕМ РЕКЛАМУ
                // 1. Сначала показываем ВСЕ строки
                allRows.forEach(row => {
                    row.style.display = '';
                });

                // 2. Скрываем ТОЛЬКО рекламные строки (тип 'block' или 'segment')
                allRows.forEach(row => {
                    const typeBadge = row.querySelector('td:nth-child(5) .badge');
                    if (typeBadge) {
                        const type = typeBadge.textContent.trim().toLowerCase();
                        if (type === 'block' || type === 'segment') {
                            row.style.display = 'none';
                        }
                    }
                });

                // 3. Восстанавливаем состояние папок из localStorage
                const folderRows = document.querySelectorAll('tr[data-has-children="true"]');
                folderRows.forEach(row => {
                    const folderId = row.dataset.id;
                    const savedState = localStorage.getItem(`folder-${folderId}`);

                    // Проверяем, видима ли папка (она могла быть скрыта как реклама)
                    if (row.style.display !== 'none') {
                        if (savedState === 'expanded') {
                            // Показываем детей (но только нерекламные)
                            showNonAdvertChildren(folderId);
                        } else {
                            // Скрываем детей
                            hideAllChildren(folderId);
                            // Обновляем иконку
                            const toggleIcon = document.getElementById(`toggle-${folderId}`);
                            if (toggleIcon) {
                                toggleIcon.querySelector('svg').style.transform = 'rotate(-90deg)';
                            }
                        }
                    }
                });

            } else {
                // ПОКАЗЫВАЕМ ВСЁ
                // 1. Сначала показываем ВСЕ строки
                allRows.forEach(row => {
                    row.style.display = '';
                });

                // 2. Восстанавливаем оригинальное состояние из localStorage
                const folderRows = document.querySelectorAll('tr[data-has-children="true"]');
                folderRows.forEach(row => {
                    const folderId = row.dataset.id;
                    const savedState = localStorage.getItem(`folder-${folderId}`);

                    if (savedState === 'expanded') {
                        // Показываем всех детей
                        showAllChildren(folderId);
                        const toggleIcon = document.getElementById(`toggle-${folderId}`);
                        if (toggleIcon) {
                            toggleIcon.querySelector('svg').style.transform = 'rotate(0deg)';
                        }
                    } else {
                        // Скрываем детей
                        hideAllChildren(folderId);
                        const toggleIcon = document.getElementById(`toggle-${folderId}`);
                        if (toggleIcon) {
                            toggleIcon.querySelector('svg').style.transform = 'rotate(-90deg)';
                        }
                    }
                });
            }
        });
    }
}

// Основная функция инициализации
function initScheduleDay() {
    console.log('=== Инициализация таблицы расписания ===');

    // Восстанавливаем состояние всех папок
    initScheduleTableState();

    // Настраиваем фильтр рекламы ПОСЛЕ восстановления состояния
    // Это важно: сначала все папки в правильном состоянии, потом применяем фильтр
    setTimeout(() => {
        setupAdvertFilter();

        // Проверяем состояние чекбокса и применяем фильтр
        const advertCheckbox = document.getElementById('advert');
        if (advertCheckbox && advertCheckbox.checked) {
            // Имитируем событие change для применения фильтра
            advertCheckbox.dispatchEvent(new Event('change'));
        }
    }, 100);

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