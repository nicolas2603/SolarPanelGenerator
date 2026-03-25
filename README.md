# SolarPanelGenerator - Plugin QGIS

Plugin QGIS pour la génération automatique d'implantations de panneaux solaires avec optimisation et calcul de couverture.

![QGIS](https://img.shields.io/badge/QGIS-3.16+-green.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)

## Caractéristiques principales

- **Génération automatique** de panneaux photovoltaïques dans des zones polygonales
- **Optimisation de l'implantation** avec calcul de 200 combinaisons pour interrang fixe
- **Calcul du taux de couverture** et implantation possible
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
│   └── panel_dialog.py            # Interface utilisateur et logique algorithme
│
├── forms/
│   └── panel_generator_dialog.ui  # Interface Qt Designer
│
├── core/                          # Logique algorithme principale
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

## Installation

1. Télécharger le plugin
2. Extraire dans le dossier plugins QGIS
3. Redémarrer QGIS
4. Activer le plugin dans le gestionnaire d'extensions

## Utilisation

1. Sélectionner une couche de polygones
2. Configurer les dimensions des panneaux
3. Définir les espacements
4. Choisir le mode de calcul :
   - Génération simple
   - Calcul de recouvrement avec interrang fixe
   - Optimisation automatique pour un taux cible
5. Lancer la génération

## Licence

GPL-3.0 - Voir [LICENSE](LICENSE)

## Auteur

Nicolas Lieutenant
