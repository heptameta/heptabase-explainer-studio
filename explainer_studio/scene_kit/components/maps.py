"""Maps: countries, land, rivers, lakes, cities and any GeoJSON (historical borders, provinces, empires) drawn as
native shapes, so a region can be coloured, highlighted, labelled, moved along or morphed beat by beat.

Natural Earth data (public domain) comes from the folder `explainer-studio setup` fills. A series' own GeoJSON lives
under production/ (record where it came from in credits.yaml).

    world = GeoMap(projection="robinson")                    # every country, keyed by ISO code: world["FRA"]
    europe = GeoMap(bounds=(-12, 34, 42, 62))                 # crop to a lon/lat box (west, south, east, north)
    world.color_by_values({"CHN": 1.4e9, "IND": 1.4e9})       # choropleth
    self.play(ShowCreation(world.get_route([(2.35, 48.86), (-74, 40.7)])))   # great-circle route, Paris to New York
    later = GeoMap(geojson="shared/assets/geo/1815.geojson", key_property="NAME", reference_map=europe)
    self.play(morph_map(europe, later))
"""

from __future__ import annotations

import itertools
import json
import math
from functools import lru_cache

import numpy as np
import shapely.geometry as shapely_geometry  # module alias: manimlib also defines Polygon and Point
from manimlib import *
from shapely.ops import transform as _shapely_transform

from ... import user_dirs
from ..context import get_scene_context
from ..parts import KeyedGroup
from ..style import SMALL_FONT_SIZE

__all__ = ["CONTINENTS", "SHORT_NAME_ZHT_BY_CODE_MAP", "GeoMap", "get_color_legend", "get_map", "merge_regions",
           "morph_map"]

# Natural Earth's NAME_ZHT is the formal name ("中華人民共和國"); these are the everyday ones for labels.
SHORT_NAME_ZHT_BY_CODE_MAP = {
    "CHN": "中國", "TWN": "台灣", "USA": "美國", "GBR": "英國", "RUS": "俄羅斯", "KOR": "南韓", "PRK": "北韓",
    "DEU": "德國", "FRA": "法國", "JPN": "日本", "IND": "印度", "ITA": "義大利", "ESP": "西班牙", "CAN": "加拿大",
    "AUS": "澳洲", "BRA": "巴西", "MEX": "墨西哥", "IDN": "印尼", "TUR": "土耳其", "IRN": "伊朗", "EGY": "埃及",
    "ZAF": "南非", "NLD": "荷蘭", "CHE": "瑞士", "SWE": "瑞典", "NOR": "挪威", "POL": "波蘭", "UKR": "烏克蘭",
    "VNM": "越南", "THA": "泰國", "PHL": "菲律賓", "MYS": "馬來西亞", "SGP": "新加坡", "SAU": "沙烏地阿拉伯",
    "ARG": "阿根廷", "NGA": "奈及利亞", "GRC": "希臘", "PRT": "葡萄牙", "AUT": "奧地利", "BEL": "比利時",
}

CONTINENTS = {"Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America",
              "Seven seas (open ocean)"}


@lru_cache(None)
def _read_natural_earth_features(name: str) -> tuple:
    geojson_file_path = user_dirs.get_geo_dir_path() / f"{name}.geojson"
    if not geojson_file_path.exists():
        raise FileNotFoundError(f"{geojson_file_path} is missing: run `explainer-studio setup`, which downloads the "
                                "Natural Earth map data")
    return tuple(json.loads(geojson_file_path.read_text(encoding="utf-8"))["features"])


def _read_geojson_features(geojson) -> list[dict]:
    if isinstance(geojson, (str, Path)):
        geojson = json.loads(get_scene_context().resolve_path(geojson).read_text(encoding="utf-8"))
    if geojson.get("type") == "FeatureCollection":
        return list(geojson["features"])
    if geojson.get("type") == "Feature":
        return [geojson]
    return [{"type": "Feature", "properties": {}, "geometry": geojson}]


# ---------------------------------------------------------------------------
# Projections: degrees in, unitless plane out (scaled to the frame later)
# ---------------------------------------------------------------------------
_ROBINSON_X = np.array([1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427, 0.9216, 0.8962, 0.8679,
                        0.8350, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322])
_ROBINSON_Y = np.array([0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340, 0.4958, 0.5571, 0.6176,
                        0.6769, 0.7346, 0.7903, 0.8435, 0.8936, 0.9394, 0.9761, 1.0000])
_ROBINSON_LATITUDES = np.arange(0, 91, 5)


def _project(lon, lat, projection: str, center: tuple[float, float]):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon0, lat0 = center
    if projection == "equirect":     # equidistant cylindrical: true shape along the standard parallel lat0
        return (lon - lon0) * math.cos(math.radians(lat0)), lat
    if projection == "mercator":
        latitude_radians = np.radians(np.clip(lat, -85, 85))
        return np.radians(lon - lon0), np.log(np.tan(np.pi / 4 + latitude_radians / 2))
    if projection == "robinson":
        abs_latitude = np.abs(lat)
        x_factor = np.interp(abs_latitude, _ROBINSON_LATITUDES, _ROBINSON_X)
        y_factor = np.interp(abs_latitude, _ROBINSON_LATITUDES, _ROBINSON_Y)
        return 0.8487 * x_factor * np.radians(lon - lon0), 1.3523 * y_factor * np.sign(lat)
    if projection == "ortho":   # a globe seen from (lon0, lat0); far-side points are pushed onto the horizon
        latitude_radians, longitude_radians = np.radians(lat), np.radians(lon - lon0)
        center_latitude_radians = np.radians(lat0)
        x = np.cos(latitude_radians) * np.sin(longitude_radians)
        y = (np.cos(center_latitude_radians) * np.sin(latitude_radians)
             - np.sin(center_latitude_radians) * np.cos(latitude_radians) * np.cos(longitude_radians))
        is_far_side = (np.sin(center_latitude_radians) * np.sin(latitude_radians)
                       + np.cos(center_latitude_radians) * np.cos(latitude_radians) * np.cos(longitude_radians)) < 0
        radius = np.hypot(x, y)
        radius[radius == 0] = 1
        x = np.where(is_far_side, x / radius, x)
        y = np.where(is_far_side, y / radius, y)
        return x, y
    raise ValueError(f"unknown projection {projection!r}: equirect | mercator | robinson | ortho")


def _sample_great_circle(start, end, point_count: int = 48) -> np.ndarray:
    """point_count points (lon, lat) along the great circle from start to end."""
    def convert_lon_lat_to_unit_vector(lon, lat):
        longitude_radians, latitude_radians = math.radians(lon), math.radians(lat)
        return np.array([math.cos(latitude_radians) * math.cos(longitude_radians),
                         math.cos(latitude_radians) * math.sin(longitude_radians), math.sin(latitude_radians)])
    start_vector, end_vector = convert_lon_lat_to_unit_vector(*start), convert_lon_lat_to_unit_vector(*end)
    angle = math.acos(max(-1.0, min(1.0, float(start_vector @ end_vector))))
    if angle < 1e-9:
        return np.array([start, end], dtype=float)
    fractions = np.linspace(0, 1, point_count)
    points = np.array([(math.sin((1 - fraction) * angle) * start_vector + math.sin(fraction * angle) * end_vector)
                       / math.sin(angle) for fraction in fractions])
    return np.column_stack([np.degrees(np.arctan2(points[:, 1], points[:, 0])), np.degrees(np.arcsin(points[:, 2]))])


def _convert_lon_lat_to_unit_vectors(lon, lat) -> np.ndarray:
    longitude_radians, latitude_radians = np.radians(lon), np.radians(lat)
    return np.column_stack([np.cos(latitude_radians) * np.cos(longitude_radians),
                            np.cos(latitude_radians) * np.sin(longitude_radians), np.sin(latitude_radians)])


def _compute_ortho_basis(center):
    center_vector = _convert_lon_lat_to_unit_vectors([center[0]], [center[1]])[0]
    east = np.array([-math.sin(math.radians(center[0])), math.cos(math.radians(center[0])), 0.0])
    north = np.cross(center_vector, east)
    return center_vector, east, north


def _project_ortho_ring(coords, center) -> list[tuple[float, float]]:
    """Clip one lon/lat ring to the visible hemisphere and project it; where it leaves the visible side the boundary
    follows the horizon (the shorter way round) until it comes back."""
    ring = shapely_geometry.LineString(coords).segmentize(1.0).coords
    vectors = _convert_lon_lat_to_unit_vectors([point[0] for point in ring], [point[1] for point in ring])
    center_vector, east, north = _compute_ortho_basis(center)
    depths = vectors @ center_vector
    if (depths < 0).all():
        return []
    project_vector = lambda vector: (float(vector @ east), float(vector @ north))
    if (depths >= 0).all():
        return [project_vector(vector) for vector in vectors]
    points, pending_angle = [], None   # pending_angle: where the ring went behind the horizon
    for i in range(len(vectors) - 1):
        start, end, start_depth, end_depth = vectors[i], vectors[i + 1], depths[i], depths[i + 1]
        if start_depth >= 0:
            points.append(project_vector(start))
        if (start_depth >= 0) != (end_depth >= 0):
            fraction = start_depth / (start_depth - end_depth)
            crossing = start + fraction * (end - start)
            crossing = crossing - (crossing @ center_vector) * center_vector
            crossing = crossing / (np.linalg.norm(crossing) or 1)
            angle = math.atan2(crossing @ north, crossing @ east)
            if start_depth >= 0:                      # leaving the visible side
                pending_angle = angle
                points.append((math.cos(angle), math.sin(angle)))
            else:                            # coming back: walk the horizon from where we left
                if pending_angle is not None:
                    delta = (angle - pending_angle + math.pi) % (2 * math.pi) - math.pi
                    for step in np.linspace(0, 1, max(2, int(abs(delta) / 0.05)))[1:-1]:
                        theta = pending_angle + delta * step
                        points.append((math.cos(theta), math.sin(theta)))
                    pending_angle = None
                points.append((math.cos(angle), math.sin(angle)))
    return points if len(points) >= 3 else []


def _project_ortho_geometry(geometry, center):
    polygons = []
    for polygon in _list_polygons(geometry):
        ring = _project_ortho_ring(list(polygon.exterior.coords), center)
        if ring:
            projected = shapely_geometry.Polygon(ring).buffer(0)
            if not projected.is_empty:
                polygons.append(projected)
    if not polygons:
        return shapely_geometry.GeometryCollection()
    return shapely_geometry.MultiPolygon([part for piece in polygons for part in _list_polygons(piece)])


def _list_polygons(geometry) -> list:
    if isinstance(geometry, shapely_geometry.Polygon):
        return [geometry] if not geometry.is_empty else []
    if isinstance(geometry, (shapely_geometry.MultiPolygon, shapely_geometry.GeometryCollection)):
        return [polygon for part in geometry.geoms for polygon in _list_polygons(part)]
    return []


def _list_lines(geometry) -> list:
    if isinstance(geometry, shapely_geometry.LineString):
        return [geometry] if not geometry.is_empty else []
    if isinstance(geometry, (shapely_geometry.MultiLineString, shapely_geometry.GeometryCollection)):
        return [line for part in geometry.geoms for line in _list_lines(part)]
    if isinstance(geometry, shapely_geometry.Polygon):
        return [shapely_geometry.LineString(geometry.exterior.coords)]
    return []


class GeoMap(KeyedGroup):
    """A map whose regions are native shapes keyed by `key_property` (ISO code for countries: world["FRA"]).

    regions: codes, names (matched against key_property, NAME, NAME_EN) or continent names to draw; default all.
    bounds: (west, south, east, north) in degrees to crop to; the map is fitted to it (else to what is drawn).
    projection: "robinson" (world), "equirect", "mercator", "ortho" (a globe; center=(lon, lat)). "equirect" (the default
      with bounds or regions) keeps true shapes along its middle latitude, so a map far from the equator is not
      stretched east–west; pass center=(lon, lat) to choose that latitude.
    detail: "50m" (default, regional maps) or "110m" (lighter world maps). geojson/key_property: draw your own
      data instead.
    reference_map: another GeoMap whose projection and frame to reuse, so two maps line up for Transform.
    Parts: map[key] (a VGroup of polygons), .geometry_by_key_map[key] (projected shapely geometry),
    .properties_by_key_map[key]."""

    def __init__(self, regions=None, bounds=None, projection: str | None = None, center=None, detail: str = "50m",
                 geojson=None, key_property: str | None = None, width: float = 12.0, height: float = 6.6,
                 fill_color=GREY_E, fill_opacity: float = 1.0, stroke_color=GREY_B, stroke_width: float = 1.0,
                 reference_map: GeoMap | None = None, tolerance: float = 0.008):
        if reference_map is not None:
            projection, center = reference_map.projection, reference_map.center
            bounds = bounds if bounds is not None else reference_map.bounds
        self.projection = projection or ("robinson" if bounds is None and regions is None else "equirect")
        if center is None and self.projection == "equirect" and bounds is not None:
            center = (0.0, (bounds[1] + bounds[3]) / 2)   # a regional map keeps its shape at its middle latitude
        self.center = tuple(center) if center is not None else (0.0, 0.0)
        self.bounds = tuple(bounds) if bounds is not None else None
        if geojson is not None:
            features = _read_geojson_features(geojson)
        else:
            features = list(_read_natural_earth_features(f"ne_{detail}_admin_0_countries"))
        key_property = key_property or ("ADM0_A3" if geojson is None else None)
        wanted_names = (None if regions is None
                        else {str(region) for region in ([regions] if isinstance(regions, str) else regions)})
        clip_box = shapely_geometry.box(*self.bounds) if self.bounds else None

        geometry_by_key_map: dict[str, object] = {}
        self.properties_by_key_map: dict[str, dict] = {}
        for index, feature in enumerate(features):
            properties = feature.get("properties") or {}
            if key_property:
                region_key = str(properties.get(key_property, index))
            else:
                region_key = str(properties.get("NAME", properties.get("name", index)))
            region_names = {region_key, str(properties.get("NAME", "")), str(properties.get("NAME_EN", "")),
                            str(properties.get("CONTINENT", ""))}
            if wanted_names is not None and not (region_names & wanted_names):
                continue
            geometry = shapely_geometry.shape(feature["geometry"]) if feature.get("geometry") else None
            if geometry is None or geometry.is_empty:
                continue
            if clip_box is not None:
                geometry = geometry.intersection(clip_box)
                if geometry.is_empty:
                    continue
            if region_key in geometry_by_key_map:
                geometry = geometry_by_key_map[region_key].union(geometry)
            geometry_by_key_map[region_key] = geometry
            self.properties_by_key_map[region_key] = properties

        project_point = lambda x, y, z=None: _project(x, y, self.projection, self.center)
        if self.projection == "ortho":
            projected_geometry_by_key_map = {region_key: _project_ortho_geometry(geometry, self.center)
                                             for region_key, geometry in geometry_by_key_map.items()}
            projected_geometry_by_key_map = {region_key: geometry
                                             for region_key, geometry in projected_geometry_by_key_map.items()
                                             if not geometry.is_empty}
        else:
            projected_geometry_by_key_map = {region_key: _shapely_transform(project_point, geometry)
                                             for region_key, geometry in geometry_by_key_map.items()}
        if reference_map is not None:
            self._scale, self._offset = reference_map._scale, reference_map._offset
        else:
            if clip_box is not None and self.projection != "ortho":
                extent = _shapely_transform(project_point, clip_box.segmentize(1.0))
            elif self.projection == "ortho":
                extent = shapely_geometry.Point(0, 0).buffer(1.0)
            else:
                extent = shapely_geometry.GeometryCollection(list(projected_geometry_by_key_map.values()))
            x0, y0, x1, y1 = extent.bounds
            scale = min(width / max(x1 - x0, 1e-9), height / max(y1 - y0, 1e-9))
            self._scale, self._offset = scale, np.array([-(x0 + x1) / 2 * scale, -(y0 + y1) / 2 * scale])

        region_by_key_map: dict[str, VGroup] = {}
        self.geometry_by_key_map = {}
        for region_key, geometry in projected_geometry_by_key_map.items():
            geometry = _shapely_transform(lambda x, y, z=None: (np.asarray(x) * self._scale + self._offset[0],
                                                     np.asarray(y) * self._scale + self._offset[1]), geometry)
            geometry = geometry.simplify(tolerance, preserve_topology=True)
            self.geometry_by_key_map[region_key] = geometry
            polygons = VGroup()
            for polygon in _list_polygons(geometry):
                points = np.array(polygon.exterior.coords)
                if len(points) < 4:
                    continue
                mobject = VMobject()
                mobject.set_points_as_corners([[x, y, 0] for x, y in points])
                polygons.add(mobject)
            if len(polygons):
                polygons.set_fill(fill_color, fill_opacity).set_stroke(stroke_color, stroke_width)
                region_by_key_map[region_key] = polygons
        super().__init__(region_by_key_map)
        self.geometry_by_key_map = {region_key: self.geometry_by_key_map[region_key]
                                    for region_key in region_by_key_map}
        self._built_box = (np.array(self.get_corner(DL), dtype=float), np.array(self.get_corner(UR), dtype=float))

    # -- coordinates ---------------------------------------------------------
    def project(self, lon: float, lat: float) -> np.ndarray:
        """Frame point of a lon/lat (follows the map if it has been moved or scaled since)."""
        x, y = _project([lon], [lat], self.projection, self.center)
        built_point = np.array([x[0] * self._scale + self._offset[0], y[0] * self._scale + self._offset[1], 0])
        return self._convert_built_point_to_frame_point(built_point)

    def _convert_built_point_to_frame_point(self, point: np.ndarray) -> np.ndarray:
        """Construction coordinates → current frame, so overlays follow a map that was shifted or scaled later."""
        built_bottom_left, built_top_right = self._built_box
        bottom_left, top_right = self.get_corner(DL), self.get_corner(UR)
        built_width = (built_top_right - built_bottom_left)[0]
        scale = (top_right - bottom_left)[0] / built_width if built_width else 1.0
        return bottom_left + (point - built_bottom_left) * scale

    def format_region_name(self, key: str) -> str:
        """The region's everyday name in the episode's language (Traditional Chinese for zh, English otherwise)."""
        properties = self.properties_by_key_map.get(key, {})
        if get_scene_context().language_code.lower().startswith("zh"):
            return SHORT_NAME_ZHT_BY_CODE_MAP.get(key) or properties.get("NAME_ZHT") or properties.get("NAME") or key
        return properties.get("NAME_EN") or properties.get("NAME") or key

    # -- styling -------------------------------------------------------------
    def color_by_values(self, value_by_key_map: dict, low_color=BLUE_E, high_color=YELLOW,
                        min_value: float | None = None, max_value: float | None = None, is_log_scale: bool = False,
                        missing_color=GREY_E) -> GeoMap:
        """Choropleth: fill each region by its value (linear, or is_log_scale=True for populations and GDP)."""
        convert_value = (lambda value: math.log10(max(value, 1e-12))) if is_log_scale else float
        converted_value_by_key_map = {key: convert_value(value) for key, value in value_by_key_map.items()
                                      if value is not None}
        low_value = convert_value(min_value) if min_value is not None else min(converted_value_by_key_map.values())
        high_value = convert_value(max_value) if max_value is not None else max(converted_value_by_key_map.values())
        for key, part in self.items():
            if key in converted_value_by_key_map:
                fraction = (0.0 if high_value == low_value
                            else (converted_value_by_key_map[key] - low_value) / (high_value - low_value))
                part.set_fill(interpolate_color(low_color, high_color, min(1.0, max(0.0, fraction))), 1.0)
            else:
                part.set_fill(missing_color, 1.0)
        return self

    # -- overlays (returned, not added: the scene decides when they appear) --
    def get_region_label(self, key: str, text: str | None = None, font_size: float = SMALL_FONT_SIZE,
                         color=WHITE) -> Text:
        """The region's name at a point inside it (largest polygon), unless text= says otherwise."""
        geometry = self.geometry_by_key_map[key]
        polygons = _list_polygons(geometry)
        biggest = max(polygons, key=lambda polygon: polygon.area) if polygons else geometry
        representative_point = biggest.representative_point()
        label_text = Text(text or self.format_region_name(key), font_size=font_size).set_color(color)
        built_point = np.array([representative_point.x, representative_point.y, 0])
        return label_text.move_to(self._convert_built_point_to_frame_point(built_point))

    def get_marker(self, lon: float, lat: float, label: str = "", color=YELLOW, radius: float = 0.07,
               direction=RIGHT, font_size: float = SMALL_FONT_SIZE) -> VGroup:
        dot = Dot(self.project(lon, lat), radius=radius, fill_color=color)
        marker = VGroup(dot)
        if label:
            marker.add(Text(label, font_size=font_size).set_color(color).next_to(dot, direction, buff=0.1))
        marker.dot = dot
        return marker

    def get_route(self, points: list[tuple[float, float]], color=YELLOW, stroke_width: float = 4,
                  should_follow_great_circle: bool = True, has_tip: bool = True, tip_size: float = 0.18,
                  end_spacing: float = 0.12) -> VGroup:
        """A path through (lon, lat) points: trade routes, migrations, campaigns. ShowCreation draws it in travel order."""
        lon_lat_points = []
        for start, end in itertools.pairwise(points):
            segment = _sample_great_circle(start, end) if should_follow_great_circle else np.linspace(start, end, 24)
            lon_lat_points.extend(segment if not lon_lat_points else segment[1:])
        frame_points = [self.project(lon, lat) for lon, lat in lon_lat_points]
        destination = frame_points[-1]   # stop short of the destination so its marker stays visible
        stop_distance = end_spacing + (tip_size if has_tip else 0) * 0.5
        while len(frame_points) > 2 and np.linalg.norm(frame_points[-1] - destination) < stop_distance:
            frame_points.pop()
        path = VMobject().set_points_smoothly(frame_points).set_stroke(color, stroke_width).set_fill(opacity=0)
        route = VGroup(path)
        route.path = path
        if has_tip and len(frame_points) > 1:
            direction = frame_points[-1] - frame_points[-2]
            angle = math.atan2(direction[1], direction[0])
            tip = Triangle(fill_color=color, fill_opacity=1, stroke_width=0).set_height(tip_size)
            tip.rotate(angle - PI / 2).move_to(frame_points[-1])
            route.add(tip)
            route.tip = tip
        return route

    def get_rivers(self, color=BLUE_D, stroke_width: float = 1.5, min_rank: int = 6) -> VGroup:
        """Major rivers (Natural Earth scalerank <= min_rank; smaller = more important)."""
        return self._get_overlay("ne_50m_rivers_lake_centerlines", color, stroke_width, is_line_dataset=True,
                                 check_is_kept=lambda properties: (properties.get("scalerank") or 99) <= min_rank)

    def get_lakes(self, color=BLUE_E, min_rank: int = 3) -> VGroup:
        return self._get_overlay("ne_50m_lakes", color, 0, is_line_dataset=False,
                                 check_is_kept=lambda properties: (properties.get("scalerank") or 99) <= min_rank)

    def get_cities(self, names: list[str] | None = None, min_population: int = 5_000_000, color=WHITE,
                   radius: float = 0.05) -> KeyedGroup:
        """City dots keyed by English name (Natural Earth populated places); label them with .get_marker or
        Text(...)."""
        dot_by_name_map = {}
        for feature in _read_natural_earth_features("ne_50m_populated_places_simple"):
            properties = feature["properties"]
            is_unwanted = (properties["name"] not in names if names is not None
                           else (properties.get("pop_max") or 0) < min_population)
            if is_unwanted:
                continue
            lon, lat = properties["longitude"], properties["latitude"]
            if self.bounds and not (self.bounds[0] <= lon <= self.bounds[2] and self.bounds[1] <= lat <= self.bounds[3]):
                continue
            dot_by_name_map[properties["name"]] = Dot(self.project(lon, lat), radius=radius, fill_color=color)
        return KeyedGroup(dot_by_name_map)

    def get_sphere(self, fill_color=BLUE_E, stroke_color=GREY_B, stroke_width: float = 1.5) -> Circle:
        """The ocean disk behind a globe (ortho); add it before the map."""
        center = self._convert_built_point_to_frame_point(np.array([*self._offset, 0.0]))
        ocean_disk = Circle(radius=self._scale).move_to(center)
        ocean_disk.scale(self._convert_built_point_to_frame_point(np.array([1.0, 0, 0]))[0]
                         - self._convert_built_point_to_frame_point(np.array([0.0, 0, 0]))[0])
        return ocean_disk.set_fill(fill_color, 1).set_stroke(stroke_color, stroke_width)

    def get_crop_outline(self, color=GREY_C, stroke_width: float = 1.5) -> VMobject:
        """The outline of the cropped area (bounds=): makes the cut edges read as a deliberate map frame."""
        west, south, east, north = self.bounds or (-180, -90, 180, 90)
        ring = ([(west, y) for y in np.linspace(south, north, 40)]
                + [(x, north) for x in np.linspace(west, east, 80)]
                + [(east, y) for y in np.linspace(north, south, 40)]
                + [(x, south) for x in np.linspace(east, west, 80)])
        return self._get_line(ring, color, stroke_width)

    def get_graticule(self, step_degrees: float = 30, color=GREY_D, stroke_width: float = 0.8) -> VGroup:
        west, south, east, north = self.bounds or (-180, -90, 180, 90)
        graticule = VGroup()
        for lon in np.arange(math.ceil(west / step_degrees) * step_degrees, east + 1e-9, step_degrees):
            meridian = [(lon, lat) for lat in np.linspace(max(south, -89), min(north, 89), 60)]
            graticule.add(self._get_line(meridian, color, stroke_width))
        for lat in np.arange(math.ceil(south / step_degrees) * step_degrees, north + 1e-9, step_degrees):
            graticule.add(self._get_line([(lon, lat) for lon in np.linspace(west, east, 120)], color, stroke_width))
        return graticule

    def check_is_visible(self, lon: float, lat: float) -> bool:
        """False for points on the far side of a globe (ortho); always True for flat maps."""
        if self.projection != "ortho":
            return True
        return float(_convert_lon_lat_to_unit_vectors([lon], [lat])[0] @ _compute_ortho_basis(self.center)[0]) >= 0

    def _get_line(self, lon_lat_points, color, stroke_width) -> VMobject:
        """A polyline through lon/lat points; on a globe only the visible stretches are drawn."""
        line = VMobject().set_stroke(color, stroke_width).set_fill(opacity=0)
        visible_points = []
        for point in list(lon_lat_points) + [None]:
            if point is not None and self.check_is_visible(*point):
                visible_points.append(self.project(*point))
                continue
            if len(visible_points) >= 2:
                line.start_new_path(visible_points[0])
                line.add_points_as_corners(visible_points[1:])
            visible_points = []
        return line

    def _get_overlay(self, dataset: str, color, stroke_width, is_line_dataset: bool, check_is_kept) -> VGroup:
        clip_box = shapely_geometry.box(*self.bounds) if self.bounds else None
        overlay = VGroup()
        for feature in _read_natural_earth_features(dataset):
            if not check_is_kept(feature.get("properties") or {}):
                continue
            geometry = shapely_geometry.shape(feature["geometry"])
            if clip_box is not None:
                geometry = geometry.intersection(clip_box)
            for part in (_list_lines(geometry) if is_line_dataset else _list_polygons(geometry)):
                coords = part.coords if is_line_dataset else part.exterior.coords
                mobject = VMobject().set_points_as_corners([self.project(x, y) for x, y in coords])
                if is_line_dataset:
                    mobject.set_stroke(color, stroke_width).set_fill(opacity=0)
                else:
                    mobject.set_fill(color, 1).set_stroke(width=0)
                overlay.add(mobject)
        return overlay


def morph_map(old_map: GeoMap, new_map: GeoMap, keys=None, run_time: float = 2.0) -> Succession:
    """Borders changing over time. The regions of `new_map` fade in underneath (new land with no previous owner
    appears), then `old_map` fades out on top (unchanged land looks unchanged, land that changes hands shifts to the
    new owner's colour, land lost to nobody disappears). No shape interpolation, so nothing shrinks or flies. Build
    new_map with reference_map=old_map so both maps share a frame; afterwards the scene shows new_map's regions, so
    keep working with new_map."""
    keys_to_show = keys or list(new_map.keys())
    fade_ins = [FadeIn(new_map[key]) for key in keys_to_show]
    fade_outs = [FadeOut(old_map[key]) for key in (keys or old_map.keys())]
    return Succession(AnimationGroup(*fade_ins, run_time=run_time / 2),
                      AnimationGroup(*fade_outs, run_time=run_time / 2))


def merge_regions(country_codes_by_region_name_map: dict[str, list[str]], detail: str = "50m") -> dict:
    """A FeatureCollection whose features are unions of modern countries: {"羅馬帝國（約）": ["ITA", "FRA", ...]}.
    A quick approximation of a historical realm or a bloc when no historical GeoJSON is at hand; say on screen or in
    narration that the borders are modern approximations. Use: GeoMap(geojson=merge_regions({...}),
    key_property="NAME")."""
    from shapely.ops import unary_union
    geometry_by_code_map = {feature["properties"]["ADM0_A3"]: shapely_geometry.shape(feature["geometry"])
                            for feature in _read_natural_earth_features(f"ne_{detail}_admin_0_countries")}
    features = []
    for name, codes in country_codes_by_region_name_map.items():
        missing_codes = [code for code in codes if code not in geometry_by_code_map]
        if missing_codes:
            raise KeyError(f"unknown country codes {missing_codes}; use ISO alpha-3 codes (ADM0_A3), e.g. FRA, DEU, "
                           "TWN")
        geometry = shapely_geometry.mapping(unary_union([geometry_by_code_map[code] for code in codes]))
        features.append({"type": "Feature", "properties": {"NAME": name}, "geometry": geometry})
    return {"type": "FeatureCollection", "features": features}


def get_map(**kwargs) -> GeoMap:
    """Same as GeoMap(**kwargs); see its docstring."""
    return GeoMap(**kwargs)


def get_color_legend(low_label: str, high_label: str, low_color=BLUE_E, high_color=YELLOW, width: float = 3.0,
                     font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """A small gradient bar for a choropleth: [low label] ███ [high label]."""
    step_count = 24
    bar = VGroup(*[Rectangle(width=width / step_count, height=0.22, stroke_width=0,
                             fill_color=interpolate_color(low_color, high_color, i / (step_count - 1)),
                             fill_opacity=1) for i in range(step_count)])
    bar.arrange(RIGHT, buff=0)
    low_text = Text(low_label, font_size=font_size).set_color(GREY_A).next_to(bar, LEFT, buff=0.15)
    high_text = Text(high_label, font_size=font_size).set_color(GREY_A).next_to(bar, RIGHT, buff=0.15)
    return VGroup(low_text, bar, high_text)
