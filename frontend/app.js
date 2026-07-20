const API_BASE = "https://surplusai-backend.vercel.app";
const API_TIMEOUT_MS = 4000;

async function fetchWithTimeout(url, opts={}){
  const ctrl = new AbortController();
  const t = setTimeout(()=>ctrl.abort(), API_TIMEOUT_MS);
  try{
    const res = await fetch(url, {...opts, signal: ctrl.signal});
    return res;
  } finally {
    clearTimeout(t);
  }
}


const MAP_LAYOUT = {
  "ngo_hope": { x:62, y:38 },
  "ngo_asha": { x:78, y:60 },
  "ngo_seva": { x:20, y:70 },
  "ngo_annadaan": { x:40, y:22 },
};
const RESTAURANT_POS = { x:50, y:88 };

const MOCK_NGOS = [
  { id:"ngo_hope", name:"Hope Foundation", need:0.82 },
  { id:"ngo_asha", name:"Asha Shelter Home", need:0.74 },
  { id:"ngo_seva", name:"Seva Community Kitchen", need:0.88 },
  { id:"ngo_annadaan", name:"Annadaan Trust", need:0.65 },
];

let NGOS_CACHE = [];
let DEMO_MODE = false;
let selectedWinnerId = null;
let mapZoom = 1;
let mapFilters = {restaurants:true, ngos:true, volunteers:true, routes:true};
let activeDelivery = null;
let activityEvents = [];

async function checkConnection(){
  const el = document.getElementById('connStatus');
  const label = document.getElementById('connLabel');
  try{
    const res = await fetchWithTimeout(API_BASE + '/health');
    if(!res.ok) throw new Error('bad status');
    DEMO_MODE = false;
    el.classList.remove('demo'); el.classList.add('live');
    label.textContent = 'Backend connected';
    const adminLive=document.getElementById('adminLiveLabel'); if(adminLive) adminLive.textContent='SYSTEM ONLINE';
    NGOS_CACHE = await (await fetchWithTimeout(API_BASE + '/ngos')).json();
    renderMap();
    const impact = await (await fetchWithTimeout(API_BASE + '/impact')).json();
    applyImpactTotals(impact);
  }catch(e){
    DEMO_MODE = true;
    el.classList.remove('live'); el.classList.add('demo');
    label.textContent = 'Demo mode · sample data';
    const adminLive=document.getElementById('adminLiveLabel'); if(adminLive) adminLive.textContent='DEMO MODE · SIMULATED';
    NGOS_CACHE = MOCK_NGOS;
    renderMap();
  }
}
checkConnection();
setInterval(checkConnection, 8000);

document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-'+btn.dataset.view).classList.add('active');
  });
});

document.getElementById('pitchDismiss').addEventListener('click', ()=>{
  document.getElementById('pitchStrip').classList.add('hidden');
});
document.getElementById('pitchCta').addEventListener('click', ()=>{
  document.getElementById('view-restaurant').scrollIntoView({behavior:'smooth'});
  const btn = document.getElementById('donateBtn');
  btn.classList.remove('nudge'); void btn.offsetWidth; btn.classList.add('nudge');
});

const donateBtnEl = document.getElementById('donateBtn');
donateBtnEl.addEventListener('click', ()=>donateBtnEl.classList.remove('nudge'), {once:true});
setTimeout(()=>donateBtnEl.classList.remove('nudge'), 6000);


const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
let uploadedImageBase64 = null;
uploadBox.addEventListener('click', ()=>fileInput.click());
fileInput.addEventListener('change', e=>{
  const f = e.target.files[0];
  if(!f) return;
  const reader = new FileReader();
  reader.onload = ev=>{
    uploadedImageBase64 = ev.target.result;
    uploadBox.innerHTML = `<img src="${ev.target.result}" alt="food photo">`;
  };
  reader.readAsDataURL(f);
});

const AGENT_NAMES = ["Donation","Quality","Expiry","Matching","Routing","Notify","Impact"];
function buildLights(){
  document.getElementById('agentLights').innerHTML =
    AGENT_NAMES.map(n=>`<div class="light" data-agent="${n}"><div class="dot"></div><div class="name">${n}</div></div>`).join('');
}
buildLights();
renderMap();
function resetLights(){ document.querySelectorAll('.light').forEach(l=>l.classList.remove('active','done','fail')); }
function setLight(name, state){
  const el = document.querySelector(`.light[data-agent="${name}"]`);
  if(el){ el.classList.remove('active','done','fail'); el.classList.add(state); }
}

function renderMap(winnerId){
  selectedWinnerId = winnerId || selectedWinnerId;
  const wrap = document.getElementById('mapWrap');
  const canvas = document.getElementById('mapCanvas');
  if(!wrap || !canvas) return;

  canvas.querySelectorAll('.pin,.route-line,.route-hit,.vehicle').forEach(e=>e.remove());

  const addPin = (x,y,color,label,type,extra={})=>{
    const p = document.createElement('div');
    p.className = 'pin interactive-pin ' + (type==='volunteer'?'pin-volunteer':'');
    if(extra.selected) p.classList.add('selected');
    p.style.left=x+'%'; p.style.top=y+'%';
    p.dataset.type=type;
    p.innerHTML = `<div class="dot" style="background:${color}">${type==='volunteer'?'🚚':''}</div><div class="tag">${label}</div>`;
    p.addEventListener('click', (ev)=>{
      ev.stopPropagation();
      if(type==='ngo') showNGOPopup(p, extra.ngo);
    });
    canvas.appendChild(p);
    return p;
  };

  const restaurant = {x:50,y:88};
  if(mapFilters.restaurants) addPin(restaurant.x,restaurant.y,'var(--flare)','Restaurant','restaurant');

  const routeData = [];
  NGOS_CACHE.forEach(n=>{
    const pos = MAP_LAYOUT[n.id] || {x:50,y:50};
    const selected = selectedWinnerId && n.id===selectedWinnerId;
    if(mapFilters.ngos) addPin(pos.x,pos.y,selected?'var(--sage)':'var(--line)',n.name,'ngo',{selected,ngo:n});

    if(mapFilters.routes){
      const dx=pos.x-restaurant.x, dy=pos.y-restaurant.y;
      const len=Math.sqrt(dx*dx+dy*dy);
      const angle=Math.atan2(dy,dx)*180/Math.PI;
      const line=document.createElement('div');
      line.className='route-line '+(selected?'route-selected':'route-muted');
      line.style.left=restaurant.x+'%'; line.style.top=restaurant.y+'%'; line.style.width=len+'%';
      line.style.transform=`rotate(${angle}deg)`;
      line.dataset.ngoId=n.id;
      canvas.appendChild(line);

      const hit=document.createElement('div');
      hit.className='route-hit'; hit.style.left=restaurant.x+'%'; hit.style.top=restaurant.y+'%'; hit.style.width=len+'%';
      hit.style.transform=`rotate(${angle}deg)`;
      hit.addEventListener('click',()=>{selectedWinnerId=n.id; renderMap(n.id); showNGOPopup(null,n);});
      canvas.appendChild(hit);
      routeData.push({n,pos});
    }
  });

  if(activeDelivery && mapFilters.volunteers){

    let vehicle = canvas.querySelector('.vehicle');
    if(!vehicle){
      vehicle = document.createElement('div');
      vehicle.className = 'vehicle';
      vehicle.innerHTML = '🚚<span class="vehicle-label"></span>';
      canvas.appendChild(vehicle);
    }

    const v = activeDelivery;
    const ngoPos = MAP_LAYOUT[v.winnerId] || {x:50,y:50};
    const progress = v.progress || 0;
    const vx = restaurant.x + (ngoPos.x-restaurant.x)*progress;
    const vy = restaurant.y + (ngoPos.y-restaurant.y)*progress;

    vehicle.style.left = vx + '%';
    vehicle.style.top = vy + '%';

    const label = vehicle.querySelector('.vehicle-label');
    if(label) label.textContent = v.volunteer || 'Volunteer';
  }
}

function showNGOPopup(pin, ngo){
  const popup=document.getElementById('mapPopup');
  if(!popup || !ngo) return;
  const pos=MAP_LAYOUT[ngo.id] || {x:50,y:50};
  const score=Math.round((ngo.score || ngo.need || .75)*100);
  popup.innerHTML=`
    <button class="popup-close" onclick="document.getElementById('mapPopup').classList.remove('show')">×</button>
    <h4>${ngo.name}</h4>
    <div class="popup-score">${score}% match</div>
    <div class="popup-bar"><span style="width:${score}%"></span></div>
    <div class="popup-meta">
      ${ngo.distance_km ? `Distance: ${ngo.distance_km} km<br>`:''}
      Current need: ${Math.round((ngo.need_match||ngo.need||.75)*100)}%<br>
      Capacity fit: ${Math.round((ngo.capacity_fit||.8)*100)}%<br>
      Urgency: ${Math.round((ngo.urgency_bonus||.8)*100)}%
    </div>
    <button class="popup-action" onclick="focusDelivery('${ngo.id}')">View route</button>`;
  popup.style.left=Math.min(Math.max(pos.x,12),78)+'%';
  popup.style.top=Math.min(Math.max(pos.y-18,4),70)+'%';
  popup.classList.add('show');
}

let vehicleAnimationFrame = null;
let vehicleAnimationToken = 0;

function animateVehicle(){
  if(!activeDelivery) return;
  if(vehicleAnimationFrame) cancelAnimationFrame(vehicleAnimationFrame);

  const canvas = document.getElementById('mapCanvas');
  if(!canvas) return;

  let vehicle = canvas.querySelector('.vehicle');
  if(!vehicle){
    vehicle = document.createElement('div');
    vehicle.className = 'vehicle';
    vehicle.innerHTML = '🚚<span class="vehicle-label"></span>';
    canvas.appendChild(vehicle);
  }

  const winner = NGOS_CACHE.find(n => n.id === activeDelivery.winnerId);
  const ngoPos = MAP_LAYOUT[activeDelivery.winnerId] || {x:50,y:50};
  const restaurant = {x:50,y:88};

  const startProgress = activeDelivery.progress || 0;
  const endProgress = activeDelivery.progressTarget ?? .7;
  const start = performance.now();
  const duration = 6500;
  const token = ++vehicleAnimationToken;

  const tick = (now) => {
    if(!activeDelivery || token !== vehicleAnimationToken) return;

    const t = Math.min(1, (now - start) / duration);
    const eased = t < .5 ? 2*t*t : 1 - Math.pow(-2*t+2,2)/2;
    const progress = startProgress + (endProgress - startProgress) * eased;

    activeDelivery.progress = progress;

    const x = restaurant.x + (ngoPos.x - restaurant.x) * progress;
    const y = restaurant.y + (ngoPos.y - restaurant.y) * progress;

    vehicle.style.left = x + '%';
    vehicle.style.top = y + '%';

    const label = vehicle.querySelector('.vehicle-label');
    if(label){
      label.textContent = activeDelivery.volunteer || 'Volunteer';
    }

    if(t < 1){
      vehicleAnimationFrame = requestAnimationFrame(tick);
    } else {
      vehicleAnimationFrame = null;
    }
  };

  vehicleAnimationFrame = requestAnimationFrame(tick);
}

function focusDelivery(winnerId){
  selectedWinnerId=winnerId;
  renderMap(winnerId);
  document.getElementById('mapPopup')?.classList.remove('show');
  document.getElementById('mapWrap')?.scrollIntoView({behavior:'smooth',block:'center'});
}


function addActivity(icon,text){
  const feed=document.getElementById('activityFeed');
  if(!feed) return;
  if(feed.querySelector('.portal-note')) feed.innerHTML='';
  const now=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const row=document.createElement('div');
  row.className='activity-item';
  row.innerHTML=`<span class="activity-time">${now}</span><span class="activity-icon">${icon}</span><span class="activity-text">${text}</span>`;
  feed.prepend(row);
  while(feed.children.length>12) feed.lastChild.remove();
  const updated=document.getElementById('lastUpdated');
  if(updated) updated.textContent='Updated just now';
}

function renderMatchPanel(ranked,winner){
  if(!ranked || !winner) return;
  const winnerEl=document.getElementById('matchWinner');
  const rankEl=document.getElementById('rankList');
  const factors=[
    ['Need Match',winner.need_match||0],
    ['Proximity',winner.proximity||0],
    ['Capacity Fit',winner.capacity_fit||0],
    ['Urgency',winner.urgency_bonus||0]
  ];
  winnerEl.innerHTML=`
    <div class="match-winner-head">
      <div><div class="match-winner-name">🏆 ${winner.name}</div><div class="portal-note">Best overall match selected by the Matching Agent</div></div>
      <div class="match-score">${Math.round(winner.score*100)}%</div>
    </div>
    ${factors.map(([name,val])=>`<div class="reason-row"><div class="reason-head"><span>${name}</span><b>${Math.round(val*100)}%</b></div><div class="reason-bar"><span style="width:${Math.round(val*100)}%"></span></div></div>`).join('')}`;
  rankEl.innerHTML=ranked.map((n,i)=>`
    <div class="rank-item" onclick="focusDelivery('${n.id}')">
      <span class="rank-num">${String(i+1).padStart(2,'0')}</span>
      <span class="rank-name">${n.name}${n.id===winner.id?' <span class="badge">Selected</span>':''}</span>
      <span class="rank-score">${Math.round(n.score*100)}%</span>
    </div>`).join('');
}

function renderDelivery(result){
  if(!result || !result.matching || !result.routing) return;
  const list=document.getElementById('deliveryList');
  if(!list) return;
  if(list.querySelector('.portal-note')) list.innerHTML='';
  const winner=result.matching.winner;
  const volunteer=result.routing.volunteer.name;
  activeDelivery={
    winnerId:winner.id,
    volunteer,
    progress:0,
    progressTarget:.85,
    ticketId:result.ticket_id
  };
  const card=document.createElement('div');
  card.className='delivery-card';
  card.dataset.winnerId=winner.id;
  card.innerHTML=`
    <div class="delivery-top"><span class="delivery-id">${result.ticket_id}</span><span class="delivery-status">● En route</span></div>
    <div class="delivery-main">🍱 ${result.donation.quantity} × ${result.donation.food_type}</div>
    <div class="delivery-route">🔴 Restaurant → 🚚 ${volunteer} → 🟢 ${winner.name}<br>ETA: ${result.routing.eta_minutes} min</div>
    <div class="delivery-progress"><span></span></div>`;
  card.addEventListener('click',()=>focusDelivery(winner.id));
  list.prepend(card);
  while(list.children.length>5) list.lastChild.remove();

  renderMap(winner.id);
  animateVehicle();

  const deliveryTicket = result.ticket_id;
  setTimeout(()=>{
    if(activeDelivery && activeDelivery.ticketId===deliveryTicket){
      
      activeDelivery.progressTarget = 1;
      animateVehicle();

      const status=card.querySelector('.delivery-status');
      if(status) status.textContent='● Delivered';
      addActivity('✅',`<b>Delivery completed</b> — ${result.donation.quantity} meals reached ${winner.name}.`);
    }
  },7000);
}

let mapRefreshTimer = null;
function refreshMapSmooth(){
  clearTimeout(mapRefreshTimer);
  mapRefreshTimer = setTimeout(() => renderMap(selectedWinnerId), 30);
}

document.querySelectorAll('.map-filter').forEach(btn=>{
  btn.addEventListener('click',()=>{
    const key=btn.dataset.mapFilter;
    mapFilters[key]=!mapFilters[key];
    btn.classList.toggle('active',mapFilters[key]);
    refreshMapSmooth();
  });
});
document.getElementById('mapZoomIn')?.addEventListener('click',()=>{
  mapZoom=Math.min(1.6,mapZoom+.15);
  document.getElementById('mapCanvas').style.transform=`scale(${mapZoom})`;
});
document.getElementById('mapZoomOut')?.addEventListener('click',()=>{
  mapZoom=Math.max(.75,mapZoom-.15);
  document.getElementById('mapCanvas').style.transform=`scale(${mapZoom})`;
});
document.getElementById('mapZoomReset')?.addEventListener('click',()=>{
  mapZoom=1; document.getElementById('mapCanvas').style.transform='scale(1)';
});
document.getElementById('mapWrap')?.addEventListener('click',(event)=>{
  if(event.target.closest('.map-popup') || event.target.closest('.interactive-pin') || event.target.closest('.route-hit')) return;
  document.getElementById('mapPopup')?.classList.remove('show');
});

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }
function addStep(container, {agent, cls, detail, stamp, stampCls}){
  const div = document.createElement('div');
  div.className = `step ${cls}`;
  div.innerHTML = `
    <div class="step-dot"></div>
    <div class="step-agent">${agent}</div>
    <div class="step-detail">${detail}</div>
    <div class="step-stamp ${stampCls}">${stamp}</div>
  `;
  container.appendChild(div);
}
const CLS_MAP = { ok:['ok','stamp-ok'], warn:['warn','stamp-warn'], fail:['fail','stamp-fail'] };
const LIGHT_MAP = { ok:'done', warn:'done', fail:'fail' };
const agentToLight = { "Donation Agent":"Donation", "Quality Agent":"Quality", "Expiry Agent":"Expiry",
                        "Matching Agent":"Matching", "Route Agent":"Routing", "Notification Agent":"Notify",
                        "Impact Agent":"Impact" };

function showToast(title, body){
  const el = document.getElementById('toast');
  document.getElementById('toastTitle').textContent = title;
  document.getElementById('toastBody').textContent = body;
  el.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(()=>el.classList.remove('show'), 4200);
}

function buildMockResult(body){
  const ticketId = 'DEMO-' + Math.floor(1000 + Math.random()*9000);
  const steps = [
    { agent:'Donation Agent', status:'ok',
      detail:`Logged <b>${body.quantity} × ${body.food_type}</b> from Restaurant Portal. Ticket ${ticketId} opened.`,
      stamp:'Logged' },
  ];

  if(body.force_reject){
    steps.push({ agent:'Quality Agent', status:'fail',
      detail:'Freshness heuristic failed the photo / category check. Donation flagged unsafe and stopped.',
      stamp:'Rejected' });
    return { ticket_id: ticketId, status:'rejected', steps,
      donation:{ quantity: body.quantity, food_type: body.food_type } };
  }

  steps.push({ agent:'Quality Agent', status:'ok', detail:'Freshness heuristic passed. Category risk low.', stamp:'Cleared' });
  steps.push({ agent:'Expiry Agent', status:'ok', detail:`Estimated safe consumption window: ~3h from pickup (${body.pickup_time}).`, stamp:'3h left' });

  const ranked = MOCK_NGOS.map(n=>{
    const need_match = clamp01(n.need + (Math.random()*0.1 - 0.05));
    const proximity = clamp01(0.5 + Math.random()*0.45);
    const capacity_fit = clamp01(0.5 + Math.random()*0.45);
    const urgency_bonus = clamp01(0.5 + Math.random()*0.45);
    const score = +(0.35*need_match + 0.30*proximity + 0.20*capacity_fit + 0.15*urgency_bonus).toFixed(2);
    return { ...n, need_match:+need_match.toFixed(2), proximity:+proximity.toFixed(2),
      capacity_fit:+capacity_fit.toFixed(2), urgency_bonus:+urgency_bonus.toFixed(2),
      score, distance_km:+(1 + Math.random()*6).toFixed(1) };
  }).sort((a,b)=>b.score-a.score);
  const winner = ranked[0];

  steps.push({ agent:'Matching Agent', status:'ok',
    detail:`Ranked ${ranked.length} NGOs on need, proximity, capacity and urgency. <b>${winner.name}</b> selected — score ${winner.score}.`,
    stamp:'Matched' });

  const volunteerNames = ['Rahul V.','Priya S.','Aman K.','Neha T.'];
  const volunteer = volunteerNames[Math.floor(Math.random()*volunteerNames.length)];
  const eta = 8 + Math.floor(Math.random()*20);
  steps.push({ agent:'Route Agent', status:'ok', detail:`<b>${volunteer}</b> assigned. Route to ${winner.name} calculated.`, stamp:eta+' min' });
  steps.push({ agent:'Notification Agent', status:'ok', detail:'Restaurant, NGO, and volunteer notified.', stamp:'Sent' });

  const meals = body.quantity;
  const people = Math.round(meals*0.9);
  const waste_kg = +(meals*0.35).toFixed(1);
  const co2_kg = +(meals*0.9).toFixed(1);
  steps.push({ agent:'Impact Agent', status:'ok', detail:`+${meals} meals rescued, ~${people} people fed.`, stamp:'Logged' });

  return {
    ticket_id: ticketId,
    status: 'completed',
    steps,
    donation: { quantity: meals, food_type: body.food_type },
    matching: { ranked, winner },
    routing: { volunteer:{ name: volunteer }, eta_minutes: eta },
    impact: { session_totals: {
      meals: lastTotals.meals + meals,
      people: lastTotals.people + people,
      waste_kg: +(lastTotals.waste_kg + waste_kg).toFixed(1),
      co2_kg: +(lastTotals.co2_kg + co2_kg).toFixed(1),
    }}
  };
}
function clamp01(v){ return Math.max(0, Math.min(1, v)); }

document.getElementById('donateBtn').addEventListener('click', runDonation);

async function runDonation(){
  const btn = document.getElementById('donateBtn');
  const errBanner = document.getElementById('errBanner');
  errBanner.classList.remove('show');
  btn.disabled = true;

  const body = {
    food_type: document.getElementById('foodType').value,
    quantity: parseInt(document.getElementById('quantity').value) || 1,
    pickup_time: document.getElementById('pickupTime').value,
    force_reject: document.getElementById('forceReject').checked,
    image_base64: uploadedImageBase64,
  };

  let result, usedMock = false;
  if(!DEMO_MODE){
    try{
      const res = await fetchWithTimeout(API_BASE + '/donate', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(body),
      });
      if(!res.ok) throw new Error('Backend returned ' + res.status);
      result = await res.json();
    }catch(e){
      usedMock = true;
    }
  } else {
    usedMock = true;
  }

  if(usedMock){
    result = buildMockResult(body);
  }

  await renderResult(result, usedMock);
  btn.disabled = false;
}

async function renderResult(result, usedMock){
  resetLights();
  const pipeline = document.getElementById('pipeline');
  pipeline.innerHTML = '';
  document.getElementById('decisionBox').classList.remove('show');
  document.getElementById('ticketBadge').textContent = (usedMock ? 'DEMO · ' : '') + (result.ticket_id || '');

  for(const step of result.steps){
    const [stepCls, stampCls] = CLS_MAP[step.status] || CLS_MAP.ok;
    const lightName = agentToLight[step.agent];
    if(lightName) setLight(lightName, 'active');
    addActivity(step.status==='fail'?'⚠️':step.status==='warn'?'⏳':'🤖',`<b>${step.agent}</b> — ${step.detail}`);
    await sleep(550);
    addStep(pipeline, { agent: step.agent, cls: stepCls, detail: step.detail, stamp: step.stamp, stampCls });
    if(lightName) setLight(lightName, LIGHT_MAP[step.status] || 'done');

    if(step.agent === 'Matching Agent' && result.matching && result.matching.ranked){
      showDecisionTimeline(result.matching.ranked);
      renderMap(result.matching.winner.id);
      renderMatchPanel(result.matching.ranked,result.matching.winner);
      addActivity('🎯',`<b>Matching Agent selected ${result.matching.winner.name}</b> with a ${Math.round(result.matching.winner.score*100)}% match score.`);
    }
    if(step.agent === 'Route Agent' && result.routing){
      addActivity('🚚',`<b>Route Agent assigned ${result.routing.volunteer.name}</b> — ETA ${result.routing.eta_minutes} min.`);
    }
    await sleep(250);
  }

  if(result.status === 'completed'){
    applyImpactTotals(result.impact.session_totals);
    logDonation(result);
    addFeed(result);
    renderDelivery(result);
    addActivity('📦',`<b>Donation created</b> — ${result.donation.quantity} × ${result.donation.food_type} is now in the rescue network.`);
    showToast('Rescued', `${result.donation.quantity} × ${result.donation.food_type} routed to ${result.matching.winner.name}.`);
  } else if(result.status === 'rejected'){
    showToast('Rejected', 'Quality Agent stopped this donation — see the pipeline for why.');
  }
}

function showDecisionTimeline(ranked){
  const dbox = document.getElementById('decisionBox');
  const bd = document.getElementById('ngoBreakdown');
  bd.innerHTML = ranked.map((n,i)=>`
    <div class="ngo-row ${i===0?'winner':''}">
      <div>
        <div>${i===0?'🏆 ':''}${n.name} — ${n.distance_km} km</div>
        <div class="ngo-detail">need ${n.need_match} · proximity ${n.proximity} · capacity ${n.capacity_fit} · urgency ${n.urgency_bonus}</div>
      </div>
      <span class="ngo-score">score ${n.score}</span>
    </div>`).join('');
  dbox.classList.add('show');
}

function animateNum(el, from, to, suffix=''){
  const dur = 600, start = performance.now();
  function step(t){
    const p = Math.min(1, (t-start)/dur);
    const val = Math.round(from + (to-from)*p);
    el.textContent = val + suffix;
    if(p<1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
let lastTotals = {meals:0, people:0, waste_kg:0, co2_kg:0};
function applyImpactTotals(totals){
  animateNum(document.getElementById('statMeals'), lastTotals.meals, totals.meals);
  animateNum(document.getElementById('statPeople'), lastTotals.people, totals.people);
  animateNum(document.getElementById('statWaste'), lastTotals.waste_kg, totals.waste_kg, 'kg');
  animateNum(document.getElementById('statCO2'), lastTotals.co2_kg, totals.co2_kg, 'kg');
  lastTotals = totals;
}

function logDonation(result){
  const log = document.getElementById('donationLog');
  if(log.querySelector('.portal-note')) log.innerHTML = '';
  const row = document.createElement('div');
  row.className = 'log-row';
  const now = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  row.innerHTML = `<span>${result.ticket_id} · ${result.donation.quantity} × ${result.donation.food_type} → ${result.matching.winner.name}</span><span class="log-time">${now}</span>`;
  log.prepend(row);
}
function addFeed(result){
  const ngoFeed = document.getElementById('ngoFeed');
  if(ngoFeed.querySelector('.portal-note')) ngoFeed.innerHTML='';
  const row = document.createElement('div');
  row.className='log-row';
  row.innerHTML = `<span><span class="badge">${result.ticket_id}</span>${result.donation.quantity} × ${result.donation.food_type} arriving from Restaurant</span><span class="log-time">via ${result.routing.volunteer.name}</span>`;
  ngoFeed.prepend(row);

  const volFeed = document.getElementById('volFeed');
  if(volFeed.querySelector('.portal-note')) volFeed.innerHTML='';
  const vrow = document.createElement('div');
  vrow.className='log-row';
  vrow.innerHTML = `<span><span class="badge">${result.ticket_id}</span>Deliver ${result.donation.quantity} × ${result.donation.food_type} to ${result.matching.winner.name}</span><span class="log-time">ETA ${result.routing.eta_minutes} min</span>`;
  volFeed.prepend(vrow);
}

const demoSteps = [
  {
    icon:'🍱',
    title:'Donation received',
    detail:'A restaurant has registered 40 fresh vegetarian meals that would otherwise become food waste.',
    status:'Donation Agent · Intake complete'
  },
  {
    icon:'🔍',
    title:'Quality verified',
    detail:'The Quality Agent checks the food category and confirms that the donation is suitable for redistribution.',
    status:'Quality Agent · Verified'
  },
  {
    icon:'⏳',
    title:'Expiry checked',
    detail:'The Expiry Agent confirms that the meals are still within a safe consumption window.',
    status:'Expiry Agent · Safe window confirmed'
  },
  {
    icon:'🎯',
    title:'Best NGO selected',
    detail:'The Matching Agent compares need, proximity, capacity and urgency, then selects Hope Foundation with a 92% match.',
    status:'Matching Agent · 92% AI match'
  },
  {
    icon:'🚚',
    title:'Volunteer assigned',
    detail:'The Route Agent assigns Rahul V. and calculates an estimated 8-minute delivery route.',
    status:'Route Agent · ETA 8 minutes',
    route:true
  },
  {
    icon:'🗺️',
    title:'Delivery in progress',
    detail:'The volunteer moves from the restaurant to the selected NGO while the operation is tracked in real time.',
    status:'Live Operations · En route',
    route:true
  },
  {
    icon:'🌍',
    title:'Impact recorded',
    detail:'The rescue is complete. The system records the meals rescued, people fed and food waste prevented.',
    status:'Impact Agent · Mission complete',
    stats:true
  }
];

let demoIndex = -1;
let demoTimer = null;

function openDemo(){
  const modal=document.getElementById('demoModal');
  if(!modal) return;
  modal.classList.add('show');
  modal.setAttribute('aria-hidden','false');
  document.body.style.overflow='hidden';
  resetDemo();
}

function closeDemo(){
  const modal=document.getElementById('demoModal');
  if(!modal) return;
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden','true');
  document.body.style.overflow='';
  clearTimeout(demoTimer);
}

function resetDemo(){
  clearTimeout(demoTimer);
  demoIndex=-1;
  document.getElementById('demoNext').style.display='inline-flex';
  document.getElementById('demoNext').textContent='Start Demo';
  document.getElementById('demoRestart').style.display='none';
  document.getElementById('demoRoute').style.display='none';
  document.getElementById('demoStats').style.display='none';
  document.getElementById('demoComplete').classList.remove('show');
  document.getElementById('demoProgress').style.width='0%';
  document.getElementById('demoStepNumber').textContent='Ready to start';
  document.getElementById('demoStepIcon').textContent='🍱';
  document.getElementById('demoStepTitle').textContent='Watch SurplusAI work';
  document.getElementById('demoStepDetail').textContent='Click Start Demo to see a complete surplus-food rescue journey.';
  document.getElementById('demoStatus').textContent='Interactive simulation ready';
  const truck=document.getElementById('demoTruck');
  if(truck) truck.style.left='10%';
}

function renderDemoStep(index){
  const step=demoSteps[index];
  if(!step) return;

  document.getElementById('demoStepNumber').textContent=`Step ${index+1} of ${demoSteps.length}`;
  document.getElementById('demoStepIcon').textContent=step.icon;
  document.getElementById('demoStepTitle').textContent=step.title;
  document.getElementById('demoStepDetail').textContent=step.detail;
  document.getElementById('demoStatus').textContent=step.status;
  document.getElementById('demoProgress').style.width=((index+1)/demoSteps.length*100)+'%';

  const route=document.getElementById('demoRoute');
  const stats=document.getElementById('demoStats');
  const complete=document.getElementById('demoComplete');
  route.style.display=step.route?'block':'none';
  stats.style.display=step.stats?'grid':'none';

  if(index===demoSteps.length-1){
    complete.classList.add('show');
    document.getElementById('demoNext').style.display='none';
    document.getElementById('demoRestart').style.display='inline-flex';
  }else{
    complete.classList.remove('show');
    document.getElementById('demoNext').style.display='inline-flex';
    document.getElementById('demoNext').textContent=index===demoSteps.length-2?'Complete Rescue':'Next Step';
  }

  if(index===5){
    const truck=document.getElementById('demoTruck');
    if(truck){
      truck.style.left='10%';
      requestAnimationFrame(()=>requestAnimationFrame(()=>truck.style.left='90%'));
    }
  }
}

function nextDemoStep(){
  clearTimeout(demoTimer);
  demoIndex++;
  if(demoIndex>=demoSteps.length){
    demoIndex=demoSteps.length-1;
  }
  renderDemoStep(demoIndex);

 
  if(demoIndex<demoSteps.length-1){
    demoTimer=setTimeout(nextDemoStep,1900);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('demoClose')?.addEventListener('click', closeDemo);
  document.getElementById('demoNext')?.addEventListener('click', nextDemoStep);
  document.getElementById('demoRestart')?.addEventListener('click', resetDemo);
  document.getElementById('demoExplore')?.addEventListener('click', () => {
    closeDemo();
    const adminNav = document.querySelector('[data-view="admin"]');
    if (adminNav) adminNav.click();
    else if (typeof showView === 'function') showView('admin');
  });

  document.getElementById('demoModal')?.addEventListener('click', (event) => {
    if (event.target.id === 'demoModal') closeDemo();
  });
});

document.addEventListener('keydown',(event)=>{
  if(event.key==='Escape') closeDemo();
});


const watchButtons=document.querySelectorAll(
  '#watchItWork, .watch-it-work, [data-action="watch-demo"]'
);
watchButtons.forEach(btn=>{
  btn.addEventListener('click',(event)=>{
    event.preventDefault();
    openDemo();
  });
});

if(watchButtons.length===0){
  [...document.querySelectorAll('button,a')].forEach(btn=>{
    if(btn.textContent.trim().toLowerCase().includes('watch it work')){
      btn.addEventListener('click',(event)=>{
        event.preventDefault();
        openDemo();
      });
    }
  });
}
