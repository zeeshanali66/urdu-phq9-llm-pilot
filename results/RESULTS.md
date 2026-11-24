# Results

Unparseable judge outputs (after one retry): 0 of 1050

## Main table (MAE in PHQ-9 points; bias < 0 means the judge UNDER-estimates severity)

```
      judge condition  n  MAE MAE_95CI  bias  band_acc  QWK  sensitivity@10  specificity@10
 gemma3 12b        en 30 0.77  0.5-1.1  0.43      0.83 0.96            1.00            0.83
 gemma3 12b        ur 30 1.23  0.9-1.6 -0.23      0.80 0.95            1.00            0.83
 gemma3 12b        ru 30 1.53  1.0-2.2 -0.20      0.73 0.90            1.00            0.83
 gemma3 12b     ur2en 30 1.97  1.3-2.7 -0.57      0.60 0.89            0.94            0.83
 gemma3 12b     ru2en 30 1.30  0.9-1.7  0.30      0.73 0.93            1.00            0.83
 gemma3 12b    ur_rag 30 2.33  1.6-3.1 -2.00      0.67 0.91            0.83            1.00
 gemma3 12b    ru_rag 30 0.93  0.6-1.3  0.20      0.83 0.96            0.94            0.92
 gemma4 12b        en 30 0.17  0.0-0.4  0.03      0.97 0.99            1.00            0.92
 gemma4 12b        ur 30 0.83  0.4-1.3  0.57      0.87 0.97            1.00            0.83
 gemma4 12b        ru 30 1.00  0.6-1.5  0.60      0.83 0.96            1.00            0.92
 gemma4 12b     ur2en 30 0.80  0.4-1.3  0.73      0.90 0.98            1.00            0.92
 gemma4 12b     ru2en 30 0.90  0.5-1.4  0.77      0.87 0.97            1.00            0.83
 gemma4 12b    ur_rag 30 0.47  0.1-0.9  0.40      0.93 0.98            1.00            0.92
 gemma4 12b    ru_rag 30 0.13  0.0-0.3  0.07      1.00 1.00            1.00            1.00
llama3.1 8b        en 30 1.40  1.1-1.8  1.20      0.80 0.95            1.00            0.83
llama3.1 8b        ur 30 2.50  1.9-3.1  1.10      0.57 0.88            0.89            0.75
llama3.1 8b        ru 30 2.73  2.0-3.5 -0.40      0.63 0.86            1.00            0.83
llama3.1 8b     ur2en 30 3.20  2.0-4.6 -1.33      0.60 0.71            0.94            0.92
llama3.1 8b     ru2en 30 3.10  2.3-3.9  0.17      0.53 0.80            1.00            0.75
llama3.1 8b    ur_rag 30 1.60  1.1-2.2 -1.13      0.80 0.95            0.94            1.00
llama3.1 8b    ru_rag 30 2.37  1.7-3.1 -1.57      0.50 0.81            0.89            1.00
 qwen2.5 7b        en 30 3.03  2.1-4.0 -2.63      0.50 0.76            0.83            1.00
 qwen2.5 7b        ur 30 3.60  2.5-4.7 -3.60      0.47 0.70            0.78            1.00
 qwen2.5 7b        ru 30 3.43  2.4-4.6 -3.23      0.43 0.72            0.78            1.00
 qwen2.5 7b     ur2en 30 4.20  2.8-5.9 -4.07      0.37 0.64            0.72            1.00
 qwen2.5 7b     ru2en 30 3.33  2.2-4.5 -3.00      0.57 0.75            0.83            1.00
 qwen2.5 7b    ur_rag 30 3.90  2.9-5.0 -3.70      0.40 0.68            0.61            1.00
 qwen2.5 7b    ru_rag 30 2.60  1.9-3.4 -2.20      0.50 0.84            0.89            1.00
 qwen3.5 9b        en 30 0.83  0.5-1.3 -0.17      0.80 0.95            0.94            0.92
 qwen3.5 9b        ur 30 1.33  0.9-1.9  0.07      0.70 0.93            0.89            0.83
 qwen3.5 9b        ru 30 1.70  1.2-2.2 -0.43      0.63 0.91            0.89            0.83
 qwen3.5 9b     ur2en 30 1.80  1.3-2.4 -1.13      0.63 0.91            0.89            0.92
 qwen3.5 9b     ru2en 30 1.10  0.7-1.6 -0.57      0.70 0.93            0.89            1.00
 qwen3.5 9b    ur_rag 30 1.17  0.8-1.6 -0.50      0.77 0.94            1.00            1.00
 qwen3.5 9b    ru_rag 30 1.23  0.7-2.0 -1.03      0.73 0.94            0.94            1.00
```

## Paired permutation tests (same persona, different language)

```
      judge      compare  n  mean_diff(b-a)  p_perm  p_holm
 gemma3 12b     en vs ur 30           0.467   0.085   1.000
 gemma3 12b     en vs ru 30           0.767   0.074   1.000
 gemma3 12b  ur vs ur2en 30           0.733   0.069   1.000
 gemma3 12b  ru vs ru2en 30          -0.233   0.589   1.000
 gemma3 12b ur vs ur_rag 30           1.100   0.004   0.105
 gemma3 12b ru vs ru_rag 30          -0.600   0.144   1.000
 gemma4 12b     en vs ur 30           0.667   0.002   0.068
 gemma4 12b     en vs ru 30           0.833   0.000   0.006
 gemma4 12b  ur vs ur2en 30          -0.033   1.000   1.000
 gemma4 12b  ru vs ru2en 30          -0.100   0.771   1.000
 gemma4 12b ur vs ur_rag 30          -0.367   0.050   1.000
 gemma4 12b ru vs ru_rag 30          -0.867   0.000   0.014
llama3.1 8b     en vs ur 30           1.100   0.007   0.166
llama3.1 8b     en vs ru 30           1.333   0.010   0.237
llama3.1 8b  ur vs ur2en 30           0.700   0.383   1.000
llama3.1 8b  ru vs ru2en 30           0.367   0.352   1.000
llama3.1 8b ur vs ur_rag 30          -0.900   0.002   0.064
llama3.1 8b ru vs ru_rag 30          -0.367   0.554   1.000
 qwen2.5 7b     en vs ur 30           0.567   0.201   1.000
 qwen2.5 7b     en vs ru 30           0.400   0.316   1.000
 qwen2.5 7b  ur vs ur2en 30           0.600   0.418   1.000
 qwen2.5 7b  ru vs ru2en 30          -0.100   0.800   1.000
 qwen2.5 7b ur vs ur_rag 30           0.300   0.547   1.000
 qwen2.5 7b ru vs ru_rag 30          -0.833   0.106   1.000
 qwen3.5 9b     en vs ur 30           0.500   0.027   0.601
 qwen3.5 9b     en vs ru 30           0.867   0.004   0.099
 qwen3.5 9b  ur vs ur2en 30           0.467   0.214   1.000
 qwen3.5 9b  ru vs ru2en 30          -0.600   0.124   1.000
 qwen3.5 9b ur vs ur_rag 30          -0.167   0.614   1.000
 qwen3.5 9b ru vs ru_rag 30          -0.467   0.182   1.000
```

## Mean prompt tokens per judgement (same content, different language)

```
cond            en     ur     ru  ur2en  ru2en  ur_rag  ru_rag
judge                                                         
gemma3 12b   408.0  446.0  467.0  426.0  427.0   960.0   927.0
gemma4 12b   410.0  448.0  469.0  426.0  428.0   962.0   929.0
llama3.1 8b  397.0  742.0  512.0  417.0  413.0  1390.0  1088.0
qwen2.5 7b   395.0  736.0  513.0  402.0  402.0  1392.0  1102.0
qwen3.5 9b   409.0  544.0  517.0  420.0  422.0  1129.0  1038.0
```

## Item-level bias, averaged over judges (negative = symptom under-detected)

```
condition        en    ur    ru
item                           
appetite      -0.13 -0.15 -0.20
concentration -0.04  0.04 -0.05
energy         0.11  0.21  0.11
interest       0.03 -0.00  0.03
mood           0.03 -0.03 -0.07
psychomotor   -0.19 -0.47 -0.45
self-harm      0.01  0.00  0.01
self-worth    -0.01 -0.01 -0.03
sleep         -0.04 -0.01 -0.09
```
