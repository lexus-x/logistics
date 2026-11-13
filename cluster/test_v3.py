"""python -I cluster/test_v3.py: the physical-fit planning and the multi-task model's plumbing on toy loads."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from ryry import C, C14, MAX14  # noqa: E402
from ryry_v3 import GAP, Packer, area_of, box_rows, mt_class, mt_graph, model_fit, score3, settle, true_fit  # noqa: E402

# floor of a 1-ton is 160 x 275 cm: two 150 x 110 boxes fit one behind the other with a small box, three don't, even on a 1.4-ton (170 x 290)
fp = [[(150, 110)], [(150, 110)], [(150, 110)], [(40, 40)]]
P = Packer(fp)
assert P((0, 1), "1t") and not P((0, 1, 2), "1t") and not P((0, 1, 2), "1.4t")
assert P.truck((0, 1), 1.0) == "1t" and P.truck((0, 1), C * 1.05) == "1.4t" and P.truck((0, 1), C14 * 1.05) is None
s, xy, v = np.arange(4), np.array([[0.0, 0], [1, 0], [0, 1], [1, 1]]), np.full(4, 0.5)
area = np.array([area_of(f) for f in fp])
ok, need = true_fit(P, s, v, area)(np.array([[0, 1, 3], [0, 1, 2]]))
assert ok.tolist() == [True, False] and need.tolist() == [False, False]

# settle: the load that can't be laid out sheds its biggest stop and becomes true; nothing is lost
cl, tr, shed = settle(P, s, xy, v, area, [[0, 1, 2, 3]])
assert shed == 1 and sorted(i for c in cl for i in c) == [0, 1, 2, 3] and all(t == "1t" for t in tr), (cl, tr, shed)
j = dict(xy=xy, v=v)
M = (np.ones((5, 5)) - np.eye(5),) * 2
assert score3(j, M, s, cl, tr)["trucks"] == 2
# a load over a 1-ton's volume limit that fits the floor rides a 1.4-ton
assert settle(P, s, xy, np.full(4, C * 0.55), area, [[0, 3], [1], [2]])[1][0] == "1.4t" and MAX14 >= 1

# the model: shapes, probabilities, and the fit head as a solver callback
ll = np.array([[35.3, 128.7], [35.31, 128.7], [35.3, 128.71], [35.31, 128.71]])
g = mt_graph(dict(xy=xy * 5, v=v, ll=ll), s, fp)
torch, _, MT = mt_class()
m = MT().eval()
x, e = m.encode(*(torch.as_tensor(g[k]) for k in ("X", "E")), torch.as_tensor(g["a"]), torch.as_tensor(g["b"]))
assert x.shape == (4, 48) and m.pair_logit(x, e, torch.as_tensor(g["a"]), torch.as_tensor(g["b"])).shape == (len(g["a"]),)
km = m.road_km(x, torch.as_tensor(g["xy"]), torch.tensor([0, 1]), torch.tensor([3, 2]))
assert (km >= torch.as_tensor(np.linalg.norm(g["xy"][[0, 1]] - g["xy"][[3, 2]], axis=1)) - 1e-5).all(), "never shorter than the straight line"
bf, gi, ex = box_rows(fp, [[0, 1], [0, 1, 2]], ["1t", "1t"])
assert bf.shape == (5, 3) and gi.tolist() == [0, 0, 1, 1, 1] and ex[1, 0] > 1 > ex[0, 0], "three boxes cover more than the floor"
okm, needm = model_fit(m, fp, s)(np.array([[0, 1], [2, 3]]))
assert okm.shape == needm.shape == (2,)
# the rival encoders: same shapes, and a job's result must not depend on which other jobs sit in the same batch
from ryry_v3 import context  # noqa: E402
g2 = mt_graph(dict(xy=xy[::-1] * 9, v=v[::-1], ll=ll[::-1] + 0.2), s, fp)
T = lambda z, dt=None: torch.as_tensor(z, dtype=dt)  # noqa: E731
sizes = {}
for arch in ("transformer", "pointer"):
    r = mt_class(arch=arch)[2]().eval()
    sizes[arch] = sum(p.numel() for p in r.parameters())
    one = r.encode(T(g["X"]), T(g["E"]), T(g["a"]), T(g["b"]), context([g], torch))[0]
    both = r.encode(T(np.r_[g["X"], g2["X"]]), T(np.r_[g["E"], g2["E"]]), T(np.r_[g["a"], g2["a"] + 4]), T(np.r_[g["b"], g2["b"] + 4]), context([g, g2], torch))[0]
    assert one.shape == (4, 48) and torch.allclose(one, both[:4], atol=1e-5), arch
    assert not torch.allclose(both[:4], both[4:], atol=1e-3), "the two jobs differ"
print("v3 ok", sum(p.numel() for p in m.parameters()), "parameters; rivals", sizes)
