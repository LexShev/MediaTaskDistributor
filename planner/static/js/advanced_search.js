window.addEventListener('load', function() {
    let search_id = document.getElementById('search_id')
    let tableFilter = document.getElementById('tableFilter')
    search_id.addEventListener('change', function() {
        if (search_id.value == 4 || search_id.value == 5) {
        tableFilter.type = 'date'
//        tableFilter.pattern="[0-9]{2}-[0-9]{2}-[0-9]{4}"
//        tableFilter.format = '%d-%m-%Y'
        }
        else {
        tableFilter.type = 'text'
        };
    });
});