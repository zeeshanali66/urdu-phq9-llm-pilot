"""Can LLMs screen for depression in Urdu? A controlled pilot.

Design (see PLAN.md):
  * 30 synthetic personas with known PHQ-9 item scores (item 9, self-harm, is 0 for all on purpose).
  * Each persona has one dialogue written in 3 parallel versions: English (en), Urdu script (ur),
    Roman Urdu with code-mixing (ru). Translations are written carefully and validated by a native
    speaker, so differences in scores come from the JUDGE, not from the data.
  * 3 open LLM judges (run locally with Ollama) rate PHQ-9 from each dialogue.
  * Mitigation test: the same judge first translates ur/ru into English, then rates it (ur2en, ru2en).

Usage (only when the PC is free):
    python -I pipeline.py check     # sanity-check the dialogue files (no models needed)
    python -I pipeline.py sheet     # native-speaker validation sheet -> data/validation_TODO.csv
    python -I pipeline.py judge     # all judges, all conditions -> data/ratings.jsonl   (resumable)
    python -I pipeline.py results   # tables, statistics, charts -> results/
"""
import csv, glob, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
OLLAMA = "http://localhost:11434/api/chat"
JUDGES = ["llama3.1:8b", "qwen2.5:7b", "gemma3:12b"]
LANGS = ["en", "ur", "ru"]
CONDITIONS = ["en", "ur", "ru", "ur2en", "ru2en", "ur_rag", "ru_rag"]
EMBED_MODEL = "bge-m3"  # multilingual embedding model (covers Urdu and Latin-script text)
OLLAMA_EMBED = "http://localhost:11434/api/embed"
ITEM_NAMES = ["interest", "mood", "sleep", "energy", "appetite", "self-worth", "concentration", "psychomotor", "self-harm"]


# ---------------- helpers ----------------
def chat(model, system, user, num_predict=200, as_json=False):
    # num_ctx 8192: Urdu script costs many more tokens than English; the Ollama default context
    # would silently truncate long Urdu inputs and bias the comparison against Urdu.
    payload = {"model": model, "stream": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0, "seed": 42, "num_predict": num_predict, "num_ctx": 8192}}
    if as_json:
        payload["format"] = "json"
    body = json.dumps(payload).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1800) as r:
                out = json.loads(r.read())
            if out.get("prompt_eval_count", 0) >= 8192:
                print("WARN: input may be truncated", model, flush=True)
            return out["message"]["content"].strip()
        except Exception as e:
            print(f"retry {attempt + 1}/3 after error: {e}", flush=True)
            time.sleep(20)
    raise RuntimeError("Ollama failed 3 times")


def jl_load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def jl_add(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def personas():
    with open(os.path.join(DATA, "personas.csv"), encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def dialogues():
    """Parse data/dialogues/batch*.txt -> {(id, lang): text}"""
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA, "dialogues", "batch*.txt"))):
        with open(path, encoding="utf-8") as f:
            parts = re.split(r"^### (P\d\d) (en|ur|ru)\s*$", f.read(), flags=re.M)
        for i in range(1, len(parts), 3):
            out[(parts[i], parts[i + 1])] = parts[i + 2].strip()
    return out


def band(t):
    return 0 if t <= 4 else 1 if t <= 9 else 2 if t <= 14 else 3 if t <= 19 else 4


BAND_NAMES = ["minimal", "mild", "moderate", "mod. severe", "severe"]


# ---------------- check & validation sheet ----------------
def check():
    P, D = personas(), dialogues()
    missing = [(p, l) for p in P for l in LANGS if (p, l) not in D]
    print(f"{len(D)} dialogues found, missing: {missing or 'none'}")
    for (p, l), t in sorted(D.items()):
        users = len(re.findall(r"^User:", t, re.M))
        if users != 4:
            print("WARN", p, l, "has", users, "User turns")
        if l == "ru" and re.search(r"[؀-ۿ]", t):
            print("WARN", p, "ru contains Urdu script")
        if l == "ur" and len(re.findall(r"[؀-ۿ]", t)) < 200:
            print("WARN", p, "ur has little Urdu script")
    print("check done")


def sheet():
    D = dialogues()
    out = os.path.join(DATA, "validation_TODO.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "lang", "english", "translated", "faithful (yes/no)", "natural (1-5)", "notes"])
        for pid in sorted({k[0] for k in D}):
            for lang in ("ur", "ru"):
                w.writerow([pid, lang, D[(pid, "en")], D[(pid, lang)], "", "", ""])
    print("wrote", out)


# ---------------- judging ----------------
SYS_J = "You are a careful clinical assessment assistant. You answer only with JSON."
SYS_T = "You are a professional translator. Translate faithfully into English. Keep the 'User:' and 'Listener:' labels. Output only the translation."


def judge_prompt(text):
    return ("Read the conversation below. Based only on what the User says, rate each PHQ-9 item for the last two weeks "
            "(0 = not at all, 1 = several days, 2 = more than half the days, 3 = nearly every day). "
            "If something is not mentioned, rate it 0.\n"
            "Items: q1 little interest or pleasure, q2 feeling down or hopeless, q3 sleep problems, q4 tired or low energy, "
            "q5 poor appetite or overeating, q6 feeling bad about yourself or a failure, q7 trouble concentrating, "
            "q8 moving or speaking slowly, or being restless, q9 thoughts of self-harm.\n"
            'Return JSON exactly like {"q1":0,"q2":0,"q3":0,"q4":0,"q5":0,"q6":0,"q7":0,"q8":0,"q9":0}.\n\n'
            "Conversation:\n" + text)


def parse(s):
    m = re.search(r"\{[^{}]*\}", s, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
        return {f"q{k}": max(0, min(3, int(j[f"q{k}"]))) for k in range(1, 10)}
    except Exception:
        return None


# ---------------- RAG: retrieve Urdu / Roman Urdu glossary notes ----------------
_GLOSS = None


def embed(texts):
    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(OLLAMA_EMBED, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["embeddings"]


def glossary():
    """Load the glossary and embed each entry once (cached on disk)."""
    global _GLOSS
    if _GLOSS is None:
        import numpy as np
        with open(os.path.join(DATA, "glossary.json"), encoding="utf-8") as f:
            G = json.load(f)
        cache = os.path.join(DATA, "glossary_emb.json")
        docs = [f"{g['term']}. {g['ur']}. {g['ru']}. {g['note']}" for g in G]
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as f:
                c = json.load(f)
        if not os.path.exists(cache) or c.get("docs") != docs:
            c = {"docs": docs, "emb": embed(docs)}
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(c, f)
        E = np.array(c["emb"], float)
        _GLOSS = (G, E / np.linalg.norm(E, axis=1, keepdims=True))
    return _GLOSS


def retrieve(text, per_turn=2, max_notes=6):
    """Dense retrieval: embed each User turn, take the top glossary entries by cosine similarity."""
    import numpy as np
    G, E = glossary()
    turns = [l[5:].strip() for l in text.splitlines() if l.startswith("User:")]
    Q = np.array(embed(turns), float)
    Q = Q / np.linalg.norm(Q, axis=1, keepdims=True)
    S = Q @ E.T
    best = {}
    for row in S:
        for i in np.argsort(-row)[:per_turn]:
            best[i] = max(best.get(i, -1), row[i])
    chosen = sorted(best, key=lambda i: -best[i])[:max_notes]
    return [G[i] for i in chosen]


def rag_prompt(text):
    notes = "\n".join(f"- {g['term']}: {g['note']} (Urdu: {g['ur']} | Roman Urdu: {g['ru']})" for g in retrieve(text))
    return ("Reference notes on how Urdu and Roman Urdu speakers describe these experiences "
            "(retrieved from a glossary; use them only to interpret the language):\n" + notes + "\n\n" + judge_prompt(text))


def keep_awake():
    """Stop Windows from sleeping while the run is active (released automatically when the process exits)."""
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED


def judge():
    keep_awake()
    D = dialogues()
    rpath = os.path.join(DATA, "ratings.jsonl")
    tpath = os.path.join(DATA, "translations.jsonl")
    for jm in JUDGES:
        done = {(r["judge"], r["id"], r["cond"]) for r in jl_load(rpath)}
        trans = {(r["judge"], r["id"], r["lang"]): r["text"] for r in jl_load(tpath)}
        for pid in sorted({k[0] for k in D}):
            for cond in CONDITIONS:
                if (jm, pid, cond) in done:
                    continue
                prompt_fn = judge_prompt
                if cond in LANGS:
                    text = D[(pid, cond)]
                elif cond.endswith("_rag"):  # original language + retrieved glossary notes
                    text = D[(pid, cond[:2])]
                    prompt_fn = rag_prompt
                else:  # self-translate first, then judge in English
                    src = cond[:2]
                    if (jm, pid, src) not in trans:
                        t = chat(jm, SYS_T, D[(pid, src)], num_predict=1500)
                        jl_add(tpath, {"judge": jm, "id": pid, "lang": src, "text": t})
                        trans[(jm, pid, src)] = t
                    text = trans[(jm, pid, src)]
                prompt = prompt_fn(text)
                raw = chat(jm, SYS_J, prompt, as_json=True)
                sc = parse(raw)
                if sc is None:  # one retry with a stricter reminder
                    raw = chat(jm, SYS_J, prompt + "\n\nReply with the JSON object only, all nine keys.", as_json=True)
                    sc = parse(raw)
                jl_add(rpath, {"judge": jm, "id": pid, "cond": cond, "raw": raw, "scores": sc})
            print(jm, pid, "done", flush=True)


# ---------------- statistics ----------------
def qwk(a, b, k=5):
    """Quadratic weighted kappa between two lists of band indices."""
    import numpy as np
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[x, y] += 1
    W = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    E = np.outer(O.sum(1), O.sum(0)) / max(O.sum(), 1)
    return 1 - (W * O).sum() / max((W * E).sum(), 1e-9)


def boot_ci(vals, fn=None, n=5000, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    vals = np.asarray(vals, float)
    fn = fn or np.mean
    stats = [fn(vals[rng.integers(0, len(vals), len(vals))]) for _ in range(n)]
    return np.percentile(stats, 2.5), np.percentile(stats, 97.5)


def perm_test(x, y, n=10000, seed=0):
    """Paired sign-flip permutation test on per-persona differences (two-sided)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    d = np.asarray(x, float) - np.asarray(y, float)
    obs = abs(d.mean())
    flips = rng.choice([-1, 1], size=(n, len(d)))
    return float(((np.abs((flips * d).mean(1))) >= obs - 1e-12).mean())


def results():
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(RES, exist_ok=True)
    P = personas()
    R = pd.DataFrame(jl_load(os.path.join(DATA, "ratings.jsonl")))
    n_bad = int(R["scores"].isna().sum())
    R = R[R["scores"].notna()].copy()
    R["true"] = R["id"].map(lambda i: int(P[i]["phq9_total"]))
    R["pred"] = R["scores"].map(lambda s: sum(s.values()))
    R["err"] = R["pred"] - R["true"]
    R["abs_err"] = R["err"].abs()
    R["tb"] = R["true"].map(band)
    R["pb"] = R["pred"].map(band)
    R["judge"] = R["judge"].str.replace(":", " ")
    lines = [f"# Results\n\nUnparseable judge outputs (after one retry): {n_bad} of {n_bad + len(R)}\n"]

    rows = []
    for (j, c), g in R.groupby(["judge", "cond"]):
        lo, hi = boot_ci(g["abs_err"])
        tp = ((g["true"] >= 10) & (g["pred"] >= 10)).sum(); fn_ = ((g["true"] >= 10) & (g["pred"] < 10)).sum()
        tn = ((g["true"] < 10) & (g["pred"] < 10)).sum(); fp = ((g["true"] < 10) & (g["pred"] >= 10)).sum()
        rows.append({"judge": j, "condition": c, "n": len(g), "MAE": g["abs_err"].mean(), "MAE_95CI": f"{lo:.1f}-{hi:.1f}",
                     "bias": g["err"].mean(), "band_acc": (g["tb"] == g["pb"]).mean(),
                     "QWK": qwk(g["tb"], g["pb"]),
                     "sensitivity@10": tp / max(tp + fn_, 1), "specificity@10": tn / max(tn + fp, 1)})
    T = pd.DataFrame(rows)
    T["condition"] = pd.Categorical(T["condition"], CONDITIONS)
    T = T.sort_values(["judge", "condition"]).round(2)
    T.to_csv(os.path.join(RES, "main_table.csv"), index=False)
    lines += ["## Main table (MAE in PHQ-9 points; bias < 0 means the judge UNDER-estimates severity)\n", "```\n" + T.to_string(index=False) + "\n```", ""]

    # paired tests: does the language change the error for the same persona?
    tests = []
    for j, g in R.groupby("judge"):
        piv = g.pivot(index="id", columns="cond", values="abs_err")
        for a, b in [("en", "ur"), ("en", "ru"), ("ur", "ur2en"), ("ru", "ru2en"), ("ur", "ur_rag"), ("ru", "ru_rag")]:
            if a in piv and b in piv:
                s = piv[[a, b]].dropna()
                tests.append({"judge": j, "compare": f"{a} vs {b}", "n": len(s), "mean_diff(b-a)": (s[b] - s[a]).mean(),
                              "p_perm": perm_test(s[b], s[a])})
    Tt = pd.DataFrame(tests)
    # Holm-Bonferroni correction across all paired tests
    order_idx = Tt["p_perm"].sort_values().index
    m, running = len(Tt), 0.0
    for rank, i in enumerate(order_idx):
        running = max(running, min(1.0, (m - rank) * Tt.at[i, "p_perm"]))
        Tt.at[i, "p_holm"] = running
    Tt = Tt.round(3)
    Tt.to_csv(os.path.join(RES, "paired_tests.csv"), index=False)
    lines += ["## Paired permutation tests (same persona, different language)\n", "```\n" + Tt.to_string(index=False) + "\n```", ""]

    # item-level: which symptoms get lost in which language?
    item_rows = []
    for (j, c), g in R.groupby(["judge", "cond"]):
        for k in range(1, 10):
            e = [s[f"q{k}"] - int(P[i][f"q{k}"]) for s, i in zip(g["scores"], g["id"])]
            item_rows.append({"judge": j, "condition": c, "item": ITEM_NAMES[k - 1], "item_bias": np.mean(e), "item_MAE": np.mean(np.abs(e))})
    Ti = pd.DataFrame(item_rows)
    Ti.to_csv(os.path.join(RES, "item_level.csv"), index=False)
    piv = Ti[Ti["condition"].isin(LANGS)].groupby(["item", "condition"])["item_bias"].mean().unstack()[LANGS].round(2)
    lines += ["## Item-level bias, averaged over judges (negative = symptom under-detected)\n", "```\n" + piv.to_string() + "\n```", ""]

    # native-speaker validation (if filled in)
    vpath = os.path.join(DATA, "validation.csv")
    if os.path.exists(vpath):
        V = pd.read_csv(vpath)
        V["ok"] = V.iloc[:, 4].astype(str).str.lower().str.startswith("y")
        lines += [f"## Native-speaker validation\n\nFaithful translations: {int(V['ok'].sum())} of {len(V)}; "
                  f"mean naturalness: {pd.to_numeric(V.iloc[:, 5], errors='coerce').mean():.2f} / 5\n"]
        keep = set(zip(V.loc[V["ok"], "id"], V.loc[V["ok"], "lang"]))
        Rv = R[R.apply(lambda r: r["cond"] == "en" or (r["id"], r["cond"][:2]) in keep, axis=1)]
        Mv = Rv.groupby(["judge", "cond"])["abs_err"].agg(["mean", "count"]).round(2)
        Mv.to_csv(os.path.join(RES, "validated_only.csv"))
        lines += ["## MAE using only translations marked faithful\n", "```\n" + Mv.to_string() + "\n```", ""]

    # charts
    order = CONDITIONS
    labels = ["English", "Urdu script", "Roman Urdu", "Urdu→EN (self-translated)", "Roman Urdu→EN", "Urdu + glossary RAG", "Roman Urdu + glossary RAG"]
    M = T.pivot(index="judge", columns="condition", values="MAE")[order]
    ax = M.plot(kind="bar", figsize=(11, 4.5), width=0.85)
    ax.set_ylabel("Mean absolute error (PHQ-9 points, lower is better)")
    ax.set_title("PHQ-9 scoring error by language and judge")
    ax.legend(labels, fontsize=8)
    plt.xticks(rotation=0); plt.tight_layout(); plt.savefig(os.path.join(RES, "fig1_mae.png"), dpi=200); plt.close()

    S = T.pivot(index="judge", columns="condition", values="sensitivity@10")[order]
    ax = S.plot(kind="bar", figsize=(11, 4.5), width=0.85)
    ax.set_ylabel("Sensitivity at PHQ-9 >= 10")
    ax.set_title("Share of moderate-or-worse cases the judge catches")
    ax.set_ylim(0, 1.05); ax.legend(labels, fontsize=8)
    plt.xticks(rotation=0); plt.tight_layout(); plt.savefig(os.path.join(RES, "fig2_sensitivity.png"), dpi=200); plt.close()

    with open(os.path.join(RES, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    {"check": check, "sheet": sheet, "judge": judge, "results": results}[sys.argv[1]]()
