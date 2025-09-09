# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Main Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import os

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.utils import iface as qgis_iface

from .config import Config
from .ui.panel_dialog import SolarPanelGeneratorDialog


class SolarPanelGeneratorPlugin:
    """
    Classe principale du plugin pour SolarPanelGenerator.
    Gère l'initialisation du plugin, la configuration de l'interface graphique et le nettoyage.
    """
    
    def __init__(self, iface):
        """
        Initialisation du plugin.
        
        Args:
            iface: QGIS interface instance
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        self.action = None
        self.dialog = None
        self.translator = None
        
        self.plugin_name = "SolarPanelGenerator"
        self.plugin_version = "1.0"
        
        print(f"SolarPanelGenerator chargé avec qgis.PyQt (version-independent)")
        
    def initGui(self):
        """
        Crée les entrées de menu et les icônes de la barre d'outils.
        """
        self._create_action()
        self._add_to_interface()
        
    def unload(self):
        """
        Supprime l'élément de menu et l'icône du plugin.
        """
        if self.action:
            self.iface.removePluginMenu("SolarPanelGenerator", self.action)
            self.iface.removeToolBarIcon(self.action)
            
        if self.dialog:
            self.dialog.close()
            self.dialog = None
            
    def run(self):
        """
        Méthode d'exécution qui effectue tout le travail réel.
        """
        if not self.dialog:
            self.dialog = SolarPanelGeneratorDialog(self.iface)
        else:
            self.dialog.populate_layer_combobox()
            
        self.dialog.show()
        
    def _create_action(self):
        """
        Crée l'action pour le plugin.
        """
        icon_path = os.path.join(self.plugin_dir, 'icons', 'solar-energy.svg')
        
        self.action = QAction(
            QIcon(icon_path), 
            "SolarPanelGenerator", 
            self.iface.mainWindow()
        )
        
        tooltip_text = Config.get_tooltip_text()        
        self.action.setToolTip(tooltip_text)
        
        self.action.triggered.connect(self.run)
        
    def _add_to_interface(self):
        """
        Ajoute l'action à l'interface QGIS.
        """
        if self.action:
            self.iface.addPluginToMenu("SolarPanelGenerator", self.action)
            self.iface.addToolBarIcon(self.action)
            
    def tr(self, message):
        """
        Gère la traduction d'une chaîne à l'aide de l'API de traduction Qt.
        
        Args:
            message (str): String for translation
            
        Returns:
            str: Translated string
        """
        return QCoreApplication.translate(self.__class__.__name__, message)