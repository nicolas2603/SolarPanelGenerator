# SolarPanelGenerator - Plugin QGIS

Plugin QGIS pour la génération automatique d'implantations de panneaux solaires avec optimisation et calcul de recouvrement.

## Caractéristiques principales

- **Génération automatique** de panneaux photovoltaïques dans des zones polygonales
- **Optimisation de l'implantation** avec calcul de 400 combinaisons pour interrang fixe
- **Calcul du taux de recouvrement** et implantation possible
- **Support des trackers solaires** avec orientation verticale
- **Gestion des demi-tables** pour optimiser l'utilisation de l'espace
- **Compatible Qt5/Qt6** - Fonctionne avec toutes les versions QGIS 3.16+
- **Interface intuitive** avec validation en temps réel des paramètres

## Compatibilité

- **QGIS** : 3.16 - 3.99
- **Qt** : Qt5 et Qt6 (détection automatique via qgis.PyQt)
- **Python** : 3.7+
- **Plateformes** : Windows, Linux, macOS

## Architecture du code

### Structure des modules

```
SolarPanelGenerator/
├── __init__.py                    # Point d'entrée avec vérifications Qt5/Qt6
├── solar_panel_generator.py       # Plugin principal QGIS
├── config.py                      # Configuration centralisée avec paramètres de sécurité
├── panel_models.json              # Modèles de panneaux prédéfinis
├── qt_detection.py                # Détection automatique Qt5/Qt6
│
├── ui/
│   └── panel_dialog.py            # Interface utilisateur et logique métier
│
├── forms/
│   └── panel_generator_dialog.ui  # Interface Qt Designer
│
├── core/                          # Logique métier principale
│   ├── tracing_logic.py           # Algorithme de traçage sécurisé
│   └── coverage_logic.py          # Calcul des enveloppes de couverture
│
├── utils/                         # Utilitaires et helpers
│   ├── layer_helpers.py           # Helpers pour les couches QGIS
│   ├── geometry_helpers.py        # Helpers géométriques
│   ├── parameter_validator.py     # Validation robuste des paramètres
│   └── panel_models_manager.py    # Gestionnaire des modèles de panneaux
│
├── icons/
│   └── solar-energy.svg           # Icône du plugin
│
└── metadata.txt                   # Métadonnées du plugin
```

### Classes principales

#### Interface et coordination
- **`SolarPanelGeneratorPlugin`** : Plugin principal avec intégration QGIS
  - Gestion du cycle de vie du plugin
  - Création des actions et menus
  - Compatible Qt5/Qt6 via qgis.PyQt
  
- **`SolarPanelGeneratorDialog`** : Interface utilisateur avec logique de validation
  - Validation en temps réel des paramètres
  - Gestion des trois modes : génération simple, calcul recouvrement, optimisation
  - Interface responsive avec feedback visuel

#### Gestionnaires de données
- **`PanelModelsManager`** : Gestionnaire des modèles de panneaux prédéfinis
  - Chargement automatique depuis `panel_models.json`
  - Interface utilisateur avec combobox de sélection
  - Format extensible supportant métadonnées (puissance, fabricant, etc.)

#### Logique métier
- **`TracingLogic`** : Interface de compatibilité pour le traçage d'enveloppe
- **`PanelTracer`** : Algorithme de traçage sécurisé avec protection anti-boucles
  - Protection contre les boucles infinies avec limites configurables
  - Gestion sécurisée de l'état du traçage via `TracingState`
  - Algorithme de décision complexe pour le traçage optimal

- **`TracingState`** : Gestion sécurisée de l'état du traçage
  - Limites de récursion (200 appels max)
  - Limite par panneau (15 décisions max)
  - Timeout d'exécution (120 secondes max)

- **`CoverageLogic`** : Calcul des surfaces de recouvrement
  - Génération d'enveloppes de couverture
  - Calcul des taux de recouvrement par îlot
  - Intégration avec le système de traçage

#### Helpers et validation
- **`GeometryHelpers`** : Opérations géométriques (placement, optimisation)
  - Détection et séparation des trous dans les polygones
  - Placement optimisé des panneaux avec différents modes d'ancrage
  - Support des orientations horizontales et verticales (trackers)

- **`LayerHelpers`** : Utilitaires pour les couches QGIS
  - Filtrage strict des couches polygonales
  - Création de couches temporaires
  - Compatible Qt5/Qt6

- **`ParameterValidator`** : Validation complète des paramètres utilisateur
  - Validation progressive : syntaxe → limites → cohérence géométrique
  - Messages d'erreur explicites avec suggestions
  - Validation en temps réel avec feedback visuel

- **`ParameterNormalizer`** : Normalisation des valeurs numériques
  - Arrondi automatique à la précision appropriée
  - Normalisation des très petites valeurs

#### Configuration et compatibilité
- **`Config`** : Configuration centralisée avec constantes et méthodes utilitaires
  - Paramètres par défaut et limites de validation
  - Gestion des trois modes d'exécution
  - Configuration des couleurs et du rendu

- **`QtDetection`** : Système de détection Qt5/Qt6
  - Détection automatique de la version Qt
  - Marqueurs de compatibilité pour QGIS
  - Gestion des erreurs de compatibilité

### Nouveautés version compatible Qt5/Qt6

#### Système de compatibilité Qt
- **Détection automatique** de Qt5/Qt6 via `qgis.PyQt`
- **Import unifié** : tous les modules utilisent `qgis.PyQt`
- **Métadonnées étendues** avec marqueurs de compatibilité
- **Messages de debug** pour confirmer la version Qt détectée

#### Améliorations de l'interface
- **Validation en temps réel** des paramètres avec coloration des champs
- **Messages informatifs** avec séparateurs visuels
- **Logique de verrouillage** des options incompatibles
- **Gestion intelligente** des valeurs par défaut

#### Modes d'exécution améliorés
- **Mode 1 - Génération simple** : placement sans calcul de recouvrement
- **Mode 2 - Calcul recouvrement** : avec v_spacing fixe saisi
- **Mode 3 - Optimisation** : recherche automatique du v_spacing optimal

#### Robustesse et sécurité
- **Protection du traçage** contre les boucles infinies
- **Gestion d'erreur** gracieuse avec continuation
- **Validation géométrique** complète
- **Compatible** toutes versions QGIS 3.16+

### Flux de données

```
Interface utilisateur (Qt5/Qt6 compatible)
    ↓ (paramètres validés)
ParameterValidator
    ↓ (paramètres normalisés)
GeometryHelpers (placement panneaux)
    ↓ (rectangles)
TracingLogic (si recouvrement demandé)
    ↓ (enveloppes sécurisées)
CoverageLogic (calcul surfaces)
    ↓ (statistiques)
LayerHelpers (création couches QGIS)
    ↓ (couches finales)
Interface QGIS
```

### Sécurité et robustesse

#### Protection du traçage
- **Limite de récursion** : 200 appels maximum
- **Limite par panneau** : 15 décisions maximum  
- **Timeout d'exécution** : 120 secondes maximum
- **Validation d'état** continue avec gestion d'exceptions

#### Validation des paramètres
- **Validation progressive** : syntaxe → limites → cohérence géométrique
- **Feedback visuel** : coloration des champs en erreur
- **Messages explicites** avec suggestions de correction
- **Normalisation automatique** des valeurs numériques

#### Compatibilité Qt5/Qt6
- **Imports unifiés** via `qgis.PyQt` pour tous les modules
- **Détection automatique** de la version Qt au chargement
- **Gestion d'erreur** robuste pour les incompatibilités
- **Metadata étendues** pour la reconnaissance par QGIS

#### Gestion d'erreur
- **Capture d'exceptions** à tous les niveaux critiques
- **Continuation gracieuse** en cas d'erreur partielle
- **Logging détaillé** pour le débogage
- **Retour utilisateur** informatif sans détails techniques

## Installation

1. Télécharger le plugin
2. Extraire dans le dossier plugins QGIS
3. Redémarrer QGIS
4. Activer le plugin dans le gestionnaire d'extensions

Compatible avec toutes les versions QGIS récentes (Qt5 et Qt6).

## Utilisation

1. Sélectionner une couche de polygones
2. Configurer les dimensions des panneaux
3. Définir les espacements
4. Choisir le mode de calcul :
   - Génération simple
   - Calcul de recouvrement avec v_spacing fixe
   - Optimisation automatique pour un taux cible
5. Lancer la génération

## Licence

GPL-3.0-or-later - Copyright (C) 2025 Nicolas Lieutenant