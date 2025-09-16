# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Qt Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ce fichier gère toutes les incompatibilités Qt5/Qt6 de manière centralisée.
"""

# Import pour forcer la détection Qt
try:
    from qgis.core import QgsPalLayerSettings
    QT_COMPATIBLE = True
    
    # Variables globales pour les constantes
    LABEL_PLACEMENT_OVER_POINT = None
    LABEL_PLACEMENT_AROUND_POINT = None
    LABEL_PLACEMENT_LINE = None
    LABEL_ENUM_AVAILABLE = False
    
    # Détection de la version Qt et export des constantes compatibles
    try:
        from PyQt6.QtCore import QT_VERSION_STR, Qt
        QT_VERSION_MAJOR = 6
        print(f"SolarPanelGenerator: Qt6 détecté ({QT_VERSION_STR})")
        
        # Qt6 - constantes dans des sous-modules
        WINDOW_MODAL = Qt.WindowModality.WindowModal
        ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
                
        # Test 1: Nouvelle API Qt6 avec QgsPalLayerSettings.Placement
        try:
            if hasattr(QgsPalLayerSettings, 'Placement'):
                # API Qt6 moderne
                LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.Placement.OverPoint
                LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.Placement.AroundPoint
                LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Placement.Line
                LABEL_ENUM_AVAILABLE = True
                
        except AttributeError:
            # Test 2: API Qt6 avec LabelPlacement
            try:
                if hasattr(QgsPalLayerSettings, 'LabelPlacement'):
                    # Enum LabelPlacement existe
                    enum_class = QgsPalLayerSettings.LabelPlacement
                    LABEL_PLACEMENT_OVER_POINT = enum_class.OverPoint
                    LABEL_PLACEMENT_AROUND_POINT = enum_class.AroundPoint
                    LABEL_PLACEMENT_LINE = enum_class.Line
                    LABEL_ENUM_AVAILABLE = True
                    
            except AttributeError:
                # Test 3: Constantes directes (fallback Qt6)
                try:
                    # Tester si les constantes directes existent
                    test_val = QgsPalLayerSettings.OverPoint
                    
                    # Si pas d'exception, utiliser les constantes directes
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.OverPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint  
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                    LABEL_ENUM_AVAILABLE = True
                    
                except AttributeError:
                    LABEL_ENUM_AVAILABLE = False
        
    except ImportError:
        try:
            from PyQt5.QtCore import QT_VERSION_STR, Qt
            QT_VERSION_MAJOR = 5
            print(f"SolarPanelGenerator: Qt5 détecté ({QT_VERSION_STR})")
            
            # Qt5 - constantes directes
            WINDOW_MODAL = Qt.WindowModal
            ALIGN_CENTER = Qt.AlignCenter
            
            # Constantes QGIS Qt5 - utiliser l'approche la plus compatible
            try:
                # Test direct des constantes Qt5
                LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.OverPoint
                LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                LABEL_ENUM_AVAILABLE = True
                
            except AttributeError:
                # Fallback Qt5 avec AroundPoint pour OverPoint
                try:
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                    LABEL_ENUM_AVAILABLE = True
                    
                except AttributeError:
                    LABEL_ENUM_AVAILABLE = False
            
        except ImportError:
            # Fallback complet via qgis.PyQt
            try:
                from qgis.PyQt.QtCore import Qt
                QT_VERSION_MAJOR = "unknown"
                print("SolarPanelGenerator: Version Qt inconnue, utilisation qgis.PyQt")
                
                # Constantes Qt basiques
                WINDOW_MODAL = Qt.WindowModal if hasattr(Qt, 'WindowModal') else 1
                ALIGN_CENTER = Qt.AlignCenter if hasattr(Qt, 'AlignCenter') else 0x0084
                
                # Liste tous les attributs disponibles pour diagnostic
                available_attrs = [attr for attr in dir(QgsPalLayerSettings) 
                                 if 'Point' in attr or 'Placement' in attr]
                
                # Test par ordre de priorité
                test_order = [
                    ('Placement.OverPoint', lambda: QgsPalLayerSettings.Placement.OverPoint),
                    ('LabelPlacement.OverPoint', lambda: QgsPalLayerSettings.LabelPlacement.OverPoint),
                    ('OverPoint', lambda: QgsPalLayerSettings.OverPoint),
                    ('AroundPoint', lambda: QgsPalLayerSettings.AroundPoint),
                ]
                
                for name, getter in test_order:
                    try:
                        val = getter()
                        LABEL_PLACEMENT_OVER_POINT = val
                        
                        # Trouver les autres constantes de la même famille
                        if 'Placement.' in name:
                            LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.Placement.AroundPoint
                            LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Placement.Line
                        elif 'LabelPlacement.' in name:
                            LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.LabelPlacement.AroundPoint
                            LABEL_PLACEMENT_LINE = QgsPalLayerSettings.LabelPlacement.Line
                        else:
                            LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                            LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                        
                        LABEL_ENUM_AVAILABLE = True
                        break
                        
                    except AttributeError:
                        continue
                    
            except Exception as e:
                QT_VERSION_MAJOR = "error"
                WINDOW_MODAL = 1
                ALIGN_CENTER = 0x0084
                LABEL_ENUM_AVAILABLE = False
    
    # Marque la compatibilité
    __qt_compatible__ = True
    __supports_qt5__ = True
    __supports_qt6__ = True
    
except ImportError as e:
    QT_COMPATIBLE = False
    __qt_compatible__ = False
    __supports_qt5__ = False
    __supports_qt6__ = False
    QT_VERSION_MAJOR = "error"
    
    # Valeurs par défaut en cas d'erreur
    WINDOW_MODAL = 1
    ALIGN_CENTER = 0x0084
    LABEL_PLACEMENT_OVER_POINT = None
    LABEL_PLACEMENT_AROUND_POINT = None
    LABEL_PLACEMENT_LINE = None
    LABEL_ENUM_AVAILABLE = False

# Dictionnaire des constantes pour accès facile
QT_CONSTANTS = {
    'window_modal': WINDOW_MODAL,
    'align_center': ALIGN_CENTER,
    'label_over_point': LABEL_PLACEMENT_OVER_POINT,
    'label_around_point': LABEL_PLACEMENT_AROUND_POINT,
    'label_line': LABEL_PLACEMENT_LINE,
    'label_enum_available': LABEL_ENUM_AVAILABLE
}

# Metadata pour la détection QGIS
PLUGIN_QT_COMPATIBILITY = {
    "qt5_compatible": True,
    "qt6_compatible": True,
    "uses_qgis_pyqt": True,
    "version_independent": True,
    "qt_version": QT_VERSION_MAJOR,
    "label_enum_available": LABEL_ENUM_AVAILABLE
}

def get_qt_compatibility():
    """Retourne les informations de compatibilité Qt."""
    return PLUGIN_QT_COMPATIBILITY

def is_qt_compatible():
    """Vérifie si le plugin est compatible avec la version Qt actuelle."""
    return QT_COMPATIBLE

def get_qt_version():
    """Retourne la version Qt détectée."""
    return QT_VERSION_MAJOR

def are_label_enums_available():
    """Vérifie si les énumérations de labels sont disponibles."""
    return LABEL_ENUM_AVAILABLE

# Fonctions d'accès aux constantes
def get_window_modal():
    """Retourne WindowModal compatible Qt5/Qt6."""
    return WINDOW_MODAL

def get_align_center():
    """Retourne AlignCenter compatible Qt5/Qt6."""
    return ALIGN_CENTER

def get_label_placement_over_point():
    """
    Retourne LabelPlacement.OverPoint compatible Qt5/Qt6.
    CRITIQUE: Retourne None si aucune énumération valide n'est disponible.
    """
    return LABEL_PLACEMENT_OVER_POINT

def get_label_placement_around_point():
    """Retourne LabelPlacement.AroundPoint compatible Qt5/Qt6."""
    return LABEL_PLACEMENT_AROUND_POINT

def get_label_placement_line():
    """Retourne LabelPlacement.Line compatible Qt5/Qt6."""
    return LABEL_PLACEMENT_LINE

def get_qt_constant(name):
    """
    Accès générique aux constantes Qt.
    
    Args:
        name (str): Nom de la constante ('window_modal', 'align_center', etc.)
        
    Returns:
        Valeur de la constante ou None si non trouvée
    """
    return QT_CONSTANTS.get(name, None)

def test_label_placement():
    """
    Teste les placements d'étiquettes disponibles avec diagnostic complet.
    
    Returns:
        bool: True si le test réussit
    """
    
    if not LABEL_ENUM_AVAILABLE:
        return False
        
    if LABEL_PLACEMENT_OVER_POINT is None:
        return False
    
    try:
        # Test d'instanciation
        settings = QgsPalLayerSettings()
        
        # Test d'assignation
        settings.placement = LABEL_PLACEMENT_OVER_POINT
                    
        return True
        
    except Exception as e:
        return False
