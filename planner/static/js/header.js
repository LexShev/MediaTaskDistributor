function StartDistribution() {
    svg_spinner = document.getElementById('svg_spinner');
    svg_spinner.classList.add('spinner');
    console.log(svg_spinner);
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

