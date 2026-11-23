# Can LLMs screen for depression in Urdu?

A controlled pilot study of how open large language models score the **PHQ-9** depression questionnaire when the same person describes the same symptoms in **English**, **Urdu script**, or **Roman Urdu** (Urdu typed in Latin letters, mixed with English, which is how most Pakistanis write online).


## Why
Mental-health chatbots and LLM-based screening tools are mostly built and tested in English. Urdu is Pakistan's national language, and online it is very often typed as Roman Urdu. If a model misses symptoms because of the language they're written in, people who need help could be under-screened. I first ran into this question while building PHQ-9 screening into a mental-health assistant for my undergraduate thesis.

## Design
- **30 synthetic personas**, 6 per PHQ-9 severity band (minimal → severe), each with known **item-level** scores. Item 9 (self-harm) is set to 0 for every persona, for safety.
- **90 parallel dialogues:** one 8-turn conversation per persona, written in three versions with a fixed mapping for frequency words (*a few days / most days / nearly every day* → *چند دن / زیادہ تر دن / تقریباً ہر روز* → *kuch din / zyada tar din / taqreeban har roz*). Keeping the content identical **isolates the effect of language**.
- **Authoring and validation:** the dialogues were drafted with the help of an AI assistant using the fixed frequency mapping, then every Urdu and Roman Urdu version is checked by a native speaker for faithfulness and naturalness (validation in progress).
- **Three open LLM judges** run locally with [Ollama](https://ollama.com) at temperature 0: Llama 3.1 8B, Qwen 2.5 7B and Gemma 3 12B.
- **Two mitigation strategies:**
  1. **Translate-then-score:** each judge first translates the Urdu or Roman Urdu dialogue into English itself, then scores it.
  2. **Glossary RAG:** a small glossary of how Urdu and Roman Urdu speakers express distress and frequency (`data/glossary.json`) is embedded with the multilingual model `bge-m3`. For each user turn, the most similar entries are retrieved by cosine similarity and added to the judge's prompt.
- **Metrics:**
  - MAE with bootstrap 95% CIs
  - bias (under- vs over-estimation)
  - band accuracy and quadratic weighted kappa
  - sensitivity and specificity at the clinical cut-off PHQ-9 ≥ 10
  - paired permutation tests across languages
  - item-level bias (which symptoms are lost)

## Key results (pilot, n = 30 personas × 3 judges)
- **Error grows outside English.** Averaged over the three judges, mean absolute error rose from **1.73** PHQ-9 points in English to **2.44** in Urdu script (+41%) and **2.56** in Roman Urdu (+48%). The direction was the same for every judge. With n = 30, the individual contrasts don't survive Holm correction, so this is a consistent trend rather than a confirmed effect.
- **Severity gets softened.** Example: a persona with true PHQ-9 = 21 (severe) was scored 21 in English but 16 in Roman Urdu by Llama 3.1 8B, which reads "nearly every day" (*taqreeban har roz*) as "most days".
- **Psychomotor symptoms are lost most.** Under-detection of restlessness or slowing roughly doubled (item bias −0.32 in English vs −0.69 in Urdu and −0.64 in Roman Urdu).
- **Translate-then-score did not help.** For Urdu script it increased error for all three judges; for Roman Urdu the effect was mixed (better for 2 judges, worse for 1).
- **Glossary RAG cuts both ways.** It reduced Llama's Urdu-script error from 2.50 to 1.60 (the only contrast significant after Holm correction, p = 0.041), but increased Gemma's Urdu-script error from 1.23 to 2.33 and pushed it toward *under*-estimation (bias −2.0).
- **Urdu script is expensive.** The same conversation used about **1.86×** more prompt tokens in Urdu script for Llama and Qwen, but only **1.09×** for Gemma.
- **Tokenizer cost (9 tokenizers, CPU-only analysis):** Roman Urdu costs about 1.3–1.7× English everywhere. Urdu script ranges from 0.92× Roman Urdu (Gemma 3, GPT-4o) to 2.4× (GPT-4). See [`results/tokenizer_cost.md`](results/tokenizer_cost.md). This complements concurrent work on Indic tokenizer cost (arXiv 2611.13058), which used formal text and did not cover Llama 3 or Gemma 3.
- **Screening sensitivity:** Qwen 2.5 7B under-estimated severity in every condition, and its sensitivity at PHQ-9 ≥ 10 fell from 0.83 (English) to 0.78 (Urdu and Roman Urdu).

Full tables: [`results/RESULTS.md`](results/RESULTS.md). Figures: `results/fig1_mae.png`, `results/fig2_sensitivity.png`.

## Research log
The problems we ran into and how each was addressed (confounded translations, ambiguous ground truth, silent context truncation for Urdu script, safety, multiple comparisons, and more) are documented in [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Reproduce
```bash
ollama pull llama3.1:8b && ollama pull qwen2.5:7b && ollama pull gemma3:12b && ollama pull bge-m3
python pipeline.py check     # validate dialogue files
python pipeline.py judge     # run all judges and conditions (resumable)
python pipeline.py results   # tables, tests and figures in results/
```
Requires Python 3.10+, `pandas`, `numpy` and `matplotlib`.

## Data
- `data/personas.csv`: personas and ground-truth PHQ-9 item scores
- `data/dialogues/batch*.txt`: the 90 dialogues
- `data/ratings.jsonl`, `data/translations.jsonl`: raw judge outputs

## Limitations
This is a small pilot: 30 personas, synthetic AI-assisted dialogues from a single source, no real patients, and 7–12B models only. The glossary was written alongside the dialogues, so the RAG results are an optimistic upper bound for what a glossary can do. It is not a clinical tool and must not be used to assess real people.

## Author
Muhammad Zeeshan Ali, BS Computer Science, University of Management and Technology, Lahore
