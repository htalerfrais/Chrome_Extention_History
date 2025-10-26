// background.js
importScripts('utils/preprocess_history.js');
importScripts('scripts/constants.js');
importScripts('api/config.js');
importScripts('api/api_client.js');

const MAX_ITEMS = 5000;

// Collecte l'historique initial et le stocke dans chrome.storage.local
function collectHistory() {
    chrome.history.search(
        { text: '', maxResults: MAX_ITEMS, startTime: 0 },
        function(results) {         // fonction de callback 
            const dated = datesFormating(results);
            const withUrlFeatures = addUrlFeatures(dated);
            const filtered = filterHistoryURL(withUrlFeatures);
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


chrome.identity.getAuthToken({ interactive: true }, async (token) => {
    if (chrome.runtime.lastError || !token) {
      console.error('Auth error:', chrome.runtime.lastError?.message || 'No token');
      return; // don't call /authenticate with an invalid token
    }
    try {
      const user = await authenticateWithGoogle(token);
      console.log("Authenticated user:", user);
      
      // Store token for future requests
      await chrome.storage.local.set({ userToken: token });
      console.log("User token stored in chrome.storage.local");
    } catch (e) {
      console.error("Backend auth failed:", e);
    }
});


// Mise à jour en temps réel avec un listner 
chrome.history.onVisited.addListener((result) => {
    chrome.storage.local.get({ historyItems: [] }, (data) => {
        let historyItems = data.historyItems;
        // Traiter uniquement le nouvel item
        const processedNew = filterHistoryURL(addUrlFeatures(datesFormating([result])));
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
