# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-09-10

### Ajouté
- Protection récursion intelligente pour les grandes installations
- Filtrage spatial optimisé des candidats de traçage
- Statistiques de performance en temps réel
- Support de milliers de panneaux sans limitation artificielle
- Monitoring détaillé des opérations de traçage

### Amélioré
- Performance du traçage : réduction jusqu'à 95% des candidats examinés
- Stabilité sur les grandes installations (plus de crash par débordement)
- Timeout étendu de 2 à 5 minutes pour les projets complexes
- Gestion mémoire optimisée

### Technique
- Nouveau système de protection basé sur les visites (panneau, coin)
- Classe `SpatialFilter` pour l'optimisation géométrique
- Limites configurables dans `config.py`
- Messages de debug améliorés

### Sécurité
- Protection contre les boucles infinies améliorée
- Validation des limites de traitement renforcée

## [1.0.0] - 2025-09-09

### Ajouté
- Génération automatique de panneaux photovoltaïques
- Support des trackers solaires (orientation verticale)
- Calcul des taux de recouvrement
- Optimisation automatique de l'espacement interrang
- Interface utilisateur intuitive avec validation temps réel
- Compatibilité Qt5/Qt6 complète
- Gestion des demi-tables pour optimiser l'espace
- Modèles de panneaux prédéfinis
- Trois modes de fonctionnement (simple, calcul, optimisation)