document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value.toLowerCase();  // getElementById permet de se référer au HTML de la page 

    chrome.storage.local.get({historyItems: []}, (data) => { // fonction callback exécuter une fonction avec la donnée lue dans storage.local as data
        console.log(data.historyItems)
        const results = data.historyItems.filter(item =>
            item.title && item.title.toLowerCase().includes(query)
        );

        const resultsEl = document.getElementById('results'); // here resultsEl : est result html element != results as JS variable
        resultsEl.innerHTML = ''; // resets the html element to put what has been processed by the java script (the filtered history)
        results.forEach(item => { // this part is to put what we want to display in the html document ( title and url )
            const li = document.createElement('li');
            li.textContent = item.title + " (" + item.url + ")";
            resultsEl.appendChild(li);
            console.log(li)
        });
    });
});

// Allow Enter key to trigger the same search action (simulate a click)
document.getElementById('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('searchBtn').click();
    }
});