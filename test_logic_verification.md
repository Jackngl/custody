# Vérification de la logique de calcul

## Scénarios à tester

### Scénario 1 : Enfant en garde, fenêtre se termine dans le futur
- `current_window` existe
- `current_window.end > now_local + 1 minute`
- `is_present = True`
- **Attendu** :
  - `next_departure = current_window.end`
  - `next_arrival = fenêtre après current_window.end`

### Scénario 2 : Enfant en garde, fenêtre se termine très bientôt (< 1 minute)
- `current_window` existe
- `current_window.end <= now_local + 1 minute`
- **Attendu** :
  - `is_present = False` (forcé)
  - `current_window = None`
  - `next_arrival = next_window.start`
  - `next_departure = next_window.end`

### Scénario 3 : Enfant pas en garde, prochaine fenêtre dans le futur
- `current_window = None`
- `next_window` existe
- `is_present = False`
- **Attendu** :
  - `next_arrival = next_window.start`
  - `next_departure = next_window.end`

### Scénario 4 : Enfant pas en garde, pas de fenêtre future
- `current_window = None`
- `next_window = None`
- `is_present = False`
- **Attendu** :
  - `next_arrival = None`
  - `next_departure = None`

### Scénario 5 : Override actif avec date de fin
- `override_state = True`
- `presence_override["until"]` existe
- **Attendu** :
  - `is_present = True`
  - `next_departure = presence_override["until"]`
  - `next_arrival = fenêtre après until`

### Scénario 6 : Override actif sans date de fin
- `override_state = True`
- `presence_override["until"] = None`
- **Attendu** :
  - `is_present = True`
  - `next_departure = next_window.end`
  - `next_arrival = next_window.start`

## Problèmes identifiés

1. **Redondance ligne 201-204** : La vérification est redondante car on a déjà filtré à la ligne 184
2. **Ligne 249** : Vérification `next_departure <= now_local` mais `next_window.end` devrait toujours être dans le futur
3. **Ligne 251** : Utilise `now_local` au lieu de `now_local + timedelta(minutes=1)` pour la cohérence
