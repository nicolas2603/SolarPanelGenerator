# -*- coding: utf-8 -*-
"""
SolarPanelGenerator Plugin Geometry Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2025 Nicolas Lieutenant
"""

import math
from qgis.core import *

from ..config import Config


class GeometryHelpers:
    """
    Opérations géométriques (placement, optimisation).
    """
    
    def detect_and_split_holes(self, polygon_geometry, margin=10.0):
        """Détection des trous dans les géométries."""
        if polygon_geometry.isEmpty():
            return []
        
        poly = polygon_geometry.asPolygon()
        if not poly or len(poly) <= 1:
            return [polygon_geometry]

        geom = polygon_geometry.makeValid()
        shrunk = geom.buffer(-margin, 5)
        if shrunk.isEmpty():
            return [geom]
        expanded = shrunk.buffer(margin, 5)
        geoms = []
        if expanded.isMultipart():
            multi = expanded.asMultiPolygon()
            for poly in multi:
                geoms.append(QgsGeometry.fromPolygonXY(poly))
        else:
            poly = expanded.asPolygon()
            if poly:
                geoms.append(QgsGeometry.fromPolygonXY(poly))
        
        return geoms if len(geoms) > 0 else [polygon_geometry]

    def fill_polygon_with_panels(self, polygon, length, width, h_spacing, v_spacing, allow_half, edge_margin, ilot_id, orientation=0.0, row_offset=0.0, col_offset=0.0, anchor_mode="bottom_left"):
        """Remplissage des polygones."""
        rects = []
        inner = polygon.buffer(-edge_margin, 50)
        if inner.isEmpty():
            return rects

        env = inner.boundingBox()
        min_x, max_x = env.xMinimum(), env.xMaximum()
        min_y, max_y = env.yMinimum(), env.yMaximum()

        full_length = float(length)
        half_length = full_length / 2.0

        # déterminer mode vertical (tracker) ou horizontal (historique)
        is_vertical = Config.is_tracker_mode(orientation)

        if not is_vertical:
            # ----- MODE HORIZONTAL -----
            step_perp = width + v_spacing            # espacement entre lignes (Y)
            axial_step_len = full_length + h_spacing # espacement le long de X (panneaux successifs)
            # départ selon bottom/top
            if "bottom" in anchor_mode:
                perp = min_y + (row_offset % step_perp)
            else:
                perp = max_y - width - (row_offset % step_perp)

            while perp + width <= max_y:
                # ligne centrale de la bande (axe X)
                line = QgsGeometry.fromPolylineXY([QgsPointXY(min_x, perp + width/2.0), QgsPointXY(max_x, perp + width/2.0)])
                inter = inner.intersection(line.buffer(width/2.0, 5))
                if inter and not inter.isEmpty():
                    segments = []
                    if inter.type() == QgsWkbTypes.LineGeometry:
                        segments = inter.asMultiPolyline() if inter.isMultipart() else [inter.asPolyline()]
                    else:
                        for poly_ in (inter.asMultiPolygon() if inter.isMultipart() else [inter.asPolygon()]):
                            for ring in poly_:
                                segments.append(ring)

                    # trier par min X
                    segments.sort(key=lambda seg: min(pt.x() for pt in seg if pt is not None))

                    cy = perp + width/2.0

                    for seg in segments:
                        xs = [pt.x() for pt in seg if pt is not None]
                        if not xs:
                            continue
                        seg_min, seg_max = min(xs), max(xs)

                        # départ horizontal (left/right)
                        if "left" in anchor_mode:
                            x = seg_min + (col_offset % axial_step_len)
                        else:
                            x = seg_max - (col_offset % axial_step_len)

                        if x < seg_min:
                            x = seg_min
                        if x > seg_max:
                            x = seg_max

                        # placement le long de X
                        while x + half_length <= seg_max:
                            placed = False

                            # table entière
                            if x + full_length <= seg_max:
                                cx = x + full_length / 2.0
                                rect = self.create_rectangle(QgsPointXY(cx, cy), full_length, width, orientation)
                                if rect.area() > 0:
                                    inter_area = rect.intersection(inner).area()
                                    if inner.contains(rect):
                                        rects.append((rect, "full table", ilot_id, v_spacing))
                                        x += full_length + h_spacing
                                        placed = True

                            # demi-table
                            if not placed and allow_half:
                                cx = x + half_length / 2.0
                                rect = self.create_rectangle(QgsPointXY(cx, cy), half_length, width, orientation)
                                if rect.area() > 0:
                                    inter_area = rect.intersection(inner).area()
                                    if inner.contains(rect):
                                        rects.append((rect, "half table", ilot_id, v_spacing))
                                        x += half_length + h_spacing
                                        placed = True

                            if not placed:
                                x += 1.0
                                if x + half_length > seg_max:
                                    break
                perp += step_perp

        else:
            # ----- MODE VERTICAL -----
            step_perp = width + v_spacing            # espacement entre colonnes (X)
            axial_step_len = full_length + h_spacing # espacement le long de Y (hauteur des rangées)
        
            # --- Pré-calcul des lignes horizontales ---
            lines_y = []
            if "bottom" in anchor_mode:
                y = min_y + (row_offset % axial_step_len)
                while y + full_length <= max_y:
                    lines_y.append(y)
                    y += axial_step_len
            else:  # anchor_mode = "top"
                y = max_y - full_length - (row_offset % axial_step_len)
                while y >= min_y:
                    lines_y.append(y)
                    y -= axial_step_len
        
            # --- Boucle colonnes ---
            if "left" in anchor_mode:
                perp = min_x + (col_offset % step_perp)
                step_sign = +1
            else:  # "right"
                perp = max_x - width - (col_offset % step_perp)
                step_sign = -1
        
            while (perp + width <= max_x and step_sign > 0) or (perp >= min_x and step_sign < 0):
                cx = perp + width / 2.0
        
                for y in lines_y:
                    cy = y + full_length / 2.0
                    rect = self.create_rectangle(QgsPointXY(cx, cy), full_length, width, orientation)
                    if rect and inner.contains(rect):
                        rects.append((rect, "full table", ilot_id, v_spacing))
        
                perp += step_sign * step_perp

        return rects

    def optimize_fill_polygon(self, polygon, length, width, h_spacing, v_spacing, allow_half, edge_margin, ilot_id, orientation=0.0, anchor_modes=None, steps=10):
        """Optimise la position des panneaux en testant les x combinaisons."""
        if anchor_modes is None:
            anchor_modes = ["bottom_left", "bottom_right", "top_left", "top_right"]

        best_rects = []
        best_count = 0

        axial_step_len = length + h_spacing
        step_perp = width + v_spacing

        for anchor in anchor_modes:
            for i in range(steps):
                row_offset = (i / steps) * axial_step_len
                for j in range(steps):
                    col_offset = (j / steps) * step_perp

                    rects = self.fill_polygon_with_panels(
                        polygon, length, width, h_spacing, v_spacing, allow_half,
                        edge_margin, ilot_id, orientation=orientation,
                        row_offset=row_offset, col_offset=col_offset,
                        anchor_mode=anchor
                    )

                    if len(rects) > best_count:
                        best_count = len(rects)
                        best_rects = rects

        return best_rects

    def create_rectangle(self, center, length, width, orientation=0.0):
        """Trace le panneau."""
        dx = length / 2.0
        dy = width / 2.0
        # points locaux centrés en (0,0)
        local_pts = [(-dx, -dy), (-dx, +dy), (+dx, +dy), (+dx, -dy), (-dx, -dy)]
        
        if orientation % 360.0 == 0.0:
            pts = [QgsPointXY(center.x() + x, center.y() + y) for (x, y) in local_pts]
            return QgsGeometry.fromPolygonXY([pts])
        
        # appliquer rotation
        angle = math.radians(orientation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated = []
        for (x, y) in local_pts:
            xr = cos_a * x - sin_a * y
            yr = sin_a * x + cos_a * y
            rotated.append(QgsPointXY(center.x() + xr, center.y() + yr))
        return QgsGeometry.fromPolygonXY([rotated])