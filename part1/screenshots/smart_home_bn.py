# Smart Home Energy Consumption - Bayesian Network
# Group members: (write names and roll numbers here)
# Pure Python + matplotlib. Inference by enumeration over the full joint.

import random
import itertools
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42   # fixed seed for reproducibility

# ---------------------------------------------------------------
# 1. Network structure
# ---------------------------------------------------------------
ORDER = ["W", "D", "O", "A", "L", "E"]   # topological order

STATES = {
    "W": ["Hot", "Mild", "Cold"],
    "D": ["Weekday", "Weekend"],
    "O": ["High", "Low"],
    "A": ["On", "Off"],
    "L": ["Heavy", "Light"],
    "E": ["High", "Low"],
}

PARENTS = {
    "W": [],
    "D": [],
    "O": ["D"],
    "A": ["W", "O"],
    "L": ["O"],
    "E": ["A", "L"],
}

# ---------------------------------------------------------------
# 2. Expert CPTs.  cpt[var][parent_values_tuple] = {state: prob}
# ---------------------------------------------------------------
def two_way(p_first, first, second):
    # helper: build {first: p, second: 1-p}
    return {first: p_first, second: round(1 - p_first, 10)}

expert = {}
expert["W"] = {(): {"Hot": 0.50, "Mild": 0.30, "Cold": 0.20}}
expert["D"] = {(): {"Weekday": 0.70, "Weekend": 0.30}}
expert["O"] = {
    ("Weekday",): two_way(0.45, "High", "Low"),
    ("Weekend",): two_way(0.80, "High", "Low"),
}
ac_on = {("Hot", "High"): 0.90, ("Hot", "Low"): 0.60,
         ("Mild", "High"): 0.40, ("Mild", "Low"): 0.15,
         ("Cold", "High"): 0.10, ("Cold", "Low"): 0.05}
expert["A"] = {}
for key in ac_on:
    expert["A"][key] = two_way(ac_on[key], "On", "Off")
expert["L"] = {
    ("High",): two_way(0.75, "Heavy", "Light"),
    ("Low",): two_way(0.35, "Heavy", "Light"),
}
e_high = {("On", "Heavy"): 0.92, ("On", "Light"): 0.68,
          ("Off", "Heavy"): 0.55, ("Off", "Light"): 0.12}
expert["E"] = {}
for key in e_high:
    expert["E"][key] = two_way(e_high[key], "High", "Low")

# Verify every CPT row sums to 1
def check_cpt(cpt):
    ok = True
    for var in ORDER:
        for key in cpt[var]:
            total = sum(cpt[var][key].values())
            if abs(total - 1.0) > 1e-9:
                print("BAD ROW:", var, key, total)
                ok = False
    return ok

print("Expert CPTs valid:", check_cpt(expert))

# ---------------------------------------------------------------
# 3. Visualise the network
# ---------------------------------------------------------------
def draw_network(filename):
    pos = {"W": (0, 2), "D": (3, 2), "O": (3, 1), "A": (1.5, 0.5),
           "L": (4.5, 0.5), "E": (3, -0.5)}
    names = {"W": "Weather", "D": "DayType", "O": "Occupancy",
             "A": "AC Usage", "L": "Appl. Load", "E": "Energy"}
    plt.figure(figsize=(7, 5))
    for child in ORDER:
        for par in PARENTS[child]:
            plt.annotate("", xy=pos[child], xytext=pos[par],
                         arrowprops=dict(arrowstyle="->", lw=1.5,
                                         shrinkA=22, shrinkB=22))
    for v in ORDER:
        plt.text(pos[v][0], pos[v][1], names[v], ha="center", va="center",
                 bbox=dict(boxstyle="round", fc="lightblue", ec="black"))
    plt.xlim(-1, 5.5)
    plt.ylim(-1, 2.6)
    plt.axis("off")
    plt.title("Smart Home Bayesian Network")
    plt.savefig(filename, dpi=120)
    plt.close()

draw_network("network.png")

# ---------------------------------------------------------------
# 4. Inference by enumeration
# ---------------------------------------------------------------
def joint(cpt, state):
    # state = dict var -> value; multiply P(var | parents)
    p = 1.0
    for var in ORDER:
        key = ()
        for par in PARENTS[var]:
            key = key + (state[par],)
        p = p * cpt[var][key][state[var]]
    return p

def all_states():
    lists = []
    for var in ORDER:
        lists.append(STATES[var])
    for combo in itertools.product(*lists):
        s = {}
        for i in range(len(ORDER)):
            s[ORDER[i]] = combo[i]
        yield s

def prob(cpt, target, evidence):
    # P(target | evidence); target and evidence are dicts
    num = 0.0
    den = 0.0
    for s in all_states():
        match_ev = True
        for v in evidence:
            if s[v] != evidence[v]:
                match_ev = False
        if not match_ev:
            continue
        p = joint(cpt, s)
        den = den + p
        match_t = True
        for v in target:
            if s[v] != target[v]:
                match_t = False
        if match_t:
            num = num + p
    if den == 0:
        return float("nan")
    return num / den

QUERIES = [
    ("Q1", {"E": "High"}, {}),
    ("Q2", {"E": "High"}, {"W": "Hot"}),
    ("Q3", {"E": "High"}, {"D": "Weekend"}),
    ("Q4", {"E": "High"}, {"W": "Cold", "O": "High"}),
    ("Q5", {"W": "Hot"}, {"E": "High"}),
    ("Q6", {"A": "On"}, {"E": "High"}),
    ("Q7", {"A": "On"}, {"E": "High", "L": "Heavy"}),
]

def run_queries(cpt):
    out = []
    for name, tgt, ev in QUERIES:
        out.append(prob(cpt, tgt, ev))
    return out

expert_res = run_queries(expert)
print("\nExpert results")
for i in range(7):
    print(QUERIES[i][0], round(expert_res[i], 4))

# Hand calculation of Q1 (P(E=High)) via P(A,L) summation
def hand_q1(cpt):
    # P(A=a, L=l) = sum_{w,d,o} P(w)P(d)P(o|d)P(a|w,o)P(l|o)
    total = 0.0
    print("\nHand calc of Q1: sum over A,L of P(E=High|A,L) * P(A,L)")
    for a in STATES["A"]:
        for l in STATES["L"]:
            pal = 0.0
            for w in STATES["W"]:
                for d in STATES["D"]:
                    for o in STATES["O"]:
                        pal += (cpt["W"][()][w] * cpt["D"][()][d] *
                                cpt["O"][(d,)][o] * cpt["A"][(w, o)][a] *
                                cpt["L"][(o,)][l])
            pe = cpt["E"][(a, l)]["High"]
            print("  P(A=%s,L=%s)=%.5f  P(E=High|a,l)=%.2f  product=%.5f"
                  % (a, l, pal, pe, pal * pe))
            total += pal * pe
    print("  Q1 =", round(total, 5))
    return total

hand_q1(expert)

# ---------------------------------------------------------------
# 5. d-separation checks (numeric verification)
# ---------------------------------------------------------------
print("\nNumeric independence checks")
print("1) W vs D:  P(W=Hot)=%.4f  P(W=Hot|D=Weekend)=%.4f"
      % (prob(expert, {"W": "Hot"}, {}),
         prob(expert, {"W": "Hot"}, {"D": "Weekend"})))
print("2) W vs D | E=High: P(W=Hot|E=High)=%.4f  P(W=Hot|E=High,D=Weekend)=%.4f"
      % (prob(expert, {"W": "Hot"}, {"E": "High"}),
         prob(expert, {"W": "Hot"}, {"E": "High", "D": "Weekend"})))
print("3) W vs L | O=High: P(W=Hot|O=High)=%.4f  P(W=Hot|O=High,L=Heavy)=%.4f"
      % (prob(expert, {"W": "Hot"}, {"O": "High"}),
         prob(expert, {"W": "Hot"}, {"O": "High", "L": "Heavy"})))

# ---------------------------------------------------------------
# 6. Ancestral sampling
# ---------------------------------------------------------------
def pick(rng, dist):
    # draw one value from {state: prob}
    r = rng.random()
    cum = 0.0
    last = None
    for st in dist:
        cum += dist[st]
        last = st
        if r < cum:
            return st
    return last

def sample_data(cpt, n, seed):
    rng = random.Random(seed)
    data = []
    for i in range(n):
        row = {}
        for var in ORDER:                 # topological order
            key = ()
            for par in PARENTS[var]:
                key = key + (row[par],)
            row[var] = pick(rng, cpt[var][key])
        data.append(row)
    return data

SIZES = [500, 5000, 20000]
datasets = {}
for n in SIZES:
    datasets[n] = sample_data(expert, n, SEED)

print("\nSampling summary (seed = %d)" % SEED)
for n in SIZES:
    d = datasets[n]
    print("n =", n)
    for w in STATES["W"]:
        c = 0
        for row in d:
            if row["W"] == w:
                c += 1
        print("  freq W=%s: %.4f" % (w, c / n))
    for w in STATES["W"]:
        for o in STATES["O"]:
            c = 0
            for row in d:
                if row["W"] == w and row["O"] == o:
                    c += 1
            print("  count (W=%s, O=%s): %d" % (w, o, c))

# ---------------------------------------------------------------
# 7. Learning: MLE and BDeu (ESS = 10)
# ---------------------------------------------------------------
def learn(data, method, ess=10.0):
    cpt = {}
    for var in ORDER:
        cpt[var] = {}
        r = len(STATES[var])
        q = 1
        for par in PARENTS[var]:
            q = q * len(STATES[par])
        # all parent configurations
        plists = []
        for par in PARENTS[var]:
            plists.append(STATES[par])
        for key in itertools.product(*plists):
            counts = {}
            for st in STATES[var]:
                counts[st] = 0
            for row in data:
                same = True
                for i in range(len(PARENTS[var])):
                    if row[PARENTS[var][i]] != key[i]:
                        same = False
                if same:
                    counts[row[var]] += 1
            total = sum(counts.values())
            cpt[var][key] = {}
            for st in STATES[var]:
                if method == "mle":
                    if total == 0:
                        cpt[var][key][st] = 1.0 / r     # fallback: uniform
                    else:
                        cpt[var][key][st] = counts[st] / total
                else:
                    a = ess / (q * r)                   # BDeu pseudo-count
                    cpt[var][key][st] = (counts[st] + a) / (total + ess / q)
    return cpt

results = {}
for n in SIZES:
    mle = learn(datasets[n], "mle")
    bde = learn(datasets[n], "bdeu")
    results[n] = (mle, bde, run_queries(mle), run_queries(bde))

print("\nAC CPT: P(A=On | W,O)  expert vs MLE vs BDeu")
for n in SIZES:
    print("n =", n)
    for key in ac_on:
        print("  %s expert=%.3f MLE=%.3f BDeu=%.3f"
              % (key, expert["A"][key]["On"],
                 results[n][0]["A"][key]["On"], results[n][1]["A"][key]["On"]))

# ---------------------------------------------------------------
# 8. Comparison tables and plot
# ---------------------------------------------------------------
mean_mle = []
mean_bde = []
for n in SIZES:
    qm = results[n][2]
    qb = results[n][3]
    print("\nComparison, n =", n)
    print("%-4s %8s %8s %8s %8s %8s" % ("Q", "Expert", "MLE", "Bayes", "|dMLE|", "|dBayes|"))
    sm = 0.0
    sb = 0.0
    for i in range(7):
        dm = abs(qm[i] - expert_res[i])
        db = abs(qb[i] - expert_res[i])
        sm += dm
        sb += db
        print("%-4s %8.4f %8.4f %8.4f %8.4f %8.4f"
              % (QUERIES[i][0], expert_res[i], qm[i], qb[i], dm, db))
    mean_mle.append(sm / 7)
    mean_bde.append(sb / 7)
    print("Mean abs diff: MLE=%.5f  BDeu=%.5f" % (sm / 7, sb / 7))

plt.figure(figsize=(6, 4))
plt.plot(SIZES, mean_mle, "o-", label="MLE")
plt.plot(SIZES, mean_bde, "s-", label="Bayesian (BDeu, ESS=10)")
plt.xscale("log")
plt.xlabel("Dataset size")
plt.ylabel("Mean |difference| over Q1-Q7")
plt.title("Learning error vs data size")
plt.legend()
plt.grid(True)
plt.savefig("error_plot.png", dpi=120)
plt.close()

# Largest error at n=500
worst = 0
for i in range(7):
    if abs(results[500][2][i] - expert_res[i]) > abs(results[500][2][worst] - expert_res[worst]):
        worst = i
print("\nLargest MLE error at n=500:", QUERIES[worst][0])
c = 0
for row in datasets[500]:
    if row["W"] == "Cold" and row["O"] == "High":
        c += 1
print("Samples with W=Cold,O=High at n=500 (evidence of Q4):", c)
