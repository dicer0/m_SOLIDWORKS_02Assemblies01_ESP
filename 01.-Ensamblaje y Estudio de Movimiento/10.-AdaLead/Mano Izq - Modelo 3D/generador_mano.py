"""Organic left hand built from the sketches inside Diego's 'Mano Izq..SLDPRT' (real mm).

Sources (extracted from the SLDPRT feature stream):
  * Croquis6 front outline (sketch x = SW Y, sketch y = SW Z)
  * side profile sketch (sketch x + 45.8 = SW Z, sketch y = SW X; dorsal side is -X)
  * Recubrir1 wrist ellipses (~51 x 38 mm), wrist from SW Z = -15 to 25

Working frame (same as hand_sdf.py): Xm = -SW_Y (thumb +Xm), Ym = SW_X (dorsal -Ym), Z = SW_Z.
The exported STL is written back in the SolidWorks frame so it lands on top of Croquis6/Recubrir1.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
import trimesh
from scipy.interpolate import splev, splprep
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString, Point, Polygon
from skimage import measure

parser = argparse.ArgumentParser()
parser.add_argument("groups_json")
parser.add_argument("out_dir")
parser.add_argument("--voxel", type=float, default=0.4)
parser.add_argument("--pad-scale", type=float, default=0.0)
args = parser.parse_args()
out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

groups = {g["byte"]: np.array(g["points"]) * 1000.0 for g in json.load(open(args.groups_json))}

# ------------------------------------------------------------------ front outline (Croquis6)
OUTLINE_ORDER = [102910, 104896, 105972, 107826, 109022, 111162, 112176, 113978, 114772, 115948]
chain = [groups[OUTLINE_ORDER[0]]]
for key in OUTLINE_ORDER[1:]:
    pts = groups[key]
    if np.linalg.norm(pts[-1] - chain[-1][-1]) < np.linalg.norm(pts[0] - chain[-1][-1]):
        pts = pts[::-1]
    chain.append(pts[1:] if np.linalg.norm(pts[0] - chain[-1][-1]) < 1e-6 else pts)
sketch_outline = np.vstack(chain)
# drop exact duplicates, close along the wrist line (y = 25)
keep = np.r_[True, np.linalg.norm(np.diff(sketch_outline, axis=0), axis=1) > 1e-6]
sketch_outline = sketch_outline[keep]
outline_m = np.column_stack([-sketch_outline[:, 0], sketch_outline[:, 1]])  # (Xm, Z)


def smooth_closed(points, samples=900, smoothing=0.0):
    pts = np.vstack([points, points[:1]])
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=smoothing, per=True)
    x, z = splev(np.linspace(0, 1, samples, endpoint=False), tck)
    return np.column_stack([x, z])


outline_xz = Polygon(smooth_closed(outline_m, smoothing=len(outline_m) * 0.15)).buffer(0)
WRIST_TOP = 25.0
# extend the outline straight down over the wrist so the palm field is defined there too
_full = outline_xz.union(Polygon([(-25.75, -20), (25.75, -20), (25.75, 10), (29.5, 24), (33.5, 34), (35.6, 38),
                                  (-32.0, 38), (-30.5, 32), (-28.0, 22), (-25.75, 10)]))
# round the wrist corners only; closing the whole outline would glue the fingers together
_lower = _full.intersection(Polygon([(-200, -40), (200, -40), (200, 52), (-200, 52)])).buffer(2.5).buffer(-2.5)
_upper = _full.intersection(Polygon([(-200, 48), (200, 48), (200, 300), (-200, 300)]))
outline_xz = _lower.union(_upper).buffer(0)


def m(xs, z):
    return np.array([-xs, z])


WEB_PINKY_RING = m(29.9, 87.0)
WEB_RING_MIDDLE = m(12.3, 95.4)
WEB_MIDDLE_INDEX = m(-5.0, 96.0)
WEB_INDEX_THUMB = m(-31.0, 71.5)
PINKY_OUTER_BASE = m(39.3, 71.0)
PINKY_CAP_POINT = m(47.0, 84.5)  # palm cap edge, pushed up along the pinky
INDEX_OUTER_BASE = m(-24.0, 80.0)
THUMB_ROOT_OUTER = m(-44.6, 55.3)  # where the thumb leaves the palm outline
THUMB_OUTER_BASE = m(-49.5, 72.0)  # palm cap edge, pushed across the thumb root
TIPS = {
    "pinky": m(53.24, 113.38), "ring": m(32.81, 141.42), "middle": m(5.75, 152.74), "index": m(-13.68, 147.2),
}
THUMB_TIP = m(-55.5, 100.8)

palm_cut = Polygon([
    (-90, -30), (-90, PINKY_OUTER_BASE[1] + 25), tuple(PINKY_OUTER_BASE), tuple(WEB_PINKY_RING + [0, 1.5]),
    tuple(WEB_RING_MIDDLE + [0, 1.5]), tuple(WEB_MIDDLE_INDEX + [0, 1.5]), tuple(INDEX_OUTER_BASE),
    tuple(WEB_INDEX_THUMB), tuple(THUMB_OUTER_BASE), (90, THUMB_OUTER_BASE[1] - 10), (90, -30),
])
palm_xz = outline_xz.intersection(palm_cut).buffer(-4).buffer(4)
pieces = list(getattr(outline_xz.difference(palm_cut), "geoms", [outline_xz.difference(palm_cut)]))


def region_for(tip):
    return min(pieces, key=lambda g: (round(g.distance(Point(tip)), 3), -g.area))


# ------------------------------------------------------------------ side profile (thickness)
SIDE_ORDER = [169948, 171646, 170662, 172810, 173994, 174688, 175314]
side_chain = [groups[SIDE_ORDER[0]]]
for key in SIDE_ORDER[1:]:
    pts = groups[key]
    if np.linalg.norm(pts[-1] - side_chain[-1][-1]) < np.linalg.norm(pts[0] - side_chain[-1][-1]):
        pts = pts[::-1]
    side_chain.append(pts)
side = np.vstack(side_chain)
side_poly = Polygon(np.column_stack([side[:, 1], side[:, 0] + 45.8])).buffer(0)  # (Ym, Z)
z_samples = np.arange(WRIST_TOP, 152.5, 0.5)
dorsal_raw, palmar_raw = [], []
for z in z_samples:
    cut = LineString([(-80, z), (80, z)]).intersection(side_poly)
    if cut.is_empty:
        dorsal_raw.append(np.nan)
        palmar_raw.append(np.nan)
        continue
    xs = [c[0] for g in getattr(cut, "geoms", [cut]) for c in g.coords]
    dorsal_raw.append(min(xs))
    palmar_raw.append(max(xs))
dorsal_raw = np.array(dorsal_raw)
palmar_raw = np.array(palmar_raw)
valid = ~np.isnan(dorsal_raw)
z_samples, dorsal_raw, palmar_raw = z_samples[valid], dorsal_raw[valid], palmar_raw[valid]
palm_zone = np.clip((z_samples - 92.0) / 12.0, 0.0, 1.0)
DORSAL = gaussian_filter1d(dorsal_raw, 18, mode='nearest') * (1 - palm_zone) + gaussian_filter1d(dorsal_raw, 6, mode='nearest') * palm_zone
PALMAR_FULL = gaussian_filter1d(palmar_raw, 6, mode='nearest')
PALMAR_PALM = gaussian_filter1d(np.minimum(palmar_raw, 15.5), 16, mode='nearest')  # thenar bulge comes from its own pad


def dorsal(z):
    return np.interp(z, z_samples, DORSAL)


# palm-side line of the palm itself (pads come on top): thinner lower palm, fuller under the knuckles
from scipy.interpolate import PchipInterpolator
_PALMAR_TARGET = PchipInterpolator([25, 32, 40, 50, 60, 70, 80, 90, 100, 152],
                                   [12.0, 12.3, 13.0, 13.0, 12.0, 10.8, 8.8, 6.6, 3.8, -8.0])


def palmar_palm(z):
    return _PALMAR_TARGET(np.clip(z, 25, 152))


def palmar_full(z):
    return np.interp(z, z_samples, PALMAR_FULL)


# ------------------------------------------------------------------ SDF helpers
def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def round_cone(p, a, b, r1, r2, flatten):
    axis = b - a
    length = np.linalg.norm(axis)
    e_u = axis / length
    e_n = np.array([0.0, 1.0, 0.0]) - e_u[1] * e_u
    e_n /= np.linalg.norm(e_n)
    e_v = np.cross(e_u, e_n)
    d = p - a
    du, dv, dn = d @ e_u, d @ e_v, (d @ e_n) * flatten
    q_r = np.sqrt(dv * dv + dn * dn)
    rr = r1 - r2
    l2 = length * length
    a2 = l2 - rr * rr
    y = du * length
    z = y - l2
    x2 = (q_r * l2) ** 2
    y2, z2 = y * y * l2, z * z * l2
    k = np.sign(rr) * rr * rr * x2
    out = (np.sqrt(np.maximum(x2 * a2 / l2, 0)) + y * rr) / l2 - r1
    cap_b = np.sign(z) * a2 * z2 > k
    cap_a = np.sign(y) * a2 * y2 < k
    out = np.where(cap_b, np.sqrt(x2 + z2) / l2 - r2, out)
    return np.where(cap_a & ~cap_b, np.sqrt(x2 + y2) / l2 - r1, out)


def ellipsoid(p, center, radii):
    q = (p - center) / radii
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / radii, axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def oriented_ellipsoid(p, center, axis_u, radii):
    e_u = axis_u / np.linalg.norm(axis_u)
    e_n = np.array([0.0, 1.0, 0.0]) - e_u[1] * e_u
    e_n /= np.linalg.norm(e_n)
    e_v = np.cross(e_u, e_n)
    d = p - center
    return ellipsoid(np.stack([d @ e_u, d @ e_v, d @ e_n], axis=-1), np.zeros(3), np.asarray(radii, float))


def chord(region, point, across):
    line = LineString([point - 40 * across, point + 40 * across]).intersection(region)
    if line.is_empty:
        return None
    coords = np.array([c for g in getattr(line, "geoms", [line]) for c in g.coords])
    offsets = (coords - point) @ across
    return offsets.min(), offsets.max()


# ------------------------------------------------------------------ fingers
FINGER_WEBS = {
    "pinky": (PINKY_OUTER_BASE, WEB_PINKY_RING), "ring": (WEB_PINKY_RING, WEB_RING_MIDDLE),
    "middle": (WEB_RING_MIDDLE, WEB_MIDDLE_INDEX), "index": (WEB_MIDDLE_INDEX, INDEX_OUTER_BASE),
}
middle_web_z = ((WEB_RING_MIDDLE + WEB_MIDDLE_INDEX) / 2)[1]
middle_tip_z = TIPS["middle"][1]


def finger_thickness(frac):
    """Thickness of the finger at a fraction of its length, from the side profile (middle finger range)."""
    z = middle_web_z + frac * (middle_tip_z - middle_web_z)
    return palmar_full(z) - dorsal(z), dorsal(z)


fingers = {}
for name, (a, b) in FINGER_WEBS.items():
    tip = TIPS[name]
    web = (a + b) / 2
    region = region_for(tip)
    axis = tip - web
    u2 = axis / np.linalg.norm(axis)
    across = np.array([u2[1], -u2[0]])
    length = np.linalg.norm(axis)
    halves, centers = [], []
    for frac in (0.06, 0.4, 0.7, 0.9):
        point = web + u2 * length * frac
        c = chord(region, point, across)
        if c is None:
            c = (-6.0, 6.0)
        halves.append((c[1] - c[0]) / 2)
        centers.append(point + across * (c[0] + c[1]) / 2)
    halves = np.array(halves)
    # root sits inside the palm, a bit wider than where the finger outline starts
    halves[0] = min(np.linalg.norm(b - a) / 2 * 0.95, halves[1] * 1.18)
    base_center = centers[0] - u2 * 10.0
    tip_center = tip - u2 * halves[3]
    fingers[name] = {"u": u2, "half": halves, "base": base_center, "mid": centers[1], "tip": tip_center, "tip_point": tip}

middle_width = fingers["middle"]["half"][1]
for name, f in fingers.items():
    ratio = (f["half"][1] / middle_width) ** 0.8
    thickness_pts, dorsal_pts = zip(*(finger_thickness(fr) for fr in (0.0, 0.4, 0.7, 0.9)))
    f["t_half"] = np.array(thickness_pts) / 2 * ratio
    # back of every finger follows the dorsal line of the side view
    f["center_y"] = np.array(dorsal_pts) + f["t_half"]
    base3 = np.array([f["base"][0], f["center_y"][0], f["base"][1]])
    total = np.linalg.norm(f["tip"] - f["base"])
    u3 = np.array([f["u"][0], 0.0, f["u"][1]])
    joints = [base3]
    for frac, idx in ((0.47, 1), (0.74, 2), (1.0, 3)):
        p = f["base"] + f["u"] * total * frac
        joints.append(np.array([p[0], f["center_y"][idx], p[1]]))
    f["points"] = joints
    f["total"] = total

# ------------------------------------------------------------------ thumb
thumb_mcp = (WEB_INDEX_THUMB + THUMB_ROOT_OUTER) / 2
thumb_u = (THUMB_TIP - thumb_mcp) / np.linalg.norm(THUMB_TIP - thumb_mcp)
thumb_len = np.linalg.norm(THUMB_TIP - thumb_mcp)
thumb_region = region_for(THUMB_TIP).convex_hull
thumb_across = np.array([thumb_u[1], -thumb_u[0]])
thumb_halves = []
for frac in (0.2, 0.55, 0.85):
    c = chord(thumb_region, thumb_mcp + thumb_u * thumb_len * frac, thumb_across)
    thumb_halves.append((c[1] - c[0]) / 2 if c else 7.0)
thumb_halves = np.array(thumb_halves)
THUMB_Y = 3.0
thumb_cmc3 = np.array([thumb_mcp[0] - 12.0, 6.0, 34.0])
thumb_mcp3 = np.array([thumb_mcp[0], THUMB_Y, thumb_mcp[1]])
thumb_ip3 = np.array([*(thumb_mcp + thumb_u * thumb_len * 0.55)[:1], THUMB_Y, (thumb_mcp + thumb_u * thumb_len * 0.55)[1]])
thumb_tip3 = np.array([THUMB_TIP[0], THUMB_Y + 1.0, THUMB_TIP[1]]) - np.array([thumb_u[0], 0, thumb_u[1]]) * thumb_halves[2]

_edge = LineString([(-90, 52.0), (0, 52.0)]).intersection(outline_xz)
HYPO_X = min(c[0] for g in getattr(_edge, 'geoms', [_edge]) for c in g.coords) + 12.0

# ------------------------------------------------------------------ wrist (Recubrir1)
WRIST_HALF_W, WRIST_HALF_T, WRIST_BOTTOM = 25.5, 19.0, -15.0

# ------------------------------------------------------------------ grid
V = args.voxel
gx = np.arange(-70.0, 72.0, V)
gy = np.arange(-27.0, 32.0, V)
gz = np.arange(WRIST_BOTTOM - 2.0, 158.0, V)
print(f"grid {len(gx)} x {len(gy)} x {len(gz)} = {len(gx) * len(gy) * len(gz) / 1e6:.1f} M voxels")
XX, ZZ = np.meshgrid(gx, gz, indexing="ij")
pts2d = shapely.points(XX.ravel(), ZZ.ravel())
d_boundary = shapely.distance(pts2d, palm_xz.boundary).reshape(XX.shape)
inside = shapely.contains_xy(palm_xz, XX.ravel(), ZZ.ravel()).reshape(XX.shape)
palm_2d = np.where(inside, -d_boundary, d_boundary).astype(np.float32)
d_outer = shapely.distance(pts2d, outline_xz.boundary).reshape(XX.shape)
in_outer = shapely.contains_xy(outline_xz, XX.ravel(), ZZ.ravel()).reshape(XX.shape)
outer_2d = np.where(in_outer, -d_outer, d_outer).astype(np.float32)
cut_region = palm_cut.intersection(Polygon([(-200, -40), (200, -40), (200, 300), (-200, 300)]))
d_cut = shapely.distance(pts2d, cut_region.boundary).reshape(XX.shape)
in_cut = shapely.contains_xy(cut_region, XX.ravel(), ZZ.ravel()).reshape(XX.shape)
cut_2d = np.where(in_cut, -d_cut, d_cut).astype(np.float32)
palm_mid_x = (palm_xz.bounds[0] + palm_xz.bounds[2]) / 2

def smax(a, b, k):
    return -smin(-a, -b, k)


def chaikin_open(points, iterations=4):
    pts = np.asarray(points, dtype=float)
    for _ in range(iterations):
        new = [pts[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            new += [0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]
        new.append(pts[-1])
        pts = np.array(new)
    return pts


def frame_for(axis, toward):
    """Orthonormal (e_u along axis, e_v across, e_n pointing to `toward` side, made perpendicular to the axis)."""
    e_u = axis / np.linalg.norm(axis)
    e_n = toward - (toward @ e_u) * e_u
    e_n /= np.linalg.norm(e_n)
    return e_u, np.cross(e_n, e_u), e_n


def add_nail(finger, P, start, end, half_w, side_dir, tip_radius, nail_length_factor=1.25):
    """Raised nail plate (0.5 mm) following the finger surface, with a nail-fold groove on the proximal/lateral border."""
    e_u, e_v, e_n = frame_for(end - start, side_dir)
    length = np.linalg.norm(end - start)
    d = P - start
    du, dv, dn = d @ e_u, d @ e_v, d @ e_n
    u1 = length + tip_radius * 0.35
    u0 = u1 - nail_length_factor * half_w  # ~0.62 x finger width, like the trimmed nails in the photo
    uc, a, b = (u0 + u1) / 2, (u1 - u0) / 2, half_w * 0.72
    exponent = 3.0
    shape = (np.abs((du - uc) / a) ** exponent + np.abs(dv / b) ** exponent) ** (1 / exponent)
    footprint = (shape - 1.0) * min(a, b)
    footprint = np.maximum(footprint, 0.2 * tip_radius - dn)  # only on the nail side of the finger
    plate = np.maximum(finger - 0.22, footprint)
    cuticle = np.maximum(np.abs(footprint - 0.15) - 0.3, -(finger + 0.3))
    cuticle = np.maximum(cuticle, du - (uc - 0.35 * a))  # only along the proximal (cuticle) edge
    finger = smax(finger, -cuticle, 0.25)
    return smin(finger, plate, 0.3)


def crease_field(points_xz):
    line = LineString(chaikin_open(points_xz))
    grid_points = shapely.points(XX.ravel(), ZZ.ravel())
    distance = shapely.distance(grid_points, line).reshape(XX.shape)
    along = (shapely.line_locate_point(line, grid_points) / line.length).reshape(XX.shape)
    taper = smoothstep(along / 0.22) * smoothstep((1.0 - along) / 0.22)
    return distance.astype(np.float32), taper.astype(np.float32)


# palmar creases (work frame Xm, Z): heart line, head line, life line
CREASES = [
    ([(-29, 73), (-22, 75), (-14, 78), (-6, 82.5), (2, 87.5)], 1.0, 0.45),
    ([(35, 70), (22, 67), (8, 63), (-8, 60), (-25, 57)], 0.95, 0.45),
    ([(33, 69), (25, 62), (18, 54), (13, 44), (10, 35), (10, 30)], 1.1, 0.5),
]
crease_maps = [(crease_field(pts), width, depth) for pts, width, depth in CREASES]

# pinky root pulled slightly into the palm so it does not stick out of the ulnar edge
palm_centroid = np.array(palm_xz.centroid.coords[0])
for name, f in fingers.items():
    f["half"][0] = min(f["half"][0], f["half"][1] * (0.98 if name == "pinky" else 1.12))
pinky = fingers["pinky"]
shift = palm_centroid - pinky["points"][0][[0, 2]]
shift = shift / np.linalg.norm(shift) * 4.0 - pinky["u"] * 4.0
pinky["points"][0] = pinky["points"][0] + np.array([shift[0], 0.0, shift[1]])

def dorsal_surface(x, z):
    return dorsal(z) + 0.0035 * (x - palm_mid_x) ** 2 * (1 - 0.6 * smoothstep((z - 70) / 25))


# extensor tendons: faint ridges on the back of the hand, fanning from the wrist to each knuckle
TENDONS = []
for name, f in fingers.items():
    knuckle_xz = f["points"][0][[0, 2]] - f["u"] * 5.0
    wrist_xz = np.array([palm_mid_x + (knuckle_xz[0] - palm_mid_x) * 0.5, 40.0])
    r_start, r_end, proud = 0.9, 1.5, 0.45
    start = np.array([wrist_xz[0], dorsal_surface(wrist_xz[0], wrist_xz[1]) + r_start - proud * 0.4, wrist_xz[1]])
    end = np.array([knuckle_xz[0], dorsal_surface(knuckle_xz[0], knuckle_xz[1]) + r_end - proud, knuckle_xz[1]])
    TENDONS.append((start, end, r_start, r_end))

TENDON_HEIGHT, TENDON_WIDTH = 0.4, 4.2
tendon_maps = []
for t_start, t_end, _, _ in TENDONS:
    a2, b2 = t_start[[0, 2]], t_end[[0, 2]]
    seg = b2 - a2
    t = np.clip(((XX - a2[0]) * seg[0] + (ZZ - a2[1]) * seg[1]) / (seg @ seg), 0.0, 1.0)
    dist = np.hypot(XX - (a2[0] + t * seg[0]), ZZ - (a2[1] + t * seg[1]))
    tendon_maps.append((dist.astype(np.float32), t.astype(np.float32)))

_root_levels = []
for _f in fingers.values():
    _flat = float(np.mean(_f["half"][1:]) / np.mean(_f["t_half"][1:]))
    _root_levels.append(_f["points"][0][1] + _f["half"][0] / _flat)
FINGER_ROOT_PALMAR = float(np.mean(_root_levels)) + 4.5
TOP_TAPER = 14.0
BLUR_MM = 3.0
print("finger root palmar level", round(FINGER_ROOT_PALMAR, 2))
EDGE_R = 13.0  # in-plane radius of the rounded palm border (lens-shaped section instead of a slab)
_pf = fingers["pinky"]
PINKY_FLATTEN = float(np.mean(_pf["half"][1:]) / np.mean(_pf["t_half"][1:]))
_pu3 = np.array([_pf["u"][0], 0.0, _pf["u"][1]])
PINKY_MC_END = _pf["points"][0].copy()
PINKY_MC_START = PINKY_MC_END - _pu3 * 28.0
PINKY_MC_START[1] = (palmar_palm(PINKY_MC_START[2]) + dorsal(PINKY_MC_START[2])) / 2
PINKY_MC_R0, PINKY_MC_R1 = _pf["half"][0] * 0.9, _pf["half"][0] * 1.0
FINGER_PADS = []
for _name, _f in fingers.items():
    _base = _f["points"][0][[0, 2]] + _f["u"] * 1.5
    if _name == "pinky":
        _base = _base + (palm_centroid - _base) / np.linalg.norm(palm_centroid - _base) * 3.5
    _radius_x = _f["half"][0] * (0.85 if _name == "pinky" else 1.2)
    FINGER_PADS.append(np.array([_base[0], palmar_palm(_base[1]) - 1.8, _base[1]]))
FINGER_PADS.sort(key=lambda c: c[0])
PAD_R, PAD_DEPTH = 7.0, 2.6
DIGIT_PADS = []
for _name, _f in fingers.items():
    _c2 = _f["base"] + _f["u"] * 7.0
    _scale = 0.85 if _name == "pinky" else 1.0
    _center = np.array([_c2[0], FINGER_ROOT_PALMAR - 3.6, _c2[1]])
    _axis = np.array([_f["u"][0], 0.0, _f["u"][1]])
    DIGIT_PADS.append((_center, _axis, (6.5 * _scale, _f["half"][0] * 0.95 * _scale, 2.6 * _scale)))
volume = np.empty((len(gx), len(gy), len(gz)), dtype=np.float32)
slab = 24
for k0 in range(0, len(gz), slab):
    k1 = min(k0 + slab, len(gz))
    X, Y, Z = np.meshgrid(gx, gy, gz[k0:k1], indexing="ij")
    P = np.stack([X, Y, Z], axis=-1)
    zc = np.clip(Z, WRIST_TOP, 152.0)
    d_line = dorsal(zc)
    p_line = palmar_palm(zc)
    near_top = 1.0 - smoothstep(-cut_2d[:, None, k0:k1] / TOP_TAPER)
    p_line = p_line - np.maximum(p_line - FINGER_ROOT_PALMAR, 0.0) * near_top
    # pinky side of the lower palm: slimmer on the palm side (no hypothenar bulge)
    ulnar_lower = smoothstep((palm_mid_x - 8.0 - X) / 22.0) * (1.0 - smoothstep((Z - 80.0) / 12.0))
    p_line = p_line - 4.0 * ulnar_lower
    half_t = (p_line - d_line) / 2
    center = (p_line + d_line) / 2 + 0.0035 * (X - palm_mid_x) ** 2 * (1 - 0.6 * smoothstep((Z - 70) / 25))
    u = outer_2d[:, None, k0:k1]
    ulnar_w = smoothstep((palm_mid_x - 12.0 - X) / 18.0)
    edge_r = EDGE_R + 7.0 * ulnar_w
    lens = np.sqrt((np.maximum(u + edge_r, 0) / edge_r) ** 2 + ((Y - center) / half_t) ** 2) - 1.0
    cut_r = 9.0 + 5.0 * ulnar_w
    ucut = cut_2d[:, None, k0:k1]
    cut_lens = np.sqrt((np.maximum(ucut + cut_r, 0) / cut_r) ** 2 + ((Y - center) / half_t) ** 2) - 1.0
    palm = smax(lens * np.minimum(half_t, edge_r), cut_lens * np.minimum(half_t, cut_r), 4.0)
    # wrist: rounded-rectangle section, slight waist above the crease, forearm widening below
    waist = 1.0 - 0.035 * np.exp(-(((Z - 10.0) / 12.0) ** 2))
    widen = 1.0 + 0.035 * smoothstep(-Z / 30.0)
    a = WRIST_HALF_W * waist * widen
    b_dorsal = WRIST_HALF_T * waist * widen
    b_palm = np.interp(Z, [-15.0, 0.0, 10.0, 20.0, 30.0], [19.0, 18.4, 15.6, 13.0, 12.4]) * widen
    b = b_dorsal + (b_palm - b_dorsal) * smoothstep(Y / 8.0 + 0.5)
    n_exp = 2.4
    q = (np.abs(X / a) ** n_exp + np.abs(Y / b) ** n_exp) ** (1 / n_exp)
    wrist = (q - 1.0) * 14.0
    blend = smoothstep((Z - 8.0) / 36.0)
    body = wrist * (1 - blend) + palm * blend
    body = np.maximum(body, -(Z - WRIST_BOTTOM))
    # thenar (thumb base) and hypothenar pads on the palm side
    body = smin(body, ellipsoid(P, np.array([22.0, 7.5, 42.0]), np.array([14.0, 10.0, 18.0])), 6.0)
    # pinky metacarpal: the ulnar border of the hand flows into the pinky instead of a shoulder
    body = smin(body, round_cone(P, PINKY_MC_START, PINKY_MC_END, PINKY_MC_R0, PINKY_MC_R1, PINKY_FLATTEN), 8.0)
    # palm pads under each finger root (fill the notch on the palm side at the finger bases)
    dorsal_mask = smoothstep((center - Y) / 3.0)
    for dist2d, along in tendon_maps:
        d2 = dist2d[:, None, k0:k1]
        s = along[:, None, k0:k1]
        fade = smoothstep(s / 0.45) * smoothstep((1.0 - s) / 0.2)
        raise_ = TENDON_HEIGHT * np.clip(1.0 - (d2 / TENDON_WIDTH) ** 2, 0.0, 1.0) * fade * dorsal_mask
        body = body - raise_
    for name, f in fingers.items():
        pts, half, t_half = f["points"], f["half"], f["t_half"]
        finger = None
        flatten = float(np.mean(half[1:]) / np.mean(t_half[1:]))
        for i in range(3):
            seg = round_cone(P, pts[i], pts[i + 1], half[i], half[i + 1], flatten)
            finger = seg if finger is None else smin(finger, seg, 0.8)
        knuckle = pts[0] + np.array([0.0, -t_half[0] * 0.6, 0.0]) + np.array([f["u"][0], 0, f["u"][1]]) * 3.0
        knuckle_scale = 0.5 if name == "pinky" else 1.0
        finger = smin(finger, ellipsoid(P, knuckle, np.array([half[0] * 0.55, 3.0, 4.5]) * knuckle_scale), 2.0)
        finger = add_nail(finger, P, pts[2], pts[3], half[3], np.array([0.0, -1.0, 0.0]), half[3])
        body = smin(body, finger, 5.0)
    thumb = round_cone(P, thumb_cmc3, thumb_mcp3, 10.0, thumb_halves[0], 1.12)
    thumb = smin(thumb, round_cone(P, thumb_mcp3, thumb_ip3, thumb_halves[0], thumb_halves[1], 1.15), 1.2)
    thumb = smin(thumb, round_cone(P, thumb_ip3, thumb_tip3, thumb_halves[1], thumb_halves[2], 1.2), 1.2)
    # thumb nail faces back and slightly away from the palm (the thumb is rotated ~45 degrees)
    away = np.array([thumb_across[0], 0.0, thumb_across[1]])
    if away @ np.array([1.0, 0.0, 0.0]) < 0:
        away = -away
    thumb_nail_dir = np.array([0.0, -1.0, 0.0]) + 0.7 * away
    thumb = add_nail(thumb, P, thumb_ip3, thumb_tip3, thumb_halves[2], thumb_nail_dir, thumb_halves[2], 1.4)
    body = smin(body, thumb, 11.0)
    if args.pad_scale > 0:
        for pad_center, pad_axis, pad_radii in DIGIT_PADS:
            body = smin(body, oriented_ellipsoid(P, pad_center, pad_axis, np.asarray(pad_radii) * args.pad_scale), 4.0)
    volume[:, :, k0:k1] = body
    print(f"  slab {k0}/{len(gz)}", flush=True)

from scipy.ndimage import gaussian_filter
print("smoothing palm top...", flush=True)
blurred = gaussian_filter(volume, sigma=BLUR_MM / V)
for k0 in range(0, len(gz), slab):
    k1 = min(k0 + slab, len(gz))
    X, Y, Z = np.meshgrid(gx, gy, gz[k0:k1], indexing="ij")
    zone_z = smoothstep((Z - 52.0) / 12.0) * (1.0 - smoothstep((Z - 104.0) / 8.0))
    palm_side = smoothstep((Y + 4.0) / 6.0)
    ulnar_side = smoothstep((palm_mid_x - 22.0 - X) / 10.0)
    palm_only = 1.0 - smoothstep((cut_2d[:, None, k0:k1] + 3.0) / 8.0)  # keep the fingers out of the blur
    junction = np.exp(-((cut_2d[:, None, k0:k1] + 1.0) / 7.0) ** 2)
    zone_j = smoothstep((Z - 60.0) / 10.0) * (1.0 - smoothstep((Z - 112.0) / 8.0))
    weight = np.maximum(zone_z * np.maximum(palm_side, ulnar_side) * palm_only, zone_j * junction * palm_side)
    body = volume[:, :, k0:k1] * (1.0 - weight) + blurred[:, :, k0:k1] * weight
    # palm creases: V grooves on the palmar side only (after smoothing so they stay crisp)
    for (dist2d, taper2d), width, depth in crease_maps:
        d2 = dist2d[:, None, k0:k1]
        taper = taper2d[:, None, k0:k1]
        groove = d2 - width * taper * np.clip(1.0 + body / (depth * np.maximum(taper, 0.05)), 0.0, 1.0)
        groove = np.maximum(groove, -(Y - 1.0))
        body = smax(body, -groove, 0.45)
    volume[:, :, k0:k1] = body
del blurred

verts, faces, _, _ = measure.marching_cubes(volume, level=0.0, spacing=(V, V, V))
verts += np.array([gx[0], gy[0], gz[0]])
mesh = trimesh.Trimesh(verts, faces, process=True)
mesh = max(mesh.split(only_watertight=False), key=lambda b: len(b.faces))
trimesh.repair.fix_normals(mesh)
mesh.export(out_dir / "hand_work_frame.stl")
# back to the SolidWorks frame: SW_X = Ym, SW_Y = -Xm, SW_Z = Z
to_sw = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
mesh_sw = mesh.copy()
mesh_sw.apply_transform(to_sw)
mesh_sw.export(out_dir / "hand_sw_frame.stl")
lo, hi = mesh_sw.bounds
summary = {
    "faces": len(mesh.faces), "watertight": bool(mesh.is_watertight), "volume_cm3": round(mesh.volume / 1000, 1),
    "sw_bounds_min": np.round(lo, 1).tolist(), "sw_bounds_max": np.round(hi, 1).tolist(),
    "fingers": {n: {"length_from_web": round(float(np.linalg.norm(TIPS[n] - np.mean(FINGER_WEBS[n], axis=0))), 1),
                    "width_mid": round(float(2 * f["half"][1]), 1), "thickness_mid": round(float(2 * f["t_half"][1]), 1)} for n, f in fingers.items()},
    "palm_thickness_at_knuckles": round(float(palmar_palm(92) - dorsal(92)), 1),
    "palm_width_at_knuckles": round(float(abs(PINKY_OUTER_BASE[0] - INDEX_OUTER_BASE[0])), 1),
}
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
