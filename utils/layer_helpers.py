# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Layer Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

from qgis.core import *
from qgis.PyQt.QtCore import QVariant


class LayerHelpers:
    """
    Helpers pour les couches SIG.
    """
    
    def __init__(self):
        """Initialiser de layer helpers."""
        print(f"LayerHelpers chargé avec qgis.PyQt (version-independent)")
    
    def get_polygon_layers(self):
        """
        Récupère les couches de polygones.
        """
        polygon_layers = []
        
        for layer in QgsProject.instance().mapLayers().values():
            if (isinstance(layer, QgsVectorLayer) and 
                layer.isValid() and
                layer.geometryType() == QgsWkbTypes.PolygonGeometry):
                polygon_layers.append(layer)
                
        return polygon_layers
    
    def get_layer_by_name(self, layer_name):
        """Récupère les couches par nom."""
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == layer_name:
                return layer
        return None
    
    def build_temp_layer(self, rectangles, crs_authid, name):
        """Prépare la couche temporaire."""
        temp_layer = QgsVectorLayer("Polygon?crs=" + crs_authid, name, "memory")
        pr = temp_layer.dataProvider()
        pr.addAttributes([
            QgsField("id", QVariant.Int),
            QgsField("table", QVariant.String),
            QgsField("ilot", QVariant.Int),
            QgsField("v_spacing", QVariant.Double),
        ])
        temp_layer.updateFields()
        for idx, (g, table_type, ilot, vspace) in enumerate(rectangles):
            f = QgsFeature()
            f.setGeometry(g)
            f.setAttributes([idx, table_type, ilot, vspace])
            pr.addFeature(f)
        temp_layer.updateExtents()
        return temp_layer