let seasons = document.getElementsByClassName('season');

for (let i = 0; i < seasons.length; i++) {
    let season = seasons[i];
    let parentCheckbox = season.querySelector('input[type="checkbox"]');
    let episodes = season.getElementsByTagName('li');
    let episodeCheckboxes = [];

    // Все чекбоксы эпизодов
    for (let n = 0; n < episodes.length; n++) {
        let checkbox = episodes[n].querySelector('input[type="checkbox"]');
        if (checkbox) {
            episodeCheckboxes.push(checkbox);
            // Обработчик на каждый чекбокс
            checkbox.addEventListener('change', updateParentCheckbox);
        }
    }

    // Функция обновления состояния родительского чекбокса
    function updateParentCheckbox() {
        let checkedCount = episodeCheckboxes.filter(checkbox => checkbox.checked).length;
        let completeTask = season.querySelector('[name="complete_task"]');

        if (checkedCount > 0 && checkedCount < episodeCheckboxes.length) {
            parentCheckbox.indeterminate = true;
            parentCheckbox.checked = false;
            completeTask.style.display = 'inline';
        }
        else if (checkedCount === episodeCheckboxes.length) {
            parentCheckbox.indeterminate = false;
            parentCheckbox.checked = true;
            completeTask.style.display = 'inline';
        }
        else if (checkedCount === 0) {
            parentCheckbox.indeterminate = false;
            parentCheckbox.checked = false;
            completeTask.style.display = 'none';
        }
    };
}

function changeProgramIdCheckbox() {
    for (let i = 0; i < seasons.length; i++) {
        let season = seasons[i];
        let parentCheckbox = season.querySelector('input[type="checkbox"]');
        let episodes = season.getElementsByTagName('li');
        let episodeCheckboxes = [];

        for (let n = 0; n < episodes.length; n++) {
            let checkbox = episodes[n].querySelector('input[type="checkbox"]');
            if (checkbox) {
                episodeCheckboxes.push(checkbox);
            }
        }
        if (parentCheckbox.checked) {
            for (let i = 0; i < episodeCheckboxes.length; i++) {
                episodeCheckboxes[i].checked = true;
            };
        }
        else {
            for (let i = 0; i < episodeCheckboxes.length; i++) {
                episodeCheckboxes[i].checked = false;
            };
        }
    }
};