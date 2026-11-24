"""Mitigation 3: a fixed frequency table in the prompt ("spell it out"), compared with glossary RAG.

The full study found that the newest models still lose accuracy outside English, mainly by misreading how often a
symptom happens. RAG with a glossary helped strong models but hurt a weaker one. Here we test the simplest possible
fix: a short, fixed table that maps common Urdu / Roman Urdu frequency phrases onto the PHQ-9 0-3 scale, added to
every prompt (no retrieval, no embedding model). The table lists several common phrases per level, not only the ones
used to write the dialogues, but it overlaps with them, so like the RAG glossary it is an optimistic upper bound.

Judges: Gemma 3 12B (RAG hurt it), Qwen 3.5 9B and Gemma 4 12B (newest). Conditions: ur_hint, ru_hint.
Ratings go to data/ratings_hint.jsonl (the main ratings file is not touched).

  python -I urdu_hint.py prompt | run | results
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # needed under python -I
import pipeline as P

OUT = os.path.join(P.DATA, "ratings_hint.jsonl")
JUDGES = ["gemma4:12b", "qwen3.5:9b", "gemma3:12b"]
CONDS = ["ur_hint", "ru_hint"]

TABLE = """How often, in Urdu and Roman Urdu (use this to convert the User's words into PHQ-9 scores):
- 1 (several days): kabhi kabhi / کبھی کبھی, kuch din / کچھ دن, chand din / چند دن
- 2 (more than half the days): aksar / اکثر, zyada tar din / زیادہ تر دن, hafte mein kai din / ہفتے میں کئی دن
- 3 (nearly every day): roz / روز, har roz / ہر روز, rozana / روزانہ, taqreeban har roz / تقریباً ہر روز
Note: "zyada tar" on its own can also mean "mostly" (zyada tar theek hoon = I am mostly fine); that is not a frequency."""


def hint_prompt(text):
    return TABLE + "\n\n" + P.judge_prompt(text)


def run():
    P.keep_awake()
    D = P.dialogues()
    done = {(r["judge"], r["id"], r["cond"]) for r in P.jl_load(OUT)}
    for jm in JUDGES:
        for pid in sorted({k[0] for k in D}):
            for cond in CONDS:
                if (jm, pid, cond) in done:
                    continue
                prompt = hint_prompt(D[(pid, cond[:2])])
                raw = P.chat(jm, P.SYS_J, prompt, as_json=True)
                sc = P.parse(raw)
                if sc is None:
                    raw = P.chat(jm, P.SYS_J, prompt + "\n\nReply with the JSON object only, all nine keys.", as_json=True)
                    sc = P.parse(raw)
                P.jl_add(OUT, {"judge": jm, "id": pid, "cond": cond, "raw": raw, "scores": sc,
                               "prompt_tokens": P.LAST.get("prompt_tokens")})
            print(jm, pid, "done", flush=True)
        print("judge done", jm, flush=True)
    print("done", flush=True)


def results():
    import numpy as np
    import pandas as pd
    per = P.personas()
    R = pd.DataFrame(P.jl_load(os.path.join(P.DATA, "ratings.jsonl")) + P.jl_load(OUT))
    R = R[R.judge.isin(JUDGES) & R.scores.notna()].copy()
    R["true"] = R.id.map(lambda i: int(per[i]["phq9_total"]))
    R["pred"] = R.scores.map(lambda s: sum(s.values()))
    R["abs_err"] = (R.pred - R.true).abs()
    R["bias"] = R.pred - R.true
    order = ["en", "ur", "ru", "ur_rag", "ru_rag", "ur_hint", "ru_hint"]
    rows = []
    for (j, c), g in R.groupby(["judge", "cond"]):
        if c not in order:
            continue
        lo, hi = P.boot_ci(g.abs_err)
        rows.append({"judge": j, "cond": c, "n": len(g), "MAE": round(g.abs_err.mean(), 2), "MAE_95CI": f"{lo:.1f}-{hi:.1f}",
                     "bias": round(g.bias.mean(), 2)})
    T = pd.DataFrame(rows)
    T["cond"] = pd.Categorical(T.cond, order)
    T = T.sort_values(["judge", "cond"])
    tests = []
    for j in JUDGES:
        g = R[R.judge == j].pivot_table(index="id", columns="cond", values="abs_err")
        for a, b in [("ur", "ur_hint"), ("ru", "ru_hint"), ("ur_rag", "ur_hint"), ("ru_rag", "ru_hint"), ("en", "ur_hint"), ("en", "ru_hint")]:
            if a in g and b in g:
                d = g[[a, b]].dropna()
                tests.append({"judge": j, "compare": f"{a} vs {b}", "n": len(d),
                              "mean_diff(b-a)": round((d[b] - d[a]).mean(), 3), "p_perm": round(P.perm_test(d[a].values, d[b].values), 3)})
    S = pd.DataFrame(tests)
    if len(S):
        p = S.p_perm.values; idx = np.argsort(p); m = len(p); adj = np.empty(m); run_max = 0
        for rank, i in enumerate(idx):
            run_max = max(run_max, (m - rank) * p[i]); adj[i] = min(1.0, run_max)
        S["p_holm"] = adj.round(3)
    L = ["# Mitigation 3: fixed frequency table in the prompt", "",
         f"Judges: {', '.join(JUDGES)}. MAE in PHQ-9 points (0-27), bootstrap 95% CI; bias < 0 = under-estimation.", "",
         "```", T.to_string(index=False), "```", "", "## Paired permutation tests (Holm within this table)", "",
         "```", S.to_string(index=False), "```", ""]
    open(os.path.join(P.RES, "RESULTS_hint.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prompt"
    if cmd == "prompt":
        D = P.dialogues()
        print(hint_prompt(D[("P01", "ru")])[:1500])
    elif cmd == "run":
        run()
    elif cmd == "results":
        results()
