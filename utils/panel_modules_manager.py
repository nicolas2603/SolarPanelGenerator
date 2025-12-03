# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Panel modules Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import json
import os

from ..config import Config


class PanelModulesManager:
    """
    Gestionnaire des modules de panneaux avec chargement automatique depuis JSON.
    """
    
    def __init__(self):
        self.modules = {}
        self._load_modules()
    
    def _load_modules(self):
        """Charge automatiquement les modules depuis panel_modules.json."""
        plugin_dir = os.path.dirname(os.path.dirname(__file__))
        modules_file = os.path.join(plugin_dir, "panel_models.json")
                
        if os.path.exists(modules_file):
            try:
                with open(modules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "modules" in data:
                    self.modules = data["modules"]
                else:
                    print(f"Format JSON invalide dans {modules_file}: clé 'modules' manquante")
                    
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                print(f"Erreur chargement modèles {modules_file}: {e}")
        else:
            print(f"Fichier modules non trouvé: {modules_file}")
    
    def get_module_names(self):
        """Retourne la liste des noms de modules disponibles."""
        return list(self.modules.keys())
    
    def get_module(self, model_name):
        """Retourne les détails d'un module."""
        return self.modules.get(model_name, None)
    
    def has_modules(self):
        """Vérifie si des modules sont disponibles."""
        return len(self.modules) > 0