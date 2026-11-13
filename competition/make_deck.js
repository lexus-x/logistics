// Competition slides (2nd LogisticSolver 2026, team ANALOG): Version 1 results only, 15 slides, poster colours.
//   NODE_PATH=<scratchpad>/ppt/node_modules node competition/make_deck.js
// Images: figs/slides/*.png (figures rendered at 6x by svg2png.mjs; proto.png cut from figs/proto_results.png).
// shortcut: pptxgenjs and the theme helper live outside the project (scratchpad / skill folder); install them in the project if the deck must outlive this session
const fs = require("fs");
const path = require("path");
const os = require("os");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/home/ubuntu/.claude/skills/synced/0e648cc8-83f9-4087-8207-429837a7574a_b2e6097f-fb1d-41dc-8d96-2f0ff4f7910d/pptx/scripts/apply_theme.js");

const IMG = path.join(__dirname, "figs/slides");
const OUT = path.join(os.homedir(), "reports/LogisticSolver_2026/ANALOG_LogisticSolver2026_Slides.pptx");
const N = JSON.parse(fs.readFileSync(path.join(__dirname, "numbers.json"), "utf8"));

const THEME = {
  name: "ANALOG poster",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1C2430", lt1: "FFFFFF", dk2: "1D3F86", lt2: "EEF4FB",
    accent1: "2F6FDB", accent2: "CF7F2E", accent3: "A3ACB8", accent4: "5B6676", accent5: "DCE8FB", accent6: "7A8594",
    hlink: "2F6FDB", folHlink: "1D3F86",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Team ANALOG";
pres.title = "AI-Based Automatic Dispatch Clustering for Large-Volume Bulky Delivery";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "Title dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.8, y: 0.55, w: 11.7, h: 0.45, fontSize: 14, bold: true, color: C.accent5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.35, w: 7.2, h: 2.75, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.3, w: 6.9, h: 1.05, fontSize: 16, color: C.accent5, valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "team", type: "body", x: 0.8, y: 5.5, w: 7.0, h: 1.55, fontSize: 14, color: C.background1, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Content",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.9, fontSize: 34, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Team ANALOG  |  2nd LogisticSolver 2026", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent4, align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "Closing dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 0.6, w: 11.7, h: 1.0, fontSize: 38, bold: true, color: C.background1, align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------- helpers ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
// picture fitted inside the box (x, y, w, h), centred, aspect kept
function pic(slide, name, x, y, w, h, alt) {
  const file = path.join(IMG, name + ".png");
  const s = pngSize(file);
  let pw = w, ph = (w * s.h) / s.w;
  if (ph > h) { ph = h; pw = (h * s.w) / s.h; }
  slide.addImage({ path: file, x: x + (w - pw) / 2, y: y + (h - ph) / 2, w: pw, h: ph, altText: alt, objectName: "Picture " + name });
  return { x: x + (w - pw) / 2, y: y + (h - ph) / 2, w: pw, h: ph };
}
function card(slide, x, y, w, h, name, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || C.background2 }, line: { type: "none" }, objectName: name });
}
function text(slide, t, o) {
  slide.addText(t, Object.assign({ isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top" }, o));
}
// big number with a label under it
function stat(slide, x, y, w, big, label, name, color) {
  text(slide, big, { x, y, w, h: 0.85, fontSize: 44, bold: true, color: color || C.accent1, valign: "bottom", objectName: name + " number" });
  text(slide, label, { x, y: y + 0.9, w, h: 0.75, fontSize: 15, color: C.accent4, objectName: name + " label" });
}
// navy circle with a white number: the deck's motif for steps
function dot(slide, x, y, label, name, fill) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: fill || C.text2 }, line: { type: "none" }, objectName: name });
  text(slide, String(label), { x, y, w: 0.5, h: 0.5, fontSize: 15, bold: true, color: C.background1, align: "center", valign: "middle", objectName: name + " text" });
}
function arrow(slide, x1, y1, x2, y2, name) {
  slide.addShape(pres.shapes.LINE, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: HEX.accent4, width: 1.5, endArrowType: "triangle" }, objectName: name });
}
const notes = (slide, cues) => slide.addNotes(cues.map((c) => "- " + c).join("\n"));
const fmt = (n) => n.toLocaleString("en-US");
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" };

const M = N.methods;
const T = (k) => M[k].trucks;

// ---------- 1. title ----------
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Opening" });
s.addText("2nd LogisticSolver 2026  |  Smart Logistics Problem-Solving Competition", { placeholder: "kicker" });
s.addText("AI-Based Automatic Dispatch Clustering for Large-Volume Bulky Delivery", { placeholder: "title" });
s.background = { path: path.join(IMG, "slide_bg.png") };
s.addText("A graph neural network that shortlists and an exact optimizer that decides, tested on 97 real dispatch jobs and on a public benchmark", { placeholder: "body" });
s.addText([
  { text: "Team ANALOG", options: { bold: true, fontSize: 18, breakLine: true } },
  { text: "Ryry Rizky Asri (team lead), Dept. of Information and Communication Engineering", options: { breakLine: true } },
  { text: "최영은", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: " and ", options: {} },
  { text: "최정혜", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: ", Dept. of Electronic Engineering", options: { breakLine: true } },
  { text: "Changwon National University, November 2026", options: { color: C.accent5 } },
], { placeholder: "team" });
notes(s, ["Team ANALOG, Changwon National University", "Bulky delivery: fewer trucks with AI plus an exact optimizer", "Version 1 results on 97 real dispatch jobs"]);

// ---------- 2. results at a glance ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Opening" });
s.addText("23 % fewer trucks on 97 real jobs", { placeholder: "title" });
const glance = [
  [`${N.pct.real.trucks} %`.replace("-", "−"), `trucks: ${fmt(T("gnn_opt"))} instead of ${fmt(T("real"))} in the real dispatch`],
  [`${N.pct.real.km} %`.replace("-", "−"), `total road km: ${fmt(M.gnn_opt.km)} instead of ${fmt(M.real.km)}`],
  ["0.06 %", "average gap to the proven optimum on a public benchmark"],
  [`${N.gnn.s[1]} s`, "median planning time per job on one PC"],
];
glance.forEach(([big, label], k) => {
  const x = 0.6 + k * 3.1;
  card(s, x, 1.75, 2.85, 2.35, `Result card ${k + 1}`);
  stat(s, x + 0.3, 1.95, 2.3, big, label, `Result ${k + 1}`);
});
card(s, 0.6, 4.75, 12.1, 1.75, "Context card", C.accent5);
text(s, [
  { text: "Same jobs, same roads, same company rules. ", options: { bold: true, color: C.text2 } },
  { text: "Every truck of every plan meets every rule (0 violations). Data: 6,395 stops, 7 April to 7 August 2026. Accuracy is checked on public benchmark instances with proven optimal answers." },
], { x: 0.9, y: 5.0, w: 11.5, h: 1.3, fontSize: 17, valign: "middle", objectName: "Context text" });
notes(s, ["Main message first: −23 % trucks, −21 % total road km", "Accuracy: 0.06 % from proven optima on a public benchmark", "Fast: about 7 s per job", "All company rules met"]);

// ---------- 3. problem ----------
pres.addSection({ title: "Problem" });
s = pres.addSlide({ masterName: "Content", sectionTitle: "Problem" });
s.addText("Bulky deliveries are grouped by hand", { placeholder: "title" });
const prob = [
  ["One depot, the whole country", "A home-appliance maker in the Changwon area ships air coolers, large fans and similar goods with trucks hired per trip."],
  ["Grouping by rules of thumb", "For every dispatch job a person groups the addresses into trucks. It takes time, depends on the person and is hard to check."],
  ["Volume decides almost everything", `A typical job has ${N.data.per_job_med} addresses (${N.data.per_job_min} to ${N.data.per_job_max}), about ${N.data.vol_med} m³ each: five of them already fill a 1-ton truck.`],
];
prob.forEach(([h, b], k) => {
  const y = 1.65 + k * 1.7;
  dot(s, 0.6, y + 0.05, k + 1, `Problem ${k + 1} marker`);
  text(s, h, { x: 1.35, y, w: 6.9, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: `Problem ${k + 1} heading` });
  text(s, b, { x: 1.35, y: y + 0.5, w: 6.9, h: 1.05, fontSize: 16, objectName: `Problem ${k + 1} text` });
});
const mp = pic(s, "map", 8.7, 1.45, 4.0, 5.1, "Map of South Korea with one dot per delivery stop and the depot in Changwon");
text(s, "6,395 stops, one dot each; every truck leaves the depot in Changwon", { x: 8.55, y: mp.y + mp.h + 0.05, w: 4.3, h: 0.45, fontSize: 11, color: C.accent4, align: "center", objectName: "Map caption" });
notes(s, ["Hired trucks: question is how few, not how many", "Today: by hand, rules of thumb", "Typical job 63 addresses; volume rule dominates"]);

// ---------- 4. rules and why it is hard ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Problem" });
s.addText("Four rules, millions of choices", { placeholder: "title" });
pic(s, "rules", 0.6, 1.5, 12.1, 2.2, "Up to 5 addresses per truck, load at most 60 percent of the box, every stop within 50 km of the centre");
text(s, [
  { text: "Rule 4: ", options: { bold: true, color: C.text2 } },
  { text: "at most ten 1.4-ton trucks per job; larger trucks take one address only." },
], { x: 0.6, y: 3.85, w: 12.1, h: 0.4, fontSize: 16, objectName: "Rule 4" });
card(s, 0.6, 4.5, 5.9, 2.15, "Objective card");
text(s, "Objective", { x: 0.9, y: 4.7, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Objective heading" });
text(s, "First, the fewest trucks. Second, among those plans, the fewest road kilometres. Every stop is served exactly once.", { x: 0.9, y: 5.2, w: 5.3, h: 1.3, fontSize: 16, objectName: "Objective text" });
card(s, 6.8, 4.5, 5.9, 2.15, "Hardness card");
text(s, "7.7 million", { x: 7.1, y: 4.6, w: 5.3, h: 0.8, fontSize: 44, bold: true, color: C.accent1, valign: "bottom", objectName: "Hardness number" });
text(s, "possible groups of up to 5 stops in a 63-stop job. Choosing groups that cover every stop once is set partitioning, an NP-hard problem.", { x: 7.1, y: 5.45, w: 5.3, h: 1.1, fontSize: 15, color: C.accent4, objectName: "Hardness text" });
notes(s, ["Rules from the company's constraint list", "Goal: fewest trucks, then fewest km", "7.7 million groups: too many for hand or greedy rules"]);

// ---------- 5. data and privacy ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Problem" });
s.addText("Real data that stays in the company", { placeholder: "title" });
[[String(N.data.jobs), "real dispatch jobs"], [fmt(N.data.stops), "delivery stops"], [String(N.data.days), "operating days, April to August 2026"]].forEach(([big, label], k) => {
  stat(s, 0.6, 1.55 + k * 1.75, 4.2, big, label, `Data ${k + 1}`, C.text2);
});
const priv = [
  ["Company records, shared with consent", "Job, date, coordinates, order volume and the real truck groups, plus the truck list and the dispatch rules."],
  ["Our own map server", "Road km and driving time from OpenStreetMap on a private OSRM server: no address is sent to an online service."],
  ["Personal data never used", "Names and phone numbers stay out of the planner. Every example shown here uses synthetic data."],
];
priv.forEach(([h, b], k) => {
  const y = 1.6 + k * 1.75;
  card(s, 5.3, y, 7.4, 1.5, `Data card ${k + 1}`);
  dot(s, 5.55, y + 0.25, k + 1, `Data card ${k + 1} marker`, C.accent1);
  text(s, h, { x: 6.3, y: y + 0.2, w: 6.2, h: 0.42, fontSize: 18, bold: true, color: C.text2, objectName: `Data card ${k + 1} heading` });
  text(s, b, { x: 6.3, y: y + 0.62, w: 6.2, h: 0.8, fontSize: 15, objectName: `Data card ${k + 1} text` });
});
notes(s, ["97 jobs, 6,395 stops, 84 days", "Private map server: no address leaves", "Synthetic data in every example"]);

// ---------- 6. approach ----------
pres.addSection({ title: "Method" });
s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
s.addText("AI narrows the search, the optimizer decides", { placeholder: "title" });
const steps = [
  ["Road km", "Distances and times on real roads, private server", null],
  ["GNN short list", "8 likely truck partners per stop", "ai"],
  ["Candidate loads", "Every group of 1 to 5 that obeys the rules", null],
  ["Exact selection", "Fewest trucks, then fewest km", "opt"],
  ["Check", "Every truck against every rule", null],
];
steps.forEach(([h, b, kind], k) => {
  const x = 0.6 + k * 2.47, w = 2.2;
  const fill = kind === "ai" ? C.accent1 : kind === "opt" ? C.text2 : C.background2;
  const ink = kind ? C.background1 : C.text1;
  card(s, x, 1.65, w, 2.3, `Step ${k + 1} box`, fill);
  dot(s, x + 0.2, 1.85, k + 1, `Step ${k + 1} marker`, kind ? C.background1 : C.text2);
  if (kind) s.addText(String(k + 1), { isTextBox: true, x: x + 0.2, y: 1.85, w: 0.5, h: 0.5, margin: 0, fontSize: 15, bold: true, color: fill, align: "center", valign: "middle", objectName: `Step ${k + 1} number dark` });
  text(s, h, { x: x + 0.2, y: 2.5, w: w - 0.35, h: 0.45, fontSize: 18, bold: true, color: kind ? C.background1 : C.text2, objectName: `Step ${k + 1} heading` });
  text(s, b, { x: x + 0.2, y: 2.98, w: w - 0.35, h: 0.9, fontSize: 14, color: ink, objectName: `Step ${k + 1} text` });
  if (k < 4) arrow(s, x + w + 0.03, 2.8, x + 2.44, 2.8, `Arrow ${k + 1}`);
});
card(s, 0.6, 4.4, 5.9, 2.2, "AI role card", C.accent5);
text(s, "AI for speed", { x: 0.9, y: 4.6, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.accent1, objectName: "AI role heading" });
text(s, "The GNN cuts the candidate loads about 7 times and the solve time about 10 times. It only ranks; it never decides.", { x: 0.9, y: 5.1, w: 5.3, h: 1.3, fontSize: 16, objectName: "AI role text" });
card(s, 6.8, 4.4, 5.9, 2.2, "Optimizer role card", C.accent5);
text(s, "Optimizer for quality", { x: 7.1, y: 4.6, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Optimizer role heading" });
text(s, "A mixed-integer program weighs all loads at once and guarantees every rule; on a public benchmark it matches the proven optimum on 4 of 5 instances.", { x: 7.1, y: 5.1, w: 5.3, h: 1.3, fontSize: 16, objectName: "Optimizer role text" });
notes(s, ["Five steps per dispatch job", "Blue = AI (speed), navy = optimizer (quality)", "Safety net: a simple greedy plan, so there is always a valid answer"]);

// ---------- 7. GNN ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
s.addText("GNN: 8 likely partners per stop", { placeholder: "title" });
pic(s, "gnn", 0.6, 1.45, 12.1, 2.6, "Job graph, features, 4 rounds of message passing, pair score, short list");
const gnnCards = [
  ["The graph", "Stops are nodes; each is linked to its 12 nearest stops. 8 stop features, 4 link features."],
  ["The network", `4 rounds of message passing, ${fmt(N.gnn.params)} parameters, trained on the optimizer's own plans.`],
  ["The result", `Candidate loads per job: ${fmt(N.gnn.cols[0])} → ${fmt(N.gnn.cols[1])}. Ranking quality AUC ${N.gnn.auc.toFixed(2)} on unseen jobs.`],
];
gnnCards.forEach(([h, b], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 4.35, 3.85, 2.3, `GNN card ${k + 1}`);
  text(s, h, { x: x + 0.3, y: 4.55, w: 3.3, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: `GNN card ${k + 1} heading` });
  text(s, b, { x: x + 0.3, y: 5.05, w: 3.3, h: 1.5, fontSize: 15, objectName: `GNN card ${k + 1} text` });
});
notes(s, ["GNN scores: will two stops share a truck?", "Keeps top 8 partners: 7x fewer candidates", "Trained on optimizer plans; evaluated out of fold"]);

// ---------- 8. exact selection and rule check ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
s.addText("Exact selection, then a rule check", { placeholder: "title" });
const sel = [
  ["Stage A", "Choose loads so that every stop is served exactly once, with at most ten 1.4-ton trucks: the fewest trucks."],
  ["Stage B", "Among plans with that many trucks, the fewest road km. Each load's km is its best stop order, so grouping and routing are decided together."],
  ["Check", "Every truck is checked against every rule before the plan is accepted; a failure stops the run."],
];
sel.forEach(([h, b], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 1.55, 3.85, 2.45, `Selection ${k + 1} card`);
  dot(s, x + 0.25, 1.75, ["A", "B", "C"][k], `Selection ${k + 1} marker`);
  text(s, h, { x: x + 0.9, y: 1.78, w: 2.75, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: `Selection ${k + 1} heading` });
  text(s, b, { x: x + 0.25, y: 2.4, w: 3.4, h: 1.5, fontSize: 15, objectName: `Selection ${k + 1} text` });
});
card(s, 0.6, 4.3, 7.95, 2.3, "Why exact card", C.accent5);
text(s, "Why exact, not greedy", { x: 0.9, y: 4.5, w: 7.35, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Why exact heading" });
text(s, "A greedy rule fills one truck at a time and cannot undo a choice, so the last stops end up in half-empty trucks. The optimizer weighs every candidate load at once, and its constraints guarantee every rule by construction.", { x: 0.9, y: 5.0, w: 7.35, h: 1.5, fontSize: 16, objectName: "Why exact text" });
card(s, 8.85, 4.3, 3.85, 2.3, "Time limit card");
stat(s, 9.15, 4.4, 3.3, "60 s", "per stage at most; a simple greedy plan is the safety net", "Time limit", C.text2);
notes(s, ["Stage A trucks, stage B km: grouping and routing together", "Rule check on every truck", "Why exact: greedy cannot undo a choice"]);

// ---------- 9. worked example ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Method" });
s.addText("A worked example: 26 stops, 6 trucks", { placeholder: "title" });
pic(s, "example", 0.6, 1.45, 12.1, 3.75, "A 26-stop synthetic job: the stops, the short list of partners, and the optimal plan with 6 trucks");
const ex = N.example;
const exCards = [
  [fmt(ex.candidates), "candidate loads from each stop's 8 nearest partners"],
  [`${ex.trucks} trucks, ${fmt(ex.km)} km`, "the optimizer's plan, every rule met"],
  ["6 is the minimum", `${ex.volume} m³ needs at least 6 trucks of 4.73 m³`],
];
exCards.forEach(([big, label], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 5.3, 3.85, 1.35, `Example card ${k + 1}`);
  text(s, big, { x: x + 0.3, y: 5.38, w: 3.3, h: 0.55, fontSize: 24, bold: true, color: k === 1 ? C.accent1 : C.text2, valign: "bottom", objectName: `Example card ${k + 1} number` });
  text(s, label, { x: x + 0.3, y: 5.95, w: 3.3, h: 0.6, fontSize: 14, color: C.accent4, objectName: `Example card ${k + 1} label` });
});
notes(s, ["Synthetic data, real code", "Short list, then exact choice", "6 trucks: the fewest possible by volume"]);

// ---------- 10. trucks and road km by method ----------
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
s.addText(`${fmt(T("real") - T("gnn_opt"))} fewer trucks, 21 % fewer road km`, { placeholder: "title" });
const rows = [
  ["k-means", "kmeans", HEX.accent3], ["Real dispatch", "real", HEX.accent2], ["Agglomerative", "agg", HEX.accent3],
  ["Optimizer, 15 nearest", "opt", "9DBBEF"], ["GNN + optimizer (ours)", "gnn_opt", HEX.accent1],
];
const methodChart = (key, title, max, fmtCode, x, name) => s.addChart(pres.charts.BAR, [{ name: title, labels: rows.map((r) => r[0]), values: rows.map((r) => M[r[1]][key]) }], Object.assign({
  x, y: 1.5, w: 6.0, h: 3.9, barDir: "bar", catAxisOrientation: "maxMin", chartColors: rows.map((r) => r[2]), barGapWidthPct: 45,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: fmtCode, dataLabelFontSize: 13, dataLabelColor: HEX.dk1,
  catAxisLabelFontSize: 13, catAxisLabelColor: HEX.dk1, catAxisLineShow: false, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: max,
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  showTitle: true, title, titleFontSize: 16, titleColor: HEX.dk2, objectName: name,
}, chartText));
methodChart("trucks", "Trucks for all 97 jobs", 3300, "#,##0", 0.6, "Trucks by method chart");
methodChart("km", "Total road km for all 97 jobs", 860000, "#,##0", 6.7, "Road km by method chart");
[["Existing practice", HEX.accent2], ["Classic clustering", HEX.accent3], ["This work", HEX.accent1]].forEach(([lab, col], k) => {
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + k * 2.4, y: 5.72, w: 0.22, h: 0.22, fill: { color: col }, line: { type: "none" }, objectName: `Legend ${lab} swatch` });
  text(s, lab, { x: 0.95 + k * 2.4, y: 5.66, w: 2.0, h: 0.34, fontSize: 14, objectName: `Legend ${lab}` });
});
card(s, 7.95, 5.6, 4.75, 1.05, "Per job card");
text(s, [{ text: `${N.perjob.fewer} of 97 jobs `, options: { bold: true, color: C.accent1 } }, { text: "need fewer trucks than the real dispatch" }], { x: 8.2, y: 5.7, w: 4.3, h: 0.85, fontSize: 16, valign: "middle", objectName: "Per job text" });
notes(s, ["All 97 jobs, same rules and roads", "Optimizer rows beat every other method on trucks", "Total road km falls with the trucks: −21 %", "Real dispatch also handles things not in our data"]);

// ---------- 11. accuracy ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
s.addText("Accurate on a public benchmark", { placeholder: "title" });
const hdr = (t_) => ({ text: t_, options: { bold: true, color: C.text2, fill: { color: C.background2 } } });
const bt = [["Instance", "Customers", "Proven optimum", "Our distance", "Gap"].map(hdr)].concat(
  N.bench.map((r) => [r.name, String(r.customers), fmt(r.optimum), fmt(r.cost), `${r.gap.toFixed(1)} %`]));
s.addTable(bt, { x: 0.6, y: 1.55, w: 7.4, colW: [1.7, 1.3, 1.6, 1.6, 1.2], fontSize: 15, color: C.text1, border: { type: "solid", pt: 0.5, color: HEX.accent5 }, rowH: 0.48, objectName: "Benchmark table" });
text(s, "CVRPLIB set P (Augerat et al., 1995): the five instances whose proven optimal routes visit at most 5 customers, like the 5-address rule. Same code, 15 nearest partners.", { x: 0.6, y: 4.65, w: 7.4, h: 0.85, fontSize: 12, color: C.accent4, objectName: "Benchmark note" });
stat(s, 8.5, 1.55, 4.2, "4 of 5", "instances solved to the proven optimum", "Benchmark optimal", C.accent1);
stat(s, 8.5, 3.3, 4.2, "0.06 %", "average gap to the proven optimum", "Benchmark gap", C.text2);
card(s, 0.6, 5.6, 12.1, 1.05, "GNN accuracy card", C.accent5);
text(s, [{ text: "The GNN on unseen jobs: AUC 0.74. ", options: { bold: true, color: C.text2 } }, { text: "Its accuracy is 81.8 %, but the default accuracy (always \"different truck\") is already 81.3 %, so we judge it by its ranking." }], { x: 0.9, y: 5.7, w: 11.5, h: 0.85, fontSize: 15, valign: "middle", objectName: "GNN accuracy text" });
notes(s, ["Accuracy = gap to proven optimum on a public benchmark", "4 of 5 optimal, 0.06 % on average, anyone can rerun it", "GNN: judge by AUC, not by default accuracy"]);

// ---------- 12. speed ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Results" });
s.addText("10 times faster with the GNN", { placeholder: "title" });
const speedOpts = (title, fmtCode, max, name) => Object.assign({
  barDir: "bar", catAxisOrientation: "maxMin", chartColors: [HEX.accent3, HEX.accent1], barGapWidthPct: 45,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: fmtCode, dataLabelFontSize: 14, dataLabelColor: HEX.dk1,
  catAxisLabelFontSize: 14, catAxisLabelColor: HEX.dk1, catAxisLineShow: false, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: max,
  valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  showTitle: true, title, titleFontSize: 16, titleColor: HEX.dk2, objectName: name,
}, chartText);
const lists = ["15 nearest stops", "GNN short list"];
s.addChart(pres.charts.BAR, [{ name: "Loads", labels: lists, values: N.gnn.cols }], Object.assign({ x: 0.6, y: 1.55, w: 5.9, h: 2.9 }, speedOpts("Candidate loads per job (median)", "#,##0", 23000, "Candidate loads chart")));
s.addChart(pres.charts.BAR, [{ name: "Seconds", labels: lists, values: N.gnn.s }], Object.assign({ x: 6.8, y: 1.55, w: 5.9, h: 2.9 }, speedOpts("Solve time per job, seconds (median)", '0.0" s"', 80, "Solve time chart")));
const sp = [
  [`${N.gnn.limit[0]} → ${N.gnn.limit[1]}`, "jobs that hit the 60-second limit"],
  [`${fmt(T("gnn_opt"))} vs ${fmt(T("opt"))}`, "trucks: within 0.7 % of the slower list"],
  [`${N.timesize.gnn_small_med} s`, `median on jobs under 50 stops (${N.timesize.opt_small_med} s without the GNN)`],
];
sp.forEach(([big, label], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 4.75, 3.85, 1.9, `Speed card ${k + 1}`);
  text(s, big, { x: x + 0.3, y: 4.85, w: 3.3, h: 0.75, fontSize: 32, bold: true, color: C.text2, valign: "bottom", objectName: `Speed card ${k + 1} number` });
  text(s, label, { x: x + 0.3, y: 5.65, w: 3.3, h: 0.85, fontSize: 15, color: C.accent4, objectName: `Speed card ${k + 1} label` });
});
notes(s, ["7x fewer candidates, 10x faster solve", "Honest cost: 0.7 % more trucks than the slow list", "Daily use: a plan in seconds"]);

// ---------- 13. prototype and demo ----------
pres.addSection({ title: "Impact" });
s = pres.addSlide({ masterName: "Content", sectionTitle: "Impact" });
s.addText("A prototype for the daily routine", { placeholder: "title" });
const pp = pic(s, "jobmap", 0.6, 1.45, 7.9, 4.6, "One real dispatch job on the map: 70 stops grouped into 24 trucks, with 50 km circles");
text(s, "One real job as our plan groups it: 70 stops, 24 trucks, no labels. The prototype shows every job like this, behind a password.", { x: 0.6, y: pp.y + pp.h + 0.1, w: 7.9, h: 0.55, fontSize: 11, color: C.accent4, objectName: "Prototype caption" });
const flow = [["Order export", "today's spreadsheet"], ["Planner", "on the company PC, seconds per job"], ["Plan sheet and map", "stops in order, truck size, km, hours"], ["Dispatcher", "reviews, edits, books trucks"]];
flow.forEach(([h, b], k) => {
  const y = 1.5 + k * 1.02;
  card(s, 8.95, y, 3.75, 0.8, `Flow ${k + 1}`, k === 1 ? C.accent5 : C.background2);
  text(s, [{ text: h, options: { bold: true, color: C.text2, breakLine: true } }, { text: b, options: { fontSize: 13, color: C.accent4 } }], { x: 9.2, y: y + 0.08, w: 3.35, h: 0.66, fontSize: 16, valign: "middle", objectName: `Flow ${k + 1} text` });
  if (k < 3) arrow(s, 10.82, y + 0.8, 10.82, y + 1.02, `Flow arrow ${k + 1}`);
});
card(s, 8.95, 5.75, 3.75, 0.85, "Demo cue", C.accent1);
text(s, "Live demo: switch to the prototype", { x: 9.15, y: 5.75, w: 3.35, h: 0.85, fontSize: 17, bold: true, color: C.background1, align: "center", valign: "middle", objectName: "Demo cue text" });
notes(s, ["Fits the existing routine: export in, plan sheet out", "LIVE DEMO here: headline numbers, then one job on the map", "Password protected; no external services"]);

// ---------- 14. expected effects and pilot ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: "Impact" });
s.addText("Expected effects and pilot plan", { placeholder: "title" });
const y1 = N.save.real.year;
const eff = [[`~${fmt(Math.round(y1.trucks / 100) * 100)}`, "fewer trucks hired"], [`~${fmt(Math.round(y1.km / 1000) * 1000)}`, "fewer road km"], [`~${fmt(Math.round(y1.hours / 100) * 100)}`, "fewer driving hours"]];
text(s, "Per year, at most, against the real dispatch", { x: 0.6, y: 1.5, w: 5.2, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: "Effects heading" });
eff.forEach(([big, label], k) => stat(s, 0.6, 2.0 + k * 1.45, 5.2, big, label, `Effect ${k + 1}`));
text(s, "Upper bound: April to August is the main season; 4 months × 365 / 123 days", { x: 0.6, y: 6.4, w: 5.4, h: 0.4, fontSize: 11, color: C.accent4, objectName: "Effects note" });
const pilot = [
  ["Dec 2026", "Setup", "Install on a company PC, train on past jobs"],
  ["Jan 2027", "Shadow mode", "Runs beside the dispatcher; plans compared, not used"],
  ["Feb–Mar 2027", "Assisted mode", "The dispatcher starts from the plan and edits it"],
  ["Apr 2027", "Review", "Measured savings against these estimates"],
];
text(s, "Pilot", { x: 6.6, y: 1.5, w: 6.1, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: "Pilot heading" });
s.addShape(pres.shapes.LINE, { x: 6.85, y: 2.3, w: 0, h: 3.9, line: { color: HEX.accent5, width: 3 }, objectName: "Pilot line" });
pilot.forEach(([when, h, b], k) => {
  const y = 2.05 + k * 1.15;
  dot(s, 6.6, y, k, `Pilot ${k} marker`);
  text(s, [{ text: `${h}  `, options: { bold: true, color: C.text2 } }, { text: when, options: { color: C.accent1, bold: true } }], { x: 7.35, y: y - 0.02, w: 5.35, h: 0.42, fontSize: 17, objectName: `Pilot ${k} heading` });
  text(s, b, { x: 7.35, y: y + 0.4, w: 5.35, h: 0.6, fontSize: 15, objectName: `Pilot ${k} text` });
});
notes(s, ["Per year ~1,700 trucks, ~412,000 km, ~5,100 hours", "Basis: measured 4 months x 2.97; upper bound, main season", "Pilot Dec 2026 to Apr 2027, shadow mode first"]);

// ---------- 15. closing ----------
s = pres.addSlide({ masterName: "Closing dark", sectionTitle: "Impact" });
s.addText("Exact, fast and checked", { placeholder: "title" });
const news = [
  ["Grouping and routing together", "An exact optimizer under the company's full rule set."],
  ["AI that keeps the guarantee", "The GNN shortlists; the optimizer still checks every rule."],
  ["Accuracy anyone can check", "Proven optimum on 4 of 5 public benchmark instances, 0.06 % on average."],
  ["Ready for a pilot", "Seconds per job on one PC; customer data stays inside."],
];
news.forEach(([h, b], k) => {
  const x = 0.8 + (k % 2) * 6.0, y = 2.0 + Math.floor(k / 2) * 1.9;
  dot(s, x, y + 0.02, k + 1, `Takeaway ${k + 1} marker`, C.accent1);
  text(s, h, { x: x + 0.7, y, w: 5.0, h: 0.45, fontSize: 20, bold: true, color: C.background1, objectName: `Takeaway ${k + 1} heading` });
  text(s, b, { x: x + 0.7, y: y + 0.5, w: 5.0, h: 0.9, fontSize: 16, color: C.accent5, objectName: `Takeaway ${k + 1} text` });
});
text(s, "Thank you. Questions?", { x: 0.8, y: 6.0, w: 7, h: 0.6, fontSize: 26, bold: true, color: C.background1, objectName: "Thanks" });
text(s, "Team ANALOG, Changwon National University", { x: 7.3, y: 6.15, w: 5.2, h: 0.4, fontSize: 14, color: C.accent5, align: "right", objectName: "Team line" });
notes(s, ["Four takeaways: together, AI + guarantee, benchmark accuracy, pilot-ready", "Invite questions"]);

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
