// background.js
importScripts('utils.js');

const MAX_ITEMS = 5000;

// Collecte l'historique initial et le stocke dans chrome.storage.local
function collectHistory() {
    chrome.history.search(
        { text: '', maxResults: MAX_ITEMS, startTime: 0 },
        function(results) {         // fonction de callback 
            const dated = datesFormating(results);
            const filtered = filterHistory(dated);
            chrome.storage.local.set({ historyItems: filtered }, () => {
                console.log(`Historique collecté initial: ${results.length} items`);
                console.log(results)
                console.log(`Historique collecté filtré: ${filtered.length} items`);
                console.log(filtered)
            });
        } 
    );
}

// Collecte initiale au lancement du service worker
collectHistory();

// Mise à jour en temps réel avec un listner 
chrome.history.onVisited.addListener((result) => {
    chrome.storage.local.get({ historyItems: [] }, (data) => {
        let historyItems = data.historyItems;
        // Traiter uniquement le nouvel item
        const processedNew = filterHistory(datesFormating([result]));
        if (processedNew && processedNew.length > 0) {
            historyItems.push(processedNew[0]);
        }

        // Limiter le nombre d'items pour rester dans chrome.storage.local
        if (historyItems.length > MAX_ITEMS) {
            historyItems = historyItems.slice(-MAX_ITEMS);
        }

        chrome.storage.local.set({ historyItems: historyItems }, () => {
            console.log(`Nouvelle page ajoutée : ${result.url}`);
        });
    });
});
