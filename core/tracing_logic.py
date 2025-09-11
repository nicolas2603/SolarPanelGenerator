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
from collections import deque

from ..config import Config


class TracingError(Exception):
    """Exception spécifique au traçage."""
    pass


class SpatialFilter:
    """
    Filtre spatial pour optimiser la sélection des panneaux candidats.
    """
    
    def __init__(self, h_spacing, v_spacing, orientation=0.0):
        """Initialisation du filtre spatial."""
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.orientation = orientation
        self.tracker = Config.is_tracker_mode(orientation)
        
        # Calcul des tolérances
        self.tol_x, self.tol_y = Config.get_tolerances(h_spacing, v_spacing, orientation)
            
    def get_panel_dimensions(self, panneau):
        """Calcule les dimensions d'un panneau."""
        coords = panneau["coords_norm"]
        xs = [pt[0] for pt in coords]
        ys = [pt[1] for pt in coords]
        
        panel_width = max(xs) - min(xs)
        panel_height = max(ys) - min(ys)
        
        return panel_width, panel_height
    
    def get_uniform_bounding_box(self, panneau):
        """
        Calcule une zone tampon uniforme autour d'un panneau.
        Zone tampon = la longueur du panneau dans toutes les directions.
        """
        coords = panneau["coords_norm"]
        
        # Centre du panneau
        center_x = sum(pt[0] for pt in coords) / len(coords)
        center_y = sum(pt[1] for pt in coords) / len(coords)
        
        # Dimensions du panneau
        panel_width, panel_height = self.get_panel_dimensions(panneau)
        table_type = panneau.get("table_type", "full table")       
        if table_type == "half table":
            max_dimension = max(panel_width * 2, panel_height)
        else:
            max_dimension = max(panel_width, panel_height)
        
        # Zone tampon - limitée pour éviter trop de candidats
        buffer_size = min(max_dimension, 50.0)  # Maximum 50m
        
        bbox = (
            center_x - buffer_size,  # x_min
            center_x + buffer_size,  # x_max  
            center_y - buffer_size,  # y_min
            center_y + buffer_size   # y_max
        )
        
        return bbox
    
    def is_in_bounding_box(self, panneau, bbox):
        """Vérifie si un panneau est dans la zone tampon."""
        x_min, x_max, y_min, y_max = bbox
        coords = panneau["coords_norm"]
        
        # Vérifie si au moins un point du panneau est dans la bbox
        for pt in coords:
            if x_min <= pt[0] <= x_max and y_min <= pt[1] <= y_max:
                return True
        
        # Vérifie si le centre du panneau est dans la bbox
        center_x = sum(pt[0] for pt in coords) / len(coords)
        center_y = sum(pt[1] for pt in coords) / len(coords)
        
        return x_min <= center_x <= x_max and y_min <= center_y <= y_max
    
    def filter_candidates(self, panneau, candidats, sort_direction="distance", max_candidates=25):
        """
        Filtre les candidats avec la zone tampon.
        """
        if not candidats:
            return []
        
        # Zone tampon
        bbox = self.get_uniform_bounding_box(panneau)
        filtered = [p for p in candidats if self.is_in_bounding_box(p, bbox)]
        
        # Tri selon la direction demandée
        if sort_direction == "distance":
            ref_center_x = sum(pt[0] for pt in panneau["coords_norm"]) / 4
            ref_center_y = sum(pt[1] for pt in panneau["coords_norm"]) / 4
            
            def distance_to_ref(p):
                p_center_x = sum(pt[0] for pt in p["coords_norm"]) / 4
                p_center_y = sum(pt[1] for pt in p["coords_norm"]) / 4
                return ((p_center_x - ref_center_x)**2 + (p_center_y - ref_center_y)**2)**0.5
            
            filtered.sort(key=distance_to_ref)
            
        elif sort_direction == "x_asc":
            # Trie par X croissant (gauche vers droite)
            filtered.sort(key=lambda p: min(pt[0] for pt in p["coords_norm"]))
            
        elif sort_direction == "x_desc":
            # Trie par X décroissant (droite vers gauche)
            filtered.sort(key=lambda p: max(pt[0] for pt in p["coords_norm"]), reverse=True)
            
        elif sort_direction == "y_asc":
            # Trie par Y croissant (bas vers haut)
            filtered.sort(key=lambda p: min(pt[1] for pt in p["coords_norm"]))
            
        elif sort_direction == "y_desc":
            # Trie par Y décroissant (haut vers bas)
            filtered.sort(key=lambda p: max(pt[1] for pt in p["coords_norm"]), reverse=True)
        
        # Limite le nombre de candidats pour éviter les explosions
        return filtered[:max_candidates]
    
    def filter_candidates_right(self, panneau, candidats):
        """Filtre les candidats vers la droite (pour panneau_a_droite)."""
        return self.filter_candidates(panneau, candidats, "x_asc", 20)
    
    def filter_candidates_left(self, panneau, candidats):
        """Filtre les candidats vers la gauche (pour panneau_a_gauche)."""
        return self.filter_candidates(panneau, candidats, "x_desc", 20)
    
    def filter_candidates_up(self, panneau, candidats):
        """Filtre les candidats vers le haut (pour panneau_au_dessus)."""
        return self.filter_candidates(panneau, candidats, "y_asc", 20)
    
    def filter_candidates_down(self, panneau, candidats):
        """Filtre les candidats vers le bas (pour panneau_en_dessous, panneau_projection_bas)."""
        return self.filter_candidates(panneau, candidats, "y_desc", 20)


class TracingState:
    """Encapsule l'état du traçage avec protections intelligentes contre les boucles."""
    
    def __init__(self):
        """Initialisation de tracing state."""
        self.s = 0
        self.p = 0
        self.contexte = {"origine": None}
        self.segments_visites = set()
        
        self.panel_coin_visits = {}
        self.panel_forced_visits = {}
        
        self.start_time = time.time()
        self.segment_id = 1
        
        # Statistiques
        self.iterations = 0
        self.max_stack_size = 0
        
        self.max_visits_per_panel_coin = getattr(Config, 'TRACING_MAX_VISITS_PER_PANEL_COIN', 3)
        self.max_forced_visits_per_panel = getattr(Config, 'TRACING_MAX_FORCED_VISITS_PER_PANEL', 5)
        self.max_execution_time = getattr(Config, 'TRACING_MAX_EXECUTION_TIME', 300)
                
    def _get_coin_hash(self, coin):
        """Crée un hash stable pour un coin (point)."""
        if coin is None:
            return None
        return (round(coin[0], 6), round(coin[1], 6))
    
    def check_safety_limits(self, panel_id=None, coin=None, forcer=False):
        """Vérifie les limites de sécurité intelligentes."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_execution_time:
            raise TracingError(f"Timeout: traçage dépassé {self.max_execution_time}s")
        
        if panel_id is not None:
            # Vérification des visites forcées
            if forcer:
                forced_count = self.panel_forced_visits.get(panel_id, 0)
                if forced_count >= self.max_forced_visits_per_panel:
                    raise TracingError(f"Trop de visites forcées pour panneau {panel_id}: {forced_count}")
            
            # Vérification des visites (panel_id, coin)
            if coin is not None:
                coin_hash = self._get_coin_hash(coin)
                if coin_hash is not None:
                    key = (panel_id, coin_hash)
                    visits = self.panel_coin_visits.get(key, 0)
                    if visits >= self.max_visits_per_panel_coin:
                        raise TracingError(f"Trop de visites pour panneau {panel_id}, coin {coin_hash}: {visits}")
    
    def can_process_panel_coin(self, panel_id, coin, forcer=False):
        """Vérifie si on peut encore traiter ce panneau/coin."""
        try:
            self.check_safety_limits(panel_id, coin, forcer)
            return True
        except TracingError:
            return False
    
    def register_visit(self, panel_id, coin, forcer=False):
        """Enregistre une visite panneau/coin."""
        self.iterations += 1
        
        # Enregistre visite forcée
        if forcer:
            self.panel_forced_visits[panel_id] = self.panel_forced_visits.get(panel_id, 0) + 1
        
        # Enregistre visite panneau/coin
        if coin is not None:
            coin_hash = self._get_coin_hash(coin)
            if coin_hash is not None:
                key = (panel_id, coin_hash)
                self.panel_coin_visits[key] = self.panel_coin_visits.get(key, 0) + 1


class PanelTracer:
    """
    Logique de traçage avec conversion récursion -> itération simple.
    """
    
    def __init__(self):
        """Initialisation de panel tracer."""
        self.tol_x = 0.1
        self.tol_y = 0.1
        self.tracker = False
        self.state = None
        self.layer = None
        self.provider = None
        self.spatial_filter = None
        
        # Pour la conversion itérative
        self.call_stack = None
        
    def run_tracing_algorithm(self, panneaux_layer, h_spacing, v_spacing, orientation):
        """Point d'entrée principal."""
        try:
            # Initialisation de l'état
            self.state = TracingState()
            
            # Calcul des tolérances
            self.tol_x, self.tol_y = Config.get_tolerances(h_spacing, v_spacing, orientation)
            self.tracker = Config.is_tracker_mode(orientation)
            
            # Initialisation du filtre spatial
            self.spatial_filter = SpatialFilter(h_spacing, v_spacing, orientation)
            
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
            
            print(f"Organisation: {len(lignes)} lignes, {len(panneaux)} panneaux total")
            
            # Démarrage du traçage avec version itérative
            if lignes and lignes[0]:
                premier_panneau = lignes[0][0]
                pt_depart = self._get_starting_point(premier_panneau)
                
                # Conversion en itératif avec pile de calls
                self.call_stack = deque()
                self.call_stack.append(('tracer_recouvrement', premier_panneau, pt_depart, lignes, panneau_lignes, False))
                
                self._process_stack()
            
            self.layer.updateExtents()
            
            print(f"Traçage terminé: {self.state.iterations} itérations, "
                  f"{self.state.segment_id - 1} segments, "
                  f"pile max: {self.state.max_stack_size}")
            
            return self.layer
            
        except TracingError as e:
            print(f"Erreur de traçage: {e}")
            return self.layer  # Retourner ce qu'on a même en cas d'erreur
        except Exception as e:
            print(f"Erreur inattendue dans le traçage: {e}")
            return None
    
    def _process_stack(self):
        """Traite la pile d'appels de façon itérative."""
        max_iterations = 100000
        iteration = 0
        
        while self.call_stack and iteration < max_iterations:
            iteration += 1
            self.state.max_stack_size = max(self.state.max_stack_size, len(self.call_stack))
            
            if iteration % 1000 == 0:
                self.state.check_safety_limits()
                print(f"Itération {iteration}: pile={len(self.call_stack)}, segments={self.state.segment_id-1}")
            
            # Prendre le prochain appel
            call_info = self.call_stack.pop()
            method_name = call_info[0]
            args = call_info[1:]
            
            # Dispatch vers la bonne méthode
            if method_name == 'tracer_recouvrement':
                self._tracer_recouvrement(*args)
            elif method_name == 'panneau_a_droite':
                self._panneau_a_droite(*args)
            elif method_name == 'panneau_au_dessus':
                self._panneau_au_dessus(*args)
            elif method_name == 'panneau_en_dessous':
                self._panneau_en_dessous(*args)
            elif method_name == 'panneau_projection_haut':
                self._panneau_projection_haut(*args)
            elif method_name == 'panneau_projection_bas':
                self._panneau_projection_bas(*args)
            elif method_name == 'panneau_a_gauche':
                self._panneau_a_gauche(*args)
            elif method_name == 'panneau_sens_1':
                self._panneau_sens_1(*args)
            elif method_name == 'panneau_sens_2':
                self._panneau_sens_2(*args)
            elif method_name == 'calcul_projection':
                self._calcul_projection(*args)
        
        if iteration >= max_iterations:
            print(f"Warning: Limite d'itérations atteinte ({max_iterations})")
    
    def _add_call(self, method_name, *args):
        """Ajoute un appel à la pile (remplace l'appel récursif)."""
        self.call_stack.append((method_name, *args))
    
    def _tracer_recouvrement(self, panneau, coin, lignes, panneau_lignes, forcer=False):
        """Fonction principale de traçage avec protection contre boucles infinies."""
        panel_id = id(panneau)
        
        if not self.state.can_process_panel_coin(panel_id, coin, forcer):
            return
        
        # Enregistrer cette visite
        self.state.register_visit(panel_id, coin, forcer)
        
        try:
            origine = self.state.contexte.get("origine")
            
            if origine in (None, "panneau_au_dessus_None", "panneau_projection_haut_ko", "calcul_projection"):
                if origine in (None, "panneau_au_dessus_None", "panneau_projection_haut_ko"):
                    coin = self._bord_haut(panneau)
                self._add_call('panneau_a_droite', panneau, lignes, panneau_lignes)

            elif origine in ("panneau_a_droite_ko", "panneau_a_gauche_ok"):
                self.state.contexte["origine"] = None
                self._add_call('panneau_en_dessous', panneau, lignes, panneau_lignes)

            elif origine in ("panneau_a_droite_ok", "panneau_a_gauche_ko"):
                self.state.contexte["origine"] = None
                self._add_call('panneau_au_dessus', panneau, lignes, panneau_lignes)

            elif origine == "panneau_au_dessus_ko":
                self.state.contexte["origine"] = None
                self._add_call('panneau_projection_haut', panneau, lignes, panneau_lignes)

            elif origine == "panneau_au_dessus_ok":
                self.state.contexte["origine"] = None
                self._add_call('panneau_sens_2', panneau, lignes, panneau_lignes)
            
            elif origine == "panneau_en_dessous_ko":
                self.state.contexte["origine"] = None
                self._add_call('panneau_projection_bas', panneau, lignes, panneau_lignes)

            elif origine == "panneau_en_dessous_ok":
                self.state.contexte["origine"] = None
                self._add_call('panneau_sens_1', panneau, lignes, panneau_lignes)

            elif origine == "panneau_projection_bas_ko":
                self.state.contexte["origine"] = None
                self._add_call('panneau_a_gauche', panneau, lignes, panneau_lignes)

        except TracingError:
            raise
        except Exception as e:
            print(f"Erreur dans tracer_recouvrement: {e}")
    
    def _panneau_a_droite(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_droit = coords[2]
        ligne_index, panneau_index = panneau_lignes[id(panneau)]
        ligne = lignes[ligne_index]

        candidats_bruts = ligne[panneau_index + 1:]
        candidats_filtrés = self.spatial_filter.filter_candidates_right(panneau, candidats_bruts)

        for next_p in candidats_filtrés:
            next_coords = next_p["coords_norm"]
            next_haut_gauche = next_coords[1]
            dx = next_haut_gauche[0] - pt_haut_droit[0]

            if 0 <= dx <= self.tol_x:
                self.state.contexte["origine"] = "panneau_a_droite_ok"
                coin = self._liaison_droite(panneau, next_p)
                self._add_call('tracer_recouvrement', next_p, coin, lignes, panneau_lignes, False)
                return

        self.state.contexte["origine"] = "panneau_a_droite_ko"
        coin = self._bord_droite(panneau)
        self._add_call('tracer_recouvrement', panneau, coin, lignes, panneau_lignes, False)
    
    def _panneau_au_dessus(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_gauche = coords[1]
        x_ref, y_ref = pt_haut_gauche
        ligne_index, _ = panneau_lignes[id(panneau)]

        if ligne_index - 1 < 0:
            self.state.s = 0
            self.state.contexte["origine"] = "panneau_au_dessus_None"
            self._add_call('tracer_recouvrement', panneau, coords[2], lignes, panneau_lignes, False)
            return

        candidats_bruts = lignes[ligne_index - 1]
        candidats_filtrés = self.spatial_filter.filter_candidates_up(panneau, candidats_bruts)

        for p2 in candidats_filtrés:
            coords2 = p2["coords_norm"]
            pt_bas_gauche = coords2[0]
            x2, y2 = pt_bas_gauche

            if abs(x_ref - x2) < 1e-6 and 0 < (y2 - y_ref) <= self.tol_y:
                self.state.contexte["origine"] = "panneau_au_dessus_ok"
                coin = self._liaison_haute(panneau, p2)
                self._add_call('tracer_recouvrement', p2, coin, lignes, panneau_lignes, False)
                return

        self.state.contexte["origine"] = "panneau_au_dessus_ko"
        self._add_call('tracer_recouvrement', panneau, pt_haut_gauche, lignes, panneau_lignes, True)
    
    def _panneau_en_dessous(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_droit = coords[3]
        x_ref, y_ref = pt_bas_droit
        ligne_index, _ = panneau_lignes[id(panneau)]

        if ligne_index + 1 >= len(lignes):
            coin = self._bord_bas(panneau)
            self.state.s = 1
            self.state.contexte["origine"] = 'panneau_projection_bas_ko'
            self._add_call('tracer_recouvrement', panneau, coin, lignes, panneau_lignes, False)
            return

        candidats_bruts = lignes[ligne_index + 1]
        candidats_filtrés = self.spatial_filter.filter_candidates_down(panneau, candidats_bruts)

        for p2 in candidats_filtrés:
            coords2 = p2["coords_norm"]
            pt_haut_droit = coords2[2]
            x2, y2 = pt_haut_droit

            if abs(x_ref - x2) < 1e-6 and 0 < (y_ref - y2) <= self.tol_y:
                self.state.contexte["origine"] = "panneau_en_dessous_ok"
                coin = self._liaison_basse(panneau, p2)
                self._add_call('tracer_recouvrement', p2, coin, lignes, panneau_lignes, False)
                return

        self.state.contexte["origine"] = "panneau_en_dessous_ko"
        self._add_call('tracer_recouvrement', panneau, pt_bas_droit, lignes, panneau_lignes, True)

    def _panneau_projection_haut(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_haut_gauche = coords[1]
        pt_haut_droit = coords[2]
        x1 = pt_haut_gauche[0]
        x2 = pt_haut_droit[0]
        y = coords[1][1]
        ligne_index, _ = panneau_lignes[id(panneau)]
        
        candidats_bruts = lignes[ligne_index - 1]
        candidats_filtrés = self.spatial_filter.filter_candidates_up(panneau, candidats_bruts)

        for p2 in candidats_filtrés:
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
                self._add_call('calcul_projection', panneau, lignes, panneau_lignes, p2)
                return

        self.state.s = 0
        self.state.contexte["origine"] = "panneau_projection_haut_ko"
        self._add_call('tracer_recouvrement', panneau, pt_haut_droit, lignes, panneau_lignes, False)
    
    def _panneau_projection_bas(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_gauche = coords[0]
        pt_bas_droit = coords[3]
        x1 = pt_bas_gauche[0]
        x2 = pt_bas_droit[0]
        y = coords[0][1]
        ligne_index, _ = panneau_lignes[id(panneau)]
        
        candidats_bruts = lignes[ligne_index + 1]
        candidats_filtrés = self.spatial_filter.filter_candidates_down(panneau, candidats_bruts)
        candidats_filtrés.reverse()  # Garder l'ordre reversed de l'original
        
        for p2 in candidats_filtrés:
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
                self._add_call('calcul_projection', panneau, lignes, panneau_lignes, p2)
                return
        
        coin = self._bord_bas(panneau)
        self.state.s = 1
        self.state.contexte["origine"] = 'panneau_projection_bas_ko'
        self._add_call('tracer_recouvrement', panneau, coin, lignes, panneau_lignes, False)

    def _panneau_a_gauche(self, panneau, lignes, panneau_lignes):
        coords = panneau["coords_norm"]
        pt_bas_gauche = coords[0]
        x_ref, y_ref = pt_bas_gauche
        ligne_index, panneau_index = panneau_lignes[id(panneau)]
        ligne = lignes[ligne_index]

        if panneau_index - 1 >= 0:
            candidats_bruts = ligne[:panneau_index]
            candidats_filtrés = self.spatial_filter.filter_candidates_left(panneau, candidats_bruts)

            for prev_p in candidats_filtrés:
                prev_coords = prev_p["coords_norm"]
                prev_bas_droit = prev_coords[3]
                x2, y2 = prev_bas_droit
                dx = x_ref - x2
                
                if 0 < dx <= self.tol_x:
                    self.state.contexte["origine"] = "panneau_a_gauche_ok"
                    coin = self._liaison_gauche(panneau, prev_p)
                    self._add_call('tracer_recouvrement', prev_p, coin, lignes, panneau_lignes, False)
                    return

        coin = self._bord_gauche(panneau)
        self.state.contexte["origine"] = "panneau_a_gauche_ko"
        self._add_call('tracer_recouvrement', panneau, coin, lignes, panneau_lignes, False)

    def _panneau_sens_1(self, panneau, lignes, panneau_lignes):
        if self.state.s == 0:
            self._add_call('panneau_a_droite', panneau, lignes, panneau_lignes)
        else:
            self._bord_droite(panneau)
            self._add_call('panneau_en_dessous', panneau, lignes, panneau_lignes)

    def _panneau_sens_2(self, panneau, lignes, panneau_lignes):
        if self.state.s == 0 and not self.tracker:
            self._bord_gauche(panneau)
            self._add_call('panneau_au_dessus', panneau, lignes, panneau_lignes)
        else:
            self._add_call('panneau_a_gauche', panneau, lignes, panneau_lignes)
    
    def _calcul_projection(self, panneau, lignes, panneau_lignes, panneau_cible):
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
                self._add_call('panneau_au_dessus', panneau_cible, lignes, panneau_lignes)
                return
        
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
                self._add_call('tracer_recouvrement', panneau_cible, pt_haut_droit_cible, lignes, panneau_lignes, False)
                return
        
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
                self._add_call('panneau_a_gauche', panneau_cible, lignes, panneau_lignes)
                return
            
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
                self.state.contexte["origine"] = 'panneau_a_droite_ko'
                self._add_call('tracer_recouvrement', panneau_cible, coin, lignes, panneau_lignes, False)
                return
    
    # Méthodes utilitaires (identiques à l'original)
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
                    table_type = "full table"
                    try:
                        if "table" in feat.fields().names():
                            table_type = feat["table"]
                    except:
                        pass
                    panneaux.append({
                        "geometry": poly,
                        "centroid": centroid,
                        "mean_y": mean_y,
                        "mean_x": mean_x,
                        "coords": coords,
                        "id": feat["id"] if "id" in feat.fields().names() else feat.id(),
                        "qgs_geometry": g,
                        "table_type": table_type
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
    
    def _chevauchement_sur_x(self, x1, x2, x1_cible, x2_cible):
        return max(x1, x1_cible) <= min(x2, x2_cible)


class TracingLogic:
    """Interface de compatibilité avant le refactoring."""
    
    def __init__(self):
        """Initialisation de tracing logic."""
        self.tracer = PanelTracer()
        print(f"TracingLogic chargé avec traçage itératif simple (logique préservée)")
    
    def run_tracing_algorithm(self, panneaux_layer, h_spacing, v_spacing, orientation):
        """Point d'entrée principal."""
        return self.tracer.run_tracing_algorithm(panneaux_layer, h_spacing, v_spacing, orientation)