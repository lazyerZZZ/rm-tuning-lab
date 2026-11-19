const byId = id => document.getElementById(id);
const picker = byId("case");
const form = byId("knobs");
let cases, rows = [], request = 0;
const colors = {reference:"#344958", output:"#00749e", measurement:"#b66519", effort:"#98448e"};
const names = {reference:"目标 / 真值", output:"响应 / 估计", measurement:"观测", effort:"控制量"};

function drawPanel(canvas, keys) {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const scale = window.devicePixelRatio || 1;
  canvas.width = Math.round(w * scale); canvas.height = Math.round(h * scale);
  const ctx = canvas.getContext("2d"); ctx.scale(scale, scale);
  const values = rows.flatMap(row => keys.map(k => row[k]));
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
  for(const key of keys) {
    ctx.strokeStyle=colors[key] || "#405b58";ctx.lineWidth=key==="output"?2.7:1.4;
    ctx.setLineDash(key==="reference"?[6,4]:[]);ctx.beginPath();
    rows.forEach((row,i)=>i?ctx.lineTo(x(row.t),y(row[key])):ctx.moveTo(x(row.t),y(row[key])));
    ctx.stroke();
  }
}

function draw() {
  if (!rows.length) return;
  const c = cases[picker.value];
  const primary = ["measurement","reference","output"].filter(k => k in rows[0]);
  const extra = Object.keys(rows[0]).filter(k => k !== "t" && !primary.includes(k));
  const panels = [[primary, c.unit], ...extra.map(k => [[k], ({
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
        : ({velocity:"估计速度",valid:"观测有效",...names})[key] || key;
      caption.append(item);
    }
    const canvas=document.createElement("canvas");
    canvas.setAttribute("aria-label", caption.textContent+" 随时间变化");
    figure.append(caption,canvas);container.append(figure);drawPanel(canvas,keys);
  }
}
async function run() {
  const id=++request;
  if (!form.reportValidity()) return;
  const qs = new URLSearchParams(new FormData(form));qs.set("case",picker.value);
  try {
    const res=await fetch("/api/run?"+qs);
    const data=await res.json();if(!res.ok) throw Error(data.error);
    if(id!==request) return;
    rows=data;draw();byId("status").textContent="仿真完成 · "+rows.length+" 个采样点";
  } catch(e) {if(id===request) byId("status").textContent=e.message;}
}
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
picker.onchange=selectCase;form.onchange=run;form.onsubmit=e=>{e.preventDefault();run()};
byId("reset").onclick=selectCase;window.addEventListener("resize",draw);
init().catch(e=>byId("status").textContent=e.message);
