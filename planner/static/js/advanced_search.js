let search_id = document.getElementById('search_id')
let search_input = document.getElementById('search_input')
let engineers = document.getElementById('engineers')
console.log(search_id);


window.addEventListener('load', search_update);

search_id.addEventListener('change', search_update);
function search_update() {
    console.log('upd');
    if (search_id.value == 3) {
        console.log(3)
        search_input.hidden = true
        engineers.hidden = false
    }
    else if (search_id.value == 4 || search_id.value == 5) {
        console.log('4 or 5');
        search_input.type = 'date'
        search_input.hidden = false
        engineers.hidden = true
    }
    else {
        console.log('else');
        search_input.type = 'text'
        search_input.hidden = false
        engineers.hidden = true
    };
};