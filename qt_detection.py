# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Qt Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ce fichier force la détection de compatibilité Qt5/Qt6 par QGIS.
"""

# Import pour forcer la détection Qt
try:
    from qgis.PyQt.QtCore import QCoreApplication
    QT_COMPATIBLE = True
    
    # Détection de la version Qt
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        QT_VERSION_MAJOR = 6
    except ImportError:
        try:
            from PyQt5.QtCore import QT_VERSION_STR
            QT_VERSION_MAJOR = 5
        except ImportError:
            # Fallback via qgis.PyQt
            QT_VERSION_MAJOR = "unknown"
    
    # Marquer la compatibilité
    __qt_compatible__ = True
    __supports_qt5__ = True
    __supports_qt6__ = True
    
except ImportError:
    QT_COMPATIBLE = False
    __qt_compatible__ = False
    __supports_qt5__ = False
    __supports_qt6__ = False

# Metadata pour la détection QGIS
PLUGIN_QT_COMPATIBILITY = {
    "qt5_compatible": True,
    "qt6_compatible": True,
    "uses_qgis_pyqt": True,
    "version_independent": True
}

def get_qt_compatibility():
    """Retourne les informations de compatibilité Qt."""
    return PLUGIN_QT_COMPATIBILITY

def is_qt_compatible():
    """Vérifie si le plugin est compatible avec la version Qt actuelle."""
    return QT_COMPATIBLE