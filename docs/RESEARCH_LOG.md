# Research log: problems we hit and how we solved them

This log records the methodological decisions behind the study, in the order they came up. Each entry gives the problem, why it matters, and what we did about it.

---

### 1. Generated translations would confound the experiment
**Problem.** The first plan was to have a small local LLM (about 7B parameters) write each dialogue in English and then translate it into Urdu and Roman Urdu. Small open models write noticeably weaker Urdu than English.
**Why it matters.** If a judge scored Urdu worse, we could not tell whether the *judge* failed or the *translation* had already changed the meaning. The two effects would be confounded.
**Fix.** We wrote the 90 dialogues as **parallel versions** with a fixed mapping for frequency words (*a few days* = چند دن = *kuch din*; *most days* = زیادہ تر دن = *zyada tar din*; *nearly every day* = تقریباً ہر روز = *taqreeban har roz*), drafted with an AI assistant and reviewed by a native speaker. The content stays constant, so any score difference is attributable to the language.

### 2. Ambiguous frequency wording in the ground truth
**Problem.** An automated check that counts frequency cues against each persona's item scores found one dialogue (P14) where "tired *most of the day*" was meant as "most days" (score 2). The two are not the same thing.
**Why it matters.** If the ground truth itself is ambiguous, the judge gets penalised for a reasonable reading.
**Fix.** Rewrote P14 to "most days" in all three languages. A second scan across languages confirmed that the cue counts match in EN, UR and RU for all 30 personas. The only differences were the general word *mostly* (زیادہ تر / *zyada tar*), which is not a symptom frequency.

### 3. "زیادہ تر / zyada tar" means both "most days" and "mostly"
**Problem.** The second scan showed that the same Urdu word marks a clinical frequency (*zyada tar din*, "most days") and a general opinion (*zyada tar theek hoon*, "I'm mostly fine").
**Why it matters.** This is a genuine linguistic trap for any model scoring frequency in Urdu. An English speaker would never confuse "mostly fine" with "most days".
**Fix.** Kept it, because it reflects real language. We added an explicit note to the RAG glossary and will check whether judges over-score these cases.

### 4. Silent context truncation would bias results against Urdu
**Problem.** Ollama uses a small default context window. Urdu script is tokenised much less efficiently than English, so the *same* conversation takes many more tokens.
**Why it matters.** Long Urdu prompts could be **cut off silently**, making Urdu look worse because of an engineering default rather than model ability.
**Fix.** Set `num_ctx = 8192`, print a warning if any prompt reaches the limit, and **log the prompt token count of every judgement**. The token cost per language is now reported as a result in its own right.

### 5. Unreliable output format
**Problem.** LLM judges sometimes wrap the JSON in extra text or skip keys.
**Fix.** Ollama JSON mode (`format: "json"`), a strict parser that requires all nine items and clamps values to 0–3, and one retry with a stricter reminder. The number of outputs that still fail to parse is reported, not hidden.

### 6. Safety: suicidal ideation
**Problem.** PHQ-9 item 9 asks about self-harm. Writing synthetic dialogues about it, and evaluating models on it, needs clinical safeguards this pilot doesn't have.
**Fix.** Item 9 is 0 for every persona and is never described. In severe cases the listener gently suggests talking to a doctor or someone trusted. We report any item-9 false positives as a separate finding.

### 7. Reproducibility
**Fix.** Temperature 0 with a fixed seed, pinned model tags, all raw outputs saved (`data/ratings.jsonl`, `data/translations.jsonl`), and a resumable pipeline: re-running continues from the last saved result.

### 8. Many statistical tests
**Problem.** We compare 3 judges × 6 language contrasts, which is 18 paired tests. Some would look "significant" by chance.
**Fix.** Paired sign-flip permutation tests (no normality assumption, n = 30) with **Holm–Bonferroni correction**. Bootstrap 95% CIs for MAE.

### 9. The metric should reflect clinical harm
**Problem.** Mean error treats over- and under-estimation the same. In screening, *missing* a depressed person is the costly error.
**Fix.** Report signed **bias**, **sensitivity and specificity at PHQ-9 ≥ 10** (the standard cut-off), and **item-level bias** to show *which* symptoms get lost.

### 10. Mitigations, and the risk of overstating them
**Problem.** Measuring a gap is useful. Testing fixes is more useful, but fixes can be oversold.
**Fix.** We test two mitigations: translate-then-score, and glossary RAG with dense retrieval using `bge-m3`. Because the glossary was written alongside the dialogues, the RAG result is reported as an **optimistic upper bound**.

### 11. Running an overnight job on a home PC
**Problem.** Windows sleep, network hiccups and GPU heat can kill or corrupt a long run.
**Fix.** The process keeps the system awake only while it runs, each request is retried 3 times, and a watchdog logs GPU temperature every 30 s and stops the run if the GPU reaches 84 °C. The pipeline then resumes from where it stopped.

### 12. Early signal from the smoke test
Before the full run, we tested one judge (Llama 3.1 8B) on two personas. For a severe case (true PHQ-9 = 21), the English and Urdu-script scores were 21 and 23, but **Roman Urdu was 16**. That is a drop of 5 points, which moves the person out of the "severe" band. This is a single example, not a result, but it motivated the full design.

### 13. What the full run showed, and what surprised us
- **Clean run:** 630 judgements, 0 unparseable outputs, 0 retries, 0 truncation warnings, peak GPU temperature 70 °C.
- **Expected:** error rose from English to Urdu to Roman Urdu for every judge.
- **Surprise 1: translating first made Urdu-script scoring worse for all three judges.** A check of the translations supports one explanation: of the 67 "nearly every day" phrases (*تقریباً ہر روز* / *taqreeban har roz*), only 54–61 survived as "nearly/almost every day" in the Urdu-script translations, and only 44–55 in the Roman Urdu ones. Up to a third of the strongest frequency markers were lost before scoring even started.
- **Surprise 2: retrieval is not a free win.** Even with a glossary written alongside the data (a best case), RAG helped one judge on Urdu script and two judges on Roman Urdu, but made Gemma 3 under-estimate severity on Urdu script. Longer prompts (about 2–3× the tokens) may dilute attention. Any RAG fix needs to be validated per model.
- **Statistical honesty:** with n = 30, only one contrast (Llama, Urdu vs Urdu + RAG) survives Holm correction. We report the rest as consistent trends and plan a larger follow-up.

### 14. Tokenizer cost, and placing the work next to concurrent research
**Why we looked.** Entry 4 showed that Urdu script used more tokens on some judges. A concurrent preprint, *The Indic Token Tax in 2026* (arXiv 2611.13058, Nov 2026), measures native vs romanized token cost on formal Wikipedia sentences (Dakshina) for GPT-4, GPT-4o, Qwen2.5, DeepSeek-V3 and Mistral-Nemo. It does not cover Llama 3 or Gemma 3, or conversational, code-mixed Roman Urdu.
**What we added (CPU only).** We counted tokens for our 90 parallel dialogues with 9 tokenizers ([`results/tokenizer_cost.md`](../results/tokenizer_cost.md)):
- Roman Urdu costs about **1.3–1.7× English on every tokenizer**.
- Urdu script splits the tokenizers into two groups. Newer multilingual ones (Gemma 3, GPT-4o, Mistral-Nemo) make Urdu script *cheaper* than Roman Urdu (0.92–0.94×). English-centric ones (Llama 3.1, Qwen 2.5, Phi-3.5, GPT-4) make it **1.75–2.4× more expensive**.
- **A hint, not a result:** Gemma 3, the judge with the most Urdu-efficient tokenizer, also had the lowest Urdu error. With three judges this proves nothing, but it is worth testing with more models.

### 15. Adding the newest models (Qwen 3.5 9B, Gemma 4 12B)
**Question.** Is the language gap just a weakness of older small models, which newer ones fix?
**Problems and fixes.**
- Both new models "think" before answering by default. That made outputs slow and sometimes put text before the JSON. We turned thinking off (`think: false`) so every judge gets the same kind of prompt and answers in one step. All 1050 new outputs parsed.
- Midway the run looked stalled (GPU near 0%, no model loaded). It was swapping between Gemma 4 and the `bge-m3` embedding model for the RAG condition, which only 8 GB of VRAM cannot hold together. It was slow (about 2 h 45 min), not broken; a later version should embed all turns once up front.
- Adding two judges doubles the size of the Holm correction family, so the earlier "significant" Llama RAG result (p = 0.041 with 3 judges) is p = 0.064 with 5. We report both instead of choosing the nicer one.
**What we found.** Gemma 4 is far more accurate (English MAE 0.17), but its error still rises about 5× in Urdu script and 6× in Roman Urdu. English vs Roman Urdu is significant after correction (p = 0.006). Translate-then-score again did not help. Glossary RAG brought Gemma 4's Roman Urdu error down to the English level (1.00 → 0.13, Holm p = 0.014), the opposite of what it did for Gemma 3 on Urdu script. Gemma 4 also over-estimates rather than under-estimates outside English.
**What it means.** Newer models shrink the error but not the language gap. Retrieval of culturally specific phrasing looks more promising with stronger models; testing that on more personas and real (consented, anonymized) text is the natural next step.

### 16. A simpler mitigation, and a native speaker's correction
**Question.** Is retrieval needed, or does a short fixed table of frequency phrases work as well?
**Design.** Same 30 personas, 3 judges (Gemma 3, Qwen 3.5, Gemma 4), Urdu and Roman Urdu with the table prepended;
ratings saved separately (`data/ratings_hint.jsonl`, `results/RESULTS_hint.md`).
**Result.** For Gemma 4 the table brought Roman Urdu to the English level (1.00 -> 0.07, Holm p < 0.001). For Gemma 3 it
avoided the harm that RAG caused on Urdu script. Same caveat as RAG: an optimistic upper bound.
**Correction from a native speaker.** People usually say "kabhi kabhi" rather than "kuch din", and "zyada tar" without
"din"; "taqreeban roz" or "taqreeban har din" for nearly every day, while plain "roz" means exactly every day. Our
dialogues use the more textbook forms. We added this to the limitations and used several everyday phrasings in the
follow-up logit-lens study.
