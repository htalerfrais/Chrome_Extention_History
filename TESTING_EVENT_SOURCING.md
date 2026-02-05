# Tests Event-Sourcing Architecture

## Changements Implémentés

### 1. Permission Alarms
✅ Ajoutée dans `extension/manifest.json`

### 2. SessionService Réécrit
✅ Event-sourcing avec cache intelligent (~250 lignes vs ~450 avant)
- Plus de state machine (currentSession/completedSessions en mémoire)
- Dérivation à la demande depuis historyItems
- Cache à deux niveaux (completed/current)
- chrome.alarms pour analyse automatique

### 3. Background.js Modifié
✅ Suppression de `startTracking()` et `addItem()`
✅ Ajout de `onNewItem()` pour reprogrammer l'alarme

## Tests à Effectuer

### Test 1: Chargement Initial
1. Recharger l'extension dans Chrome (`chrome://extensions/`)
2. Ouvrir la console du service worker (background)
3. Vérifier les logs:
   ```
   [SESSION] Initializing session service (event-sourcing mode)...
   [SESSION] Loaded X analyzed session IDs
   [SESSION] Session service initialized
   ```

### Test 2: Navigation et Création de Session
1. Naviguer sur plusieurs pages (5-10 pages)
2. Dans la console, vérifier:
   ```
   [SESSION] Alarm reprogrammed: check in X min
   ```
3. Ouvrir le dashboard
4. Vérifier qu'une session courante apparaît avec les pages visitées

### Test 3: Refresh Dashboard (Cache)
1. Avec le dashboard ouvert, rafraîchir la page
2. Dans la console, vérifier:
   ```
   [SESSION] Item count unchanged, using cache
   [SESSION] Returning X sessions from cache
   ```
3. Les sessions doivent apparaître instantanément (cache)

### Test 4: Dérivation Incrémentale
1. Naviguer sur 2-3 nouvelles pages
2. Rafraîchir le dashboard
3. Dans la console, vérifier:
   ```
   [SESSION] X new items, incremental derivation
   [SESSION] Returning X sessions (Y completed, Z current)
   ```

### Test 5: Fermeture de Session par Timeout
1. Arrêter de naviguer pendant 30+ minutes
2. Attendre que l'alarme se déclenche
3. Dans la console, vérifier:
   ```
   [SESSION] Alarm triggered: checking closed sessions
   [SESSION] Found X completed sessions
   [SESSION] Analyzing session: session_XXXXXXXX
   [SESSION] ✅ Session session_XXXXXXXX analyzed successfully
   ```

### Test 6: Analyse Automatique
1. Créer une session (naviguer sur plusieurs pages)
2. Attendre 30+ minutes (ou modifier `SESSION_GAP_MINUTES` temporairement)
3. Vérifier que la session est automatiquement envoyée au backend
4. Rafraîchir le dashboard
5. Vérifier que la session a des clusters analysés

### Test 7: Pas de Perte d'Items
1. Naviguer activement (10+ pages)
2. Fermer brutalement Chrome (pas de shutdown gracieux)
3. Rouvrir Chrome et recharger l'extension
4. Ouvrir le dashboard
5. Vérifier que TOUTES les pages visitées sont présentes dans les sessions

### Test 8: Service Worker Idle/Wake
1. Naviguer sur quelques pages
2. Ne rien faire pendant 5 minutes (le service worker s'endort)
3. Rouvrir le dashboard
4. Dans la console, vérifier que les sessions sont correctement dérivées
5. L'alarme doit toujours fonctionner après le réveil

## Logs de Debug

Les logs importants à surveiller:

### Initialisation
```
[SESSION] Initializing session service (event-sourcing mode)...
[SESSION] Loaded X analyzed session IDs
[SESSION] Checking for closed sessions to analyze...
[SESSION] Session service initialized
```

### Nouveau Item
```
[SESSION] Alarm reprogrammed: check in X min
```

### Dérivation (première fois)
```
[SESSION] Full derivation of sessions
[SESSION] Returning X sessions (Y completed, Z current)
```

### Dérivation (cache hit)
```
[SESSION] Item count unchanged, using cache
[SESSION] Returning X sessions from cache
```

### Dérivation (incrémentale)
```
[SESSION] X new items, incremental derivation
[SESSION] Returning X sessions (Y completed, Z current)
```

### Analyse Automatique
```
[SESSION] Alarm triggered: checking closed sessions
[SESSION] Found X completed sessions, Y already analyzed
[SESSION] Analyzing session: session_XXXXXXXX (Z items)
[SESSION] ✅ Session session_XXXXXXXX analyzed successfully
[SESSION] Analyzed X new sessions
```

## Vérifications Chrome DevTools

### Storage
Dans `chrome://extensions/` → Extension → "Inspect views: service worker" → Console:
```javascript
chrome.storage.local.get(['analyzedSessionIds', 'historyItems'], console.log)
```

Vérifier:
- `analyzedSessionIds`: Array de session_identifiers
- `historyItems`: Array d'items (max 5000)

### Alarms
Dans la console:
```javascript
chrome.alarms.getAll(console.log)
```

Devrait montrer:
```javascript
[{
  name: "checkClosedSessions",
  scheduledTime: <timestamp>,
  periodInMinutes: undefined
}]
```

## Points d'Attention

1. **Pas de currentSession/completedSessions en storage** : Ces clés ne sont plus utilisées
2. **Cache en mémoire seulement** : Le cache est perdu au redémarrage du service worker, c'est normal
3. **Alarmes survivent au service worker idle** : C'est l'avantage principal vs setTimeout
4. **Performance** : Les appels répétés à getAllSessions doivent être rapides (cache)

## Comparaison Ancien vs Nouveau

| Aspect | Ancien | Nouveau |
|--------|--------|---------|
| Source of truth | currentSession en storage | historyItems |
| Fermeture session | setTimeout (perdu si idle) | chrome.alarms (persiste) |
| Performance refresh | Recalcul à chaque fois | Cache intelligent |
| Perte d'items | Possible si formatSessionForApi échoue | Impossible |
| Complexité | ~450 lignes, timers | ~250 lignes, event-sourcing |

## Si Problème

1. Vérifier les logs dans la console du service worker
2. Vérifier le storage: `chrome.storage.local.get(console.log)`
3. Vérifier les alarmes: `chrome.alarms.getAll(console.log)`
4. En cas de doute, recharger l'extension complètement
