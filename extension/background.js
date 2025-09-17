// background.js

const MAX_ITEMS = 5000;

// Fonction pour collecter l'historique initial et le mettre dans le chrome storage
function collectHistory() {
    chrome.history.search(
        { text: '', maxResults: MAX_ITEMS, startTime: 0 },
        function(results) {
            chrome.storage.local.set({ historyItems: results }, () => {
                console.log(`Historique collecté : ${results.length} items`);
                console.log(results)
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
        historyItems.push(result);

        // Limiter le nombre d'items pour rester dans chrome.storage.local
        if (historyItems.length > MAX_ITEMS) {
            historyItems = historyItems.slice(-MAX_ITEMS);
        }

        chrome.storage.local.set({ historyItems: historyItems }, () => {
            console.log(`Nouvelle page ajoutée : ${result.url}`);
        });
    });
});
