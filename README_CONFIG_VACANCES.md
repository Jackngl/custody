# 📖 Guide de Configuration - Vacances Scolaires

Ce guide explique comment configurer les **vacances scolaires** dans l'application Planning de garde.

> ⚠️ **Important** : 
> - Ce guide concerne **uniquement les vacances scolaires**
> - Les **vacances scolaires ont priorité absolue** sur la garde classique (weekends/semaines)
> - Les **jours fériés** ne s'appliquent pas pendant les vacances scolaires
> - Pour la garde classique, voir `README_CONFIG_GARDE.md`

---

## 📋 Table des matières

1. [Séparation garde classique / vacances scolaires](#séparation-garde-classique--vacances-scolaires)
2. [API des vacances scolaires](#api-des-vacances-scolaires)
3. [Zones scolaires](#zones-scolaires)
4. [Règles de vacances disponibles](#règles-de-vacances-disponibles)
5. [Configuration de base](#configuration-de-base)
6. [Règles de vacances détaillées](#règles-de-vacances-détaillées)
7. [Règles spéciales pour l'été](#règles-spéciales-pour-lété)
8. [Calcul des dates et horaires](#calcul-des-dates-et-horaires)
9. [Exemples de configuration](#exemples-de-configuration)

---

## 🔀 Séparation garde classique / vacances scolaires

L'application sépare clairement **deux systèmes de garde indépendants** :

### 1. **Garde classique** (voir `README_CONFIG_GARDE.md`)
- **Configuration** : Masque de saisie "Garde classique (weekends/semaines)"
- **Période** : Hors vacances scolaires uniquement
- **Fonctionnalités** :
  - Weekends alternés, semaines alternées, rythmes 2-2-3, etc.
  - Extension automatique avec jours fériés (vendredi/lundi)
  - Basé sur cycles ou parité ISO des semaines

### 2. **Vacances scolaires** (ce guide)
- **Configuration** : Masque de saisie "Vacances scolaires"
- **Période** : Pendant les vacances scolaires uniquement
- **Fonctionnalités** :
  - Récupération automatique des dates depuis l'API Éducation Nationale
  - Règles par moitié, par semaine, par parité d'année
  - Calcul automatique du milieu exact des vacances
  - Priorité absolue sur la garde classique

### ⚠️ Règle de priorité

```
Vacances scolaires > Jours fériés > Garde classique
```

- **Pendant les vacances** : Seules les règles de vacances s'appliquent
- **Hors vacances** : La garde classique s'applique, avec extension fériée si applicable
- **Jours fériés pendant vacances** : Ignorés (les vacances priment déjà)

---

## 🌐 API des vacances scolaires

L'application utilise l'**API officielle du Ministère de l'Éducation Nationale** pour récupérer automatiquement les dates des vacances scolaires.

### Source de données

- **API** : `https://data.education.gouv.fr/api/records/1.0/search/`
- **Dataset** : `fr-en-calendrier-scolaire`
- **Format** : JSON
- **Mise à jour** : Automatique (cache de 15 minutes)

### Fonctionnement

1. **Récupération automatique** : L'application interroge l'API pour votre zone scolaire
2. **Cache** : Les données sont mises en cache pour éviter les appels répétés
3. **Années scolaires** : L'API utilise le format "2024-2025" (septembre à juin)
4. **Filtrage** : Seules les vacances futures ou en cours sont affichées

### Zones supportées

| Zone | Code | Villes principales |
|------|------|-------------------|
| **Zone A** | `A` | Besançon, Bordeaux, Clermont-Ferrand, Dijon, Grenoble, Limoges, Lyon, Poitiers |
| **Zone B** | `B` | Aix-Marseille, Amiens, Lille, Nancy-Metz, Nantes, Nice, Normandie, Orléans-Tours, Reims, Rennes, Strasbourg |
| **Zone C** | `C` | Créteil, Montpellier, Paris, Toulouse, Versailles |
| **Corse** | `Corse` | Corse |
| **DOM-TOM** | `DOM-TOM` | Guadeloupe, Martinique, Guyane, La Réunion, Mayotte |

### Types de vacances récupérés

L'API fournit les périodes suivantes :
- **Vacances de la Toussaint** (octobre)
- **Vacances de Noël** (décembre-janvier)
- **Vacances d'Hiver** (février-mars)
- **Vacances de Printemps** (avril-mai)
- **Vacances d'Été** (juillet-août)
- **Pont de l'Ascension** (mai)

### Corrections manuelles

Certaines dates peuvent être corrigées manuellement dans le code si l'API est incomplète ou incorrecte (ex: Zone C hiver 2025-2026).

---

## ⚙️ Configuration de base

### Champs obligatoires

#### 1. **Zone scolaire** (`zone`)
- **Description** : Zone géographique pour les vacances scolaires
- **Valeurs** : `"A"`, `"B"`, `"C"`, `"Corse"`, `"DOM-TOM"`
- **Exemple** : `"C"` pour la zone C (Paris, Créteil, etc.)

#### 2. **Année de référence** (`reference_year`)
- **Description** : Détermine automatiquement quelle partie des vacances vous avez
- **Valeurs** : `"even"` (paire), `"odd"` (impaire)
- **Configuration** : Dans le masque de saisie "Vacances scolaires"
- **Fonctionnement automatique** :
  - `reference_year: "odd"` (impaire) → **1ère partie** des vacances (1ère semaine, 1ère moitié, Juillet)
  - `reference_year: "even"` (paire) → **2ème partie** des vacances (2ème semaine, 2ème moitié, Août)
- **Exemples** :
  - Année 2025 (impaire) + `reference_year: "odd"` → Vous avez la 1ère partie
  - Année 2026 (paire) + `reference_year: "even"` → Vous avez la 2ème partie
- **Note** : Cette logique s'applique à **toutes les vacances** (Noël, Hiver, Printemps, Toussaint, Été)

#### 3. **Niveau scolaire** (`school_level`)
- **Description** : Niveau scolaire de l'enfant (affecte les horaires de sortie)
- **Valeurs** : `"primary"` (primaire), `"middle"` (collège), `"high"` (lycée)
- **Impact** :
  - **Primaire** : Début des vacances = vendredi 16:15 (sortie d'école)
  - **Collège/Lycée** : Début des vacances = samedi matin (selon API)

### Champs optionnels

#### 4. **Règle d'été** (`summer_rule`)
- **Description** : Règle spéciale pour les vacances d'été (juillet-août)
- **Valeurs** : Voir [Règles spéciales pour l'été](#règles-spéciales-pour-lété)
- **Exemple** : `"summer_half_parity"` pour partage par moitié selon parité d'année

---

## 🎯 Règles de vacances disponibles

### Système simplifié basé sur `reference_year`

L'application utilise un **système automatique** basé sur le champ `reference_year` pour déterminer quelle partie des vacances vous avez :

- **`reference_year: "odd"` (impaire)** → **1ère partie** des vacances
  - 1ère semaine, 1ère moitié, Juillet (pour l'été)
  - S'applique automatiquement en **années impaires** (2025, 2027, ...)

- **`reference_year: "even"` (paire)** → **2ème partie** des vacances
  - 2ème semaine, 2ème moitié, Août (pour l'été)
  - S'applique automatiquement en **années paires** (2024, 2026, ...)

### Exemples

**Configuration** : `reference_year: "odd"` (impaire)
- **2025 (impaire)** : ✅ Vous avez la 1ère partie (1ère semaine, 1ère moitié, Juillet)
- **2026 (paire)** : ❌ Pas de garde (car c'est la 2ème partie, l'autre parent a la garde)

**Configuration** : `reference_year: "even"` (paire)
- **2024 (paire)** : ✅ Vous avez la 2ème partie (2ème semaine, 2ème moitié, Août)
- **2025 (impaire)** : ❌ Pas de garde (car c'est la 1ère partie, l'autre parent a la garde)

### Règles spéciales pour l'été (quinzaines)

| Règle | Code | Description |
|-------|------|-------------|
| **Automatique selon année** | `summer_parity_auto` | Année paire = Août complet<br>Année impaire = Juillet complet<br>S'applique aussi aux découpages (paire=seconde partie, impaire=première partie) |
| **Juillet - 1ère moitié** | `july_first_half` | 1er au 15 juillet |
| **Juillet - 2ème moitié** | `july_second_half` | 16 au 31 juillet |
| **Août - 1ère moitié** | `august_first_half` | 1er au 15 août |
| **Août - 2ème moitié** | `august_second_half` | 16 au 31 août |

> **Note** : Ces règles sont utilisées via le champ `summer_rule` et s'appliquent uniquement aux vacances d'été.

---

## 📅 Règles de vacances détaillées

### Système automatique basé sur `reference_year`

L'application détermine automatiquement quelle partie des vacances vous avez selon le champ `reference_year` :

#### 1. Première partie (`reference_year: "odd"`)

**Fonctionnement** :
- Garde la **première partie** des vacances (1ère semaine, 1ère moitié, Juillet pour l'été)
- **Uniquement en années impaires** (2025, 2027, ...)
- Années paires : pas de garde (car c'est la 2ème partie)
- **Milieu calculé automatiquement** pour les règles de moitié : Date/heure exacte au milieu de la période effective
- Début : Vendredi 16:15 (sortie d'école) ou samedi selon niveau
- Fin : Milieu exact (pour moitié) ou Dimanche 19:00 (pour semaine)

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # 1ère partie
school_level: "primary"
```

**Exemple** (Vacances de Noël 2025) :
- 2025 (impaire) : ✅ 1ère moitié (19/12/2025 16:15 → 27/12/2025 17:37:30)
- 2026 (paire) : ❌ Pas de garde (car c'est la 2ème partie)

---

#### 2. Deuxième partie (`reference_year: "even"`)

**Fonctionnement** :
- Garde la **deuxième partie** des vacances (2ème semaine, 2ème moitié, Août pour l'été)
- **Uniquement en années paires** (2024, 2026, ...)
- Années impaires : pas de garde (car c'est la 1ère partie)
- **Milieu calculé automatiquement** pour les règles de moitié : Date/heure exacte au milieu de la période effective
- Début : Milieu exact (pour moitié) ou début de la 2ème semaine
- Fin : Dimanche 19:00 (fin officielle)

**Configuration** :
```yaml
zone: "C"
reference_year: "even"  # 2ème partie
school_level: "primary"
```

**Exemple** (Vacances de Noël 2026) :
- 2026 (paire) : ✅ 2ème moitié (27/12/2026 17:37:30 → 03/01/2027 19:00)
- 2025 (impaire) : ❌ Pas de garde (car c'est la 1ère partie)

---

### Calcul du milieu exact

Pour les règles de partage par moitié, le milieu est calculé automatiquement :

- **Période effective** : Vendredi 16:15 → Dimanche 19:00 (fin officielle)
- **Milieu** = (début + fin) / 2 (avec heures et minutes précises)
- **Exemple** : 19/12/2025 16:15 → 05/01/2026 19:00 → Milieu = 27/12/2025 17:37:30

---

## ☀️ Règles spéciales pour l'été

Les règles d'été permettent de configurer spécifiquement les vacances d'été (juillet-août). Elles sont utilisées via le champ `summer_rule` dans le masque de saisie "Vacances scolaires".

### Automatique selon année (`summer_parity_auto`)

**Fonctionnement** :
- **Année paire** → Août complet
- **Année impaire** → Juillet complet
- S'applique automatiquement selon la parité de l'année des vacances

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # ou "even", utilisé pour les autres vacances
summer_rule: "summer_parity_auto"
school_level: "primary"
```

**Résultat** :
- 2024 (paire) : ✅ Août 2024 complet
- 2025 (impaire) : ✅ Juillet 2025 complet
- 2026 (paire) : ✅ Août 2026 complet

---

### Juillet - 1ère moitié (`july_first_half`)

**Fonctionnement** :
- Garde la **1ère quinzaine de juillet** (1er au 15 juillet)

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # ou "even"
summer_rule: "july_first_half"
school_level: "primary"
```

---

### Juillet - 2ème moitié (`july_second_half`)

**Fonctionnement** :
- Garde la **2ème quinzaine de juillet** (16 au 31 juillet)

**Configuration** :
```yaml
zone: "C"
reference_year: "even"  # ou "odd"
summer_rule: "july_second_half"
school_level: "primary"
```

---

### Août - 1ère moitié (`august_first_half`)

**Fonctionnement** :
- Garde la **1ère quinzaine d'août** (1er au 15 août)

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # ou "even"
summer_rule: "august_first_half"
school_level: "primary"
```

---

### Août - 2ème moitié (`august_second_half`)

**Fonctionnement** :
- Garde la **2ème quinzaine d'août** (16 au 31 août)

**Configuration** :
```yaml
zone: "C"
reference_year: "even"  # ou "odd"
summer_rule: "august_second_half"
school_level: "primary"
```

---

## 🕐 Calcul des dates et horaires

### Période effective des vacances

L'application ajuste automatiquement les dates de l'API pour correspondre aux horaires de garde :

#### Début effectif
- **Primaire** : Vendredi précédent à 16:15 (sortie d'école)
- **Collège/Lycée** : Samedi matin (selon API)

#### Fin effective
- **Toujours** : Dimanche 19:00 (même si l'API indique "reprise lundi")

### Calcul des dates

Les dates sont calculées automatiquement selon la règle sélectionnée et la parité de l'année (définie par `reference_year`).

---

## 📝 Exemples de configuration

### Exemple 1 : Partage par moitié (toutes vacances)

**Situation** : Vous avez la 1ère moitié, l'autre parent a la 2ème moitié.

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # 1ère partie (1ère moitié)
school_level: "primary"
```

**Résultat** (Vacances de Noël) :
- 2025 (impaire) : ✅ 1ère moitié (19/12/2025 16:15 → 27/12/2025 17:37:30)
- 2026 (paire) : ❌ Pas de garde (car c'est la 2ème partie, l'autre parent a la garde)

---

### Exemple 2 : Règle automatique été (paire=Août, impaire=Juillet)

**Situation** : Année paire = Août complet, Année impaire = Juillet complet.

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # Utilisé pour les autres vacances (1ère partie)
summer_rule: "summer_parity_auto"  # Automatique selon année
school_level: "primary"
```

**Résultat** :
- 2024 (paire) : ✅ Août 2024 complet
- 2025 (impaire) : ✅ Juillet 2025 complet
- 2026 (paire) : ✅ Août 2026 complet
- 2027 (impaire) : ✅ Juillet 2027 complet

> **Note** : Cette règle s'applique automatiquement selon la parité de l'année des vacances. Le champ `reference_year` est utilisé pour les autres vacances (Noël, Hiver, Printemps, Toussaint).

---

### Exemple 3 : Quinzaine de juillet

**Situation** : Vous avez la 1ère quinzaine de juillet (1-15 juillet).

**Configuration** :
```yaml
zone: "C"
reference_year: "odd"  # ou "even"
summer_rule: "july_first_half"  # 1ère moitié de juillet
school_level: "primary"
```

**Résultat** (Juillet 2025) :
- 1-15 juillet 2025 : ✅ Garde
- 16-31 juillet 2025 : ❌ Pas de garde

---

### Exemple 4 : Quinzaine d'août

**Situation** : Vous avez la 2ème quinzaine d'août (16-31 août).

**Configuration** :
```yaml
zone: "C"
reference_year: "even"  # ou "odd"
summer_rule: "august_second_half"  # 2ème moitié d'août
school_level: "primary"
```

**Résultat** (Août 2026) :
- 1-15 août 2026 : ❌ Pas de garde
- 16-31 août 2026 : ✅ Garde

---


## 🔧 Dépannage

### L'API ne retourne pas de données

1. **Vérifier la zone** : Assurez-vous que la zone est correcte (A, B, C, Corse, DOM-TOM)
2. **Vérifier l'année scolaire** : L'API utilise le format "2024-2025"
3. **Tester la connexion** : Utilisez le service `test_holiday_api` dans Home Assistant
4. **Vérifier les logs** : Consultez les logs pour voir les erreurs API

### Les dates ne correspondent pas

1. **Niveau scolaire** : Vérifiez que `school_level` est correct (primaire = vendredi 16:15)
2. **Zone** : Vérifiez que la zone correspond à votre académie
3. **Année** : Vérifiez que l'année de référence est correcte pour les règles basées sur la parité

### Les règles ne s'appliquent pas correctement

1. **Reference_year** : Vérifiez que `reference_year` est correctement configuré (paire/impaire)
   - `"odd"` (impaire) = 1ère partie (années impaires)
   - `"even"` (paire) = 2ème partie (années paires)
2. **Summer_rule** : Vérifiez que `summer_rule` est correctement configuré pour les vacances d'été
3. **Logs** : Consultez les logs pour voir les dates calculées

---

## 📚 Ressources

- **API Éducation Nationale** : https://data.education.gouv.fr/explore/dataset/fr-en-calendrier-scolaire
- **Documentation garde classique** : `README_CONFIG_GARDE.md`
- **Zones scolaires** : https://www.education.gouv.fr/les-zones-de-vacances-12073

---

## ✅ Récapitulatif

### Priorité des règles

```
Vacances scolaires > Jours fériés > Garde classique
```

### Points clés

- ✅ Les vacances sont récupérées automatiquement depuis l'API
- ✅ Les dates sont ajustées pour correspondre aux horaires de garde
- ✅ Le milieu est calculé automatiquement pour les règles de partage
- ✅ Les vacances remplacent complètement la garde classique pendant leur durée
- ✅ Les jours fériés ne s'appliquent pas pendant les vacances

