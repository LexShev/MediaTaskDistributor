function StartDistribution() {
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

