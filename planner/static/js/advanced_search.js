window.addEventListener('load', function() {
    let searchSettings = document.getElementById('searchSettings')
    let tableFilter = document.getElementById('tableFilter')
    searchSettings.addEventListener('change', function() {
        if (searchSettings.value == 4 || searchSettings.value == 5) {
        console.log(tableFilter);
        tableFilter.type = 'date'
        }
        else {
        tableFilter.type = 'text'
        };
    });
});