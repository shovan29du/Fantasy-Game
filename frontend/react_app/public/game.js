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
 {name:'No adventurer yet',role:'Create one in the Characters tab',lv:0,hp:0,initials:'?',linked:true},
 {name:'Kael Ironroot',role:'Dwarf · Vanguard',lv:7,hp:74,initials:'KI'},
 {name:'Nyx-13',role:'Cyborg · Operative',lv:6,hp:91,initials:'N13'},
 {name:'Seraphine',role:'Tiefling · Seer',lv:6,hp:62,initials:'SE'},
];
const actions=[
 {name:'Engage Enemies',icon:'⚔',kind:'attack',cost:'Tactical'}, {name:'Fire Bolt',icon:'✦',kind:'attack',cost:'1 mana',xp:5},
 {name:'Guard',icon:'◈',kind:'defence',cost:'1 AP'}, {name:'Aegis',icon:'⬡',kind:'defence',cost:'3 mana'},
 {name:'Blink',icon:'⌁',kind:'utility',cost:'2 mana'}, {name:'Inspect',icon:'⌕',kind:'utility',cost:'Free'},
 {name:'Loot',icon:'⚗',kind:'utility',cost:'Free'},
];

let state={worldIndex:0,scale:'local',x:42,y:52,zoom:100,selected:0,characterId:null,worlds:[],flavorWorlds:[],sessionId:'default',sheet:null,inventory:{economy:{},items:[]},quests:[],weaponTiers:[],locations:[],locationImageCache:{},pendingCategory:null,randomScenarioText:'',hasActiveGame:false,allSpells:{},dndWeapons:{},dndWeaponCategories:[],voiceEnabled:localStorage.getItem('companion-voice')==='true'};
const SESSION_KEY='worldweaver-session';
const TERRAIN_ICONS={Forest:'♣',Desert:'▲',Mountain:'⛰',Ocean:'≈',Swamp:'♨',Volcano:'▲',Plains:'❦',City:'⌂',Ruins:'⌂',Space:'✦',Underground:'▼',Tundra:'❄',Jungle:'♣',Savanna:'❦',Canyon:'▲'};

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
// No auto-created placeholder character: character creation always goes
// through the same form/endpoint as the AI Companion "Characters" tab (see
// #characterForm below). Play just picks up whichever character exists.
async function getExistingCharacterId(){
 const chars=await api('/api/characters');
 return chars.length?chars[chars.length-1].id:null;
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
 const p=party[0];
 if(state.sheet){p.name=state.sheet.name||p.name;p.lv=state.sheet.calc_lv||state.sheet.level||1;p.role=`${safe(state.sheet.race||'Unknown')} · ${safe(state.sheet.profession||'Adventurer')}`;p.hp=100;p.initials=(state.sheet.name||'??').slice(0,2).toUpperCase()}
 $('#partyList').innerHTML=party.map((pt,i)=>`<div class="party-card ${i===state.selected?'active':''}" data-party="${i}"><div class="portrait">${safe(pt.initials)}</div><div><strong>${safe(pt.name)}</strong><small>${pt.role}</small><div class="hp"><i style="width:${pt.hp}%"></i></div></div><span class="level">LV ${safe(pt.lv)}</span></div>`).join('');
 $$('[data-party]').forEach(el=>el.onclick=()=>{const i=+el.dataset.party;if(i===0&&!state.characterId){goCreateCharacter();return}state.selected=i;renderParty();toast(`${party[state.selected].name} selected`)})
}
function renderQuests(){
 if(!state.quests.length){$('#questList').innerHTML=`<div class="quest"><p>No active quests.</p><div class="quest-progress"><span>Generate one from the current reality</span><button id="genQuestBtn" class="ghost">✦ Generate</button></div></div>`;const b=$('#genQuestBtn');if(b)b.onclick=generateQuest;return}
 $('#questList').innerHTML=state.quests.map((q,i)=>`<div class="quest"><b>${i===0?'✦ ':''}${safe(q.title||'Quest')}</b><p>${safe(q.description||'')}</p><div class="quest-progress"><span>Progress ${safe(q.progress ?? 0)} · Reward: ${safe(q.reward||'—')}</span><span>›</span></div></div>`).join('')
}
async function generateQuest(){
 if(!state.characterId){goCreateCharacter();return}
 try{const world=state.worlds[state.worldIndex];await api('/api/quests/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_name:state.sheet?.name,character_id:state.characterId,world_id:world?.id})});await refreshCharacterState();renderQuests();toast('New quest generated')}catch(error){toast(error.message)}
}
function goCreateCharacter(){toast('Create your adventurer in the Characters tab first');openView('characters');const nameField=$('#characterForm')?.elements?.name;if(nameField)nameField.focus()}
function renderActions(filter='all'){
 const visible=actions.filter(a=>filter==='all'||a.kind===filter);
 $('#actionBar').innerHTML=visible.map((a,i)=>`<button class="action" data-action="${a.name}"><kbd>${i+1}</kbd><span class="icon">${a.icon}</span><b>${a.name}</b><small>${a.cost}</small></button>`).join('');
 $$('[data-action]').forEach(el=>el.onclick=()=>runAction(el.dataset.action));
}
async function runAction(name){
 const action=actions.find(a=>a.name===name);
 if(!action){toast(`${name} readied`);return}
 if((action.kind==='attack'||name==='Loot')&&!state.characterId){goCreateCharacter();return}
 if(name==='Engage Enemies'){await startCombat();return}
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
  const s=state.sheet; if(!s) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const stats=s.total_stats||{}; const xp=s.xp_progress||{into:0,need:1,fraction:0};
  const rows=[['STR','strength'],['DEX','dexterity'],['CON','constitution'],['INT','intelligence'],['WIS','wisdom'],['CHA','charisma_stat']];
  const {maxHp,maxMana}=derivedResources(s);
  const sig=s.reality_signature||{}; const tier=s.power_tier_info||{name:'Heroic'};
  return `<div class="character-hero"><div class="hero-portrait">${safe((s.name||'?').slice(0,2).toUpperCase())}</div><h2>${safe(s.name)}</h2><p>${safe(s.race||'Unknown')} · Level ${safe(s.calc_lv||s.level||1)} ${safe(s.profession||'Adventurer')}</p><p>${safe(tier.name)} tier · ${safe(sig.reality_type||'Prime Reality')} (${safe(sig.universe_tag||'—')})</p></div><div class="xp-row"><div><span>EXPERIENCE</span><span>${safe(s.xp||0)} XP (${xp.into}/${xp.need} to next)</span></div><div class="meter"><i style="width:${Math.round((xp.fraction||0)*100)}%"></i></div></div><div class="stats">${rows.map(([label,key])=>`<div class="stat"><b>${(stats[key]||{}).total ?? 10}</b><small>${label} · +${statMod((stats[key]||{}).total)}</small></div>`).join('')}</div><div class="resource"><div><span>Health</span><b>${maxHp} / ${maxHp}</b></div><div class="meter"><i style="width:100%;background:var(--green)"></i></div></div><div class="resource"><div><span>Mana</span><b>${maxMana} / ${maxMana}</b></div><div class="meter"><i style="width:100%;background:var(--purple)"></i></div></div>`;
 },
 inventory:()=>{
  if(!state.characterId) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const items=state.inventory.items||[];
  const invHtml=items.length?`<div class="panel-title"><span>INVENTORY</span><small>${items.length} items</small></div><div class="inventory-grid">${items.map(it=>`<button class="item" data-item-id="${it.id}">${it.equip_slot?'⚔':'◇'}${it.quantity>1?`<small>${it.quantity}</small>`:''}</button>`).join('')}</div><div class="item-info"><h3 id="itemName">Select an item</h3><p id="itemDesc">Click an item to inspect it.</p></div>`
   :`<div class="panel-title"><span>INVENTORY</span><small>0 items</small></div><div class="empty-state">Nothing carried yet — try the <b>Loot</b> utility action.</div>`;
  const equippedName=(items.find(it=>it.equip_slot==='weapon')||{}).item_name;
  const cats=state.dndWeaponCategories.length?state.dndWeaponCategories:[...new Set(Object.values(state.dndWeapons).map(w=>w.category))].sort();
  const armory=cats.map(cat=>{
   const catWeapons=Object.entries(state.dndWeapons).filter(([,w])=>w.category===cat);
   if(!catWeapons.length)return '';
   return `<div class="armory-cat"><small>${safe(cat)}</small>${catWeapons.map(([name,w])=>`<button class="armory-item${name===equippedName?' equipped':''}" data-equip-weapon="${safe(name)}"><b>${safe(name)}</b><small>${safe(w.damage)} ${safe(w.damage_type)}${w.properties.length?` · ${w.properties.join(', ')}`:''}</small>${name===equippedName?'<em>Equipped</em>':''}</button>`).join('')}</div>`;
  }).join('');
  return `${invHtml}<div class="panel-title"><span>ARMORY</span><small>D&amp;D weapons</small></div><div class="armory-grid">${armory}</div>`;
 },
 spells:()=>{
  const known=state.sheet?.spells||[];
  const profession=state.sheet?.profession||'';
  const knownHtml=known.length?known.map(name=>{
   const sp=state.allSpells[name];
   if(!sp)return `<div class="spell-row"><span class="rune">✦</span><span><b>${safe(name)}</b></span></div>`;
   const level=sp.level===0?'Cantrip':`Level ${sp.level}`;
   return `<div class="spell-row"><span class="rune">✦</span><span><b>${safe(name)}</b><small>${level} · ${safe(sp.school)} — ${safe(sp.description)}</small></span></div>`;
  }).join(''):'<div class="empty-state">No spells learned yet.</div>';
  const learnable=Object.entries(state.allSpells).filter(([name,sp])=>!known.includes(name)&&(!profession||sp.classes.includes(profession)));
  const learnHtml=learnable.length?learnable.map(([name,sp])=>{
   const level=sp.level===0?'Cantrip':`Level ${sp.level}`;
   return `<button class="spell-row learnable" data-learn-spell="${safe(name)}"><span class="rune">＋</span><span><b>${safe(name)}</b><small>${level} · ${safe(sp.school)} — ${safe(sp.description)}</small></span></button>`;
  }).join(''):'<div class="empty-state">No more spells for this class.</div>';
  return `<div class="panel-title"><span>SPELLBOOK</span><small>${known.length} prepared</small></div>${knownHtml}<div class="panel-title"><span>LEARN A SPELL</span><small>${safe(profession||'Any class')}</small></div>${learnHtml}`;
 },
 skills:()=>{
  const s=state.sheet; if(!s) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const learned=[...(s.skills||[]),...(s.traits||[])]; const available=(s.available_feats||[]).slice(0,6);
  return `<div class="panel-title"><span>SKILL TREE</span><small>${safe(s.skill_points_available||0)} points</small></div><div class="tree">${learned.map(sk=>`<button class="skill-node unlocked"><b>${safe(sk)}</b><small>Unlocked</small></button>`).join('')||'<p class="empty-state">No skills or feats learned yet.</p>'}${available.map(f=>`<button class="skill-node" data-feat="${safe(f)}"><b>${safe(f)}</b><small>Learn feat</small></button>`).join('')}</div>`;
 },
};
function showPanel(name){
 $('#detailContent').innerHTML=panels[name]();
 const createBtn=$('#goCreateCharacterBtn'); if(createBtn)createBtn.onclick=goCreateCharacter;
 if(name==='inventory'){
  $$('[data-item-id]').forEach(el=>el.onclick=()=>{const item=(state.inventory.items||[]).find(i=>String(i.id)===el.dataset.itemId);if(!item)return;$('#itemName').textContent=item.item_name;const tierInfo=item.weapon_tier_info||{};$('#itemDesc').textContent=item.equip_slot?`Weapon tier ${item.weapon_tier} · ${tierInfo.era||''} — ${(tierInfo.properties||[]).join(', ')||'No special properties.'}`:(item.description||'A piece of multiverse adventuring gear.')});
  $$('[data-equip-weapon]').forEach(el=>el.onclick=async()=>{try{await api(`/api/characters/${state.characterId}/equip`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({weapon_name:el.dataset.equipWeapon})});await refreshCharacterState();toast(`${el.dataset.equipWeapon} equipped`);showPanel('inventory')}catch(error){toast(error.message)}});
 }
 if(name==='skills')$$('[data-feat]').forEach(el=>el.onclick=async()=>{try{const result=await api(`/api/characters/${state.characterId}/feats`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feat:el.dataset.feat})});state.sheet=result.sheet;toast(`${el.dataset.feat} learned`);showPanel('skills')}catch(error){toast(error.message)}});
 if(name==='spells')$$('[data-learn-spell]').forEach(el=>el.onclick=async()=>{try{const result=await api(`/api/characters/${state.characterId}/spells`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spell:el.dataset.learnSpell})});state.sheet=result.sheet;toast(`${el.dataset.learnSpell} learned`);showPanel('spells')}catch(error){toast(error.message)}});
}
function worldTagsText(world){
 const r=world.ratings||{};
 return `${world.space} · Magic ${r.magic ?? '?'} · Tech ${r.technology ?? '?'} · Weapon ${r.weapon ?? '?'} · ${world.reality_type}`;
}
function updateWorld(){
 const w=state.worlds[state.worldIndex]; if(!w)return;
 $('#worldName').textContent=w.name;$('#worldTags').textContent=worldTagsText(w);$('#locationName').textContent=w.place;state.scale=w.theme;setScale(state.scale);
 loadLocations();
}

// ═══ Locations: enter a map icon to generate a scene image and use it as background ═══
function renderMapNodes(){
 $('#mapNodes').innerHTML=state.locations.map(loc=>`<button class="map-node" style="--x:${loc.x}%;--y:${loc.y}%" data-loc-id="${loc.id}" data-label="${safe(loc.name)}" title="${safe(loc.name)}">${TERRAIN_ICONS[loc.terrain]||'⌂'}</button>`).join('');
 $$('#mapNodes [data-loc-id]').forEach(el=>el.onclick=()=>{const loc=state.locations.find(l=>String(l.id)===el.dataset.locId);if(loc)enterLocation(loc)});
}
async function loadLocations(){
 const world=state.worlds[state.worldIndex]; if(!world)return;
 try{state.locations=await api(`/api/worlds/${world.id}/locations`);renderMapNodes()}catch(error){state.locations=[];renderMapNodes()}
}
async function enterLocation(loc){
 const world=state.worlds[state.worldIndex];
 $('#sceneTitle').textContent=loc.name;
 $('#sceneSubtitle').textContent=`${loc.terrain} · ${world?.name||''}`;
 $('#sceneOverlay').classList.add('open');
 const bg=$('#sceneBg'), loading=$('#sceneLoading');
 if(state.locationImageCache[loc.id]){bg.style.backgroundImage=`url("${encodeURI(state.locationImageCache[loc.id])}")`;loading.classList.add('hidden');return}
 loading.classList.remove('hidden');bg.style.backgroundImage='';
 const character=state.sheet;
 const prompt=`${world?.name||'A realm'}, ${loc.terrain} region called ${loc.name}. ${loc.description||''} A ${character?.race||'traveller'} ${character?.profession||'adventurer'} named ${character?.name||'the hero'} stands in the scene.`;
 try{
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:'Cinematic',width:1024,height:576,save_to_chat:false})});
  const url=result.url||result.path;
  if(url){state.locationImageCache[loc.id]=url;bg.style.backgroundImage=`url("${encodeURI(url)}")`}
 }catch(error){toast(`Scene generation failed: ${error.message}`)}
 loading.classList.add('hidden');
}
$('#exitSceneBtn').onclick=()=>$('#sceneOverlay').classList.remove('open');
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

function loadSessionFromStorage(){try{const raw=localStorage.getItem(SESSION_KEY);return raw?JSON.parse(raw):null}catch{return null}}
function saveSessionToStorage(){localStorage.setItem(SESSION_KEY,JSON.stringify({sessionId:state.sessionId,worldId:state.worlds[0]?.id,characterId:state.characterId}))}
function toWorldEntry(w){return {id:w.id,name:w.name,ratings:w.ratings||{},reality_type:w.reality_type||'Prime Reality',space:w.space_alignment||'unknown',place:'Uncharted',theme:'local'}}
async function loadChatHistory(){
 try{
  const history=await api(`/api/chat/history?session_id=${encodeURIComponent(state.sessionId)}&limit=40`);
  $('#chatLog').innerHTML=history.length?history.map(m=>`<p class="${m.role==='user'?'player':'gm'}">${safe(m.content)}</p>`).join(''):'<p class="gm">The portal hums, waiting for your first move.</p>';
  $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
 }catch{}
}
async function bindSession({sessionId,worldId,characterId}){
 state.hasActiveGame=true;
 state.sessionId=sessionId||'default';
 let world=null;
 if(worldId){try{world=toWorldEntry(await api(`/api/worlds/${worldId}`))}catch{}}
 state.worlds=world?[world,...state.flavorWorlds.filter(f=>f.id!==world.id)]:state.flavorWorlds;
 state.worldIndex=0;
 if(characterId){state.characterId=characterId;await refreshCharacterState()}
 await loadChatHistory();
 saveSessionToStorage();
 updateWorld();renderParty();renderQuests();
 try{const active=await api(`/api/combat/active?session_id=${encodeURIComponent(state.sessionId)}`);openCombat(active)}catch{/* no combat in progress for this session */}
}
async function initPlay(){
 try{
  const [flavorWorlds,characterId,weaponTiers,spellData,weaponData]=await Promise.all([ensureWorlds(),getExistingCharacterId(),api('/api/weapons/tiers'),api('/api/spells'),api('/api/weapons/dnd')]);
  state.flavorWorlds=flavorWorlds; state.characterId=characterId; state.weaponTiers=weaponTiers;
  state.allSpells=spellData.spells||{}; state.dndWeapons=weaponData.weapons||{}; state.dndWeaponCategories=weaponData.categories||[];
  if(state.characterId) await refreshCharacterState();
 }catch(error){toast(`Play mode running offline: ${error.message}`)}
 renderParty();renderQuests();renderActions();showPanel('character');
 const saved=loadSessionFromStorage();
 if(saved){try{await bindSession(saved);hidePlayHub();return}catch{/* fall through to start screen */}}
 state.worlds=state.flavorWorlds;state.worldIndex=0;updateWorld();
 showPlayHub();
}

// ═══ Play hub: New Game (category -> scenario) or Load Saved Game ═══
function showStartStep(name){$$('.start-step').forEach(s=>s.hidden=(s.id!==`startStep-${name}`))}
function showPlayHub(){$('#playHub').hidden=false;$('#gameArea').hidden=true;showStartStep('choice');$('#hubCloseBtn').hidden=!state.hasActiveGame}
function hidePlayHub(){$('#playHub').hidden=true;$('#gameArea').hidden=false;state.hasActiveGame=true}
$('#hubCloseBtn').onclick=hidePlayHub;
$('#switchGameBtn').onclick=showPlayHub;
$$('.back-btn').forEach(b=>b.onclick=()=>showStartStep(b.dataset.back));

let categoriesCache=null;
async function beginGame(payload){
 try{
  const result=await api('/api/scenarios/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const world=toWorldEntry(result.world);
  state.sessionId=result.session_id;
  state.worlds=[world,...state.flavorWorlds.filter(f=>f.id!==world.id)];
  state.worldIndex=0;
  saveSessionToStorage();
  hidePlayHub();
  const opening=payload.custom_text?payload.custom_text:`You arrive in ${world.name}. The story begins...`;
  try{await api('/api/chat/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'assistant',content:opening,session_id:state.sessionId})})}catch{}
  await loadChatHistory();
  updateWorld();renderParty();renderQuests();
  toast(`New game started: ${world.name}`);
 }catch(error){toast(error.message)}
}
$('#startNewGameBtn').onclick=async()=>{
 try{if(!categoriesCache)categoriesCache=await api('/api/scenarios/categories');
  $('#categoryGrid').innerHTML=categoriesCache.map(c=>`<button data-category="${safe(c.key)}"><b>${safe(c.label)}</b><small>${c.scenarios.length} scenario${c.scenarios.length===1?'':'s'}</small></button>`).join('');
  $$('#categoryGrid [data-category]').forEach(btn=>btn.onclick=()=>{
   const category=categoriesCache.find(c=>c.key===btn.dataset.category);state.pendingCategory=category;
   $('#scenarioStepTitle').textContent=`${category.label}: choose a scenario`;
   $('#scenarioGrid').innerHTML=category.scenarios.map(s=>`<button data-scenario="${safe(s.name)}" data-type="${s.type}"><b>${safe(s.name)}</b><small>${s.type==='prebuilt'?'Simulated world':'Preset flavor'}</small></button>`).join('')||'<div class="empty-state">No curated scenarios yet — write your own below.</div>';
   $$('#scenarioGrid [data-scenario]').forEach(sb=>sb.onclick=()=>beginGame({category:category.key,scenario_name:sb.dataset.scenario,scenario_type:sb.dataset.type}));
   showStartStep('scenario');
  });
  showStartStep('category');
 }catch(error){toast(error.message)}
};
$('#customScenarioForm').onsubmit=e=>{e.preventDefault();const text=new FormData(e.currentTarget).get('text')||'';if(!text.trim()){toast('Write a scenario first');return}beginGame({category:state.pendingCategory?.key||'fantasy',scenario_name:text.slice(0,40),scenario_type:'custom',custom_text:text})};

$('#showTemplatesBtn').onclick=async()=>{await loadTemplateList();showStartStep('templates')};
async function loadTemplateList(){
 try{const templates=await api('/api/scenario-templates');$('#templateList').innerHTML=templates.length?templates.map(t=>`<button data-template-id="${t.id}"><b>${safe(t.name)}</b><small>${safe(t.scenario.slice(0,60))}</small></button>`).join(''):'<div class="empty-state">No saved templates yet.</div>';
  $$('#templateList [data-template-id]').forEach(btn=>{
   const template=templates.find(t=>String(t.id)===btn.dataset.templateId);
   btn.onclick=async()=>{try{const rendered=await api('/api/scenario-templates/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:template.name,scenario:template.scenario})});beginGame({category:state.pendingCategory?.key||'fantasy',scenario_name:template.name,scenario_type:'custom',custom_text:rendered.scenario})}catch(error){toast(error.message)}};
  });
 }catch(error){$('#templateList').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
}
$('#newTemplateForm').onsubmit=async e=>{e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());try{await api('/api/scenario-templates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Template saved');formEl.reset();loadTemplateList()}catch(error){toast(error.message)}};

$('#randomScenarioBtn').onclick=async()=>{await rollRandomScenario();showStartStep('random')};
async function rollRandomScenario(){try{const result=await api('/api/random/prompts');state.randomScenarioText=result.scenario;$('#randomScenarioText').textContent=result.scenario}catch(error){$('#randomScenarioText').textContent=error.message}}
$('#rerollScenarioBtn').onclick=rollRandomScenario;
$('#useRandomScenarioBtn').onclick=()=>beginGame({category:state.pendingCategory?.key||'fantasy',scenario_name:'Random Scenario',scenario_type:'custom',custom_text:state.randomScenarioText});

async function loadSavedGame(save){try{await bindSession({sessionId:save.session_id,worldId:save.world_id,characterId:save.character_id});hidePlayHub();toast(`Loaded: ${save.save_name}`)}catch(error){toast(error.message)}}
$('#startLoadGameBtn').onclick=async()=>{
 try{const saves=await api('/api/chat/saves');
  $('#savedGameList').innerHTML=saves.length?saves.map(s=>`<button data-save-id="${s.id}"><b>${safe(s.save_name)}</b><small>${safe(s.character_name||'')} · ${safe((s.created_at||'').slice(0,16))}</small></button>`).join(''):'<div class="empty-state">No saved games yet.</div>';
  $$('#savedGameList [data-save-id]').forEach(btn=>{const save=saves.find(s=>String(s.id)===btn.dataset.saveId);btn.onclick=()=>loadSavedGame(save)});
  showStartStep('load');
 }catch(error){toast(error.message)}
};

$$('[data-scale]').forEach(b=>b.onclick=()=>setScale(b.dataset.scale));
$$('.detail-tabs button').forEach(b=>b.onclick=()=>{$$('.detail-tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');showPanel(b.dataset.panel)});
$$('.dock-head button').forEach(b=>b.onclick=()=>{$$('.dock-head button').forEach(x=>x.classList.remove('active'));b.classList.add('active');renderActions(b.dataset.filter)});
$('#map').addEventListener('click',e=>{if(e.target.closest('button'))return;const r=e.currentTarget.getBoundingClientRect();move((e.clientX-r.left)/r.width*100,(e.clientY-r.top)/r.height*100)});
document.addEventListener('keydown',e=>{const active=document.activeElement;if(active&&active.tagName==='INPUT')return;const keys={w:[0,-3],ArrowUp:[0,-3],s:[0,3],ArrowDown:[0,3],a:[-3,0],ArrowLeft:[-3,0],d:[3,0],ArrowRight:[3,0]};if(keys[e.key]){e.preventDefault();move(state.x+keys[e.key][0],state.y+keys[e.key][1])}if('1234'.includes(e.key))setScale(['local','area','world','universe'][+e.key-1])});
$('#portal').onclick=crossPortal;
$('#zoomIn').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.min(140,state.zoom+10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#zoomOut').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.max(70,state.zoom-10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#saveBtn').onclick=async()=>{
 saveSessionToStorage();
 const world=state.worlds[state.worldIndex];
 try{
  await api('/api/chat/saves',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId,save_name:`${world?.name||'Unknown'} - Level ${state.sheet?.calc_lv||1}`,character_name:state.sheet?.name||'',world_id:world?.id,character_id:state.characterId})});
  toast('Campaign and story saved');
 }catch(error){toast(`Saved on this device only: ${error.message}`)}
};
$('#journalBtn').onclick=()=>toast('Quest journal opened');
function playerContextLine(){
 const world=state.worlds[state.worldIndex]; const s=state.sheet;
 const bits=[`World: ${world?.name}`,`Reality: ${world?.reality_type}`,`Location: ${world?.place}`];
 if(s){
  bits.push(`Player character: ${s.name}, Level ${s.calc_lv||s.level||1} ${s.race||''} ${s.profession||''}`.trim());
  const equipped=(state.inventory.items||[]).filter(i=>i.equip_slot).map(i=>i.item_name);
  if(equipped.length)bits.push(`Equipped: ${equipped.join(', ')}`);
  if(s.reality_signature?.universe_tag)bits.push(`Reality signature: ${s.reality_signature.universe_tag} (${s.reality_signature.reality_type})`);
 }
 if(state.quests.length)bits.push(`Active quests: ${state.quests.map(q=>q.title).join('; ')}`);
 bits.push(`Party: ${party.map(p=>p.name).join(', ')}`);
 return `[${bits.join(' | ')}]`;
}
let chatAudio=null;
function stopChatAudio(){if(chatAudio){chatAudio.pause();chatAudio=null}$('#chatAvatar').classList.remove('speaking')}
async function speakReply(text){
 if(!state.voiceEnabled||!text)return;
 stopChatAudio();
 try{
  const result=await api('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:text})});
  if(!result.url)return;
  chatAudio=new Audio(result.url);
  $('#chatAvatar').classList.add('speaking');
  chatAudio.onended=chatAudio.onerror=()=>{$('#chatAvatar').classList.remove('speaking');chatAudio=null};
  await chatAudio.play();
 }catch{$('#chatAvatar').classList.remove('speaking')}
}
$('#voiceToggleBtn').onclick=()=>{
 state.voiceEnabled=!state.voiceEnabled;
 localStorage.setItem('companion-voice',state.voiceEnabled);
 $('#voiceToggleBtn').classList.toggle('active',state.voiceEnabled);
 $('#voiceToggleBtn').innerHTML=state.voiceEnabled?'🔊 Voice on':'🔈 Voice off';
 if(!state.voiceEnabled)stopChatAudio();
};
$('#voiceToggleBtn').classList.toggle('active',state.voiceEnabled);
$('#voiceToggleBtn').innerHTML=state.voiceEnabled?'🔊 Voice on':'🔈 Voice off';

// Chat voice INPUT: the browser's own Web Speech API (Chrome/Edge). No
// server round-trip and no Python dependency -- Firefox has no
// implementation, so the mic button just stays hidden there.
const SpeechRecognitionApi=window.SpeechRecognition||window.webkitSpeechRecognition;
let speechRecognizer=null,isListening=false;
if(SpeechRecognitionApi){
 $('#micBtn').hidden=false;
 speechRecognizer=new SpeechRecognitionApi();
 speechRecognizer.continuous=false;speechRecognizer.interimResults=false;speechRecognizer.lang='en-US';
 speechRecognizer.onresult=e=>{
  const transcript=e.results[0][0].transcript;
  $('#chatInput').value=transcript;
  $('#chatForm').requestSubmit();
 };
 speechRecognizer.onend=()=>{isListening=false;$('#micBtn').classList.remove('listening')};
 speechRecognizer.onerror=()=>{isListening=false;$('#micBtn').classList.remove('listening')};
 $('#micBtn').onclick=()=>{
  if(isListening){speechRecognizer.stop();return}
  stopChatAudio();
  isListening=true;$('#micBtn').classList.add('listening');
  try{speechRecognizer.start()}catch{isListening=false;$('#micBtn').classList.remove('listening')}
 };
}
$('#chatForm').onsubmit=async e=>{e.preventDefault();const input=$('#chatInput'),msg=input.value.trim();if(!msg)return;$('#chatLog').insertAdjacentHTML('beforeend',`<p class="player"><b>YOU</b>${safe(msg)}</p>`);input.value='';$('#aiStatus').textContent='Thinking...';try{const world=state.worlds[state.worldIndex];const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:msg,extra_context:playerContextLine(),session_id:state.sessionId,world_id:world?.id,user_name:'Player',character_name:'Worldweaver',participants:['Worldweaver'],temperature:.75})});const data=await r.json();if(!r.ok)throw new Error(data.detail||'Local model unavailable');$('#chatLog').insertAdjacentHTML('beforeend',`<p class="gm"><b>WORLDWEAVER</b>${safe(data.reply)}</p>`);$('#aiStatus').textContent='LM Studio connected';speakReply(data.reply)}catch(error){$('#chatLog').insertAdjacentHTML('beforeend',`<p class="gm"><b>WORLDWEAVER</b>${safe(error.message||'The local storyteller cannot be reached.')}</p>`);$('#aiStatus').textContent='Start LM Studio on port 1234'}$('#chatLog').scrollTop=$('#chatLog').scrollHeight};

// ═══ AI Companion-style workspace navigation and studios ═══
function openView(name){$$('.app-view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.side-nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));if(name==='play'){$('#playHub').hidden=state.hasActiveGame;$('#gameArea').hidden=!state.hasActiveGame}if(name==='characters')loadCharacterStudio();if(name==='explore')loadExplore();if(name==='worlds')loadWorlds();if(name==='knowledge'){loadLore();loadKnowledgeDocs()}if(name==='media')loadMediaTab();if(name==='settings'){checkModelStatus();loadSettingsExtras()}}
$$('.side-nav button').forEach(button=>button.onclick=()=>openView(button.dataset.view));

let studioOptions={};
function fillSelect(selector,values){const el=$(selector);if(!el)return;const list=Array.isArray(values)?values:Object.keys(values||{});el.innerHTML=list.map(value=>`<option value="${safe(value)}">${safe(value)}</option>`).join('')}
async function loadCharacterStudio(){try{if(!Object.keys(studioOptions).length){studioOptions=await api('/api/options');fillSelect('#raceSelect',studioOptions.races);fillSelect('#professionSelect',studioOptions.professions);fillSelect('#backgroundSelect',studioOptions.backgrounds);fillSelect('#alignmentSelect',studioOptions.alignments)}const characters=await api('/api/characters');$('#characterLibrary').innerHTML=characters.length?characters.map(c=>`<article class="entity-card"><span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span><div><b>${safe(c.name)}</b><small>${safe(c.race||'Unknown ancestry')} · ${safe(c.profession||'Adventurer')}</small></div><em>LV ${safe(c.level||1)}</em></article>`).join(''):'<div class="empty-state">No saved characters yet. Create your first companion.</div>'}catch(error){$('#characterLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#characterForm').onsubmit=async event=>{
 event.preventDefault();
 const formEl=event.currentTarget; // native currentTarget is cleared once we `await`, so capture it now
 const form=new FormData(formEl);
 const payload=Object.fromEntries(form.entries());
 payload.level=Number(payload.level||1);
 payload.origin_world=state.worlds[state.worldIndex]?.name||'Aethoria Prime';
 payload.scenario=`Origin reality: ${payload.scenario}`;
 try{
  const created=await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  toast(`${payload.name} saved`);
  formEl.reset();
  await loadCharacterStudio();
  // Character creation is a single shared flow: the same form used here in
  // the AI Companion library also becomes the Play view's active adventurer
  // whenever Play doesn't have one bound yet.
  if(!state.characterId&&created?.id){
   state.characterId=created.id;
   await refreshCharacterState();
   renderParty();renderQuests();showPanel('character');
   toast(`${payload.name} is now your active adventurer — switch to Play to begin`);
  }
 }catch(error){toast(error.message)}
};
$('#randomCharacter').onclick=async()=>{try{const {character}=await api('/api/characters/random',{method:'POST'});const form=$('#characterForm');['name','race','profession','background','alignment','backstory','goals'].forEach(key=>{if(form.elements[key]&&character[key]!=null)form.elements[key].value=Array.isArray(character[key])?character[key].join(', '):character[key]});toast('Random character generated')}catch(error){toast(error.message)}};
$('#refreshCharacters').onclick=loadCharacterStudio;$('#newCharacterBtn').onclick=()=>{$('#characterForm').scrollIntoView({behavior:'smooth'});$('#characterForm').elements.name.focus()};

async function loadWorlds(){try{const items=await api('/api/worlds');$('#worldLibrary').innerHTML=items.length?items.map(w=>`<article class="entity-card"><span class="entity-avatar">◎</span><div><b>${safe(w.name)}</b><small>${safe(w.space_alignment||'multiverse')} · ${safe(w.reality_type||'Prime Reality')} · Magic ${safe(w.ratings?.magic ?? w.magic_level)}</small></div><em>${safe(w.time_of_day||'Active')}</em></article>`).join(''):'<div class="empty-state">No database worlds yet. The four play-map realities remain available.</div>'}catch(error){$('#worldLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#worldForm').onsubmit=async event=>{event.preventDefault();const formEl=event.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());payload.num_locs=Number(payload.num_locs||8);try{await api('/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`${payload.name} created`);formEl.reset();loadWorlds()}catch(error){toast(error.message)}};$('#refreshWorlds').onclick=loadWorlds;

async function loadLore(){try{const items=await api('/api/knowledge/lorebook');$('#loreLibrary').innerHTML=items.length?items.map(item=>`<article class="entity-card"><span class="entity-avatar">◇</span><div><b>${safe(item.title)}</b><small>${safe((item.content||'').slice(0,90))}</small></div><em>${item.enabled===0?'Off':'Active'}</em></article>`).join(''):'<div class="empty-state">No lorebook entries. Add rules, locations, and secrets here.</div>'}catch(error){$('#loreLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#loreForm').onsubmit=async event=>{event.preventDefault();const formEl=event.currentTarget;const raw=Object.fromEntries(new FormData(formEl).entries());const payload={title:raw.title,content:raw.content,keywords:raw.keywords.split(',').map(x=>x.trim()).filter(Boolean),world_id:0,always_active:true};try{await api('/api/knowledge/lorebook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Lore saved');formEl.reset();loadLore()}catch(error){toast(error.message)}};$('#refreshLore').onclick=loadLore;

async function checkModelStatus(){const badge=$('#modelBadge');badge.textContent='Checking';badge.classList.remove('good');try{const result=await api('/api/settings/model');badge.textContent='Configured';badge.classList.add('good');$('#activeModel').textContent=result.active_model||'LM Studio model'}catch{badge.textContent='Offline';$('#activeModel').textContent='Start LM Studio on port 1234'}}
$('#checkModel').onclick=checkModelStatus;$('#reducedMotion').onchange=e=>{document.body.classList.toggle('reduced-motion',e.target.checked);localStorage.setItem('reduced-motion',e.target.checked)};$('#compactMode').onchange=e=>{document.body.classList.toggle('compact',e.target.checked);localStorage.setItem('compact-mode',e.target.checked)};$('#reducedMotion').checked=localStorage.getItem('reduced-motion')==='true';$('#compactMode').checked=localStorage.getItem('compact-mode')==='true';document.body.classList.toggle('reduced-motion',$('#reducedMotion').checked);document.body.classList.toggle('compact',$('#compactMode').checked);$$('[data-feature]').forEach(button=>button.onclick=()=>toast(`${button.dataset.feature} tools are connected to the local media API`));

// ═══ Explore: built-in character library + web search/import ═══
let libraryRacesLoaded=false;
async function loadExplore(){
 if(!libraryRacesLoaded){try{const options=await api('/api/options');fillSelect('#libraryRaceSelect',['All',...Object.keys(options.races||{})]);libraryRacesLoaded=true}catch{}}
 await searchLibrary();
}
function renderExploreCards(list,container,importHandler){
 if(!list.length){container.innerHTML='<div class="empty-state">No results.</div>';return}
 container.innerHTML=list.map((c,i)=>`<article class="entity-card"><span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span><div><b>${safe(c.name||'Unknown')}</b><small>${safe(c.race||'')} ${c.profession?'· '+safe(c.profession):''}</small></div><button data-import-index="${i}" class="ghost">Import</button></article>`).join('');
 [...container.querySelectorAll('[data-import-index]')].forEach(btn=>btn.onclick=()=>importHandler(list[+btn.dataset.importIndex],btn));
}
let lastLibraryResults=[];
async function searchLibrary(){
 const form=$('#libraryFilterForm');
 const payload=Object.fromEntries(new FormData(form).entries());
 try{
  const result=await api(`/api/explore/library?query=${encodeURIComponent(payload.query||'')}&race=${encodeURIComponent(payload.race||'All')}&limit=30`);
  lastLibraryResults=result.characters||[];
  $('#libraryCount').textContent=`${result.filtered} / ${result.total}`;
  renderExploreCards(lastLibraryResults,$('#libraryResults'),async(character,btn)=>{btn.disabled=true;try{await api('/api/explore/library/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character})});btn.textContent='Imported';toast(`${character.name} imported`)}catch(error){toast(error.message);btn.disabled=false}});
 }catch(error){$('#libraryResults').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
}
$('#libraryFilterForm').onsubmit=e=>{e.preventDefault();searchLibrary()};
$('#importAllBtn').onclick=async()=>{if(!lastLibraryResults.length){toast('Nothing to import');return}try{const result=await api('/api/explore/library/import-all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({characters:lastLibraryResults})});toast(`${result.imported} characters imported`)}catch(error){toast(error.message)}};
$('#webSearchForm').onsubmit=async e=>{
 e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());
 const container=$('#webSearchResults');container.innerHTML='<div class="empty-state">Searching…</div>';
 try{
  const {results,error}=await api('/api/explore/character-search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:payload.query})});
  if(error){container.innerHTML=`<div class="empty-state">${safe(error)}</div>`;return}
  renderExploreCards(results||[],container,async(result,btn)=>{btn.disabled=true;try{await api('/api/explore/character-search/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({result})});btn.textContent='Imported';toast(`${result.name||'Character'} imported`)}catch(error){toast(error.message);btn.disabled=false}});
 }catch(error){container.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};

// ═══ Explore: import a full character package (JSON / link / text) ═══
// Brings in whichever of character, chat history, memory, and
// achievements/events the source actually contains, reusing the existing
// single-purpose endpoints rather than inventing one monolithic import.
$$('[data-import-mode]').forEach(btn=>btn.onclick=()=>{
 $$('[data-import-mode]').forEach(b=>b.classList.toggle('active',b===btn));
 $$('.import-mode').forEach(panel=>panel.hidden=panel.id!==`importMode-${btn.dataset.importMode}`);
});
$('#importJsonFile').onchange=e=>{const file=e.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=()=>{$('#importJsonText').value=reader.result};reader.readAsText(file)};

async function importCharacterIfPresent(character){
 if(!character||!character.name)return null;
 const result=await api('/api/characters/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character})});
 return result.id;
}
async function inferAndImportCharacters(messages,scenario=''){
 if(!messages||!messages.length)return[];
 try{
  const {characters}=await api('/api/chat/import/infer-characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages,scenario})});
  const imported=[];
  for(const character of (characters||[]).slice(0,3)){const id=await importCharacterIfPresent(character);if(id)imported.push({id,name:character.name})}
  return imported;
 }catch{return[]}
}
async function loadMessagesIntoNewSession(messages){
 if(!messages||!messages.length)return{sessionId:null,count:0};
 const sessionId=`import-${Date.now().toString(36)}`;
 const result=await api('/api/chat/import/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages,session_id:sessionId})});
 return{sessionId,count:result.saved||0};
}
async function importMemoryFacts(memory,characterName=''){
 let count=0;
 for(const item of (memory||[]).slice(0,50)){
  const fact=typeof item==='string'?item:(item.fact||item.content||'');
  if(!fact)continue;
  try{await api('/api/memory/facts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fact,source:'import',character_name:(item.character_name||characterName||'')})});count++}catch{}
 }
 return count;
}
async function importAchievements(items,characterName=''){
 let count=0;
 for(const item of (items||[]).slice(0,50)){
  const title=item.title||item.name||(typeof item==='string'?item:'');
  if(!title)continue;
  try{await api('/api/media/achievements',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,description:item.description||'',character_name:item.character_name||characterName||'Unassigned'})});count++}catch{}
 }
 return count;
}
function renderImportSummary({characterName,messageCount,memoryCount,achievementCount,sessionId}){
 const parts=[];
 parts.push(characterName?`Character: ${characterName}`:'No character imported');
 if(messageCount)parts.push(`${messageCount} chat messages loaded${sessionId?` (session ${sessionId})`:''}`);
 if(memoryCount)parts.push(`${memoryCount} memory facts stored`);
 if(achievementCount)parts.push(`${achievementCount} achievements/events added`);
 $('#importResult').innerHTML=`<div class="entity-card" style="grid-template-columns:1fr"><div><b>Import complete</b><small>${parts.map(safe).join(' · ')}</small></div></div>`;
}

$('#importJsonBtn').onclick=async()=>{
 const raw=$('#importJsonText').value.trim();
 if(!raw){toast('Paste or upload JSON first');return}
 let data;
 try{data=JSON.parse(raw)}catch{toast('Invalid JSON');return}
 try{
  let character=null,messages=[],memory=[],achievements=[];
  if(Array.isArray(data)){messages=data}
  else if(data.character||data.messages||data.memory||data.achievements||data.events){
   character=data.character||null;messages=data.messages||[];memory=data.memory||[];achievements=data.achievements||data.events||[];
  }else if(data.name){character=data}
  let characterId=await importCharacterIfPresent(character);
  let characterName=character?.name||'';
  if(!characterId&&messages.length){const inferred=await inferAndImportCharacters(messages);if(inferred.length){characterId=inferred[0].id;characterName=inferred[0].name}}
  const {sessionId,count}=await loadMessagesIntoNewSession(messages);
  const memoryCount=await importMemoryFacts(memory,characterName);
  const achievementCount=await importAchievements(achievements,characterName);
  renderImportSummary({characterName,messageCount:count,memoryCount,achievementCount,sessionId});
  if(characterId){toast(`${characterName} imported`);loadCharacterStudio()}else toast('Import finished');
 }catch(error){toast(error.message)}
};

async function importFromMessages(messages,sourceLabel){
 const inferred=await inferAndImportCharacters(messages);
 const {sessionId,count}=await loadMessagesIntoNewSession(messages);
 const characterName=inferred[0]?.name||'';
 let memoryCount=0;
 if(messages.length)memoryCount=await importMemoryFacts([{fact:`Imported ${messages.length} messages from ${sourceLabel}.`}],characterName);
 renderImportSummary({characterName,messageCount:count,memoryCount,achievementCount:0,sessionId});
 if(characterName){toast(`${characterName} imported`);loadCharacterStudio()}else toast(`${messages.length} messages imported`);
}
$('#importLinkBtn').onclick=async()=>{
 const url=$('#importLinkInput').value.trim();
 if(!url){toast('Enter a link first');return}
 try{const {messages}=await api('/api/chat/import/url',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});await importFromMessages(messages||[],url)}catch(error){toast(error.message)}
};
$('#importTextBtn').onclick=async()=>{
 const text=$('#importTextInput').value.trim();
 if(!text){toast('Paste some text first');return}
 try{
  const file=new File([text],'pasted.txt',{type:'text/plain'});
  const formData=new FormData();formData.append('file',file);
  const {messages}=await api('/api/chat/import/file',{method:'POST',body:formData});
  await importFromMessages(messages||[],'pasted text');
 }catch(error){toast(error.message)}
};

// ═══ Knowledge: indexed documents (SRD, options, uploads) ═══
async function loadKnowledgeDocs(){
 try{const docs=await api('/api/knowledge/documents');$('#knowledgeDocs').innerHTML=docs.length?docs.map(d=>`<article class="entity-card"><span class="entity-avatar">▤</span><div><b>${safe(d.title||d.path)}</b><small>${safe(d.path)}</small></div><button data-doc-id="${d.id}" class="ghost">Remove</button></article>`).join(''):'<div class="empty-state">Nothing indexed yet — reindex the bundled knowledge folder or upload a document.</div>';
  $$('[data-doc-id]').forEach(btn=>btn.onclick=async()=>{try{await api(`/api/knowledge/documents/${btn.dataset.docId}`,{method:'DELETE'});loadKnowledgeDocs()}catch(error){toast(error.message)}});
 }catch(error){$('#knowledgeDocs').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
}
$('#reindexKnowledge').onclick=async()=>{try{const result=await api('/api/knowledge/index',{method:'POST'});toast(`${result.indexed} documents indexed`);loadKnowledgeDocs()}catch(error){toast(error.message)}};
$('#knowledgeUpload').onchange=async e=>{const file=e.target.files[0];if(!file)return;const formData=new FormData();formData.append('file',file);try{await api('/api/knowledge/index/file',{method:'POST',body:formData});toast(`${file.name} indexed`);loadKnowledgeDocs()}catch(error){toast(error.message)}e.target.value=''};
$('#knowledgeSearchForm').onsubmit=async e=>{
 e.preventDefault();const payload=Object.fromEntries(new FormData(e.currentTarget).entries());
 try{const results=await api(`/api/knowledge/search?query=${encodeURIComponent(payload.query||'')}`);$('#knowledgeSearchResults').innerHTML=results.length?results.map(r=>`<article class="entity-card"><span class="entity-avatar">◇</span><div><b>${safe(r.title||'Match')}</b><small>${safe((r.snippet||r.content||'').slice(0,120))}</small></div></article>`).join(''):'<div class="empty-state">No matches.</div>'}catch(error){$('#knowledgeSearchResults').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};

// ═══ Media: generation, gallery, voice, achievements ═══
let mediaStylesLoaded=false;
async function loadMediaTab(){
 if(!mediaStylesLoaded){
  try{
   const styles=await api('/api/media/image-styles');
   fillSelect('#mediaStyleSelect',styles);fillSelect('#animationStyleSelect',styles);fillSelect('#videoStyleSelect',styles);
   fillSelect('#animationEffectSelect',await api('/api/media/animation-effects'));
   mediaStylesLoaded=true;
  }catch{}
 }
 loadGallery();loadAchievements();
}
$('#mediaImageForm').onsubmit=async e=>{
 e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());
 const preview=$('#mediaImagePreview');preview.innerHTML='<div class="empty-state">Generating…</div>';
 try{
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:payload.prompt,style:payload.style,save_to_chat:false})});
  preview.innerHTML=`<img src="${safe(result.url)}" alt="Generated image" style="max-width:100%;border:1px solid var(--line);margin-top:8px"><div class="form-actions" style="margin-top:8px"><button id="saveToGalleryBtn" class="ghost">＋ Save to gallery</button></div>`;
  $('#saveToGalleryBtn').onclick=async()=>{try{await api('/api/media/gallery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({media_type:'image',title:payload.prompt.slice(0,60),file_path:result.path||result.url,character_name:state.sheet?.name||''})});toast('Saved to gallery');loadGallery()}catch(error){toast(error.message)}};
 }catch(error){preview.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};
$('#voiceForm').onsubmit=async e=>{
 e.preventDefault();const payload=Object.fromEntries(new FormData(e.currentTarget).entries());
 const player=$('#voicePlayer');player.innerHTML='<div class="empty-state">Generating voice…</div>';
 try{
  const result=await api('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:payload.content})});
  player.innerHTML=result.url?`<audio controls src="${safe(result.url)}" style="width:100%;margin-top:8px"></audio>`:'<div class="empty-state">TTS engine unavailable on this install (needs edge-tts).</div>';
 }catch(error){player.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};
$('#mediaAnimationForm').onsubmit=async e=>{
 e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());
 const preview=$('#mediaAnimationPreview');preview.innerHTML='<div class="empty-state">Generating image and rendering animation…</div>';
 try{
  const result=await api('/api/media/text-to-animation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:payload.prompt,style:payload.style,effect:payload.effect,save_to_chat:false})});
  preview.innerHTML=`<video controls loop src="${safe(result.video_url)}" style="max-width:100%;border:1px solid var(--line);margin-top:8px"></video><div class="form-actions" style="margin-top:8px"><button id="saveAnimToGalleryBtn" class="ghost">＋ Save to gallery</button></div>`;
  $('#saveAnimToGalleryBtn').onclick=async()=>{try{await api('/api/media/gallery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({media_type:'video',title:payload.prompt.slice(0,60),file_path:result.video_path||result.video_url,character_name:state.sheet?.name||''})});toast('Saved to gallery');loadGallery()}catch(error){toast(error.message)}};
 }catch(error){preview.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};
$('#mediaVideoForm').onsubmit=async e=>{
 e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());
 const prompts=(payload.prompts||'').split('\n').map(s=>s.trim()).filter(Boolean);
 const preview=$('#mediaVideoPreview');
 if(!prompts.length){preview.innerHTML='<div class="empty-state">Write at least one scene.</div>';return}
 preview.innerHTML=`<div class="empty-state">Rendering ${prompts.length} scene${prompts.length===1?'':'s'}…</div>`;
 try{
  const result=await api('/api/media/text-to-video',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompts,style:payload.style,save_to_chat:false})});
  preview.innerHTML=`<video controls loop src="${safe(result.video_url)}" style="max-width:100%;border:1px solid var(--line);margin-top:8px"></video><div class="form-actions" style="margin-top:8px"><button id="saveVideoToGalleryBtn" class="ghost">＋ Save to gallery</button></div>`;
  $('#saveVideoToGalleryBtn').onclick=async()=>{try{await api('/api/media/gallery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({media_type:'video',title:prompts[0].slice(0,60),file_path:result.video_path||result.video_url,character_name:state.sheet?.name||''})});toast('Saved to gallery');loadGallery()}catch(error){toast(error.message)}};
 }catch(error){preview.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
};
const MEDIA_TYPE_ICONS={image:'▧',video:'🎬',voice:'♪'};
async function loadGallery(){try{const items=await api('/api/media/gallery?limit=30');$('#mediaGallery').innerHTML=items.length?items.map(m=>`<article class="entity-card"><span class="entity-avatar">${MEDIA_TYPE_ICONS[m.media_type]||'♪'}</span><div><b>${safe(m.title||'Untitled')}</b><small>${safe(m.character_name||'')}</small></div><button data-media-id="${m.id}" class="ghost">✕</button></article>`).join(''):'<div class="empty-state">No saved media yet.</div>';$$('[data-media-id]').forEach(btn=>btn.onclick=async()=>{try{await api(`/api/media/gallery/${btn.dataset.mediaId}`,{method:'DELETE'});loadGallery()}catch(error){toast(error.message)}})}catch(error){$('#mediaGallery').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#refreshGallery').onclick=loadGallery;
async function loadAchievements(){try{const items=await api('/api/media/achievements');$('#achievementList').innerHTML=items.length?items.map(a=>`<article class="entity-card"><span class="entity-avatar">★</span><div><b>${safe(a.title)}</b><small>${safe(a.description||'')}</small></div></article>`).join(''):'<div class="empty-state">No achievements yet.</div>'}catch(error){$('#achievementList').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#refreshAchievements').onclick=loadAchievements;
$('#achievementForm').onsubmit=async e=>{e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());payload.character_name=state.sheet?.name||'';try{await api('/api/media/achievements',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Achievement added');formEl.reset();loadAchievements()}catch(error){toast(error.message)}};

// ═══ Settings: system prompt, backups, maintenance, health ═══
async function loadSettingsExtras(){
 try{const preamble=await api('/api/settings/system-preamble');$('#preambleInput').value=preamble.value||''}catch{}
 try{const model=await api('/api/settings/model');$('#modelIdInput').value=model.active_model||''}catch{}
 loadBackups();loadHealth();
}
$('#modelForm').onsubmit=async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(e.currentTarget).entries());try{await api('/api/settings/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:'active_llm_model',value:payload.value})});toast('Model id saved');checkModelStatus()}catch(error){toast(error.message)}};
$('#preambleForm').onsubmit=async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(e.currentTarget).entries());try{await api('/api/settings/system-preamble',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:'system_preamble',value:payload.value})});toast('System preamble saved')}catch(error){toast(error.message)}};
async function loadBackups(){try{const items=await api('/api/settings/backups');$('#backupList').innerHTML=items.length?items.map(b=>`<article class="entity-card"><span class="entity-avatar">⛁</span><div><b>${safe(b.name||b.path||'Backup')}</b><small>${safe(b.created_at||'')}</small></div></article>`).join(''):'<div class="empty-state">No backups yet.</div>'}catch(error){$('#backupList').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#createBackup').onclick=async()=>{try{const result=await api('/api/settings/backup',{method:'POST'});$('#backupStatus').textContent=`Saved: ${result.path}`;toast('Backup created');loadBackups()}catch(error){toast(error.message)}};
$('#checkIntegrity').onclick=async()=>{try{const result=await api('/api/settings/db-integrity');const ok=result.result?.length===1&&result.result[0]==='ok';$('#integrityStatus').textContent=ok?'OK':(result.result||[]).join(', ');toast(ok?'Database OK':'Integrity issues found')}catch(error){toast(error.message)}};
$('#runImportTest').onclick=async()=>{try{const result=await api('/api/settings/import-test',{method:'POST'});$('#importTestStatus').textContent=result.ok?`${result.passed.length} modules OK`:`${result.failures.length} failures`;toast(result.ok?'All modules import cleanly':'Some modules failed to import')}catch(error){toast(error.message)}};
async function loadHealth(){try{const {counts}=await api('/api/settings/dashboard');$('#systemHealth').innerHTML=Object.entries(counts).map(([table,count])=>`<span>${safe(table)} <i class="good">${safe(count)}</i></span>`).join('')}catch(error){$('#systemHealth').innerHTML=`<span>Health check failed <i>${safe(error.message)}</i></span>`}}
$('#refreshHealth').onclick=loadHealth;

// ═══ Tactical combat: turn-based grid battle with obstacles ═══
let combatState=null, combatReachable=new Set(), combatAttackable={}, combatSpellTargets={};
const POWER_ATTACK_FEATS=new Set(['Great Weapon Master','Sharpshooter']);
function tileKey(x,y){return `${x},${y}`}
function lineClear(obstacleSet,x1,y1,x2,y2){
 const steps=Math.max(Math.abs(x2-x1),Math.abs(y2-y1));
 if(steps<=1)return true;
 for(let i=1;i<steps;i++){const px=Math.round(x1+(x2-x1)*i/steps),py=Math.round(y1+(y2-y1)*i/steps);if(obstacleSet.has(tileKey(px,py)))return false}
 return true;
}
function weaponRangeFor(weaponName,tier){
 const weapon=weaponName?state.dndWeapons[weaponName]:null;
 if(weapon){
  if(/Ranged/.test(weapon.category))return 4;
  if((weapon.properties||[]).includes('reach'))return 2;
  return 1;
 }
 const t=tier??2;
 return t<=3?1:(t<=6?3:5);
}
function selectedSpell(){
 const select=$('#combatSpellSelect');
 const name=select?select.value:'';
 return name?{name,data:state.allSpells[name]}:null;
}
async function startCombat(){
 if(!state.characterId){goCreateCharacter();return}
 try{
  const world=state.worlds[state.worldIndex];
  const result=await api('/api/combat/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId,world_id:world?.id,character_id:state.characterId})});
  openCombat(result);
 }catch(error){toast(error.message)}
}
function openCombat(encounter){combatState=encounter;$('#combatOverlay').classList.add('open');renderCombat()}
function closeCombat(){$('#combatOverlay').classList.remove('open');combatState=null}
function computeCombatAffordances(){
 combatReachable=new Set();combatAttackable={};combatSpellTargets={};
 if(!combatState||combatState.status!=='active')return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 if(!human||combatState.current_unit_id!==human.id)return;
 const obstacles=new Set(combatState.obstacles.map(([x,y])=>tileKey(x,y)));
 const occupied=new Set(combatState.units.filter(u=>u.is_active&&u.id!==human.id).map(u=>tileKey(u.x,u.y)));
 const visited=new Map();visited.set(tileKey(human.x,human.y),0);
 const queue=[[human.x,human.y]];
 while(queue.length){
  const [cx,cy]=queue.shift();const d=visited.get(tileKey(cx,cy));
  if(d>=3)continue;
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++){
   if(dx===0&&dy===0)continue;
   const nx=cx+dx,ny=cy+dy;
   if(nx<0||ny<0||nx>=combatState.grid_width||ny>=combatState.grid_height)continue;
   const key=tileKey(nx,ny);
   if(obstacles.has(key)||occupied.has(key)||visited.has(key))continue;
   visited.set(key,d+1);queue.push([nx,ny]);
  }
 }
 visited.delete(tileKey(human.x,human.y));
 const spell=selectedSpell();
 if(spell&&spell.data){
  combatReachable=new Set();
  if(spell.data.effect_type==='attack'||spell.data.effect_type==='save'){
   for(const u of combatState.units) if(u.unit_type!==human.unit_type&&u.is_active) combatSpellTargets[tileKey(u.x,u.y)]=u.id;
  }else if(spell.data.effect_type==='heal'){
   for(const u of combatState.units) if(u.unit_type===human.unit_type&&u.is_active) combatSpellTargets[tileKey(u.x,u.y)]=u.id;
  }
  return;
 }
 combatReachable=new Set(visited.keys());
 const range=weaponRangeFor(human.stats.weapon_name,human.stats.weapon_tier);
 for(const u of combatState.units){
  if(u.unit_type==='enemy'&&u.is_active){
   const dist=Math.max(Math.abs(u.x-human.x),Math.abs(u.y-human.y));
   if(dist<=range&&(range<=1||lineClear(obstacles,human.x,human.y,u.x,u.y)))combatAttackable[tileKey(u.x,u.y)]=u.id;
  }
 }
}
function renderCombat(){
 if(!combatState)return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 const isHumanTurn=combatState.status==='active'&&human&&combatState.current_unit_id===human.id;
 const spellSelect=$('#combatSpellSelect');
 const prevSpell=spellSelect?spellSelect.value:'';
 const knownSpells=(human?.stats?.known_spells)||[];
 spellSelect.innerHTML=`<option value="">⚔ Weapon attack</option>${knownSpells.map(name=>{
  const sp=state.allSpells[name];
  const label=sp?`${name} (${sp.level===0?'Cantrip':'Lv'+sp.level})`:name;
  return `<option value="${safe(name)}">${safe(label)}</option>`;
 }).join('')}`;
 if(knownSpells.includes(prevSpell))spellSelect.value=prevSpell;
 spellSelect.disabled=!isHumanTurn;
 computeCombatAffordances();
 const obstacleSet=new Set(combatState.obstacles.map(([x,y])=>tileKey(x,y)));
 const unitByTile={};
 combatState.units.forEach(u=>{if(u.is_active)unitByTile[tileKey(u.x,u.y)]=u});
 let html='';
 for(let y=0;y<combatState.grid_height;y++){
  for(let x=0;x<combatState.grid_width;x++){
   const key=tileKey(x,y);
   const classes=['combat-tile'];
   if(obstacleSet.has(key))classes.push('obstacle');
   if(combatReachable.has(key))classes.push('reachable');
   if(key in combatAttackable)classes.push('attackable');
   if(key in combatSpellTargets)classes.push('attackable','spell-target');
   const unit=unitByTile[key];
   let inner='';
   if(unit){
    const side=unit.unit_type==='player'?'side-player':'side-enemy';
    const current=combatState.current_unit_id===unit.id?'current-turn':'';
    const pct=Math.max(0,Math.round(unit.hp/unit.max_hp*100));
    inner=`<div class="combat-unit ${side} ${current}" title="${safe(unit.unit_name)} (${unit.hp}/${unit.max_hp})">${safe(unit.unit_name.slice(0,2).toUpperCase())}<div class="hp-bar"><i style="width:${pct}%"></i></div></div>`;
   }
   html+=`<div class="${classes.join(' ')}" data-x="${x}" data-y="${y}">${inner}</div>`;
  }
 }
 $('#combatBoard').innerHTML=html;
 $$('#combatBoard .combat-tile').forEach(tile=>tile.onclick=()=>onCombatTileClick(+tile.dataset.x,+tile.dataset.y));
 $('#combatTurnList').innerHTML=combatState.turn_order.map(uid=>combatState.units.find(u=>u.id===uid)).filter(Boolean).map(u=>{
  const side=u.unit_type==='player'?'side-player':'side-enemy';
  const current=combatState.current_unit_id===u.id?'current':'';
  return `<div class="combat-turn-card ${side} ${current}"><div class="portrait combat-unit ${side}">${safe(u.unit_name.slice(0,2).toUpperCase())}</div><div><strong>${safe(u.unit_name)}</strong><small>${u.is_active?`${u.hp}/${u.max_hp} HP`:'Defeated'}</small></div></div>`;
 }).join('');
 $('#combatLog').innerHTML=(combatState.log||[]).slice().reverse().map(line=>`<div>${safe(line)}</div>`).join('');
 $('#combatRoundInfo').textContent=`Round ${combatState.round_number}`;
 $('#combatEndTurnBtn').disabled=!isHumanTurn;
 const spell=selectedSpell();
 const canPowerAttack=isHumanTurn&&!spell&&(human.stats.feats||[]).some(f=>POWER_ATTACK_FEATS.has(f));
 $('#combatPowerAttackLabel').hidden=!canPowerAttack;
 if(!canPowerAttack)$('#combatPowerAttack').checked=false;
 const castBtn=$('#combatCastBtn');
 const needsNoTarget=spell&&spell.data&&!['attack','save','heal'].includes(spell.data.effect_type);
 castBtn.hidden=!needsNoTarget;
 if(!isHumanTurn)castBtn.hidden=true;
 $('#combatHint').textContent=combatState.status!=='active'?'':(isHumanTurn?(spell?`Click a highlighted target to cast ${spell.name}, or click your own tile to target yourself.`:'Click a highlighted tile to move, or a highlighted enemy to attack.'):'Waiting for other combatants…');
 const outcome=$('#combatOutcome');
 if(combatState.status!=='active'){
  outcome.hidden=false;outcome.className=`combat-outcome ${combatState.status}`;
  outcome.textContent=combatState.status==='won'?`Victory!${combatState.reward?.loot?` +${combatState.reward.xp_awarded} XP, found: ${combatState.reward.loot}`:''}`:'Defeat… the enemies overwhelm you.';
  $('#combatEndTurnBtn').hidden=true;$('#combatLeaveBtn').hidden=false;
 }else{outcome.hidden=true;$('#combatEndTurnBtn').hidden=false;$('#combatLeaveBtn').hidden=true}
}
async function onCombatTileClick(x,y){
 if(!combatState||combatState.status!=='active')return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 if(!human||combatState.current_unit_id!==human.id)return;
 const key=tileKey(x,y);
 const spell=selectedSpell();
 try{
  let result=null;
  if(spell){
   let targetId=combatSpellTargets[key];
   if(targetId==null&&spell.data?.effect_type==='heal'&&x===human.x&&y===human.y)targetId=human.id;
   if(targetId==null)return;
   result=await api(`/api/combat/${combatState.id}/cast`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id,spell_name:spell.name,target_id:targetId})});
  }else if(key in combatAttackable){
   const powerAttack=!!$('#combatPowerAttack')?.checked;
   result=await api(`/api/combat/${combatState.id}/attack`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id,target_id:combatAttackable[key],power_attack:powerAttack})});
  }else if(combatReachable.has(key)){
   result=await api(`/api/combat/${combatState.id}/move`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id,x,y})});
  }else return;
  combatState=result;renderCombat();
 }catch(error){toast(error.message)}
}
$('#combatSpellSelect').onchange=()=>renderCombat();
$('#combatCastBtn').onclick=async()=>{
 if(!combatState)return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 const spell=selectedSpell();
 if(!human||!spell)return;
 try{const result=await api(`/api/combat/${combatState.id}/cast`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id,spell_name:spell.name,target_id:null})});combatState=result;renderCombat()}catch(error){toast(error.message)}
};
$('#combatEndTurnBtn').onclick=async()=>{
 if(!combatState)return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 if(!human)return;
 try{const result=await api(`/api/combat/${combatState.id}/end-turn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id})});combatState=result;renderCombat()}catch(error){toast(error.message)}
};
$('#combatLeaveBtn').onclick=async()=>{closeCombat();await refreshCharacterState();renderParty();showPanel('character')};

openView('play');
initPlay();
