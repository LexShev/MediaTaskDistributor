const programId = document.getElementById('program_id').dataset.programId;
const userId = document.body.dataset.userId || null;

window.addEventListener('load', CheckLockCard);
window.addEventListener('beforeunload', function(e) {
    fetch(`/unblock_card/${programId}/${userId}/`, {
        method: 'GET',
        keepalive: true, // Важная опция!
        cache: 'no-store'
    }).catch(() => {}); // Игнорируем ошибки
});

async function CheckLockCard() {
    try {
        let response = await fetch(`/check_lock_card/${programId}/`);
        let data = await response.json();
        // Если карточка НЕ заблокирована, то блокируем ее
        if (!data) {
            return
        };
//        console.log(String(data.worker_id) !== String(userId));

        if (data.message === 'not_locked') {
            console.log('Was not blocked. LockCard');
            await fetch(`/block_card/${programId}/${userId}/`)
                .then(response => response.json())
                .then(check => {
                    console.log(check.message);
                })
                .catch(error => {
                    console.log('Block error:', error);
                });
            return;
        };
        if (data.status === 'error') {
            console.error(data.message);
        };
        if (data.message === 'locked' && String(data.worker_id) !== String(userId)) {
            let messageContainer = document.getElementById('message_container');
            messageContainer.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show mx-0 mb-2 mt-0" role="alert">
                    Карточка материала заблокирована в ${data.app} пользователем: ${data.worker_name} в ${data.lock_time}
                </div>`;
            let cenzApproveBtn = document.getElementById('cenz_approve_btn');
            let askFixBtn = document.getElementById('ask_fix_btn');
            cenzApproveBtn.disabled = true;
            askFixBtn.disabled = true;
        };
    } catch (error) {
        console.log('Loading error:', error);
    }
};

document.addEventListener('DOMContentLoaded', function() {
  const dropZone = document.getElementById('drop_zone');
  const fileInput = document.getElementById('uploaded_ready_file_input');

  // Функции для предотвращения стандартного поведения
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    dropZone.classList.add('dragover');
    fileInput.classList.add('dragover');
  }

  function unhighlight() {
    dropZone.classList.remove('dragover');
    fileInput.classList.remove('dragover');
  }

  // Обработчики событий перетаскивания
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

// Обработка drop - файл перетащили в зону
dropZone.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
      //  Берем только ПЕРВЫЙ файл, даже если перетащили несколько
      const firstFile = files[0];

      // Создаем новый FileList с одним файлом
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(firstFile);

      // Присваиваем только первый файл в input
      fileInput.files = dataTransfer.files;

      // Триггерим событие change, чтобы другие обработчики узнали о выборе файла
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);

    }
  }

  // Клик по зоне тоже открывает выбор файла
  dropZone.addEventListener('click', function(e) {
    // Кликаем только если кликнули не по самому input
    if (e.target !== fileInput) {
      fileInput.click();
    }
  });
  // Обработчик изменения файла через стандартный диалог
  fileInput.addEventListener('change', function() {

    if (this.files.length > 0) {
        const fileName = this.files[0].name;
        updateDropZoneAppearance(dropZone, fileName);
    } else {
      // Если файл сброшен
        resetDropZoneAppearance(dropZone);
    }
    });

  function updateDropZoneAppearance(dropZone, fileName) {
    dropZone.classList.add('file-selected');
    dropZone.classList.remove('border-secondary', 'text-secondary');
    dropZone.classList.add('border-success', 'text-success');

    const paragraphs = dropZone.querySelectorAll('p');
    if (paragraphs.length >= 3) {
        paragraphs[0].textContent = `Выбран файл: ${fileName}`;
        paragraphs[1].textContent = '';
        paragraphs[2].textContent = '';
    } else if (paragraphs.length === 1) {
        paragraphs[0].textContent = `Выбран файл: ${fileName}`;
    }
  };

  function resetDropZoneAppearance(dropZone) {
    dropZone.classList.remove('file-selected', 'border-success', 'text-success');
    dropZone.classList.add('border-secondary', 'text-secondary');

    const paragraphs = dropZone.querySelectorAll('p');
    if (paragraphs.length >= 2) {
        paragraphs[0].textContent = 'Перетащите файл сюда...';
        paragraphs[1].textContent = '(или кликните для выбора)';
        paragraphs[2].textContent = 'Убедитесь, что загружаете из папки "ContentA\\0_INTERNET_VIDEO\\_CENZ"';
    }
  };
});

function checkNoCenz() {
    const noCenz = document.getElementById('no_cenz').checked
    const dropZone = document.getElementById('drop_zone');
    const fileInput = document.getElementById('uploaded_ready_file_input');
    fileInput.classList.remove('is-invalid', 'is-valid');

    const event = new Event('change', { bubbles: true });
    fileInput.dispatchEvent(event);
    fileInput.value = ''

    if (noCenz) {
        dropZone.style.display = 'none';
        fileInput.style.display = 'none';
    }
    else {
        dropZone.style.display = '';
        fileInput.style.display = '';
    };
};

function FormatDate(timestamp) {
    const date = new Date(timestamp);

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    const formatted = `${hours}:${minutes}:${seconds} ${day}.${month}.${year}`;
    return formatted
};

async function getWorkerName(workerId) {
    try {
        const response = await fetch(`/get_worker_name/${workerId}`);
        const data = await response.json();
        return data.worker_name;
    }
    catch (error) {
        console.error('Getting name error:', error);
        return 'Аноним';
    }
}

function ValidateCenzApprove(task) {
    let workDate = document.getElementById('work_date_form')
    let cenzRate = document.getElementById('cenz_rate_form')
    let engineers = document.getElementById('engineers_form')

    if (!workDate.value || !cenzRate.value || !engineers.value) {
        workDate.classList.add('is-invalid');
        cenzRate.classList.add('is-invalid');
        engineers.classList.add('is-invalid');
        return;
        }
    workDate.classList.remove('is-invalid');
    cenzRate.classList.remove('is-invalid');
    engineers.classList.remove('is-invalid');

    if (task === 'status_ready') {
        const CenzApproveModal = bootstrap.Modal.getInstance(document.getElementById('CenzApproveModal')) ||
                            new bootstrap.Modal(document.getElementById('CenzApproveModal'));
        CenzApproveModal.toggle()
    }
    else if (task === 'cenz_info_change') {
        CenzApprove(task);
    };
};

function ValidateAskFix(task) {
    let deadline = document.getElementById('deadline')

    if (!deadline.value) {
        deadline.classList.add('is-invalid');
        return;
        }
    deadline.classList.remove('is-invalid');

    CenzApprove(task);

};

function ValidateFileUpload(task) {
    const noCenz = document.getElementById('no_cenz').checked
    const fileInput = document.getElementById('uploaded_ready_file_input');

    fileInput.classList.remove('is-invalid', 'is-valid');
    if (!noCenz && fileInput.files.length < 1 ) {
        fileInput.classList.add('is-invalid');
        console.log('Есть ошибки валидации - проверьте выделенные поля');
        return;
    }
    fileInput.classList.remove('is-invalid');
    CenzApprove(task);

};

function CenzApprove(task) {
    let noCenz = document.getElementById('no_cenz').checked
    const cenzFormElements = document.getElementById('cenz_form').elements;
    let forms = {'program_id': programId}
    Array.from(cenzFormElements).forEach(element => {
        if (element.name) {
            if (element.type === 'file' && element.files.length > 0) {
                // Берем только имя файла из File object
                forms[element.name] = element.files[0].name;
            } else if (element.type === 'select-multiple') {
                // Обрабатываем множественный выбор
                const selectedValues = Array.from(element.selectedOptions).map(option => option.value).join(';');
                forms[element.name] = selectedValues;
            } else {
                forms[element.name] = element.value;
            };
        }
    });
//    console.log(forms);
    fetch(`/${task}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': forms['csrfmiddlewaretoken'],
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify([noCenz, forms]),
    credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = `/${programId}/`;
        }
        else {
            console.log('error', data.message)

            const CenzApproveModal = bootstrap.Modal.getInstance(document.getElementById('CenzApproveModal')) ||
                        new bootstrap.Modal(document.getElementById('CenzApproveModal'));
            const AskFixModal = bootstrap.Modal.getInstance(document.getElementById('AskFixModal')) ||
                        new bootstrap.Modal(document.getElementById('AskFixModal'));
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            error_message = document.getElementById('error_message');
            error_message.textContent = data.message;

            CenzApproveModal.hide();
            AskFixModal.hide();
            errorModal.toggle();
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
};

document.addEventListener('DOMContentLoaded', function() {
    let poster = document.getElementById('movie_poster');

    let materialType = poster.dataset.materialType;
    let programId = poster.dataset.programId;
    let parentId = poster.dataset.parentId;
    let fallback = poster.dataset.fallback;
    let name = poster.dataset.name;
    let year = poster.dataset.year;
    let country = poster.dataset.country;
    let query;
    let src;

    if (materialType === 'film') {
        query = [programId, name, year, country]
        src = `/media/posters/${programId}.jpg`
    }
    else {
        query = [parentId, name, year, country]
        src = `/media/posters/${parentId}.jpg`
    };

    function checkPoster() {
        fetch('/get_movie_poster/', {
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
                poster.src = src;
                console.log('success', src)
            }
            else {
                poster.src = fallback;
                console.log('error', fallback)
            }
        })
        .catch(error => {
            console.error('Error checking poster:', error);
            poster.src = fallback;
        });
    }

    checkPoster();
});

function enlargeImage(file) {
    const modalImage = document.getElementById('modalImage');
    const modalLabel = document.getElementById('imageModalLabel');
    fileName = file.dataset.fileName
    filePath = file.dataset.filePath;
    const fileType = file.dataset.fileType;
    if (fileType === 'image') {
            const imageModal = bootstrap.Modal.getInstance(document.getElementById('imageModal')) ||
            new bootstrap.Modal(document.getElementById('imageModal'));
        if (modalImage && modalLabel && file) {
            modalImage.src = filePath;
            modalLabel.textContent = fileName || "Изображение";
            imageModal.toggle();
        }
    }
    else {
        const link = document.createElement('a');
        link.href = filePath;
        link.download = fileName;
        link.click();
    }
};

function autoResizeTextareas() {
    let comments = document.getElementById('comment_textarea')
    let textareas = comments.querySelectorAll('textarea');
    if (textareas) {
        textareas.forEach(textarea => {
            const text = textarea.value;
            const cols = 80; // Примерное количество символов в строке (зависит от ширины textarea)

            // Разбиваем текст на строки с учетом явных переносов
            const explicitLines = text.split(/\r\n|\r|\n/);
            let totalLines = 0;

            explicitLines.forEach(line => {
                // Добавляем строки для переноса длинных строк
                totalLines += Math.max(1, Math.ceil(line.length / cols));
            });

            textarea.rows = Math.max(1, totalLines);
        });
    }
}

// Вызываем при загрузке страницы
document.addEventListener('DOMContentLoaded', autoResizeTextareas);

// Вызываем при раскрытии аккордеона
document.getElementById('collapseComments').addEventListener('shown.bs.collapse', function() {
    autoResizeTextareas();
});

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

function CopyText(field) {
    let textInput = document.getElementById(field)
    textInput.focus()
    textInput.select()
    document.execCommand('copy');
};