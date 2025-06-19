let fullList = document.getElementById('full_list');
const containers = [
  document.getElementById('cards_container_01'),
  document.getElementById('cards_container_02'),
  document.getElementById('cards_container_03'),
  document.getElementById('cards_container_04')
];

new Sortable(fullList, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    onEnd: WriteOrder
});

containers.forEach(container => {
  new Sortable(container, {
    group: 'desktop',
	animation: 200,
	ghostClass: "custom-ghost",
    chosenClass: "custom-chosen",
    dragClass: "custom-drag",
    onEnd: WriteOrder
  });
});


function WriteOrder() {
    const orders = containers.map(container => {
        const cards = container.getElementsByClassName('card');
        return Array.from(cards).map(card => card.dataset.programId);
    });
    console.log(orders);
    fetch('update_order/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify(orders),
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
