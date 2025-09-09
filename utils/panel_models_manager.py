# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Panel Models Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import json
import os

from ..config import Config


class PanelModelsManager:
    """
    Gestionnaire des modèles de panneaux avec chargement automatique depuis JSON.
    """
    
    def __init__(self):
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Charge automatiquement les modèles depuis panel_models.json."""
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        models_file = os.path.join(plugin_dir, "panel_models.json")
                
        if os.path.exists(models_file):
            try:
                with open(models_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "models" in data:
                    self.models = data["models"]
                else:
                    print(f"Format JSON invalide dans {models_file}: clé 'models' manquante")
                    
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                print(f"Erreur chargement modèles {models_file}: {e}")
        else:
            print(f"Fichier modèles non trouvé: {models_file}")
    
    def get_model_names(self):
        """Retourne la liste des noms de modèles disponibles."""
        return list(self.models.keys())
    
    def get_model(self, model_name):
        """Retourne les détails d'un modèle."""
        return self.models.get(model_name, None)
    
    def has_models(self):
        """Vérifie si des modèles sont disponibles."""
        return len(self.models) > 0