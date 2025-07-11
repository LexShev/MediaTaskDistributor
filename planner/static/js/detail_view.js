const programId = document.getElementById('program_id').dataset.programId;
const userId = document.body.dataset.userId || null;

window.addEventListener('load', CheckLockCard);
window.addEventListener('beforeunload', function(e) {
    fetch(`/unblock_card/${programId}/${userId}/`)
        .then(response => response.json())
        .then(data => {
            console.log(data.response);
        })
        .catch(error => {
            console.log('Unblock error:', error);
        });
});

async function CheckLockCard() {
    try {
        let response = await fetch(`/check_lock_card/${programId}/`);
        let data = await response.json();
        if (!data?.locked) {
            await fetch(`/block_card/${programId}/${userId}/`)
                .then(response => response.json())
                .then(data => {
                    console.log(data.response);
                })
                .catch(error => {
                    console.log('Block error:', error);
                });
            return;
        }
        let [lockType, [workerId, lockTime]] = data.locked;
        let workerName = await getWorkerName(workerId);

        let messageContainer = document.getElementById('message_container');
        messageContainer.innerHTML = `
            <div class="alert alert-warning alert-dismissible fade show mx-0 mb-2 mt-0" role="alert">
                Карточка материала заблокирована в ${lockType} пользователем: ${workerName} в ${FormatDate(lockTime)}
            </div>`;
        let cenzApproveBtn = document.getElementById('cenz_approve_btn');
        let askFixBtn = document.getElementById('ask_fix_btn');
        cenzApproveBtn.disabled = true;
        askFixBtn.disabled = true;
    } catch (error) {
        console.log('Loading error:', error);
    }
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
    } catch (error) {
        console.error('Getting name error:', error);
        return 'Аноним';
    }
}

function ValidateForm() {
    const form = document.querySelector('.needs-validation')
    const CenzApproveModal = bootstrap.Modal.getInstance(document.getElementById('CenzApprove')) ||
                        new bootstrap.Modal(document.getElementById('CenzApprove'));

    if (form.checkValidity()) {
        CenzApproveModal.toggle();
    }
    else {
        form.classList.add('was-validated');
    }
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
        src = `/static/banners/${programId}.jpg`
    }
    else {
        query = [parentId, name, year, country]
        src = `/static/banners/${parentId}.jpg`
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
})

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

function CopyText() {
    var text = document.getElementById('file_path')
    text.focus()
    text.select()
    document.execCommand('copy');
};