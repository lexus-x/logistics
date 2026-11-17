// Competition slides (2nd LogisticSolver 2026, team ANALOG): Version 1 results only, 15 slides, road-sign colours.
//   node competition/make_deck.js       -> English deck
//   node competition/make_deck.js ko    -> Korean deck (same layout, Korean text, Malgun Gothic)
// Charts, diagrams and tables are native, so every word and number stays editable. Pictures remain only where they show
// real stop locations (national map, title background), the synthetic job's two plans, and the prototype's screen.
// Pictures: figs/slides/*.png (figs/ko/slides/ for the Korean deck), figs/slide_bg.png (figs/ko/ for Korean).
const fs = require("fs");
const path = require("path");
const os = require("os");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const KO = process.argv[2] === "ko";
const L = (en, ko) => (KO ? ko : en);
const LANG = KO ? { lang: "ko-KR" } : {};
const pc = (v) => (L(`${v}\u00a0%`, `${v}%`)).replace("-", "−"); // Korean writes no space before %; the English space never breaks

const FIGS = path.join(__dirname, "figs");
const OUT = path.join(os.homedir(), "reports/LogisticSolver_2026", L("ANALOG_LogisticSolver2026_Slides.pptx", "ANALOG_LogisticSolver2026_Slides_KO.pptx"));
const N = JSON.parse(fs.readFileSync(path.join(__dirname, "numbers.json"), "utf8"));
const W = JSON.parse(fs.readFileSync(path.join(__dirname, "webfigs/data.json"), "utf8")); // per-job savings and the 8-nearest row
const J = JSON.parse(fs.readFileSync(path.join(__dirname, "synthetic_job.json"), "utf8")); // synthetic example job
const ORTOOLS_TRUCKS = 2264; // sum over cluster/results/ryry_ortools.jsonl (report Table 8); that file is not in numbers.json
const TITLE = L("AI-Based Clustering and Automatic Dispatching for Bulky Product Delivery", "대형 제품 배송을 위한 AI 기반 클러스터링 및 자동 배차");

// Bahnschrift is Windows' DIN road-sign face: titles and big numbers. Body: Calibri, or Malgun Gothic for Korean.
const HEAD = "Bahnschrift";
const THEME = {
  name: "ANALOG road",
  headFontFace: HEAD,
  bodyFontFace: L("Calibri", "Malgun Gothic"),
  eaFont: L(undefined, "Malgun Gothic"), // Korean letters in titles and body get Malgun Gothic from the theme (apply_theme.js)
  colors: {
    dk1: "1E2622", lt1: "FFFFFF", dk2: "0E5A3F", lt2: "EDF3EF",
    accent1: "1A7A52", accent2: "F4B400", accent3: "B9BFC4", accent4: "6B747C", accent5: "3A4148", accent6: "CFE5D9",
    hlink: "1A7A52", folHlink: "0E5A3F",
  },
};
const HEX = THEME.colors;
const SOFT = "C9DDD1"; // secondary text on the green slides
const HAIR = "DDE3E0"; // hairlines and chart grid

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = L("Team ANALOG", "팀 ANALOG");
pres.title = TITLE;
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
const FOOT = L("Team ANALOG, 2nd LogisticSolver 2026", "팀 ANALOG, 제2회 LogisticSolver 2026");
pres.defineSlideMaster({
  title: "Title dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.8, y: 0.6, w: 6.6, h: 0.45, fontSize: 14, color: SOFT, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 1.3, w: 6.6, h: 2.9, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.4, w: 6.2, h: 0.95, fontSize: 16, color: SOFT, valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "team", type: "body", x: 0.8, y: 5.55, w: 6.6, h: 1.5, fontSize: 13, color: C.background1, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Content",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.42, w: 12.1, h: 0.85, fontSize: 32, bold: false, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: Object.assign({ x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 }, LANG) } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: HEX.accent4, align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "Statement dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 0.5, w: 11.7, h: 0.9, fontSize: 32, bold: false, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: SOFT, align: "right", margin: 0 },
});

// ---------- helpers ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
// picture file: the Korean deck takes the Korean-labelled copy when it exists
function img(name) {
  const ko = path.join(FIGS, "ko/slides", name + ".png");
  if (KO && fs.existsSync(ko)) return ko;
  if (KO) console.warn(`note: ${ko} not found, using the English picture`);
  return path.join(FIGS, "slides", name + ".png");
}
// picture fitted inside the box (x, y, w, h), top-left aligned, aspect kept
function pic(slide, file, x, y, w, h, alt, name) {
  const s = pngSize(file);
  let pw = w, ph = (w * s.h) / s.w;
  if (ph > h) { ph = h; pw = (h * s.w) / s.h; }
  slide.addImage({ path: file, x, y, w: pw, h: ph, altText: alt, objectName: "Picture " + name });
  return { x, y, w: pw, h: ph };
}
function text(slide, t, o) {
  slide.addText(t, Object.assign({ isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top" }, LANG, o));
}
const title = (slide, t) => slide.addText(t, Object.assign({ placeholder: "title" }, LANG));
// big number in the road-sign face with a label under it
function stat(slide, x, y, w, big, label, name, o = {}) {
  const size = o.size || 44, hb = size / 60 + 0.15;
  text(slide, big, { x, y, w, h: hb, fontSize: size, fontFace: HEAD, color: o.color || C.text2, valign: "bottom", objectName: name + " number" });
  text(slide, label, { x, y: y + hb + 0.08, w, h: o.lh || 0.8, fontSize: o.ls || 15, color: o.lcolor || C.text1, objectName: name + " label" });
}
function seg(slide, x1, y1, x2, y2, line, name) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line, objectName: name });
}
function disc(slide, cx, cy, d, fill, name, line) {
  slide.addShape(pres.shapes.OVAL, { x: cx - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: fill }, line: line || { type: "none" }, objectName: name });
}
const hair = (slide, x, y, w, name) => seg(slide, x, y, x + w, y, { color: HAIR, width: 0.75 }, name);
// the deck's motif: a route line with stops, only for real sequences. kind: "ai" yellow, "opt" green, else open.
function stopDot(slide, cx, cy, kind, name, onDark) {
  const fill = kind === "ai" ? C.accent2 : kind === "opt" ? (onDark ? C.accent2 : C.text2) : (onDark ? C.text2 : C.background1);
  disc(slide, cx, cy, 0.42, fill, name, { color: onDark ? HEX.lt1 : HEX.accent5, width: 1.75 });
}
// icon (Tabler outline, figs/icons) as a square picture; colour: white | green | asphalt
const ICON = (name, colour) => path.join(FIGS, "icons", `${name}_${colour}.png`);
function icon(slide, name, colour, x, y, d, alt) {
  slide.addImage({ path: ICON(name, colour), x, y, w: d, h: d, altText: alt || name, objectName: `Icon ${name}` });
}
// a larger route stop that carries the icon of what happens there: open stops green line icon, AI yellow, optimizer green
function iconStop(slide, cx, cy, kind, name, label, d = 0.66) {
  const fill = kind === "ai" ? C.accent2 : kind === "opt" ? C.text2 : C.background1;
  disc(slide, cx, cy, d, fill, `${label} stop`, { color: kind === "opt" ? HEX.dk2 : HEX.accent5, width: 1.75 });
  icon(slide, name, kind === "ai" ? "asphalt" : kind === "opt" ? "white" : "green", cx - d * 0.3, cy - d * 0.3, d * 0.6, label);
}
const notes = (slide, cues) => slide.addNotes(cues.map((c) => "- " + c).join("\n"));
const fmt = (n) => Math.round(n).toLocaleString("en-US");
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" };
// horizontal bar chart, one series, one colour per bar, values printed at the bar end
function bars(slide, labels, values, colors, o) {
  slide.addChart(pres.charts.BAR, [{ name: o.name, labels, values }], Object.assign({
    x: o.x, y: o.y, w: o.w, h: o.h, barDir: "bar", barGapWidthPct: o.gap || 45, chartColors: colors, catAxisOrientation: "maxMin",
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: o.ink || HEX.dk1, dataLabelFontSize: o.fs || 14, dataLabelFormatCode: o.format || "#,##0",
    catAxisLabelColor: o.ink || HEX.dk1, catAxisLabelFontSize: o.fs || 14, catAxisLabelFrequency: 1, catAxisLineShow: false, valAxisHidden: true, valAxisMinVal: 0,
    valAxisMaxVal: o.max, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: !!o.title, title: o.title, titleColor: o.ink || HEX.dk1, titleFontSize: 14, objectName: o.name,
  }, chartText, LANG));
}

const M = N.methods;
const T = (k) => M[k].trucks;
const SEC = { open: L("Opening", "도입"), prob: L("Problem", "문제"), meth: L("Method", "방법"), res: L("Results", "결과"), imp: L("Impact", "효과") };
const gap = N.bench.reduce((a, r) => a + (100 * (r.cost - r.optimum)) / r.optimum, 0) / N.bench.length;
const nOpt = N.bench.filter((r) => r.cost === r.optimum).length;

// ---------- 1. title ----------
pres.addSection({ title: SEC.open });
let s = pres.addSlide({ masterName: "Title dark", sectionTitle: SEC.open });
s.background = { path: path.join(FIGS, KO ? "ko/slide_bg.png" : "slide_bg.png") };
s.addText(L("2nd LogisticSolver 2026, Smart Logistics Problem-Solving Competition", "제2회 LogisticSolver 2026 스마트 물류 문제 해결 경진대회"), Object.assign({ placeholder: "kicker" }, LANG));
s.addText(TITLE, Object.assign({ placeholder: "title" }, LANG));
s.addText(L("A graph neural network shortlists, an exact optimizer decides. Tested on 97 real dispatch jobs and a public benchmark.",
  "그래프 신경망(GNN)이 후보를 추리고 정확 최적화기가 결정. 실제 배차 작업 97건과 공개 벤치마크로 검증."), Object.assign({ placeholder: "body" }, LANG));
s.addText(KO ? [
  { text: "팀 ANALOG", options: { bold: true, fontSize: 17, breakLine: true } },
  { text: "Ryry Rizky Asri (팀장), 정보통신공학과", options: { breakLine: true } },
  { text: "최영은, 전자공학과", options: { breakLine: true } },
  { text: "최정혜, 전자공학과", options: { breakLine: true } },
  { text: "국립창원대학교, 2026년 11월", options: { color: SOFT } },
] : [
  { text: "Team ANALOG", options: { bold: true, fontSize: 17, breakLine: true } },
  { text: "Ryry Rizky Asri (team lead), Dept. of Information and Communication Engineering", options: { breakLine: true } },
  { text: "최영은", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: " and ", options: {} },
  { text: "최정혜", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: ", Dept. of Electronic Engineering", options: { breakLine: true } },
  { text: "Changwon National University, November 2026", options: { color: SOFT } },
], Object.assign({ placeholder: "team" }, LANG));
notes(s, KO
  ? ["팀 ANALOG, 국립창원대학교", "오른쪽 지도: 실제 배차 작업 하나, 노란 선 하나가 트럭 한 대", "대형 제품 배송: AI와 정확 최적화기로 트럭 감소"]
  : ["Team ANALOG, Changwon National University", "The map: one real dispatch job, each yellow line one truck", "Bulky delivery: fewer trucks with AI plus an exact optimizer"]);

// ---------- 2. problem ----------
pres.addSection({ title: SEC.prob });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Every dispatch job is grouped into trucks by hand", "배차 작업마다 사람이 직접 트럭을 묶음"));
const mp = pic(s, img("map"), 0.6, 1.35, 3.6, 4.95, L("Map of South Korea with one dot per delivery stop and the depot in Changwon", "배송지마다 점 하나를 찍은 대한민국 지도와 창원 물류센터"), "map");
text(s, L("6,395 stops, one dot each. Every truck leaves the depot in Changwon.", "배송지 6,395곳(점 하나가 한 곳). 모든 트럭은 창원 물류센터에서 출발."),
  { x: 0.6, y: mp.y + mp.h + 0.08, w: 4.0, h: 0.45, fontSize: 11, color: C.accent4, objectName: "Map caption" });
[
  [String(N.data.per_job_med), L(`addresses in a typical job (${N.data.per_job_min} to ${N.data.per_job_max}), all served from one depot by trucks hired per trip`,
    `일반적인 작업의 주소 수(${N.data.per_job_min}~${N.data.per_job_max}곳). 모두 물류센터 한 곳에서 운행마다 빌리는 트럭으로 배송`)],
  [`${N.data.vol_med} m³`, L("per address, a fifth of a 1-ton truck: volume decides almost every grouping", "주소 한 곳당 부피, 1톤 트럭의 5분의 1: 묶음은 거의 부피로 결정됨")],
  [L("by hand", "수작업"), L("every day, by rules of thumb. Nobody can tell how far a plan is from the best one.", "매일 경험칙으로 처리. 계획이 최선에서 얼마나 먼지 아무도 알 수 없음.")],
].forEach(([big, label], k) => {
  const y = 1.6 + k * 1.75;
  text(s, big, { x: 4.9, y, w: 2.9, h: 0.9, fontSize: 44, fontFace: HEAD, color: C.text2, valign: "bottom", objectName: `Fact ${k + 1} number` });
  text(s, label, { x: 8.0, y: y + 0.12, w: 4.7, h: 1.2, fontSize: 17, objectName: `Fact ${k + 1} text` });
  if (k < 2) hair(s, 4.9, y + 1.45, 7.8, `Fact ${k + 1} rule`);
});
notes(s, KO
  ? ["용차: 몇 대가 필요한가가 아니라 얼마나 줄일 수 있는가", "배송지 하나가 1톤 트럭의 5분의 1: 부피 규칙이 지배적", "현재: 사람이 경험칙으로, 최선과의 차이는 알 수 없음"]
  : ["Hired trucks: the question is how few, not how many", "One address is a fifth of a 1-ton truck: the volume rule dominates", "Today: by hand, rules of thumb, no way to know the distance to the best plan"]);

// ---------- 3. rules ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Four rules turn one job into millions of choices", "규칙 4가지가 작업 하나를 수백만 가지 선택지로 만듦"));
const rx = (k) => 0.6 + k * 3.1;
for (let i = 0; i < 5; i++) icon(s, "map-pin", "green", rx(0) + i * 0.52, 1.95, 0.5, L(`Address ${i + 1}`, `주소 ${i + 1}`));
// a box truck seen from the side: boxes on the floor up to 60 % of the box, no stacking
const tb = { x: rx(1), y: 1.65, w: 2.05, h: 0.95 };
s.addShape(pres.shapes.RECTANGLE, { x: tb.x, y: tb.y, w: tb.w, h: tb.h, fill: { color: C.background1 }, line: { color: HEX.dk2, width: 1.75 }, objectName: "Rule 2 truck box" });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: tb.x + tb.w + 0.06, y: tb.y + 0.3, w: 0.55, h: tb.h - 0.3, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: HEX.accent5, width: 1.5 }, objectName: "Rule 2 truck cab" });
[0.74, 0.8, 0.7].forEach((hh, i) => s.addShape(pres.shapes.RECTANGLE, { x: tb.x + 0.05 + i * 0.4, y: tb.y + tb.h - 0.04 - hh, w: 0.36, h: hh, fill: { color: C.accent6 }, line: { color: HEX.accent1, width: 1 }, objectName: `Rule 2 parcel ${i + 1}` }));
seg(s, tb.x + tb.w * 0.6, tb.y - 0.08, tb.x + tb.w * 0.6, tb.y + tb.h, { color: HEX.dk2, width: 1.5, dashType: "dash" }, "Rule 2 limit");
text(s, pc(60), { x: tb.x + tb.w * 0.6 + 0.06, y: tb.y + 0.08, w: 0.75, h: 0.35, fontSize: 15, fontFace: HEAD, color: C.text2, objectName: "Rule 2 share" });
[tb.x + 0.38, tb.x + tb.w + 0.3].forEach((wx, i) => disc(s, wx, tb.y + tb.h + 0.06, 0.26, C.accent5, `Rule 2 wheel ${i + 1}`));
const rc = { x: rx(2) + 0.75, y: 2.25, r: 0.6 };
s.addShape(pres.shapes.OVAL, { x: rc.x - rc.r, y: rc.y - rc.r, w: 2 * rc.r, h: 2 * rc.r, fill: { color: C.background2 }, line: { color: HEX.dk2, width: 1.5, dashType: "dash" }, objectName: "Rule 3 circle" });
[[-1.2, 0.6], [0.9, 1.1], [0.3, -1.2], [-0.6, -0.5], [1.5, -0.2]].forEach(([dx, dy], i) => disc(s, rc.x + dx * 0.26, rc.y - dy * 0.26, 0.18, C.accent1, `Rule 3 stop ${i + 1}`));
seg(s, rc.x, rc.y, rc.x + rc.r * 0.8, rc.y + rc.r * 0.6, { color: HEX.accent5, width: 1 }, "Rule 3 radius");
text(s, "50 km", { x: rc.x + rc.r + 0.05, y: rc.y + 0.15, w: 0.9, h: 0.32, fontSize: 14, color: C.accent4, objectName: "Rule 3 radius label" });
for (let i = 0; i < 10; i++) icon(s, "truck", "asphalt", rx(3) + (i % 5) * 0.52, 1.65 + Math.floor(i / 5) * 0.55, 0.48, L(`1.4-ton truck ${i + 1}`, `1.4톤 트럭 ${i + 1}`));
[
  L("1 to 5 addresses per truck", "트럭당 주소 1~5곳"),
  L("load at most 60 % of the truck's box", "적재는 적재함 부피의 60% 이하"),
  L("every stop within 50 km of the truck's centre", "모든 배송지가 묶음 중심에서 50 km 이내"),
  L("at most ten 1.4-ton trucks per job; larger trucks take one address", "작업당 1.4톤 트럭 최대 10대, 그보다 큰 트럭은 주소 1곳만"),
].forEach((t_, k) => text(s, t_, { x: rx(k), y: 3.0, w: 2.85, h: 0.8, fontSize: 15, objectName: `Rule ${k + 1} label` }));
hair(s, 0.6, 4.1, 12.1, "Rules rule");
text(s, L("Objective", "목적"), { x: 0.6, y: 4.45, w: 5.6, h: 0.45, fontSize: 20, fontFace: HEAD, color: C.text2, objectName: "Objective heading" });
text(s, L("Fewest trucks first; among those plans, the fewest road kilometres. Every stop is served exactly once.",
  "첫째, 트럭 수 최소. 둘째, 그 계획들 가운데 도로 km 최소. 모든 배송지는 정확히 한 번 방문."), { x: 0.6, y: 5.0, w: 5.6, h: 1.2, fontSize: 17, objectName: "Objective text" });
stat(s, 6.9, 4.3, 5.8, L("7.7 million", "770만 개"), L("possible groups of up to 5 stops in a 63-stop job. Choosing groups that cover every stop once is set partitioning, an NP-hard problem.",
  "배송지 63곳 작업에서 가능한 5곳 이하 묶음의 수. 모든 배송지를 한 번씩 덮는 묶음 선택은 집합 분할 문제(NP-난해)."), "Hardness", { size: 48, lh: 1.2 });
notes(s, KO
  ? ["회사의 제약 조건 목록에 따른 규칙 4가지", "목표: 트럭 최소, 다음으로 km 최소", "묶음 770만 개: 수작업이나 탐욕 규칙으로는 감당 불가"]
  : ["Four rules from the company's constraint list", "Goal: fewest trucks, then fewest km", "7.7 million groups: too many for hand or greedy rules"]);

// ---------- 4. data and privacy ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Real company data that stays in the company", "회사 밖으로 나가지 않는 실제 회사 데이터"));
const MON = KO ? ["", "", "", "", "4월", "5월", "6월", "7월", "8월"] : ["", "", "", "", "April", "May", "June", "July", "August"]; // index = month number
// column chart over the jobs in date order. The plot area is placed by hand, so the month names can sit under the
// first bar of each month as text boxes (category labels with blanks drift in some renderers).
function colChart(slide, dates, values, colors, o) {
  const P = { x: 0.05, y: 0.19, w: 0.935, h: 0.66 }; // plot below the chart title
  slide.addChart(pres.charts.BAR, [{ name: o.name, labels: dates.map(() => ""), values }], Object.assign({
    x: o.x, y: o.y, w: o.w, h: o.h, layout: P, barDir: "col", barGapWidthPct: 35, chartColors: colors, catAxisHidden: true,
    valAxisLabelColor: HEX.accent4, valAxisLabelFontSize: 12, valAxisLineShow: false, valGridLine: { color: HAIR, size: 0.75 }, catGridLine: { style: "none" },
    showLegend: false, showTitle: true, title: o.title, titleColor: HEX.dk1, titleFontSize: 14, objectName: o.name,
  }, chartText, LANG));
  const bw = (o.w * P.w) / dates.length;
  dates.forEach((d, i) => {
    if (i && d.slice(5, 7) === dates[i - 1].slice(5, 7)) return;
    const x = o.x + o.w * P.x + i * bw;
    seg(slide, x, o.y + o.h * (P.y + P.h), x, o.y + o.h * (P.y + P.h) + 0.12, { color: HEX.accent4, width: 0.75 }, `${o.name} tick ${d.slice(5, 7)}`);
    text(slide, MON[+d.slice(5, 7)], { x: x + 0.04, y: o.y + o.h * (P.y + P.h) + 0.02, w: 1.0, h: 0.3, fontSize: 12, color: C.accent4, objectName: `${o.name} month ${d.slice(5, 7)}` });
  });
}
colChart(s, N.jobsizes.map((j) => j.date), N.jobsizes.map((j) => j.n), N.jobsizes.map(() => HEX.accent5),
  { name: "Stops per job", x: 0.6, y: 1.35, w: 8.3, h: 2.75, title: L("Stops in each dispatch job, in date order", "배차 작업별 배송지 수, 날짜 순") });
[[String(N.data.jobs), L("real dispatch jobs", "실제 배차 작업")], [fmt(N.data.stops), L("delivery stops", "배송지")], [String(N.data.days), L("operating days in the main season", "성수기 운영일")]].forEach(([big, label], k) => {
  text(s, big, { x: 9.4, y: 1.4 + k * 0.92, w: 1.75, h: 0.7, fontSize: 36, fontFace: HEAD, color: C.text2, valign: "bottom", objectName: `Data ${k + 1} number` });
  text(s, label, { x: 11.2, y: 1.52 + k * 0.92, w: 1.5, h: 0.62, fontSize: 14, valign: "bottom", objectName: `Data ${k + 1} label` });
});
const DROPPED = 9; // stops whose coordinates came from a typo correction (report section 3)
const dx = (k) => 1.85 + k * 3.15, dy = 5.0;
seg(s, dx(0), dy, dx(3), dy, { color: HEX.accent5, width: 2.25 }, "Data route line");
[
  ["file-spreadsheet", null, L("Order export", "주문 내보내기"), L(`${fmt(N.data.stops + DROPPED)} stops; ${DROPPED} with corrected coordinates left out`, `배송지 ${fmt(N.data.stops + DROPPED)}곳, 좌표를 고친 ${DROPPED}곳 제외`)],
  ["server", null, L("Private map server", "비공개 지도 서버"), L("road km and times from OpenStreetMap; no address goes online", "OpenStreetMap 도로 km와 시간, 주소는 외부로 나가지 않음")],
  ["truck", null, L("Large orders", "대형 주문"), L(`${N.data.big} stops too big for a 1.4-ton truck get a truck of their own`, `1.4톤에 실을 수 없는 ${N.data.big}곳은 단독 트럭`)],
  ["cpu", "opt", L("Planner input", "계획기 입력"), L(`${fmt(N.data.stops - N.data.big)} stops; no names or phone numbers`, `배송지 ${fmt(N.data.stops - N.data.big)}곳, 이름과 전화번호 없음`)],
].forEach(([ic, kind, h, b], k) => {
  iconStop(s, dx(k), dy, kind, ic, `Data step ${k + 1}`);
  text(s, h, { x: dx(k) - 1.45, y: 4.15, w: 2.9, h: 0.42, fontSize: 18, fontFace: HEAD, color: C.text2, align: "center", valign: "bottom", objectName: `Data step ${k + 1} heading` });
  text(s, b, { x: dx(k) - 1.45, y: 5.45, w: 2.9, h: 0.95, fontSize: 14, align: "center", objectName: `Data step ${k + 1} text` });
});
notes(s, KO
  ? ["작업 97건, 배송지 6,395곳, 84일: 냉풍기와 선풍기 성수기", "작업 크기는 8~141곳으로 매일 다름", "회사 기록은 동의를 받아 공유, 비공개 지도 서버: 주소가 밖으로 나가지 않음", "보여 주는 예시는 모두 합성 데이터"]
  : ["97 jobs, 6,395 stops, 84 days: the main season for coolers and fans", "Job size changes every day, from 8 to 141 stops", "Company records shared with consent; private map server, no address leaves", "Every example shown is synthetic"]);

// ---------- 5. approach: the route line ----------
pres.addSection({ title: SEC.meth });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("AI narrows the search, the optimizer decides", "AI가 탐색 범위를 좁히고, 최적화기가 결정"));
// each stop shows what one median job looks like at that step
const steps = [
  ["road", L("Road km", "도로 km"), L("one request per job to the private map server", "작업당 한 번, 비공개 지도 서버에 요청"), null],
  ["affiliate", L("GNN short list", "GNN 후보 목록"), L("8 likely partners per stop", "배송지당 유력 파트너 8곳"), "ai"],
  ["packages", L("Candidate loads", "후보 묶음"), L(`${fmt(N.gnn.cols[1])} rule-safe groups per job (median)`, `작업당 규칙을 지키는 묶음 ${fmt(N.gnn.cols[1])}개(중앙값)`), null],
  ["target", L("Exact selection", "정확 선택"), L("fewest trucks, then fewest km", "트럭 최소, 다음으로 km 최소"), "opt"],
  ["list-check", L("Rule check", "규칙 검사"), L(`0 breaks in ${fmt(T("gnn_opt"))} trucks`, `트럭 ${fmt(T("gnn_opt"))}대 중 위반 0`), null],
];
const lx0 = 1.85, lx1 = 11.5, ly = 2.85, sx = (k) => lx0 + (k * (lx1 - lx0)) / 4;
seg(s, lx0, ly, lx1, ly, { color: HEX.accent5, width: 2.25 }, "Route line");
steps.forEach(([ic, h, b, kind], k) => {
  iconStop(s, sx(k), ly, kind, ic, `Step ${k + 1}`);
  text(s, h, { x: sx(k) - 1.15, y: 1.65, w: 2.3, h: 0.7, fontSize: 19, fontFace: HEAD, color: C.text2, align: "center", valign: "bottom", objectName: `Step ${k + 1} heading` });
  text(s, b, { x: sx(k) - 1.0, y: 3.35, w: 2.0, h: 1.0, fontSize: 15, align: "center", objectName: `Step ${k + 1} text` });
});
[
  ["ai", L("AI for speed", "속도는 AI가"), L("The GNN cuts the candidate loads 7 times and the solve time 10 times. It ranks partners; it never decides.",
    "GNN이 후보 묶음을 1/7, 풀이 시간을 1/10로 줄임. 파트너 순위만 매길 뿐 결정하지 않음.")],
  ["opt", L("Optimizer for quality", "품질은 최적화기가"), L(`A mixed-integer program weighs all loads at once and guarantees every rule. Proven optimum on ${nOpt} of 5 benchmark instances.`,
    `혼합정수계획 모형이 모든 묶음을 한꺼번에 비교하고 모든 규칙을 보장. 벤치마크 인스턴스 5개 중 ${nOpt}개에서 증명된 최적해.`)],
].forEach(([kind, h, b], c) => {
  const x = 0.6 + c * 6.3;
  stopDot(s, x + 0.21, 4.95, kind, `${kind} legend stop`);
  text(s, h, { x: x + 0.6, y: 4.73, w: 5.2, h: 0.45, fontSize: 20, fontFace: HEAD, color: C.text2, objectName: `${kind} role heading` });
  text(s, b, { x: x + 0.6, y: 5.3, w: 5.2, h: 1.3, fontSize: 16, objectName: `${kind} role text` });
});
notes(s, KO
  ? ["배차 작업마다 5단계", "노란색 = AI(속도), 초록색 = 최적화기(품질)", "안전망: 단순한 탐욕 계획이 있어 항상 유효한 답이 나옴"]
  : ["Five steps per dispatch job", "Yellow = AI (speed), green = optimizer (quality)", "Safety net: a simple greedy plan, so there is always a valid answer"]);

// ---------- 6. GNN ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("The GNN keeps each stop's 8 likely partners", "GNN은 배송지마다 유력 파트너 8곳만 남김"));
// the synthetic job with each stop's 4 nearest partners (4 for clarity, as in the report's Figure 5b)
const P = Object.fromEntries(J.stops.map((p) => [p.stop, p]));
const km2 = (a, b) => (a.x_km - b.x_km) ** 2 + (a.y_km - b.y_km) ** 2;
const near = J.stops.map((p) => J.stops.filter((q) => q !== p).sort((a, b) => km2(p, a) - km2(p, b)).slice(0, 4));
const gx = 0.6, gy = 1.5, gw = 5.6, gh = 4.9, sc = Math.min(gw / 172, gh / 152);
const X = (km) => gx + (gw - 172 * sc) / 2 + (km + 12) * sc, Y = (km) => gy + (gh - 152 * sc) / 2 + (140 - km) * sc;
const done = new Set();
J.stops.forEach((p, i) => near[i].forEach((q) => {
  const id = [p.stop, q.stop].sort().join("-");
  if (done.has(id)) return;
  done.add(id);
  seg(s, X(p.x_km), Y(p.y_km), X(q.x_km), Y(q.y_km), { color: HEX.accent1, width: 1.25, transparency: 45 }, `Partner link ${id}`);
}));
J.stops.forEach((p) => disc(s, X(p.x_km), Y(p.y_km), 0.03 * Math.sqrt(14 + 22 * p.volume_m3), C.accent1, `Stop ${p.stop}`, { color: "FFFFFF", width: 0.75 }));
s.addShape(pres.shapes.STAR_5_POINT, { x: X(J.depot[0]) - 0.16, y: Y(J.depot[1]) - 0.16, w: 0.32, h: 0.32, fill: { color: C.accent2 }, line: { color: HEX.dk1, width: 0.75 }, objectName: "Depot" });
text(s, L("Synthetic job, 26 stops, each linked to its 4 nearest stops for clarity; the GNN keeps 8 partners. Star: depot.", "합성 작업, 배송지 26곳: 알아보기 쉽게 최근접 4곳과 연결(GNN은 파트너 8곳 유지). 별: 물류센터."),
  { x: gx, y: gy + gh + 0.05, w: gw, h: 0.45, fontSize: 11, color: C.accent4, objectName: "GNN picture caption" });
const gsteps = [
  [L("Reads the job as a graph", "작업을 그래프로 읽음"), L("Each stop is linked to its 12 nearest stops: 8 stop features, 4 pair features.", "배송지마다 가장 가까운 12곳과 연결: 배송지 특징 8개, 쌍 특징 4개.")],
  [L("Passes messages four times", "메시지를 4번 전달"), L(`${fmt(N.gnn.params)} parameters, trained on the optimizer's own plans.`, `파라미터 ${fmt(N.gnn.params)}개, 최적화기 자체의 계획으로 학습.`)],
  [L("Ranks partners", "파트너 순위 결정"), L(`Keeps each stop's top 8. On jobs it never saw: AUC ${N.gnn.auc.toFixed(2)}.`, `배송지별 상위 8곳 유지. 처음 보는 작업에서 AUC ${N.gnn.auc.toFixed(2)}.`)],
];
const vx = 7.05, vy = (k) => 1.85 + k * 1.75;
seg(s, vx, vy(0), vx, vy(2), { color: HEX.accent5, width: 2.25 }, "GNN route line");
gsteps.forEach(([h, b], k) => {
  stopDot(s, vx, vy(k), k === 2 ? "ai" : null, `GNN step ${k + 1} stop`);
  text(s, h, { x: vx + 0.5, y: vy(k) - 0.25, w: 5.2, h: 0.5, fontSize: 20, fontFace: HEAD, color: C.text2, valign: "middle", objectName: `GNN step ${k + 1} heading` });
  text(s, b, { x: vx + 0.5, y: vy(k) + 0.3, w: 5.2, h: 0.9, fontSize: 16, objectName: `GNN step ${k + 1} text` });
});
notes(s, KO
  ? ["GNN 점수: 두 배송지가 같은 트럭에 탈까?", "상위 파트너 8곳만 유지: 후보 1/7", "최적화기 계획으로 학습, 학습에 쓰지 않은 날짜 구간으로 평가",
    "질문이 나오면: 정확도 81.8%는 기본 정확도(항상 '다른 트럭') 81.3%와 비슷하므로 AUC 0.74로 평가"]
  : ["GNN scores: will two stops share a truck?", "Keeps the top 8 partners: 7x fewer candidates", "Trained on the optimizer's plans; evaluated on date blocks it never saw",
    "If asked: accuracy 81.8 % is close to the 81.3 % of always saying 'different truck', so we judge it by AUC 0.74"]);

// ---------- 7. exact selection ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("Weighing every load at once: 6 trucks, not 7", "모든 묶음을 한꺼번에 비교: 트럭 7대가 아니라 6대"));
const gv = pic(s, img("greedy_vs_opt"), 0.6, 1.5, 8.6, 4.5, L(`The same synthetic job: the earlier rule-based method needs ${N.example.greedy_trucks} trucks and ${fmt(N.example.greedy_km)} km, the exact optimizer ${N.example.trucks} trucks and ${fmt(N.example.km)} km`,
  `같은 합성 작업: 이전 규칙 기반 방법은 트럭 ${N.example.greedy_trucks}대, ${fmt(N.example.greedy_km)} km, 정확 최적화기는 트럭 ${N.example.trucks}대, ${fmt(N.example.km)} km`), "greedy_vs_opt");
text(s, L(`One truck at a time leaves a stop alone in its own truck. ${N.example.volume} m³ needs at least 6 trucks, so 6 is the minimum.`,
  `한 대씩 채우면 배송지 하나가 혼자 트럭을 씀. ${N.example.volume} m³에는 트럭이 최소 6대 필요하므로 6대가 최소.`),
  { x: 0.6, y: gv.y + gv.h + 0.1, w: gv.w, h: 0.5, fontSize: 12, color: C.accent4, objectName: "Example caption" });
const ox = 9.75, oy = (k) => 1.7 + k * 1.45;
seg(s, ox, oy(0), ox, oy(2), { color: HEX.accent5, width: 2.25 }, "Selection route line");
[
  [L("Stage A", "단계 A"), L("the fewest trucks that serve every stop once", "모든 배송지를 한 번씩 방문하는 최소 트럭 수"), "opt"],
  [L("Stage B", "단계 B"), L("among those plans, the fewest road km", "그 계획들 가운데 도로 km 최소"), "opt"],
  [L("Rule check", "규칙 검사"), L("every truck, every rule; 60 s per stage, a greedy plan as safety net", "모든 트럭, 모든 규칙. 단계당 60초, 안전망은 탐욕 계획"), null],
].forEach(([h, b, kind], k) => {
  stopDot(s, ox, oy(k), kind, `Selection ${k + 1} stop`);
  text(s, h, { x: ox + 0.45, y: oy(k) - 0.25, w: 2.6, h: 0.5, fontSize: 20, fontFace: HEAD, color: C.text2, valign: "middle", objectName: `Selection ${k + 1} heading` });
  text(s, b, { x: ox + 0.45, y: oy(k) + 0.28, w: 2.6, h: 1.0, fontSize: 15, objectName: `Selection ${k + 1} text` });
});
notes(s, KO
  ? ["같은 합성 작업, 같은 규칙", "탐욕: 트럭을 한 대씩 채우고 되돌릴 수 없음, 마지막 배송지가 혼자 남음", "단계 A 트럭, 단계 B km: 묶음 구성과 경로를 함께 결정", "모든 트럭에 규칙 검사"]
  : ["Same synthetic job, same rules", "Greedy fills one truck at a time and cannot undo: the last stop ends up alone", "Stage A trucks, stage B km: grouping and routing decided together", "Rule check on every truck"]);

// ---------- 8. headline result ----------
pres.addSection({ title: SEC.res });
s = pres.addSlide({ masterName: "Statement dark", sectionTitle: SEC.res });
title(s, L(`${fmt(T("real") - T("gnn_opt"))} fewer trucks on the same 97 jobs`, `같은 작업 97건에서 트럭 ${fmt(T("real") - T("gnn_opt"))}대 감소`));
text(s, pc(N.pct.real.trucks), { x: 0.8, y: 1.55, w: 5.6, h: 1.55, fontSize: 96, fontFace: HEAD, color: C.accent2, valign: "bottom", objectName: "Headline number" });
text(s, L(`trucks: ${fmt(T("gnn_opt"))} instead of ${fmt(T("real"))} in the real dispatch`, `트럭: 실제 배차 ${fmt(T("real"))}대 대신 ${fmt(T("gnn_opt"))}대`),
  { x: 0.8, y: 3.2, w: 5.4, h: 0.8, fontSize: 18, color: C.background1, objectName: "Headline label" });
stat(s, 0.8, 4.35, 2.7, pc(N.pct.real.km), L(`road km: ${fmt(M.gnn_opt.km)} instead of ${fmt(M.real.km)}`, `도로 km: ${fmt(M.real.km)} 대신 ${fmt(M.gnn_opt.km)}`), "Km",
  { size: 40, color: C.background1, lcolor: SOFT, ls: 14, lh: 0.9 });
stat(s, 3.75, 4.35, 2.5, "0", L("rule breaks in our plans, checked on every truck", "본 계획의 규칙 위반, 모든 트럭 검사"), "Breaks",
  { size: 40, color: C.background1, lcolor: SOFT, ls: 14, lh: 0.9 });
const methods = [
  [L("Real dispatch", "실제 배차"), T("real"), "E6EBE8"],
  [L("k-means", "k-평균"), T("kmeans"), "8FA89B"],
  [L("Agglomerative", "병합 군집"), T("agg"), "8FA89B"],
  ["OR-Tools", ORTOOLS_TRUCKS, "8FA89B"],
  [L("Optimizer, 15 nearest", "최적화기(15곳)"), T("opt"), "8FA89B"],
  [L("Optimizer, 8 nearest", "최적화기(8곳)"), W.methods.knn8.trucks, "8FA89B"],
  [L("GNN + optimizer (ours)", "GNN+최적화기(본 연구)"), T("gnn_opt"), HEX.accent2],
];
bars(s, methods.map((m) => m[0]), methods.map((m) => m[1]), methods.map((m) => m[2]),
  { name: "Trucks by method", x: 6.6, y: 1.55, w: 6.1, h: 4.9, ink: "FFFFFF", max: 3300, title: L("Trucks, all 97 jobs", "트럭 수, 작업 97건 전체"), gap: 40 });
text(s, L("Same jobs, roads and rules for every method.", "모든 방법에 같은 작업, 같은 도로, 같은 규칙."), { x: 6.6, y: 6.5, w: 6.1, h: 0.35, fontSize: 12, color: SOFT, objectName: "Chart note" });
notes(s, KO
  ? ["핵심: 트럭 −23%, 도로 km −21%, 규칙 위반 0", "최적화기 세 행이 트럭 수에서 다른 모든 방법보다 우수", "OR-Tools는 50 km 반경 규칙을 표현하지 못해 경로를 쪼갠 뒤 2,264대",
    "실제 배차는 데이터에 없는 사항(시간 요청 등)도 처리함: 시범 운영에서 측정"]
  : ["Main message: −23 % trucks, −21 % road km, 0 rule breaks", "The three optimizer rows beat every other method on trucks", "OR-Tools cannot express the 50 km radius: 2,264 trucks after splitting routes",
    "The real dispatch also handles things not in our data (time requests): the pilot will measure them"]);

// ---------- 9. one real job ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L(`One real job: ${N.compare.real} trucks became ${N.compare.ours}`, `실제 작업 하나: 트럭 ${N.compare.real}대가 ${N.compare.ours}대로`));
const cmp = pic(s, img("compare"), 0.6, 1.35, 8.7, 5.3, L(`One real job with ${N.compare.stops} stops on the map: ${N.compare.real} trucks in the real dispatch, ${N.compare.ours} in our plan; each line is one truck`,
  `지도 위 실제 작업 하나(배송지 ${N.compare.stops}곳): 실제 배차 트럭 ${N.compare.real}대, 본 계획 ${N.compare.ours}대; 선 하나가 트럭 한 대`), "compare");
stat(s, 9.8, 1.45, 2.9, pc((100 * (N.compare.ours / N.compare.real - 1)).toFixed(0)), L(`trucks on this job: ${N.compare.ours} instead of ${N.compare.real} for the same ${N.compare.stops} stops`,
  `이 작업의 트럭: 같은 배송지 ${N.compare.stops}곳에 ${N.compare.real}대 대신 ${N.compare.ours}대`), "Job saving", { size: 48, lh: 1.2 });
text(s, L("Each line is one truck leaving the depot (star). In the dense north-west, our plan joins short trips into full trucks of up to 5 stops.",
  "선 하나가 물류센터(별)에서 출발하는 트럭 한 대. 배송지가 몰린 수도권에서 짧은 운행을 최대 5곳짜리 트럭으로 합침."),
  { x: 9.8, y: 3.75, w: 2.9, h: 2.0, fontSize: 15, objectName: "Job note" });
text(s, L("Real stops at national scale, no labels.", "실제 배송지, 전국 축척, 표지 없음."), { x: 9.8, y: 6.3, w: 2.9, h: 0.35, fontSize: 11, color: C.accent4, objectName: "Job privacy note" });
notes(s, KO
  ? [`표지 지도와 같은 실제 작업: 배송지 ${N.compare.stops}곳`, `실제 배차 ${N.compare.real}대, 본 계획 ${N.compare.ours}대`, "같은 규칙: 트럭당 최대 5곳, 적재 60%, 반경 50 km"]
  : [`The real job from the title map: ${N.compare.stops} stops`, `Real dispatch ${N.compare.real} trucks, our plan ${N.compare.ours}`, "Same rules: up to 5 stops, 60 % load, 50 km radius"]);

// ---------- 10. per job ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L(`Fewer trucks on ${N.perjob.fewer} of 97 jobs`, `97건 중 ${N.perjob.fewer}건에서 트럭 감소`));
colChart(s, W.jobs.map((j) => j.date), W.jobs.map((j) => j.saved), W.jobs.map((j) => (j.saved < 0 ? HEX.accent5 : HEX.accent1)),
  { name: "Trucks saved per job", x: 0.6, y: 1.4, w: 12.1, h: 3.4, title: L("Trucks saved on each job against the real dispatch, in date order", "작업별 절감 트럭 수(실제 배차 대비), 날짜 순") });
stat(s, 0.6, 5.0, 5.8, pc(-N.bysize.big_pct), L(`on jobs above ${N.bysize.med_stops} stops (${pc(-N.bysize.small_pct)} below): bigger jobs give the optimizer more to combine`,
  `${N.bysize.med_stops}곳 초과 작업(이하 ${pc(-N.bysize.small_pct)}): 큰 작업일수록 조합할 여지가 많음`), "Big jobs", { size: 36, lh: 0.9 });
stat(s, 6.9, 5.0, 5.8, pc(-28.2), L("on the 13 jobs where the real dispatch kept every written rule: the saving does not come from rule breaks",
  "실제 배차가 문서화된 규칙을 모두 지킨 13건에서도: 절감은 규칙 위반 때문이 아님"), "Rule-keeping jobs", { size: 36, lh: 0.9 });
notes(s, KO
  ? [`작업별 절감: 97건 중 ${N.perjob.fewer}건에서 감소, 1건에서 1대 증가`, "가장 큰 절감은 5월 초 한 작업에서 24대", "큰 작업일수록 절감이 크고, 규칙 위반 때문이 아님"]
  : [`Per job: fewer trucks on ${N.perjob.fewer} of 97, one more truck on 1 job`, "Largest saving: 24 trucks on one job in early May", "Bigger jobs save more; not from rule breaks"]);

// ---------- 11. accuracy and speed ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L("Near-optimal on a benchmark, seconds on real jobs", "벤치마크에서는 최적에 근접, 실제 작업은 수 초"));
const hdr = (t_, right) => ({ text: t_, options: Object.assign({ bold: true, color: C.text2, fill: { color: C.background2 }, align: right ? "right" : "left" }, LANG) });
const cell = (t_, o = {}) => ({ text: t_, options: Object.assign({ align: "right" }, o) });
const bt = [[hdr(L("Benchmark instance", "벤치마크 인스턴스")), hdr(L("Proven optimum", "증명된 최적해"), 1), hdr(L("Ours", "본 연구"), 1), hdr(L("Gap", "격차"), 1)]].concat(
  N.bench.map((r) => [{ text: r.name, options: { align: "left" } }, cell(fmt(r.optimum)), cell(fmt(r.cost), { bold: true }), cell(pc(r.gap.toFixed(1)), { bold: r.gap > 0 })]));
s.addTable(bt, Object.assign({ x: 0.6, y: 1.5, w: 6.1, colW: [2.2, 1.6, 1.1, 1.2], fontSize: 14, color: C.text1, fontFace: L("Calibri", "Malgun Gothic"),
  border: { type: "solid", pt: 0.75, color: HAIR }, rowH: 0.44, margin: [0, 0.08, 0, 0.08], valign: "middle", objectName: "Benchmark table" }, LANG));
stat(s, 0.6, 4.4, 2.8, L(`${nOpt} of 5`, `5개 중 ${nOpt}개`), L("instances solved to the proven optimum", "인스턴스에서 증명된 최적해"), "Benchmark optimal", { size: 36, ls: 14, lh: 0.7 });
stat(s, 3.7, 4.4, 3.0, pc(gap.toFixed(2)), L(`average gap; at most ${Math.ceil(Math.max(...N.bench.map((r) => r.s)))} s per instance`, `평균 격차, 인스턴스당 최대 ${Math.ceil(Math.max(...N.bench.map((r) => r.s)))}초`), "Benchmark gap", { size: 36, ls: 14, lh: 0.7 });
text(s, L("CVRPLIB set P (Augerat et al., 1995): the five instances whose optimal routes have at most 5 customers, like the 5-address rule.",
  "CVRPLIB 세트 P(Augerat 외, 1995): 최적 경로가 고객 5곳 이하인 인스턴스 5개(주소 5곳 규칙과 같은 조건)."),
  { x: 0.6, y: 6.15, w: 6.1, h: 0.6, fontSize: 11, color: C.accent4, objectName: "Benchmark note" });
const pair = [L("15 nearest stops", "최근접 15곳"), L("GNN short list", "GNN 후보 목록")];
bars(s, pair, N.gnn.cols, [HEX.accent3, HEX.accent1], { name: "Candidate loads", x: 7.2, y: 1.4, w: 5.5, h: 2.2, max: 25000, title: L("Real jobs: candidate loads per job, median", "실제 작업: 작업당 후보 묶음, 중앙값") });
bars(s, pair, N.gnn.s, [HEX.accent3, HEX.accent1], { name: "Solve time", x: 7.2, y: 3.75, w: 5.5, h: 2.2, max: 88, format: L('0.0" s"', '0.0"초"'), title: L("Real jobs: solve time per job, median", "실제 작업: 작업당 풀이 시간, 중앙값") });
text(s, L(`The price: ${pc("+" + (100 * (T("gnn_opt") / T("opt") - 1)).toFixed(1))} trucks against the 15-nearest list, and ${W.methods.knn8.trucks - T("gnn_opt")} fewer than the 8 nearest stops at the same list size.`,
  `대가: 최근접 15곳 목록보다 트럭 ${pc("+" + (100 * (T("gnn_opt") / T("opt") - 1)).toFixed(1))}, 같은 목록 크기의 최근접 8곳보다는 ${W.methods.knn8.trucks - T("gnn_opt")}대 적음.`),
  { x: 7.2, y: 6.1, w: 5.5, h: 0.7, fontSize: 14, objectName: "Speed note" });
notes(s, KO
  ? ["정확도 = 공개 벤치마크에서 증명된 최적해와의 격차, 누구나 다시 실행 가능", "작은 인스턴스이므로 어려운 시험은 아님: 최적화기와 거리 코드가 맞는지 확인", "속도: 후보 1/7, 시간 1/10",
    `60초 제한에 걸린 작업: GNN 목록 ${N.gnn.limit[1]}건, 최근접 15곳 ${N.gnn.limit[0]}건`, "질문: 왜 15곳 목록이 트럭이 더 적은가? 후보가 약 19,000개 대 2,900개, 대신 67초 대 7초"]
  : ["Accuracy = gap to the proven optimum on a public benchmark; anyone can rerun it", "Small instances, so not a hard test: it confirms the optimizer and distance code", "Speed: 7x fewer candidates, 10x faster",
    `Jobs hitting the 60 s limit: ${N.gnn.limit[1]} with the GNN list, ${N.gnn.limit[0]} with 15 nearest`, "If asked why the 15-nearest list wins on trucks: ~19,000 candidates per job vs ~2,900, but 67 s vs 7 s"]);

// ---------- 12. expected effects ----------
pres.addSection({ title: SEC.imp });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.imp });
title(s, L("What it means over a year", "1년으로 보면"));
const R = N.save.real, Y_ = R.year, rnd = (v, u) => fmt(Math.round(v / u) * u);
// one row per KPI: what it is (icon), 4 months measured, the change, the year (upper bound)
const kpis = [
  ["truck", L("Trucks hired", "용차 트럭(대)"), fmt(R.trucks), pc(N.pct.real.trucks), rnd(Y_.trucks, 100)],
  ["road", L("Road km", "도로 km"), fmt(R.km), pc(N.pct.real.km), rnd(Y_.km, 1000)],
  ["clock", L("Driving hours", "운행 시간"), fmt(R.hours), pc(N.pct.real.hours), rnd(Y_.hours, 100)],
  ["currency-won", L("Hire cost, million won (estimate)", "용차 비용, 백만 원(추정)"), String(Math.round(R.won / 1e6)), pc(N.pct.real.cost), String(Math.round(Y_.won / 1e7) * 10)],
];
const kx = { name: 1.4, now: 5.0, pct: 7.3, year: 9.4 };
[[L("Saved in 4 months, 97 jobs", "4개월 절감, 작업 97건"), kx.now, 2.2], [L("Change", "변화"), kx.pct, 1.6], [L("Per year, upper bound", "연간, 상한"), kx.year, 2.4]].forEach(([t_, x, w], k) =>
  text(s, t_, { x, y: 1.4, w, h: 0.45, fontSize: 14, color: C.accent4, align: "right", valign: "bottom", objectName: `KPI header ${k + 1}` }));
kpis.forEach(([ic, name, now, chg, year], k) => {
  const y = 1.95 + k * 0.95;
  hair(s, 0.6, y, 11.2, `KPI ${k + 1} rule`);
  icon(s, ic, "green", 0.6, y + 0.17, 0.55, name);
  text(s, name, { x: kx.name, y: y + 0.12, w: 3.5, h: 0.65, fontSize: 18, valign: "middle", objectName: `KPI ${k + 1} name` });
  text(s, now, { x: kx.now, y: y + 0.08, w: 2.2, h: 0.72, fontSize: 32, fontFace: HEAD, color: C.text2, align: "right", valign: "middle", objectName: `KPI ${k + 1} four months` });
  text(s, chg, { x: kx.pct, y: y + 0.08, w: 1.6, h: 0.72, fontSize: 20, fontFace: HEAD, color: C.accent1, align: "right", valign: "middle", objectName: `KPI ${k + 1} change` });
  text(s, L("about ", "약 ") + year, { x: kx.year, y: y + 0.08, w: 2.4, h: 0.72, fontSize: 24, fontFace: HEAD, color: C.accent5, align: "right", valign: "middle", objectName: `KPI ${k + 1} year` });
});
hair(s, 0.6, 1.95 + 4 * 0.95, 11.2, "KPI rule end");
[
  [L("Upper bound: ", "상한: "), L("97 jobs × 365 / 123 days, all from the main season for coolers and fans.", "작업 97건 × 365 / 123일, 모두 냉풍기와 선풍기 성수기 자료.")],
  [L("Cost: ", "비용: "), L("two brokers' public list prices. Fares depend mostly on km, so money saved is smaller than trucks saved.", "중개업체 두 곳의 공개 요금표. 요금은 주로 km에 따라 정해지므로 비용 절감이 트럭 절감보다 작음.")],
].forEach(([h, b], k) => text(s, [{ text: h, options: { bold: true, color: C.text2 } }, { text: b }],
  { x: 0.6 + k * 6.15, y: 6.0, w: 5.8, h: 0.75, fontSize: 13, objectName: `Effects note ${k + 1}` }));
notes(s, KO
  ? ["4개월은 측정값, 연간은 상한", "비용 절감 약 14%: 요금이 주로 거리에 따라 정해지기 때문", "트럭이 줄면 예약할 기사, 상차 시간대, 배차 담당자의 시간도 줄어듦", "목적 함수를 비용으로 바꿀 수 있음(향후 과제)"]
  : ["Four months measured; per year is an upper bound", "Money saved about 14 %: fares depend mostly on distance", "Fewer trucks also mean fewer drivers to book, fewer loading slots, less dispatcher time", "The objective could be changed to cost (future work)"]);

// ---------- 13. prototype ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.imp });
title(s, L("A planner that fits the daily routine", "일상 배차 업무에 맞춘 계획기"));
const app = pic(s, img("app_top"), 0.45, 1.35, 8.6, 2.6, L("The prototype's opening screen: title and headline numbers (1,933 trucks, −23.2 %, −21.2 % road km, 0 rule breaks)",
  "프로토타입 첫 화면: 제목과 주요 수치(트럭 1,933대, −23.2%, 도로 km −21.2%, 규칙 위반 0)"), "app_top");
text(s, L("The prototype: headline numbers, one job step by step, every method, and every job on a map, behind a password.",
  "프로토타입: 주요 수치, 작업 하나의 단계별 과정, 모든 방법 비교, 모든 작업의 지도. 비밀번호로 보호."),
  { x: 0.6, y: app.y + app.h + 0.12, w: app.w, h: 0.45, fontSize: 12, color: C.accent4, objectName: "Prototype caption" });
// the plan sheet a dispatcher receives, for the synthetic job (example_plan.md, written by make_figs.py)
const planRows = fs.readFileSync(path.join(__dirname, "example_plan.md"), "utf8").split("\n").filter((l) => /^\| \d/.test(l))
  .map((l) => l.split("|").slice(1, -1).map((c_) => c_.trim()));
const ph = (t_, right) => ({ text: t_, options: Object.assign({ bold: true, color: C.text2, fill: { color: C.background2 }, align: right ? "right" : "left" }, LANG) });
const sizeKo = (t_) => L(t_, t_.replace("-ton", "톤"));
s.addTable([[ph(L("Truck", "트럭")), ph(L("Stops in visiting order", "방문 순서")), ph("m³", 1), ph(L("Size", "크기")), ph(L("Of 60 % limit", "60% 한도 대비"), 1), ph("km", 1)]].concat(
  planRows.map((r) => [r[0], r[1], r[2], sizeKo(r[3]), pc(r[4].replace(" %", "")), r[5]].map((c_, k) => ({ text: c_, options: { align: [0, 2, 4, 5].includes(k) ? "right" : "left" } })))),
Object.assign({ x: 0.6, y: 4.78, w: 8.3, colW: [0.75, 3.5, 0.85, 1.1, 1.4, 0.7], fontSize: 12, color: C.text1, fontFace: L("Calibri", "Malgun Gothic"),
  border: { type: "solid", pt: 0.75, color: HAIR }, rowH: 0.26, margin: [0, 0.08, 0, 0.08], valign: "middle", objectName: "Plan sheet table" }, LANG));
text(s, L(`The plan sheet for the synthetic job: ${planRows.length} trucks for 26 stops.`, `합성 작업의 배차표: 배송지 26곳에 트럭 ${planRows.length}대.`),
  { x: 0.6, y: 6.66, w: 8.3, h: 0.3, fontSize: 11, color: C.accent4, objectName: "Plan sheet caption" });
const fx = 9.7, fy = (k) => 1.8 + k * 1.35;
seg(s, fx, fy(0), fx, fy(3), { color: HEX.accent5, width: 2.25 }, "Routine route line");
[
  ["file-spreadsheet", L("Order export", "주문 내보내기"), L("today's spreadsheet", "현재 쓰는 스프레드시트")],
  ["cpu", L("Planner", "배차 계획기"), L("company PC, seconds per job", "회사 PC, 작업당 수 초")],
  ["map-2", L("Plan sheet and map", "배차표와 지도"), L("stops in order, truck size, km", "방문 순서, 트럭 크기, km")],
  ["user-check", L("Dispatcher", "배차 담당자"), L("reviews, edits, books trucks", "검토, 수정, 트럭 예약")],
].forEach(([ic, h, b], k) => {
  iconStop(s, fx, fy(k), k === 1 ? "opt" : null, ic, `Routine ${k + 1}`);
  text(s, h, { x: fx + 0.5, y: fy(k) - 0.3, w: 2.55, h: 0.45, fontSize: 19, fontFace: HEAD, color: C.text2, valign: "middle", objectName: `Routine ${k + 1} heading` });
  text(s, b, { x: fx + 0.5, y: fy(k) + 0.17, w: 2.55, h: 0.6, fontSize: 14, color: C.text1, objectName: `Routine ${k + 1} text` });
});
notes(s, KO
  ? ["기존 업무에 맞춤: 내보내기 파일이 들어가고 배차표가 나옴", "여기서 실시간 시연: 핵심 수치, 이어서 지도 위 작업 하나", "비밀번호 보호, 외부 서비스 없음"]
  : ["Fits the existing routine: export in, plan sheet out", "LIVE DEMO here: headline numbers, then one job on the map", "Password protected; no external services"]);

// ---------- 14. conclusion and pilot ----------
s = pres.addSlide({ masterName: "Statement dark", sectionTitle: SEC.imp });
title(s, L("Fewer trucks, every rule kept, seconds per job", "트럭은 줄이고, 규칙은 지키고, 작업당 수 초"));
text(s, [
  L(`${Math.round(-N.pct.real.trucks)} % fewer trucks and ${Math.round(-N.pct.real.km)} % fewer road km on 97 real jobs, with 0 rule breaks`, `실제 작업 97건에서 트럭 ${Math.round(-N.pct.real.trucks)}%, 도로 km ${Math.round(-N.pct.real.km)}% 감소, 규칙 위반 0`),
  L(`${gap.toFixed(2)} % from the proven optimum on a public benchmark`, `공개 벤치마크에서 증명된 최적해와 평균 ${gap.toFixed(2)}% 차이`),
  L(`${N.gnn.s[1]} s per job on one PC; customer data stays in the company`, `PC 1대에서 작업당 ${N.gnn.s[1]}초, 고객 데이터는 회사 안에`),
  L(`Up to about ${rnd(Y_.trucks, 100)} fewer trucks a year (main-season upper bound)`, `연간 최대 약 ${rnd(Y_.trucks, 100)}대 감소(성수기 기준 상한)`),
].map((t_, k, a) => ({ text: t_, options: { bullet: { indent: 18 }, breakLine: k < a.length - 1, paraSpaceAfter: 12 } })),
{ x: 0.8, y: 1.75, w: 5.7, h: 3.9, fontSize: 18, color: C.background1, objectName: "Conclusions" });
text(s, L("Next: a pilot next to the dispatcher", "다음 단계: 배차 담당자 옆에서 시범 운영"), { x: 7.2, y: 1.6, w: 5.5, h: 0.5, fontSize: 20, fontFace: HEAD, color: C.background1, objectName: "Pilot heading" });
const px = 7.45, py = (k) => 2.55 + k * 0.95;
seg(s, px, py(0), px, py(3), { color: HEX.lt1, width: 2 }, "Pilot route line");
[
  [L("Dec 2026", "2026년 12월"), L("set up on a company PC", "회사 PC에 설치")],
  [L("Jan 2027", "2027년 1월"), L("shadow mode, side by side", "섀도 모드, 나란히 비교")],
  [L("Feb to Mar 2027", "2027년 2~3월"), L("dispatcher starts from the plan", "담당자가 계획에서 시작")],
  [L("Apr 2027", "2027년 4월"), L("measure the savings, decide", "절감 측정, 도입 결정")],
].forEach(([when, what], k) => {
  stopDot(s, px, py(k), null, `Pilot ${k + 1} stop`, true);
  text(s, [{ text: when + "  ", options: { fontFace: HEAD, color: C.background1 } }, { text: what, options: { color: SOFT } }],
    { x: px + 0.45, y: py(k) - 0.25, w: 4.8, h: 0.5, fontSize: 16, valign: "middle", objectName: `Pilot ${k + 1} text` });
});
text(s, L("Thank you. Questions?", "감사합니다. 질문을 받겠습니다."), { x: 0.8, y: 6.15, w: 6.5, h: 0.6, fontSize: 26, fontFace: HEAD, color: C.background1, objectName: "Thanks" });
text(s, L("Team ANALOG, Changwon National University", "팀 ANALOG, 국립창원대학교"), { x: 7.2, y: 6.3, w: 4.7, h: 0.4, fontSize: 14, color: SOFT, objectName: "Team line" });
notes(s, KO
  ? ["결론: 트럭 23%, 거리 21%, 위반 0, 벤치마크 0.06%", "연간 최대 약 1,700대(상한)", "다음: 2026년 12월부터 시범 운영, 이후 시간 창·기사 근무 시간 추가, 비용 최적화, 매월 재학습", "질문 받기"]
  : ["Conclusion: −23 % trucks, −21 % km, 0 breaks, 0.06 % benchmark gap", "Up to ~1,700 trucks a year (upper bound)", "Next: pilot from Dec 2026; then time windows and driver hours, a cost objective, monthly retraining", "Invite questions"]);

// ---------- 15. key references (short form; the full list with DOIs is in the report) ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.imp });
title(s, L("Key references", "주요 참고문헌"));
const KEYREFS = require("./deck_refs.json"); // [[left column...], [right column...]], short form, from the report's list
KEYREFS.forEach((col, c) => text(s, col.map((r, k) => ({ text: r, options: { breakLine: k < col.length - 1, paraSpaceAfter: 6 } })),
  { x: 0.6 + c * 6.25, y: 1.45, w: 5.85, h: 5.1, fontSize: 12, color: C.text1, lang: "en-US", objectName: `References ${c + 1}` }));
text(s, L("Full list with DOIs: report, References.", "DOI를 포함한 전체 목록: 보고서 참고문헌."), { x: 0.6, y: 6.6, w: 8, h: 0.3, fontSize: 11, color: C.accent4, objectName: "References note" });
notes(s, KO ? ["보고서 참고문헌의 핵심 항목"] : ["The key entries of the report's list"]);

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
