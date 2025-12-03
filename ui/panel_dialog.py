# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import os
from collections import defaultdict

from qgis.PyQt.QtCore import Qt, QVariant, QSettings
from qgis.PyQt.QtWidgets import QApplication, QProgressDialog
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt import QtWidgets, uic

from qgis.core import *

from ..qt_detection import get_window_modal
from ..config import Config
from ..utils.parameter_validator import ParameterValidator, ValidationError, ParameterNormalizer
from ..utils.layer_helpers import LayerHelpers
from ..utils.geometry_helpers import GeometryHelpers
from ..utils.panel_models_manager import PanelModelsManager
from ..utils.panel_modules_manager import PanelModulesManager
from ..core.tracing_logic import TracingLogic
from ..core.coverage_logic import CoverageLogic

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "..", Config.UI_FORM_PATH)
)


class SolarPanelGeneratorDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    Interface utilisateur avec logique de validation.
    """
    
    def __init__(self, iface):
        """Initialisation de dialog."""
        super().__init__()
        self.iface = iface
        
        print(f"Panel Dialog chargé avec qgis.PyQt (version-independent)")
        
        # Initialisation UI
        self.setupUi(self)
        
        # Initialisation helpers
        self.layer_helpers = LayerHelpers()
        self.geometry_helpers = GeometryHelpers()
        self.tracing_logic = TracingLogic()
        self.coverage_logic = CoverageLogic()
        self.models_manager = PanelModelsManager()
        self.modules_manager = PanelModulesManager()
        
        # Configuration des connexions
        self.trackerCheckBox.toggled.connect(self.on_tracker_toggled)
        self.generateButton.clicked.connect(self.run)
        self.recouvrementComboBox.currentTextChanged.connect(self.on_coverage_combo_changed)
        self.coveringCheckBox.toggled.connect(self.on_covering_checkbox_toggled)
        
        # Connections pour les modèles
        self.modelsComboBox.currentTextChanged.connect(self.on_model_selected)
        self.populate_models_combobox()
        
        # Connections pour les modules
        self.modulesComboBox.currentTextChanged.connect(self.on_modules_selected)
        self.populate_modules_combobox()
        
        # Validation en temps réel
        self._setup_realtime_validation()
        
        # Remplissage de l'interface
        self.populate_layer_combobox()
        self.populate_recouvrement_combobox()
        
        # Valeurs initiales
        self.hSpacingLineEdit.setText(str(Config.DEFAULT_H_SPACING))
        self.edgeMarginLineEdit.setText(str(Config.DEFAULT_EDGE_MARGIN))
    
    def _setup_realtime_validation(self):
        """Configure la validation en temps réel des champs."""
        self.lengthLineEdit.editingFinished.connect(
            lambda: self._validate_field('length', self.lengthLineEdit)
        )
        self.widthLineEdit.editingFinished.connect(
            lambda: self._validate_field('width', self.widthLineEdit)
        )
        self.hSpacingLineEdit.editingFinished.connect(
            lambda: self._validate_field('h_spacing', self.hSpacingLineEdit)
        )
        self.vSpacingLineEdit.editingFinished.connect(
            lambda: self._validate_field('v_spacing', self.vSpacingLineEdit)
        )
        self.edgeMarginLineEdit.editingFinished.connect(
            lambda: self._validate_field('edge_margin', self.edgeMarginLineEdit)
        )
    
    def _validate_field(self, field_type, line_edit):
        """Valide un champ individuel avec feedback visuel."""
        try:
            value = line_edit.text()
            if not value.strip():
                return
            
            if field_type in ['length', 'width']:
                ParameterValidator.validate_panel_dimensions(value, value)
            elif field_type in ['h_spacing', 'v_spacing']:
                if field_type == 'h_spacing':
                    ParameterValidator.validate_spacings(value, 1.0)
                else:
                    ParameterValidator.validate_spacings(1.0, value)
            elif field_type == 'edge_margin':
                ParameterValidator.validate_edge_margin(value)
            
            line_edit.setStyleSheet("")
            line_edit.setToolTip("")
            
        except ValidationError as e:
            line_edit.setStyleSheet("QLineEdit { border: 2px solid red; }")
            line_edit.setToolTip(f"Erreur: {str(e)}")
        except Exception:
            line_edit.setStyleSheet("QLineEdit { border: 2px solid orange; }")
            line_edit.setToolTip("Veuillez entrer un nombre valide")
    
    def populate_layer_combobox(self):
        """Remplis layer combobox avec filtrage strict des couche de polygones uniquement."""
        self.layerComboBox.clear()       
        self.layerComboBox.addItem("Sélectionner une couche", None)
        
        # Récupérer UNIQUEMENT les couches de polygones
        self.available_layers = self.layer_helpers.get_polygon_layers()
        
        if not self.available_layers:
            # Aucune couche de polygones disponible
            self.layerComboBox.addItem("(Aucune couche de polygones disponible)")
            self.layerComboBox.setEnabled(False)
            self.generateButton.setEnabled(False)
            self.iface.messageBar().pushWarning(
                "Couches", Config.MESSAGES['error_no_polygon_layers']
            )
            return
        
        self.layerComboBox.insertSeparator(self.layerComboBox.count())
        
        layer_names = [layer.name() for layer in self.available_layers]
        self.layerComboBox.addItems(layer_names)
        self.layerComboBox.setEnabled(True)
        self.generateButton.setEnabled(True)
        
        self.layerComboBox.setCurrentIndex(0)
        
        # Restorer la dernière sélection
        settings = QSettings()
        last_layer = settings.value(Config.SETTINGS_LAST_LAYER, "")
        if last_layer and last_layer in layer_names:
            idx = self.layerComboBox.findText(last_layer)
            if idx >= 0:
                self.layerComboBox.setCurrentIndex(idx)

    def on_tracker_toggled(self, checked):
        """Gestion de la checkbox Tracker"""
        self.halfPanelCheckBox.setChecked(False)
        self.halfPanelCheckBox.setEnabled(not checked)

    def populate_models_combobox(self):
        """Remplis automatiquement la combobox avec les modèles du fichier JSON."""
        self.modelsComboBox.clear()
        self.modelsComboBox.addItem("Choisir un modèle ou saisir manuellement", None)
        
        if self.models_manager.has_models():
            self.modelsComboBox.insertSeparator(self.modelsComboBox.count())
            model_names = self.models_manager.get_model_names()
            for name in sorted(model_names):
                model = self.models_manager.get_model(name)
                if model:
                    display_name = f"{model.get('name', name)} ({model['length']}×{model['width']}m)"
                    self.modelsComboBox.addItem(display_name, name)

        else:
            # Aucun modèle trouvé
            self.modelsComboBox.addItem("(Aucun modèle disponible)", None)
            self.modelsComboBox.setEnabled(False)
        
        if self.models_manager.has_models():
            tooltip = (
                "Sélectionnez un modèle prédéfini pour remplir automatiquement "
                "les dimensions, ou utilisez 'Saisie manuelle'"
            )
        else:
            tooltip = (
                "Aucun modèle trouvé dans panel_models.json. "
                "Placez ce fichier à la racine du plugin pour activer les modèles prédéfinis."
            )
        
        self.modelsComboBox.setToolTip(tooltip)

    def on_model_selected(self):
        """Appelé automatiquement quand un modèle est sélectionné."""
        current_data = self.modelsComboBox.currentData()
        
        if current_data:
            # Un modèle est sélectionné
            model = self.models_manager.get_model(current_data)
            if model:
                self.lengthLineEdit.setText(str(model['length']))
                self.widthLineEdit.setText(str(model['width']))
                
                self.lengthLineEdit.setToolTip("Longueur du panneau en m")
                self.widthLineEdit.setToolTip("Largeur du panneau en m")
                
                # Calcul automatique du nombre de modules par table depuis le nom du modèle
                model_name = model.get('name', current_data)
                modules_per_table = self._extract_modules_from_model_name(model_name)
                if modules_per_table is not None:
                    self.pertableLineEdit.setText(str(modules_per_table))
                    self.pertableLineEdit.setToolTip(f"Calculé automatiquement depuis {model_name}")
    
    def _extract_modules_from_model_name(self, model_name):
        """Extrait le nombre de modules par table depuis le nom du modèle."""
        import re
        
        # Pattern pour capturer XVY (ex: 2V24, 1V27, 3V30)
        pattern = r'(\d+)V(\d+)'
        match = re.search(pattern, model_name, re.IGNORECASE)
        
        if match:
            try:
                x = int(match.group(1))
                y = int(match.group(2))
                return x * y
            except (ValueError, IndexError):
                return None
        
        return None

    def reset_model_selection(self):
        """Remet la sélection sur 'Saisie manuelle'."""
        self.modelsComboBox.setCurrentIndex(0)  # Premier item = "Saisie manuelle"

    def populate_modules_combobox(self):
        """Remplis automatiquement la combobox avec les modules du fichier JSON."""
        self.modulesComboBox.clear()
        self.modulesComboBox.addItem("Choisir un modules ou saisir manuellement", None)
        
        if self.modules_manager.has_modules():
            self.modulesComboBox.insertSeparator(self.modulesComboBox.count())
            modules_names = self.modules_manager.get_module_names()
            for name in sorted(modules_names):
                modules = self.modules_manager.get_module(name)
                if modules:
                    display_name = f"{modules.get('name', name)} ({modules['puissance']}Wc)"
                    self.modulesComboBox.addItem(display_name, name)

        else:
            # Aucun modèle trouvé
            self.modulesComboBox.addItem("(Aucun module disponible)", None)
            self.modulesComboBox.setEnabled(False)
        
        if self.modules_manager.has_modules():
            tooltip = (
                "Sélectionnez un module prédéfini pour remplir automatiquement "
                "la puissance, ou utilisez 'Saisie manuelle'"
            )
        else:
            tooltip = (
                "Aucun module trouvé dans panel_models.json. "
                "Placez ce fichier à la racine du plugin pour activer les modules prédéfinis."
            )
        
        self.modulesComboBox.setToolTip(tooltip)

    def on_modules_selected(self):
        """Appelé automatiquement quand un module est sélectionné."""
        current_data = self.modulesComboBox.currentData()
        
        if current_data:
            # Un module est sélectionné
            modules = self.modules_manager.get_module(current_data)
            if modules:
                self.puissanceLineEdit.setText(str(modules['puissance']))
                
                self.lengthLineEdit.setToolTip("Puissance du module en Wc")

    def reset_modules_selection(self):
        """Remet la sélection sur 'Saisie manuelle'."""
        self.modulesComboBox.setCurrentIndex(0)  # Premier item = "Saisie manuelle"

    def populate_recouvrement_combobox(self):
        """Remplis recouvrement combobox avec 'Placement par défaut' par défaut."""
        self.recouvrementComboBox.clear()
        self.recouvrementComboBox.addItem(Config.NO_OPTIMIZATION_LABEL)
        self.recouvrementComboBox.insertSeparator(self.recouvrementComboBox.count())
        for value in Config.COVERAGE_VALUES[1:]:
            self.recouvrementComboBox.addItem(value)
        self.recouvrementComboBox.setCurrentIndex(0)
        
        self.recouvrementComboBox.setToolTip(
            "Laisser 'Placement par défaut' pour calculer avec l'interrang saisi,\n"
            "ou sélectionner un pourcentage pour optimiser automatiquement l'interrang."
        )

    def on_coverage_combo_changed(self, text):
        """Gère les changements de la combobox de recouvrement."""
        if Config.is_optimization_disabled(text):
            # "Placement par défaut" : autorise décochage et décoche
            self.coveringCheckBox.setEnabled(True)
            self.coveringCheckBox.setChecked(False)
            self.coveringCheckBox.setToolTip("Calcule le recouvrement avec l'interrang saisi")
        else:
            # Pourcentage sélectionné : force cochage et verrouille
            self.coveringCheckBox.setChecked(True)
            self.coveringCheckBox.setEnabled(False)
            self.coveringCheckBox.setToolTip(
                f"Optimisation automatique pour {text} de recouvrement (obligatoire)"
            )

    def on_covering_checkbox_toggled(self, checked):
        """Valide les changements de la checkbox de recouvrement."""
        coverage_text = self.recouvrementComboBox.currentText()
        
        # Si un pourcentage est sélectionné, empêche le décochage
        if not Config.is_optimization_disabled(coverage_text) and not checked:
            self.coveringCheckBox.blockSignals(True)
            self.coveringCheckBox.setChecked(True)
            self.coveringCheckBox.blockSignals(False)
            
            self.iface.messageBar().pushInfo(
                "Mode optimisation", 
                f"Le calcul de recouvrement est obligatoire pour l'optimisation à {coverage_text}%"
            )

    def _get_and_validate_parameters(self):
        """Récupère et valide tous les paramètres avec nouvelle logique."""
        try:
            # Vérifie qu'on a des couches polygones
            if not self.available_layers:
                raise ValidationError("Aucune couche de polygones disponible")
            
            # Récupére les valeurs brutes
            raw_params = {
                'length': self.lengthLineEdit.text(),
                'width': self.widthLineEdit.text(),
                'h_spacing': self.hSpacingLineEdit.text(),
                'v_spacing': self.vSpacingLineEdit.text(),
                'edge_margin': self.edgeMarginLineEdit.text(),
                'tracker': self.trackerCheckBox.isChecked(),
                'allow_half': self.halfPanelCheckBox.isChecked(),
                'calculate_coverage': self.coveringCheckBox.isChecked(),
                'selection_only': self.selectionOnlyCheckBox.isChecked(),
                'layer_name': self.layerComboBox.currentText(),
                'puissance': self.puissanceLineEdit.text(),
                'modules_per_table': self.pertableLineEdit.text(),
            }

            layer_name = self.layerComboBox.currentText()
            if layer_name == "Sélectionner une couche":
                raise ValidationError("Veuillez sélectionner une couche de polygones.")
            
            coverage_text = self.recouvrementComboBox.currentText()
            if not Config.is_optimization_disabled(coverage_text):
                # Un pourcentage est sélectionné -> mode optimisation
                if not raw_params['v_spacing'].strip():
                    # v_spacing vide -> utiliser valeur par défaut pour l'optimisation
                    raw_params['v_spacing'] = '1.0'
                    self.iface.messageBar().pushInfo(
                        "Optimisation", 
                        "v_spacing vide : utilisation de 1.0m comme point de départ pour l'optimisation"
                    )
            if raw_params['calculate_coverage']:
                if Config.is_optimization_disabled(coverage_text):
                    # Mode calcul simple : utiliser v_spacing saisi
                    raw_params['optimization_mode'] = False
                    raw_params['target_coverage_rate'] = None
                else:
                    # Mode optimisation : chercher v_spacing pour atteindre le taux
                    raw_params['optimization_mode'] = True
                    target_rate = Config.parse_coverage_percentage(coverage_text)
                    if target_rate is None:
                        raise ValidationError(f"Taux de recouvrement invalide: {coverage_text}")
                    raw_params['target_coverage_rate'] = target_rate
            else:
                # Pas de calcul de recouvrement du tout
                raw_params['optimization_mode'] = False
                raw_params['target_coverage_rate'] = None
            
            # Validation de la couche
            ParameterValidator.validate_layer_selection(
                raw_params['layer_name'], self.available_layers
            )
            
            # Validation complète des paramètres
            validated_params = ParameterValidator.validate_all_parameters(raw_params)
            
            # Ajoute les nouveaux paramètres
            validated_params['optimization_mode'] = raw_params['optimization_mode']
            validated_params['target_coverage_rate'] = raw_params['target_coverage_rate']
            validated_params['puissance'] = raw_params['puissance']
            validated_params['modules_per_table'] = raw_params['modules_per_table']
            
            # Normalisation
            normalized_params = ParameterNormalizer.normalize_parameters(validated_params)
            
            # Vérification de cohérence géométrique
            #ParameterValidator.validate_geometric_consistency(normalized_params)
            
            return normalized_params
            
        except ValidationError as e:
            self.iface.messageBar().pushWarning("Paramètres invalides", str(e))
            return None
        except Exception as e:
            self.iface.messageBar().pushCritical("Erreur de validation", f"Erreur inattendue: {str(e)}")
            return None

    def run(self):
        """Méthode principale."""
        # Validation complète des paramètres
        params = self._get_and_validate_parameters()
        if not params:
            return
        
        # Récupération de la couche source
        layer = self.layer_helpers.get_layer_by_name(params['layer_name'])
        if not layer:
            self.iface.messageBar().pushCritical("Erreur", "Couche introuvable")
            return
        
        # Récupération des features
        features = list(
            layer.selectedFeatures() if params['selection_only'] 
            else layer.getFeatures()
        )
        
        if not features:
            self.iface.messageBar().pushWarning("Erreur", Config.MESSAGES['error_no_features'])
            return
        
        # Affichage du mode choisi
        if params['calculate_coverage']:
            if params['optimization_mode']:
                mode_msg = f"Mode optimisation: recherche interrang pour {params['target_coverage_rate']}%"
            else:
                mode_msg = f"Mode calcul: recouvrement avec interrang = {params['v_spacing']}m"
            self.iface.messageBar().pushInfo("Mode sélectionné", mode_msg)
        
        # Génération avec les paramètres validés
        success = self._generate_panels_with_new_logic(layer, features, params)
        
        if success:
            settings = QSettings()
            settings.setValue(Config.SETTINGS_LAST_LAYER, params['layer_name'])
            self.close()

    def _generate_panels_with_new_logic(self, layer, features, params):
        """Génération des panneaux."""
        rects = []
        ilot_id = 1
        
        progress = QProgressDialog(
            Config.MESSAGES['progress_label'], 
            Config.MESSAGES['progress_cancel'], 
            0, len(features), 
            self.iface.mainWindow()
        )
        progress.setWindowTitle(Config.MESSAGES['progress_title'])
        progress.setWindowModality(get_window_modal())
        progress.show()
        progress.setValue(0)
        QApplication.processEvents()
        
        try:
            for idx, feat in enumerate(features):
                if progress.wasCanceled():
                    self.iface.messageBar().pushInfo("Info", Config.MESSAGES['progress_interrupted'])
                    return False

                geom = feat.geometry()
                ilot_id = self._process_feature(geom, params, rects, ilot_id, layer)
                progress.setValue(idx + 1)
            
            self._create_panels_layer(rects, layer.crs().authid(), params)
            
            # Calcul de recouvrement selon le mode choisi
            if params['calculate_coverage']:
                self._calculate_coverage_with_mode(params)
            
            return True
            
        except Exception as e:
            self.iface.messageBar().pushCritical("Erreur", f"Erreur lors de la génération: {str(e)}")
            return False
            
        finally:
            progress.close()
            QApplication.processEvents()
    
    def _process_feature(self, geom, params, rects, ilot_id, layer):
        """Traite les géométries."""
        def process_one_polygon(polygon_geom, ilot_id):
            polys = self.geometry_helpers.detect_and_split_holes(
                polygon_geom, margin=Config.HOLE_DETECTION_MARGIN
            )
            if len(polys) > 1:
                for subgeom in polys:
                    ilot_id = process_one_polygon(subgeom, ilot_id)
                return ilot_id

            polygon_geom = polys[0]
            
            # 3 modes distincts
            if params['optimization_mode']:
                # Mode 3: Optimisation v_spacing pour atteindre taux cible
                rects_local = self._optimize_for_target_coverage(
                    polygon_geom, params, ilot_id, layer
                )
            else:
                # Mode 1 et Mode 2: Optimisation du placement (200 configs)
                rects_local = self._optimize_fill_polygon(polygon_geom, params, ilot_id)
            
            rects.extend(rects_local)
            return ilot_id + 1

        # Traitement multipart/singlepart
        if geom.isMultipart():
            multi = geom.asMultiPolygon()
            for part in multi:
                poly = QgsGeometry.fromPolygonXY(part)
                ilot_id = process_one_polygon(poly, ilot_id)
        else:
            ilot_id = process_one_polygon(geom, ilot_id)
        
        return ilot_id

    def _optimize_for_target_coverage(self, polygon_geom, params, ilot_id, layer):
        """Optimise v_spacing pour atteindre le taux de recouvrement cible."""
        target_rate = params['target_coverage_rate']
        v_test = params['v_spacing']
        best_result = None
        best_panels = None
        best_v = None
        
        # Recherche du v_spacing optimal
        while v_test <= Config.V_SPACING_MAX:
            tmp_rects = self._fill_polygon_with_panels(
                polygon_geom, params, ilot_id, v_spacing=v_test
            )
            
            if tmp_rects:
                temp_layer = self._build_temp_layer(
                    tmp_rects, layer.crs().authid(), f"ilot_{ilot_id}_v{int(v_test)}"
                )
                result = self.coverage_logic.generate_covering_for_group(
                    temp_layer, params['h_spacing'], v_test, params['orientation']
                )
                
                if result:
                    # Priorité : résultats <= taux cible, sinon le plus proche
                    if (best_result is None) or (
                        (result["taux"] <= target_rate and best_result["taux"] > target_rate) or
                        (result["taux"] <= target_rate and best_result["taux"] <= target_rate and result["taux"] > best_result["taux"]) or
                        (result["taux"] > target_rate and best_result["taux"] > target_rate and result["taux"] < best_result["taux"])
                    ):
                        best_result = result
                        best_panels = tmp_rects
                        best_v = v_test
                    
                    # Si on est en dessous ou égal au taux cible, on s'arrête
                    if result["taux"] <= target_rate:
                        return tmp_rects

            v_test += Config.V_SPACING_STEP

        # Si pas de solution exacte, prendre la meilleure
        if best_panels is not None:
            return best_panels
        
        # Aucune solution trouvée
        self.iface.messageBar().pushWarning(
            "Optimisation", f"Îlot {ilot_id}: impossible d'optimiser pour {target_rate}%"
        )
        return []

    def _calculate_coverage_with_mode(self, params):
        """Calcule le recouvrement selon le mode choisi."""
        if params['optimization_mode']:
            # En mode optimisation, le recouvrement est déjà calculé
            # mais on refait le calcul final avec les v_spacing optimisés
            message = f"Recouvrement optimisé pour {params['target_coverage_rate']}%"
        else:
            # En mode calcul simple
            message = Config.MESSAGES['info_coverage_calculated'].format(
                v_spacing=params['v_spacing']
            )
        
        self.iface.messageBar().pushInfo("Recouvrement", message)
        self.coverage_logic.calculate_coverage(
            self.iface, params['h_spacing'], params['orientation']
        )

    def _calculate_total_power(self, full_count, half_count):
        """
        Calcule la puissance totale estimée en MWc.
        
        Args:
            full_count (int): Nombre de tables entières
            half_count (int): Nombre de demi-tables
            
        Returns:
            str: Puissance formatée avec unité ou None si données manquantes
        """
        try:
            # Récupération des valeurs depuis l'interface
            puissance_text = self.puissanceLineEdit.text().strip()
            modules_per_table_text = self.pertableLineEdit.text().strip()
            
            # Vérification que les champs sont remplis et valides
            if not puissance_text or not modules_per_table_text:
                return None
            
            puissance = float(puissance_text)
            modules_per_table = float(modules_per_table_text)
            
            # Vérification que les valeurs sont cohérentes
            if puissance <= 0 or modules_per_table <= 0:
                return None
            
            # Formule : (((nombre de full table * nombre de modules par tables) + 
            #             (nombre de half table * (nombre de modules par tables / 2))) * puissance) / 1000000
            puissance_totale = (
                ((full_count * modules_per_table) + 
                 (half_count * (modules_per_table / 2))) * puissance
            ) / 1000000
            
            # Formatage avec unité appropriée
            if puissance_totale >= 1.0:
                return f"{puissance_totale:.2f} MWc"
            else:
                # Si < 1 MWc, afficher en kWc
                puissance_kwc = puissance_totale * 1000
                return f"{puissance_kwc:.1f} kWc"
            
        except (ValueError, ZeroDivisionError, AttributeError):
            # En cas d'erreur, retourner None (pas d'affichage de puissance)
            return None

    def _fill_polygon_with_panels(self, polygon, params, ilot_id, v_spacing=None, anchor_mode="bottom_left"):
        """Délègue au geometry_helpers avec gestion d'erreur."""
        try:
            return self.geometry_helpers.fill_polygon_with_panels(
                polygon, params['length'], params['width'], params['h_spacing'], 
                v_spacing or params['v_spacing'], params['allow_half'], 
                params['edge_margin'], ilot_id, params['orientation'], 
                0.0, 0.0, anchor_mode
            )
        except Exception as e:
            self.iface.messageBar().pushWarning(
                "Erreur géométrique", 
                f"Erreur lors du remplissage du polygone: {str(e)}"
            )
            return []
    
    def _optimize_fill_polygon(self, polygon, params, ilot_id):
        """Délègue au geometry_helpers avec gestion d'erreur."""
        try:
            return self.geometry_helpers.optimize_fill_polygon(
                polygon, params['length'], params['width'], params['h_spacing'], 
                params['v_spacing'], params['allow_half'], params['edge_margin'], 
                ilot_id, params['orientation'], Config.ANCHOR_MODES, Config.OPTIMIZATION_STEPS
            )
        except Exception as e:
            self.iface.messageBar().pushWarning(
                "Erreur d'optimisation", 
                f"Erreur lors de l'optimisation: {str(e)}"
            )
            return []

    def _build_temp_layer(self, rectangles, crs_authid, name):
        """Délègue au layer_helpers avec gestion d'erreur."""
        try:
            return self.layer_helpers.build_temp_layer(rectangles, crs_authid, name)
        except Exception as e:
            self.iface.messageBar().pushWarning(
                "Erreur de couche", 
                f"Erreur lors de la création de couche temporaire: {str(e)}"
            )
            return None

    def _create_panels_layer(self, rects, crs_authid, params):
        """Création couche panneaux avec gestion d'erreur."""
        try:
            if not rects:
                self.iface.messageBar().pushWarning(
                    "Aucun panneau", 
                    "Aucun panneau n'a pu être généré avec les paramètres donnés."
                )
                return
            
            out = QgsVectorLayer(
                f"Polygon?crs={crs_authid}", 
                Config.OUTPUT_PANELS_LAYER_NAME, 
                "memory"
            )
            prov = out.dataProvider()
            prov.addAttributes([
                QgsField("id", QVariant.Int),
                QgsField("table", QVariant.String),
                QgsField("ilot", QVariant.Int),
                QgsField("v_spacing", QVariant.Double),
            ])
            out.updateFields()
            
            for idx, (geom, table_type, ilot, vspace) in enumerate(rects):
                f = QgsFeature()
                f.setGeometry(geom)
                f.setAttributes([idx, table_type, ilot, vspace])
                prov.addFeature(f)
            
            QgsProject.instance().addMapLayer(out)

            # Rendu catégorisé avec couleurs Config
            self._setup_panel_renderer(out)
            
            # Statistiques de génération
            full_count = sum(1 for _, table_type, _, _ in rects if table_type == Config.PANEL_TYPE_FULL)
            half_count = sum(1 for _, table_type, _, _ in rects if table_type == Config.PANEL_TYPE_HALF)
            
            # Calcul de la puissance estimée
            puissance_totale_str = self._calculate_total_power(full_count, half_count)
            
            # Message avec durée infinie (0 = persistant)
            message = f" {full_count} tables entières et {half_count} demi-tables ({len(rects)} panneaux au total)"
            if puissance_totale_str:
                message += f" pour une puissance estimée de {puissance_totale_str}"
            
            # Utiliser pushMessage avec Qgis.Success et duration=0 pour message persistant
            self.iface.messageBar().pushMessage(
                "Génération réussie", 
                message,
                level=Qgis.Success,
                duration=0  # Message persistant
            )
            
        except Exception as e:
            self.iface.messageBar().pushCritical(
                "Erreur de création", 
                f"Impossible de créer la couche panneaux: {str(e)}"
            )
    
    def _setup_panel_renderer(self, layer):
        """Configure le rendu de la couche panneaux."""
        try:
            field_name = "table"
            symbol_full = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol_full.setColor(QColor(Config.COLORS['full_panel']))
            
            symbol_half = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol_half.setColor(QColor(Config.COLORS['half_panel']))
            
            categories = [
                QgsRendererCategory(
                    Config.PANEL_TYPE_FULL, 
                    symbol_full, 
                    Config.PANEL_LABELS[Config.PANEL_TYPE_FULL]
                ),
                QgsRendererCategory(
                    Config.PANEL_TYPE_HALF, 
                    symbol_half, 
                    Config.PANEL_LABELS[Config.PANEL_TYPE_HALF]
                )
            ]
            renderer = QgsCategorizedSymbolRenderer(field_name, categories)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
            
        except Exception as e:
            self.iface.messageBar().pushWarning(
                "Rendu", f"Impossible de configurer le rendu: {str(e)}"
            )