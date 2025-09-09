# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Tracing Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import time
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
from shapely.geometry import Polygon

from ..config import Config


class TracingError(Exception):
    """Exception spécifique au traçage."""
    pass


class TracingState:
    """Encapsule l'état du traçage avec protections intégrées."""
    
    def __init__(self):
        """Initialisation de tracing state."""
        self.s = 0
        self.p = 0
        self.contexte = {"origine": None}
        self.protection = set()
        self.segments_visites = set()
        
        # Protections contre boucles infinies
        self.recursion_depth = 0
        self.panel_decisions = {}
        self.start_time = time.time()
        self.segment_id = 1
        
        # Limites depuis config
        self.max_recursion_depth = getattr(Config, 'TRACING_MAX_RECURSION', 200)
        self.max_decisions_per_panel = getattr(Config, 'TRACING_MAX_DECISIONS_PER_PANEL', 15)
        self.max_execution_time = getattr(Config, 'TRACING_MAX_EXECUTION_TIME', 120)
        
        print(f"TracingState chargé avec qgis.PyQt (version-independent)")
        
    def check_safety_limits(self, panel_id=None):
        """Vérifie toutes les limites de sécurité."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_execution_time:
            raise TracingError(f"Timeout: traçage dépassé {self.max_execution_time}s")
        
        if self.recursion_depth > self.max_recursion_depth:
            raise TracingError(f"Récursion trop profonde: {self.recursion_depth}")
        
        if panel_id is not None:
            count = self.panel_decisions.get(panel_id, 0)
            if count > self.max_decisions_per_panel:
                raise TracingError(f"Trop de décisions pour panneau {panel_id}: {count}")
    
    def can_process_panel(self, panel_id):
        """Vérifie si on peut encore traiter ce panneau."""
        count = self.panel_decisions.get(panel_id, 0)
        return count < self.max_decisions_per_panel
    
    def increment_panel_decision(self, panel_id):
        """Incrémente le compteur de décisions pour un panneau."""
        self.panel_decisions[panel_id] = self.panel_decisions.get(panel_id, 0) + 1
        
    def is_protected(self, panel_id, coin):
        """Vérifie si un panneau/coin est déjà protégé."""
        key = (panel_id, round(coin[0], 6), round(coin[1], 6))
        return key in self.protection
    
    def add_protection(self, panel_id, coin):
        """Ajoute une protection."""
        key = (panel_id, round(coin[0], 6), round(coin[1], 6))
        self.protection.add(key)
    
    def enter_recursion(self, panel_id):
        """Entre dans une nouvelle récursion avec vérifications."""
        self.check_safety_limits(panel_id)
        self.recursion_depth += 1
        self.increment_panel_decision(panel_id)
    
    def exit_recursion(self):
        """Sort d'une récursion."""
        self.recursion_depth -= 1


class PanelTracer:
    """
    Logique de traçage sécurisée de l'enveloppe périphérique.
    """
    
    def __init__(self):
        """Initialisation de panel tracer."""
        self.tol_x = 0.1
        self.tol_y = 0.1
        self.tracker = False
        self.state = None
        self.layer = None
        self.provider = None
        
        print(f"PanelTracer chargé avec qgis.PyQt (version-independent)")
        
    def run_tracing_algorithm(self, panneaux_layer, h_spacing, v_spacing, orientation):
        """Point d'entrée principal."""
        try:
            # Initialisation de l'état
            self.state = TracingState()
            
            # Calcul des tolérances
            self.tol_x, self.tol_y = Config.get_tolerances(h_spacing, v_spacing, orientation)
            self.tracker = Config.is_tracker_mode(orientation)
            
            # Préparation des panneaux
            panneaux = self._prepare_panels(panneaux_layer)
            if not panneaux:
                return None
            
            # Organisation en lignes
            lignes = self._organize_panels_into_lines(panneaux)
            if not lignes:
                return None
            
            # Création de la couche de sortie
            self.layer = self._create_output_layer(panneaux_layer)
            self.provider = self.layer.dataProvider()
            
            # Mapping panneaux -> positions
            panneau_lignes = {id(p): (i, j) for i, ligne in enumerate(lignes) for j, p in enumerate(ligne)}
            
            # Démarrage du traçage avec protection
            if lignes and lignes[0]:
                premier_panneau = lignes[0][0]
                pt_depart = self._get_starting_point(premier_panneau)
                self._tracer_recouvrement(premier_panneau, pt_depart, lignes, panneau_lignes)
            
            self.layer.updateExtents()
            return self.layer
            
        except TracingError as e:
            print(f"Erreur de traçage: {e}")
            return self.layer  # Retourner ce qu'on a même en cas d'erreur
        except Exception as e:
            print(f"Erreur inattendue dans le traçage: {e}")
            return None
    
    def _prepare_panels(self, panneaux_layer):
        """Préparation des panneaux."""
        features = list(panneaux_layer.getFeatures())
        panneaux = []

        for feat in features:
            geom = feat.geometry()
            polys = geom.asGeometryCollection() if geom.isMultipart() else [geom]
            for g in polys:
                coords = [(pt.x(), pt.y()) for pt in g.asPolygon()[0]]
                poly = Polygon(coords)
                if poly.is_valid and not poly.is_empty:
                    centroid = poly.centroid
                    mean_y = sum(pt[1] for pt in coords) / len(coords)
                    mean_x = sum(pt[0] for pt in coords) / len(coords)
                    panneaux.append({
                        "geometry": poly,
                        "centroid": centroid,
                        "mean_y": mean_y,
                        "mean_x": mean_x,
                        "coords": coords,
                        "id": feat["id"] if "id" in feat.fields().names() else feat.id(),
                        "qgs_geometry": g
                    })
        
        # Normalisation des coordonnées pour tracker
        for p in panneaux:
            coords = p["coords"]
            if self.tracker:
                coords = [coords[1], coords[2], coords[3], coords[0]]
            p["coords_norm"] = coords
        
        return panneaux
    
    def _organize_panels_into_lines(self, panneaux):
        """Organisation en lignes."""
        lignes = []
        panneaux_sorted = sorted(panneaux, key=lambda p: -p["mean_y"])
        
        while panneaux_sorted:
            base = panneaux_sorted.pop(0)
            ligne = [base]
            to_remove = []
            
            for i, p in enumerate(panneaux_sorted):
                if abs(p["mean_y"] - base["mean_y"]) < 0.1:
                    ligne.append(p)
                    to_remove.append(i)
            
            for i in reversed(to_remove):
                panneaux_sorted.pop(i)
            
            lignes.append(sorted(ligne, key=lambda p: p["centroid"].x))
        
        return lignes
    
    def _create_output_layer(self, source_layer):
        """Création de la couche de sortie."""
        layer = QgsVectorLayer(f"LineString?crs={source_layer.crs().authid()}", "recouvrement_temp", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("id", QVariant.Int), QgsField("remarque", QVariant.String)])
        layer.updateFields()
        return layer
    
    def _get_starting_point(self, premier_panneau):
        """Calcul du point de départ."""
        if self.tracker:
            return min(premier_panneau["coords_norm"], key=lambda pt: (pt[0], -pt[1]))
        else:
            return min(premier_panneau["coords_norm"], key=lambda pt: (-pt[1], pt[0]))
    
    def _add_segment(self, p1, p2, note):
        """Ajout sécurisé de segment."""
        if p1 == p2:
            return
        
        key = tuple(sorted((p1, p2)))
        if key in self.state.segments_visites:
            return
        
        self.state.segments_visites.add(key)
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(*p1), QgsPointXY(*p2)]))
        feat.setAttributes([self.state.segment_id, note])
        self.provider.addFeature(feat)
        self.state.segment_id += 1
    
    # Fonctions de bord
    def _bord_droite(self, p):
        pt = p["coords_norm"]
        self._add_segment(pt[2], pt[3], "Bord droite")
        return pt[3]

    def _bord_gauche(self, p):
        pt = p["coords_norm"]
        self._add_segment(pt[0], pt[1], "Bord gauche")
        return pt[1]

    def _bord_haut(self, p):
        pt = p["coords_norm"]
        self._add_segment(pt[1], pt[2], "Bord haut")
        return pt[2]

    def _bord_bas(self, p):
        pt = p["coords_norm"]
        self._add_segment(pt[3], pt[0], "Bord bas")
        return pt[0]
    
    # Fonctions de liaison
    def _liaison_droite(self, p1, p2):
        self._add_segment(p1["coords_norm"][2], p2["coords_norm"][1], "Liaison droite")
        return p2["coords_norm"][1]

    def _liaison_gauche(self, p1, p2):
        self._add_segment(p1["coords_norm"][0], p2["coords_norm"][3], "Liaison gauche")
        return p2["coords_norm"][3]

    def _liaison_basse(self, p1, p2):
        self._add_segment(p1["coords_norm"][3], p2["coords_norm"][2], "Liaison basse")
        return p2["coords_norm"][2]

    def _liaison_haute(self, p1, p2):
        self._add_segment(p1["coords_norm"][1], p2["coords_norm"][0], "Liaison haute")
        return p2["coords_norm"][0]
    
    def _tracer_recouvrement(self, panneau, coin, lignes, panneau_lignes, forcer=False):
        """Fonction principale de traçage avec protection contre boucles infinies."""
        panel_id = id(panneau)
        
        # Vérifications de sécurité AVANT traitement
        if not forcer and self.state.is_protected(panel_id, coin):
            return
        
        if not self.state.can_process_panel(panel_id):
            print(f"Panneau {panel_id} atteint limite de décisions")
            return
        
        # Entrer dans la récursion avec protections
        try:
            self.state.enter_recursion(panel_id)
            self.state.add_protection(panel_id, coin)
            
            origine = self.state.contexte.get("origine")
            
            if origine in (None, "decision_2_None", "decision_4_ko", "calcul_projection"):
                if origine in (None, "decision_2_None", "decision_4_ko"):
                    coin = self._bord_haut(panneau)
                return self._decision_1(panneau, lignes, panneau_lignes)

            elif origine in ("decision_1_ko", "decision_6_ok"):
                self.state.contexte["origine"] = None
                return self._decision_3(panneau, lignes, panneau_lignes)

            elif origine in ("decision_1_ok", "decision_6_ko"):
                self.state.contexte["origine"] = None
                return self._decision_2(panneau, lignes, panneau_lignes)

            elif origine == "decision_2_ko":
                self.state.contexte["origine"] = None
                return self._decision_4(panneau, lignes, panneau_lignes)

            elif origine == "decision_2_ok":
                self.state.contexte["origine"] = None
                return self._decision_8(panneau, lignes, panneau_lignes)
            
            elif origine == "decision_3_ko":
                self.state.contexte["origine"] = None
                return self._decision_5(panneau, lignes, panneau_lignes)

            elif origine == "decision_3_ok":
                self.state.contexte["origine"] = None
                return self._decision_7(panneau, lignes, panneau_lignes)

            elif origine == "decision_5_ko":
                self.state.contexte["origine"] = None
                return self._decision_6(panneau, lignes, panneau_lignes)

        except TracingError:
            raise
        except Exception as e:
            print(f"Erreur dans tracer_recouvrement: {e}")
        finally:
            self.state.exit_recursion()
    
    # Fonctions de décision
    def _decision_1(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_droit = coords[2]
        ligne_index, panneau_index = panneau_lignes[id(panneau)]
        ligne = lignes[ligne_index]

        if panneau_index + 1 < len(ligne):
            next_p = ligne[panneau_index + 1]
            next_coords = next_p["coords_norm"]
            next_haut_gauche = next_coords[1]
            dx = next_haut_gauche[0] - pt_haut_droit[0]

            if 0 <= dx <= self.tol_x:
                self.state.contexte["origine"] = "decision_1_ok"
                coin = self._liaison_droite(panneau, next_p)
                return self._tracer_recouvrement(next_p, coin, lignes, panneau_lignes)

        self.state.contexte["origine"] = "decision_1_ko"
        coin = self._bord_droite(panneau)
        return self._tracer_recouvrement(panneau, coin, lignes, panneau_lignes)
    
    def _decision_2(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_gauche = coords[1]
        x_ref, y_ref = pt_haut_gauche
        ligne_index, _ = panneau_lignes[id(panneau)]

        if ligne_index - 1 < 0:
            self.state.s = 0
            self.state.contexte["origine"] = "decision_2_None"
            return self._tracer_recouvrement(panneau, coords[2], lignes, panneau_lignes)

        ligne_precedente = lignes[ligne_index - 1]

        for p2 in ligne_precedente:
            coords2 = p2["coords_norm"]
            pt_bas_gauche = coords2[0]
            x2, y2 = pt_bas_gauche

            if abs(x_ref - x2) < 1e-6 and 0 < (y2 - y_ref) <= self.tol_y:
                self.state.contexte["origine"] = "decision_2_ok"
                coin = self._liaison_haute(panneau, p2)
                return self._tracer_recouvrement(p2, coin, lignes, panneau_lignes)

        self.state.contexte["origine"] = "decision_2_ko"
        return self._tracer_recouvrement(panneau, pt_haut_gauche, lignes, panneau_lignes, forcer=True)
    
    def _decision_3(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_droit = coords[3]
        x_ref, y_ref = pt_bas_droit
        ligne_index, _ = panneau_lignes[id(panneau)]

        if ligne_index + 1 >= len(lignes):
            coin = self._bord_bas(panneau)
            self.state.s = 1
            self.state.contexte["origine"] = 'decision_5_ko'
            return self._tracer_recouvrement(panneau, coin, lignes, panneau_lignes)

        ligne_suivante = lignes[ligne_index + 1]

        for p2 in ligne_suivante:
            coords2 = p2["coords_norm"]
            pt_haut_droit = coords2[2]
            x2, y2 = pt_haut_droit

            if abs(x_ref - x2) < 1e-6 and 0 < (y_ref - y2) <= self.tol_y:
                self.state.contexte["origine"] = "decision_3_ok"
                coin = self._liaison_basse(panneau, p2)
                return self._tracer_recouvrement(p2, coin, lignes, panneau_lignes)

        self.state.contexte["origine"] = "decision_3_ko"
        return self._tracer_recouvrement(panneau, pt_bas_droit, lignes, panneau_lignes, forcer=True)

    def _decision_4(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_gauche = coords[1]
        pt_haut_droit = coords[2]
        x1 = pt_haut_gauche[0]
        x2 = pt_haut_droit[0]
        y = coords[1][1]
        ligne_index, _ = panneau_lignes[id(panneau)]
        ligne_precedente = lignes[ligne_index - 1]

        for p2 in ligne_precedente:
            coords2 = p2["coords_norm"]
            x1_cible = coords2[0][0]
            x2_cible = coords2[3][0]
            y_cible = coords2[0][1]
            
            if self._chevauchement_sur_x(x1, x2, x1_cible, x2_cible) and abs(y_cible - y) <= self.tol_y:
                if x1 < x1_cible:
                    self.state.s = 0
                elif x1 > x1_cible:
                    self.state.s = 1
                
                self.state.p = 1
                return self._calcul_projection(panneau, lignes, panneau_lignes, p2)

        self.state.s = 0
        self.state.contexte["origine"] = "decision_4_ko"
        return self._tracer_recouvrement(panneau, pt_haut_droit, lignes, panneau_lignes)
    
    def _decision_5(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_gauche = coords[0]
        pt_bas_droit = coords[3]
        x1 = pt_bas_gauche[0]
        x2 = pt_bas_droit[0]
        y = coords[0][1]
        ligne_index, _ = panneau_lignes[id(panneau)]
        ligne_suivante = lignes[ligne_index + 1]
        
        for p2 in reversed(ligne_suivante):
            coords2 = p2["coords_norm"]
            x1_cible = coords2[1][0]
            x2_cible = coords2[2][0]
            y_cible = coords2[1][1]

            if self._chevauchement_sur_x(x1, x2, x1_cible, x2_cible) and abs(y_cible - y) <= self.tol_y:
                if x2 < x2_cible:
                    self.state.s = 0
                elif x2 > x2_cible:
                    self.state.s = 1
                
                self.state.p = 2
                return self._calcul_projection(panneau, lignes, panneau_lignes, p2)
        
        coin = self._bord_bas(panneau)
        self.state.s = 1
        self.state.contexte["origine"] = 'decision_5_ko'
        return self._tracer_recouvrement(panneau, coin, lignes, panneau_lignes)

    def _decision_6(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_gauche = coords[0]
        x_ref, y_ref = pt_bas_gauche
        ligne_index, panneau_index = panneau_lignes[id(panneau)]
        ligne = lignes[ligne_index]

        if panneau_index - 1 >= 0:
            prev_p = ligne[panneau_index - 1]
            prev_coords = prev_p["coords_norm"]
            prev_bas_droit = prev_coords[3]
            x2, y2 = prev_bas_droit
            dx = x_ref - x2
            if 0 < dx <= self.tol_x:
                self.state.contexte["origine"] = "decision_6_ok"
                coin = self._liaison_gauche(panneau, prev_p)
                return self._tracer_recouvrement(prev_p, coin, lignes, panneau_lignes)

        coin = self._bord_gauche(panneau)
        self.state.contexte["origine"] = "decision_6_ko"
        return self._tracer_recouvrement(panneau, coin, lignes, panneau_lignes)

    def _decision_7(self, panneau, lignes, panneau_lignes):
        if self.state.s == 0:
            return self._decision_1(panneau, lignes, panneau_lignes)
        else:
            self._bord_droite(panneau)
            return self._decision_3(panneau, lignes, panneau_lignes)

    def _decision_8(self, panneau, lignes, panneau_lignes):
        if self.state.s == 0 and not self.tracker:
            self._bord_gauche(panneau)
            return self._decision_2(panneau, lignes, panneau_lignes)
        else:
            return self._decision_6(panneau, lignes, panneau_lignes)
    
    def _chevauchement_sur_x(self, x1, x2, x1_cible, x2_cible):
        """Détection de chevauchement sur X."""
        return max(x1, x1_cible) <= min(x2, x2_cible)
    
    def _calcul_projection(self, panneau, lignes, panneau_lignes, panneau_cible):
        """Calcul de projection."""
        coords = panneau["coords_norm"]
        coords_cible = panneau_cible["coords_norm"]
        
        if self.state.s == 0 and self.state.p == 1:
            pt_depart = coords_cible[0]
            x_proj = pt_depart[0]
            y_depart = pt_depart[1]
            pt_haut_gauche = coords[1]
            pt_haut_droit = coords[2]
            x1, y1 = pt_haut_gauche
            x2, y2 = pt_haut_droit
            
            if x1 <= x_proj <= x2 and abs(y1 - y_depart) <= self.tol_y:
                pt_proj = (x_proj, y1)
                self._add_segment(pt_depart, pt_proj, "Liaison haute alternative 1")
                self._add_segment(pt_proj, pt_haut_gauche, "Bord haut alternatif 1")
                self._bord_gauche(panneau_cible)
                return self._decision_2(panneau_cible, lignes, panneau_lignes)
            else:
                return None        
        
        elif self.state.s == 0 and self.state.p == 2:
            pt_depart = coords[3]
            x_proj = pt_depart[0]
            y_depart = pt_depart[1]
            pt_haut_gauche_cible = coords_cible[1]
            pt_haut_droit_cible = coords_cible[2]
            x1, y1 = pt_haut_gauche_cible
            x2, y2 = pt_haut_droit_cible

            if x1 <= x_proj <= x2 and abs(y_depart - y1) <= self.tol_y:
                pt_proj = (x_proj, y1)
                self._add_segment(pt_depart, pt_proj, "Liaison haute alternative 2")
                self._add_segment(pt_proj, pt_haut_droit_cible, "Bord haut alternatif 2")
                self.state.contexte["origine"] = 'calcul_projection'
                return self._tracer_recouvrement(panneau_cible, pt_haut_droit_cible, lignes, panneau_lignes)
            else:
                return None
        
        elif self.state.s == 1 and self.state.p == 1:
            pt_depart = coords[1]
            x_proj = pt_depart[0]
            y_depart = pt_depart[1]
            pt_bas_gauche_cible = coords_cible[0]
            pt_bas_droit_cible = coords_cible[3]
            x1, y1 = pt_bas_gauche_cible
            x2, y2 = pt_bas_droit_cible
            
            if x1 <= x_proj <= x2 and abs(y_depart - y1) <= self.tol_y:
                pt_proj = (x_proj, y1)
                self._add_segment(pt_depart, pt_proj, "Liaison basse alternative 1")
                self._add_segment(pt_proj, pt_bas_gauche_cible, "Bord bas alternatif 1")
                return self._decision_6(panneau_cible, lignes, panneau_lignes)
            else:
                return None
            
        elif self.state.s == 1 and self.state.p == 2:
            pt_depart = coords_cible[2]
            x_proj = pt_depart[0]
            y_depart = pt_depart[1]
            pt_bas_gauche = coords[0]
            pt_bas_droit = coords[3]
            x1, y1 = pt_bas_gauche
            x2, y2 = pt_bas_droit

            if x1 <= x_proj <= x2 and abs(y1 - y_depart) <= self.tol_y:
                pt_proj = (x_proj, y1)
                self._add_segment(pt_depart, pt_proj, "Liaison basse alternative 2")
                self._add_segment(pt_proj, pt_bas_droit, "Bord bas alternatif 2")
                coin = self._bord_droite(panneau_cible)
                self.state.contexte["origine"] = 'decision_1_ko'
                return self._tracer_recouvrement(panneau_cible, coin, lignes, panneau_lignes)
            else:
                return None
        
        return None


class TracingLogic:
    """Interface de compatibilité avant le refactoring."""
    
    def __init__(self):
        """Initialisation de tracing logic."""
        self.tracer = PanelTracer()
        print(f"TracingLogic chargé avec qgis.PyQt (version-independent)")
    
    def run_tracing_algorithm(self, panneaux_layer, h_spacing, v_spacing, orientation):
        """Point d'entrée principal."""
        return self.tracer.run_tracing_algorithm(panneaux_layer, h_spacing, v_spacing, orientation)