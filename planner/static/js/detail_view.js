const programId = document.getElementById('program_id').dataset.programId;
const userId = document.body.dataset.userId || null;

window.addEventListener('load', CheckLockCard);
window.addEventListener('beforeunload', function(e) {
    fetch(`/unblock_card/${programId}/${userId}`)
        .then(response => response.json())
        .then(data => {
            console.log(data.response);
        })
        .catch(error => {
            console.log('Ошибка разблокировки:', error);
        });
});

async function CheckLockCard() {
    try {
        let response = await fetch(`/check_lock_card/${programId}`);
        let data = await response.json();
        if (!data?.locked) {
            await fetch(`/block_card/${programId}/${userId}`)
                .then(response => response.json())
                .then(data => {
                    console.log(data.response);
                })
                .catch(error => {
                    console.log('Ошибка блокировки:', error);
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
        console.log('Ошибка загрузки:', error);
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
        console.error('Ошибка при получении имени:', error);
        return 'Аноним';
    }
}

function UpdateCenzInfo() {

}