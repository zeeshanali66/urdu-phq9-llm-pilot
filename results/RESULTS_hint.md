# Mitigation 3: fixed frequency table in the prompt

Judges: gemma4:12b, qwen3.5:9b, gemma3:12b. MAE in PHQ-9 points (0-27), bootstrap 95% CI; bias < 0 = under-estimation.

```
     judge    cond  n  MAE MAE_95CI  bias
gemma3:12b      en 30 0.77  0.5-1.1  0.43
gemma3:12b      ur 30 1.23  0.9-1.6 -0.23
gemma3:12b      ru 30 1.53  1.0-2.2 -0.20
gemma3:12b  ur_rag 30 2.33  1.6-3.1 -2.00
gemma3:12b  ru_rag 30 0.93  0.6-1.3  0.20
gemma3:12b ur_hint 30 1.13  0.8-1.5  0.13
gemma3:12b ru_hint 30 0.97  0.6-1.3  0.57
gemma4:12b      en 30 0.17  0.0-0.4  0.03
gemma4:12b      ur 30 0.83  0.4-1.3  0.57
gemma4:12b      ru 30 1.00  0.6-1.5  0.60
gemma4:12b  ur_rag 30 0.47  0.1-0.9  0.40
gemma4:12b  ru_rag 30 0.13  0.0-0.3  0.07
gemma4:12b ur_hint 30 0.33  0.1-0.6  0.07
gemma4:12b ru_hint 30 0.07  0.0-0.2 -0.07
qwen3.5:9b      en 30 0.83  0.5-1.3 -0.17
qwen3.5:9b      ur 30 1.33  0.9-1.9  0.07
qwen3.5:9b      ru 30 1.70  1.2-2.2 -0.43
qwen3.5:9b  ur_rag 30 1.17  0.8-1.6 -0.50
qwen3.5:9b  ru_rag 30 1.23  0.7-2.0 -1.03
qwen3.5:9b ur_hint 30 0.70  0.4-1.0  0.37
qwen3.5:9b ru_hint 30 0.97  0.6-1.4 -0.03
```

## Paired permutation tests (Holm within this table)

```
     judge           compare  n  mean_diff(b-a)  p_perm  p_holm
gemma4:12b     ur vs ur_hint 30          -0.500   0.033   0.495
gemma4:12b     ru vs ru_hint 30          -0.933   0.000   0.000
gemma4:12b ur_rag vs ur_hint 30          -0.133   0.700   1.000
gemma4:12b ru_rag vs ru_hint 30          -0.067   0.752   1.000
gemma4:12b     en vs ur_hint 30           0.167   0.439   1.000
gemma4:12b     en vs ru_hint 30          -0.100   0.496   1.000
qwen3.5:9b     ur vs ur_hint 30          -0.633   0.050   0.700
qwen3.5:9b     ru vs ru_hint 30          -0.733   0.007   0.119
qwen3.5:9b ur_rag vs ur_hint 30          -0.467   0.075   0.975
qwen3.5:9b ru_rag vs ru_hint 30          -0.267   0.562   1.000
qwen3.5:9b     en vs ur_hint 30          -0.133   0.679   1.000
qwen3.5:9b     en vs ru_hint 30           0.133   0.684   1.000
gemma3:12b     ur vs ur_hint 30          -0.100   0.766   1.000
gemma3:12b     ru vs ru_hint 30          -0.567   0.170   1.000
gemma3:12b ur_rag vs ur_hint 30          -1.200   0.007   0.119
gemma3:12b ru_rag vs ru_hint 30           0.033   1.000   1.000
gemma3:12b     en vs ur_hint 30           0.367   0.116   1.000
gemma3:12b     en vs ru_hint 30           0.200   0.424   1.000
```
