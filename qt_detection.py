# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Qt Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ce fichier gère toutes les incompatibilités Qt5/Qt6 de manière centralisée.
"""

# Import pour forcer la détection Qt
try:
    from qgis.PyQt.QtCore import QCoreApplication, Qt
    from qgis.core import QgsPalLayerSettings
    QT_COMPATIBLE = True
    
    # Détection de la version Qt et export des constantes compatibles
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        QT_VERSION_MAJOR = 6
        print(f"SolarPanelGenerator: Qt6 détecté ({QT_VERSION_STR})")
        
        # Qt6 - constantes dans des sous-modules
        WINDOW_MODAL = Qt.WindowModality.WindowModal
        ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
        
        # CORRECTION CRITIQUE: Constantes QGIS Qt6 - Placement d'étiquettes
        try:
            # QGIS 3.x Qt6: Utiliser LabelPlacement, pas LabelPredefinedPointPosition
            if hasattr(QgsPalLayerSettings, 'LabelPlacement'):
                # Nouvelle API Qt6
                LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.LabelPlacement.OverPoint
                LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.LabelPlacement.AroundPoint
                LABEL_PLACEMENT_LINE = QgsPalLayerSettings.LabelPlacement.Line
                LABEL_ENUM_AVAILABLE = True
                print("✅ Qt6: Énumérations LabelPlacement trouvées")
            else:
                # Fallback vers les constantes directes
                LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.OverPoint
                LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                LABEL_ENUM_AVAILABLE = True
                print("✅ Qt6: Énumérations directes trouvées")
        except AttributeError:
            # Aucune énumération disponible
            LABEL_PLACEMENT_OVER_POINT = None
            LABEL_PLACEMENT_AROUND_POINT = None
            LABEL_PLACEMENT_LINE = None
            LABEL_ENUM_AVAILABLE = False
            print("❌ Qt6: Aucune énumération de placement trouvée")
            
    except (ImportError, AttributeError):
        try:
            from PyQt5.QtCore import QT_VERSION_STR
            QT_VERSION_MAJOR = 5
            print(f"SolarPanelGenerator: Qt5 détecté ({QT_VERSION_STR})")
            
            # Qt5 - constantes directes
            WINDOW_MODAL = Qt.WindowModal
            ALIGN_CENTER = Qt.AlignCenter
            
            # Constantes QGIS Qt5 - tester le type des énumérations
            try:
                # Vérifier le type de AroundPoint
                test_around = QgsPalLayerSettings.AroundPoint
                if 'LabelPlacement' in str(type(test_around)):
                    # Utiliser AroundPoint si c'est du bon type
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                    print("✅ Qt5: Utilisation de AroundPoint (LabelPlacement)")
                else:
                    # Utiliser les constantes directes
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.OverPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                    print("✅ Qt5: Énumérations directes utilisées")
                LABEL_ENUM_AVAILABLE = True
            except AttributeError:
                LABEL_PLACEMENT_OVER_POINT = None
                LABEL_PLACEMENT_AROUND_POINT = None
                LABEL_PLACEMENT_LINE = None
                LABEL_ENUM_AVAILABLE = False
                print("❌ Qt5: Aucune énumération de placement trouvée")
            
        except (ImportError, AttributeError):
            # Fallback via qgis.PyQt
            QT_VERSION_MAJOR = "unknown"
            print("SolarPanelGenerator: Version Qt inconnue")
            
            # Essayer de charger les constantes via qgis.PyQt
            try:
                WINDOW_MODAL = Qt.WindowModal
                ALIGN_CENTER = Qt.AlignCenter
                
                # Test des énumérations de placement
                if hasattr(QgsPalLayerSettings, 'LabelPlacement'):
                    # Nouvelle API
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.LabelPlacement.OverPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.LabelPlacement.AroundPoint
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.LabelPlacement.Line
                    LABEL_ENUM_AVAILABLE = True
                    print("✅ Unknown Qt: Énumérations LabelPlacement trouvées")
                else:
                    # API ancienne
                    LABEL_PLACEMENT_OVER_POINT = QgsPalLayerSettings.OverPoint
                    LABEL_PLACEMENT_AROUND_POINT = QgsPalLayerSettings.AroundPoint
                    LABEL_PLACEMENT_LINE = QgsPalLayerSettings.Line
                    LABEL_ENUM_AVAILABLE = True
                    print("✅ Unknown Qt: Énumérations directes trouvées")
            except AttributeError:
                # Valeurs par défaut pour Qt seulement
                WINDOW_MODAL = 1
                ALIGN_CENTER = 0x0084
                LABEL_PLACEMENT_OVER_POINT = None
                LABEL_PLACEMENT_AROUND_POINT = None
                LABEL_PLACEMENT_LINE = None
                LABEL_ENUM_AVAILABLE = False
                print("❌ Unknown Qt: Aucune énumération trouvée, utilisation des valeurs par défaut")
    
    # Marquer la compatibilité
    __qt_compatible__ = True
    __supports_qt5__ = True
    __supports_qt6__ = True
    
except ImportError:
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
    print("❌ Import Qt échoué complètement")

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
    return LABEL_PLACEMENT_OVER_POINT  # Peut être None

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

def log_qt_info():
    """Affiche les informations de compatibilité Qt."""
    print(f"=== SolarPanelGenerator Qt Detection ===")
    print(f"Qt Compatible: {QT_COMPATIBLE}")
    print(f"Qt Version: {QT_VERSION_MAJOR}")
    print(f"Constants loaded: {len(QT_CONSTANTS)}")
    print(f"WindowModal: {WINDOW_MODAL}")
    print(f"LabelOverPoint: {LABEL_PLACEMENT_OVER_POINT}")
    print(f"Label Enums Available: {LABEL_ENUM_AVAILABLE}")
    
    # NOUVEAU: Test détaillé des énumérations
    if LABEL_ENUM_AVAILABLE and LABEL_PLACEMENT_OVER_POINT is not None:
        print(f"LabelOverPoint Type: {type(LABEL_PLACEMENT_OVER_POINT)}")
        print(f"LabelOverPoint Value: {LABEL_PLACEMENT_OVER_POINT}")
        
        # Vérification de la compatibilité
        try:
            # Test simple d'assignation
            test_settings = QgsPalLayerSettings()
            test_settings.placement = LABEL_PLACEMENT_OVER_POINT
            print("✅ Assignation de placement réussie")
        except Exception as e:
            print(f"❌ Erreur d'assignation: {e}")
    
    print(f"========================================")

def test_label_placement():
    """Teste les placements d'étiquettes disponibles."""
    print("=== Test Label Placement ===")
    
    if LABEL_ENUM_AVAILABLE:
        try:
            # Tester l'attribution
            settings = QgsPalLayerSettings()
            settings.placement = LABEL_PLACEMENT_OVER_POINT
            print(f"✅ Label placement fonctionne: {LABEL_PLACEMENT_OVER_POINT}")
            print(f"   Type: {type(LABEL_PLACEMENT_OVER_POINT)}")
            return True
        except Exception as e:
            print(f"❌ Label placement échoue: {e}")
            print(f"   Type attendu vs reçu: {type(LABEL_PLACEMENT_OVER_POINT)}")
            return False
    else:
        print("❌ Aucune énumération de label disponible")
        return False

def debug_label_enums():
    """Debug détaillé des énumérations disponibles."""
    print("=== Debug Label Enums ===")
    
    # Test de toutes les possibilités
    try:
        print("Test 1: QgsPalLayerSettings.LabelPlacement.OverPoint")
        val1 = QgsPalLayerSettings.LabelPlacement.OverPoint
        print(f"   Valeur: {val1}, Type: {type(val1)}")
    except:
        print("   ❌ Non disponible")
    
    try:
        print("Test 2: QgsPalLayerSettings.OverPoint")
        val2 = QgsPalLayerSettings.OverPoint
        print(f"   Valeur: {val2}, Type: {type(val2)}")
    except:
        print("   ❌ Non disponible")
        
    # Lister tous les attributs disponibles
    print("Attributs QgsPalLayerSettings:")
    for attr in dir(QgsPalLayerSettings):
        if 'Point' in attr or 'Placement' in attr:
            try:
                val = getattr(QgsPalLayerSettings, attr)
                print(f"   {attr}: {val} ({type(val)})")
            except:
                print(f"   {attr}: ❌ Erreur d'accès")
    
    print("=========================")