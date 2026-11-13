# Literature check for the bulky-delivery work (2026-11-11)

Done by a Sonnet 5.5 worker with web search only. Abstracts and catalogue records were read, not full texts, and many
publisher pages were blocked. Nothing here has been checked a second time: open each paper before citing it. An empty
search result is not proof that nothing exists.

## A. Price of each operational rule: partly done, this exact form appears open
- Kovacs, Golden, Hartl, Parragh 2015, Transportation Science 49(4):796-816. Cost of driver/time consistency (heuristic, no proven bounds). https://econpapers.repec.org/RePEc:inm:ortrsc:v:49:y:2015:i:4:p:796-816
- Matl, Hartl, Vidal 2018, Transportation Science 52(2):239-260. Workload-equity rules on small instances solved to optimality. https://econpapers.repec.org/RePEc:inm:ortrsc:v:52:y:2018:i:2:p:239-260
- Zhang 2021, PhD thesis, Polytechnique Montreal. Cost of last-in-first-out loading with exact methods. https://publications.polymtl.ca/6639
- Bertoli 2018, ANU thesis. Cost of districting (search snippet only). https://openresearch-repository.anu.edu.au/bitstream/1885/146047/1/F.%20Bertoli%20Thesis%202018.pdf

None found for stops per truck, radius, load limit and fleet cap with proven bounds on real bulky-goods data.

## B. Auditing a volume rule of thumb against real loading: the audit appears open, the learned method is done
- Zhang, Chen, Gendreau, Langevin 2022, INFORMS J. Computing 34(3):1419-1436. 2D loading with time windows; a learned model cuts feasibility-checker calls inside branch-and-price. https://econpapers.repec.org/RePEc:inm:orijoc:v:34:y:2022:i:3:p:1419-1436
- Xia, Zhang, IJCAI 2024. Neural predictor of column loading feasibility, 2D plus LIFO. https://www.arxiv.org/abs/2406.12454
- Sun, Kirtonia, Chen 2025, Transportation Science 59(5):1076-1100. ML loading feasibility inside column generation for car carriers. https://ideas.repec.org/a/inm/ortrsc/v59y2025i5p1076-1100.html
- Tamke, Linss, Kuttner, Buscher, arXiv 2024. Exact branch-and-cut for routing with 3D loading. https://arxiv.org/abs/2402.14868

No study found that audits a fixed volume-percentage rule against real packing with real box and truck sizes.

## C. ML shortlists for exact solvers: already done, do not claim
- Morabit, Desaulniers, Lodi 2021, Transportation Science 55(4):815-831. GNN column selection. https://pubsonline.informs.org/doi/10.1287/trsc.2021.1045
- Babaki, Charlin, Jena 2022, CIRRELT report 2022-25. GNN + imitation learning for column choice. https://www.cirrelt.ca/documentstravail/cirrelt-2022-25.pdf
- Morabit et al. 2023, INFORMS J. Optimization 5(2):191-210. ML arc selection for pricing. https://arxiv.org/abs/2201.02535
- Abouelrous et al., arXiv 2025. GNN prunes the pricing graph. https://arxiv.org/abs/2504.08401
- Shen et al., AAAI 2022. ML pricing heuristic, graph colouring (not routing). https://ojs.aaai.org/index.php/AAAI/article/view/21230
- Falkner, Schmidt-Thieme 2023. Neural capacitated clustering (capacity only). https://arxiv.org/abs/2302.05134

## D. The problem itself: partly done
- Ferreira et al. 2023, Applied Sciences 13(5):3285. Heuristic for furniture delivery and installation, no optimality bound. https://novaresearch.unl.pt/en/publications/a-heuristic-approach-to-support-route-planning-for-delivery-and-i/
- Alidaee, Wang, Sua 2023, Logistics 7(4):98. Review of heavy and bulky last-mile delivery. https://econpapers.repec.org/RePEc:gam:jlogis:v:7:y:2023:i:4:p:98-:d:1298201
- Tuma, Ostermeier, Huebner 2024, INFORMS J. Applied Analytics 54(4):312-328. Exact set partitioning for a real retailer, about 8 % saving (details from the search description only). https://ideas.repec.org/a/inm/orinte/v54y2024i4p312-328.html
- Abdellaoui et al., arXiv 2024. Routing recast as constrained clustering (heuristic). https://arxiv.org/abs/2403.14013

No exact method with proven gaps found for real bulky data under this combination of rules.

## E. Dispatch or wait: already done in general, nothing bulky-specific; not built here
- Klapp, Erera, Toriello 2018, EJOR 271(2):519-534. Dispatch waves for same-day delivery. https://econpapers.repec.org/RePEc:eee:ejores:v:271:y:2018:i:2:p:519-534
- Izadkhah et al. 2022, Digital Chemical Engineering 5:100057. Delivery-day windows on real industrial data, up to 12 % saving. https://pure.psu.edu/en/publications/quantifying-the-impact-of-delivery-day-flexibility-on-last-mile-d/
- Voigt, Frank, Kuhn 2025, EJOR 324(2):477-491. "Some-day" delivery option. https://ideas.repec.org/a/eee/ejores/v324y2025i2p477-491.html
- Schrotenboer, Uit het Broek, Buijs, Ulmer, arXiv 2021. Consolidation versus urgency. https://arxiv.org/abs/2108.12608

## F. Public datasets: partly done
- Guo, Yu, Allon, Wang, Zhang 2024, M&SOM 26(4):1358-1371. RiRiShun (Haier) appliance orders with SKU dimensions; order-level, access terms not verified. https://ideas.repec.org/a/inm/ormsom/v26y2024i4p1358-1371.html
- Merchan et al. 2022, Transportation Science. Amazon last-mile data (parcels). https://amazon.science/publications/2021-amazon-last-mile-routing-research-challenge-data-set
- You, Li, arXiv 2026 (PackingGPT). Benchmark from real flat-pack furniture sizes; public release not confirmed. https://arxiv.org/abs/2608.01427

No public set found with real dispatch jobs, truck assignments and stops for bulky goods.

## Verdict
1. **A is the most defensible claim**, with B as a component once the real box dimensions are used.
2. B next, framed as an audit of one rule, not as a method.
3. D and F are supporting points (real data with proven gaps; a possible anonymised release).
4. E is not built. C should not be claimed.

Suggested wording (avoid "first"): "A literature search found cost-of-rule analyses for consistency, workload equity,
LIFO loading, districting and delivery-day flexibility, but none that quantifies, with proven lower bounds, how many
trucks each of four dispatch rules (stops per truck, cluster radius, load limit, fleet cap) costs on real bulky-goods
dispatch data. This paper reports that."

## Could not verify
- Wang et al. 2023 (ML route selection for set partitioning): not found.
- Bertoli, the Zhang thesis details, Tamke's EJOR 2025 venue and Ceschia et al. 2013 (Computers & Industrial Engineering 66(4)) come from search listings or abstracts only.
- The TU Delft load-feasibility thesis (de Wolf): page unreachable.
- Shen et al. AAAI page was blocked; details from the search listing.
