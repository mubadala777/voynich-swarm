"""The closed picture vocabulary (P-L4-030, P-L4-032) and how two annotations of a folio are compared.

Free wording cannot agree as strings: two seats who both see a figure standing in a tub score zero
on 'posture' unless they wrote the same sentence. So agreement is measured only on a fixed list of
features with a fixed set of values. Any other feature may still be written; it is kept on the
record as description and never compared.

New annotations must write vocabulary features with one of the listed values (vs/experiment.py
checks this). Annotations already on the record were written before the list existed; their values
are read through `normalize`, which maps the common wordings onto the list and leaves the rest out
of the comparison (a value it cannot place is not compared, never counted as a disagreement).

Objects are paired by label locus where both annotations give one; otherwise within the same kind
and ring, by nearest clock angle when both give one, else in list order.
"""
from collections import Counter, defaultdict
from itertools import combinations
import re

UNCLEAR = "unclear"

# feature -> allowed values. Every feature also accepts "unclear", which is never compared.
VOCAB = {
    "sex": ("female", "male"),
    "clothing": ("nude", "partly", "clothed"),
    "container": ("none", "tub", "barrel", "other"),
    "posture": ("standing", "lying", "in_container", "sitting"),
    "headwear": ("none", "some"),
    "holds": ("nothing", "star", "other"),
    "hair": ("long", "short", "bound"),
    "cheeks": ("red", "none"),
    "facing": ("left", "right", "front"),
    "ring": ("outer", "middle", "inner", "centre", "outside"),
    "colour": ("none", "red", "blue", "green", "yellow", "brown", "mixed"),
    "points": tuple(str(n) for n in range(3, 33)),
    "centre": ("none", "dot", "ring", "face"),
    "tail": ("yes", "no"),
    "count": tuple(str(n) for n in range(1, 101)),
}

# older or alternative key names on the record -> vocabulary key
ALIASES = {"color": "colour", "headdress": "headwear", "headgear": "headwear", "nude": "clothing",
           "star_points": "points", "rays": "points", "centre_mark": "centre", "center_mark": "centre",
           "star": "holds"}

_COLOURS = (("red", ("red", "pink", "rose")), ("blue", ("blue",)), ("green", ("green", "olive")),
            ("yellow", ("yellow", "ochre", "tan", "gold")), ("brown", ("brown",)))


def _words(v):
    return re.findall(r"[a-z]+", v)


def _colour(v):
    if v.startswith(("uncoloured", "uncolored", "ink only", "none", "outline", "unfilled", "no colour")):
        return "none"
    found = {c for c, ws in _COLOURS if any(w.startswith(x) for w in _words(v) for x in ws)}
    if len(found) == 1:
        return found.pop()
    return "mixed" if found else None


def _points(v):
    ns = sorted({int(n) for n in re.findall(r"\d+", v)})
    return str(ns[0]) if len(ns) == 1 else None   # "7 or 8" is not one value: not compared


def _normalize(key, v):
    w = set(_words(v))
    if key == "sex":
        return "female" if "female" in w or "woman" in w else "male" if "male" in w or "man" in w else None
    if key == "clothing":
        if {"dressed", "robe", "tunic", "clothed", "garment", "gown"} & w:
            return "clothed"
        if "bare" in w or "above" in w or "partly" in w:
            return "partly"
        return "nude" if "nude" in w or "naked" in w else None
    if key == "container":
        if v.startswith(("none", "no ")) or v == "no":
            return "none"
        return "barrel" if "barrel" in w else "tub" if "tub" in w else None
    if key == "posture":
        if {"tub", "barrel", "emerging", "rising", "half"} & w or "upper body" in v:
            return "in_container"
        if "lying" in w or "reclining" in w:
            return "lying"
        if "sitting" in w or "seated" in w:
            return "sitting"
        return "standing" if "standing" in w or "upright" in w else None
    if key == "headwear":
        if v in ("no", "none", "bare", "false"):
            return "none"
        return "some" if {"yes", "band", "crown", "cap", "hat", "wreath", "veil", "true"} & w else None
    if key == "holds":
        if v in ("yes", "true", "attached") or v.startswith("star"):
            return "star"
        if v in ("no", "none", "false", "nothing"):
            return "nothing"
        return None
    if key == "hair":
        if {"bound", "braided", "braids", "up"} & w:
            return "bound"
        return "long" if "long" in w else "short" if "short" in w else None
    if key == "cheeks":
        return "red" if "red" in w else "none" if v in ("none", "no", "plain") else None
    if key == "ring":
        if {"top", "outside", "above"} & w:
            return "outside"
        for r in ("outer", "middle", "inner"):
            if r in w:
                return r
        return "centre" if {"centre", "center"} & w else None
    if key == "colour":
        return _colour(v)
    if key in ("points", "count"):
        p = _points(v)
        return p if p in VOCAB[key] else None
    if key == "centre":
        if v.startswith("none") or v in ("no", "hollow", "empty"):
            return "none"
        if "dot" in w:
            return "dot"
        if "ring" in w or "circle" in w or "ringed" in w:
            return "ring"
        return "face" if "face" in w else None
    if key == "tail":
        return "yes" if v in ("yes", "true") else "no" if v in ("no", "none", "false") else None
    if key == "facing":
        for d in ("left", "right"):
            if d in w:
                return d
        return "front" if {"front", "frontal", "viewer"} & w else None
    return None


def normalize(features):
    """The comparable vocabulary features of one object: {key: value}. Exact vocabulary values are
    taken as written; older wordings are mapped where the mapping is plain; the rest is dropped."""
    out = {}
    for k, v in (features or {}).items():
        key = ALIASES.get(k, k)
        if key not in VOCAB or key in out and k != key:
            continue
        s = str(v).strip().lower()
        if s in VOCAB[key]:
            val = s
        elif s == UNCLEAR:
            continue
        else:
            val = _normalize(key, s)
        if val is not None:
            out[key] = val
    return out


def check_features(features):
    """Errors for a new annotation: a vocabulary feature must carry one of its listed values."""
    errs = []
    for k, v in (features or {}).items():
        key = ALIASES.get(k, k)
        if key not in VOCAB:
            continue
        if k != key:
            errs.append(f"feature {k!r}: write it as {key!r}")
        s = str(v).strip().lower()
        if s != UNCLEAR and s not in VOCAB[key]:
            vals = VOCAB[key] if len(VOCAB[key]) < 12 else (VOCAB[key][0] + ".." + VOCAB[key][-1],)
            errs.append(f"feature {key!r} is one of {', '.join(vals)} or unclear (got {v!r}); free description "
                        "goes under any other feature name, where it is kept but not compared")
    return errs


def _angle(o):
    f = o.get("features") or {}
    for k in ("angle_deg_clockwise_from_top", "bearing_clockwise_deg"):
        try:
            return float(f[k]) % 360
        except (KeyError, TypeError, ValueError):
            pass
    for k in ("clock_position", "clock"):
        m = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?", str(f.get(k, "")))
        if m:
            h, mi = int(m.group(1)) % 12, int(m.group(2) or 0)
            return (h * 30 + mi / 2) % 360
    return None


def _ring(o):
    return normalize({"ring": (o.get("features") or {}).get("ring", "")}).get("ring")


def pair_objects(A, B):
    """Pairs of objects that describe the same drawing, in A's order."""
    pairs, used = [], set()
    for o in A:
        lab = o.get("label")
        m = next((k for k, q in enumerate(B) if k not in used and lab and q.get("label") == lab), None)
        if m is None:
            cands = [k for k, q in enumerate(B) if k not in used and q.get("kind") == o.get("kind")
                     and not (lab and q.get("label"))
                     and (_ring(o) is None or _ring(q) is None or _ring(o) == _ring(q))]
            ao = _angle(o)
            angled = [(min(abs(ao - aq), 360 - abs(ao - aq)), k) for k in cands
                      for aq in [_angle(B[k])] if ao is not None and aq is not None]
            if angled:
                d, m = min(angled)
                m = m if d <= 30 else None   # more than an hour apart on the clock is not the same figure
            elif cands:
                m = cands[0]
        if m is not None:
            used.add(m)
            pairs.append((o, B[m]))
    return pairs


def agreement(a, b):
    """Share of compared items on which two annotations of one folio agree. Compared items: every
    vocabulary feature both recorded on a paired object; for objects paired by label locus, also
    their kind and ring (objects paired without a label were paired on kind and ring, so those
    cannot count as agreement); and every object one seat drew that the other has no partner for,
    which counts as a disagreement. None if nothing is comparable."""
    def objs(d):
        return [o for o in (d.get("objects") or []) if isinstance(o, dict)]
    A, B = objs(a), objs(b)
    pairs = pair_objects(A, B)
    tot = len(A) + len(B) - 2 * len(pairs)
    same = 0
    for o, q in pairs:
        fo, fq = normalize(o.get("features")), normalize(q.get("features"))
        by_label = bool(o.get("label")) and o.get("label") == q.get("label")
        if by_label:
            tot += 1
            same += o.get("kind") == q.get("kind")
        else:
            fo.pop("ring", None)
            fq.pop("ring", None)
        for k in set(fo) & set(fq):
            tot += 1
            same += fo[k] == fq[k]
    return same / tot if tot else None


# These legacy position descriptions include the frame, direction and size of the run.
_RING_POSITION = re.compile(
    r"(inner|middle|outer) ring, (\d{1,3}) of (\d{1,3}) clockwise from "
    r"(?:the top|twelve o'clock)(?: \([^()]*\))?"
)
_ROW_POSITION = re.compile(
    r"(upper pool|row above the wheel|above the wheel, outside the outer text ring), "
    r"(\d{1,3}) of (\d{1,3}) from (?:the )?left"
)


def _ordinal_position(obj):
    position = str((obj.get("features") or {}).get("position", "")).strip().lower().replace("’", "'")
    match = _RING_POSITION.fullmatch(position) or _ROW_POSITION.fullmatch(position)
    if match:
        frame, ordinal, size = match.groups()
        if 1 <= int(ordinal) <= int(size):
            ring = _ring(obj)
            if frame in ("inner", "middle", "outer") and ring and ring != frame:
                return None
            frame = "above the wheel" if "above the wheel" in frame else frame
            return frame, int(ordinal), int(size)
    return None


def _nearest_unambiguous(candidates):
    nearest = {}
    for index, choices in candidates.items():
        choices.sort()
        if len(choices) == 1 or choices[0][0] != choices[1][0]:
            nearest[index] = choices[0][1]
    return nearest


def _label_angle(obj):
    features = obj.get("features") or {}
    for key in ("angle_deg_clockwise_from_top", "bearing_clockwise_deg"):
        angle = features.get(key)
        if type(angle) in (int, float) and -360 <= angle <= 360:
            return angle % 360
    return None


def _physical_pairs(a, b):
    """Mutual unique matches using shared positions, without using labels or list order."""
    def locate(objects):
        return [(o.get("kind"), _ring(o), _label_angle(o), _ordinal_position(o)) for o in objects]

    left, right = defaultdict(list), defaultdict(list)
    positions_b = locate(b)
    for i, (kind, ring, angle, ordinal) in enumerate(locate(a)):
        for j, (other_kind, other_ring, other_angle, other_ordinal) in enumerate(positions_b):
            if kind != other_kind:
                continue
            distance = None
            if angle is not None and other_angle is not None:
                delta = abs(angle - other_angle)
                distance = min(delta, 360 - delta)
            # An hour of clock position can encompass several figures in a crowded ring.
            if distance is not None and distance > 8:
                continue
            if ordinal is not None and other_ordinal is not None:
                if ordinal != other_ordinal:
                    continue
                priority = (0, 0)
            elif ring and ring == other_ring and distance is not None:
                priority = (1, distance)
            else:
                continue
            left[i].append((priority, j))
            right[j].append((priority, i))
    nearest_b = _nearest_unambiguous(right)
    return [(i, j) for i, j in _nearest_unambiguous(left).items() if nearest_b.get(j) == i]


def label_agreement(a, b):
    """Return corroborated object pairs and the number of explicit label comparisons.

    A different or missing label is a disagreement for a physical pair. A label
    with no physical partner counts against agreement too. Repeated loci are
    ambiguous, including when both seats repeat the same locus.
    """
    folio = a.get("folio")
    if (not isinstance(folio, str) or not folio or folio != b.get("folio")
            or not a.get("canvas") or a["canvas"] != b.get("canvas")):
        return [], 0

    def labelled_objects(annotation):
        objects = [o for o in annotation.get("objects") or [] if isinstance(o, dict)]
        pattern = re.compile(rf"{re.escape(folio)}\.\d+")
        labels = [o.get("label") for o in objects]
        return objects, [label if isinstance(label, str) and pattern.fullmatch(label) else None
                         for label in labels]

    objects_a, labels_a = labelled_objects(a)
    objects_b, labels_b = labelled_objects(b)
    counts_a, counts_b = Counter(labels_a), Counter(labels_b)
    compared = len(labels_a) + len(labels_b) - counts_a[None] - counts_b[None]
    confirmed = []
    for i, j in _physical_pairs(objects_a, objects_b):
        first, second = labels_a[i], labels_b[j]
        if first and second:
            compared -= 1
            if first == second and counts_a[first] == counts_b[second] == 1:
                confirmed.append((objects_a[i], objects_b[j]))
    return confirmed, compared


def verified_picture_objects(records):
    """Objects with corroborated label assignments from one qualifying pair per folio."""
    by_folio = defaultdict(list)
    for record in sorted(records, key=lambda record: record["id"]):
        if record.get("verdict") == "AGREED":
            by_folio[record["detail"]["folio"]].append(record)

    best = {}
    for folio, records in by_folio.items():
        for a, b in combinations(records, 2):
            first_seat = a["provenance"].get("seat", a["provenance"].get("added_by"))
            second_seat = b["provenance"].get("seat", b["provenance"].get("added_by"))
            if not first_seat or not second_seat or first_seat == second_seat:
                continue
            first, second = a["detail"], b["detail"]
            appearance = min(agreement(first, second) or 0, agreement(second, first) or 0)
            if appearance < 0.8:
                continue
            confirmed, compared = label_agreement(first, second)
            if confirmed:
                rank = (appearance, len(confirmed), len(confirmed) / compared)
                if folio not in best or rank > best[folio][0]:
                    best[folio] = (rank, [obj for obj, _ in confirmed])
    return {folio: objects for folio, (_, objects) in best.items()}
