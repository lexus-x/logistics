"""Does a set of boxes fit on a truck floor without stacking? python -I cluster/pack.py runs the self-check.
Boxes stand upright and may turn 90 degrees. fits() returns True (a layout was found), False (proved impossible: the
footprints exceed the floor, or a box fits in neither direction) or None (the heuristic found no layout: undecided)."""
E = 1e-9


def _pack(boxes, W, L, rule, turn, out=None):
    """MaxRects, boxes [(w, d)] placed in the given order. rule picks the spot for each box: 0 = least leftover on the
    short side, 1 = least leftover on the long side, 2 = lowest then leftmost. turn = False keeps each box as given and
    turns it only when it fits nowhere otherwise. True if every box was placed; out collects each box's (x, y, w, d)."""
    free = [(0.0, 0.0, W, L)]
    for w, d in boxes:
        best = None
        for ways in (((w, d), (d, w)),) if turn else (((w, d),), ((d, w),)):
            for fx, fy, fw, fl in free:
                for a, b in ways:
                    if a <= fw + E and b <= fl + E:
                        lo, hi = sorted((fw - a, fl - b))
                        s = ((lo, hi), (hi, lo), (fy + b, fx))[rule]
                        if best is None or s < best[0]:
                            best = (s, fx, fy, a, b)
            if best is not None:
                break
        if best is None:
            return False
        _, x, y, a, b = best
        if out is not None:
            out.append((x, y, a, b))
        new = set()
        for fx, fy, fw, fl in free:  # cut the placed box out of every free rectangle it overlaps
            if x >= fx + fw - E or x + a <= fx + E or y >= fy + fl - E or y + b <= fy + E:
                new.add((fx, fy, fw, fl))
                continue
            if x > fx + E:
                new.add((fx, fy, x - fx, fl))
            if x + a < fx + fw - E:
                new.add((x + a, fy, fx + fw - x - a, fl))
            if y > fy + E:
                new.add((fx, fy, fw, y - fy))
            if y + b < fy + fl - E:
                new.add((fx, y + b, fw, fy + fl - y - b))
        new = list(new)
        free = [r for r in new if not any(q is not r and q[0] <= r[0] + E and q[1] <= r[1] + E and q[0] + q[2] >= r[0] + r[2] - E
                                          and q[1] + q[3] >= r[1] + r[3] - E for q in new)]
    return True


ORDERS = (lambda b: -b[0] * b[1], lambda b: -max(b), lambda b: -min(b), lambda b: (-max(b), -min(b)), lambda b: -(b[0] + b[1]))


def fits(boxes, W, L, gap=0.0):
    """boxes: [(w, d)] footprints in the floor's unit. gap = clearance kept between neighbouring boxes."""
    bs = [(w + gap, d + gap) for w, d in boxes]
    W, L = W + gap, L + gap  # a box at the wall needs no clearance beyond it
    lo, hi = min(W, L), max(W, L)
    if sum(w * d for w, d in bs) > W * L + E or any(min(b) > lo + E or max(b) > hi + E for b in bs):
        return False
    along = [tuple(sorted(b)) for b in bs]  # every box with its long side along the floor's length, or across it
    tries = [(bs, True), (along, False), ([b[::-1] for b in along], False)]
    return True if any(_pack(sorted(b, key=k), W, L, rule, turn) for b, turn in tries for k in ORDERS for rule in (0, 1, 2)) else None


def layout(boxes, W, L, gap=0.0):
    """The first layout fits() finds, for drawing: [(x, y, w, d)] per box with the clearance taken off again, or None."""
    bs = [(w + gap, d + gap) for w, d in boxes]
    along = [tuple(sorted(b)) for b in bs]
    for b, turn in ((bs, True), (along, False), ([q[::-1] for q in along], False)):
        for k in ORDERS:
            for rule in (0, 1, 2):
                out = []
                if _pack(sorted(b, key=k), W + gap, L + gap, rule, turn, out):
                    return [(x, y, a - gap, c - gap) for x, y, a, c in out]
    return None


def key(boxes, W, L, gap=0.0):
    """One string per packing question, the same whatever the order or orientation of the boxes."""
    return f"{W:g}x{L:g}g{gap:g}:" + ",".join(f"{a:g}x{b:g}" for a, b in sorted(tuple(sorted(b)) for b in boxes))


if __name__ == "__main__":
    assert fits([(80, 137.5)] * 4, 160, 275) is True, "four quarters tile the floor"
    assert fits([(80, 137.5)] * 5, 160, 275) is False, "five don't: more footprint than floor"
    assert fits([(170, 100)], 160, 275) is True, "turned 90 degrees"
    assert fits([(300, 10)], 160, 275) is False, "longer than the floor either way"
    assert fits([(100, 100), (100, 100)], 160, 275) is True and fits([(100, 100)] * 3, 160, 275) is None, "3 x 1 m2 can't sit on 1.6 x 2.75, but only area is proved"
    assert fits([(75, 130)] * 4, 160, 275, gap=5) is True and fits([(78, 135)] * 4, 160, 275, gap=5) is not True, "clearance between boxes"
    assert fits([(3, 2)] * 4 + [(1, 1)], 5, 5) in (True, None), "pinwheel: may be undecided, never False"
    lay = layout([(75, 130)] * 4, 160, 275, gap=5)
    assert len(lay) == 4 and all(x >= -E and y >= -E and x + w <= 160 + E and y + d <= 275 + E for x, y, w, d in lay), lay
    assert all(a[0] + a[2] + 5 <= b[0] + E or b[0] + b[2] + 5 <= a[0] + E or a[1] + a[3] + 5 <= b[1] + E or b[1] + b[3] + 5 <= a[1] + E
               for i, a in enumerate(lay) for b in lay[i + 1:]), "boxes keep their clearance"
    assert layout([(100, 100)] * 3, 160, 275) is None
    print("pack ok")
