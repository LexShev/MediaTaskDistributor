let fullList = document.getElementById('full_list');
const containers = [
  document.getElementById('cards_container_1'),
  document.getElementById('cards_container_2'),
  document.getElementById('cards_container_3'),
  document.getElementById('cards_container_4')
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


let currentEditingLabel = null;

function EditListMarker(clickedButton) {
    const newLabel = clickedButton.parentElement;

    // Если уже есть редактируемый элемент - завершаем его редактирование
    if (currentEditingLabel && currentEditingLabel !== newLabel) {
        finishEditing(currentEditingLabel);
    }

    startEditing(newLabel);
}

function startEditing(label) {
    currentEditingLabel = label;
    const markerName = label.querySelector('[name="input-markerName"]');
    const btnEdit = label.querySelector('[name="btn-edit"]');
    const btnApply = label.querySelector('[name="btn-apply"]');

    btnEdit.style.display = 'none';
    btnApply.style.display = '';
    markerName.disabled = false;

    const handleApply = () => finishEditing(label);
    const handleOutsideClick = (e) => {
        if (!label.contains(e.target)) {
            finishEditing(label);
        }
    };
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            finishEditing(label);
        }
    };

    btnApply.addEventListener('click', handleApply);
    document.addEventListener('click', handleOutsideClick);
    markerName.addEventListener('keydown', handleKeyDown);

    // Сохраняем ссылки на обработчики для последующего удаления
    label._editHandlers = { handleApply, handleOutsideClick, handleKeyDown };
}

function finishEditing(label) {
    if (!label) return;

    const markerName = label.querySelector('[name="input-markerName"]');
    const btnEdit = label.querySelector('[name="btn-edit"]');
    const btnApply = label.querySelector('[name="btn-apply"]');

    btnEdit.style.display = '';
    btnApply.style.display = 'none';
    markerName.disabled = true;

    // Отправляем изменения на сервер
    WriteMarkerName(markerName);

    // Удаляем обработчики
    if (label._editHandlers) {
        btnApply.removeEventListener('click', label._editHandlers.handleApply);
        document.removeEventListener('click', label._editHandlers.handleOutsideClick);
        markerName.removeEventListener('keydown', label._editHandlers.handleKeyDown);
        delete label._editHandlers;
    }

    if (currentEditingLabel === label) {
        currentEditingLabel = null;
    }
};

function WriteMarkerName(markerName) {
    fetch('update_marker_name/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
    },

    body: JSON.stringify([markerName.dataset.listId, markerName.value]),
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
    });
};

