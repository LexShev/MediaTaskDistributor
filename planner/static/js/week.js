function toggleWeekSeason(element) {
    const seasonElement = element.closest('.season');
    const seasonId = seasonElement.dataset.seasonId;
    const dayDate = seasonElement.dataset.dayDate;
    const uniqueKey = `${dayDate}-${seasonId}`;

    const episodesContainer = seasonElement.querySelector('.episodes-container');
    const toggleIcon = seasonElement.querySelector('.season-toggle svg');

    if (!episodesContainer || !toggleIcon) {
        console.warn(`Элементы для сезона ${uniqueKey} не найдены`);
        return;
    }

    if (episodesContainer.classList.contains('collapsed')) {
        episodesContainer.classList.remove('collapsed');
        episodesContainer.classList.add('expanded');
        toggleIcon.style.transform = 'rotate(0deg)';
        localStorage.setItem(`season-${uniqueKey}`, 'expanded');
    } else {
        episodesContainer.classList.remove('expanded');
        episodesContainer.classList.add('collapsed');
        toggleIcon.style.transform = 'rotate(-90deg)';
        localStorage.setItem(`season-${uniqueKey}`, 'collapsed');
    }
}

// Восстановление состояния при загрузке для недельного view
document.addEventListener('DOMContentLoaded', function() {
    const seasonElements = document.querySelectorAll('.season');

    if (!seasonElements || seasonElements.length === 0) {
        return;
    }

    seasonElements.forEach(seasonElement => {
        const seasonId = seasonElement.dataset.seasonId;
        const dayDate = seasonElement.dataset.dayDate;
        const uniqueKey = `${dayDate}-${seasonId}`;

        const episodesContainer = seasonElement.querySelector('.episodes-container');
        const toggleIcon = seasonElement.querySelector('.season-toggle svg');

        if (!episodesContainer || !toggleIcon) {
            return;
        }

        const savedState = localStorage.getItem(`season-${uniqueKey}`);

        if (savedState === 'expanded') {
            episodesContainer.classList.remove('collapsed');
            episodesContainer.classList.add('expanded');
            toggleIcon.style.transform = 'rotate(0deg)';
        } else {
            // Уже есть класс collapsed из шаблона, просто настраиваем иконку
            toggleIcon.style.transform = 'rotate(-90deg)';
        }
    });
});