# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Coverage Logic
~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

from collections import defaultdict
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
import processing

from .tracing_logic import TracingLogic


class CoverageLogic:
    """
    Logique de calcul des surfaces de recouvrement.
    """
    
    def __init__(self):
        """Initialisation de coverage logic."""
        self.tracing_logic = TracingLogic()
    
    def generate_covering_for_group(self, panneaux_layer, h_spacing, v_spacing, orientation):
        """
        Génération de l'enveloppe de couverture.
        """
        # Applique le moteur de traçage
        linestring_layer = self.tracing_logic.run_tracing_algorithm(panneaux_layer, h_spacing, v_spacing, orientation)
        
        if not linestring_layer:
            return None

        # Nettoyage géométrique
        try:
            fixed = processing.run("native:fixgeometries", {
                'INPUT': linestring_layer,
                'OUTPUT': 'memory:'
            })['OUTPUT']

            # Dissolve toutes les lignes en une seule géométrie
            dissolved = processing.run("native:dissolve", {
                'INPUT': fixed,
                'FIELD': [],
                'OUTPUT': 'memory:'
            })['OUTPUT']

            # Ferme la ligne pour créer un polygone
            polygon_layer = processing.run("native:polygonize", {
                'INPUT': dissolved,
                'OUTPUT': 'memory:'
            })['OUTPUT']

            recouvrement_feat = next(polygon_layer.getFeatures())
        except:
            return None

        geom = recouvrement_feat.geometry()
        poly_geom = geom
        surface_ha = poly_geom.area() / 10_000

        count_full = 0
        count_half = 0
        full_areas = []
        half_areas = []
        
        for f in panneaux_layer.getFeatures():
            g = f.geometry()
            if g:
                area = g.area()
                table_type = f["table"]
                if table_type == "full table":
                    count_full += 1
                    full_areas.append(area)
                elif table_type == "half table":
                    count_half += 1
                    half_areas.append(area)

        if not full_areas and not half_areas:
            return None

        surface_full = sum(full_areas) / len(full_areas) if full_areas else 0
        surface_half = sum(half_areas) / len(half_areas) if half_areas else 0

        denom = surface_ha * 10_000
        if denom > 0:
            taux_recouvrement = ((count_full * surface_full) + (count_half * surface_half)) * 100 / denom
            taux_recouvrement = round(taux_recouvrement, 1)
        else:
            taux_recouvrement = 0

        return {
            "geometry": poly_geom,
            "surface": surface_ha,
            "full": count_full,
            "half": count_half,
            "taux": taux_recouvrement
        }

    def calculate_coverage(self, iface, h_spacing, orientation):
        """
        Calcul des taux de recouvrement par îlot.
        """
        layer_name = "panneaux"
        panneaux_layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == layer_name:
                panneaux_layer = layer
                break

        if not panneaux_layer:
            iface.messageBar().pushWarning("Erreur", f"Couche '{layer_name}' introuvable.")
            return

        grouped_by_ilot = defaultdict(list)
        for feat in panneaux_layer.getFeatures():
            ilot = feat["ilot"]
            grouped_by_ilot[ilot].append(feat)

        recouvrement_layer = QgsVectorLayer("Polygon?crs=" + panneaux_layer.crs().authid(), "recouvrement", "memory")
        prov = recouvrement_layer.dataProvider()
        prov.addAttributes([
            QgsField("ilot", QVariant.Int),
            QgsField("surface", QVariant.Double),
            QgsField("table", QVariant.Int),
            QgsField("demi_table", QVariant.Int),
            QgsField("taux", QVariant.Double)
        ])
        recouvrement_layer.updateFields()
        
        recouvrement_layer.setName("recouvrement")
        symbol = QgsFillSymbol.createSimple({
            'outline_color': 'red',
            'outline_width': '1.0',
            'color': '0,0,0,0'
        })
        recouvrement_layer.renderer().setSymbol(symbol)

        for ilot, feats in grouped_by_ilot.items():
            # v_spacing de l'îlot (toutes les entités d'un îlot partagent le même)
            try:
                v_spacing_ilot = float(feats[0]["v_spacing"])
            except Exception:
                v_spacing_ilot = 3.0  # valeur par défaut
            
            # Couche temporaire de panneaux pour l'îlot
            temp_layer = QgsVectorLayer("Polygon?crs=" + panneaux_layer.crs().authid(), f"ilot_{ilot}", "memory")
            pr = temp_layer.dataProvider()
            pr.addAttributes(panneaux_layer.fields())
            temp_layer.updateFields()
            pr.addFeatures(feats)
            temp_layer.updateExtents()

            result = self.generate_covering_for_group(temp_layer, h_spacing, v_spacing_ilot, orientation)
            if result:
                f = QgsFeature()
                f.setGeometry(result["geometry"])
                f.setAttributes([ilot, result["surface"], result["full"], result["half"], result["taux"]])
                prov.addFeature(f)

        QgsProject.instance().addMapLayer(recouvrement_layer)
        
        # Configuration des étiquettes
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'taux'
        label_settings.placement = QgsPalLayerSettings.OverPoint
        label_settings.enabled = True

        # Configuration du texte (taille, couleur)
        text_format = QgsTextFormat()
        text_format.setSize(10)
        text_format.setColor(QColor('red'))
        
        # Tampon (halo autour du texte)
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor('white'))

        # Appliquer le format
        text_format.setBuffer(buffer_settings)
        label_settings.setFormat(text_format)

        # Application à la couche
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        recouvrement_layer.setLabeling(labeling)
        recouvrement_layer.setLabelsEnabled(True)
        recouvrement_layer.triggerRepaint()