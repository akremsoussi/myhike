"""Calculs sur les chemins : longueur et dénivelé positif."""

import math
from collections.abc import Sequence

EARTH_RADIUS_M = 6_371_000
# Variation d'altitude ignorée : le bruit des altitudes GPS gonflerait le dénivelé.
ELEVATION_THRESHOLD_M = 5


def haversine_m(a: Sequence[float], b: Sequence[float]) -> float:
    """Distance à vol d'oiseau entre deux points [latitude, longitude, …]."""
    lat1, lng1, lat2, lng2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def length_m(points: Sequence[Sequence[float]]) -> int:
    return round(sum(haversine_m(a, b) for a, b in zip(points, points[1:], strict=False)))


def elevation_gain_m(altitudes: Sequence[float]) -> int:
    """Somme des montées, en ne comptant une variation qu'au-delà du seuil (hystérésis)."""
    if not altitudes:
        return 0
    gain = 0.0
    reference = altitudes[0]
    for altitude in altitudes[1:]:
        if altitude - reference >= ELEVATION_THRESHOLD_M:
            gain += altitude - reference
            reference = altitude
        elif reference - altitude >= ELEVATION_THRESHOLD_M:
            reference = altitude
    return round(gain)
