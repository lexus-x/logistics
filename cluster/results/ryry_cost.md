Estimated hire cost from public list prices (two sources). Won, all 97 jobs.

| method | trucks | road km | cost, source 1 | vs real | cost, source 2 | vs real | per stop (source 1) |
|---|---|---|---|---|---|---|---|
| Real dispatch | 2,517 | 655,445 | 426.5 M | +0.0 % | 403.6 M | +0.0 % | 66,699 |
| Rule-based (Ryry's paper) | 2,092 | 570,936 | 391.5 M | -8.2 % | 371.3 M | -8.0 % | 61,220 |
| k-means | 2,702 | 680,366 | 453.8 M | +6.4 % | 428.8 M | +6.2 % | 70,967 |
| Agglomerative | 2,235 | 575,984 | 394.3 M | -7.6 % | 373.5 M | -7.5 % | 61,651 |
| GNN alone | 2,241 | 582,990 | 397.0 M | -6.9 % | 376.2 M | -6.8 % | 62,082 |
| Optimizer | 1,920 | 526,086 | 367.5 M | -13.8 % | 348.8 M | -13.6 % | 57,469 |
| Optimizer, 8 nearest | 1,941 | 518,682 | 365.3 M | -14.4 % | 346.3 M | -14.2 % | 57,125 |
| GNN + optimizer | 1,933 | 516,628 | 364.6 M | -14.5 % | 345.6 M | -14.4 % | 57,011 |
| GNN + optimizer, long run | 1,912 | 519,762 | 364.9 M | -14.4 % | 346.2 M | -14.2 % | 57,067 |

List prices, undated, not contract rates. Fare = base + per km by truck size, plus 10,000-30,000 won per extra address. No waiting, loading-help, toll or night fees. The real dispatch's trucks are read from its free-text labels.
