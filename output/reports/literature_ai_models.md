# Which model families are most used for learning-based vehicle routing and capacitated clustering

Read date for every number and quote below: 2026-11-11.

## How I got this, and what it is worth

- I used web search only. I opened no full paper and no live Semantic Scholar, OpenAlex or Google Scholar page.
- The search tool returns short summaries of cached pages. So every citation count and every survey sentence below is a **snippet reading** and is tagged "(snippet)". The page behind each number was cached on a date I cannot see. Counts from different caches disagree, so I give the range.
- I read no OpenAlex count. Where I write "not read", I do not have a number.
- "Google Scholar (GS) profile" means a count shown next to the paper on an author's profile page in a search result. "S2" means Semantic Scholar.
- No survey I could reach gives a count of papers per model family. The ranking in section 2 therefore rests on survey wording, wording in method papers, and citation counts of anchor papers. That is indirect evidence.

---

## 1. Ranked list of model families

Order is my judgement from the evidence below. Section 2 explains the order and how sure I am.

### Rank 1. Attention / Transformer encoder-decoder trained with reinforcement learning (construction), plus attention-based improvement methods

Anchor papers:

1. Kool, van Hoof, Welling. "Attention, Learn to Solve Routing Problems!" ICLR 2019. https://arxiv.org/abs/1803.08475 (OpenReview id ByxBFsRqYm).
   - S2 pages (snippet): 1,299; 1,338; 1,404; 1,424; 1,433 (pages cached at different times).
   - GS profiles (snippet): 3,108 and 2,734 (Kool profile), 3,171 and 3,126 (Welling profile), 2,460 (the arXiv-preprint record).
   - Aggregator sites, not primary indexes (snippet): Liner 1,286, Emergent Mind 1,051.
   - Venue year differs by source: ICLR 2019 in most; an S2 BibTeX key says 2018.
2. Kwon, Choo, Kim, Yoon, Min, Gwon. "POMO: Policy Optimization with Multiple Optima for Reinforcement Learning." NeurIPS 2020. https://arxiv.org/abs/2010.16011
   - S2 paper page (snippet): 473. S2 author page of a co-author: 585.
   - GS profiles (snippet): 623 (Kwon profile); 977 and 517 (Choo profile, English and Korean pages cached at different times).
   - Aggregator (snippet): Liner 380, undated.
   - Abstract (snippet): tested on TSP, CVRP and knapsack; 0.14% gap on TSP100.
3. Wu, Song, Cao, Zhang, Lim. "Learning Improvement Heuristics for Solving Routing Problems." IEEE TNNLS 33(9):5057-5069. Year shown as 2021 in GS and 2022 in one citing paper. https://arxiv.org/abs/1912.05784 (self-attention policy that picks the next solution; this is the improvement-based branch).
   - GS (snippet): 573.
   - S2 count: not read.

Also seen (not counted as anchors): Sym-NCO, Kim, Park, Park, NeurIPS 2022, pp. 1936-1949. GS query page (snippet): "cited by 109". Neural Large Neighbourhood Search for CVRP (Hottung and Tierney): count not read.

What surveys and papers say about how common it is (all snippet):

- Wu et al., "Neural Combinatorial Optimization Algorithms for Solving Vehicle Routing Problems: A Comprehensive Survey with Perspectives," arXiv 2406.00415 (2024). Sentence as the search tool returned it: "Ever since, AM has become a prevalent encoder model choice, adopted by many L2C solvers as the backbone structure." (AM = Kool's attention model; L2C = learning to construct.)
- Same survey, as summarised by the tool: AM adopts the Transformer and reaches strong results on several routing problems with up to 100 nodes.
- Method papers, not surveys, with stronger wording. RouteFinder (arXiv 2406.15007): AM is "the de-facto standard in recent works". USPR (arXiv 2505.05119): the Kool approach "remains the de facto basis for most modern neural VRP approaches". These are the authors' own claims, not counts.
- ICLR 2025 AGFN paper (proceedings.iclr.cc, paper b210c387...): "many current construction-based neural solvers predominantly utilize Transformer architectures" (snippet, truncated).
- ICLR 2025 slides (iclr.cc/media/iclr-2025/Slides/33144.pdf): constructive solvers for VRPs commonly use "a Transformer-based encoder-decoder framework as their policy network" (snippet).
- Counterpoint: a 2025 paper on constraint tightness uses the LEHD model as its backbone, so AM is not the only default now (snippet, arXiv 2505.24627).

### Rank 2 (low confidence, close to rank 3). Pointer networks: recurrent encoder-decoder with attention over inputs

Anchor papers:

1. Vinyals, Fortunato, Jaitly. "Pointer Networks." NeurIPS (NIPS) 2015. https://arxiv.org/abs/1506.03134 (supervised, TSP among other tasks).
   - S2 page (snippet): about 3,227 (cache looks old).
   - GS (Jaitly profile, snippet): 5,200.
   - Aggregators (snippet): Emergent Mind 2,873, Liner 3,113.
   - Caution: this paper is cited far outside routing, so the count says little about routing use.
2. Bello, Pham, Le, Norouzi, Bengio. "Neural Combinatorial Optimization with Reinforcement Learning." arXiv 1611.09940. S2 shows the venue as ICLR 2017 in one snippet and 2016 in another; I did not confirm it against proceedings.
   - S2 (snippet): 1,533; 1,648; 1,534 (the last from a reference listing).
   - GS (Bello profile, snippet): 3,052.
3. Nazari, Oroojlooy, Snyder, Takac. "Reinforcement Learning for Solving the Vehicle Routing Problem." NeurIPS 2018. https://arxiv.org/abs/1802.04240 (extends pointer-style RL to capacitated VRP with demands).
   - S2 (snippet): 965 on the paper page; 1,023 and 804 in two other pages' reference lists.
   - GS (Nazari profile, snippet): 2,211.

What surveys say (snippet):

- A review quoted in a citing paper (arXiv 2503.12662, TuneNSearch): Vinyals et al. introduced pointer networks trained with supervised learning on TSP; Bello et al. moved to reinforcement learning, which removed the need for near-optimal labels. This describes the family as the early approach.
- Alanzi and Menai, "Solving the traveling salesman problem with machine learning: a review of recent advances and challenges," Artificial Intelligence Review 58, article 267 (2025). Tool summary: it groups ML methods into pointer-network, GNN, Transformer, hybrid and multi-model approaches, and treats the first three as key families. It does not rank them in what I could see.
- Wu et al. 2024 survey (arXiv 2406.00415), tool summary: graph pointer networks pair a GNN encoder with a pointer network. The family and the GNN family overlap.

### Rank 3. Graph neural networks (your family): supervised edge prediction or heatmaps, and GNN with reinforcement learning

Anchor papers:

1. Joshi, Laurent, Bresson. "An Efficient Graph Convolutional Network Technique for the Travelling Salesman Problem." arXiv 1906.01227 (2019); also an INFORMS meeting version.
   - GS (snippet): 671 (GS result listing) and 758 (Joshi profile, INFORMS entry; may be a separate record).
   - S2 (snippet): figures of 279, 394 and 418 appeared. The tool noted 394 may belong to a different Joshi paper. I treat the S2 count as not reliably read.
2. Fu, Qiu, Zha. "Generalize a Small Pre-trained Model to Arbitrarily Large TSP Instances." AAAI 2021, pp. 7474-7482. https://arxiv.org/abs/2012.10658 (supervised GNN heatmap plus Monte Carlo tree search).
   - GS (snippet): 254. S2: not read.
3. Khalil, Dai, Zhang, Dilkina, Song. "Learning Combinatorial Optimization Algorithms over Graphs." NeurIPS 2017 (GNN embedding with deep Q-learning). Source page: Google Scholar article view.
   - GS (snippet): 2,573 (article page), 2,584 (Dai profile). S2 (snippet): 1,331; 1,355; 1,612 (from reference lists).
4. For capacitated clustering specifically: Falkner and Schmidt-Thieme. "Neural Capacitated Clustering." IJCAI 2023. https://ijcai.org/proceedings/2023/410 ; https://arxiv.org/abs/2302.05134. Tool summary (snippet): a graph-based neural scorer, trained on earlier good solutions, plugged into the assignment step of capacitated k-means; covers capacitated p-median and capacitated centered clustering; also adapted to cluster-first route-second routing. Citation count: not read.

What surveys say (snippet):

- Cappart et al., "Combinatorial Optimization and Reasoning with Graph Neural Networks," JMLR 24(130), 2023 (arXiv 2102.09544). Abstract wording as returned: "a surge of interest in using graph neural networks as a key building block for combinatorial tasks". This says the topic is active. It does not say GNNs are the most used.
- The heatmap-plus-MCTS line is mostly on TSP, and it has been challenged. Position paper arXiv 2406.03503 (authors not read), snippet: heatmap-guided MCTS methods "significantly underperform compared to LKH-3, regardless of the allocated runtime or fine-tuning of MCTS parameters". An ICLR 2026 paper (proceedings.iclr.cc, "Beyond the Heatmap") argues that a well-tuned MCTS with simple heatmaps matches complex learned heatmap generators (snippet).
- Boundary note (my inference, not a source statement): the attention model's encoder is attention over a fully connected graph. Some authors would file it under GNNs. If you count it that way, GNN-style encoders are rank 1. I kept them apart because papers and surveys name them as separate lines.

### Rank 4 (tie, low confidence). Large language model approaches

Anchor papers:

1. Romera-Paredes et al. "Mathematical discoveries from program search with large language models" (FunSearch). Nature 625:468-475 (2024). Not a routing paper (cap set, bin packing).
   - S2 (snippet): 547 to 601 (578 and 601 on two pages).
2. Liu, Tong, Yuan, Lin, Luo, Wang, Lu, Zhang. "Evolution of Heuristics: Towards Efficient Automatic Algorithm Design Using Large Language Model" (EoH). ICML 2024. https://arxiv.org/abs/2401.02051
   - S2 (snippet): 155 (the tool judged the cache about two years old).
3. Ye, Wang, Cao, Berto, Hua, Kim, Park, Song. "ReEvo: Large Language Models as Hyper-Heuristics with Reflective Evolution." NeurIPS 2024, pp. 43571-43608.
   - GS (Cao profile, snippet): 598. S2 (snippet): 5 on the old arXiv record under the earlier title. The two do not describe the same record, so I do not take the gap as a dispute.
4. Preprint with routing focus: Li et al. "ARS: Automatic Routing Solver with Large Language Models," arXiv 2502.15359. Preprint only; author list changed between versions (snippet). Count not read.

What surveys say (snippet):

- Xiu, Shen, Zhu, Liu. "Vehicle Routing Problem Meets Large Language Models: An Overview and Perspectives," arXiv 2607.00604 (July 2026, marked in progress). It sorts work into three roles: turning requirements into models, generating heuristics or route plans, and coordinating tools and neural solvers. Sentence: "Direct route generation remains fragile in large combinatorial spaces where feasibility and quality must be maintained simultaneously." Most of the work shown is heuristic design, not the LLM solving routes itself.

### Rank 4 (tie, low confidence). Classical machine learning inside exact solvers or heuristics (trees, forests, small networks for branching, column or arc selection)

Anchor papers:

1. Khalil, Le Bodic, Song, Nemhauser, Dilkina. "Learning to Branch in Mixed Integer Programming." AAAI 2016, pp. 724-731. DOI 10.1609/aaai.v30i1.10080. Not routing-specific.
   - S2 (snippet): 246 and 338 on two pages; 398 and 337 in reference lists.
2. Morabit, Desaulniers, Lodi. "Machine-Learning-Based Column Selection for Column Generation." Transportation Science 55(4):815-831 (2021). DOI 10.1287/trsc.2021.1045. Tested on vehicle and crew scheduling and on VRP with time windows.
   - GS (Morabit profile, snippet): 145. (An EconPapers figure of 3 is a different kind of count and I ignore it.)
3. Morabit, Desaulniers, Lodi. "Machine-Learning-Based Arc Selection for Constrained Shortest Path Problems in Column Generation." INFORMS Journal on Optimization 5(2):191-210 (2023). DOI 10.1287/ijoo.2022.0082. https://arxiv.org/abs/2201.02535
   - GS (snippet): 49.
4. Also seen: "Two-Stage Learning to Branch in Branch-Price-and-Cut Algorithms for Solving Vehicle Routing Problems Exactly," Operations Research, DOI 10.1287/opre.2023.0615. Authors and count not read. Snippet: uses classifiers (logistic regression, random forests, neural networks) to flag arcs to remove; about 45% and 50% time cut versus a hand-made branching rule on CVRP and VRP with time windows (ResearchGate fragments, so low trust).

What surveys say:

- Bengio, Lodi, Prouvost. "Machine Learning for Combinatorial Optimization: a Methodological Tour d'Horizon." EJOR 290(2):405-421 (2021). GS (snippet): 2,925 (Lodi profile), 2,715 (another locale), 2,843 (Prouvost profile). S2 (snippet): 665 and 668. I found no sentence in it that says how common this family is for routing.
- I found no survey sentence that ranks this family for routing. Work in this family is mostly in the OR literature and is rarely compared with the neural solvers above.

### Rank 6. Diffusion models

Anchor papers:

1. Sun and Yang. "DIFUSCO: Graph-based Diffusion Solvers for Combinatorial Optimization." NeurIPS 2023. https://proceedings.neurips.cc/paper_files/paper/2023/file/0ba520d93c3df592c83a611961314c98-Paper-Conference.pdf
   - GS (Sun profile, snippet): 449. S2 (snippet): 198 (older cache).
   - Snippet: narrows the gap to ground-truth on TSP-500 from 1.76% to 0.46%. It uses a graph network inside the diffusion model, so it overlaps with the GNN family.
2. Li, Guo, Wang, Yan. "From Distribution Learning in Training to Gradient Search in Testing for Combinatorial Optimization" (T2T). NeurIPS 36:50020-50040 (2023).
   - GS (snippet): 202 (Guo profile), 199 (Li profile). S2 (snippet): 95.
3. Li et al. "Fast T2T: Optimization Consistency Speeds Up Diffusion-Based Training-to-Testing Solving for Combinatorial Optimization." NeurIPS 2024. https://arxiv.org/abs/2502.02941
   - GS (snippet): 78, 81 and 87 on three pages. S2 count: not read (a 95 figure that appeared belongs to T2T).
- CVRP use: EDISCO (arXiv 2610.04953) and CAM (arXiv 2605.30920) report CVRP results; both are recent preprints, read as snippets only; counts not read.

What surveys say (snippet): an SSRN survey, Khosravi et al., "Diffusion Models for Combinatorial Optimization: A Survey" (2026), describes a rapidly growing body of work (tool paraphrase, not a verified quote). From the snippets, work on TSP is much larger than on CVRP (my reading of the results, not a survey statement).

### Seen but not scored as separate families

- Learning to improve (Wu 2021 above, DACT, NeuOpt, NLNS) is a way of using the models above, not a family. Wu et al. 2024 tables list Transformer as the architecture for DACT and NeuOpt (snippet).
- Learned partitioning for capacitated routing: Neural CFRS via optimal transport (Chin and Schiffer, 2026 arXiv 2605.09301) and an LLM-guided adaptive cluster-first route-second method (arXiv 2606.31820). Both preprints, snippet only, counts not read.
- Constrained clustering with a GNN trained by RL (arXiv 2402.10177). Constraints there are connectivity and distance, not capacity.

---

## 2. Besides GNNs, which two families are the most used?

**Short answer:**

1. Attention / Transformer encoder-decoder trained with reinforcement learning (Kool 2019, POMO 2020, and follow-ups). Sure: fairly.
2. Pointer networks (recurrent encoder-decoder with RL, Vinyals 2015, Bello 2017, Nazari 2018). Sure: low to medium.

**GNNs are not the most-used family.** On the evidence I could read, the order is:

1. Attention / Transformer with RL.
2. Pointer network with RL, and GNN (supervised heatmap or GNN with RL). I cannot separate these two.
3. LLM heuristic design and classical ML inside exact solvers. I cannot separate these two. LLM work is growing fast. The classical work is steady and sits mostly in the OR literature.
4. Diffusion. It is the newest, and it is concentrated on TSP.

**Evidence for rank 1.**

- A 2024 survey sentence says AM became "a prevalent encoder model choice, adopted by many" construction solvers (snippet).
- Several 2024-2026 method papers call it the "de-facto standard" or "de facto basis" (snippets). These are claims by authors, not counts.
- The RL4CO benchmark library (arXiv 2306.17100) builds its routing comparison around AM, POMO and Sym-NCO (snippet).
- Anchor citations are the highest among routing-specific papers: Kool at about 1,300 to 1,400 on S2 and about 2,500 to 3,200 on GS, then POMO and Wu 2021 in the hundreds.

**Evidence for rank 2 (weaker).**

- Routing-specific pointer-network anchor Nazari 2018 has 804 to 1,023 on S2 and 2,211 on GS. The GNN heatmap anchors Joshi 2019 and Fu 2021 are lower (roughly 250 to 760 on GS). The GNN with RL anchor Khalil 2017 is as high as Nazari (2,573 on GS).
- Surveys describe pointer networks as the early approach (snippet). So this rank reflects how much the family was cited and built on, not proof of heavy use in 2026 work. Recent papers I saw use the attention model as the base, not the pointer network.
- Vinyals and Bello counts are inflated by use outside routing.

**Why the near-ties stay near-ties.** The counts come from different caches and different ages of paper. Older papers have had more years to collect citations. Citations measure being cited, not being used. I could not count papers per family.

**Which two to pick, if you must justify it.** The attention / Transformer family is the safest pick: the evidence is strong and consistent. For the second comparison, pointer networks have the better citation record among non-GNN families, but a reviewer may see them as dated next to the attention model. If you prefer recency over citations, the evidence points to LLM-guided heuristic design as the fastest-growing alternative, but it is a different kind of method (it writes heuristics, it does not learn a route policy), and its usage is not established by anything I read.

**Capacitated clustering specifically.** I found one direct neural method for general capacitated clustering (Neural Capacitated Clustering, IJCAI 2023, GNN based) and a few 2026 preprints. I found no survey on learning for capacitated clustering. So the ranking above is for vehicle routing, and I carry it over to clustering without direct support.

---

## 3. How papers usually compare these models

All of this is from snippets of method papers and surveys. I did not read the experiment sections in full.

**Instances.**

- Most neural routing papers train and test on randomly generated instances (uniform points) at fixed sizes, and re-run baselines on the same test instances. One paper says it ran all baselines itself on the same test instances taken from Kool et al. (paper not identified in my notes).
- Test sets in the papers I saw are about 1,000 instances for the standard sizes. Large-scale sets are smaller: 100 instances each, except two sets with 16 (CVRP10K and CVRP1M) (snippet from one paper, not identified). I did not verify how many test instances Kool et al. used.
- Generalisation is often tested on CVRPLIB benchmark instances. One IJCAI 2024 paper reports the average gap to best-known solutions and copies the HGS and LKH3 CVRPLIB numbers from the HGS paper (snippet).

**Metrics.**

- Objective value (route length) and gap in percent to a reference solver. References seen: Concorde for TSP; HGS or LKH-3 for CVRP. A NeurIPS 2024 paper uses HGS for CVRP gaps and runs LKH3 with 10,000 trials, 1 run (snippet).
- Run time per instance or per set. Some papers give every method the same wall-time limit, for example 5, 60, 120 and 240 seconds (snippet, paper not identified).
- Decoding setting matters: greedy; sampling; multi-start with instance augmentation (for example x1 and x16). One study runs every neural method greedy to compare basic ability (snippets).
- Check the reference solver. One 2026 paper's headline gap is "relative to LKH-3" while its table note says the gaps are relative to HGS (snippet). Gaps from different papers are not directly comparable.

**Typical sizes.**

- Training and main tables: 20, 50 and 100 nodes for TSP and CVRP. The attention model is described as strong up to 100 nodes (snippet). RL4CO reports AM, POMO and Sym-NCO mostly at 20 and 50 nodes for TSP and CVRP (snippet).
- Large-scale work goes to 1,000, 10,000 and beyond. A 2025 paper reports CVRP1M instances that LKH3 and HGS cannot run in their limits (snippet).
- Diffusion and heatmap papers report TSP-50 to TSP-10,000 (DIFUSCO TSP-500; EDISCO TSP 100 to 10,000 and CVRP 50 to 2,000) (snippets).

**What the comparisons show, and warnings.**

- RL4CO (snippet): AM with small encoder changes and enough samples can match or beat POMO and Sym-NCO on 20 and 50 nodes. The ordering AM < POMO < Sym-NCO changes with the decoding scheme. With augmentation the differences shrink. A table in the snippet shows CVRP AM (rollout) at 5.30 and POMO at 3.99; I could not tie the node count or unit to it, so I do not rely on it.
- The heatmap-plus-MCTS line is reported to lose to LKH-3 under fair settings (snippet, section 1 rank 3).
- Accorsi, Lodi, Vigo, "Guidelines for the Computational Testing of Machine Learning approaches to Vehicle Routing Problems," Operations Research Letters 2022 (arXiv 2109.13983) say differing evaluation practices likely keep the OR community from adopting ML routing methods (snippet). I did not read the guidelines themselves.
- Li et al., "An Overview and Experimental Study of Learning-based Optimization Algorithms for Vehicle Routing Problem," arXiv 2107.07076 (IEEE/CAA J. Automatica Sinica 2022): tested four methods; concluded that adding heuristic search can improve learning ability and sample efficiency (snippet).
- Practical rule for your own comparison: same instances, same reference solver, same time budget, same decoding setting, and report gap, time and the instance size together.

---

## 4. Could not verify

- No survey I could reach counts papers per model family. I searched for one several ways and found none. An empty result is not proof that none exists.
- Survey sentences were read only through search-tool summaries. I did not read the full text of Bogyrbayeva et al. (arXiv 2205.02453; IEEE T-ITS 2024, 25(6):4754-4772), Zhou et al. (arXiv 2507.00218; Transportation Research Part E 2025), Wu et al. (arXiv 2406.00415), the neural routing solver survey (arXiv 2602.21761), or the 2025 TSP reviews. In particular I did not see what Bogyrbayeva et al. and Zhou et al. say about family popularity. Quotes marked as returned by the tool may differ in small ways from the paper text.
- No OpenAlex count was read for any paper. No live Semantic Scholar or Google Scholar page was opened. All counts are cached snapshots with unknown dates.
- Counts for the survey papers: Bogyrbayeva et al. GS 138 for the T-ITS version (snippet); S2 author page showed 46 and 27, but the tool said these may not be total counts. Counts not read: Wu et al. 2024, Zhou et al. 2025, the 2026 surveys, Neural Capacitated Clustering, Neural Large Neighbourhood Search, EDISCO, CAM, ARS, the Two-Stage Learning to Branch paper, and Kool et al. on OpenAlex.
- FunSearch is not a routing paper. I use it only as the LLM-for-optimisation anchor.
- Venue of Bello et al. (ICLR 2016 or 2017) not confirmed against proceedings. Venue year of Kool et al. differs between sources (2018 or 2019). TNNLS year for Wu et al. differs (2021 or 2022).
- Authors of the heatmap position paper (arXiv 2406.03503) and of the Two-Stage Learning to Branch paper were not read. The arXiv id of Sym-NCO was not read.
- Number of test instances used by Kool et al. was not verified. The "about 1,000" figure is from other papers.
- Several 2026 items (arXiv ids starting 26xx, the SSRN diffusion survey, the LLM-VRP overview) were seen only as snippets and are preprints; they may change or be withdrawn. The ARS preprint had an authorship dispute noted in the snippet.
- Gradient-boosted trees for column or arc selection: my searches returned no routing paper using gradient boosting by name. The two arc and column selection papers above use other learners or I did not see the model type. This is an empty search, not proof.
- Families not searched: genetic programming and hyper-heuristics without LLMs, plain Q-learning on tabular states, and non-English literature.
- The search tool is US-only and summarises pages. Three times it told me that author names or author orders I had guessed from memory in my own queries were wrong; I used its corrections. My queries used paper titles and author names as literature identifiers only; none came from your brief. It may still contain errors I could not detect.
