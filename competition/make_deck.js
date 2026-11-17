// Competition slides (2nd LogisticSolver 2026, team ANALOG): Version 1 results only, 15 slides, poster colours.
//   node competition/make_deck.js       -> English deck
//   node competition/make_deck.js ko    -> Korean deck (same layout, Korean text, Malgun Gothic)
// Every diagram is native (shapes, lines, charts), so all words and numbers stay editable. Pictures remain only where
// they show real stop locations (national map, one-job map, title background): editable data there would embed customer
// coordinates. Pictures: figs/slides/*.png; the Korean deck takes figs/ko/*.png (from `make_figs.py ko`) when present.
const fs = require("fs");
const path = require("path");
const os = require("os");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const KO = process.argv[2] === "ko";
const L = (en, ko) => (KO ? ko : en);
const LANG = KO ? { lang: "ko-KR" } : {};
const pc = (v) => L(`${v} %`, `${v}%`); // Korean writes no space before %

const IMG = path.join(__dirname, "figs/slides");
const IMG_KO = path.join(__dirname, "figs/ko");
const OUT = path.join(os.homedir(), "reports/LogisticSolver_2026", L("ANALOG_LogisticSolver2026_Slides.pptx", "ANALOG_LogisticSolver2026_Slides_KO.pptx"));
const N = JSON.parse(fs.readFileSync(path.join(__dirname, "numbers.json"), "utf8"));
const J = JSON.parse(fs.readFileSync(path.join(__dirname, "synthetic_job.json"), "utf8")); // synthetic example job
const TITLE = L("AI-Based Clustering and Automatic Dispatching for Bulky Product Delivery", "대형 제품 배송을 위한 AI 기반 클러스터링 및 자동 배차");

const FONT = L("Calibri", "Malgun Gothic");
const THEME = {
  name: "ANALOG poster",
  headFontFace: FONT,
  bodyFontFace: FONT,
  eaFont: L(undefined, FONT),  // Korean letters get Malgun Gothic from the theme (apply_theme.js)
  colors: {
    dk1: "1C2430", lt1: "FFFFFF", dk2: "1D3F86", lt2: "EEF4FB",
    accent1: "2F6FDB", accent2: "CF7F2E", accent3: "A3ACB8", accent4: "5B6676", accent5: "DCE8FB", accent6: "7A8594",
    hlink: "2F6FDB", folHlink: "1D3F86",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = L("Team ANALOG", "팀 ANALOG");
pres.title = TITLE;
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
    { text: { text: L("Team ANALOG  |  2nd LogisticSolver 2026", "팀 ANALOG  |  제2회 LogisticSolver 2026"), options: Object.assign({ x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 }, LANG) } },
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
// picture file: the Korean deck uses the Korean-labelled copy from make_figs.py ko when it exists
function img(name) {
  const ko = path.join(IMG_KO, name + ".png");
  if (KO && fs.existsSync(ko)) return ko;
  if (KO) console.warn(`note: ${ko} not found, using the English picture`);
  return path.join(IMG, name + ".png");
}
// picture fitted inside the box (x, y, w, h), centred, aspect kept
function pic(slide, name, x, y, w, h, alt) {
  const file = img(name);
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
  slide.addText(t, Object.assign({ isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top" }, LANG, o));
}
const title = (slide, t) => slide.addText(t, Object.assign({ placeholder: "title" }, LANG));
// big number with a label under it
function stat(slide, x, y, w, big, label, name, color) {
  text(slide, big, { x, y, w, h: 0.85, fontSize: L(44, 36), bold: true, color: color || C.accent1, valign: "bottom", objectName: name + " number" });
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
// straight line from (x1, y1) to (x2, y2) in any direction (a LINE shape runs top-left to bottom-right unless flipped)
function seg(slide, x1, y1, x2, y2, line, name) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line, objectName: name });
}
// filled circle centred on (cx, cy)
function disc(slide, cx, cy, d, fill, name, line) {
  slide.addShape(pres.shapes.OVAL, { x: cx - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: fill }, line: line || { type: "none" }, objectName: name });
}
const notes = (slide, cues) => slide.addNotes(cues.map((c) => "- " + c).join("\n"));
const fmt = (n) => n.toLocaleString("en-US");
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" };

const M = N.methods;
const T = (k) => M[k].trucks;
const SEC = { open: L("Opening", "도입"), prob: L("Problem", "문제"), meth: L("Method", "방법"), res: L("Results", "결과"), imp: L("Impact", "효과") };

// ---------- 1. title ----------
pres.addSection({ title: SEC.open });
let s = pres.addSlide({ masterName: "Title dark", sectionTitle: SEC.open });
s.addText(L("2nd LogisticSolver 2026  |  Smart Logistics Problem-Solving Competition", "제2회 LogisticSolver 2026 스마트 물류 문제 해결 경진대회"), Object.assign({ placeholder: "kicker" }, LANG));
s.addText(TITLE, Object.assign({ placeholder: "title" }, LANG));
s.background = { path: img("slide_bg") };
s.addText(L("A graph neural network that shortlists and an exact optimizer that decides, tested on 97 real dispatch jobs and on a public benchmark",
  "후보를 추리는 그래프 신경망(GNN)과 결정을 내리는 정확 최적화기, 실제 배차 작업 97건과 공개 벤치마크로 검증"), Object.assign({ placeholder: "body" }, LANG));
s.addText(KO ? [
  { text: "팀 ANALOG", options: { bold: true, fontSize: 18, breakLine: true } },
  { text: "Ryry Rizky Asri (팀장), 정보통신공학과", options: { breakLine: true } },
  { text: "최영은, 전자공학과", options: { breakLine: true } },
  { text: "최정혜, 전자공학과", options: { breakLine: true } },
  { text: "국립창원대학교, 2026년 11월", options: { color: C.accent5 } },
] : [
  { text: "Team ANALOG", options: { bold: true, fontSize: 18, breakLine: true } },
  { text: "Ryry Rizky Asri (team lead), Dept. of Information and Communication Engineering", options: { breakLine: true } },
  { text: "최영은", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: " and ", options: {} },
  { text: "최정혜", options: { lang: "ko-KR", fontFace: "Malgun Gothic" } },
  { text: ", Dept. of Electronic Engineering", options: { breakLine: true } },
  { text: "Changwon National University, November 2026", options: { color: C.accent5 } },
], Object.assign({ placeholder: "team" }, LANG));
notes(s, KO
  ? ["팀 ANALOG, 국립창원대학교", "대형 제품 배송: AI와 정확 최적화기로 트럭 감소", "실제 배차 작업 97건에 대한 버전 1 결과"]
  : ["Team ANALOG, Changwon National University", "Bulky delivery: fewer trucks with AI plus an exact optimizer", "Version 1 results on 97 real dispatch jobs"]);

// ---------- 2. results at a glance ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.open });
title(s, L("23 % fewer trucks on 97 real jobs", "실제 배차 작업 97건에서 트럭 23% 절감"));
const glance = [
  [pc(N.pct.real.trucks).replace("-", "−"), L(`trucks: ${fmt(T("gnn_opt"))} instead of ${fmt(T("real"))} in the real dispatch`, `트럭: 실제 배차 ${fmt(T("real"))}대 대신 ${fmt(T("gnn_opt"))}대`)],
  [pc(N.pct.real.km).replace("-", "−"), L(`total road km: ${fmt(M.gnn_opt.km)} instead of ${fmt(M.real.km)}`, `총 도로 km: ${fmt(M.real.km)} 대신 ${fmt(M.gnn_opt.km)}`)],
  [pc("0.06"), L("average gap to the proven optimum on a public benchmark", "공개 벤치마크에서 증명된 최적해와의 평균 격차")],
  [L(`${N.gnn.s[1]} s`, `${N.gnn.s[1]}초`), L("median planning time per job on one PC", "PC 1대에서 작업당 계획 시간(중앙값)")],
];
glance.forEach(([big, label], k) => {
  const x = 0.6 + k * 3.1;
  card(s, x, 1.75, 2.85, 2.35, `Result card ${k + 1}`);
  stat(s, x + 0.3, 1.95, 2.3, big, label, `Result ${k + 1}`);
});
card(s, 0.6, 4.75, 12.1, 1.75, "Context card", C.accent5);
text(s, [
  { text: L("Same jobs, same roads, same company rules. ", "같은 작업, 같은 도로, 같은 회사 규칙. "), options: { bold: true, color: C.text2 } },
  { text: L("Every truck of every plan meets every rule (0 violations). Data: 6,395 stops, 7 April to 7 August 2026. Accuracy is checked on public benchmark instances with proven optimal answers.",
    "모든 계획의 모든 트럭이 모든 규칙을 충족(위반 0건). 데이터: 배송지 6,395곳, 2026년 4월 7일~8월 7일. 정확도는 최적해가 증명된 공개 벤치마크 인스턴스로 검증.") },
], { x: 0.9, y: 5.0, w: 11.5, h: 1.3, fontSize: 17, valign: "middle", objectName: "Context text" });
notes(s, KO
  ? ["핵심 메시지 먼저: 트럭 −23%, 총 도로 km −21%", "정확도: 공개 벤치마크의 증명된 최적해 대비 0.06%", "속도: 작업당 약 7초", "회사 규칙 모두 충족"]
  : ["Main message first: −23 % trucks, −21 % total road km", "Accuracy: 0.06 % from proven optima on a public benchmark", "Fast: about 7 s per job", "All company rules met"]);

// ---------- 3. problem ----------
pres.addSection({ title: SEC.prob });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Bulky deliveries are grouped by hand", "대형 제품 배송은 수작업으로 묶음 구성"));
const prob = [
  [L("One depot, the whole country", "물류센터 한 곳, 전국 배송"), L("A home-appliance maker in the Changwon area ships air coolers, large fans and similar goods with trucks hired per trip.",
    "창원 지역의 한 가전 제조사가 냉풍기, 대형 선풍기 등을 운행마다 빌리는 트럭(용차)으로 배송.")],
  [L("Grouping by rules of thumb", "경험칙에 의한 묶음 구성"), L("For every dispatch job a person groups the addresses into trucks. It takes time, depends on the person and is hard to check.",
    "배차 작업마다 담당자가 주소를 트럭별로 묶음. 시간이 걸리고, 사람에 따라 달라지며, 검증이 어려움.")],
  [L("Volume decides almost everything", "부피가 거의 모든 것을 결정"), L(`A typical job has ${N.data.per_job_med} addresses (${N.data.per_job_min} to ${N.data.per_job_max}), about ${N.data.vol_med} m³ each: five of them already fill a 1-ton truck.`,
    `일반적인 작업은 주소 ${N.data.per_job_med}곳(${N.data.per_job_min}~${N.data.per_job_max}곳), 각 약 ${N.data.vol_med} m³: 5곳이면 1톤 트럭이 가득 참.`)],
];
prob.forEach(([h, b], k) => {
  const y = 1.65 + k * 1.7;
  dot(s, 0.6, y + 0.05, k + 1, `Problem ${k + 1} marker`);
  text(s, h, { x: 1.35, y, w: 6.9, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: `Problem ${k + 1} heading` });
  text(s, b, { x: 1.35, y: y + 0.5, w: 6.9, h: 1.05, fontSize: 16, objectName: `Problem ${k + 1} text` });
});
const mp = pic(s, "map", 8.7, 1.45, 4.0, 5.1, L("Map of South Korea with one dot per delivery stop and the depot in Changwon", "배송지마다 점 하나를 찍은 대한민국 지도와 창원 물류센터"));
text(s, L("6,395 stops, one dot each; every truck leaves the depot in Changwon", "배송지 6,395곳(점 하나가 한 곳), 모든 트럭은 창원 물류센터에서 출발"),
  { x: 8.55, y: mp.y + mp.h + 0.05, w: 4.3, h: 0.45, fontSize: 11, color: C.accent4, align: "center", objectName: "Map caption" });
notes(s, KO
  ? ["용차: 몇 대가 필요한가가 아니라 얼마나 줄일 수 있는가", "현재: 수작업, 경험칙", "일반적인 작업은 주소 63곳, 부피 규칙이 지배적"]
  : ["Hired trucks: question is how few, not how many", "Today: by hand, rules of thumb", "Typical job 63 addresses; volume rule dominates"]);

// ---------- 4. rules and why it is hard ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Four rules, millions of choices", "규칙 4가지, 수백만 가지 선택지"));
// three rule panels, drawn: 5 stops | box filled to 60 % | 50 km circle
const ruleLab = [L("1 to 5 addresses per truck", "트럭당 주소 1~5곳"), L("load at most 60 % of the box", "적재는 적재함의 60% 이하"), L("every stop within 50 km of the centre", "모든 배송지가 중심에서 50 km 이내")];
ruleLab.forEach((t_, k) => text(s, t_, { x: 0.6 + k * 4.033 - 0.05, y: 3.2, w: 4.13, h: 0.42, fontSize: 16, align: "center", objectName: `Rule ${k + 1} label` }));
for (let i = 0; i < 5; i++) disc(s, 1.38 + i * 0.62, 2.3, 0.46, C.accent1, `Rule 1 stop ${i + 1}`);
s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.8, w: 2.9 * 0.6, h: 1.0, fill: { color: "C9DAF7" }, line: { type: "none" }, objectName: "Rule 2 load" });
s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.8, w: 2.9, h: 1.0, fill: { type: "none" }, line: { color: HEX.dk2, width: 1.75 }, objectName: "Rule 2 box" });
seg(s, 5.2 + 2.9 * 0.6, 1.8, 5.2 + 2.9 * 0.6, 2.8, { color: HEX.dk2, width: 1.75, dashType: "dash" }, "Rule 2 limit");
text(s, pc(60), { x: 5.2, y: 1.8, w: 2.9 * 0.6, h: 1.0, fontSize: 20, bold: true, color: C.text2, align: "center", valign: "middle", objectName: "Rule 2 share" });
const rc = { x: 10.5, y: 2.3, r: 0.72 };
s.addShape(pres.shapes.OVAL, { x: rc.x - rc.r, y: rc.y - rc.r, w: 2 * rc.r, h: 2 * rc.r, fill: { color: C.background2 }, line: { color: HEX.dk2, width: 1.5, dashType: "dash" }, objectName: "Rule 3 circle" });
[[-1.2, 0.6], [0.9, 1.1], [0.3, -1.2], [-0.6, -0.5], [1.5, -0.2]].forEach(([dx, dy], i) => disc(s, rc.x + dx * 0.314, rc.y - dy * 0.314, 0.21, C.accent1, `Rule 3 stop ${i + 1}`));
seg(s, rc.x, rc.y, rc.x + rc.r * 0.8, rc.y + rc.r * 0.6, { color: HEX.accent4, width: 1 }, "Rule 3 radius");
text(s, "50 km", { x: rc.x + rc.r * 1.0, y: rc.y + rc.r * 0.5, w: 0.9, h: 0.32, fontSize: 14, color: C.accent4, objectName: "Rule 3 radius label" });
text(s, [
  { text: L("Rule 4: ", "규칙 4: "), options: { bold: true, color: C.text2 } },
  { text: L("at most ten 1.4-ton trucks per job; larger trucks take one address only.", "작업당 1.4톤 트럭은 최대 10대, 그보다 큰 트럭은 주소 1곳만 배송.") },
], { x: 0.6, y: 3.85, w: 12.1, h: 0.4, fontSize: 16, objectName: "Rule 4" });
card(s, 0.6, 4.5, 5.9, 2.15, "Objective card");
text(s, L("Objective", "목적"), { x: 0.9, y: 4.7, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Objective heading" });
text(s, L("First, the fewest trucks. Second, among those plans, the fewest road kilometres. Every stop is served exactly once.",
  "첫째, 트럭 수 최소. 둘째, 그 계획들 가운데 도로 km 최소. 모든 배송지는 정확히 한 번 방문."), { x: 0.9, y: 5.2, w: 5.3, h: 1.3, fontSize: 16, objectName: "Objective text" });
card(s, 6.8, 4.5, 5.9, 2.15, "Hardness card");
text(s, L("7.7 million", "770만"), { x: 7.1, y: 4.6, w: 5.3, h: 0.8, fontSize: 44, bold: true, color: C.accent1, valign: "bottom", objectName: "Hardness number" });
text(s, L("possible groups of up to 5 stops in a 63-stop job. Choosing groups that cover every stop once is set partitioning, an NP-hard problem.",
  "배송지 63곳 작업에서 만들 수 있는 5곳 이하 묶음의 수. 모든 배송지를 한 번씩 덮는 묶음 선택은 집합 분할 문제로, NP-난해."),
  { x: 7.1, y: 5.45, w: 5.3, h: 1.1, fontSize: 15, color: C.accent4, objectName: "Hardness text" });
notes(s, KO
  ? ["회사의 제약 조건 목록에 따른 규칙", "목표: 트럭 최소, 다음으로 km 최소", "묶음 770만 개: 수작업이나 탐욕 규칙으로는 감당 불가"]
  : ["Rules from the company's constraint list", "Goal: fewest trucks, then fewest km", "7.7 million groups: too many for hand or greedy rules"]);

// ---------- 5. data and privacy ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.prob });
title(s, L("Real data that stays in the company", "회사 밖으로 나가지 않는 실제 데이터"));
[[String(N.data.jobs), L("real dispatch jobs", "실제 배차 작업")], [fmt(N.data.stops), L("delivery stops", "배송지")], [String(N.data.days), L("operating days, April to August 2026", "운영일, 2026년 4월~8월")]].forEach(([big, label], k) => {
  stat(s, 0.6, 1.55 + k * 1.75, 4.2, big, label, `Data ${k + 1}`, C.text2);
});
const priv = [
  [L("Company records, shared with consent", "동의를 받아 공유된 회사 기록"), L("Job, date, coordinates, order volume and the real truck groups, plus the truck list and the dispatch rules.",
    "작업, 날짜, 좌표, 주문 부피, 실제 트럭 묶음, 그리고 트럭 목록과 배차 규칙.")],
  [L("Our own map server", "자체 지도 서버"), L("Road km and driving time from OpenStreetMap on a private OSRM server: no address is sent to an online service.",
    "비공개 OSRM 서버에서 OpenStreetMap으로 도로 km와 운행 시간 계산: 온라인 서비스로 보내는 주소 없음.")],
  [L("Personal data never used", "개인정보 미사용"), L("Names and phone numbers stay out of the planner. Every example shown here uses synthetic data.",
    "이름과 전화번호는 배차 계획기에 넣지 않음. 여기 나오는 모든 예시는 합성 데이터.")],
];
priv.forEach(([h, b], k) => {
  const y = 1.6 + k * 1.75;
  card(s, 5.3, y, 7.4, 1.5, `Data card ${k + 1}`);
  dot(s, 5.55, y + 0.25, k + 1, `Data card ${k + 1} marker`, C.accent1);
  text(s, h, { x: 6.3, y: y + 0.2, w: 6.2, h: 0.42, fontSize: 18, bold: true, color: C.text2, objectName: `Data card ${k + 1} heading` });
  text(s, b, { x: 6.3, y: y + 0.62, w: 6.2, h: 0.8, fontSize: 15, objectName: `Data card ${k + 1} text` });
});
notes(s, KO
  ? ["작업 97건, 배송지 6,395곳, 84일", "비공개 지도 서버: 주소가 밖으로 나가지 않음", "모든 예시는 합성 데이터"]
  : ["97 jobs, 6,395 stops, 84 days", "Private map server: no address leaves", "Synthetic data in every example"]);

// ---------- 6. approach ----------
pres.addSection({ title: SEC.meth });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("AI narrows the search, the optimizer decides", "AI가 탐색 범위를 좁히고, 최적화기가 결정"));
const steps = [
  [L("Road km", "도로 km"), L("Distances and times on real roads, private server", "실제 도로의 거리와 시간, 비공개 서버"), null],
  [L("GNN short list", "GNN 후보 목록"), L("8 likely truck partners per stop", "배송지당 유력 파트너 8곳"), "ai"],
  [L("Candidate loads", "후보 묶음"), L("Every group of 1 to 5 that obeys the rules", "규칙을 지키는 1~5곳 묶음 전부"), null],
  [L("Exact selection", "정확 선택"), L("Fewest trucks, then fewest km", "트럭 최소, 다음으로 km 최소"), "opt"],
  [L("Check", "규칙 검사"), L("Every truck against every rule", "모든 트럭을 모든 규칙으로 확인"), null],
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
text(s, L("AI for speed", "속도는 AI가"), { x: 0.9, y: 4.6, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.accent1, objectName: "AI role heading" });
text(s, L("The GNN cuts the candidate loads about 7 times and the solve time about 10 times. It only ranks; it never decides.",
  "GNN이 후보 묶음을 약 1/7로, 풀이 시간을 약 1/10로 줄임. 순위만 매길 뿐 결정하지 않음."), { x: 0.9, y: 5.1, w: 5.3, h: 1.3, fontSize: 16, objectName: "AI role text" });
card(s, 6.8, 4.4, 5.9, 2.2, "Optimizer role card", C.accent5);
text(s, L("Optimizer for quality", "품질은 최적화기가"), { x: 7.1, y: 4.6, w: 5.3, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Optimizer role heading" });
text(s, L("A mixed-integer program weighs all loads at once and guarantees every rule; on a public benchmark it matches the proven optimum on 4 of 5 instances.",
  "혼합정수계획 모형이 모든 묶음을 한꺼번에 비교하고 모든 규칙을 보장. 공개 벤치마크 인스턴스 5개 중 4개에서 증명된 최적해와 일치."), { x: 7.1, y: 5.1, w: 5.3, h: 1.3, fontSize: 16, objectName: "Optimizer role text" });
notes(s, KO
  ? ["배차 작업마다 5단계", "파란색 = AI(속도), 남색 = 최적화기(품질)", "안전망: 단순한 탐욕 계획이 있어 항상 유효한 답이 나옴"]
  : ["Five steps per dispatch job", "Blue = AI (speed), navy = optimizer (quality)", "Safety net: a simple greedy plan, so there is always a valid answer"]);

// ---------- 7. GNN ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("GNN: 8 likely partners per stop", "GNN: 배송지당 유력 파트너 8곳"));
// the GNN as a flow of five boxes; the middle one (message passing) is the network itself
const gnnFlow = [
  [L("Job graph", "작업 그래프"), L("stops as nodes,\n12 nearest linked", "배송지 = 노드,\n최근접 12곳 연결")],
  [L("Features", "특징"), L("8 per stop,\n4 per pair", "배송지당 8개,\n쌍당 4개")],
  [L("4 rounds of\nmessage passing", "메시지 전달\n4회"), null],
  [L("Pair score", "쌍 점수"), L("chance two stops\nshare a truck", "두 배송지가 같은\n트럭에 탈 확률")],
  [L("Short list", "후보 목록"), L("each stop's\n8 best partners", "배송지별 상위\n파트너 8곳")],
];
gnnFlow.forEach(([h, b], k) => {
  const w = 2.132, x = 0.6 + k * (w + 0.36), y = 1.6, hh = 2.15;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: hh, rectRadius: 0.15, fill: { color: b ? C.background2 : C.accent5 }, line: { color: b ? "B9C8DE" : HEX.dk2, width: b ? 1.25 : 2 }, objectName: `GNN step ${k + 1} box` });
  if (b) {
    text(s, h, { x: x + 0.2, y: y + 0.3, w: w - 0.3, h: 0.5, fontSize: 19, bold: true, color: C.text2, objectName: `GNN step ${k + 1} heading` });
    text(s, b, { x: x + 0.2, y: y + 1.0, w: w - 0.3, h: 0.85, fontSize: 15, lineSpacingMultiple: 1.1, objectName: `GNN step ${k + 1} text` });
  } else {
    text(s, h, { x: x + 0.1, y, w: w - 0.2, h: hh, fontSize: 18, bold: true, color: C.text2, align: "center", valign: "middle", objectName: `GNN step ${k + 1} heading` });
  }
  if (k < 4) seg(s, x + w + 0.06, y + hh / 2, x + w + 0.3, y + hh / 2, { color: HEX.dk2, width: 1.5, endArrowType: "triangle" }, `GNN arrow ${k + 1}`);
});
const gnnCards = [
  [L("The graph", "그래프"), L("Stops are nodes; each is linked to its 12 nearest stops. 8 stop features, 4 link features.", "배송지가 노드, 각 배송지는 가장 가까운 12곳과 연결. 배송지 특징 8개, 연결 특징 4개.")],
  [L("The network", "신경망"), L(`4 rounds of message passing, ${fmt(N.gnn.params)} parameters, trained on the optimizer's own plans.`, `메시지 전달 4회, 파라미터 ${fmt(N.gnn.params)}개, 최적화기 자체의 계획으로 학습.`)],
  [L("The result", "결과"), L(`Candidate loads per job: ${fmt(N.gnn.cols[0])} → ${fmt(N.gnn.cols[1])}. Ranking quality AUC ${N.gnn.auc.toFixed(2)} on unseen jobs.`,
    `작업당 후보 묶음: ${fmt(N.gnn.cols[0])} → ${fmt(N.gnn.cols[1])}. 처음 보는 작업에서 순위 품질 AUC ${N.gnn.auc.toFixed(2)}.`)],
];
gnnCards.forEach(([h, b], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 4.35, 3.85, 2.3, `GNN card ${k + 1}`);
  text(s, h, { x: x + 0.3, y: 4.55, w: 3.3, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: `GNN card ${k + 1} heading` });
  text(s, b, { x: x + 0.3, y: 5.05, w: 3.3, h: 1.5, fontSize: 15, objectName: `GNN card ${k + 1} text` });
});
notes(s, KO
  ? ["GNN 점수: 두 배송지가 같은 트럭에 탈까?", "상위 파트너 8곳만 유지: 후보 1/7", "최적화기 계획으로 학습, 학습에 쓰지 않은 폴드로 평가"]
  : ["GNN scores: will two stops share a truck?", "Keeps top 8 partners: 7x fewer candidates", "Trained on optimizer plans; evaluated out of fold"]);

// ---------- 8. exact selection and rule check ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("Exact selection, then a rule check", "정확 선택 후 규칙 검사"));
const sel = [
  [L("Stage A", "단계 A"), L("Choose loads so that every stop is served exactly once, with at most ten 1.4-ton trucks: the fewest trucks.",
    "모든 배송지를 정확히 한 번 방문하고 1.4톤 트럭은 최대 10대가 되도록 묶음 선택: 트럭 최소.")],
  [L("Stage B", "단계 B"), L("Among plans with that many trucks, the fewest road km. Each load's km is its best stop order, so grouping and routing are decided together.",
    "그 트럭 수의 계획 가운데 도로 km 최소. 묶음마다 최적 방문 순서의 km를 쓰므로 묶음 구성과 경로가 함께 결정됨.")],
  [L("Check", "규칙 검사"), L("Every truck is checked against every rule before the plan is accepted; a failure stops the run.",
    "계획 채택 전 모든 트럭을 모든 규칙으로 검사, 하나라도 어기면 실행 중단.")],
];
sel.forEach(([h, b], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 1.55, 3.85, 2.45, `Selection ${k + 1} card`);
  dot(s, x + 0.25, 1.75, ["A", "B", "C"][k], `Selection ${k + 1} marker`);
  text(s, h, { x: x + 0.9, y: 1.78, w: 2.75, h: 0.45, fontSize: 19, bold: true, color: C.text2, objectName: `Selection ${k + 1} heading` });
  text(s, b, { x: x + 0.25, y: 2.4, w: 3.4, h: 1.5, fontSize: 15, objectName: `Selection ${k + 1} text` });
});
card(s, 0.6, 4.3, 7.95, 2.3, "Why exact card", C.accent5);
text(s, L("Why exact, not greedy", "탐욕이 아닌 정확 최적화를 쓰는 이유"), { x: 0.9, y: 4.5, w: 7.35, h: 0.45, fontSize: 20, bold: true, color: C.text2, objectName: "Why exact heading" });
text(s, L("A greedy rule fills one truck at a time and cannot undo a choice, so the last stops end up in half-empty trucks. The optimizer weighs every candidate load at once, and its constraints guarantee every rule by construction.",
  "탐욕 규칙은 트럭을 한 대씩 채우고 선택을 되돌릴 수 없어, 마지막 배송지들이 반쯤 빈 트럭에 남음. 최적화기는 모든 후보 묶음을 한꺼번에 비교하며, 제약 조건 자체가 모든 규칙을 보장."),
  { x: 0.9, y: 5.0, w: 7.35, h: 1.5, fontSize: 16, objectName: "Why exact text" });
card(s, 8.85, 4.3, 3.85, 2.3, "Time limit card");
stat(s, 9.15, 4.4, 3.3, L("60 s", "60초"), L("per stage at most; a simple greedy plan is the safety net", "단계마다 최대 시간, 단순한 탐욕 계획이 안전망"), "Time limit", C.text2);
notes(s, KO
  ? ["단계 A 트럭, 단계 B km: 묶음 구성과 경로를 함께", "모든 트럭에 규칙 검사", "정확 최적화인 이유: 탐욕은 선택을 되돌릴 수 없음"]
  : ["Stage A trucks, stage B km: grouping and routing together", "Rule check on every truck", "Why exact: greedy cannot undo a choice"]);

// ---------- 9. worked example ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.meth });
title(s, L("A worked example: 26 stops, 6 trucks", "예시: 배송지 26곳, 트럭 6대"));
const ex = N.example;
// three panels drawn from synthetic_job.json: stops (dot area = volume), each stop's 4 nearest (as in make_figs.py), the plan
const P = Object.fromEntries(J.stops.map((p) => [p.stop, p]));
const km2 = (a, b) => (a.x_km - b.x_km) ** 2 + (a.y_km - b.y_km) ** 2;
const near = J.stops.map((p) => J.stops.filter((q) => q !== p).sort((a, b) => km2(p, a) - km2(p, b)).slice(0, 4));
const exPanels = [L("(a) Stops and depot", "(a) 배송지와 물류센터"), L("(b) Short list of partners", "(b) 파트너 후보 목록"), L(`(c) Optimal plan: ${J.plan.length} trucks`, `(c) 최적 계획: 트럭 ${J.plan.length}대`)];
const exNote = [L("dot size = volume", "점 크기 = 부피"), null, L("dashed = drive from depot", "점선 = 물류센터에서 출발")];
exPanels.forEach((t_, k) => {
  const fx = 0.6 + k * 4.13, fy = 1.9, fw = 3.84, fh = 3.3;
  text(s, t_, { x: fx, y: 1.42, w: fw, h: 0.42, fontSize: 18, bold: true, valign: "bottom", objectName: `Example panel ${k + 1} title` });
  s.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy, w: fw, h: fh, fill: { color: C.background1 }, line: { color: "E3E8EF", width: 1 }, objectName: `Example panel ${k + 1} frame` });
  const sc = Math.min(fw / 172, fh / 152); // same scale on both axes; view x -12..160 km, y -12..140 km
  const X = (km) => fx + (fw - 172 * sc) / 2 + (km + 12) * sc, Y = (km) => fy + (fh - 152 * sc) / 2 + (140 - km) * sc;
  if (exNote[k]) text(s, exNote[k], { x: X(0), y: Y(128) - 0.15, w: 3.0, h: 0.3, fontSize: 12, color: C.accent4, objectName: `Example panel ${k + 1} note` });
  if (k === 1) {
    const done = new Set();
    J.stops.forEach((p, i) => near[i].forEach((q) => {
      const id = [p.stop, q.stop].sort().join("-");
      if (done.has(id)) return;
      done.add(id);
      seg(s, X(p.x_km), Y(p.y_km), X(q.x_km), Y(q.y_km), { color: HEX.accent1, width: 1, transparency: 55 }, `Short list ${id}`);
    }));
  }
  if (k === 2) J.plan.forEach((route, t) => {
    const a = P[route[0]];
    seg(s, X(J.depot[0]), Y(J.depot[1]), X(a.x_km), Y(a.y_km), { color: HEX.accent3, width: 1, dashType: "sysDash" }, `Truck ${t + 1} drive from depot`);
    route.slice(1).forEach((id, i) => {
      const p = P[route[i]], q = P[id];
      seg(s, X(p.x_km), Y(p.y_km), X(q.x_km), Y(q.y_km), { color: HEX.accent1, width: 2.25 }, `Truck ${t + 1} leg ${i + 1}`);
    });
  });
  J.stops.forEach((p) => disc(s, X(p.x_km), Y(p.y_km), 0.0263 * Math.sqrt(14 + 22 * p.volume_m3), k ? HEX.accent1 : "7FA6E8", `Example panel ${k + 1} stop ${p.stop}`, { color: "FFFFFF", width: 0.75 }));
  s.addShape(pres.shapes.STAR_5_POINT, { x: X(J.depot[0]) - 0.14, y: Y(J.depot[1]) - 0.14, w: 0.28, h: 0.28, fill: { color: C.accent2 }, line: { color: "FFFFFF", width: 0.5 }, objectName: `Example panel ${k + 1} depot` });
});
const exCards = [
  [fmt(ex.candidates), L("candidate loads from each stop's 8 nearest partners", "배송지별 최근접 파트너 8곳으로 만든 후보 묶음")],
  [L(`${ex.trucks} trucks, ${fmt(ex.km)} km`, `트럭 ${ex.trucks}대, ${fmt(ex.km)} km`), L("the optimizer's plan, every rule met", "최적화기의 계획, 모든 규칙 충족")],
  [L("6 is the minimum", "6대가 최소"), L(`${ex.volume} m³ needs at least 6 trucks of 4.73 m³`, `${ex.volume} m³에는 4.73 m³ 트럭이 최소 6대 필요`)],
];
exCards.forEach(([big, label], k) => {
  const x = 0.6 + k * 4.1;
  card(s, x, 5.3, 3.85, 1.35, `Example card ${k + 1}`);
  text(s, big, { x: x + 0.3, y: 5.38, w: 3.3, h: 0.55, fontSize: L(24, 22), bold: true, color: k === 1 ? C.accent1 : C.text2, valign: "bottom", objectName: `Example card ${k + 1} number` });
  text(s, label, { x: x + 0.3, y: 5.95, w: 3.3, h: 0.6, fontSize: 14, color: C.accent4, objectName: `Example card ${k + 1} label` });
});
notes(s, KO
  ? ["합성 데이터, 실제 코드", "후보 목록 다음에 정확 선택", "트럭 6대: 부피로 보아 가능한 최소"]
  : ["Synthetic data, real code", "Short list, then exact choice", "6 trucks: the fewest possible by volume"]);

// ---------- 10. results, as the prototype's results page shows them ----------
pres.addSection({ title: SEC.res });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L(`${fmt(T("real") - T("gnn_opt"))} fewer trucks, 21 % fewer road km`, `트럭 ${fmt(T("real") - T("gnn_opt"))}대, 도로 km 21% 절감`));
// figures drawn for the slides in the prototype's look (competition/webfigs: render.mjs -> figs/slides/ and figs/ko/)
const webPic = (slide, name, x, y, w, h, alt) => {
  const f = img(name), z = pngSize(f);
  let pw = w, ph = (w * z.h) / z.w; if (ph > h) { ph = h; pw = (h * z.w) / z.h; }
  slide.addImage({ path: f, x: x + (w - pw) / 2, y, w: pw, h: ph, altText: alt, objectName: "Picture " + name });
  return { x: x + (w - pw) / 2, y, w: pw, h: ph };
};
const r10 = webPic(s, "slide_results", 0.6, 1.35, 12.1, 5.05, L("The prototype's results page: 584 fewer trucks (−23.2 %), −21.2 % road km, 0 rule breaks; trucks and road km for every method",
  "프로토타입 결과 화면: 트럭 584대 감소(−23.2%), 도로 km −21.2%, 규칙 위반 0; 방법별 트럭 수와 도로 km"));
text(s, L("All 97 jobs, the same roads and rules for every method; the prototype shows the same numbers.", "작업 97건 전체, 모든 방법에 같은 도로와 같은 규칙. 프로토타입도 같은 수치를 보여 줌."),
  { x: 0.6, y: r10.y + r10.h + 0.08, w: 12.1, h: 0.35, fontSize: 12, color: C.accent4, align: "center", objectName: "Results source" });
notes(s, KO
  ? ["프로토타입 결과 화면 그대로: 작업 97건 전체", "최적화기 세 행이 트럭 수에서 다른 모든 방법보다 우수", "트럭과 함께 총 도로 km도 감소: −21%", "실제 배차는 데이터에 없는 사항도 처리함"]
  : ["Straight from the prototype's results page: all 97 jobs", "The three optimizer rows beat every other method on trucks", "Total road km falls with the trucks: −21 %", "Real dispatch also handles things not in our data"]);

// ---------- 11. analysis ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L("What the results show", "결과 분석"));
const rj = webPic(s, "slide_perjob", 0.6, 1.3, 12.1, 2.85, L(`Trucks saved per job against the real dispatch, one column per job in date order: fewer trucks on ${N.perjob.fewer} of 97 jobs`,
  `작업별 트럭 절감(실제 배차 대비), 날짜 순 작업당 막대 하나: 97건 중 ${N.perjob.fewer}건에서 트럭 감소`));
const finds = [
  [L("The optimizer saves the trucks", "트럭을 줄이는 것은 최적화기"), L(`Every optimizer plan beats every other method by at least 294 trucks; fewer trucks on ${N.perjob.fewer} of 97 jobs.`, `모든 최적화기 계획이 다른 방법보다 트럭이 294대 이상 적고, 97건 중 ${N.perjob.fewer}건에서 절감.`)],
  [L("The GNN buys speed", "GNN은 속도를 냄"), L(`7× fewer candidate loads, 10× faster (${N.gnn.s[1]} s vs ${N.gnn.s[0]} s) for 0.7 % more trucks; at the same list size it beats the 8 nearest by 8 trucks.`,
    `후보 묶음 1/7, 10배 빠름(${N.gnn.s[1]}초 vs ${N.gnn.s[0]}초), 트럭은 0.7% 증가. 같은 목록 크기에서는 최근접 8곳보다 8대 적음.`)],
  [L("Rules belong inside the model", "규칙은 모델 안에"), L("OR-Tools cannot express the 50 km radius: 2,264 trucks after splitting routes on 89 of 97 jobs.", "OR-Tools는 50 km 반경을 표현하지 못해, 97건 중 89건에서 경로를 쪼갠 뒤 2,264대.")],
  [L("Bigger jobs save more", "큰 작업일수록 더 절감"), L(`Above 63 stops: −${N.bysize.big_pct} %, below: −${N.bysize.small_pct} %. Where the real dispatch keeps every rule (13 jobs): still −28.2 %.`,
    `63곳 초과 작업 −${N.bysize.big_pct}%, 이하 −${N.bysize.small_pct}%. 실제 배차가 규칙을 모두 지킨 13건에서도 −28.2%.`)],
];
finds.forEach(([h, b], k) => {
  const x = 0.6 + k * 3.075, y = rj.y + rj.h + 0.2;
  card(s, x, y, 2.9, 6.75 - y, `Finding ${k + 1} card`);
  dot(s, x + 0.2, y + 0.18, k + 1, `Finding ${k + 1} marker`, C.accent1);
  text(s, h, { x: x + 0.82, y: y + 0.14, w: 1.95, h: 0.6, fontSize: L(14, 13), bold: true, color: C.text2, valign: "middle", objectName: `Finding ${k + 1} heading` });
  text(s, b, { x: x + 0.2, y: y + 0.82, w: 2.55, h: 6.65 - y - 0.82, fontSize: L(12.5, 12), color: C.text1, objectName: `Finding ${k + 1} text` });
});
notes(s, KO
  ? ["작업별 절감: 97건 중 93건", "1 최적화기가 트럭을 줄임", "2 GNN은 속도: 10배 빠르고 트럭은 0.7%만 증가", "3 OR-Tools는 반경 규칙을 표현 못 함", "4 큰 작업일수록 절감이 크고, 규칙 위반 때문이 아님"]
  : ["Per job: fewer trucks on 93 of 97", "1 The optimizer saves the trucks", "2 The GNN buys speed: 10x faster for 0.7 % more trucks", "3 OR-Tools cannot express the radius rule", "4 Bigger jobs save more; not from rule breaks"]);

// ---------- 12. accuracy ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.res });
title(s, L("Accurate on a public benchmark", "공개 벤치마크에서 확인한 정확도"));
const hdr = (t_) => ({ text: t_, options: Object.assign({ bold: true, color: C.text2, fill: { color: C.background2 } }, LANG) });
const bt = [[L("Instance", "인스턴스"), L("Customers", "고객 수"), L("Proven optimum", "증명된 최적해"), L("Our distance", "본 연구 거리"), L("Gap", "격차")].map(hdr)].concat(
  N.bench.map((r) => [r.name, String(r.customers), fmt(r.optimum), fmt(r.cost), pc(r.gap.toFixed(1))]));
s.addTable(bt, Object.assign({ x: 0.6, y: 1.55, w: 7.4, colW: [1.7, 1.3, 1.6, 1.6, 1.2], fontSize: 15, color: C.text1, border: { type: "solid", pt: 0.5, color: HEX.accent5 }, rowH: 0.48, objectName: "Benchmark table" }, LANG));
text(s, L("CVRPLIB set P (Augerat et al., 1995): the five instances whose proven optimal routes visit at most 5 customers, like the 5-address rule. Same code, 15 nearest partners.",
  "CVRPLIB 세트 P(Augerat 외, 1995): 증명된 최적 경로가 고객을 최대 5곳만 방문하는 인스턴스 5개(주소 5곳 규칙과 같은 조건). 같은 코드, 최근접 파트너 15곳."),
  { x: 0.6, y: 4.65, w: 7.4, h: 0.85, fontSize: 12, color: C.accent4, objectName: "Benchmark note" });
stat(s, 8.5, 1.55, 4.2, L("4 of 5", "5개 중 4개"), L("instances solved to the proven optimum", "인스턴스에서 증명된 최적해 도달"), "Benchmark optimal", C.accent1);
stat(s, 8.5, 3.3, 4.2, pc("0.06"), L("average gap to the proven optimum", "증명된 최적해 대비 평균 최적성 격차"), "Benchmark gap", C.text2);
card(s, 0.6, 5.6, 12.1, 1.05, "GNN accuracy card", C.accent5);
text(s, [
  { text: L("The GNN on unseen jobs: AUC 0.74. ", "처음 보는 작업에서 GNN의 AUC 0.74. "), options: { bold: true, color: C.text2 } },
  { text: L("Its accuracy is 81.8 %, but the default accuracy (always \"different truck\") is already 81.3 %, so we judge it by its ranking.",
    "정확도는 81.8%이지만 기본 정확도(항상 \"다른 트럭\"이라고 답할 때)가 이미 81.3%이므로 순위 품질로 평가.") },
], { x: 0.9, y: 5.7, w: 11.5, h: 0.85, fontSize: 15, valign: "middle", objectName: "GNN accuracy text" });
notes(s, KO
  ? ["정확도 = 공개 벤치마크에서 증명된 최적해와의 격차", "5개 중 4개 최적, 평균 0.06%, 누구나 다시 실행 가능", "GNN: 기본 정확도가 아니라 AUC로 평가"]
  : ["Accuracy = gap to proven optimum on a public benchmark", "4 of 5 optimal, 0.06 % on average, anyone can rerun it", "GNN: judge by AUC, not by default accuracy"]);

// ---------- 13. prototype and demo ----------
pres.addSection({ title: SEC.imp });
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.imp });
title(s, L("A prototype for the daily routine", "일상 업무를 위한 프로토타입"));
// the prototype's own opening screen, framed as a browser window (webfigs/frame.py)
const app = webPic(s, "app_top", 0.6, 1.6, 7.9, 3.9, L("The prototype's opening screen: title and headline numbers (1,933 trucks, −23.2 %, −21.2 % road km, 0 rule breaks)",
  "프로토타입 첫 화면: 제목과 주요 수치(트럭 1,933대, −23.2%, 도로 km −21.2%, 규칙 위반 0)"));
text(s, L("The prototype opens with the headline numbers; below them, a walk through one job, every method, and every job on a map behind a password.",
  "프로토타입 첫 화면의 주요 수치. 그 아래에 작업 하나의 진행 과정, 모든 방법 비교, 그리고 비밀번호로 보호된 지도에서 모든 작업을 보여 줌."),
  { x: 0.6, y: app.y + app.h + 0.15, w: 7.9, h: 0.75, fontSize: 13, color: C.accent4, objectName: "Prototype caption" });
const flow = [[L("Order export", "주문 내보내기 파일"), L("today's spreadsheet", "현재 쓰는 스프레드시트")], [L("Planner", "배차 계획기"), L("on the company PC, seconds per job", "회사 PC에서 작업당 수 초")],
  [L("Plan sheet and map", "배차표와 지도"), L("stops in order, truck size, km, hours", "방문 순서, 트럭 크기, km, 시간")], [L("Dispatcher", "배차 담당자"), L("reviews, edits, books trucks", "검토, 수정, 트럭 예약")]];
flow.forEach(([h, b], k) => {
  const y = 1.5 + k * 1.02;
  card(s, 8.95, y, 3.75, 0.8, `Flow ${k + 1}`, k === 1 ? C.accent5 : C.background2);
  text(s, [{ text: h, options: { bold: true, color: C.text2, breakLine: true } }, { text: b, options: { fontSize: 13, color: C.accent4 } }], { x: 9.2, y: y + 0.08, w: 3.35, h: 0.66, fontSize: 16, valign: "middle", objectName: `Flow ${k + 1} text` });
  if (k < 3) arrow(s, 10.82, y + 0.8, 10.82, y + 1.02, `Flow arrow ${k + 1}`);
});
card(s, 8.95, 5.75, 3.75, 0.85, "Demo cue", C.accent1);
text(s, L("Live demo: switch to the prototype", "실시간 시연: 프로토타입으로 전환"), { x: 9.15, y: 5.75, w: 3.35, h: 0.85, fontSize: 17, bold: true, color: C.background1, align: "center", valign: "middle", objectName: "Demo cue text" });
notes(s, KO
  ? ["기존 업무에 맞춤: 내보내기 파일이 들어가고 배차표가 나옴", "여기서 실시간 시연: 핵심 수치, 이어서 지도 위 작업 하나", "비밀번호 보호, 외부 서비스 없음"]
  : ["Fits the existing routine: export in, plan sheet out", "LIVE DEMO here: headline numbers, then one job on the map", "Password protected; no external services"]);

// ---------- 14. conclusion and future work ----------
s = pres.addSlide({ masterName: "Closing dark", sectionTitle: SEC.imp });
title(s, L("Conclusion and future work", "결론과 향후 과제"));
const r100 = fmt(Math.round(N.save.real.year.trucks / 100) * 100);
const cols = [
  [L("Conclusion", "결론"), C.accent1, [
    L("23 % fewer trucks, 21 % fewer km and 0 rule breaks on 97 real jobs", "실제 작업 97건에서 트럭 23%, 거리 21% 감소, 규칙 위반 0"),
    L("Optimizer for quality, GNN for speed: seconds per job on one PC", "품질은 최적화기, 속도는 GNN: PC 1대에서 작업당 수 초"),
    L("0.06 % from the proven optimum on a public benchmark", "공개 벤치마크에서 증명된 최적해와 평균 0.06% 차이"),
    L(`Up to ~${r100} fewer trucks a year (main-season upper bound)`, `연간 최대 약 ${r100}대 감소(성수기 기준 상한)`)]],
  [L("Future work", "향후 과제"), C.accent5, [
    L("Shadow-mode pilot, Dec 2026 to Apr 2027: measure the real savings", "섀도 모드 시범 운영(2026년 12월~2027년 4월): 실제 절감량 측정"),
    L("Time windows, driver hours and unloading as new constraints", "시간 창, 기사 근무 시간, 하차 조건을 새 제약으로 추가"),
    L("Optimize the estimated hire cost directly", "추정 용차 비용을 직접 최적화"),
    L("Retrain monthly; test on new dates and larger jobs", "매월 재학습, 새 날짜와 더 큰 작업으로 검증")]],
];
cols.forEach(([h, col, items], c) => {
  const x = 0.8 + c * 6.0;
  text(s, h, { x, y: 1.75, w: 5.4, h: 0.5, fontSize: 22, bold: true, color: col, objectName: `${c ? "Future" : "Conclusion"} heading` });
  items.forEach((it, k) => {
    const y = 2.45 + k * 0.85;
    dot(s, x, y + 0.04, k + 1, `${c ? "Future" : "Conclusion"} ${k + 1} marker`, c ? C.accent4 : C.accent1);
    text(s, it, { x: x + 0.7, y, w: 4.8, h: 0.62, fontSize: 16, color: C.background1, valign: "middle", objectName: `${c ? "Future" : "Conclusion"} ${k + 1} text` });
  });
});
text(s, L("Thank you. Questions?", "감사합니다. 질문을 받겠습니다."), { x: 0.8, y: 6.05, w: 7, h: 0.6, fontSize: 26, bold: true, color: C.background1, objectName: "Thanks" });
text(s, L("Team ANALOG, Changwon National University", "팀 ANALOG, 국립창원대학교"), { x: 7.3, y: 6.2, w: 5.2, h: 0.4, fontSize: 14, color: C.accent5, align: "right", objectName: "Team line" });
notes(s, KO
  ? ["결론: 트럭 23%, 거리 21%, 위반 0, 벤치마크 0.06%", "연간 최대 약 1,700대(상한)", "향후: 섀도 모드 시범 운영, 새 제약, 비용 최적화, 매월 재학습", "질문 받기"]
  : ["Conclusion: −23 % trucks, −21 % km, 0 breaks, 0.06 % benchmark gap", "Up to ~1,700 trucks a year (upper bound)", "Next: shadow-mode pilot, new constraints, cost objective, monthly retraining", "Invite questions"]);

// ---------- 15. references (the newest report's list, read from report.md) ----------
s = pres.addSlide({ masterName: "Content", sectionTitle: SEC.imp });
title(s, L("References", "참고문헌"));
const refMd = fs.readFileSync(path.join(__dirname, "report.md"), "utf8");
const refs = refMd.slice(refMd.indexOf("::: refs")).split("\n").filter((l) => /^\[\d+\]/.test(l)).map((l) => l.replace(/\*/g, "").trim());
if (refs.length < 10) throw new Error(`only ${refs.length} references found in report.md`);
const half = Math.ceil(refs.length / 2);
[refs.slice(0, half), refs.slice(half)].forEach((col, c) => text(s, col.map((r, k) => ({ text: r, options: { breakLine: k < col.length - 1, paraSpaceAfter: 5 } })),
  { x: 0.6 + c * 6.15, y: 1.35, w: 5.95, h: 5.45, fontSize: 10, color: C.text1, lang: "en-US", objectName: `References ${c + 1}` }));
notes(s, KO ? ["보고서와 같은 참고문헌 목록"] : ["Same list as the report"]);

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
