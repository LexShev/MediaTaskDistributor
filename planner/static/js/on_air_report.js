document.addEventListener('DOMContentLoaded', function() {
    const channelContainer = document.querySelectorAll('.channel-container');
    channelContainer.forEach(channel => {
        const scheduleId = channel.dataset.scheduleId;
        const scheduleDate = channel.dataset.scheduleDate;
        fetch(`/on-air-report/get_schedule_table/${scheduleDate}/${scheduleId}`)
            .then(response => response.json())
            .then(data => {
                channel.innerHTML = data.html;
            })
            .catch(error => {
                console.error('Error loading day data:', error);
            });
    })
});

function changeProgramIdCheckbox(fullSelectCheckbox) {
    let tableBody = fullSelectCheckbox.closest('table').querySelector('tbody');
    let visibleCheckboxes = tableBody.querySelectorAll('tr:not([style*="display: none"]) input[name="program_id_check"]');
    let checkedVisibleList = [];
        visibleCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            checkedVisibleList.push(checkbox);
        }
    });

    if (checkedVisibleList.length > 0) {
        // Если есть выделенные видимые чекбоксы - снимаем выделение
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    } else {
        // Если нет выделенных видимых чекбоксов - выделяем все видимые
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    }
};

function ShowApproveFinal() {
    let checked_list = document.getElementsByName('program_id_check');
    let program_id_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);}
        }
    if (program_id_list.length > 0) {
        ApproveOTK = new bootstrap.Modal(document.getElementById('ApproveFinal'));
        ApproveOTK.toggle();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
};

function ShowReadyFail() {

};