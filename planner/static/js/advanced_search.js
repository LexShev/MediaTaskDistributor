let search_id = document.getElementById('search_id')
let search_input = document.getElementById('search_input')
let engineers = document.getElementById('engineers')

window.addEventListener('load', search_update);

search_id.addEventListener('change', search_update);
function search_update() {
    if (search_id.value == 3) {
        search_input.value = '';
        search_input.hidden = true
        engineers.hidden = false
    }
    else if (search_id.value == 4 || search_id.value == 5) {
        search_input.type = 'date'
        search_input.hidden = false
        engineers.hidden = true
    }
    else {
        search_input.type = 'text'
        search_input.hidden = false
        engineers.hidden = true
    };
};