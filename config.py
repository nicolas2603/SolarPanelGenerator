# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration centralisée.
"""


class Config:
    """
    Configuration principale du plugin.
    """
    
    # ========== MÉTADONNÉES DU PLUGIN ==========
    PLUGIN_NAME = "SolarPanelGenerator"
    PLUGIN_VERSION = "1.1-compatible"
    PLUGIN_MENU_NAME = "SolarPanelGenerator"
    
    # ========== VALEURS PAR DÉFAUT DE L'INTERFACE ==========
    DEFAULT_H_SPACING = 0.2
    DEFAULT_EDGE_MARGIN = 2.0
    
    # ========== PARAMÈTRES D'OPTIMISATION ==========
    V_SPACING_MAX = 100.0
    V_SPACING_STEP = 0.5
    OPTIMIZATION_STEPS = 5
    
    # Modes d'ancrage pour l'optimisation
    ANCHOR_MODES = ["bottom_left", "bottom_right", "top_left", "top_right"]
    
    # ========== TOLÉRANCES GÉOMÉTRIQUES ==========
    GEOMETRY_TOLERANCE = 0.1
    HOLE_DETECTION_MARGIN = 30.0
    LINE_DETECTION_TOLERANCE = 0.1
    TOLERANCE_BUFFER = 0.1
    
    # ========== TYPES DE PANNEAUX ==========
    PANEL_TYPE_FULL = "full table"
    PANEL_TYPE_HALF = "half table"
    
    # Étiquettes d'affichage
    PANEL_LABELS = {
        PANEL_TYPE_FULL: "Table entière",
        PANEL_TYPE_HALF: "Demi-table"
    }
    
    # ========== ORIENTATIONS ==========
    ORIENTATION_HORIZONTAL = 0.0
    ORIENTATION_VERTICAL = 90.0  # Mode tracker
    
    @classmethod
    def is_tracker_mode(cls, orientation):
        """Détermine si on est en mode tracker basé sur l'orientation."""
        return abs((orientation % 180.0) - cls.ORIENTATION_VERTICAL) < 1e-6
    
    # ========== VALEURS DE RECOUVREMENT ==========
    NO_OPTIMIZATION_LABEL = "Placement par défaut"
    
    # Valeurs de recouvrement pour l'optimisation
    COVERAGE_VALUES = [
        NO_OPTIMIZATION_LABEL,  # Première option par défaut
        '10%', '20%', '30%', '40%', '50%', 
        '60%', '70%', '80%', '90%', '100%'
    ]
    
    @classmethod
    def is_optimization_disabled(cls, coverage_text):
        """
        Vérifie si l'optimisation est désactivée.
        
        Args:
            coverage_text (str): Texte de la combobox de recouvrement
            
        Returns:
            bool: True si pas d'optimisation
        """
        return coverage_text == cls.NO_OPTIMIZATION_LABEL
    
    # ========== NOMS DES COUCHES ==========
    OUTPUT_PANELS_LAYER_NAME = "panneaux"
    OUTPUT_COVERAGE_LAYER_NAME = "recouvrement"
    TEMP_TRACING_LAYER_NAME = "recouvrement_temp"
    
    # ========== COULEURS ET RENDU ==========
    COLORS = {
        'full_panel': 'blue',
        'half_panel': 'cyan',
        'coverage_outline': 'red',
        'coverage_label': 'red',
        'coverage_buffer': 'white'
    }
    
    # Paramètres de rendu
    COVERAGE_OUTLINE_WIDTH = '1.0'
    COVERAGE_FILL_COLOR = '0,0,0,0'  # Transparent
    
    # Paramètres des étiquettes
    LABEL_FONT_SIZE = 10
    LABEL_BUFFER_SIZE = 1
    
    # ========== LIMITES DE VALIDATION ==========
    # Dimensions des panneaux
    MIN_PANEL_SIZE = 0.1
    MAX_PANEL_SIZE = 100.0
    
    # Espacements
    MIN_SPACING = 0.0
    MAX_H_SPACING = 50.0
    MAX_V_SPACING = 100.0
    
    # Marge de sécurité
    MIN_EDGE_MARGIN = 0.0
    MAX_EDGE_MARGIN = 50.0
    
    # ========== PARAMÈTRES DE PERFORMANCE ==========
    # Nombre de segments pour les opérations buffer
    BUFFER_SEGMENTS = 5
    BUFFER_SEGMENTS_PRECISE = 50
    
    # Limite pour les grosses géométries
    LARGE_DATASET_THRESHOLD = 1000
    
    # ========== MESSAGES D'INTERFACE ==========
    MESSAGES = {
        'progress_title': "Génération des panneaux",
        'progress_label': "Calcul en cours...",
        'progress_cancel': "Annuler",
        'progress_interrupted': "Traitement interrompu par l'utilisateur.",
        
        'error_invalid_numbers': "Veuillez entrer des nombres valides.",
        'error_invalid_layer': "Sélectionnez une couche de polygones valide.",
        'error_no_features': "Aucune entité trouvée dans la couche source.",
        'error_layer_not_found': "Couche 'panneaux' introuvable.",
        'error_no_coverage': "Impossible de générer un recouvrement.",
        'error_no_polygon_layers': "Aucune couche de polygones disponible dans le projet.",
        
        'info_optimization_failed': "Îlot {ilot}: aucun v_spacing < {max_rate:.1f}% même avec décalages. Meilleur taux = {best_rate:.1f}% (v_spacing={v_spacing}).",
        'info_coverage_calculated': "Recouvrement calculé avec v_spacing = {v_spacing}m",
        'info_optimization_found': "Optimisation réussie: v_spacing = {v_spacing}m pour {target_rate}% de recouvrement",
    }
    
    # ========== PARAMÈTRES DE FICHIERS ==========
    # Chemins relatifs
    ICON_PATH = "icons/solar-energy.svg"
    UI_FORM_PATH = "forms/panel_dialog.ui"
    
    # ========== PARAMÈTRES QGIS ==========
    # Clés pour QSettings
    SETTINGS_PREFIX = "SolarPanelGenerator"
    SETTINGS_LAST_LAYER = f"{SETTINGS_PREFIX}/last_layer"
    
    # CRS par défaut pour les couches temporaires
    DEFAULT_CRS = "EPSG:2154"  # Lambert 93 France
    
    # ========== PARAMÈTRES DE DEBUG ==========
    DEBUG_MODE = False
    DEBUG_CREATE_TEMP_LAYERS = False
    DEBUG_ADD_SPLIT_LAYERS = False
    
    # ========== PARAMÈTRES DE SÉCURITÉ POUR LE TRAÇAGE ==========
    # Limites de sécurité pour éviter les boucles infinies
    TRACING_MAX_VISITS_PER_PANEL_COIN = 3
    TRACING_MAX_FORCED_VISITS_PER_PANEL = 5
    TRACING_MAX_EXECUTION_TIME = 300
    
    # Configuration de debug pour le traçage
    TRACING_DEBUG_MODE = False
    TRACING_LOG_DECISIONS = False
    
    # ========== MÉTHODES UTILITAIRES ==========
    
    @classmethod
    def get_tooltip_text(cls):
        """
        Texte de tooltip pour l'action du plugin.
        
        Returns:
            str: Tooltip HTML formaté
        """
        return (
            f"<b>{cls.PLUGIN_NAME}</b><br/>"
            "Génère une couverture de panneaux photovoltaïques "
            "dans une surface définie.<br/>"
            "Fonctionnalités :<br/>"
            "• Calcul de couverture avec interrang fixe<br/>"
            "• Optimisation automatique de l'interrang en cas de sélection d'un taux de couverture<br/>"
            "• Support des trackers<br/>"
            "• Gestion des demi-tables"
        )
    
    @classmethod
    def parse_coverage_percentage(cls, percentage_str):
        """
        Parse une chaîne de pourcentage en float.
        
        Args:
            percentage_str (str): Chaîne comme "50%" ou "Non optimisé"
            
        Returns:
            float or None: Valeur numérique ou None si pas d'optimisation
        """
        if cls.is_optimization_disabled(percentage_str):
            return None
            
        try:
            return float(percentage_str.replace("%", ""))
        except (ValueError, AttributeError):
            return None
    
    @classmethod
    def get_tolerance_x(cls, h_spacing):
        """Calculer la tolérance X pour le tracé."""
        return h_spacing + cls.TOLERANCE_BUFFER
    
    @classmethod
    def get_tolerance_y(cls, v_spacing):
        """Calculer la tolérance Y pour le tracé."""
        return v_spacing + cls.TOLERANCE_BUFFER
    
    @classmethod
    def get_tolerances(cls, h_spacing, v_spacing, orientation):
        """
        Calculer les tolérances X et Y en tenant compte de l'orientation.
        
        Args:
            h_spacing (float): Espacement horizontal
            v_spacing (float): Espacement vertical  
            orientation (float): Orientation en degrés
            
        Returns:
            tuple: (tol_x, tol_y)
        """
        tol_x = cls.get_tolerance_x(h_spacing)
        tol_y = cls.get_tolerance_y(v_spacing)
        
        if cls.is_tracker_mode(orientation):
            return tol_y, tol_x
        else:
            return tol_x, tol_y


def validate_config():
    """
    Valide la cohérence de la configuration.
    """
    if Config.V_SPACING_STEP <= 0:
        raise ValueError("V_SPACING_STEP doit être positif")
    
    if Config.V_SPACING_MAX <= 0:
        raise ValueError("V_SPACING_MAX doit être positif")
    
    if Config.MIN_PANEL_SIZE >= Config.MAX_PANEL_SIZE:
        raise ValueError("MIN_PANEL_SIZE doit être inférieur à MAX_PANEL_SIZE")
    
    # Vérifier que "Non optimisé" est bien la première valeur
    if Config.COVERAGE_VALUES[0] != Config.NO_OPTIMIZATION_LABEL:
        raise ValueError("NO_OPTIMIZATION_LABEL doit être la première valeur de COVERAGE_VALUES")


# Valider la configuration au chargement
validate_config()