# Public truck-hire list prices in South Korea (collected 2026-11-11)

Collected by a Sonnet 5.5 worker with web search. These are brokers' advertised one-way prices for hiring a whole truck
with its driver (독차, forklift loading assumed). None of the pages is dated, none is a Changwon-origin table, and
none says how far contract rates differ. S1 was read twice with matching values, the others once, through a
summarising fetch tool. Use them to compare plans, not to budget.

## Fares in won by distance band ("up to" that many km)

| Source | Truck | 50 km | ~110 km | 200 km | 300 km | 400 km | 500 km |
|---|---|---|---|---|---|---|---|
| S1 | 1톤 | 60,000 | 90,000 | 130,000 | 170,000 | 200,000 | 250,000 |
| S1 | 1.4톤 | 70,000 | 100,000 | 140,000 | 180,000 | 220,000 | 260,000 |
| S1 | 2.5톤 | 90,000 | 120,000 | 170,000 | 240,000 | 280,000 | 320,000 |
| S1 | 3.5톤 | 100,000 | 130,000 | 190,000 | 260,000 | 300,000 | 340,000 |
| S1 | 5톤 장축 | 120,000 | 150,000 | 210,000 | 280,000 | 320,000 | 360,000 |
| S1 | 5톤 플러스 | 130,000 | 170,000 | 230,000 | 300,000 | 350,000 | 390,000 |
| S1 | 11톤 | 150,000 | 200,000 | 270,000 | 370,000 | 420,000 | 470,000 |
| S2 | 1톤 | 50,000 | 80,000 | 120,000 | 160,000 | 190,000 | 240,000 |
| S2 | 1.4톤 | 60,000 | 90,000 | 130,000 | 170,000 | 200,000 | 250,000 |
| S2 | 2.5톤 | 80,000 | 120,000 | 170,000 | 230,000 | 270,000 | 310,000 |
| S2 | 3.5톤 | 90,000 | 120,000 | 180,000 | 240,000 | 280,000 | 330,000 |
| S2 | 5톤 | 110,000 | 140,000 | 200,000 | 270,000 | 310,000 | 350,000 |
| S2 | 5톤 플러스 | 120,000 | 160,000 | 220,000 | 290,000 | 340,000 | 370,000 |
| S2 | 11톤 | 150,000 | 190,000 | 280,000 | 370,000 | 410,000 | 450,000 |

- S1: https://www.xn--3e0b77hn2heyf78a22qfc18f3xb509f.kr/html/sub0201.php (a dispatcher in Cheongju; VAT not stated)
- S2: http://kumsule.com/cost2 (footer ©2026; "참고용"; VAT not stated)
- S3: https://www.xn--3e0bx5x8ua595aw3jcxhxwb.com/price (VAT excluded; same template as S1, so not independent evidence)
- S4: https://toptrucker.co.kr/ ("기본 참고 금액"; clearly higher: 1톤 60,000 at 50 km, 150,000 at 200 km, 240,000 at 400 km)
- City pairs from Busan: http://www.18008880.co.kr/bbs/content.php?co_id=scharge2 (about 10-20 % above S1 at 400 km)

## Straight-line fits (worker's least squares on the band limits, 50-500 km): won = base + per km

| Truck | S1 | R² | S2 | R² |
|---|---|---|---|---|
| 1톤 | 46,100 + 402 | 0.994 | 36,800 + 403 | 0.992 |
| 1.4톤 | 54,400 + 416 | 0.998 | 46,800 + 403 | 0.992 |
| 2.5톤 | 62,500 + 536 | 0.993 | 60,700 + 524 | 0.991 |
| 3.5톤 | 70,700 + 565 | 0.990 | 68,000 + 539 | 0.990 |
| 5톤 | 90,700 + 565 | 0.990 | 82,700 + 565 | 0.990 |
| 5톤 플러스 | 103,000 + 605 | 0.991 | 96,500 + 595 | 0.987 |
| 11톤 | 124,000 + 731 | 0.986 | 125,000 + 713 | 0.969 |

The tables are stepped, so a line is off by up to 20,000-30,000 won for 2.5톤 and larger.

## Surcharges
- Extra address (한 곳당): 1톤 and 1.4톤 1, 2.5톤 to 5톤 2, 11톤 3. The unit is unlabelled, probably 만원. Source:
  https://www.18000510.com/bbs/content.php?co_id=2_1 ("참고용"). A second figure (20,000 same region, 30,000 other
  region) was seen only in a search snippet and is not verified.
- Waiting: first hour free at loading and at unloading, then per hour 10,000 (1-1.4톤), 20,000 (2.5-5톤), 30,000 (11톤+).
- Driver loads by hand: +20,000 to 30,000. Lift, box or wing body: +10,000 to 30,000. Night or dawn: +10 % (S4).
- Shared loads (혼적) are about 30 % cheaper than a whole truck (https://18996924.co.kr/).
- No round-trip or empty-return discount found.

## Not found
A Changwon-origin table; rates from 센디, 고고엑스, 화물맨, 원콜; any association table; KOTI's surveyed cargo rates
(the 2025 survey report has a chapter on them, but only inside a PDF: https://www.koti.re.kr/user/bbs/frghtSrvOneView.do?bbs_no=72373).
The 2026 안전운임 notice covers only containers and cement.
