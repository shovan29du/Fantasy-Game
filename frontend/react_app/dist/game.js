const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const api=async(url,options={})=>{const response=await fetch(url,options);let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||`Request failed (${response.status})`);return data};
const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message){const el=$('#toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}

// ═══ PLAY VIEW: real backend-backed tabletop state ═══
// The four playable realities. Each is created as a real /api/worlds row on
// first load (with 0-10 world-scale ratings), so map switching, the world
// readout, and the portal all reflect real multiverse data instead of a
// static mock.
const WORLD_DEFS=[
 {name:'Aethoria Prime',magic:'high',tech:'middle_age',space:'fantasy',reality_type:'Prime Reality',place:'Thornwatch Crossing',theme:'local'},
 {name:'Neon Shard-9',magic:'very_low',tech:'cyberpunk',space:'sci-fi',reality_type:'Parallel Universe',place:'Kairox Undercity',theme:'area'},
 {name:'Earth-Z',magic:'none',tech:'post_collapse',space:'post-apocalyptic',reality_type:'Dead Universe',place:'London Quarantine',theme:'area'},
 {name:'Celestia Drift',magic:'medium',tech:'futuristic',space:'sci-fi',reality_type:'Alternate Reality',place:'The Orison Gate',theme:'universe'},
];
const party=[
 {name:'Ari Solwyn',role:'Human · Spellblade',lv:1,hp:100,initials:'AS',linked:true},
 {name:'Kael Ironroot',role:'Dwarf · Vanguard',lv:7,hp:74,initials:'KI'},
 {name:'Nyx-13',role:'Cyborg · Operative',lv:6,hp:91,initials:'N13'},
 {name:'Seraphine',role:'Tiefling · Seer',lv:6,hp:62,initials:'SE'},
];
const actions=[
 {name:'Arc Slash',icon:'⚔',kind:'attack',cost:'2 AP',xp:5}, {name:'Fire Bolt',icon:'✦',kind:'attack',cost:'1 mana',xp:5},
 {name:'Guard',icon:'◈',kind:'defence',cost:'1 AP'}, {name:'Aegis',icon:'⬡',kind:'defence',cost:'3 mana'},
 {name:'Blink',icon:'⌁',kind:'utility',cost:'2 mana'}, {name:'Inspect',icon:'⌕',kind:'utility',cost:'Free'},
 {name:'Loot',icon:'⚗',kind:'utility',cost:'Free'},
];

let state={worldIndex:0,scale:'local',x:42,y:52,zoom:100,selected:0,characterId:null,worlds:[],sheet:null,inventory:{economy:{},items:[]},quests:[],weaponTiers:[]};

async function ensureWorlds(){
 const existing=await api('/api/worlds');
 const worlds=[];
 for(const def of WORLD_DEFS){
  let row=existing.find(w=>w.name===def.name);
  if(!row) row=await api('/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:def.name,magic:def.magic,tech:def.tech,space:def.space,num_locs:6,reality_type:def.reality_type})});
  worlds.push({...def,id:row.id,ratings:row.ratings||{}});
 }
 return worlds;
}
async function ensureCharacter(){
 const chars=await api('/api/characters');
 if(chars.length) return chars[chars.length-1].id;
 const created=await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Ari Solwyn',race:'Human',profession:'Wizard',level:1,origin_world:'Aethoria Prime'})});
 return created.id;
}
async function refreshCharacterState(){
 const sheet=await api(`/api/characters/${state.characterId}/sheet`);
 const [inventory,quests]=await Promise.all([
  api(`/api/characters/${state.characterId}/inventory`),
  api(`/api/quests/active?character_name=${encodeURIComponent(sheet.name||'')}`).catch(()=>[]),
 ]);
 state.sheet=sheet; state.inventory=inventory; state.quests=quests||[];
}
function statMod(v){return Math.floor(((v||10)-10)/2)}
function derivedResources(sheet){
 const con=sheet?.total_stats?.constitution?.total ?? 10, int=sheet?.total_stats?.intelligence?.total ?? 10, wis=sheet?.total_stats?.wisdom?.total ?? 10;
 const lv=sheet?.calc_lv ?? sheet?.level ?? 1;
 const maxHp=20+lv*8+statMod(con)*lv;
 const maxMana=10+lv*4+Math.max(statMod(int),statMod(wis))*lv;
 return {maxHp,maxMana};
}
function renderParty(){
 if(state.sheet){const p=party[0];p.name=state.sheet.name||p.name;p.lv=state.sheet.calc_lv||state.sheet.level||1;p.role=`${safe(state.sheet.race||'Unknown')} · ${safe(state.sheet.profession||'Adventurer')}`;p.hp=100}
 $('#partyList').innerHTML=party.map((p,i)=>`<div class="party-card ${i===state.selected?'active':''}" data-party="${i}"><div class="portrait">${safe(p.initials)}</div><div><strong>${safe(p.name)}</strong><small>${p.role}</small><div class="hp"><i style="width:${p.hp}%"></i></div></div><span class="level">LV ${safe(p.lv)}</span></div>`).join('');
 $$('[data-party]').forEach(el=>el.onclick=()=>{state.selected=+el.dataset.party;renderParty();toast(`${party[state.selected].name} selected`)})
}
function renderQuests(){
 if(!state.quests.length){$('#questList').innerHTML=`<div class="quest"><p>No active quests.</p><div class="quest-progress"><span>Generate one from the current reality</span><button id="genQuestBtn" class="ghost">✦ Generate</button></div></div>`;const b=$('#genQuestBtn');if(b)b.onclick=generateQuest;return}
 $('#questList').innerHTML=state.quests.map((q,i)=>`<div class="quest"><b>${i===0?'✦ ':''}${safe(q.title||'Quest')}</b><p>${safe(q.description||'')}</p><div class="quest-progress"><span>Progress ${safe(q.progress ?? 0)} · Reward: ${safe(q.reward||'—')}</span><span>›</span></div></div>`).join('')
}
async function generateQuest(){
 try{const world=state.worlds[state.worldIndex];await api('/api/quests/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_name:state.sheet?.name||'Ari Solwyn',character_id:state.characterId,world_id:world?.id})});await refreshCharacterState();renderQuests();toast('New quest generated')}catch(error){toast(error.message)}
}
function renderActions(filter='all'){
 const visible=actions.filter(a=>filter==='all'||a.kind===filter);
 $('#actionBar').innerHTML=visible.map((a,i)=>`<button class="action" data-action="${a.name}"><kbd>${i+1}</kbd><span class="icon">${a.icon}</span><b>${a.name}</b><small>${a.cost}</small></button>`).join('');
 $$('[data-action]').forEach(el=>el.onclick=()=>runAction(el.dataset.action));
}
async function runAction(name){
 const action=actions.find(a=>a.name===name);
 if(!action){toast(`${name} readied`);return}
 if(action.kind==='attack'&&action.xp){
  const previousLevel=state.sheet?.calc_lv||1;
  try{const result=await api(`/api/characters/${state.characterId}/xp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:action.xp,reason:name})});
   state.sheet=result.sheet;renderParty();
   const newLevel=result.sheet?.calc_lv||previousLevel;
   toast(newLevel>previousLevel?`${name}! Level up — now level ${newLevel}`:`${name}: +${action.xp} XP`);
   if($('#detailContent').innerHTML.includes('EXPERIENCE'))showPanel('character');
  }catch(error){toast(`${name} readied`)}
  return;
 }
 if(name==='Loot'){await lootItem();return}
 toast(`${name} readied`);
}
async function lootItem(){
 const world=state.worlds[state.worldIndex];
 const tier=Math.min(10,Math.max(0,world?.ratings?.weapon ?? 2));
 const found=(state.weaponTiers.find(t=>t.tier===tier)||state.weaponTiers[2]);
 const itemName=found.examples[Math.floor(Math.random()*found.examples.length)];
 try{
  await api(`/api/characters/${state.characterId}/inventory`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item_name:itemName,item_type:'weapon',weapon_tier:tier})});
  await refreshCharacterState();
  toast(`Found: ${itemName} (Weapon tier ${tier} · ${found.era})`);
  if($('#detailContent').innerHTML.includes('INVENTORY'))showPanel('inventory');
 }catch(error){toast(error.message)}
}
const panels={
 character:()=>{
  const s=state.sheet; if(!s) return '<div class="empty-state">Loading character...</div>';
  const stats=s.total_stats||{}; const xp=s.xp_progress||{into:0,need:1,fraction:0};
  const rows=[['STR','strength'],['DEX','dexterity'],['CON','constitution'],['INT','intelligence'],['WIS','wisdom'],['CHA','charisma_stat']];
  const {maxHp,maxMana}=derivedResources(s);
  const sig=s.reality_signature||{}; const tier=s.power_tier_info||{name:'Heroic'};
  return `<div class="character-hero"><div class="hero-portrait">${safe((s.name||'?').slice(0,2).toUpperCase())}</div><h2>${safe(s.name)}</h2><p>${safe(s.race||'Unknown')} · Level ${safe(s.calc_lv||s.level||1)} ${safe(s.profession||'Adventurer')}</p><p>${safe(tier.name)} tier · ${safe(sig.reality_type||'Prime Reality')} (${safe(sig.universe_tag||'—')})</p></div><div class="xp-row"><div><span>EXPERIENCE</span><span>${safe(s.xp||0)} XP (${xp.into}/${xp.need} to next)</span></div><div class="meter"><i style="width:${Math.round((xp.fraction||0)*100)}%"></i></div></div><div class="stats">${rows.map(([label,key])=>`<div class="stat"><b>${(stats[key]||{}).total ?? 10}</b><small>${label} · +${statMod((stats[key]||{}).total)}</small></div>`).join('')}</div><div class="resource"><div><span>Health</span><b>${maxHp} / ${maxHp}</b></div><div class="meter"><i style="width:100%;background:var(--green)"></i></div></div><div class="resource"><div><span>Mana</span><b>${maxMana} / ${maxMana}</b></div><div class="meter"><i style="width:100%;background:var(--purple)"></i></div></div>`;
 },
 inventory:()=>{
  const items=state.inventory.items||[];
  if(!items.length) return `<div class="panel-title"><span>INVENTORY</span><small>0 items</small></div><div class="empty-state">Nothing carried yet — try the <b>Loot</b> utility action.</div>`;
  return `<div class="panel-title"><span>INVENTORY</span><small>${items.length} items</small></div><div class="inventory-grid">${items.map(it=>`<button class="item" data-item-id="${it.id}">${it.equip_slot?'⚔':'◇'}${it.quantity>1?`<small>${it.quantity}</small>`:''}</button>`).join('')}</div><div class="item-info"><h3 id="itemName">Select an item</h3><p id="itemDesc">Click an item to inspect it.</p></div>`;
 },
 spells:()=>{
  const spells=state.sheet?.spells||[];
  if(!spells.length) return '<div class="panel-title"><span>SPELLBOOK</span><small>0 prepared</small></div><div class="empty-state">No spells learned yet.</div>';
  return `<div class="panel-title"><span>SPELLBOOK</span><small>${spells.length} prepared</small></div>${spells.map(sp=>`<div class="spell-row"><span class="rune">✦</span><span><b>${safe(sp)}</b><small>${safe((state.sheet.magic_type||[]).join(', ')||'Arcane')}</small></span></div>`).join('')}`;
 },
 skills:()=>{
  const s=state.sheet; if(!s) return '<div class="empty-state">Loading...</div>';
  const learned=[...(s.skills||[]),...(s.traits||[])]; const available=(s.available_feats||[]).slice(0,6);
  return `<div class="panel-title"><span>SKILL TREE</span><small>${safe(s.skill_points_available||0)} points</small></div><div class="tree">${learned.map(sk=>`<button class="skill-node unlocked"><b>${safe(sk)}</b><small>Unlocked</small></button>`).join('')||'<p class="empty-state">No skills or feats learned yet.</p>'}${available.map(f=>`<button class="skill-node" data-feat="${safe(f)}"><b>${safe(f)}</b><small>Learn feat</small></button>`).join('')}</div>`;
 },
};
function showPanel(name){
 $('#detailContent').innerHTML=panels[name]();
 if(name==='inventory')$$('[data-item-id]').forEach(el=>el.onclick=()=>{const item=(state.inventory.items||[]).find(i=>String(i.id)===el.dataset.itemId);if(!item)return;$('#itemName').textContent=item.item_name;const tierInfo=item.weapon_tier_info||{};$('#itemDesc').textContent=item.equip_slot?`Weapon tier ${item.weapon_tier} · ${tierInfo.era||''} — ${(tierInfo.properties||[]).join(', ')||'No special properties.'}`:(item.description||'A piece of multiverse adventuring gear.')});
 if(name==='skills')$$('[data-feat]').forEach(el=>el.onclick=async()=>{try{const result=await api(`/api/characters/${state.characterId}/feats`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feat:el.dataset.feat})});state.sheet=result.sheet;toast(`${el.dataset.feat} learned`);showPanel('skills')}catch(error){toast(error.message)}});
}
function worldTagsText(world){
 const r=world.ratings||{};
 return `${world.space} · Magic ${r.magic ?? '?'} · Tech ${r.technology ?? '?'} · Weapon ${r.weapon ?? '?'} · ${world.reality_type}`;
}
function updateWorld(){
 const w=state.worlds[state.worldIndex]; if(!w)return;
 $('#worldName').textContent=w.name;$('#worldTags').textContent=worldTagsText(w);$('#locationName').textContent=w.place;state.scale=w.theme;setScale(state.scale);
}
function setScale(scale){state.scale=scale;$('#map').className=`map map-${scale}`;$('#scaleLabel').textContent=`${scale.toUpperCase()} MAP`;$$('[data-scale]').forEach(b=>b.classList.toggle('active',b.dataset.scale===scale));}
function move(x,y){state.x=Math.max(4,Math.min(96,x));state.y=Math.max(6,Math.min(92,y));const p=$('#playerToken');p.style.setProperty('--x',state.x+'%');p.style.setProperty('--y',state.y+'%')}

async function crossPortal(){
 const fromIdx=state.worldIndex; const toIdx=(fromIdx+1)%state.worlds.length;
 const origin=state.worlds[fromIdx], dest=state.worlds[toIdx];
 try{
  const report=await api('/api/multiverse/travel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({origin_world_id:origin.id,dest_world_id:dest.id,character_id:state.characterId})});
  state.worldIndex=toIdx; updateWorld();
  const itemWarning=(report.item_effects||[]).find(e=>e.status!=='compatible');
  toast(`Portal crossed: ${dest.name} — ${itemWarning?itemWarning.message:report.effects[0]}`);
 }catch(error){state.worldIndex=toIdx;updateWorld();toast(`Portal crossed: ${dest.name}`)}
}

async function initPlay(){
 try{
  const [worlds,characterId,weaponTiers]=await Promise.all([ensureWorlds(),ensureCharacter(),api('/api/weapons/tiers')]);
  state.worlds=worlds; state.characterId=characterId; state.weaponTiers=weaponTiers;
  await refreshCharacterState();
 }catch(error){toast(`Play mode running offline: ${error.message}`)}
 renderParty();renderQuests();renderActions();showPanel('character');updateWorld();
}

$$('[data-scale]').forEach(b=>b.onclick=()=>setScale(b.dataset.scale));
$$('.detail-tabs button').forEach(b=>b.onclick=()=>{$$('.detail-tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');showPanel(b.dataset.panel)});
$$('.dock-head button').forEach(b=>b.onclick=()=>{$$('.dock-head button').forEach(x=>x.classList.remove('active'));b.classList.add('active');renderActions(b.dataset.filter)});
$('#map').addEventListener('click',e=>{if(e.target.closest('button'))return;const r=e.currentTarget.getBoundingClientRect();move((e.clientX-r.left)/r.width*100,(e.clientY-r.top)/r.height*100)});
document.addEventListener('keydown',e=>{const active=document.activeElement;if(active&&active.tagName==='INPUT')return;const keys={w:[0,-3],ArrowUp:[0,-3],s:[0,3],ArrowDown:[0,3],a:[-3,0],ArrowLeft:[-3,0],d:[3,0],ArrowRight:[3,0]};if(keys[e.key]){e.preventDefault();move(state.x+keys[e.key][0],state.y+keys[e.key][1])}if('1234'.includes(e.key))setScale(['local','area','world','universe'][+e.key-1])});
$('#portal').onclick=crossPortal;
$$('.map-node').forEach(n=>n.onclick=()=>toast(`${n.dataset.label}: destination marked`));
$('#zoomIn').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.min(140,state.zoom+10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#zoomOut').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.max(70,state.zoom-10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#saveBtn').onclick=async()=>{localStorage.setItem('worldweaver-save',JSON.stringify({characterId:state.characterId,worldIndex:state.worldIndex}));try{const r=await fetch('/api/chat/saves',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:'worldweaver-campaign',save_name:`${state.worlds[state.worldIndex]?.name||'Unknown'} - Level ${state.sheet?.calc_lv||1}`,character_name:state.sheet?.name||'Ari Solwyn'})});if(!r.ok)throw 0;toast('Campaign and story saved')}catch{toast('Campaign saved on this device')}};$('#journalBtn').onclick=()=>toast('Quest journal opened');
$('#chatToggle').onclick=()=>$('#chatPanel').classList.add('open');$('#closeChat').onclick=()=>$('#chatPanel').classList.remove('open');
$('#chatForm').onsubmit=async e=>{e.preventDefault();const input=$('#chatInput'),msg=input.value.trim();if(!msg)return;$('#chatLog').insertAdjacentHTML('beforeend',`<p class="player"><b>YOU</b>${safe(msg)}</p>`);input.value='';$('#aiStatus').textContent='Thinking...';try{const world=state.worlds[state.worldIndex];const context=`[World: ${world?.name}; Location: ${world?.place}; Level: ${state.sheet?.calc_lv||1}; Party: ${party.map(p=>p.name).join(', ')}] `;const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:context+msg,session_id:'worldweaver-campaign',user_name:'Player',character_name:'Worldweaver',participants:['Worldweaver'],temperature:.75})});const data=await r.json();if(!r.ok)throw new Error(data.detail||'Local model unavailable');$('#chatLog').insertAdjacentHTML('beforeend',`<p class="gm"><b>WORLDWEAVER</b>${safe(data.reply)}</p>`);$('#aiStatus').textContent='LM Studio connected'}catch(error){$('#chatLog').insertAdjacentHTML('beforeend',`<p class="gm"><b>WORLDWEAVER</b>${safe(error.message||'The local storyteller cannot be reached.')}</p>`);$('#aiStatus').textContent='Start LM Studio on port 1234'}$('#chatLog').scrollTop=$('#chatLog').scrollHeight};

// ═══ AI Companion-style workspace navigation and studios ═══
function openView(name){$$('.app-view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.side-nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));$('#chatToggle').style.display=name==='play'?'block':'none';$('#chatPanel').classList.remove('open');if(name==='characters')loadCharacterStudio();if(name==='worlds')loadWorlds();if(name==='knowledge')loadLore();if(name==='settings')checkModelStatus()}
$$('.side-nav button').forEach(button=>button.onclick=()=>openView(button.dataset.view));

let studioOptions={};
function fillSelect(selector,values){const el=$(selector);if(!el)return;const list=Array.isArray(values)?values:Object.keys(values||{});el.innerHTML=list.map(value=>`<option value="${safe(value)}">${safe(value)}</option>`).join('')}
async function loadCharacterStudio(){try{if(!Object.keys(studioOptions).length){studioOptions=await api('/api/options');fillSelect('#raceSelect',studioOptions.races);fillSelect('#professionSelect',studioOptions.professions);fillSelect('#backgroundSelect',studioOptions.backgrounds);fillSelect('#alignmentSelect',studioOptions.alignments)}const characters=await api('/api/characters');$('#characterLibrary').innerHTML=characters.length?characters.map(c=>`<article class="entity-card"><span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span><div><b>${safe(c.name)}</b><small>${safe(c.race||'Unknown ancestry')} · ${safe(c.profession||'Adventurer')}</small></div><em>LV ${safe(c.level||1)}</em></article>`).join(''):'<div class="empty-state">No saved characters yet. Create your first companion.</div>'}catch(error){$('#characterLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#characterForm').onsubmit=async event=>{event.preventDefault();const form=new FormData(event.currentTarget);const payload=Object.fromEntries(form.entries());payload.level=Number(payload.level||1);payload.scenario=`Origin reality: ${payload.scenario}`;try{await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`${payload.name} saved`);event.currentTarget.reset();await loadCharacterStudio()}catch(error){toast(error.message)}};
$('#randomCharacter').onclick=async()=>{try{const {character}=await api('/api/characters/random',{method:'POST'});const form=$('#characterForm');['name','race','profession','background','alignment','backstory','goals'].forEach(key=>{if(form.elements[key]&&character[key]!=null)form.elements[key].value=Array.isArray(character[key])?character[key].join(', '):character[key]});toast('Random character generated')}catch(error){toast(error.message)}};
$('#refreshCharacters').onclick=loadCharacterStudio;$('#newCharacterBtn').onclick=()=>{$('#characterForm').scrollIntoView({behavior:'smooth'});$('#characterForm').elements.name.focus()};

async function loadWorlds(){try{const items=await api('/api/worlds');$('#worldLibrary').innerHTML=items.length?items.map(w=>`<article class="entity-card"><span class="entity-avatar">◎</span><div><b>${safe(w.name)}</b><small>${safe(w.space_alignment||'multiverse')} · ${safe(w.reality_type||'Prime Reality')} · Magic ${safe(w.ratings?.magic ?? w.magic_level)}</small></div><em>${safe(w.time_of_day||'Active')}</em></article>`).join(''):'<div class="empty-state">No database worlds yet. The four play-map realities remain available.</div>'}catch(error){$('#worldLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#worldForm').onsubmit=async event=>{event.preventDefault();const payload=Object.fromEntries(new FormData(event.currentTarget).entries());payload.num_locs=Number(payload.num_locs||8);try{await api('/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`${payload.name} created`);event.currentTarget.reset();loadWorlds()}catch(error){toast(error.message)}};$('#refreshWorlds').onclick=loadWorlds;

async function loadLore(){try{const items=await api('/api/knowledge/lorebook');$('#loreLibrary').innerHTML=items.length?items.map(item=>`<article class="entity-card"><span class="entity-avatar">◇</span><div><b>${safe(item.title)}</b><small>${safe((item.content||'').slice(0,90))}</small></div><em>${item.enabled===0?'Off':'Active'}</em></article>`).join(''):'<div class="empty-state">No lorebook entries. Add rules, locations, and secrets here.</div>'}catch(error){$('#loreLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#loreForm').onsubmit=async event=>{event.preventDefault();const raw=Object.fromEntries(new FormData(event.currentTarget).entries());const payload={title:raw.title,content:raw.content,keywords:raw.keywords.split(',').map(x=>x.trim()).filter(Boolean),world_id:0,always_active:true};try{await api('/api/knowledge/lorebook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Lore saved');event.currentTarget.reset();loadLore()}catch(error){toast(error.message)}};$('#refreshLore').onclick=loadLore;

async function checkModelStatus(){const badge=$('#modelBadge');badge.textContent='Checking';badge.classList.remove('good');try{const result=await api('/api/settings/model');badge.textContent='Configured';badge.classList.add('good');$('#activeModel').textContent=result.active_model||'LM Studio model'}catch{badge.textContent='Offline';$('#activeModel').textContent='Start LM Studio on port 1234'}}
$('#checkModel').onclick=checkModelStatus;$('#reducedMotion').onchange=e=>{document.body.classList.toggle('reduced-motion',e.target.checked);localStorage.setItem('reduced-motion',e.target.checked)};$('#compactMode').onchange=e=>{document.body.classList.toggle('compact',e.target.checked);localStorage.setItem('compact-mode',e.target.checked)};$('#reducedMotion').checked=localStorage.getItem('reduced-motion')==='true';$('#compactMode').checked=localStorage.getItem('compact-mode')==='true';document.body.classList.toggle('reduced-motion',$('#reducedMotion').checked);document.body.classList.toggle('compact',$('#compactMode').checked);$$('[data-feature]').forEach(button=>button.onclick=()=>toast(`${button.dataset.feature} tools are connected to the local media API`));

openView('play');
initPlay();
