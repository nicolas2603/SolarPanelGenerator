# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Parameter Validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

from ..config import Config


class ValidationError(Exception):
    """Exception levée lors d'erreurs de validation."""
    pass


class ParameterValidator:
    """
    Validateur de paramètres d'entrée avec messages d'erreur détaillés.
    """
    
    @staticmethod
    def validate_panel_dimensions(length, width):
        """
        Valide les dimensions des panneaux.
        
        Args:
            length (float): Longueur du panneau
            width (float): Largeur du panneau
            
        Raises:
            ValidationError: Si les dimensions sont invalides
        """
        # Vérifie que ce sont des nombres
        try:
            length = float(length)
            width = float(width)
        except (ValueError, TypeError):
            raise ValidationError("Les dimensions doivent être des nombres valides.")
        
        # Vérifie les limites minimales
        if length <= 0:
            raise ValidationError(f"La longueur doit être positive (reçu: {length})")
        
        if width <= 0:
            raise ValidationError(f"La largeur doit être positive (reçu: {width})")
        
        # Vérifie les limites maximales
        if length < Config.MIN_PANEL_SIZE:
            raise ValidationError(
                f"La longueur est trop petite (min: {Config.MIN_PANEL_SIZE}m, reçu: {length}m)"
            )
        
        if width < Config.MIN_PANEL_SIZE:
            raise ValidationError(
                f"La largeur est trop petite (min: {Config.MIN_PANEL_SIZE}m, reçu: {width}m)"
            )
        
        if length > Config.MAX_PANEL_SIZE:
            raise ValidationError(
                f"La longueur est trop grande (max: {Config.MAX_PANEL_SIZE}m, reçu: {length}m)"
            )
        
        if width > Config.MAX_PANEL_SIZE:
            raise ValidationError(
                f"La largeur est trop grande (max: {Config.MAX_PANEL_SIZE}m, reçu: {width}m)"
            )
        
        # Vérifications de cohérence
        if length < width and length < 1.0:
            pass
    
    @staticmethod
    def validate_spacings(h_spacing, v_spacing):
        """
        Valide les espacements horizontaux et verticaux.
        
        Args:
            h_spacing (float): Espacement horizontal
            v_spacing (float): Espacement vertical
            
        Raises:
            ValidationError: Si les espacements sont invalides
        """
        # Vérifie que ce sont des nombres
        try:
            h_spacing = float(h_spacing)
            v_spacing = float(v_spacing)
        except (ValueError, TypeError):
            raise ValidationError("Les espacements doivent être des nombres valides.")
        
        # Espacement horizontal
        if h_spacing < Config.MIN_SPACING:
            raise ValidationError(
                f"L'espacement horizontal doit être ≥ {Config.MIN_SPACING}m (reçu: {h_spacing}m)"
            )
        
        if h_spacing > Config.MAX_H_SPACING:
            raise ValidationError(
                f"L'espacement horizontal est trop grand (max: {Config.MAX_H_SPACING}m, reçu: {h_spacing}m)"
            )
        
        # Espacement vertical
        if v_spacing < Config.MIN_SPACING:
            raise ValidationError(
                f"L'espacement vertical doit être ≥ {Config.MIN_SPACING}m (reçu: {v_spacing}m)"
            )
        
        if v_spacing > Config.MAX_V_SPACING:
            raise ValidationError(
                f"L'espacement vertical est trop grand (max: {Config.MAX_V_SPACING}m, reçu: {v_spacing}m)"
            )
    
    @staticmethod
    def validate_edge_margin(edge_margin):
        """
        Valide la marge de sécurité.
        
        Args:
            edge_margin (float): Marge de sécurité
            
        Raises:
            ValidationError: Si la marge est invalide
        """
        try:
            edge_margin = float(edge_margin)
        except (ValueError, TypeError):
            raise ValidationError("La marge de sécurité doit être un nombre valide.")
        
        if edge_margin < Config.MIN_EDGE_MARGIN:
            raise ValidationError(
                f"La marge de sécurité doit être ≥ {Config.MIN_EDGE_MARGIN}m (reçu: {edge_margin}m)"
            )
        
        if edge_margin > Config.MAX_EDGE_MARGIN:
            raise ValidationError(
                f"La marge de sécurité est trop grande (max: {Config.MAX_EDGE_MARGIN}m, reçu: {edge_margin}m)"
            )
    
    @staticmethod
    def validate_coverage_percentage(percentage_str):
        """
        Valide un pourcentage de recouvrement.
        
        Args:
            percentage_str (str): Chaîne de pourcentage (ex: "50%")
            
        Returns:
            float: Valeur numérique validée
            
        Raises:
            ValidationError: Si le pourcentage est invalide
        """
        if not isinstance(percentage_str, str):
            raise ValidationError("Le pourcentage doit être une chaîne de caractères.")
        
        # Enlève le symbole %
        try:
            if percentage_str.endswith('%'):
                value_str = percentage_str[:-1]
            else:
                value_str = percentage_str
            
            value = float(value_str)
        except ValueError:
            raise ValidationError(f"Pourcentage invalide: '{percentage_str}'")
        
        if value < 0:
            raise ValidationError(f"Le pourcentage ne peut pas être négatif (reçu: {value}%)")
        
        if value > 100:
            raise ValidationError(f"Le pourcentage ne peut pas dépasser 100% (reçu: {value}%)")
        
        return value
    
    @staticmethod
    def validate_layer_selection(layer_name, available_layers):
        """
        Valide la sélection de couche.
        
        Args:
            layer_name (str): Nom de la couche sélectionnée
            available_layers (list): Liste des couches disponibles
            
        Raises:
            ValidationError: Si la sélection est invalide
        """
        if not layer_name:
            raise ValidationError("Veuillez sélectionner une couche.")
        
        if layer_name not in [layer.name() for layer in available_layers]:
            raise ValidationError(f"La couche '{layer_name}' n'est plus disponible.")
        
        # Vérifie que la couche sélectionnée est bien une couche de polygones
        selected_layer = None
        for layer in available_layers:
            if layer.name() == layer_name:
                selected_layer = layer
                break
        
        if not selected_layer:
            raise ValidationError(f"Impossible de trouver la couche '{layer_name}'.")
        
        from qgis.core import QgsWkbTypes
        if selected_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValidationError(f"La couche '{layer_name}' doit contenir des polygones.")
    
    @staticmethod
    def validate_panel_fit(length, width, polygon_area):
        """
        Vérifie si les panneaux peuvent théoriquement tenir dans le polygone.
        
        Args:
            length (float): Longueur du panneau
            width (float): Largeur du panneau
            polygon_area (float): Aire du polygone en m²
            
        Raises:
            ValidationError: Si les panneaux sont manifestement trop grands
        """
        panel_area = length * width
        
        # Vérifie que le panneau n'est pas plus grand que le polygone
        if panel_area > polygon_area:
            raise ValidationError(
                f"Le panneau ({length}×{width}m = {panel_area:.1f}m²) est plus grand que "
                f"la zone ({polygon_area:.1f}m²)."
            )
        
        # Avertissement si le panneau occupe plus de 50% de la zone
        if panel_area > polygon_area * 0.5:
            pass
    
    @staticmethod
    def validate_all_parameters(params):
        """
        Validation complète de tous les paramètres.
        
        Args:
            params (dict): Dictionnaire des paramètres
            
        Returns:
            dict: Paramètres validés et normalisés
            
        Raises:
            ValidationError: Si un paramètre est invalide
        """
        validated = {}
        
        # Valide les dimensions des panneaux
        ParameterValidator.validate_panel_dimensions(
            params.get('length'), params.get('width')
        )
        validated['length'] = float(params['length'])
        validated['width'] = float(params['width'])
        
        # Valide les espacements
        ParameterValidator.validate_spacings(
            params.get('h_spacing'), params.get('v_spacing')
        )
        validated['h_spacing'] = float(params['h_spacing'])
        v_spacing_value = params.get('v_spacing', '').strip()
        if not v_spacing_value:
            raise ValidationError("L'espacement vertical est requis")
        validated['v_spacing'] = float(v_spacing_value)
        
        # Valide la marge de sécurité
        ParameterValidator.validate_edge_margin(params.get('edge_margin'))
        validated['edge_margin'] = float(params['edge_margin'])
        
        # Valide le pourcentage de recouvrement si fourni
        if params.get('recouvrement_text'):
            validated['recouvrement_max'] = ParameterValidator.validate_coverage_percentage(
                params['recouvrement_text']
            )
        else:
            validated['recouvrement_max'] = None
        
        # Copie les autres paramètres
        for key in ['tracker', 'allow_half', 'calculate_coverage', 'selection_only', 'layer_name']:
            if key in params:
                validated[key] = params[key]
        
        # Calcule l'orientation
        validated['orientation'] = (
            Config.ORIENTATION_VERTICAL if validated.get('tracker', False) 
            else Config.ORIENTATION_HORIZONTAL
        )
        
        # Force allow_half à False en mode tracker
        if validated.get('tracker', False):
            validated['allow_half'] = False
        
        return validated
    
    @staticmethod
    def validate_geometric_consistency(params):
        """
        Vérifie la cohérence géométrique des paramètres.
        
        Args:
            params (dict): Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres sont géométriquement incohérents
        """
        length = params['length']
        width = params['width']
        h_spacing = params['h_spacing']
        v_spacing = params['v_spacing']
        edge_margin = params['edge_margin']
        
        # Vérifie que les espacements ne sont pas disproportionnés
        min_panel_dim = min(length, width)
        max_spacing = max(h_spacing, v_spacing)
        
        if max_spacing > min_panel_dim * 2:
            raise ValidationError(
                f"L'espacement maximum ({max_spacing:.1f}m) est trop grand par rapport "
                f"à la plus petite dimension du panneau ({min_panel_dim:.1f}m). "
                f"Cela pourrait créer des layouts inefficaces."
            )
        
        # Vérifie que la marge n'est pas excessive
        max_panel_dim = max(length, width)
        if edge_margin > max_panel_dim * 3:
            raise ValidationError(
                f"La marge de sécurité ({edge_margin:.1f}m) est très grande par rapport "
                f"aux dimensions du panneau (max: {max_panel_dim:.1f}m). "
                f"Cela pourrait empêcher la génération de panneaux."
            )


class ParameterNormalizer:
    """
    Normalise et corrige automatiquement certains paramètres.
    """
    
    @staticmethod
    def normalize_small_values(value, min_threshold=0.001):
        """
        Normalise les très petites valeurs vers zéro.
        
        Args:
            value (float): Valeur à normaliser
            min_threshold (float): Seuil minimum
            
        Returns:
            float: Valeur normalisée
        """
        if abs(value) < min_threshold:
            return 0.0
        return value
    
    @staticmethod
    def round_to_precision(value, precision=3):
        """
        Arrondit une valeur à la précision donnée.
        
        Args:
            value (float): Valeur à arrondir
            precision (int): Nombre de décimales
            
        Returns:
            float: Valeur arrondie
        """
        return round(float(value), precision)
    
    @staticmethod
    def normalize_parameters(params):
        """
        Normalise tous les paramètres numériques.
        
        Args:
            params (dict): Paramètres à normaliser
            
        Returns:
            dict: Paramètres normalisés
        """
        normalized = params.copy()
        
        # Normalise les valeurs numériques
        for key in ['length', 'width', 'h_spacing', 'v_spacing', 'edge_margin']:
            if key in normalized:
                value = normalized[key]
                value = ParameterNormalizer.normalize_small_values(value)
                value = ParameterNormalizer.round_to_precision(value)
                normalized[key] = value
        
        return normalized