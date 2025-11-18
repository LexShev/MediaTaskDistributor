// Загружаем форму сразу при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    let distributionFormContainer = document.getElementById('distributionFormContainer');
    if (distributionFormContainer) {
        fetch('/get-distribution-form/')
        .then(response => response.text())
        .then(html => {
            distributionFormContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading distribution form:', error);
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    fetch(`/update_total_unread_count/`)
        .then(response => response.json())
        .then(data => {
            updateTotalUnreadCount(data.total_unread);
        })
        .catch(error => {
            console.log(error, data.message);
        });
});

function startDistribution() {
    svg_spinner = document.getElementById('svg_spinner');
    svg_spinner.classList.add('spinner');
    const distributionForm = document.getElementById('distributionForm');
    const formData = new FormData(distributionForm);

    const data = {
        distr_sched_end_date: distributionForm.querySelector('#distr_sched_end_date')?.value || '',
        distr_sched_id: distributionForm.querySelector('#distr_sched_id')?.value || ''
    };

    fetch('/start_distribution/', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = data.redirect_url;
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error(error);
    });
};

function updateNoMaterial() {
    noMaterialBtn = document.getElementById('update_no_material');
    noMaterialBtn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
    fetch('/tools/update_no_material/')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            console.error(error);
        });

};

function updateTotalUnreadCount(newCount) {
    const totalUnreadBadge = document.getElementById('total_unread_badge');
    if (!totalUnreadBadge) return;

    if (newCount > 0 && newCount <= 99) {
        totalUnreadBadge.textContent = newCount;
        totalUnreadBadge.style.display = '';
    }
    else if (newCount > 99) {
        totalUnreadBadge.textContent = '99+';
        totalUnreadBadge.style.display = '';
    }
    else {
        totalUnreadBadge.style.display = 'none';
    }

};

function showError(message) {
    const error_id = 'service_report_error'
    const modalHTML = `<div class="modal fade" id="${error_id}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Ошибка!</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <h6 id="error_message">${message}</h6>
          </div>
        </div>
      </div>
    </div>`

    // Добавляем в DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Показываем модальное окно
    const modalElement = document.getElementById(error_id);
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // Удаляем модальное окно после скрытия
    modalElement.addEventListener('hidden.bs.modal', function () {
        modalElement.remove();
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
};