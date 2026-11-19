const byId = id => document.getElementById(id);
const picker = byId("case");
const form = byId("knobs");
let cases, rows = [], request = 0, baseline = null, completedParams = null;
const colors = {reference:"#344958", output:"#00749e", measurement:"#b66519", effort:"#98448e",speed_reference:"#344958",velocity:"#00749e"};
const names = {reference:"目标 / 真值", output:"响应 / 估计", measurement:"观测", effort:"控制量"};

function drawPanel(canvas, keys) {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const scale = window.devicePixelRatio || 1;
  canvas.width = Math.round(w * scale); canvas.height = Math.round(h * scale);
  const ctx = canvas.getContext("2d"); ctx.scale(scale, scale);
  const values = rows.flatMap(row => keys.map(k => row[k]));
  if (baseline && keys.includes("output")) values.push(...baseline.rows.map(row=>row.output));
  const lo = Math.min(0,...values)-0.1, hi = Math.max(0,...values)+0.1;
  const x = t => 49 + (w-68) * t / rows[rows.length-1].t;
  const y = v => 12 + (h-48) * (hi-v)/(hi-lo);
  ctx.font = "12px sans-serif";
  for(let i=0;i<=4;i++) {
    const v = lo + i*(hi-lo)/4;
    ctx.fillStyle="#435e6c";ctx.fillText(v.toFixed(1),6,y(v)+4);
    ctx.strokeStyle="#dbe6eb";ctx.beginPath();ctx.moveTo(47,y(v));ctx.lineTo(w-17,y(v));ctx.stroke();
    const t=rows[rows.length-1].t*i/4;
    ctx.fillText(t.toFixed(1)+"s",x(t)-12,h-10);
  }
  if (baseline && keys.includes("output")) {
    ctx.strokeStyle="#8258ad";ctx.lineWidth=2;ctx.setLineDash([2,4]);ctx.beginPath();
    baseline.rows.forEach((row,i)=>i?ctx.lineTo(x(row.t),y(row.output)):ctx.moveTo(x(row.t),y(row.output)));
    ctx.stroke();
  }
  for(const key of keys) {
    ctx.strokeStyle=colors[key] || "#405b58";ctx.lineWidth=key==="output"?2.7:1.4;
    ctx.setLineDash((key==="reference" || key==="speed_reference")?[6,4]:[]);ctx.beginPath();
    rows.forEach((row,i)=>i?ctx.lineTo(x(row.t),y(row[key])):ctx.moveTo(x(row.t),y(row[key])));
    ctx.stroke();
  }
}

function draw() {
  if (!rows.length) return;
  const c = cases[picker.value];
  const primary = ["measurement","reference","output"].filter(k => k in rows[0]);
  const extra = Object.keys(rows[0]).filter(k => k !== "t" && !primary.includes(k));
  const speeds = extra.filter(k=>k==="speed_reference" || k==="velocity");
  const panels = [[primary, c.unit], ...(speeds.length ? [[speeds,"m/s"]] : []), ...extra.filter(k=>!speeds.includes(k)).map(k => [[k], ({
    effort:c.effort_unit || (c.group==="PID" ? c.unit : ""),
    velocity:"m/s", valid:"0 / 1"
  })[k] || ""])];
  const container = byId("plots");
  container.replaceChildren();
  for (const [keys,unit] of panels) {
    const figure=document.createElement("figure");
    if(keys!==primary) figure.className="aux";
    const caption=document.createElement("figcaption");
    const unitLabel=document.createElement("b");
    unitLabel.textContent=unit || "模型单位";
    caption.append(unitLabel);
    for(const key of keys) {
      const item=document.createElement("span");
      item.style.color=colors[key] || "#405b58";
      item.textContent=key==="reference" ? (c.group==="Kalman"?"仿真真值":"目标")
        : key==="output" ? (c.group==="Kalman"?"估计":"实际响应")
        : ({velocity:c.group==="Kalman"?"估计速度":"实际速度",speed_reference:"目标速度",valid:"观测有效",...names})[key] || key;
      caption.append(item);
    }
    if(baseline && keys.includes("output")) {
      const note=document.createElement("span");note.style.color="#8258ad";
      note.textContent="对照 · "+baseline.params;caption.append(note);
    }
    const canvas=document.createElement("canvas");
    canvas.setAttribute("aria-label", caption.textContent+" 随时间变化");
    figure.append(caption,canvas);container.append(figure);drawPanel(canvas,keys);
  }
}
async function run() {
  const id=++request;
  byId('pin').disabled=true;
  byId('status').textContent='等待有效参数';
  if (!form.reportValidity()) return;
  const qs = new URLSearchParams(new FormData(form));qs.set("case",picker.value);
  try {
    const res=await fetch("/api/run?"+qs);
    const data=await res.json();if(!res.ok) throw Error(data.error);
    if(id!==request) return;
    rows=data;
    completedParams=Array.from(qs, ([k,v])=>k==="case"?"":k+"="+v).filter(Boolean).join(" · ");
    byId("pin").disabled=false;
    refreshComparison();byId("status").textContent="仿真完成 · "+rows.length+" 个采样点";
  } catch(e) {if(id===request) byId("status").textContent=e.message;}
}
function rmse(samples) {
  return Math.sqrt(samples.reduce((sum,r)=>sum+(r.output-r.reference)**2,0)/samples.length);
}
function refreshComparison() {
  const current=rmse(rows).toFixed(3);
  byId("score").textContent="均方根误差 "+current+(baseline?"（对照 "+rmse(baseline.rows).toFixed(3)+"）":"")+" "+cases[picker.value].unit;
  byId("clear").hidden=!baseline;
  draw();
}
byId("pin").onclick=()=>{baseline={rows,params:completedParams};refreshComparison()};
byId("clear").onclick=()=>{baseline=null;refreshComparison()};
function selectCase() {
  const c=cases[picker.value];byId("title").textContent=c.title;byId("lesson").textContent=c.lesson;
  form.replaceChildren();
  for(const [name,p] of Object.entries(c.knobs)) {
    const label=document.createElement("label");label.textContent=p.label;
    const input=document.createElement("input");Object.assign(input,{type:"number",name,step:"any",min:p.low,max:p.high,value:p.default,required:true});
    label.append(input);form.append(label);
  }
  run();
}
async function init() {
  cases=await (await fetch("/api/cases")).json();
  for(const [id,c] of Object.entries(cases)) picker.add(new Option(c.group+" / "+c.title,id));
  selectCase();
}
picker.onchange=()=>{
  baseline=null;rows=[];byId("score").textContent="";byId("clear").hidden=true;
  byId("plots").replaceChildren();selectCase();
};form.onchange=run;form.onsubmit=e=>{e.preventDefault();run()};
byId("reset").onclick=selectCase;window.addEventListener("resize",draw);
init().catch(e=>byId("status").textContent=e.message);
