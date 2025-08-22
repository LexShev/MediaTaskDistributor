function startDistribution() {
    svg_spinner = document.getElementById('svg_spinner');
    svg_spinner.classList.add('spinner');
    fetch('/start_distribution/')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = '/'
                console.log(data.status);
            }
            else {
                console.log(data.status);
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
                window.location.href = '/'
                console.log(data.status);
            }
            else {
                console.log(data.status);
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
