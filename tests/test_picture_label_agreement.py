import unittest
from unittest.mock import patch

from vs import dsl, pictures, registry


FOLIO = "f72v1"
LOCI = [f"{FOLIO}.{i}" for i in range(2, 5)]


def figure(label, angle=None, position=None):
    features = {"ring": "outer", "colour": "red", "clothing": "nude", "holds": "star", "facing": "left"}
    if angle is not None:
        features["angle_deg_clockwise_from_top"] = angle
    if position is not None:
        features["position"] = position
    return {"kind": "human_figure", "features": features, "label": label}


def annotation(objects, canvas="yale-canvas"):
    return {"folio": FOLIO, "canvas": canvas, "objects": objects}


def record(number, detail, seat=None):
    return {"id": f"V-{number:03d}", "detail": detail, "verdict": "AGREED",
            "provenance": {"seat": seat or f"seat-{number}"}}


class LabelAgreementTest(unittest.TestCase):
    def setUp(self):
        self.a = annotation([figure(LOCI[0], 355), figure(LOCI[1], 90)])
        self.b = annotation([figure(LOCI[1], 92), figure(LOCI[0], 2)])

    def compare(self, a, b, expected_loci, expected_comparisons):
        for first, second in ((a, b), (b, a)):
            confirmed, compared = pictures.label_agreement(first, second)
            self.assertEqual({obj["label"] for obj, _ in confirmed}, set(expected_loci))
            self.assertEqual(compared, expected_comparisons)

    def test_uses_geometry_even_when_labels_would_pair_differently(self):
        self.compare(self.a, self.b, LOCI[:2], 2)
        swapped = annotation([figure(LOCI[0], 92), figure(LOCI[1], 2)])
        self.assertEqual(pictures.agreement(self.a, swapped), 1.0)
        self.compare(self.a, swapped, [], 2)

    def test_absences_and_duplicate_loci_are_not_matches(self):
        erased = annotation([figure(None, 92), figure(None, 2)])
        self.compare(self.a, erased, [], 2)
        self.compare(erased, erased, [], 0)
        duplicate = annotation([*self.b["objects"], figure(LOCI[0], 160)])
        self.compare(self.a, duplicate, [LOCI[1]], 3)

    def test_conflicting_or_ambiguous_positions_are_withheld(self):
        other_canvas = annotation(self.b["objects"], canvas="other-canvas")
        self.compare(self.a, other_canvas, [], 0)
        same = annotation([figure(LOCI[0], 0)])
        tied = annotation([figure(LOCI[0], 5), figure(LOCI[1], 355)])
        self.compare(same, tied, [], 3)
        no_position = annotation([figure(LOCI[0])])
        self.compare(no_position, no_position, [], 2)
        coarse = figure(LOCI[0])
        coarse["features"]["clock"] = "12"
        self.compare(same, annotation([coarse]), [], 2)
        self.compare(same, annotation([figure(LOCI[0], 20)]), [], 2)
        self.compare(same, annotation([figure(LOCI[0], False)]), [], 2)

    def test_legacy_ring_coordinates_end_at_declared_anchor(self):
        a = annotation([figure(LOCI[0], position="outer ring, 1 of 20 clockwise from the top")])
        b = annotation([figure(LOCI[0], position="outer ring, 1 of 20 clockwise from twelve o'clock (about 12 o'clock)")])
        self.compare(a, b, [LOCI[0]], 1)
        other = annotation([figure(LOCI[0], position="outer ring, 1 of 20 clockwise from the top left")])
        self.compare(a, other, [], 2)
        b["objects"][0]["features"]["ring"] = "inner"
        self.compare(a, b, [], 2)

    def test_registry_consumer_requires_two_seats_and_ignores_clock_inference(self):
        implicit = annotation([figure(None, 355), figure(None, 90), figure(None, 180)])
        accepted = [record(1, self.a), record(2, self.b), record(3, implicit)]
        duplicate_seat = [record(1, self.a, seat="same"), record(2, self.b, seat="same"), record(3, implicit)]
        tokens = [{"locus": locus, "lid": locus, "unit": "L", "w": "okal"} for locus in LOCI]
        for cases, expected in ((accepted, set(LOCI[:2])), (duplicate_seat, set())):
            for records in (cases, list(reversed(cases))):
                with self.subTest(records=[r["id"] for r in records]), \
                        patch.object(registry, "read", return_value=records), \
                        patch.object(dsl, "PICTURES", None), \
                        patch.object(dsl, "LABEL_POSITIONS", {FOLIO: [[(LOCI[2], 180)]]}), \
                        patch.object(dsl, "_VERIFIED_PICTURE_CACHE", None):
                    self.assertEqual({obj[3] for obj in dsl._picture_objects(tokens)}, expected)


if __name__ == "__main__":
    unittest.main()
