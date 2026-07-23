#!/usr/bin/env python3
"""Interactive review of the CLEANED category CV pools (cv_class fine pools).

Each pool row (ingredient_class × nutrient) shows the pooled median CV, distinct
food count, and IQR; clicking it reveals exactly which source foods (desc, own CV,
prep, dataset) went into the median — so inclusion can be eyeballed.

Writes a self-contained HTML page to argv[1].
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import psycopg2

import cv_config

FAMILY = {
    "amino_acid": "amino_acids", "major_mineral": "minerals_major",
    "trace_mineral": "minerals_trace", "se_i": "minerals_trace",
    "water_sol_vit": "vitamins_water", "choline": "vitamins_water",
    "fat_sol_vit": "vitamins_fat", "n3_long_chain": "fatty_acids",
    "n6_linoleic": "fatty_acids", "n3_terrestrial": "fatty_acids",
    "arachidonic": "fatty_acids", "fat": "proximates_fat",
    "low_cv_proximate": "proximates_fat",
}


def load():
    c = psycopg2.connect(host=os.environ["DATABASE_HOST"], port=os.environ["DATABASE_PORT"],
                         dbname=os.environ["DATABASE_NAME"], user=os.environ["DATABASE_USER"],
                         password=os.environ["DATABASE_PASSWORD"])
    cur = c.cursor()
    cur.execute("""SELECT ingredient_class, nutrient_nbr, nutrient_class, pooled_cv, n_foods,
                          cv_p25, cv_p75, pooling_method, method_mix
                   FROM cv_class WHERE nutrient_nbr<>-1""")
    pools = []
    names = {}
    for ic, nbr, nc, cv, nf, p25, p75, meth, mm in cur.fetchall():
        pools.append([ic, int(nbr), FAMILY.get(nc, nc), round(float(cv), 3), int(nf),
                      round(float(p25), 3) if p25 is not None else None,
                      round(float(p75), 3) if p75 is not None else None,
                      meth, (mm if isinstance(mm, str) else json.dumps(mm)) if mm else ""])
    # nutrient name is the same regardless of (sub)class -> key by nbr alone
    cur.execute("SELECT nutrient_nbr, max(nutrient_name) FROM cv_observations GROUP BY 1")
    names = {int(nbr): nm for nbr, nm in cur.fetchall()}
    cur.execute("""SELECT ingredient_class, nutrient_nbr, source_food_desc, cv, prep_state, source_dataset
                   FROM cv_observations ORDER BY cv""")
    foods = defaultdict(list)
    for ic, nbr, desc, cv, ps, ds in cur.fetchall():
        row = [desc, round(float(cv), 3), ps,
               "SR28" if ds == "sr28" else ("SRL" if ds == "fdc_sr_legacy" else "FDN")]
        foods[f"{ic}|{int(nbr)}"].append(row)
        # mirror muscle foods under their poultry/red sub-pool key (cv_pool derives
        # the subclass the same way from source_food_desc)
        if ic == "muscle":
            sub = cv_config.muscle_subclass(desc)
            if sub:
                foods[f"muscle::{sub}|{int(nbr)}"].append(row)
    c.close()
    for p in pools:
        p.append(names.get(p[1], f"#{p[1]}"))   # nutrient name at index 9
    return pools, dict(foods)


HTML = r"""<title>Cleaned CV pools — category × nutrient</title>
<style>
:root{--bg:#f6f8fa;--surface:#fff;--surface2:#f0f3f7;--border:#e0e5ec;--text:#1b2230;
--muted:#616c7d;--accent:#0d7d8a;--keep:#1c7c54;--drop:#b23a48;--amber:#9d6a12;--violet:#6a49ad;
--shadow:0 1px 2px rgba(20,28,45,.06),0 4px 16px rgba(20,28,45,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#0e131a;--surface:#161d27;--surface2:#1c2531;
--border:#28323f;--text:#e6ecf3;--muted:#93a0b2;--accent:#3cc4d2;--keep:#54cf8c;--drop:#f0808f;
--amber:#e0aa4d;--violet:#b399ec;--shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.28)}}
:root[data-theme="light"]{--bg:#f6f8fa;--surface:#fff;--surface2:#f0f3f7;--border:#e0e5ec;--text:#1b2230;--muted:#616c7d;--accent:#0d7d8a;--keep:#1c7c54;--drop:#b23a48;--amber:#9d6a12;--violet:#6a49ad}
:root[data-theme="dark"]{--bg:#0e131a;--surface:#161d27;--surface2:#1c2531;--border:#28323f;--text:#e6ecf3;--muted:#93a0b2;--accent:#3cc4d2;--keep:#54cf8c;--drop:#f0808f;--amber:#e0aa4d;--violet:#b399ec}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:14px;line-height:1.45}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1200px;margin:0 auto;padding:24px 20px 80px}
h1{font-size:22px;font-weight:650;letter-spacing:-.01em;margin:0 0 4px}
header p{margin:0;color:var(--muted);max-width:74ch}
.eyebrow{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:650;margin:0 0 8px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin:22px 0 8px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:11px 12px;box-shadow:var(--shadow);cursor:pointer}
.card.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent),var(--shadow)}
.card .name{font-size:12px;font-weight:650;text-transform:capitalize}
.card .big{font-size:20px;font-weight:680;margin-top:2px}
.card .sub{font-size:11px;color:var(--muted)}
.controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:14px 0 10px;margin-top:10px;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
input[type=search]{flex:1;min-width:180px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:7px 11px;color:var(--text);font-size:13px}
input:focus{outline:2px solid var(--accent);outline-offset:1px}
.count{color:var(--muted);font-size:12.5px;margin-left:auto}
.tblwrap{overflow-x:auto;margin-top:6px;border:1px solid var(--border);border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:var(--surface2);text-align:left;padding:8px 10px;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);font-weight:650;border-bottom:1px solid var(--border);cursor:pointer;white-space:nowrap}
thead th:hover{color:var(--accent)}
tbody td{padding:7px 10px;border-bottom:1px solid var(--border)}
tr.pool{cursor:pointer}
tr.pool:hover{background:var(--surface2)}
tr.pool.open{background:var(--surface2)}
.sc{font-weight:660}
.sc.hi{color:var(--drop)}.sc.mid{color:var(--amber)}.sc.lo{color:var(--keep)}
.thin{color:var(--drop);font-weight:640}
.foods{background:var(--bg)}
.foods td{padding:0}
.foodsInner{padding:6px 10px 12px 26px}
.foodsInner table{font-size:12px;width:100%}
.foodsInner th{background:transparent;position:static;text-transform:none;letter-spacing:0;font-size:10.5px}
.foodsInner td{border-bottom:1px dotted var(--border);padding:4px 8px}
.pill{display:inline-block;font-size:10px;font-weight:650;padding:1px 6px;border-radius:5px;background:var(--surface2);color:var(--muted)}
.chev{display:inline-block;width:12px;color:var(--muted)}
.fam{font-size:11px;color:var(--muted)}
</style>
<div class="wrap">
<header>
<p class="eyebrow">Nutrient-CV pipeline · cleaned pools (cv-v2)</p>
<h1>Category CV pools — raw + native only</h1>
<p>Each row is one pooled median CV for an ingredient class × nutrient, built only from
<b>raw / native single-ingredient foods</b> (cooked, canned, added-solution, and composite/branded foods excluded).
Click a row to see exactly which source foods and CVs went into the median. Red count = pool below the
K≥5-foods threshold (falls back to a coarser pool or prior downstream).</p>
</header>
<div class="cards" id="cards"></div>
<div class="controls">
<input type="search" id="q" placeholder="Search nutrient / class…">
<span class="count" id="count"></span>
</div>
<div class="tblwrap"><table>
<thead><tr>
<th data-k="cls">Class</th><th data-k="nut">Nutrient</th><th data-k="fam">Family</th>
<th data-k="cv">Pooled CV</th><th data-k="n">#foods</th><th data-k="iqr">IQR (p25–p75)</th>
<th data-k="method">Pooling</th>
</tr></thead>
<tbody id="tb"></tbody>
</table></div>
</div>
<script>
const POOLS=__POOLS__, FOODS=__FOODS__;
// pool fields: [cls,nbr,fam,cv,n,p25,p75,method,method_mix,nut]
const P=POOLS.map(r=>({cls:r[0],nbr:r[1],fam:r[2],cv:r[3],n:r[4],p25:r[5],p75:r[6],method:r[7],mm:r[8],nut:r[9]}));
const CLASSES=["muscle","muscle::poultry","muscle::red","organ","fish","egg","dairy","fat_oil","plant"];
let cat="all",sortK="cv",sortDir=-1,openKey=null;
const $=s=>document.querySelector(s);
function cardHTML(name,rows){const cvs=rows.map(r=>r.cv).sort((a,b)=>a-b);
 const med=cvs.length?cvs[Math.floor(cvs.length/2)]:0;
 return `<div class="card" data-cat="${name}"><div class="name">${name.replace('_',' ')}</div>
 <div class="big mono">${rows.length}</div><div class="sub">pools · med CV ${med.toFixed(2)}</div></div>`;}
function buildCards(){const c=$("#cards");
 c.innerHTML=cardHTML("all",P)+CLASSES.map(k=>cardHTML(k,P.filter(r=>r.cls===k))).join("");
 c.querySelectorAll(".card").forEach(el=>el.onclick=()=>{cat=el.dataset.cat;openKey=null;render();});}
function scc(v){return v>=0.30?"hi":(v>=0.15?"mid":"lo");}
function esc(s){return(s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function foodsHTML(key){const f=FOODS[key]||[];
 const rows=f.map(x=>`<tr><td class="mono sc ${scc(x[1])}">${x[1].toFixed(3)}</td>
  <td><span class="pill">${x[2]}</span></td><td><span class="pill">${x[3]}</span></td>
  <td>${esc(x[0])}</td></tr>`).join("");
 return `<tr class="foods"><td colspan="7"><div class="foodsInner">
  <div class="fam" style="margin-bottom:4px">${f.length} contributing food×${'nutrient'} observations (sorted by CV)</div>
  <table><thead><tr><th>CV</th><th>prep</th><th>src</th><th>food</th></tr></thead><tbody>${rows}</tbody></table>
  </div></td></tr>`;}
function poolRow(r){const key=r.cls+"|"+r.nbr;const open=openKey===key;
 const iqr=(r.p25!=null&&r.p75!=null)?`${r.p25.toFixed(3)}–${r.p75.toFixed(3)}`:"—";
 const ncls=r.n<5?"thin":"";
 return `<tr class="pool ${open?'open':''}" data-key="${key}">
  <td><span class="chev">${open?'▾':'▸'}</span>${r.cls}</td>
  <td>${esc(r.nut)}</td><td class="fam">${r.fam}</td>
  <td class="mono sc ${scc(r.cv)}">${r.cv.toFixed(3)}</td>
  <td class="mono ${ncls}">${r.n}</td><td class="mono">${iqr}</td>
  <td class="fam">${r.method}</td></tr>` + (open?foodsHTML(key):"");}
function render(){
 document.querySelectorAll(".card").forEach(el=>el.classList.toggle("active",el.dataset.cat===cat));
 let rows=cat==="all"?P.slice():P.filter(r=>r.cls===cat);
 const q=$("#q").value.trim().toLowerCase();
 if(q)rows=rows.filter(r=>(r.nut+" "+r.cls+" "+r.fam).toLowerCase().includes(q));
 rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];if(sortK==="iqr"){x=a.p75-a.p25;y=b.p75-b.p25;}
  if(typeof x==="string"){x=x.toLowerCase();y=(""+y).toLowerCase();}return x<y?-1*sortDir:x>y?sortDir:0;});
 $("#tb").innerHTML=rows.map(poolRow).join("");
 $("#count").textContent=`${rows.length} pools`;
 document.querySelectorAll("tr.pool").forEach(tr=>tr.onclick=()=>{const k=tr.dataset.key;openKey=openKey===k?null:k;render();});
}
buildCards();
document.querySelectorAll("thead th").forEach(th=>th.onclick=()=>{const k=th.dataset.k;
 if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=(k==="cv"||k==="n")?-1:1;}render();});
$("#q").oninput=()=>{openKey=null;render();};
render();
</script>
"""


def main() -> None:
    pools, foods = load()
    html = (HTML.replace("__POOLS__", json.dumps(pools, separators=(",", ":")))
                .replace("__FOODS__", json.dumps(foods, separators=(",", ":"))))
    out = sys.argv[1]
    open(out, "w").write(html)
    print(f"wrote {out}  ({len(pools)} pools, {sum(len(v) for v in foods.values())} food-obs, {len(html)//1024} KB)")


if __name__ == "__main__":
    main()
