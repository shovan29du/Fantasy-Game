const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const api=async(url,options={})=>{const response=await fetch(url,options);let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||`Request failed (${response.status})`);return data};
const safe=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message){const el=$('#toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}

const PORTRAIT_STYLES=['Anime Portrait','Anime Full Body','Realistic Portrait','Realistic Full Body','Fantasy Art','Fantasy Full Body','3D Render','3D Full Body','Comic Book','Cyberpunk','Dark Fantasy','Steampunk','Oil Painting','Watercolour','Manga','Chibi','Concept Art','Pin-Up','Cinematic','Furry Art','Sci-Fi','Gothic','Noir','Sketch','Watercolour Dark','Pastel','Impressionist','Pixel Art','Low Poly','Voxel Art'];
function fillPortraitStyles(){const sel=$('#portraitStyleSelect');if(!sel)return;sel.innerHTML=PORTRAIT_STYLES.map(s=>`<option value="${safe(s)}">${safe(s)}</option>`).join('')}

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
 const filled=state.characterId?1:0;
 const el=$('#partyCount');if(el)el.textContent=`${filled} / 6`;
 const pt=$('#playerToken');if(pt){const sp=pt.querySelector('span');if(sp)sp.textContent=state.sheet?(state.sheet.name||'??').slice(0,2).toUpperCase():'?'}
 if(!state.characterId){$('#partyList').innerHTML='<div style="padding:18px 8px;text-align:center"><p style="color:var(--muted);font-size:11px;margin:0 0 12px">No party members yet.</p><button id="goCreateCharBtn" class="add-member">+ Create Adventurer</button></div>';const b=$('#goCreateCharBtn');if(b)b.onclick=goCreateCharacter;return}
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
 $('#mapNodes').innerHTML='';
 try{state.locations=await api(`/api/worlds/${world.id}/locations`);renderMapNodes()}catch(error){state.locations=[];renderMapNodes()}
}
async function enterLocation(loc){
 const world=state.worlds[state.worldIndex];
 const panel=$('#mapLocationPanel'),img=$('#mapLocImg'),loading=$('#mapLocLoading');
 $('#mapLocName').textContent=loc.name;
 $('#mapLocSub').textContent=`${loc.terrain} · ${world?.name||''}`;
 panel.hidden=false;
 loading.style.display='flex';
 if(state.locationImageCache[loc.id]){img.src=state.locationImageCache[loc.id];img.style.opacity='1';loading.style.display='none';return}
 img.style.opacity='0';
 const character=state.sheet;
 const prompt=`${world?.name||'A realm'}, ${loc.terrain} region called ${loc.name}. ${loc.description||''} A ${character?.race||'traveller'} ${character?.profession||'adventurer'} named ${character?.name||'the hero'} stands in the scene.`;
 try{
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:'Cinematic',width:1024,height:576,save_to_chat:false})});
  const url=result.url||result.path;
  if(url){state.locationImageCache[loc.id]=url;img.src=url;img.onload=()=>{img.style.opacity='1'}}
 }catch(error){toast(`Scene generation failed: ${error.message}`)}
 loading.style.display='none';
}
$('#exitSceneBtn').onclick=()=>$('#sceneOverlay').classList.remove('open');
$('#mapLocCloseBtn').onclick=()=>{$('#mapLocationPanel').hidden=true};
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
function toWorldEntry(w){const locs=(w.locations||w.world_json?.locations||[]);const first=locs[0];const sp=w.space_alignment||'';const theme=sp==='sci-fi'||sp==='futuristic'?'universe':sp==='ancient_civilization'||sp==='prehistoric'?'area':'local';return {id:w.id,name:w.name,ratings:w.ratings||{},reality_type:w.reality_type||'Prime Reality',space:sp||'unknown',place:first?first.name:(w.name||'Unknown Location'),theme,startX:first?first.x:50,startY:first?first.y:50}}

// ── Chat content formatter: **action**, "dialogue", 'dialogue', user: label ──
function fmtChat(raw){
 const s=String(raw??'');
 let result='';
 // **action** or *action* → italic narration; "dialogue" or 'dialogue' → spoken line
 const re=/\*\*([^*]+?)\*\*|\*([^*\n]+?)\*|"([^"\n]+?)"|'([^'\n]+?)'/g;
 let last=0,m;
 while((m=re.exec(s))!==null){
  if(m.index>last)result+=safe(s.slice(last,m.index));
  if(m[1]!==undefined)result+=`<em class="chat-action">${safe(m[1])}</em>`;
  else if(m[2]!==undefined)result+=`<em class="chat-action">${safe(m[2])}</em>`;
  else if(m[3]!==undefined)result+=`<span class="chat-dialogue">&ldquo;${safe(m[3])}&rdquo;</span>`;
  else result+=`<span class="chat-dialogue">&#8216;${safe(m[4])}&#8217;</span>`;
  last=re.lastIndex;
 }
 if(last<s.length)result+=safe(s.slice(last));
 result=result.replace(/^(user|User|USER):\s*/,'<span class="chat-speaker">$1:</span> ');
 return result;
}

// ── Chat message renderer + per-message action toolbar ──
function chatMsg(cls,html,id){
 const idAttr=id?` data-mid="${id}"`:'';
 const label=cls==='player'?'<b>YOU</b>':'<b>WORLDWEAVER</b>';
 return `<div class="chat-msg ${cls}"${idAttr}><div class="msg-body">${label}${html}</div><div class="msg-actions"><button class="ma" data-act="copy" title="Copy">⎘</button><button class="ma" data-act="edit" title="Edit">✎</button><button class="ma" data-act="delete" title="Delete">🗑</button><button class="ma" data-act="rewind" title="Delete this and everything after">⏪</button><button class="ma" data-act="regenerate" title="Regenerate AI response">♻</button><button class="ma" data-act="memory" title="Save to memory">🧠</button><button class="ma" data-act="select" title="Select">☐</button><button class="ma" data-act="paste" title="Paste to input">→✏</button><button class="ma" data-act="forward" title="Progress story forward">↗</button><button class="ma" data-act="media" title="Generate media from this message">🎨</button></div></div>`;
}

// Event delegation for per-message action buttons
$('#chatLog').addEventListener('click',async e=>{
 const btn=e.target.closest('.ma');
 if(!btn)return;
 const wrap=btn.closest('.chat-msg');
 if(!wrap)return;
 const mid=wrap.dataset.mid?parseInt(wrap.dataset.mid):null;
 const bodyEl=wrap.querySelector('.msg-body');
 // extract plain text from rendered html
 const tmp=document.createElement('div');tmp.innerHTML=bodyEl.innerHTML;
 // remove the <b> label text
 const bEl=tmp.querySelector('b');if(bEl)bEl.remove();
 const text=tmp.textContent.trim();
 const act=btn.dataset.act;
 const sid=encodeURIComponent(state.sessionId||'default');

 if(act==='copy'){
  navigator.clipboard.writeText(text).catch(()=>{});
  toast('Copied!');
 }
 else if(act==='paste'){
  $('#chatInput').value=text;
  $('#chatInput').focus();
 }
 else if(act==='select'){
  wrap.classList.toggle('selected');
  btn.textContent=wrap.classList.contains('selected')?'☑':'☐';
 }
 else if(act==='forward'){
  // Auto-progress: get best logical continuation and send it
  const sid2=encodeURIComponent(state.sessionId||'default');
  btn.textContent='…';btn.disabled=true;
  try{
   const {options}=await api(`/api/chat/progressions?session_id=${sid2}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId||'default'})});
   const best=options&&options[0]?options[0]:'Continue.';
   $('#chatInput').value=best;
   $('#chatForm').requestSubmit();
  }catch{$('#chatInput').value='Continue the story.';$('#chatForm').requestSubmit();}
  finally{btn.textContent='↗';btn.disabled=false;}
 }
 else if(act==='edit'){
  if(!mid){toast('This message has no ID yet — reload chat first.');return;}
  const cur=bodyEl.querySelector('b')?bodyEl.innerHTML.replace(/^<b>[^<]*<\/b>/,'').trim():text;
  const fresh=prompt('Edit message:',text);
  if(fresh===null||fresh===text)return;
  try{
   const r=await fetch(`/api/chat/messages/${mid}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:fresh})});
   if(!r.ok)throw new Error('Edit failed');
   // update in-place
   const label=wrap.classList.contains('player')?'<b>YOU</b>':'<b>WORLDWEAVER</b>';
   bodyEl.innerHTML=label+safe(fresh);
   toast('Edited');
  }catch(err){toast(err.message);}
 }
 else if(act==='delete'){
  if(!mid){wrap.remove();return;}
  if(!confirm('Delete this message?'))return;
  try{
   const r=await fetch(`/api/chat/messages/${mid}`,{method:'DELETE'});
   if(!r.ok)throw new Error('Delete failed');
   wrap.remove();toast('Deleted');
  }catch(err){toast(err.message);}
 }
 else if(act==='rewind'){
  if(!mid){toast('No ID — reload chat first.');return;}
  if(!confirm('Delete this message and everything after it?'))return;
  try{
   const r=await fetch(`/api/chat/messages/${mid}/rewind?session_id=${sid}`,{method:'DELETE'});
   if(!r.ok)throw new Error('Rewind failed');
   let el=wrap.nextElementSibling;
   while(el){const next=el.nextElementSibling;el.remove();el=next;}
   toast('Rewound!');
  }catch(err){toast(err.message);}
 }
 else if(act==='regenerate'){
  // Re-ask the AI to respond from this point in the story
  btn.textContent='…';btn.disabled=true;
  try{
   const world=state.worlds[state.worldIndex];
   const prompt=wrap.classList.contains('player')?`The player said: ${text}. Continue the story.`:`Regenerate a different response to the previous player action.`;
   const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:prompt,extra_context:playerContextLine(),session_id:state.sessionId,world_id:world?.id,user_name:'Player',character_name:'Worldweaver',participants:['Worldweaver'],temperature:.9})});
   const data=await r.json();
   if(!r.ok)throw new Error(data.detail||'AI unavailable');
   $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',fmtChat(data.reply),data.id));
   $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
   speakReply(data.reply);
  }catch(err){toast(err.message);}
  finally{btn.textContent='♻';btn.disabled=false;}
 }
 else if(act==='memory'){
  if(!mid){
   try{
    const r=await fetch('/api/memory/facts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fact:text,source:'chat-pin',memory_type:'episodic',importance:0.9})});
    if(!r.ok)throw new Error('Memory save failed');
    toast('Saved to memory!');
   }catch(err){toast(err.message);}
   return;
  }
  try{
   const r=await fetch(`/api/chat/messages/${mid}/memory`,{method:'POST'});
   if(!r.ok)throw new Error('Memory save failed');
   toast('Saved to memory!');
  }catch(err){toast(err.message);}
 }
 else if(act==='media'){
  // Show inline media panel under the message
  let mp=wrap.querySelector('.msg-media-panel');
  if(mp){mp.remove();return;}
  mp=document.createElement('div');mp.className='msg-media-panel';
  mp.innerHTML=`<div class="mmp-head">🎨 Generate from this message</div>
<div class="mmp-btns">
 <button class="mmp-btn" data-mtype="image">🖼 Image</button>
 <button class="mmp-btn" data-mtype="anime">🎌 Anime</button>
 <button class="mmp-btn" data-mtype="video">🎬 Video</button>
</div>
<div class="mmp-result"></div>`;
  wrap.appendChild(mp);
  mp.querySelectorAll('.mmp-btn').forEach(b=>b.onclick=async()=>{
   const mtype=b.dataset.mtype;
   const styleMap={image:'Cinematic',anime:'Anime Portrait',video:'Cinematic'};
   const resultEl=mp.querySelector('.mmp-result');
   resultEl.innerHTML='<span class="mmp-loading">Generating…</span>';
   b.disabled=true;
   try{
    const endpoint='/api/media/image';
    const payload={prompt:text.slice(0,200),style:styleMap[mtype]||'Cinematic',width:mtype==='video'?1024:512,height:mtype==='video'?576:768,save_to_chat:false};
    const res=await api(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(res.url){
     resultEl.innerHTML=`<img src="${safe(res.url)}" class="mmp-img" alt="generated"><br><button class="mmp-insert ghost">Insert into chat</button>`;
     // Auto-save to media gallery
     api('/api/media/gallery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({media_type:mtype==='anime'?'image':mtype,title:text.slice(0,60)||'Chat scene',description:text.slice(0,200),file_path:res.path||res.url,source:'chat',tags:[mtype,'chat-generated']})}).catch(()=>{});
     resultEl.querySelector('.mmp-insert').onclick=()=>{
      $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',`<img src="${safe(res.url)}" style="max-width:100%;border-radius:3px;margin-top:4px" alt="generated scene">`));
      $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
      mp.remove();
     };
    }else{resultEl.innerHTML='<span class="mmp-loading">No image returned.</span>';}
   }catch(err){resultEl.innerHTML=`<span class="mmp-loading">${safe(err.message)}</span>`;}
   finally{b.disabled=false;}
  });
 }
});

async function loadChatHistory(){
 try{
  const history=await api(`/api/chat/history?session_id=${encodeURIComponent(state.sessionId)}&limit=40`);
  $('#chatLog').innerHTML=history.length?history.map(m=>chatMsg(m.role==='user'?'player':'gm',fmtChat(m.content),m.id)).join(''):'<p class="gm">The portal hums, waiting for your first move.</p>';
  $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
 }catch{}
}

// ── Dynamic clock/weather ──
async function updateClock(){
 try{
  const clk=await api(`/api/world/clock?session_id=${encodeURIComponent(state.sessionId||'default')}`);
  const h=clk.hour,m=clk.minute;
  const period=h<6?'Night':h<9?'Dawn':h<12?'Morning':h<14?'Noon':h<18?'Afternoon':h<21?'Evening':'Night';
  const icon=h<6||h>=21?'🌙':h<9?'🌅':h<18?'☀':'🌇';
  const mapTime=$('#mapTime');if(mapTime)mapTime.textContent=`${icon} ${period} · Day ${clk.day} · ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
  const wIcon={'Clear':'☀','Cloudy':'☁','Overcast':'🌥','Light Rain':'🌦','Heavy Rain':'🌧','Thunderstorm':'⛈','Fog':'🌫','Drizzle':'🌧','Snow':'❄','Blizzard':'🌨','Windy':'💨','Hail':'🌨','Sandstorm':'🏜','Aurora':'✨','Mist':'🌫'}[clk.weather]||'☁';
  const mapWeather=$('#mapWeather');if(mapWeather)mapWeather.textContent=`${wIcon} ${clk.weather} · ${clk.temp}°C`;
  const mapEl=$('#map');if(mapEl){mapEl.classList.toggle('map-night',(h<6||h>=21));mapEl.classList.toggle('map-dawn',h>=6&&h<9);}
 }catch{}
}
$('#advanceTimeBtn').onclick=async()=>{
 try{
  await api(`/api/world/clock/advance?session_id=${encodeURIComponent(state.sessionId||'default')}&minutes=30`,{method:'POST'});
  await updateClock();
  if(Math.random()<0.1) triggerRandomEvent();
 }catch{}
};
async function triggerRandomEvent(){
 try{
  const {event}=await api(`/api/world/events/random?session_id=${encodeURIComponent(state.sessionId||'default')}`,{method:'POST'});
  if(event){
   $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm','🎲 <i>Random Event:</i> '+safe(event)));
   $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
  }
 }catch{}
}
let _clockInterval=null;
function startClockTick(){
 if(_clockInterval)clearInterval(_clockInterval);
 _clockInterval=setInterval(()=>{
  api(`/api/world/clock/advance?session_id=${encodeURIComponent(state.sessionId||'default')}&minutes=15`,{method:'POST'}).then(()=>updateClock()).catch(()=>{});
 },5*60*1000);
}

// ── Chat Options: 5 progression options ──
const _FALLBACK_OPTIONS={progressions:['Investigate the area','Talk to a nearby NPC','Check your inventory','Move to a new location','Wait and observe'],alternatives:['A stranger intervenes','The enemy retreats','A portal opens nearby','A hidden passage reveals itself','An ally arrives at the last moment']};
let _optionsPanelOpen=false;
async function showChatOptions(mode='progressions'){
 const panel=$('#chatOptionsPanel');
 if(!panel)return;
 if(_optionsPanelOpen&&panel.dataset.mode===mode){panel.hidden=true;_optionsPanelOpen=false;return}
 panel.dataset.mode=mode;
 panel.hidden=false;
 _optionsPanelOpen=true;
 panel.innerHTML='<div class="options-loading">✦ Generating options…</div>';
 let options=_FALLBACK_OPTIONS[mode]||_FALLBACK_OPTIONS.progressions;
 try{
  const sid=encodeURIComponent(state.sessionId||'default');
  const url=mode==='alternatives'?`/api/chat/alternatives?session_id=${sid}`:`/api/chat/progressions?session_id=${sid}`;
  const res=await api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId||'default'})});
  if(Array.isArray(res.options)&&res.options.length>=3)options=res.options;
 }catch{}
 panel.innerHTML=`<div class="options-header">${mode==='alternatives'?'⏪ Alternative outcomes:':'✦ What do you do next?'}</div>`+
  options.map((o,i)=>`<button class="option-chip" data-opt="${safe(o)}">${i+1}. ${safe(o)}</button>`).join('');
 panel.querySelectorAll('.option-chip').forEach(btn=>btn.onclick=()=>{
  $('#chatInput').value=btn.dataset.opt;
  panel.hidden=true;_optionsPanelOpen=false;
  if(mode!=='alternatives')$('#chatForm').requestSubmit();
 });
}
$('#chatOptionsBtn').onclick=()=>showChatOptions('progressions');
// Media-tab option buttons: show a floating modal since chat panel is in play area
$$('.media-options-btn').forEach(btn=>btn.onclick=async()=>{
 const existing=$('#mediaOptsModal');
 if(existing){existing.remove();return}
 const modal=document.createElement('div');
 modal.id='mediaOptsModal';
 modal.style.cssText='position:fixed;bottom:80px;right:24px;background:#0a1018;border:1px solid var(--line);border-radius:6px;padding:12px;z-index:1000;width:280px;max-height:280px;overflow-y:auto';
 modal.innerHTML='<div class="options-loading">✦ Generating options…</div>';
 document.body.appendChild(modal);
 let opts=_FALLBACK_OPTIONS.progressions;
 try{const sid=encodeURIComponent(state.sessionId||'default');const res=await api(`/api/chat/progressions?session_id=${sid}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:state.sessionId||'default'})});if(Array.isArray(res.options)&&res.options.length>=3)opts=res.options}catch{}
 modal.innerHTML=`<div class="options-header" style="color:var(--gold);font-size:9px;margin-bottom:8px">✦ Story progressions</div>`+opts.map((o,i)=>`<div style="padding:6px 0;border-bottom:1px solid var(--line);font-size:11px;cursor:pointer" data-mopt="${safe(o)}">${i+1}. ${safe(o)}</div>`).join('')+`<div style="text-align:right;margin-top:8px"><button onclick="document.getElementById('mediaOptsModal')?.remove()" style="font-size:9px;background:none;border:none;color:var(--muted);cursor:pointer">✕ Close</button></div>`;
 modal.querySelectorAll('[data-mopt]').forEach(el=>el.onclick=()=>{const inp=$('#chatInput');if(inp)inp.value=el.dataset.mopt;modal.remove();toast('Option copied to chat input')});
 document.addEventListener('click',function h(e){if(!modal.contains(e.target)&&!e.target.classList.contains('media-options-btn')){modal.remove();document.removeEventListener('click',h)}},{once:true,capture:true});
});
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
 updateWorld();if(world){move(world.startX??50,world.startY??50)}renderParty();renderQuests();
 try{const active=await api(`/api/combat/active?session_id=${encodeURIComponent(state.sessionId)}`);openCombat(active)}catch{/* no combat in progress for this session */}
 updateClock();
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
  // Full custom_text is stored as lorebook context on the server; show only the final hook line here
  let opening;
  if(payload.custom_text){
   const sents=(payload.custom_text.match(/[^.!?]+[.!?]+(?:\s|$)/g)||[]).map(s=>s.trim()).filter(Boolean);
   opening=sents.length>2?sents.slice(-2).join(' '):payload.custom_text.slice(0,160);
  }else{
   opening=`${world.name}. The story begins.`;
  }
  try{await api('/api/chat/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'assistant',content:opening,session_id:state.sessionId})})}catch{}
  await loadChatHistory();
  updateWorld();move(world.startX??50,world.startY??50);renderParty();renderQuests();
  updateClock();startClockTick();
  toast(`New game started: ${world.name}`);
 }catch(error){toast(error.message)}
}
// ── Scenario card image queue (max 2 concurrent) ──
const _scImgCache={};
let _scImgQ=[],_scImgBusy=0;
function _scDrain(){
 if(_scImgBusy>=2||!_scImgQ.length)return;
 const{name,prompt,img}=_scImgQ.shift();
 if(_scImgCache[name]){img.src=_scImgCache[name];img.onload=()=>img.classList.add('sc-loaded');_scDrain();return}
 _scImgBusy++;
 api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:'Fantasy Art',width:512,height:384,save_to_chat:false})})
  .then(r=>{const u=r.url||r.path;if(u){_scImgCache[name]=u;img.src=u;img.onload=()=>img.classList.add('sc-loaded')}})
  .catch(()=>{}).finally(()=>{_scImgBusy--;_scDrain()});
}
function _scQueueImg(name,prompt,img){
 if(_scImgCache[name]){img.src=_scImgCache[name];img.onload=()=>img.classList.add('sc-loaded');return}
 _scImgQ.push({name,prompt,img});_scDrain();
}

let _scObserver=null;
function renderScenarioCards(cats,filterKey){
 const ICONS={fantasy:'⚔',anime:'✨',gaming:'🎮',cyberpunk:'⚡',supernatural:'👁',apocalyptic:'☢',zombie:'🧟',mystery:'🔍',drama:'💔',alien_space:'🚀'};
 const COLORS={fantasy:'#1a1a3e',anime:'#2e1a3e',gaming:'#0d1f0d',cyberpunk:'#0a1f1a',supernatural:'#2a1a2a',apocalyptic:'#2e1a0d',zombie:'#1a2a1a',mystery:'#1a1a2a',drama:'#2a0d1a',alien_space:'#0d1a2e'};
 let all=[];
 cats.forEach(c=>{if(filterKey==='all'||c.key===filterKey)c.scenarios.forEach(s=>all.push({...s,catKey:c.key,catLabel:c.label}))});
 $('#scenarioCount').textContent=`${all.length} scenario${all.length!==1?'s':''}`;
 $('#scenarioCardsGrid').innerHTML=all.map(s=>{
  const op=s.opening||'';
  const preview=op.length>0?`<div class="scenario-card-preview" hidden>${safe(op)}</div>`:'' ;
  const teaser=op.length>0?`<div class="scenario-card-teaser">${safe(op.slice(0,120))}${op.length>120?'…':''}</div>`:'';
  return `<div class="scenario-card" data-cat="${safe(s.catKey)}" data-name="${safe(s.name)}" data-type="${safe(s.type)}">
   <div class="scenario-card-img" style="background:${COLORS[s.catKey]||'#141c24'}" data-prompt="${safe(`a ${s.catLabel} rpg scene for ${s.name}, character portrait, cinematic fantasy illustration`)}"><span>${ICONS[s.catKey]||'⚔'}</span><img src="" alt=""></div>
   <div class="scenario-card-body">
    <div class="scenario-card-genre">${safe(s.catLabel)}</div>
    <div class="scenario-card-name">${safe(s.name)}</div>
    ${teaser}
    <div class="scenario-card-actions">
     ${op.length>0?`<button class="scenario-card-more" title="Show backstory">＋</button>`:''}
     <button class="scenario-card-play">▶ Play</button>
    </div>
   </div>
   ${preview}
  </div>`;
 }).join('')||'<div class="empty-state">No scenarios found.</div>';
 $$('#scenarioCardsGrid .scenario-card').forEach(card=>{
  const go=()=>{state.pendingCategory=cats.find(c=>c.key===card.dataset.cat);beginGame({category:card.dataset.cat,scenario_name:card.dataset.name,scenario_type:card.dataset.type})};
  const pb=card.querySelector('.scenario-card-play');if(pb)pb.onclick=e=>{e.stopPropagation();go()};
  const mb=card.querySelector('.scenario-card-more');
  if(mb)mb.onclick=e=>{
   e.stopPropagation();
   const pv=card.querySelector('.scenario-card-preview');
   if(!pv)return;
   const open=pv.hidden;
   pv.hidden=!open;
   mb.textContent=open?'−':'＋';
   mb.title=open?'Hide backstory':'Show backstory';
  };
  card.onclick=go;
 });
 if(_scObserver)_scObserver.disconnect();
 _scObserver=new IntersectionObserver(entries=>{entries.forEach(entry=>{
  if(!entry.isIntersecting)return;
  const imgDiv=entry.target;_scObserver.unobserve(imgDiv);
  const img=imgDiv.querySelector('img'),card=imgDiv.closest('.scenario-card');
  if(!img||!card)return;
  _scQueueImg(card.dataset.name,imgDiv.dataset.prompt,img);
 })},{threshold:0.1,rootMargin:'60px'});
 $$('#scenarioCardsGrid .scenario-card-img').forEach(el=>_scObserver.observe(el));
}

$('#startNewGameBtn').onclick=async()=>{
 try{
  if(!categoriesCache)categoriesCache=await api('/api/scenarios/categories');
  const sel=$('#worldCategorySelect');
  sel.innerHTML='<option value="all">🌐 All Worlds</option>'+categoriesCache.map(c=>`<option value="${safe(c.key)}">${safe(c.label)} (${c.scenarios.length})</option>`).join('');
  sel.onchange=()=>renderScenarioCards(categoriesCache,sel.value);
  renderScenarioCards(categoriesCache,'all');
  showStartStep('category');
 }catch(error){toast(error.message)}
};
function _activeCatKey(){const v=$('#worldCategorySelect')?.value;return(v&&v!=='all')?v:state.pendingCategory?.key||'fantasy'}
$('#customScenarioForm').onsubmit=e=>{e.preventDefault();const text=new FormData(e.currentTarget).get('text')||'';if(!text.trim()){toast('Write a scenario first');return}beginGame({category:_activeCatKey(),scenario_name:text.slice(0,40),scenario_type:'custom',custom_text:text})};

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
$('#useRandomScenarioBtn').onclick=()=>beginGame({category:_activeCatKey(),scenario_name:'Random Scenario',scenario_type:'custom',custom_text:state.randomScenarioText});
$('#autoGenScenarioBtn').onclick=async()=>{
 const worldName=state.worlds?.[state.worldIndex]?.name||'';
 const catKey=_activeCatKey();
 const genre=categoriesCache?.find(c=>c.key===catKey)?.label||'Fantasy';
 const btn=$('#autoGenScenarioBtn');
 btn.textContent='✦ Generating…';
 try{
  const {scenario}=await api('/api/scenario/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({world_name:worldName,genre,story_preset:genre,session_id:state.sessionId||'default'})});
  const ta=$('#customScenarioForm')?.elements?.text;
  if(ta)ta.value=scenario;
  toast('Scenario generated!');
 }catch(err){toast('Auto-generate failed')}
 finally{btn.textContent='✦ Auto-generate from world & preset'}
};

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


// ── Attach file / zip to chat ──
$('#attachBtn').onclick=()=>$('#chatFileInput').click();
$('#chatFileInput').onchange=async()=>{
 const f=$('#chatFileInput').files[0];
 if(!f)return;
 $('#chatFileInput').value='';
 const fd=new FormData();fd.append('file',f);
 $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('player','📎 Attached: '+safe(f.name)));
 $('#aiStatus').textContent='Reading file…';
 try{
  const r=await fetch('/api/chat/attach',{method:'POST',body:fd});
  const data=await r.json();
  if(!r.ok)throw new Error(data.detail||'Upload failed');
  const summary=data.summary;
  const world=state.worlds[state.worldIndex];
  const cr=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:summary,extra_context:playerContextLine(),session_id:state.sessionId,world_id:world?.id,user_name:'Player',character_name:'Worldweaver',participants:['Worldweaver'],temperature:.75})});
  const cd=await cr.json();
  if(!cr.ok)throw new Error(cd.detail||'AI unavailable');
  $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',fmtChat(cd.reply)));
  $('#aiStatus').textContent='LM Studio connected';
  speakReply(cd.reply);
 }catch(err){
  $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',safe(err.message||'Could not read file.')));
  $('#aiStatus').textContent='LM Studio link';
 }
 $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
};
// ── Download chat as zip ──
$('#downloadZipBtn').onclick=()=>{
 const sid=encodeURIComponent(state.sessionId||'default');
 const a=document.createElement('a');
 a.href=`/api/chat/export/zip?session_id=${sid}`;
 a.download='worldweaver-chat.zip';
 a.click();
};
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
$('#chatForm').onsubmit=async e=>{e.preventDefault();const input=$('#chatInput'),msg=input.value.trim();if(!msg)return;$('#chatLog').insertAdjacentHTML('beforeend',chatMsg('player',fmtChat(msg)));input.value='';$('#aiStatus').textContent='Thinking...';try{const world=state.worlds[state.worldIndex];const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:msg,extra_context:playerContextLine(),session_id:state.sessionId,world_id:world?.id,user_name:'Player',character_name:'Worldweaver',participants:['Worldweaver'],temperature:.75})});const data=await r.json();if(!r.ok)throw new Error(data.detail||'Local model unavailable');$('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',fmtChat(data.reply),data.id));$('#aiStatus').textContent='LM Studio connected';speakReply(data.reply)}catch(error){$('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',safe(error.message||'The local storyteller cannot be reached.')));$('#aiStatus').textContent='Start LM Studio on port 1234'}$('#chatLog').scrollTop=$('#chatLog').scrollHeight};

// ═══ AI Companion-style workspace navigation and studios ═══
function openView(name){$$('.app-view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.side-nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));if(name==='play'){$('#playHub').hidden=state.hasActiveGame;$('#gameArea').hidden=!state.hasActiveGame}if(name==='characters')loadCharacterStudio();if(name==='explore')loadExplore();if(name==='worlds')loadWorlds();if(name==='knowledge'){loadLore();loadKnowledgeDocs()}if(name==='media')loadMediaTab();if(name==='settings'){checkModelStatus();loadSettingsExtras()}}
$$('.side-nav button').forEach(button=>button.onclick=()=>openView(button.dataset.view));

let studioOptions={};
function fillSelect(selector,values){const el=$(selector);if(!el)return;const list=Array.isArray(values)?values:Object.keys(values||{});el.innerHTML=list.map(value=>`<option value="${safe(value)}">${safe(value)}</option>`).join('')}
async function loadCharacterStudio(){try{if(!Object.keys(studioOptions).length){studioOptions=await api('/api/options');fillSelect('#raceSelect',studioOptions.races);fillSelect('#professionSelect',studioOptions.professions);fillSelect('#backgroundSelect',studioOptions.backgrounds);fillSelect('#alignmentSelect',studioOptions.alignments);fillSelect('#originSelect',studioOptions.origins||[]);const el=$('#secondaryAncestrySelect');if(el){el.innerHTML='<option value="">— None —</option>';(Object.keys(studioOptions.races||{})).forEach(r=>{el.innerHTML+=`<option value="${safe(r)}">${safe(r)}</option>`})}const ptEl=$('#powerTierSelect');if(ptEl){ptEl.innerHTML=(studioOptions.powerTiers||[]).map(t=>`<option value="${t.tier}">${t.tier} · ${safe(t.name)} — ${safe(t.scope)}</option>`).join('')}initCharFormV6();}const characters=await api('/api/characters');$('#characterLibrary').innerHTML=characters.length?characters.map(c=>{const av=c.photo_path?`<img src="${safe(c.photo_path)}" class="char-avatar-img" alt="portrait">`:`<span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span>`;const isActive=String(c.id)===String(state.characterId);return`<article class="entity-card">${av}<div><b>${safe(c.name)}</b><small>${safe(c.gender?c.gender+' · ':'')}${safe(c.race||'Unknown ancestry')} · ${safe(c.profession||'Adventurer')}</small></div><em>LV ${safe(c.level||1)}</em><button data-use-char="${c.id}" class="ghost" style="font-size:9px;padding:3px 8px;${isActive?'color:var(--gold);border-color:var(--gold)':''}">${isActive?'Active':'Use'}</button></article>`}).join(''):'<div class="empty-state">No saved characters yet. Create your first companion.</div>';$$('[data-use-char]').forEach(btn=>btn.onclick=async()=>{const cid=+btn.dataset.useChar;if(state.characterId===cid)return;state.characterId=cid;await refreshCharacterState();renderParty();renderQuests();loadCharacterStudio();toast('Adventurer switched — ready for play')})}catch(error){$('#characterLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#characterForm').onsubmit=async event=>{
 event.preventDefault();
 const formEl=event.currentTarget; // native currentTarget is cleared once we `await`, so capture it now
 const form=new FormData(formEl);
 const payload=Object.fromEntries(form.entries());
 payload.level=Number(payload.level||1);
 payload.origin_world=state.worlds[state.worldIndex]?.name||'Aethoria Prime';
 payload.scenario=`Origin reality: ${payload.scenario}`;
 try{
  payload.photo_path=$('#charPortraitPreview').dataset.photoUrl||'';
  const created=await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  toast(`${payload.name} saved`);
  formEl.reset();
  const box=$('#charPortraitPreview');box.innerHTML='<div class="empty-state" style="padding:16px;font-size:10px">No portrait — fill in the form then click Generate</div>';delete box.dataset.photoUrl;
  await loadCharacterStudio();
  // Character creation is a single shared flow: the same form used here in
  // the AI Companion library also becomes the Play view's active adventurer
  // whenever Play doesn't have one bound yet.
  if(created?.id){
   if(!state.characterId){state.characterId=created.id;await refreshCharacterState();renderParty();renderQuests();showPanel('character');toast(`${payload.name} is now your active adventurer — switch to Play to begin`)}
   else{toast(`${payload.name} saved — click Use to switch adventurers`)}
  }
 }catch(error){toast(error.message)}
};
$('#randomCharacter').onclick=async()=>{try{const {character}=await api('/api/characters/random',{method:'POST'});const form=$('#characterForm');['name','race','gender','profession','background','alignment','backstory','goals','origin','power_tier','secondary_ancestry'].forEach(key=>{if(form.elements[key]&&character[key]!=null)form.elements[key].value=Array.isArray(character[key])?character[key].join(', '):character[key]});toast('Random character generated')}catch(error){toast(error.message)}};
$('#generatePortraitBtn').onclick=async()=>{
 const form=$('#characterForm');
 const data=Object.fromEntries(new FormData(form).entries());
 const box=$('#charPortraitPreview');
 box.innerHTML='<div class="empty-state" style="padding:16px;font-size:10px">Generating portrait…</div>';
 try{
  const parts=[];
  if(data.gender&&data.gender!=='— Select —') parts.push(data.gender.toLowerCase());
  if(data.race) parts.push(data.race);
  if(data.profession) parts.push(data.profession);
  if(data.backstory) parts.push(data.backstory.slice(0,100));
  const prompt=parts.length?parts.join(', '):'fantasy portrait character';
  const portraitStyle=($('#portraitStyleSelect')?.value)||'Anime Portrait';
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:portraitStyle,width:512,height:768,save_to_chat:false})});
  box.innerHTML=`<img src="${safe(result.url)}" alt="Character portrait">`;
  box.dataset.photoUrl=result.url;
 }catch(error){
  box.innerHTML='<div class="empty-state" style="padding:16px;font-size:10px">Portrait failed</div>';
  toast(error.message);
 }
};
$('#refreshCharacters').onclick=loadCharacterStudio;$('#newCharacterBtn').onclick=()=>{$('#characterForm').scrollIntoView({behavior:'smooth'});$('#characterForm').elements.name.focus()};

async function loadWorlds(){try{const items=await api('/api/worlds');$('#worldLibrary').innerHTML=items.length?items.map(w=>`<article class="entity-card"><span class="entity-avatar">◎</span><div><b>${safe(w.name)}</b><small>${safe(w.space_alignment||'multiverse')} · ${safe(w.reality_type||'Prime Reality')} · Magic ${safe(w.ratings?.magic ?? w.magic_level)}</small></div><em>${safe(w.time_of_day||'Active')}</em></article>`).join(''):'<div class="empty-state">No database worlds yet. The four play-map realities remain available.</div>'}catch(error){$('#worldLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#worldForm').onsubmit=async event=>{event.preventDefault();const formEl=event.currentTarget;const raw=Object.fromEntries(new FormData(formEl).entries());const payload={name:raw.name,magic:raw.magic,tech:raw.tech,space:raw.space,reality_type:raw.reality_type||'Prime Reality',num_locs:Number(raw.num_locs||8),ratings:{science:Number(raw.ratings_science||5),technology:Number(raw.ratings_technology||4),magic:Number(raw.ratings_magic||5),weapon:Number(raw.ratings_weapon||3),power:Number(raw.ratings_power||5),civilization:Number(raw.ratings_civilization||4),danger:Number(raw.ratings_danger||4),horror:Number(raw.ratings_horror||2)}};try{await api('/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`${payload.name} created`);formEl.reset();loadWorlds()}catch(error){toast(error.message)}};$('#refreshWorlds').onclick=loadWorlds;

async function loadLore(){try{const items=await api('/api/knowledge/lorebook');$('#loreLibrary').innerHTML=items.length?items.map(item=>`<article class="entity-card"><span class="entity-avatar">◇</span><div><b>${safe(item.title)}</b><small>${safe((item.content||'').slice(0,90))}</small></div><em>${item.enabled===0?'Off':'Active'}</em></article>`).join(''):'<div class="empty-state">No lorebook entries. Add rules, locations, and secrets here.</div>'}catch(error){$('#loreLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#loreForm').onsubmit=async event=>{event.preventDefault();const formEl=event.currentTarget;const raw=Object.fromEntries(new FormData(formEl).entries());const payload={title:raw.title,content:raw.content,keywords:raw.keywords.split(',').map(x=>x.trim()).filter(Boolean),world_id:0,always_active:true};try{await api('/api/knowledge/lorebook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Lore saved');formEl.reset();loadLore()}catch(error){toast(error.message)}};$('#refreshLore').onclick=loadLore;

async function checkModelStatus(){const badge=$('#modelBadge');badge.textContent='Checking';badge.classList.remove('good');try{const result=await api('/api/settings/model');badge.textContent='Configured';badge.classList.add('good');$('#activeModel').textContent=result.active_model||'LM Studio model'}catch{badge.textContent='Offline';$('#activeModel').textContent='Start LM Studio on port 1234'}}
$('#checkModel').onclick=checkModelStatus;$('#reducedMotion').onchange=e=>{document.body.classList.toggle('reduced-motion',e.target.checked);localStorage.setItem('reduced-motion',e.target.checked)};$('#compactMode').onchange=e=>{document.body.classList.toggle('compact',e.target.checked);localStorage.setItem('compact-mode',e.target.checked)};$('#reducedMotion').checked=localStorage.getItem('reduced-motion')==='true';$('#compactMode').checked=localStorage.getItem('compact-mode')==='true';document.body.classList.toggle('reduced-motion',$('#reducedMotion').checked);document.body.classList.toggle('compact',$('#compactMode').checked);$$('[data-feature]').forEach(button=>button.onclick=()=>toast(`${button.dataset.feature} tools are connected to the local media API`));

// ═══ Explore: built-in character library + web search/import ═══
let libraryRacesLoaded=false;
async function loadExplore(){
 if(!libraryRacesLoaded){try{const options=await api('/api/options');fillSelect('#libraryRaceSelect',['All',...Object.keys(options.races||{})]);libraryRacesLoaded=true}catch{}}
 await Promise.all([searchLibrary(),loadImportedCharacters()]);
}
async function loadImportedCharacters(){
 try{
  const characters=await api('/api/characters');
  const el=$('#importedCharacters');if(!el)return;
  el.innerHTML=characters.length?characters.map(c=>{const av=c.photo_path?`<img src="${safe(c.photo_path)}" class="char-avatar-img" alt="portrait">`:`<span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span>`;const isActive=String(c.id)===String(state.characterId);return`<article class="entity-card">${av}<div><b>${safe(c.name)}</b><small>${safe(c.gender?c.gender+' · ':'')}${safe(c.race||'Unknown')} · ${safe(c.profession||'Adventurer')}</small></div><em>LV${safe(c.level||1)}</em><button data-exp-use-char="${c.id}" class="ghost" style="font-size:9px;padding:3px 8px;${isActive?'color:var(--gold);border-color:var(--gold)':''}">${isActive?'Active':'Use'}</button></article>`}).join(''):'<div class="empty-state">No imported characters yet.</div>';
  $$('[data-exp-use-char]').forEach(btn=>btn.onclick=async()=>{const cid=+btn.dataset.expUseChar;state.characterId=cid;await refreshCharacterState();renderParty();renderQuests();loadImportedCharacters();toast('Adventurer activated')});
 }catch(error){const el=$('#importedCharacters');if(el)el.innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
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
$('#refreshImportedChars').onclick=loadImportedCharacters;
$('#importAllBtn').onclick=async()=>{if(!lastLibraryResults.length){toast('Nothing to import');return}try{const result=await api('/api/explore/library/import-all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({characters:lastLibraryResults})});toast(`${result.imported} characters imported`)}catch(error){toast(error.message)}};
$('#randomLibraryBtn').onclick=async()=>{
 try{
  const result=await api('/api/explore/library?query=&race=All&limit=400');
  const all=result.characters||[];
  const shuffled=all.sort(()=>Math.random()-.5).slice(0,12);
  renderExploreCards(shuffled,$('#libraryResults'),async(character,btn)=>{btn.disabled=true;try{await api('/api/explore/library/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character})});btn.textContent='Imported';toast(`${character.name} imported`)}catch(error){toast(error.message);btn.disabled=false}});
  $('#libraryCount').textContent=`Random 12 / ${all.length}`;
 }catch(error){toast(error.message)}
};
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
$('#refreshKnowledgeDocs').onclick=loadKnowledgeDocs;
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
$('#settingsVoiceForm')?.addEventListener('submit',async e=>{e.preventDefault();const txt=e.currentTarget.elements.vtext.value.trim();if(!txt)return;const out=$('#settingsVoiceResult');out.textContent='Generating…';try{const r=await api('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:txt})});if(r.url){out.innerHTML=`<audio controls src="${safe(r.url)}" style="width:100%;margin-top:6px"></audio>`}else{out.textContent='TTS unavailable (install edge-tts and ensure internet access)'}}catch(err){out.textContent=err.message}});

// ═══ Tactical combat: turn-based grid battle with obstacles ═══
let combatState=null, combatReachable=new Set(), combatAttackable={}, combatSpellTargets={}, combatAutoTimer=null;
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
function stopCombatPlay(){clearInterval(combatAutoTimer);combatAutoTimer=null;const btn=$('#combatPlayBtn');if(btn){btn.textContent='▶ Play';btn.classList.remove('cb-play-active');}}
async function combatAutoStep(){
  if(!combatState||combatState.status!=='active'){stopCombatPlay();return;}
  const human=combatState.units.find(u=>u.stats?.is_human);
  if(!human||combatState.current_unit_id!==human.id){stopCombatPlay();return;}
  try{const result=await api(`/api/combat/${combatState.id}/end-turn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id})});combatState=result;renderCombat();if(combatState.status!=='active')stopCombatPlay();}catch(e){stopCombatPlay();toast(e.message);}
}
function showCombatResult(){
  if(!combatState)return;
  const reward=combatState.reward||{};
  const enemies=combatState.units.filter(u=>u.unit_type==='enemy');
  const players=combatState.units.filter(u=>u.unit_type==='player');
  const killed=enemies.filter(u=>!u.is_active).length;
  const survived=players.filter(u=>u.is_active).length;
  const won=combatState.status==='won';
  const logLines=(combatState.log||[]).map(l=>`<div>${safe(l)}</div>`).join('');
  $('#combatResultBody').innerHTML=`<div class="result-outcome ${won?'won':'lost'}">${won?'🏆 Victory!':'💀 Defeat'}</div><div class="result-stats"><div class="result-stat"><span>Enemies slain</span><strong>${killed}&thinsp;/&thinsp;${enemies.length}</strong></div><div class="result-stat"><span>Allies standing</span><strong>${survived}&thinsp;/&thinsp;${players.length}</strong></div><div class="result-stat"><span>Rounds fought</span><strong>${combatState.round_number}</strong></div>${reward.xp_awarded?`<div class="result-stat"><span>XP earned</span><strong>+${reward.xp_awarded}</strong></div>`:''}${reward.loot?`<div class="result-stat"><span>Loot found</span><strong>${safe(reward.loot)}</strong></div>`:''}${reward.leveled_up?`<div class="result-level">⬆ Level up!</div>`:''}</div><div class="result-log">${logLines}</div>`;
  $('#combatResultModal').hidden=false;
}
function closeCombat(){stopCombatPlay();$('#combatOverlay').classList.remove('open');combatState=null}
function computeCombatAffordances(){
 combatReachable=new Set();combatAttackable={};combatSpellTargets={};
 if(!combatState||combatState.status!=='active')return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 if(!human||combatState.current_unit_id!==human.id)return;
 const obstacles=new Set(combatState.obstacles.map(([x,y])=>tileKey(x,y)));
 const occupied=new Set(combatState.units.filter(u=>u.is_active&&u.id!==human.id).map(u=>tileKey(u.x,u.y)));
 const moveRemaining=combatState.turn_state?.movement_remaining??6;
 const visited=new Map();visited.set(tileKey(human.x,human.y),0);
 const queue=[[human.x,human.y]];
 while(queue.length){
  const [cx,cy]=queue.shift();const d=visited.get(tileKey(cx,cy));
  if(d>=moveRemaining)continue;
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
   const unit=unitByTile[key]||(combatState.units.find(u=>!u.is_active&&u.unit_type==='player'&&u.x===x&&u.y===y));
   let inner='';
   if(unit){
    const side=unit.unit_type==='player'?'side-player':'side-enemy';
    const current=combatState.current_unit_id===unit.id?'current-turn':'';
    const unconscious=!unit.is_active&&unit.unit_type==='player';
    const pct=Math.max(0,Math.round(unit.hp/unit.max_hp*100));
    const label=unconscious?`${safe(unit.unit_name.slice(0,2).toUpperCase())}💀`:`${safe(unit.unit_name.slice(0,2).toUpperCase())}`;
    inner=`<div class="combat-unit ${side} ${current}${unconscious?' unconscious':''}" title="${safe(unit.unit_name)} ${unconscious?'(Unconscious)':'('+unit.hp+'/'+unit.max_hp+')'}">${label}<div class="hp-bar"><i style="width:${pct}%"></i></div></div>`;
   }
   html+=`<div class="${classes.join(' ')}" data-x="${x}" data-y="${y}">${inner}</div>`;
  }
 }
 const _board=$('#combatBoard');_board.style.setProperty('--cb-cols',combatState.grid_width);_board.style.setProperty('--cb-rows',combatState.grid_height);_board.innerHTML=html;
 $$('#combatBoard .combat-tile').forEach(tile=>tile.onclick=()=>onCombatTileClick(+tile.dataset.x,+tile.dataset.y));
 $('#combatTurnList').innerHTML=combatState.turn_order.map(uid=>combatState.units.find(u=>u.id===uid)).filter(Boolean).map(u=>{
  const side=u.unit_type==='player'?'side-player':'side-enemy';
  const current=combatState.current_unit_id===u.id?'current':'';
  return `<div class="combat-turn-card ${side} ${current}"><div class="portrait combat-unit ${side}">${safe(u.unit_name.slice(0,2).toUpperCase())}</div><div><strong>${safe(u.unit_name)}</strong><small>${u.is_active?`${u.hp}/${u.max_hp} HP`:'Defeated'}</small></div></div>`;
 }).join('');
 $('#combatLog').innerHTML=(combatState.log||[]).slice().reverse().map(line=>`<div>${safe(line)}</div>`).join('');
 $('#combatRoundInfo').textContent=`Round ${combatState.round_number}`;
 const ts=combatState.turn_state||{};
 const actionUsed=!!ts.action_used;
 const moveRemaining2=ts.movement_remaining??6;
 const hasDash=!!(ts.conditions||[]).includes('dashing');
 const hasDodge=!!(ts.conditions||[]).includes('dodging');
 const hasDisengage=!!(ts.conditions||[]).includes('disengaging');
 $('#combatEndTurnBtn').disabled=!isHumanTurn;
 const dashBtn=$('#combatDashBtn');const disBtn=$('#combatDisengageBtn');const dodgeBtn=$('#combatDodgeBtn');
 if(dashBtn){dashBtn.disabled=!isHumanTurn||actionUsed;dashBtn.classList.toggle('cb-play-active',hasDash);}
 if(disBtn){disBtn.disabled=!isHumanTurn||actionUsed;disBtn.classList.toggle('cb-play-active',hasDisengage);}
 if(dodgeBtn){dodgeBtn.disabled=!isHumanTurn||actionUsed;dodgeBtn.classList.toggle('cb-play-active',hasDodge);}
 const spell=selectedSpell();
 const canPowerAttack=isHumanTurn&&!spell&&(human.stats.feats||[]).some(f=>POWER_ATTACK_FEATS.has(f));
 $('#combatPowerAttackLabel').hidden=!canPowerAttack;
 if(!canPowerAttack)$('#combatPowerAttack').checked=false;
 const castBtn=$('#combatCastBtn');
 const needsNoTarget=spell&&spell.data&&!['attack','save','heal'].includes(spell.data.effect_type);
 castBtn.hidden=!needsNoTarget;
 if(!isHumanTurn)castBtn.hidden=true;
 let hintText='';
 if(combatState.status==='active'){
  if(isHumanTurn){
   const movePart=`Move: ${moveRemaining2}/${hasDash?12:6} tiles`;
   const actPart=actionUsed?'Action: Used':'Action: Available';
   if(spell)hintText=`${movePart} | ${actPart} — Click a highlighted target to cast ${spell.name}.`;
   else hintText=`${movePart} | ${actPart} — Click a tile to move or an enemy to attack.`;
  }else{hintText='Waiting for other combatants…';}
 }
 $('#combatHint').textContent=hintText;
 const outcome=$('#combatOutcome');
 if(combatState.status!=='active'){
  stopCombatPlay();
  outcome.hidden=false;outcome.className=`combat-outcome ${combatState.status}`;
  outcome.textContent=combatState.status==='won'?`Victory!${combatState.reward?.loot?` +${combatState.reward.xp_awarded} XP, found: ${combatState.reward.loot}`:''}`:'Defeat… the enemies overwhelm you.';
  $('#combatPlayBtn').hidden=true;$('#combatEndTurnBtn').hidden=true;$('#combatDashBtn').hidden=true;$('#combatDisengageBtn').hidden=true;$('#combatDodgeBtn').hidden=true;$('#combatResultBtn').hidden=false;$('#combatEndBtn').hidden=false;
 }else{
  outcome.hidden=true;$('#combatPlayBtn').hidden=false;$('#combatEndTurnBtn').hidden=false;$('#combatDashBtn').hidden=false;$('#combatDisengageBtn').hidden=false;$('#combatDodgeBtn').hidden=false;$('#combatResultBtn').hidden=true;$('#combatEndBtn').hidden=true;
 }
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
async function combatSpecialAction(action){
 if(!combatState)return;
 const human=combatState.units.find(u=>u.stats?.is_human);
 if(!human)return;
 try{const result=await api(`/api/combat/${combatState.id}/special-action`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({unit_id:human.id,action})});combatState=result;renderCombat()}catch(error){toast(error.message)}
}
$('#combatDashBtn').onclick=()=>combatSpecialAction('dash');
$('#combatDisengageBtn').onclick=()=>combatSpecialAction('disengage');
$('#combatDodgeBtn').onclick=()=>combatSpecialAction('dodge');
$('#combatPlayBtn').onclick=()=>{if(combatAutoTimer){stopCombatPlay();}else{combatAutoTimer=setInterval(combatAutoStep,1500);$('#combatPlayBtn').textContent='⏸ Pause';$('#combatPlayBtn').classList.add('cb-play-active');}};
$('#combatResultBtn').onclick=showCombatResult;
$('#combatEndBtn').onclick=async()=>{stopCombatPlay();closeCombat();await refreshCharacterState();renderParty();showPanel('character');};
$('#combatResultCloseBtn').onclick=()=>{$('#combatResultModal').hidden=true;};
$('#combatResultEndBtn').onclick=async()=>{$('#combatResultModal').hidden=true;stopCombatPlay();closeCombat();await refreshCharacterState();renderParty();showPanel('character');};

// ── Explorer Random button ──
const _randLibBtn=$('#randomLibraryBtn');
if(_randLibBtn)_randLibBtn.onclick=async()=>{
 try{
  const result=await api('/api/explore/library?query=&race=All&limit=400');
  const all=result.characters||[];
  const shuffled=[...all].sort(()=>Math.random()-.5).slice(0,12);
  renderExploreCards(shuffled,$('#libraryResults'),async(character,btn)=>{
   btn.disabled=true;
   try{await api('/api/explore/library/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character})});btn.textContent='Imported';toast(`${character.name} imported`)}
   catch(error){toast(error.message);btn.disabled=false}
  });
  const cnt=$('#libraryCount');if(cnt)cnt.textContent=`Random 12 / ${all.length}`;
 }catch(error){toast(error.message)}
};

// ── Auto-generate scenario ──
const _autoGenBtn=$('#autoGenScenarioBtn');
if(_autoGenBtn)_autoGenBtn.onclick=async()=>{
 const worldName=state.worlds?.[state.worldIndex]?.name||'';
 const genre=state.pendingCategory?.label||'Fantasy';
 _autoGenBtn.textContent='✦ Generating…';
 try{
  const {scenario}=await api('/api/scenario/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({world_name:worldName,genre,story_preset:'',session_id:state.sessionId||'default'})});
  const ta=$('#customScenarioForm')?.elements?.text;
  if(ta){ta.value=scenario;toast('Scenario generated!');}
 }catch(err){toast('Auto-generate failed')}
 finally{_autoGenBtn.textContent='✦ Auto-generate from world & preset'}
};

fillPortraitStyles();openView('play');
initPlay();

// ═══════════════════════════════════════════════════
// Extended Character Creation — v6 System
// ═══════════════════════════════════════════════════
const V6_WEAPON_TYPES=["Sword","Greatsword","Rapier","Katana","Scimitar","Bow","Longbow","Crossbow","Gun","Rifle","Dual Pistols","Staff","Wand","Sceptre","Spear","Halberd","Trident","Javelin","Martial Arts","Boxing","Kickboxing","Magic Weapon","Enchanted Blade","Spirit Weapon","Dual Weapons","Dual Swords","Dual Daggers","Axe","Battleaxe","Hammer","War Hammer","Dagger","Hidden Blade","Throwing Knives","Whip","Chain Whip","Flail","Scythe","Nunchaku","Tonfas","Shield + Sword","Zanpakuto","Keyblade","Gunblade","Claws","Gauntlets","Fists","Phaser","Staff Weapon","Zat'nik'tel","Bat'leth","Custom"];
const V6_MAGIC_TYPES=["Fire","Water","Earth","Wind","Lightning","Ice","Light","Dark","Healing","Summoning","Necromancy","Chaos","Sound","Divine","Wood","Curse","Death","Undead","Poison","Metal","Gravity","Time","Space","Blood","Nature","Psychic","Illusion","Enchantment","Divination","Abjuration","Transmutation","Conjuration","Shadow","Storm","Lava","Crystal","Sand","Void","Soul","Spirit","Rune","Arcane","Celestial","Infernal","Fey","Dream","Astral","Custom"];
const V6_POWER_SYSTEMS=["Mana","Chakra","Qi / Ki","Spiritual Energy","Reiatsu","Soul Ring (Soul Land)","Devil Fruit (One Piece)","Guild Magic (Fairy Tail)","Haki","Nen (HxH)","Cursed Energy (JJK)","Breathing (Demon Slayer)","Alchemy (FMA)","Stands (JoJo)","The Force","Biotics","Aura (RWBY)","Domain Expansion","Quirk (MHA)","Psionic","Naquadah Enhanced","Ancient Gene","Custom"];
const V6_EMOTION_STYLES=["Friendly","Serious","Mysterious","Romantic","Aggressive","Wise","Playful","Naughty","Confident","Calculative","Carefree","Mischievous","Bold","Strategic","Relaxed","Seductive","Cold","Warm","Sarcastic","Shy","Dominant","Submissive","Protective","Jealous","Tsundere","Yandere","Kuudere","Lustful","Teasing","Sadistic","Masochistic"];
const V6_TRAITS_LIST=["Alert","Athlete","Actor","Charger","Defensive Duelist","Dual Wielder","Durable","Elemental Adept","Grappler","Great Weapon Master","Healer","Heavy Armour Master","Inspiring Leader","Keen Mind","Lucky","Mage Slayer","Magic Initiate","Mobile","Observant","Polearm Master","Resilient","Savage Attacker","Sentinel","Sharpshooter","Shield Master","Skilled","Skulker","Spell Sniper","Tavern Brawler","Tough","War Caster","Weapon Master","Elemental Affinity","Quick Reflexes","Iron Will","Silver Tongue","Beast Bond","Shadow Walker","Battle Instinct","Natural Leader","Tactical Mind","Berserker Rage","Eagle Eye","Cat-like Reflexes","Stone Skin","Night Vision","Sixth Sense","Photographic Memory","Fearless","Empathic","Intimidating Presence","Danger Sense","Brave","Custom"];
const V6_QUIRKS_LIST=["Talks to self","Collects oddities","Never sits still","Always humming","Laughs at danger","Superstitious","Compulsive liar","Always late","Overly polite","Talks to animals","Collects rare objects","Sleeps very little","Eats constantly","Speaks in riddles","Whistles when nervous","Counts everything","Afraid of heights","Loves bad puns","Never removes gloves","Narrates own actions","Dramatic entrances","Afraid of the dark","Hoards food","Talks in third person","Refuses to lie","Custom"];
const V6_SKILLS_LIST=["Acrobatics","Animal Handling","Arcana","Athletics","Deception","History","Insight","Intimidation","Investigation","Medicine","Nature","Perception","Performance","Persuasion","Religion","Sleight of Hand","Stealth","Survival","Cooking","Blacksmithing","Alchemy","Herbalism","Lockpicking","Enchanting","Cartography","Sailing","Riding","Climbing","Swimming","Tracking","First Aid","Negotiation","Gambling","Disguise","Potion Brewing","Beast Taming","Strategy","Leadership","Hacking","Programming","Engineering","Piloting","Diplomacy","Espionage","Seduction","Custom"];
const V6_CHAR_TAGS=["Mom","Daughter","Wife","Girlfriend","Sister","Aunt","Cousin","Grandmother","Boyfriend","Husband","Father","Brother","Son","Uncle","Grandfather","Fiance(e)","Crush","Childhood Friend","Bestie","Rival","Frenemy","Co-worker","Boss","Classmate","Teacher","Student","Mentor","Apprentice","Tsundere","Yandere","Kuudere","Bad Boy","Bad Girl","Good Girl","Good Boy","Nerd","Jock","Goth","Punk","Adult","Mature","Fantasy","Sci-Fi","Modern","Historical","Supernatural","Mafia","Crime","Mystery","Horror","Romance","Drama","Villain","Anti-Hero","Companion","Royalty","Alien","Robot","Angel","Demon","Vampire","Werewolf","Ghost","Witch","God/Goddess","Neko","Kitsune","Adventure","Family","Forbidden","Taboo","Maid","Butler","Nurse","Custom"];
const V6_BODY_TYPES=["Slim","Athletic","Average","Muscular","Curvy","Voluptuous","Petite","Tall","Short","Stocky","Elegant","Rugged","Thicc","Toned","Hourglass","Pear","Slender","Plus-size","Statuesque","Wiry","Custom"];
const V6_GENDERS=["Male","Female","Non-binary","Androgynous","Gender-fluid","Custom"];
const V6_LANGUAGES=["Common","Elvish","Dwarvish","Draconic","Giant","Gnomish","Halfling","Infernal","Orc","Celestial","Sylvan","Undercommon","Primordial","Aquan","Auran","Abyssal","Deep Speech","Druidic","Thieves' Cant","Vulcan","Klingon","Goa'uld","Ancient","Minbari","Narn","Centauri","Gith"];
const V6_SKIN_OPTS=["Fair","Pale","Tan","Brown","Dark","Olive","Golden","Ebony","Red","Purple","Blue","Grey","Green","Bronze","Copper","Silver","Orange","Scaled","Pale Gold","Luminous","Spotted","Custom"];
const V6_HAIR_OPTS=["Black","Brown","Blonde","Red","Auburn","Grey","White","Silver","Gold","Copper","Platinum","Blue","Purple","Pink","Orange","Green","None","Custom"];
const V6_EYES_OPTS=["Brown","Blue","Green","Grey","Hazel","Amber","Gold","Silver","Violet","Red","Black","All-black","Heterochromic","Glowing","Custom"];

let v6Inited=false;
function fillV6Sel(id,arr){const el=$(id);if(!el)return;el.innerHTML=arr.map(v=>`<option value="${safe(v)}">${safe(v)}</option>`).join('');}
function setMultiSel(id,vals){const el=$(id);if(!el)return;const s=new Set(vals||[]);Array.from(el.options).forEach(o=>o.selected=s.has(o.value));}
function pickRnd(arr){return arr[Math.floor(Math.random()*arr.length)];}
function pickN(arr,n){const s=[...arr];for(let i=s.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[s[i],s[j]]=[s[j],s[i]];}return s.slice(0,n);}

function v6BuildRandom(){
  const races=Object.keys(studioOptions.races||{});
  const race=pickRnd(races)||'Human';
  const g=pickRnd(V6_GENDERS.slice(0,3));
  const profs=studioOptions.professions||[];
  const bgs=studioOptions.backgrounds||[];
  const aligns=studioOptions.alignments||[];
  const origins=studioOptions.origins||[];
  const names_m=["Aldric","Kael","Theron","Dax","Riven","Zane","Caspian","Fenris","Draven","Orion","Lucian","Talon","Ash","Blaze","Rex"];
  const names_f=["Lyra","Seraphina","Aria","Nova","Elara","Freya","Nyx","Zara","Kira","Luna","Ember","Sage","Ivy","Raven","Jade"];
  const names_n=["Morgan","Rowan","Quinn","Avery","Phoenix","River","Storm","Wren","Sky","Onyx","Echo","Vale","Aspen","Kai"];
  const nl=g==='Male'?names_m:g==='Female'?names_f:names_n;
  const stat=()=>6+Math.floor(Math.random()*13);
  return{
    name:pickRnd(nl)+'_'+(10+Math.floor(Math.random()*90)),
    race,gender:g,age:18+Math.floor(Math.random()*182),
    alignment:pickRnd(aligns)||'True Neutral',
    background:pickRnd(bgs)||'Hermit',
    profession:pickRnd(profs)||'Adventurer',
    origin:pickRnd(origins)||'Original fantasy world',
    power_tier:Math.floor(Math.random()*5),
    skin:pickRnd(V6_SKIN_OPTS.slice(0,-1)),
    hair:pickRnd(V6_HAIR_OPTS.slice(0,-1)),
    eyes:pickRnd(V6_EYES_OPTS.slice(0,-1)),
    body_type:pickRnd(V6_BODY_TYPES.slice(0,-1)),
    height:`${4+Math.floor(Math.random()*3)}'${Math.floor(Math.random()*12)}"`,
    bust_chest:`${28+Math.floor(Math.random()*16)}"`,
    waist:`${22+Math.floor(Math.random()*14)}"`,
    hips:`${30+Math.floor(Math.random()*16)}"`,
    languages:['Common'],
    strength:stat(),dexterity:stat(),intelligence:stat(),wisdom:stat(),constitution:stat(),speed:stat(),luck:stat(),charisma_stat:stat(),
    looks:4+Math.floor(Math.random()*6),
    weapon_training:pickN(V6_WEAPON_TYPES.slice(0,-1),2),
    magic_type:pickN(V6_MAGIC_TYPES.slice(0,-1),2),
    power_system:[pickRnd(V6_POWER_SYSTEMS.slice(0,-1))],
    emotion_styles:pickN(V6_EMOTION_STYLES,2),
    traits:pickN(V6_TRAITS_LIST.slice(0,-1),2),
    quirks:[pickRnd(V6_QUIRKS_LIST.slice(0,-1))],
    skills:pickN(V6_SKILLS_LIST.slice(0,-1),3),
    tags:pickN(V6_CHAR_TAGS.slice(0,-1),3),
    backstory:'',scenario:'',goals:''
  };
}

function v6FillForm(ch){
  const form=$('#characterFormV6');if(!form)return;
  const set=(name,val)=>{const e=form.elements[name];if(e&&e.type!=='range')e.value=val??'';};
  ['name','age','height','bust_chest','waist','hips','backstory','scenario','goals','gender','race','secondary_ancestry','alignment','background','profession','origin','skin','hair','eyes','body_type'].forEach(k=>set(k,ch[k]??''));
  const pt=$('#v6ptSelect');if(pt)pt.value=ch.power_tier??0;
  ['strength','dexterity','intelligence','wisdom','constitution','speed','luck','charisma_stat','looks'].forEach(s=>{
    const e=form.elements[s];if(e&&e.type==='range'){e.value=ch[s]??10;e.dispatchEvent(new Event('input'));}
  });
  setMultiSel('#v6langSelect',ch.languages);
  setMultiSel('#v6weaponSelect',ch.weapon_training);
  setMultiSel('#v6magicSelect',ch.magic_type);
  setMultiSel('#v6powerSelect',ch.power_system);
  setMultiSel('#v6emotionSelect',ch.emotion_styles);
  setMultiSel('#v6traitsSelect',ch.traits);
  setMultiSel('#v6quirksSelect',ch.quirks);
  setMultiSel('#v6skillsSelect',ch.skills);
  setMultiSel('#v6tagsSelect',ch.tags);
}

function initCharFormV6(){
  if(v6Inited)return;
  const form=$('#characterFormV6');if(!form)return;
  v6Inited=true;
  // Populate selects from studioOptions + static lists
  fillV6Sel('#v6genderSelect',V6_GENDERS);
  fillV6Sel('#v6raceSelect',Object.keys(studioOptions.races||{}));
  const sec=$('#v6secAncestrySelect');if(sec){sec.innerHTML='<option value="">— None —</option>';Object.keys(studioOptions.races||{}).forEach(r=>{sec.innerHTML+=`<option value="${safe(r)}">${safe(r)}</option>`;});}
  fillV6Sel('#v6alignSelect',studioOptions.alignments||[]);
  fillV6Sel('#v6bgSelect',studioOptions.backgrounds||[]);
  fillV6Sel('#v6profSelect',studioOptions.professions||[]);
  fillV6Sel('#v6originSelect',studioOptions.origins||[]);
  const pt=$('#v6ptSelect');if(pt){pt.innerHTML=(studioOptions.powerTiers||[]).map(t=>`<option value="${t.tier}">${t.tier} · ${safe(t.name)}</option>`).join('');}
  fillV6Sel('#v6skinSelect',V6_SKIN_OPTS);
  fillV6Sel('#v6hairSelect',V6_HAIR_OPTS);
  fillV6Sel('#v6eyesSelect',V6_EYES_OPTS);
  fillV6Sel('#v6bodySelect',V6_BODY_TYPES);
  fillV6Sel('#v6langSelect',V6_LANGUAGES);
  fillV6Sel('#v6weaponSelect',V6_WEAPON_TYPES);
  fillV6Sel('#v6magicSelect',V6_MAGIC_TYPES);
  fillV6Sel('#v6powerSelect',V6_POWER_SYSTEMS);
  fillV6Sel('#v6emotionSelect',V6_EMOTION_STYLES);
  fillV6Sel('#v6traitsSelect',V6_TRAITS_LIST);
  fillV6Sel('#v6quirksSelect',V6_QUIRKS_LIST);
  fillV6Sel('#v6skillsSelect',V6_SKILLS_LIST);
  fillV6Sel('#v6tagsSelect',V6_CHAR_TAGS);
}

// v6 tab switching
const _v6tabSingle=$('#v6tabSingle'),_v6tabMulti=$('#v6tabMulti');
if(_v6tabSingle&&_v6tabMulti){
  _v6tabSingle.onclick=()=>{$('#v6tab-single').hidden=false;$('#v6tab-multi').hidden=true;_v6tabSingle.style.borderColor='var(--gold)';_v6tabSingle.style.color='var(--gold)';_v6tabMulti.style.borderColor='';_v6tabMulti.style.color='';};
  _v6tabMulti.onclick=()=>{$('#v6tab-single').hidden=true;$('#v6tab-multi').hidden=false;_v6tabMulti.style.borderColor='var(--gold)';_v6tabMulti.style.color='var(--gold)';_v6tabSingle.style.borderColor='';_v6tabSingle.style.color='';};
}

// v6 form submit
const _v6form=$('#characterFormV6');
if(_v6form)_v6form.onsubmit=async event=>{
  event.preventDefault();
  const fd=new FormData(event.currentTarget);
  const payload=Object.fromEntries(fd.entries());
  const multiKeys=['weapon_training','magic_type','power_system','traits','quirks','emotion_styles','languages','skills','tags'];
  multiKeys.forEach(k=>{payload[k]=fd.getAll(k);});
  payload.age=Number(payload.age||25);
  payload.level=Number(payload.level||1);
  payload.looks=Number(payload.looks||5);
  payload.power_tier=Number(payload.power_tier??0);
  ['strength','dexterity','intelligence','wisdom','constitution','speed','luck','charisma_stat'].forEach(k=>{payload[k]=Number(payload[k]||10);});
  payload.origin_world=state.worlds[state.worldIndex]?.name||'Aethoria Prime';
  try{
    const created=await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    toast(`${payload.name} saved`);
    event.currentTarget.reset();
    // Reset range spans
    ['str','dex','int','wis','con','spd','lck','cha'].forEach((k,i)=>{const id='v6'+k+'Val';const el=$(id);if(el)el.textContent='10';});
    $('#v6lksVal') && ($('#v6lksVal').textContent='5');
    await loadCharacterStudio();
    if(created?.id&&!state.characterId){state.characterId=created.id;await refreshCharacterState();renderParty();renderQuests();toast(`${payload.name} is now your active adventurer`);}
  }catch(err){toast(err.message);}
};

// v6 randomize
const _rndV6=$('#rndCharV6');
if(_rndV6)_rndV6.onclick=()=>{if(!Object.keys(studioOptions).length){toast('Loading options…');return;}v6FillForm(v6BuildRandom());toast('Random character generated');};

// v6 random height button
const _v6rh=$('#v6randHeight');
if(_v6rh)_v6rh.onclick=()=>{
  const raceEl=$('#v6raceSelect');const race=raceEl?raceEl.value:'Human';
  const h=48+Math.floor(Math.random()*36);
  const inp=$('#v6heightInp');if(inp)inp.value=`${Math.floor(h/12)}'${h%12}"`;
};

// v6 random measurements
const _v6rm=$('#v6randMeasure');
if(_v6rm)_v6rm.onclick=()=>{
  const b=$('#v6bust'),w=$('#v6waist'),h=$('#v6hips');
  if(b)b.value=`${28+Math.floor(Math.random()*16)}"`;
  if(w)w.value=`${22+Math.floor(Math.random()*14)}"`;
  if(h)h.value=`${30+Math.floor(Math.random()*16)}"`;
};

// v6 multi-character generation
let _v6multiChars=[];
const _v6gen=$('#v6genGroup');
if(_v6gen)_v6gen.onclick=()=>{
  if(!Object.keys(studioOptions).length){toast('Loading options…');return;}
  const num=Math.min(10,Math.max(2,Number($('#v6multiNum').value)||3));
  const group=$('#v6groupName').value||'The Party';
  _v6multiChars=Array.from({length:num},(_,i)=>{const ch=v6BuildRandom();ch.scenario=`Member of: ${group}`;return ch;});
  const res=$('#v6multiResults');
  if(!res)return;
  res.innerHTML=_v6multiChars.map((ch,i)=>`
    <div class="v6-multi-card">
      <h4>${i+1}. ${safe(ch.name)} — ${safe(ch.race)} ${safe(ch.gender)} ${safe(ch.profession)}</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10px;color:var(--muted)">
        <span>Alignment: ${safe(ch.alignment)}</span><span>Level: 1</span>
        <span>STR ${ch.strength} DEX ${ch.dexterity} INT ${ch.intelligence}</span>
        <span>WIS ${ch.wisdom} CON ${ch.constitution} CHA ${ch.charisma_stat}</span>
        <span>Weapons: ${(ch.weapon_training||[]).join(', ')||'—'}</span>
        <span>Magic: ${(ch.magic_type||[]).join(', ')||'—'}</span>
      </div>
    </div>
  `).join('');
  const sr=$('#v6multiSaveRow');if(sr)sr.hidden=false;
};

const _v6saveAll=$('#v6saveAll');
if(_v6saveAll)_v6saveAll.onclick=async()=>{
  if(!_v6multiChars.length){toast('Generate a group first');return;}
  _v6saveAll.disabled=true;_v6saveAll.textContent='Saving…';
  try{
    for(const ch of _v6multiChars){
      ch.origin_world=state.worlds[state.worldIndex]?.name||'Aethoria Prime';
      await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(ch)});
    }
    toast(`${_v6multiChars.length} characters saved`);
    _v6multiChars=[];$('#v6multiResults').innerHTML='';$('#v6multiSaveRow').hidden=true;
    await loadCharacterStudio();
  }catch(err){toast(err.message);}
  finally{_v6saveAll.disabled=false;_v6saveAll.textContent='💾 Save All Characters';}
};
