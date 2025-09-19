document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value.toLowerCase();  // getElementById permet de se référer au HTML de la page 

    chrome.storage.local.get({historyItems: []}, (data) => { // fonction callback exécuter une fonction avec la donnée lue dans storage.local as data
        console.log(data.historyItems)
        const results = data.historyItems.filter(item => {
            const t = (item.title || '').toLowerCase();
            const u = (item.url || '').toLowerCase();
            return (t && t.includes(query)) || (u && u.includes(query));
        });

        const resultsEl = document.getElementById('results'); // here resultsEl : est result html element != results as JS variable
        resultsEl.innerHTML = ''; // resets the html element to put what has been processed by the java script (the filtered history)
        results.forEach(item => { // this part is to put what we want to display in the html document ( title and url )
            const li = document.createElement('li');
            const row = document.createElement('div');
            row.className = 'result-row';

            // favicon
            let hostname = '';
            try { hostname = new URL(item.url).hostname; } catch (e) { hostname = ''; }
            const favicon = document.createElement('img');
            favicon.className = 'favicon';
            favicon.src = hostname ? `https://www.google.com/s2/favicons?domain=${hostname}&sz=32` : 'icons/Engrave-16.png';
            favicon.alt = 'favicon';

            // title + date
            const meta = document.createElement('div');
            meta.className = 'meta';
            const title = document.createElement('div');
            title.className = 'title';
            title.textContent = item.title || item.url || '(Sans titre)';
            const date = document.createElement('div');
            date.className = 'date';
            const visitDate = item.lastVisitISO || (typeof item.lastVisitTime === 'number' ? new Date(item.lastVisitTime).toISOString() : null);
            if (visitDate) {
                date.textContent = new Date(visitDate).toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
            } else {
                date.textContent = '';
            }
            meta.appendChild(title);
            meta.appendChild(date);

            // open button
            const openBtn = document.createElement('button');
            openBtn.className = 'open-btn';
            openBtn.title = 'Ouvrir dans un nouvel onglet';
            openBtn.textContent = '↗';
            openBtn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                if (item.url) {
                    chrome.tabs.create({ url: item.url });
                }
            });

            row.appendChild(favicon);
            row.appendChild(meta);
            row.appendChild(openBtn);
            li.appendChild(row);
            resultsEl.appendChild(li);
        });
    });
});

// Allow Enter key to trigger the same search action (simulate a click)
document.getElementById('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('searchBtn').click();
    }
});

// Dashboard button handler
document.getElementById('dashboardBtn').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html') });
});