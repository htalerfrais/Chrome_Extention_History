document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value.toLowerCase();

    chrome.storage.local.get({historyItems: []}, (data) => {
        const results = data.historyItems.filter(item =>
            item.title && item.title.toLowerCase().includes(query)
        );

        const resultsEl = document.getElementById('results');
        resultsEl.innerHTML = '';
        results.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.title + " (" + item.url + ")";
            resultsEl.appendChild(li);
        });
    });
});