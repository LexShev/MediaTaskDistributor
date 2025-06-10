let cardsContainer01 = document.getElementById('cards_container_01');
let cardsContainer02 = document.getElementById('cards_container_02');
let fullList = document.getElementById('full_list');


new Sortable(fullList, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    onEnd: function() {
    let cards01 = cardsContainer01.getElementsByClassName('card');
    let cards02 = cardsContainer02.getElementsByClassName('card');
    let order01 = Array.from(cards01).map(card => card.dataset.programId);
    let order02 = Array.from(cards02).map(card => card.dataset.programId);
    WriteOrder(order01, order02);
    }
//    onStart: function() {
//    cardsContainer01.style.height = '29rem';
//    cardsContainer02.style.height = '29rem';
//    },
//    onEnd: function() {
//    cardsContainer01.style.height = '';
//    cardsContainer02.style.height = '';
//    }

});

new Sortable(cardsContainer01, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    onEnd: function() {
    let cards01 = cardsContainer01.getElementsByClassName('card');
    let cards02 = cardsContainer02.getElementsByClassName('card');
    let order01 = Array.from(cards01).map(card => card.dataset.programId);
    let order02 = Array.from(cards02).map(card => card.dataset.programId);
    WriteOrder(order01, order02);
    }

});

new Sortable(cardsContainer02, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    onEnd: function() {
    let cards01 = cardsContainer01.getElementsByClassName('card');
    let cards02 = cardsContainer02.getElementsByClassName('card');
    let order01 = Array.from(cards01).map(card => card.dataset.programId);
    let order02 = Array.from(cards02).map(card => card.dataset.programId);
    WriteOrder(order01, order02);
    }
});

function WriteOrder(order01, order02) {

    fetch('update_order/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'), // Более надежное получение CSRF
        'X-Requested-With': 'XMLHttpRequest' // Для идентификации AJAX на сервере
    },
    body: JSON.stringify({
        order_01: order01,
        order_02: order02
    }),
    credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
             console.error(response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log('data', data)
        if (data.status !== 'success') {
            console.error(data.message || 'Unknown server error');
        }

    })
    .catch(error => {
        console.error('Error:', error);
//        revertChanges();
    });
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function FastSearch() {
    let filterVal = filter.value.toLowerCase();
    let fullList = document.getElementById('full_list');
    let cards = fullList.getElementsByClassName('card');
    for (let i = 0; i < cards.length; i++) {
        let materialName = cards[i].getElementsByClassName('material_name')[0];
        if (materialName) {
            let textValue = (materialName.textContent || materialName.innerText).toLowerCase();
            cards[i].style.display = textValue.indexOf(filterVal) > -1 ? '' : 'none';
        }
    }
};

let filter = document.getElementById('list_filter');
filter.addEventListener('keyup', FastSearch);

const input = document.getElementById('list_filter');
const clearBtn = document.getElementById('clear-input');

input.addEventListener('input', function() {
  clearBtn.style.display = this.value.length > 0 ? 'block' : 'none';
});

clearBtn.addEventListener('click', function() {
  input.value = '';
  input.focus();
  clearBtn.style.display = 'none';
  FastSearch();
});
