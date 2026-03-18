function toggleScheduleItem(scheduledProgramId) {
    const childrenContainer = document.getElementById(`children_${scheduledProgramId}`);
    const toggleIcon = document.getElementById(`toggle-${scheduledProgramId}`);
    const svgElement = toggleIcon.querySelector('svg');

    if (childrenContainer.style.display === 'none') {
        childrenContainer.style.display = 'block';
        svgElement.style.transform = 'rotate(0deg)';
    } else {
        childrenContainer.style.display = 'none';
        svgElement.style.transform = 'rotate(-90deg)';
    }
}

function toggleScheduleAllItem(switcher) {
    const childrenContainers = document.querySelectorAll('.schedule-children');
    childrenContainers.forEach(child => {
            let svgElement = child.parentElement.querySelector('.folder-toggle');
            if (switcher.checked === false) {
                    child.style.display = 'block';
                    svgElement.style.transform = 'rotate(0deg)';
                } else {
                    child.style.display = 'none';
                    svgElement.style.transform = 'rotate(-90deg)';
                }
    })


}

function toggleAdvert(switcher) {
    let advertContainers = document.querySelectorAll('.advert');
    advertContainers.forEach(advertContainer => {
        if (switcher.checked === true) {
            advertContainer.style.display = 'none'
        }
        else {
            advertContainer.style.display = 'block'

        }
    })
}

function toggleProgram(switcher) {
    let programContainers = document.querySelectorAll('.segment');
    programContainers.forEach(programContainer => {
        if (switcher.checked === true) {
            programContainer.style.display = 'none'
        }
        else {
            programContainer.style.display = 'block'

        }
    })
}