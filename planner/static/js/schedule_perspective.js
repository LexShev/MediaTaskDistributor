document.addEventListener('DOMContentLoaded', function() {
  const dropdownMenu = document.getElementById('search_results');
  const searchQuery = document.getElementById('search_query');

  if (searchQuery && dropdownMenu) {
      ['input', 'click'].forEach(event => {
          searchQuery.addEventListener(event, function () {
              if (this.value.length > 0) {
                  searchProgram(this.value);
                  setTimeout(() => {
                      dropdownMenu.classList.add('show');
                  }, 300);
              }

          })
      })

    // Создаем кастомное управление dropdown
    searchQuery.addEventListener('focus', function() {
    });

    // Закрываем при клике вне области
    document.addEventListener('click', function(event) {
      if (!event.target.closest('.dropdown')) {
        dropdownMenu.classList.remove('show');
      }
    });

    // Скрываем при пустом вводе
    searchQuery.addEventListener('input', function() {
      if (this.value.length === 0) {
        setTimeout(() => {
            dropdownMenu.classList.remove('show');
        }, 300);
      }
    });

    // Предотвращаем закрытие при клике внутри меню
    dropdownMenu.addEventListener('click', function(event) {
      event.stopPropagation();
    });
  }
});

function searchProgram(query) {
    const dropdownMenu = document.getElementById('search_results');
    dropdownMenu.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="min-height: inherit;">
            <div class="spinner-border text-primary spinner-border-sm align-items-center" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>`;

    // Загружаем данные
    fetch('/schedule-perspective/search_program/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(query),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            dropdownMenu.innerHTML = '';
            if (data.search_list.length > 0) {
                data.search_list.forEach(program => {
                        let list_item = document.createElement("p");
                        list_item.innerText = `${program.Progs_name} ${program.Progs_production_year}`
                        dropdownMenu.appendChild(list_item);
                    }
                )
            }
            else {
                dropdownMenu.innerHTML = 'По вашему запросу ничего не найдено'
            }
        } else {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
}

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
};