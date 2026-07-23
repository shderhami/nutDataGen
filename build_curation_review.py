#!/usr/bin/env python3
"""Generate a self-contained interactive HTML review page from the merged
curation CSVs so the keep/drop decisions can be eyeballed per category.

Writes the page to the scratchpad path passed as argv[1].
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

D = Path(__file__).parent / "data" / "cv_curation" / "merged"
BRINE = re.compile(r"added solution|pre-basted|enhanced", re.I)

CLASSES = ["muscle", "organ", "fish", "egg", "dairy", "fat_oil", "plant"]


def load() -> list[list]:
    rows: list[list] = []
    for cls in CLASSES:
        f = D / f"{cls}.csv"
        if not f.exists():
            continue
        for r in csv.DictReader(open(f)):
            llm = float(r["llm_score"]); kw = float(r["kw_score"])
            keep = 1 if r["final"] == "KEEP" else 0
            dis = 1 if r["disagree"] == "Y" else 0
            veto = 1 if r["hard_veto"] == "Y" else 0
            brine = 1 if (cls == "muscle" and keep and BRINE.search(r["description"] or "")) else 0
            rows.append([cls, keep, round(llm, 2), round(kw, 2), dis, veto, brine,
                         r["prep"], int(r["n_obs"] or 0), r["source_dataset"],
                         r["source_food_id"], r["description"], r["llm_reason"], r["kw_reasons"]])
    return rows


HTML = r"""<title>CV Curation Review — source-food keep/drop</title>
<style>
:root{
  --bg:#f6f8fa; --surface:#ffffff; --surface2:#f0f3f7; --border:#e0e5ec;
  --text:#1b2230; --muted:#616c7d; --accent:#0d7d8a; --accent-weak:#d7eef0;
  --keep:#1c7c54; --keep-bg:#e6f4ec; --drop:#b23a48; --drop-bg:#f9e9eb;
  --amber:#9d6a12; --amber-bg:#f7efdd; --violet:#6a49ad; --violet-bg:#efe9f8;
  --shadow:0 1px 2px rgba(20,28,45,.06),0 4px 16px rgba(20,28,45,.05);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0e131a; --surface:#161d27; --surface2:#1c2531; --border:#28323f;
  --text:#e6ecf3; --muted:#93a0b2; --accent:#3cc4d2; --accent-weak:#123840;
  --keep:#54cf8c; --keep-bg:#12301f; --drop:#f0808f; --drop-bg:#361a1e;
  --amber:#e0aa4d; --amber-bg:#33270f; --violet:#b399ec; --violet-bg:#221a37;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.28);
}}
:root[data-theme="light"]{
  --bg:#f6f8fa; --surface:#ffffff; --surface2:#f0f3f7; --border:#e0e5ec;
  --text:#1b2230; --muted:#616c7d; --accent:#0d7d8a; --accent-weak:#d7eef0;
  --keep:#1c7c54; --keep-bg:#e6f4ec; --drop:#b23a48; --drop-bg:#f9e9eb;
  --amber:#9d6a12; --amber-bg:#f7efdd; --violet:#6a49ad; --violet-bg:#efe9f8;
}
:root[data-theme="dark"]{
  --bg:#0e131a; --surface:#161d27; --surface2:#1c2531; --border:#28323f;
  --text:#e6ecf3; --muted:#93a0b2; --accent:#3cc4d2; --accent-weak:#123840;
  --keep:#54cf8c; --keep-bg:#12301f; --drop:#f0808f; --drop-bg:#361a1e;
  --amber:#e0aa4d; --amber-bg:#33270f; --violet:#b399ec; --violet-bg:#221a37;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1280px;margin:0 auto;padding:24px 20px 80px}
header h1{font-size:22px;font-weight:650;letter-spacing:-.01em;margin:0 0 4px}
header p{margin:0;color:var(--muted);max-width:70ch}
.eyebrow{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:650;margin:0 0 8px}

/* summary cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:22px 0 8px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 13px;box-shadow:var(--shadow);cursor:pointer;transition:border-color .12s,transform .08s}
.card:hover{border-color:var(--accent)}
.card.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent),var(--shadow)}
.card .name{font-size:12px;font-weight:650;letter-spacing:.02em;text-transform:capitalize}
.card .big{font-size:21px;font-weight:680;margin-top:2px}
.card .sub{font-size:11px;color:var(--muted)}
.bar{height:5px;border-radius:3px;background:var(--drop);margin-top:9px;overflow:hidden;display:flex}
.bar>i{background:var(--keep);height:100%;display:block}

/* controls */
.controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:14px 0 10px;margin-top:10px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pill{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:999px;padding:5px 12px;font-size:12.5px;cursor:pointer;font-weight:550;display:inline-flex;gap:6px;align-items:center}
.pill.on{background:var(--accent);border-color:var(--accent);color:#fff}
:root[data-theme="dark"] .pill.on,@media (prefers-color-scheme:dark){.pill.on{color:#04222a}}
.pill .n{font-size:11px;opacity:.7}
.pill.on .n{opacity:.85}
input[type=search]{flex:1;min-width:180px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:7px 11px;color:var(--text);font-size:13px}
input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px}
.count{color:var(--muted);font-size:12.5px;margin-left:auto;white-space:nowrap}

/* table */
.tblwrap{overflow-x:auto;margin-top:6px;border:1px solid var(--border);border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:var(--surface2);text-align:left;padding:8px 10px;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:650;border-bottom:1px solid var(--border);cursor:pointer;white-space:nowrap;user-select:none}
thead th:hover{color:var(--accent)}
tbody td{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}
tbody tr:hover{background:var(--surface2)}
tbody tr.drop td:nth-child(3){opacity:.85}
td.desc{min-width:280px;max-width:420px}
td.reason{color:var(--muted);min-width:150px;max-width:260px;font-size:12px}
.tag{display:inline-block;font-size:10.5px;font-weight:650;padding:1px 6px;border-radius:5px;letter-spacing:.02em;white-space:nowrap}
.t-keep{color:var(--keep);background:var(--keep-bg)}
.t-drop{color:var(--drop);background:var(--drop-bg)}
.t-dis{color:var(--amber);background:var(--amber-bg)}
.t-bor{color:var(--violet);background:var(--violet-bg)}
.t-brine{color:var(--drop);background:var(--drop-bg)}
.t-veto{color:var(--drop);background:var(--drop-bg)}
.sc{font-weight:640}
.sc.hi{color:var(--keep)} .sc.lo{color:var(--drop)} .sc.mid{color:var(--amber)}
.ds{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.empty{padding:40px;text-align:center;color:var(--muted)}
.legend{font-size:11.5px;color:var(--muted);margin-top:12px;display:flex;flex-wrap:wrap;gap:14px}
.legend span{display:inline-flex;gap:5px;align-items:center}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">Nutrient-CV pipeline · data curation QA</p>
  <h1>Source-food keep / drop review</h1>
  <p>Every distinct USDA source food assigned to an ingredient class, scored by two independent judges — a
  transparent keyword rule and an LLM semantic second opinion. <b>Shipped decision = LLM keeps (≥0.50) AND no
  keyword hard-veto</b> (brand / fast-food / processed-meat / imitation / wrong-class). Only KEPT foods feed the
  category CV pools. Click a category to filter; use the quick filters to jump to the foods worth scrutinising.</p>
</header>

<div class="cards" id="cards"></div>

<div class="controls">
  <span class="pill" data-q="disagree">Disagreements <span class="n" id="n-dis"></span></span>
  <span class="pill" data-q="borderline">Borderline keeps <span class="n" id="n-bor"></span></span>
  <span class="pill" data-q="brine">Brine-injected <span class="n" id="n-bri"></span></span>
  <span class="pill" data-q="drop">Drops only <span class="n" id="n-drp"></span></span>
  <input type="search" id="q" placeholder="Search description / reason…">
  <span class="count" id="count"></span>
</div>

<div class="tblwrap">
<table>
<thead><tr>
  <th data-k="1">Verdict</th><th data-k="2">LLM</th><th data-k="3">KW</th>
  <th data-k="7">Prep</th><th data-k="8">n</th><th data-k="9">Src</th>
  <th data-k="11">Description</th><th data-k="12">LLM reason</th><th data-k="13">Keyword flags</th>
</tr></thead>
<tbody id="tb"></tbody>
</table>
</div>
<div class="empty" id="empty" hidden>No foods match these filters.</div>

<div class="legend">
  <span><span class="tag t-keep">KEEP</span> enters CV pool</span>
  <span><span class="tag t-drop">DROP</span> excluded</span>
  <span><span class="tag t-dis">disagree</span> keyword vs LLM differ</span>
  <span><span class="tag t-bor">borderline</span> LLM 0.40–0.65 &amp; kept</span>
  <span><span class="tag t-brine">brine</span> added-solution poultry</span>
</div>
</div>

<script>
const COLS=["cls","keep","llm","kw","dis","veto","brine","prep","n","ds","sid","desc","lr","kr"];
const DATA=__DATA__.map(r=>{const o={};COLS.forEach((c,i)=>o[c]=r[i]);return o;});
const CLASSES=["muscle","organ","fish","egg","dairy","fat_oil","plant"];
let cat="all", quick=null, sortK=null, sortDir=1;
const $=s=>document.querySelector(s);

// summary cards
function cardHTML(name,rows){
  const keep=rows.filter(r=>r.keep).length,drop=rows.length-keep;
  const pct=rows.length?Math.round(100*keep/rows.length):0;
  return `<div class="card" data-cat="${name}">
    <div class="name">${name.replace('_',' ')}</div>
    <div class="big mono">${keep}<span class="sub"> / ${rows.length} kept</span></div>
    <div class="sub">${drop} dropped · ${pct}% keep</div>
    <div class="bar"><i style="width:${pct}%"></i></div></div>`;
}
function buildCards(){
  const c=$("#cards");
  c.innerHTML=cardHTML("all",DATA)+CLASSES.map(k=>cardHTML(k,DATA.filter(r=>r.cls===k))).join("");
  c.querySelectorAll(".card").forEach(el=>el.onclick=()=>{cat=el.dataset.cat;render();});
  $("#n-dis").textContent=DATA.filter(r=>r.dis).length;
  $("#n-bor").textContent=DATA.filter(r=>r.keep&&r.llm>=0.40&&r.llm<=0.65).length;
  $("#n-bri").textContent=DATA.filter(r=>r.brine).length;
  $("#n-drp").textContent=DATA.filter(r=>!r.keep).length;
}
function scCls(v){return v>=0.6?"hi":(v>=0.4?"mid":"lo");}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function rowHTML(r){
  const tags=[`<span class="tag ${r.keep?'t-keep':'t-drop'}">${r.keep?'KEEP':'DROP'}</span>`];
  if(r.dis)tags.push('<span class="tag t-dis">≠</span>');
  if(r.brine)tags.push('<span class="tag t-brine">brine</span>');
  else if(r.keep&&r.llm>=0.40&&r.llm<=0.65)tags.push('<span class="tag t-bor">border</span>');
  if(r.veto)tags.push('<span class="tag t-veto">veto</span>');
  return `<tr class="${r.keep?'keep':'drop'}">
    <td>${tags.join(' ')}</td>
    <td class="mono sc ${scCls(r.llm)}">${r.llm.toFixed(2)}</td>
    <td class="mono sc ${scCls(r.kw)}">${r.kw.toFixed(2)}</td>
    <td>${r.prep}</td><td class="mono">${r.n}</td>
    <td class="ds">${r.ds==='sr28'?'SR28':(r.ds==='sr_legacy'?'SRL':'FDN')}</td>
    <td class="desc">${esc(r.desc)}</td>
    <td class="reason">${esc(r.lr)}</td>
    <td class="reason">${esc(r.kr)}</td></tr>`;
}
function filtered(){
  let rows=cat==="all"?DATA.slice():DATA.filter(r=>r.cls===cat);
  if(quick==="disagree")rows=rows.filter(r=>r.dis);
  else if(quick==="borderline")rows=rows.filter(r=>r.keep&&r.llm>=0.40&&r.llm<=0.65);
  else if(quick==="brine")rows=rows.filter(r=>r.brine);
  else if(quick==="drop")rows=rows.filter(r=>!r.keep);
  const q=$("#q").value.trim().toLowerCase();
  if(q)rows=rows.filter(r=>(r.desc+' '+r.lr+' '+r.kr).toLowerCase().includes(q));
  if(sortK){const k=COLS[sortK];rows.sort((a,b)=>{let x=a[k],y=b[k];
    if(typeof x==="string"){x=x.toLowerCase();y=y.toLowerCase();}
    return x<y?-1*sortDir:x>y?sortDir:0;});}
  else rows.sort((a,b)=>a.llm-b.llm);
  return rows;
}
function render(){
  document.querySelectorAll(".card").forEach(el=>el.classList.toggle("active",el.dataset.cat===cat));
  document.querySelectorAll(".controls .pill").forEach(el=>el.classList.toggle("on",el.dataset.q===quick));
  const rows=filtered();
  $("#tb").innerHTML=rows.map(rowHTML).join("");
  $("#empty").hidden=rows.length>0;
  const keep=rows.filter(r=>r.keep).length;
  $("#count").textContent=`${rows.length} shown · ${keep} keep · ${rows.length-keep} drop`;
}
buildCards();
document.querySelectorAll(".controls .pill").forEach(el=>el.onclick=()=>{quick=quick===el.dataset.q?null:el.dataset.q;render();});
document.querySelectorAll("thead th").forEach(th=>th.onclick=()=>{const k=+th.dataset.k;if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=1;}render();});
$("#q").oninput=render;
render();
</script>
"""


def main() -> None:
    out = Path(sys.argv[1])
    rows = load()
    html = HTML.replace("__DATA__", json.dumps(rows, separators=(",", ":")))
    out.write_text(html)
    print(f"wrote {out}  ({len(rows)} foods, {len(html)//1024} KB)")


if __name__ == "__main__":
    main()
