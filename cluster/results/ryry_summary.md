Ryry's 97 jobs, 6395 stops (132 too big for a 1.4-ton ride alone on a bigger truck). Lower bound: Ryry's formula 2181; valid under these rules 1803.

| method | trucks | vs valid bound | vs real dispatch | jobs at the bound | 1.4-ton used | road km | driving h | rule breaks | solve s (max) |
|---|---|---|---|---|---|---|---|---|---|
| real | 2517 | +39.6% | +0.0% | 0 | - | 655,444 | 8,880 | 230 | 0 |
| rule | 2092 | +16.0% | -16.9% | 1 | 829 | 570,936 | 7,856 | 0 | 0 |
| kmeans | 2702 | +49.9% | +7.4% | 0 | 587 | 680,366 | 9,170 | 0 | 0 |
| agg | 2235 | +24.0% | -11.2% | 0 | 517 | 575,984 | 7,844 | 0 | 0 |
| gnn | 2241 | +24.3% | -11.0% | 0 | 482 | 582,989 | 7,956 | 0 | 0 |
| opt | 1920 | +6.5% | -23.7% | 15 | 808 | 526,087 | 7,303 | 0 | 141 |
| knn8 | 1941 | +7.7% | -22.9% | 7 | 825 | 518,682 | 7,185 | 0 | 72 |
| gnn_opt | 1933 | +7.2% | -23.2% | 9 | 845 | 516,628 | 7,163 | 0 | 120 |
| long | 1912 | +6.0% | -24.0% | 15 | 827 | 519,761 | 7,222 | 0 | 4646 |

Solver fell back to its safety net (time limit 60 s): opt 4, gnn_opt 0 jobs. GNN rows are out-of-fold (5 folds by date): each job is planned by a model that never saw it. Real dispatch: its own clusters on the same road distances; rule breaks = clusters over 50 km, 5 stops or a 1.4-ton's 60 %.
