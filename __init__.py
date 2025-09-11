# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin for QGIS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin QGIS permettant de générer des plans d'implantation de panneaux solaires avec prise en compte ou non du taux de couverture.
Compatible avec les versions Qt5 et Qt6 de QGIS.

Author: Nicolas Lieutenant
Email: nicolas2603@gmail.com
Copyright (C) 2025 Nicolas Lieutenant
"""

from .qt_detection import is_qt_compatible, get_qt_compatibility

if not is_qt_compatible():
    raise ImportError("Plugin SolarPanelGenerator: Qt non compatible détecté")

def classFactory(iface):
    """
    Charge la classe SolarPanelGenerator avec informations Qt.
    
    Args:
        iface: QGIS interface instance
        
    Returns:
        SolarPanelGeneratorPlugin: Plugin instance
    """
    # Import conditionnel pour éviter les erreurs Qt
    try:
        from .solar_panel_generator import SolarPanelGeneratorPlugin
        from .qt_detection import log_qt_info, get_qt_compatibility
        
        # Log de la compatibilité Qt (optionnel)
        log_qt_info()
        
        compatibility = get_qt_compatibility()
        print(f"SolarPanelGenerator: Chargé avec Qt{compatibility.get('qt_version', 'unknown')}")
        
        return SolarPanelGeneratorPlugin(iface)
        
    except ImportError as e:
        print(f"SolarPanelGenerator: Erreur de chargement - {e}")
        raise

# Metadata de compatibilité pour QGIS
__qt5_compatible__ = True
__qt6_compatible__ = True
__version__ = "1.1"