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
 {name:'Neon Shard-9',magic:'very_low',tech:'cyberpunk',space:'sci-fi',reality_type:'Parallel Universe',place:'Kairox Undercity',theme:'country'},
 {name:'Earth-Z',magic:'none',tech:'post_collapse',space:'post-apocalyptic',reality_type:'Dead Universe',place:'London Quarantine',theme:'country'},
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
 {name:'Short Rest',icon:'🌙',kind:'rest',cost:'1 hr'},
 {name:'Long Rest',icon:'💤',kind:'rest',cost:'8 hrs'},
];

// ─── Persistent image cache (survives page reload) ────────────────────────────
const IMG_CACHE_KEY='worldweaver-img-cache';
function _loadImgCache(){try{const r=localStorage.getItem(IMG_CACHE_KEY);return r?JSON.parse(r):{};}catch{return {};}}
function _saveImgCache(cache){try{localStorage.setItem(IMG_CACHE_KEY,JSON.stringify(cache));}catch{}}

// ─── Thumbnail generation queue (serialise to respect Pollinations rate limit) ─
const _thumbQueue=[];let _thumbRunning=false;
function _enqueueThumb(fn){
  if(_thumbQueue.length>=20)return;
  _thumbQueue.push(fn);
  if(!_thumbRunning)_drainThumbQueue();
}
async function _drainThumbQueue(){
  _thumbRunning=true;
  while(_thumbQueue.length){
    const fn=_thumbQueue.shift();
    try{await fn();}catch{}
  }
  _thumbRunning=false;
}

let state={worldIndex:0,scale:'local',x:42,y:52,zoom:100,selected:0,characterId:null,worlds:[],flavorWorlds:[],sessionId:'default',sheet:null,inventory:{economy:{},items:[]},quests:[],weaponTiers:[],locations:[],locationImageCache:_loadImgCache(),pendingCategory:null,randomScenarioText:'',hasActiveGame:false,allSpells:{},dndWeapons:{},dndWeaponCategories:[],voiceEnabled:localStorage.getItem('companion-voice')==='true',partyChars:[],partySheets:{},activeSpeaker:null,_savedCharCache:[],npcMemories:{},visitedWorldIds:new Set(),pendingGamePayload:null,spellSlots:null,
 allSkillNodes:{},skillTreeData:{},skillTreeCat:'combat',worldOrgs:[],charMemberships:[],customSpells:[],worldSystems:{economy:{},diplomacy:{}},pendingLevelUp:false};
// 5e spell slot table per caster level (simplified; covers lv 1-20)
const _5E_SLOTS=[[],[2],[3],[4,2],[4,3],[4,3,2],[4,3,3],[4,3,3,1],[4,3,3,2],[4,3,3,3,1],[4,3,3,3,2],[4,3,3,3,2,1],[4,3,3,3,2,1],[4,3,3,3,2,1,1],[4,3,3,3,2,1,1],[4,3,3,3,2,1,1,1],[4,3,3,3,2,1,1,1],[4,3,3,3,2,1,1,1,1],[4,3,3,3,3,1,1,1,1],[4,3,3,3,3,2,1,1,1],[4,3,3,3,3,2,2,1,1]];
function _initSpellSlots(lv){const row=_5E_SLOTS[Math.min(20,Math.max(1,lv))]||_5E_SLOTS[1];return row.map((max,i)=>({level:i+1,max,current:max}));}
const SESSION_KEY='worldweaver-session';
const TERRAIN_ICONS={Forest:'♣',Desert:'▲',Mountain:'⛰',Ocean:'≈',Swamp:'♨',Volcano:'▲',Plains:'❦',City:'⌂',Ruins:'⌂',Space:'✦',Underground:'▼',Tundra:'❄',Jungle:'♣',Savanna:'❦',Canyon:'▲'};
const BUILDING_ICONS={home:'🏠',house:'🏠',cottage:'🏡',hut:'🏠',manor:'🏡',mansion:'🏰',penthouse:'🏙',villa:'🏡',apartment:'🏢',office:'🏢',headquarters:'🏢',shop:'🛍',store:'🛒',market:'🏪',stall:'🏪',boutique:'🛍',cafe:'☕',coffee:'☕',bistro:'☕',restaurant:'🍽',diner:'🍽',dining:'🍽',eatery:'🍽',tavern:'🍺',inn:'🍺',pub:'🍺',bar:'🍺',alehouse:'🍺',academy:'🎓',university:'🎓',college:'🎓',school:'🏫',classroom:'🏫',hallway:'🏫',library:'📚',archive:'📚',dungeon:'⚔',crypt:'💀',tomb:'💀',vault:'💀',jungle:'🌿',grove:'🌿',garden:'🌸',park:'🌳',courtyard:'🌳',orchard:'🌳',forest:'🌲',wood:'🌲',beach:'🏖',shore:'🏖',hotel:'🏨',lodge:'🏨',resort:'🏨',palace:'🏛',court:'🏛',throne:'👑',temple:'⛩',church:'⛪',shrine:'⛩',chapel:'⛪',castle:'🏰',fortress:'🏰',citadel:'🏰',keep:'🏰',tower:'🗼',lighthouse:'🗼',spire:'🗼',arena:'⚔',ring:'⚔',pit:'⚔',hospital:'🏥',clinic:'🏥',infirmary:'🏥',dojo:'🥋',training:'🥋',gym:'🏋',stable:'🐴',barn:'🐮',farm:'🌾',port:'⚓',dock:'⚓',harbor:'⚓',pier:'⚓',cave:'🌑',cavern:'🌑',mine:'⛏',square:'🏪',plaza:'🏛',hall:'🏛',ballroom:'🎭',dormitory:'🛏',dorm:'🛏',kitchen:'🍳',workshop:'🔧',lab:'🔬',laboratory:'🔬',party:'🎉'};
function _buildingIcon(name){const n=(name||'').toLowerCase();for(const[k,v]of Object.entries(BUILDING_ICONS)){if(n.includes(k))return v;}return'⌂';}

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
 return chars.length?Math.max(...chars.map(c=>c.id)):null;
}
async function refreshCharacterState(){
 const sheet=await api(`/api/characters/${state.characterId}/sheet`);
 const [inventory,quests]=await Promise.all([
  api(`/api/characters/${state.characterId}/inventory`),
  api(`/api/quests/active?character_name=${encodeURIComponent(sheet.name||'')}&character_id=${state.characterId||''}`).catch(()=>[]),
 ]);
 state.sheet=sheet; state.inventory=inventory; state.quests=quests||[];
 if(!state.spellSlots){state.spellSlots=_initSpellSlots(sheet.calc_lv||1);}
 // Check for any pending level-up
 try{const pend=await api(`/api/characters/${state.characterId}/level-up/pending`);if(pend.has_pending)state.pendingLevelUp=true;}catch{}
}
function statMod(v){return Math.floor(((v||10)-10)/2)}
function derivedResources(sheet){
 const con=sheet?.total_stats?.constitution?.total ?? 10, int=sheet?.total_stats?.intelligence?.total ?? 10, wis=sheet?.total_stats?.wisdom?.total ?? 10;
 const lv=sheet?.calc_lv ?? sheet?.level ?? 1;
 const maxHp=20+lv*8+statMod(con)*lv;
 const maxMana=10+lv*4+Math.max(statMod(int),statMod(wis))*lv;
 return {maxHp,maxMana};
}
function getHpState(charId,maxHp,maxMana){
 try{const d=JSON.parse(localStorage.getItem('hpState-'+charId)||'null');if(d&&d.maxHp===maxHp&&d.maxMana===maxMana)return d;}catch{}
 return {currentHp:maxHp,currentMp:maxMana,maxHp,maxMana};
}
function setHpState(charId,curHp,curMp,maxHp,maxMana){
 const clamped={currentHp:Math.max(0,Math.min(maxHp,curHp)),currentMp:Math.max(0,Math.min(maxMana,curMp)),maxHp,maxMana};
 try{localStorage.setItem('hpState-'+charId,JSON.stringify(clamped));}catch{}
 state.currentHp=clamped.currentHp;state.currentMp=clamped.currentMp;
}
// ─── Party helpers ───
function _partyAvatarHtml(ch){
  if(ch.photo_path)return`<img src="${safe(ch.photo_path)}" style="width:34px;height:34px;border-radius:50%;object-fit:cover;flex-shrink:0">`;
  return`<div class="portrait" style="flex-shrink:0">${safe((ch.initials||ch.name||'?').slice(0,2).toUpperCase())}</div>`;
}
const isLlmError=t=>/^\[(LM Studio error|Error)\]/.test(t||'');
const llmStatus=(sp,reply)=>isLlmError(reply)?'Start LM Studio on port 1234':sp?`${sp.name} · ${sp.race||sp.profession||''}`.trim():'LM Studio connected';
function llmErrorBubble(reply,msg){
  const text=String(reply||'').replace(/^\[(LM Studio error|Error)\]\s*/,'')||'The storyteller could not be reached.';
  return `<div class="chat-msg gm llm-error-msg"><div class="msg-body"><b>WORLDWEAVER</b><div class="llm-error">⚠ ${safe(text)} <button type="button" class="ghost llm-retry" data-retry="${safe(msg)}">↻ Retry</button></div></div></div>`;
}
// Shows elapsed time on an image loader; returns a function that stops it.
function startGenTimer(el,label='Generating scene'){
  if(!el)return()=>{};
  const t0=Date.now();
  const tick=()=>{const s=Math.round((Date.now()-t0)/1000);el.textContent=`${label}… ${s}s${s>=8?' · images can take up to a minute':''}`;};
  tick();const id=setInterval(tick,1000);
  return()=>clearInterval(id);
}
function savePartyToStorage(){try{localStorage.setItem('party-'+state.sessionId,JSON.stringify(state.partyChars));}catch{}}
function loadPartyFromStorage(){try{const d=localStorage.getItem('party-'+state.sessionId);if(d)state.partyChars=JSON.parse(d);}catch{}}
function addCharToParty(ch){
  if(state.partyChars.find(p=>p.id===ch.id)){toast(`${ch.name} is already in the party`);return;}
  if(state.partyChars.length>=6){toast('Party is full (max 6)');return;}
  state.partyChars.push({id:ch.id,name:ch.name,race:ch.race||'Unknown',profession:ch.profession||'Adventurer',gender:ch.gender||'',photo_path:ch.photo_path||'',initials:(ch.name||'??').slice(0,2).toUpperCase(),level:ch.level||1,backstory:ch.backstory||''});
  // Fetch and cache full sheet for combat context
  api(`/api/characters/${ch.id}`).then(s=>{state.partySheets[ch.id]=s;}).catch(()=>{});
  savePartyToStorage();renderParty();toast(`${ch.name} joined the party!`);
}
window._addStoryChar=async(id)=>{
  try{const chars=await api('/api/characters');const ch=chars.find(c=>c.id===id);if(ch)addCharToParty(ch);}catch{}
};
function updateSpeakerUI(){
  const sp=state.activeSpeaker;
  const hn=$('#chatHeadName'),ai=$('#aiStatus'),ci=$('#chatInput'),eb=$('#exitSpeakerBtn');
  if(sp){
    if(hn)hn.textContent=sp.name;
    if(ai)ai.textContent=`${sp.race||''} ${sp.profession||''}`.trim();
    if(ci)ci.placeholder=`What does ${sp.name} do or say…`;
    if(eb)eb.hidden=false;
  } else {
    if(hn)hn.textContent='WORLDWEAVER AI';
    if(ai)ai.textContent='LM Studio link';
    if(ci)ci.placeholder='Speak, investigate, or describe an action…';
    if(eb)eb.hidden=true;
  }
}
function detectStoryChars(reply){
  const low=reply.toLowerCase();
  for(const ch of (state._savedCharCache||[])){
    if(state.partyChars.find(p=>p.id===ch.id))continue;
    if(ch.name&&ch.name.length>2&&low.includes(ch.name.toLowerCase())){
      toast(`📖 ${ch.name} appears in the story — <button onclick="window._addStoryChar(${ch.id})" style="text-decoration:underline;background:none;border:none;color:var(--gold);cursor:pointer;font-size:inherit">Add to party?</button>`);
    }
  }
  const nameLineRe=/^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-z]+)?)\s*:/gm;
  const knownNames=new Set([...(state._savedCharCache||[]).map(c=>c.name.toLowerCase()),...state.partyChars.map(p=>p.name.toLowerCase())]);
  const SKIP=new Set(['worldweaver','narrator','gm','player','system','note','warning','location','time','scene','act','chapter']);
  let nm;
  while((nm=nameLineRe.exec(reply))!==null){
    const name=nm[1].trim();if(name.length<2||name.length>30)continue;if(SKIP.has(name.toLowerCase()))continue;if(knownNames.has(name.toLowerCase()))continue;
    knownNames.add(name.toLowerCase());
    const world=state.worlds[state.worldIndex];
    api('/api/knowledge/lorebook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:`NPC: ${name}`,content:`${name} appeared in the story in "${world?.name||'this world'}".`,keywords:[name],world_id:world?.id||0,always_active:false})}).catch(()=>{});
    // Record NPC memory — store local cache and persist
    if(state.characterId){
      const fact=`Appeared in ${world?.name||'this world'}`;
      if(!state.npcMemories[name])state.npcMemories[name]=[];
      if(!state.npcMemories[name].includes(fact))state.npcMemories[name].push(fact);
      api('/api/npc-memory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId,npc_name:name,fact,session_id:state.sessionId})}).catch(()=>{});
    }
    toast(`📖 ${name} logged as NPC`);
  }
}
async function loadNpcMemories(){
  if(!state.characterId)return;
  try{
    const rows=await api(`/api/npc-memory?character_id=${state.characterId}`);
    state.npcMemories={};
    for(const r of rows){
      if(!state.npcMemories[r.npc_name])state.npcMemories[r.npc_name]=[];
      state.npcMemories[r.npc_name].push(r.fact);
    }
  }catch{}
}
function renderParty(){
  // Sync main character into partyChars[0]
  if(state.sheet&&state.characterId){
    const mainCh={id:state.characterId,name:state.sheet.name,race:state.sheet.race||'Unknown',profession:state.sheet.profession||'Adventurer',gender:state.sheet.gender||'',photo_path:state.sheet.photo_path||'',initials:(state.sheet.name||'??').slice(0,2).toUpperCase(),level:state.sheet.calc_lv||state.sheet.level||1,backstory:state.sheet.backstory||''};
    const idx=state.partyChars.findIndex(c=>c.id===state.characterId);
    if(idx<0)state.partyChars.unshift(mainCh);
    else state.partyChars[idx]=mainCh;
    // Update player token
    const pt=$('#playerToken');if(pt){const sp=pt.querySelector('span');if(sp)sp.textContent=(state.sheet.name||'??').slice(0,2).toUpperCase();}
  }
  const count=state.partyChars.length;
  const el=$('#partyCount');if(el)el.textContent=`${count} / 6`;
  if(!count){$('#partyList').innerHTML='';return;}
  {const _pp=$('.party-panel'),_gg=$('.game-grid');if(_pp)_pp.classList.remove('party-hidden');if(_gg)_gg.classList.remove('party-collapsed');}
  $('#partyList').innerHTML=state.partyChars.map((ch,i)=>{
    const isSpk=state.activeSpeaker?.id===ch.id;
    const isMain=ch.id===state.characterId;
    const sh=isMain?state.sheet:state.partySheets[ch.id];
    const {maxHp:cMax}=sh?derivedResources(sh):{maxHp:ch.level?20+(ch.level||1)*8:28};
    const hpSt=getHpState(ch.id,cMax,10);
    const hpPct=Math.round(hpSt.currentHp/cMax*100);
    const hpColor=hpPct>50?'var(--green)':hpPct>25?'#e8a020':'var(--red,#c0392b)';
    return`<div class="party-card${isSpk?' active':''}" data-party="${i}" style="cursor:pointer;position:relative" title="${isSpk?'Exit '+safe(ch.name)+'\'s view':'Speak as '+safe(ch.name)}">
      ${_partyAvatarHtml(ch)}
      <div style="flex:1;min-width:0">
        <strong style="font-size:11px">${safe(ch.name)}</strong>
        <small style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${safe(ch.race)} · ${safe(ch.profession)}</small>
        <div style="display:flex;align-items:center;gap:4px;margin-top:2px"><div style="flex:1;height:3px;background:var(--line);border-radius:2px"><div style="width:${hpPct}%;height:100%;background:${hpColor};border-radius:2px;transition:width .3s"></div></div><span style="font-size:8px;color:var(--muted);flex-shrink:0">${hpSt.currentHp}/${cMax}</span></div>
        ${isSpk?'<span style="font-size:9px;color:var(--gold)">● Perspective active</span>':''}
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0">
        <span class="level" style="font-size:9px">LV ${ch.level||1}</span>
        ${!isMain?`<button data-remove-party="${i}" style="font-size:10px;background:none;border:none;color:var(--muted);cursor:pointer;padding:0;line-height:1" title="Remove from party">✕</button>`:''}
      </div>
    </div>`;
  }).join('');
  $$('[data-party]').forEach(card=>card.onclick=e=>{
    if(e.target.closest('[data-remove-party]'))return;
    const i=+card.dataset.party,ch=state.partyChars[i];if(!ch)return;
    if(state.activeSpeaker?.id===ch.id){state.activeSpeaker=null;}
    else{state.activeSpeaker=ch;}
    updateSpeakerUI();renderParty();
    toast(state.activeSpeaker?`Now speaking as ${ch.name} — click again to return to narrator`:'Returned to narrator mode');
  });
  $$('[data-remove-party]').forEach(btn=>btn.onclick=e=>{
    e.stopPropagation();
    const i=+btn.dataset.removeParty,ch=state.partyChars[i];
    if(!ch)return;
    if(state.activeSpeaker?.id===ch.id){state.activeSpeaker=null;updateSpeakerUI();}
    state.partyChars.splice(i,1);delete state.partySheets[ch.id];savePartyToStorage();renderParty();
    toast(`${ch.name} left the party`);
  });
}
function renderQuests(){
 if(!state.quests.length){$('#questList').innerHTML=`<div class="quest"><p>No active quests.</p><div class="quest-progress"><span>Generate one from the current reality</span><button id="genQuestBtn" class="ghost">✦ Generate</button></div></div>`;const b=$('#genQuestBtn');if(b)b.onclick=generateQuest;return}
 $('#questList').innerHTML=state.quests.map((q,i)=>`<div class="quest quest-collapsible" data-qidx="${i}"><div class="quest-header"><b>${i===0?'✦ ':''}${safe(q.title||'Quest')}</b><span class="quest-toggle">▸</span></div><div class="quest-body"><p>${safe(q.description||'')}</p><div class="quest-progress"><span>Progress ${safe(q.progress??0)} · Reward: ${safe(q.reward||'—')}</span><span style="display:flex;gap:4px"><button class="ghost quest-complete-btn" data-qidx="${i}" style="font-size:9px;padding:2px 6px;color:var(--green,#4caf50);border-color:var(--green,#4caf50)">✓ Done</button><button class="ghost quest-fail-btn" data-qidx="${i}" style="font-size:9px;padding:2px 6px;color:#c0392b;border-color:#c0392b" title="Mark as failed">✗ Fail</button><button class="ghost quest-abandon-btn" data-qidx="${i}" style="font-size:9px;padding:2px 6px;color:var(--muted)" title="Abandon silently">—</button></span></div></div></div>`).join('');
 $$('.quest-collapsible').forEach(card=>{
  card.querySelector('.quest-header').onclick=e=>{if(e.target.closest('button'))return;card.classList.toggle('quest-open');const tog=card.querySelector('.quest-toggle');if(tog)tog.textContent=card.classList.contains('quest-open')?'▾':'▸';};
 });
 $$('.quest-complete-btn').forEach(btn=>btn.onclick=()=>completeQuest(+btn.dataset.qidx));
 $$('.quest-fail-btn').forEach(btn=>btn.onclick=()=>failQuest(+btn.dataset.qidx));
 $$('.quest-abandon-btn').forEach(btn=>btn.onclick=()=>abandonQuest(+btn.dataset.qidx));
}
async function completeQuest(idx){
 const q=state.quests[idx];if(!q)return;
 state.quests.splice(idx,1);renderQuests();
 let result={};
 if(q.id){
  try{result=await api(`/api/quests/${q.id}/complete?character_id=${state.characterId||0}`,{method:'POST'});}catch{}
 }
 const xpAwarded=result.xp_awarded||q.xp_reward||40;
 const reward=result.reward||null;
 // Log to chat
 const chatLog=$('#chatLog');
 const rewardLine=reward?`<span style="color:var(--gold)">${safe(reward.icon||'✦')} ${safe(reward.label)}</span>`:`<span style="color:var(--gold)">${safe(q.reward||'Reward')}</span>`;
 chatLog.insertAdjacentHTML('beforeend',chatMsg('gm',`<b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action">✦ Quest Complete: "${safe(q.title)}"</em> ${rewardLine} <span style="color:var(--green,#4caf50)">+${xpAwarded} XP</span></div>`));
 chatLog.scrollTop=chatLog.scrollHeight;
 if(result.sheet){state.sheet=result.sheet;renderParty();}
 // Show quest reward modal
 if(reward)showQuestRewardModal(q.title,xpAwarded,reward);
 else toast(`Quest complete! +${xpAwarded} XP`);
 // Level-up check
 if(result.levelled_up&&result.new_level){
  await levelUp(result.new_level,result.level_up_choices);
 }else if(result.sheet&&state.sheet){
  const newLv=result.sheet.calc_lv||result.sheet.level||1;
  const prevLv=(state.sheet?.calc_lv||state.sheet?.level||1);
  if(newLv>prevLv)await levelUp(newLv);
 }
 sfx('loot');
}
function showQuestRewardModal(questTitle,xp,reward){
 const modal=$('#questRewardModal');if(!modal)return;
 const icon=reward.icon||'✦';
 $('#qrIcon').textContent=icon;
 $('#qrTitle').textContent=`Quest Complete!`;
 $('#qrSub').textContent=questTitle;
 const typeColors={feat:'var(--gold)',spell:'var(--purple)',companion:'#4caf50',title:'var(--gold)',ally:'#2196f3',stat_point:'#ff9800',plot_item:'#e91e63',gold:'var(--gold)',skill:'#00bcd4',item:'var(--muted)'};
 const col=typeColors[reward.type]||'var(--gold)';
 $('#qrBody').innerHTML=`<div style="text-align:center;padding:8px 0 12px"><div style="font-size:36px;margin-bottom:8px">${safe(icon)}</div><div style="font-size:18px;font-weight:bold;color:${col}">${safe(reward.label)}</div>${reward.desc?`<div style="font-size:11px;color:var(--muted);margin-top:4px">${safe(reward.desc)}</div>`:''}<div style="margin-top:12px;font-size:13px;color:var(--green,#4caf50)">+${xp} XP earned</div></div>`;
 modal.hidden=false;
 const close=$('#qrClose');if(close)close.onclick=()=>{modal.hidden=true;};
 modal.onclick=e=>{if(e.target===modal)modal.hidden=true;};
}
async function abandonQuest(idx){
 const q=state.quests[idx];if(!q)return;
 if(q.id){try{await api(`/api/quests/${q.id}`,{method:'DELETE'});}catch{}}
 state.quests.splice(idx,1);renderQuests();toast(`Quest abandoned: ${q.title}`);
}
async function failQuest(idx){
 const q=state.quests[idx];if(!q)return;
 const chatLog=$('#chatLog');
 chatLog.insertAdjacentHTML('beforeend',chatMsg('gm',`<b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action" style="color:var(--muted)">✗ Quest Failed: "${safe(q.title)}"</em></div>`));
 chatLog.scrollTop=chatLog.scrollHeight;
 if(q.id){try{await api(`/api/quests/${q.id}`,{method:'DELETE'});}catch{}}
 state.quests.splice(idx,1);renderQuests();toast(`Quest failed: ${q.title}`);
}
async function generateQuest(){
 if(!state.characterId){goCreateCharacter();return}
 try{const world=state.worlds[state.worldIndex];await api('/api/quests/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_name:state.sheet?.name,character_id:state.characterId,world_id:world?.id})});await refreshCharacterState();renderQuests();toast('New quest generated')}catch(error){toast(error.message)}
}
function goCreateCharacter(){toast('Create your adventurer in the Characters tab first');openView('characters');const nameField=$('#characterFormV6')?.elements?.name;if(nameField){nameField.scrollIntoView({behavior:'smooth'});nameField.focus();}}
function getContextFilter(){
 if(combatState&&combatState.status==='active')return 'combat';
 if(state.activeSpeaker)return 'social';
 return 'explore';
}
function renderActions(filter){
 if(filter===undefined)filter=getContextFilter();
 let visible;
 if(filter==='combat') visible=actions.filter(a=>a.kind==='attack'||a.kind==='defence');
 else if(filter==='social') visible=actions.filter(a=>a.kind==='utility'||a.kind==='rest');
 else visible=actions.filter(a=>a.kind!=='defence'||a.name==='Guard');
 $('#actionBar').innerHTML=visible.map((a,i)=>`<button class="action" data-action="${safe(a.name)}"><kbd>${i+1}</kbd><span class="icon">${a.icon}</span><b>${a.name}</b><small>${a.cost}</small></button>`).join('');
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
 if(name==='Short Rest'||name==='Long Rest'){await doRest(name==='Long Rest');return}
 toast(`${name} readied`);
}
async function doRest(isLong){
 if(!state.characterId){goCreateCharacter();return}
 const {maxHp,maxMana}=derivedResources(state.sheet||{});
 const hpSt=getHpState(state.characterId,maxHp,maxMana);
 const healAmount=isLong?maxHp:Math.max(1,Math.floor(maxHp*0.25));
 const mpAmount=isLong?maxMana:Math.max(1,Math.floor(maxMana*0.25));
 const newHp=Math.min(maxHp,hpSt.currentHp+healAmount);
 const newMp=Math.min(maxMana,hpSt.currentMp+mpAmount);
 setHpState(state.characterId,newHp,newMp,maxHp,maxMana);
 // Heal party members too
 state.partyChars.forEach(pc=>{
  const pSheet=state.partySheets[pc.id];
  if(!pSheet)return;
  const {maxHp:ph,maxMana:pm}=derivedResources(pSheet);
  const pSt=getHpState(pc.id,ph,pm);
  const pHeal=isLong?ph:Math.max(1,Math.floor(ph*0.25));
  const pMpHeal=isLong?pm:Math.max(1,Math.floor(pm*0.25));
  setHpState(pc.id,Math.min(ph,pSt.currentHp+pHeal),Math.min(pm,pSt.currentMp+pMpHeal),ph,pm);
 });
 renderParty();
 if($('#detailContent').innerHTML.includes('Health'))showPanel('character');
 const hours=isLong?8:1;
 try{
  await api(`/api/world/clock/advance?session_id=${encodeURIComponent(state.sessionId||'default')}&minutes=${hours*60}`,{method:'POST'});
  await updateClock();
  if(Math.random()<0.25)triggerRandomEvent();
 }catch{}
 // Restore spell slots on long rest
 if(isLong&&state.spellSlots){
  const lv=state.sheet?.calc_lv||1;
  state.spellSlots=_initSpellSlots(lv);
 }
 toast(isLong?`Long rest complete — fully restored after ${hours} hrs`:`Short rest — healed ${healAmount} HP after 1 hr`);
}
async function lootItem(){
 const world=state.worlds[state.worldIndex];
 const tier=Math.min(10,Math.max(0,world?.ratings?.weapon ?? 2));
 const found=(state.weaponTiers.find(t=>t.tier===tier)||state.weaponTiers[2]);
 const itemName=found.examples[Math.floor(Math.random()*found.examples.length)];
 try{
  await api(`/api/characters/${state.characterId}/inventory`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item_name:itemName,item_type:'weapon',weapon_tier:tier})});
  await refreshCharacterState();
  sfx('loot');
  toast(`Found: ${itemName} (Weapon tier ${tier} · ${found.era})`);
  renderInventory();
 }catch(error){toast(error.message)}
}
// ── Skill Tree SVG renderer ────────────────────────────────────────
const _ATTR_COLORS={strength:'#e53935',dexterity:'#43a047',constitution:'#fb8c00',intelligence:'#7b1fa2',wisdom:'#00838f',charisma_stat:'#d81b60'};
function _getNodeColor(node){const attrs=Object.keys(node.attr_req||{});return attrs.length?(_ATTR_COLORS[attrs[0]]||'#546e7a'):'#546e7a';}
function _getAttrReqText(attr_req){const e=Object.entries(attr_req||{});if(!e.length)return '';return e.map(([k,v])=>`${k.replace('_stat','').slice(0,3).toUpperCase()} ${v}`).join(', ');}
function _renderSkillTreeSVG(catNodes,unlocked,unlockable,stats,charLevel){
 const tiers={1:[],2:[],3:[],4:[]};
 catNodes.forEach(n=>{const t=n.tier||1;if(!tiers[t])tiers[t]=[];tiers[t].push(n);});
 const NW=120,NH=52,TIER_Y={1:30,2:190,3:350,4:510};const SVGW=800;const SVGH=600;
 const pos={};
 for(const [tier,nodes] of Object.entries(tiers)){
  const count=nodes.length;const spacing=Math.min((SVGW-60)/(count+1),140);
  const totalW=spacing*(count-1);const startX=(SVGW-totalW)/2-(NW/2);
  nodes.forEach((n,i)=>{pos[n.id]={x:startX+i*spacing,y:TIER_Y[tier]};});
 }
 let lines='',nodesSvg='';
 catNodes.forEach(node=>{
  const p=pos[node.id];if(!p)return;
  (node.children||[]).forEach(childId=>{
   const cp=pos[childId];if(!cp)return;
   const isUnlocked=unlocked.includes(node.id);
   lines+=`<line x1="${p.x+NW/2}" y1="${p.y+NH}" x2="${cp.x+NW/2}" y2="${cp.y}" stroke="${isUnlocked?'#4a6080':'#1e2a38'}" stroke-width="1.5" stroke-dasharray="${isUnlocked?'':'4,4'}"/>`;
  });
 });
 catNodes.forEach(node=>{
  const p=pos[node.id];if(!p)return;
  const isUnlocked=unlocked.includes(node.id);const canUnlock=unlockable.includes(node.id);
  const color=_getNodeColor(node);
  const opacity=isUnlocked?1:canUnlock?0.75:0.35;
  const fill=isUnlocked?color+'22':canUnlock?color+'12':'#0d1520';
  const stroke=isUnlocked?color:canUnlock?color+'88':'#2a3545';
  const sw=isUnlocked?2:canUnlock?1.5:1;
  const textCol=isUnlocked?'#eee':canUnlock?'#aaa':'#555';
  const reqText=_getAttrReqText(node.attr_req);
  const statusIcon=isUnlocked?'✓':canUnlock?'◉':'🔒';
  const statusCol=isUnlocked?color:canUnlock?color+'cc':'#444';
  nodesSvg+=`<g class="skill-svg-node" data-nid="${safe(node.id)}" style="cursor:pointer;opacity:${opacity}">
   <rect x="${p.x}" y="${p.y}" width="${NW}" height="${NH}" rx="6" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>
   <text x="${p.x+NW/2}" y="${p.y+17}" text-anchor="middle" font-size="12" fill="${textCol}" font-family="system-ui">${safe(node.icon||'')} ${safe(node.name)}</text>
   ${reqText?`<text x="${p.x+NW/2}" y="${p.y+30}" text-anchor="middle" font-size="9" fill="${isUnlocked?color+'cc':'#555'}">${safe(reqText)}</text>`:''}
   <text x="${p.x+NW/2}" y="${p.y+43}" text-anchor="middle" font-size="9" fill="${isUnlocked?color+'88':'#444'}">Lv${node.level_req||1} req</text>
   <text x="${p.x+NW-8}" y="${p.y+14}" font-size="10" fill="${statusCol}">${statusIcon}</text>
  </g>`;
 });
 const tierLabels=[1,2,3,4].map(t=>TIER_Y[t]!==undefined?`<text x="8" y="${TIER_Y[t]+28}" font-size="10" fill="#2a4060" font-family="system-ui">T${t}</text>`:''). join('');
 return `<svg viewBox="0 0 ${SVGW} ${SVGH}" xmlns="http://www.w3.org/2000/svg" style="min-width:${SVGW}px;height:${SVGH}px;display:block"><g>${lines}</g><g>${nodesSvg}</g>${tierLabels}</svg>`;
}
async function loadSkillTree(){
 try{
  if(!Object.keys(state.allSkillNodes).length){
   const data=await api('/api/skill-tree/all');
   state.allSkillNodes=data.nodes||{};
  }
  if(state.characterId){
   const st=await api(`/api/characters/${state.characterId}/skill-tree`);
   state.skillTreeData={unlocked:st.unlocked||[],unlockable:st.unlockable||[],skill_points:st.skill_points||0,stats:st.stats||{},level:st.level||1};
  }
 }catch(e){log('Skill tree load failed',e);}
}
async function loadOrganizations(){
 try{
  const worldId=(state.worlds[state.worldIndex]||{}).id;
  if(worldId){const r=await api(`/api/worlds/${worldId}/organizations`);state.worldOrgs=r.organizations||[];}
  if(state.characterId){const r=await api(`/api/characters/${state.characterId}/organizations`);state.charMemberships=r.memberships||[];}
 }catch(e){log('Orgs load failed',e);}
}
async function loadWorldSystems(){
 try{
  const worldId=(state.worlds[state.worldIndex]||{}).id;
  if(!worldId)return;
  const[eco,dip]=await Promise.all([api(`/api/worlds/${worldId}/economy`),api(`/api/worlds/${worldId}/diplomacy`)]);
  state.worldSystems={economy:eco,diplomacy:dip};
 }catch(e){log('World systems load failed',e);}
}
async function loadCustomSpells(){
 try{if(state.characterId){const r=await api(`/api/characters/${state.characterId}/spells/custom`);state.customSpells=r.spells||[];}}catch(e){}
}
const panels={
 character:()=>{
  const s=state.sheet; if(!s) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const stats=s.total_stats||{}; const xp=s.xp_progress||{into:0,need:1,fraction:0};
  const rows=[['STR','strength'],['DEX','dexterity'],['CON','constitution'],['INT','intelligence'],['WIS','wisdom'],['CHA','charisma_stat']];
  const {maxHp,maxMana}=derivedResources(s);
  const hpSt=state.characterId?getHpState(state.characterId,maxHp,maxMana):{currentHp:maxHp,currentMp:maxMana};
  const curHp=hpSt.currentHp;const curMp=hpSt.currentMp;
  const sig=s.reality_signature||{}; const tier=s.power_tier_info||{name:'Heroic'};
  const equippedWeapon=(state.inventory.items||[]).find(it=>it.equip_slot==='weapon');
  const dexMod=statMod((stats.dexterity||{}).total);const strMod=statMod((stats.strength||{}).total);
  const weaponData=equippedWeapon?state.dndWeapons[equippedWeapon.item_name]:null;
  const atkBonus=weaponData?(weaponData.properties?.includes('finesse')?Math.max(strMod,dexMod):strMod):strMod;
  const weaponHtml=equippedWeapon?`<div class="resource"><div><span>⚔ ${safe(equippedWeapon.item_name)}</span><b>${weaponData?weaponData.damage:'—'} ${weaponData?weaponData.damage_type:''} · ATK +${atkBonus>=0?'+':''}${atkBonus}</b></div></div>`:'';
  const pendingLvl=state.pendingLevelUp;
  const lvlBtnStyle=pendingLvl?'background:linear-gradient(135deg,#c8a93e,#e6c35a);color:#000;font-weight:900;animation:glowPulse 1.8s infinite;':'background:var(--panel);color:var(--gold);border-color:var(--gold);';
  const backstory=s.backstory||'';
  const backstoryHtml=`<div class="panel-title" style="margin-top:10px;display:flex;align-items:center;justify-content:space-between"><span>BACKSTORY</span><button id="editBackstoryBtn" class="ghost" style="font-size:10px;padding:2px 8px" onclick="toggleBackstoryEdit()">✏ Edit</button></div><div id="backstoryDisplay" style="font-size:11px;color:var(--muted);line-height:1.6;padding:4px 0;white-space:pre-wrap">${safe(backstory)||'<em>No backstory yet — click Edit to add one.</em>'}</div><div id="backstoryEditBox" hidden style="display:flex;flex-direction:column;gap:6px"><textarea id="backstoryTextarea" rows="12" style="width:100%;background:#0a0f14;border:1px solid var(--line);border-radius:5px;color:#e9ecf1;font-size:11px;line-height:1.6;padding:8px;resize:vertical;box-sizing:border-box">${safe(backstory)}</textarea><div style="display:flex;gap:6px;justify-content:flex-end"><button class="ghost" style="font-size:10px;padding:3px 10px" onclick="cancelBackstoryEdit()">Cancel</button><button class="gold" style="font-size:10px;padding:3px 10px" onclick="saveBackstory()">💾 Save</button></div></div>`;
  return `<div class="character-hero"><div class="hero-portrait">${safe((s.name||'?').slice(0,2).toUpperCase())}</div><h2>${safe(s.name)}</h2><p>${safe(s.race||'Unknown')} · Level ${safe(s.calc_lv||s.level||1)} ${safe(s.profession||'Adventurer')}</p><p>${safe(tier.name)} tier · ${safe(sig.reality_type||'Prime Reality')} (${safe(sig.universe_tag||'—')})</p></div><div class="xp-row"><div><span>EXPERIENCE</span><span>${safe(s.xp||0)} XP (${xp.into}/${xp.need} to next)</span></div><div class="meter"><i style="width:${Math.round((xp.fraction||0)*100)}%"></i></div></div><div class="stats">${rows.map(([label,key])=>`<div class="stat"><b>${(stats[key]||{}).total ?? 10}</b><small>${label} · +${statMod((stats[key]||{}).total)}</small></div>`).join('')}</div><div class="resource"><div><span>Health</span><b>${curHp} / ${maxHp}</b></div><div class="meter"><i style="width:${Math.round(curHp/maxHp*100)}%;background:var(--green)"></i></div></div><div class="resource"><div><span>Mana</span><b>${curMp} / ${maxMana}</b></div><div class="meter"><i style="width:${Math.round(curMp/maxMana*100)}%;background:var(--purple)"></i></div></div>${weaponHtml}<button onclick="openLevelUpModal()" style="${lvlBtnStyle}width:100%;margin-top:10px;padding:9px 0;border:1px solid var(--gold);border-radius:6px;cursor:pointer;font-size:12px;letter-spacing:1px;transition:all .2s">${pendingLvl?'🌟 LEVEL UP READY!':'⬆ Level Up'}</button>${backstoryHtml}`;
 },
 inventory:()=>{
  if(!state.characterId) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const items=state.inventory.items||[];
  const eco=state.inventory.economy||{};
  const equipped=items.filter(it=>it.equip_slot);
  const bag=items.filter(it=>!it.equip_slot);
  const weaponSlot=equipped.find(it=>it.equip_slot==='weapon');
  const ecoHtml=(eco.gold||eco.credits||eco.tokens)?`<div style="display:flex;gap:10px;padding:4px 0 8px;font-size:11px">${eco.gold?`<span>💰 ${eco.gold} gp</span>`:''}${eco.credits?`<span>⚡ ${eco.credits} cr</span>`:''}${eco.tokens?`<span>✦ ${eco.tokens} tk</span>`:''}</div>`:'';
  const slotsHtml=`<div class="panel-title"><span>EQUIPPED</span></div><div style="padding:4px 0 8px">${weaponSlot?`<div style="display:flex;align-items:center;gap:8px;background:#141c24;border:1px solid var(--line);border-radius:4px;padding:6px 8px"><span style="font-size:13px">⚔</span><span style="flex:1;font-size:11px"><b>${safe(weaponSlot.item_name)}</b><br><small>Tier ${weaponSlot.weapon_tier||'?'} · ${safe((weaponSlot.weapon_tier_info||{}).era||'')}</small></span><button class="ghost" data-unequip-id="${weaponSlot.id}" style="font-size:9px;padding:2px 6px;color:var(--muted)">✕</button></div>`:'<div style="color:var(--muted);font-size:11px;padding:4px">No weapon equipped — select one from Armory below</div>'}</div>`;
  const bagHtml=bag.length?`<div class="panel-title"><span>BAG</span><small>${bag.length} items</small></div><div class="inventory-grid">${bag.map(it=>`<button class="item" data-item-id="${it.id}" title="${safe(it.item_name)}">${it.item_type==='weapon'?'⚔':'◇'}<small style="font-size:8px;display:block;max-width:44px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${safe(it.item_name)}</small>${it.quantity>1?`<span style="font-size:8px;color:var(--gold)">${it.quantity}</span>`:''}</button>`).join('')}</div><div id="itemActions" style="min-height:28px;padding:4px 0"></div><div class="item-info"><h3 id="itemName" style="font-size:12px;margin:4px 0">Select an item</h3><p id="itemDesc" style="font-size:11px;color:var(--muted)">Click an item to inspect it.</p></div>`:`<div class="panel-title"><span>BAG</span><small>0 items</small></div><div class="empty-state">Nothing carried yet — try the <b>Loot</b> utility action.</div>`;
  const equippedName=weaponSlot?.item_name;
  const cats=state.dndWeaponCategories.length?state.dndWeaponCategories:[...new Set(Object.values(state.dndWeapons).map(w=>w.category))].sort();
  const armory=cats.map(cat=>{
   const catWeapons=Object.entries(state.dndWeapons).filter(([,w])=>w.category===cat);
   if(!catWeapons.length)return '';
   return `<div class="armory-cat"><small>${safe(cat)}</small>${catWeapons.map(([name,w])=>`<button class="armory-item${name===equippedName?' equipped':''}" data-equip-weapon="${safe(name)}"><b>${safe(name)}</b><small>${safe(w.damage)} ${safe(w.damage_type)}${w.properties.length?` · ${w.properties.join(', ')}`:''}</small>${name===equippedName?'<em>Equipped</em>':''}</button>`).join('')}</div>`;
  }).join('');
  const craftBtn=bag.length>=2?`<div style="padding:4px 0 8px"><button id="openCraftBtn" class="ghost" style="font-size:10px;padding:4px 10px;width:100%">⚗ Craft two items together</button></div>`:'';
  return `${ecoHtml}${slotsHtml}${bagHtml}${craftBtn}<div class="panel-title"><span>ARMORY</span><small>D&amp;D weapons</small></div><div class="armory-grid">${armory}</div>`;
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
 progression:()=>{
  const s=state.sheet;
  if(!s) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const xp=s.xp_progress||{into:0,need:1,fraction:0};
  const lv=s.calc_lv||s.level||1;
  const xpPct=Math.round((xp.fraction||0)*100);
  const feats=s.traits||[]; const spells=s.spells||[]; const skills=s.skills||[];
  const statPts=s.stat_points_available||0; const skillPts=s.skill_points_available||0;
  const STAT_LABELS={strength:'STR',dexterity:'DEX',intelligence:'INT',wisdom:'WIS',constitution:'CON',speed:'SPD',luck:'LCK',charisma_stat:'CHA'};
  const stats=s.total_stats||{};
  const statRows=Object.entries(STAT_LABELS).map(([k,abbr])=>`<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0"><span style="color:var(--muted)">${abbr}</span><b>${(stats[k]||{}).total??s[k]??10}</b></div>`).join('');
  const nextLvXp=xp.need+xp.into;
  const pendingBanner=statPts>0||skillPts>0?`<div style="background:#1a1a00;border:1px solid var(--gold);border-radius:5px;padding:8px 10px;font-size:11px;color:var(--gold);margin-bottom:10px">⭐ ${statPts} attribute point${statPts!==1?'s':''} & ${skillPts} skill point${skillPts!==1?'s':''} pending — open Level-Up to claim</div>`:'';
  return `<div class="panel-title"><span>PROGRESSION</span><small>Level ${lv}</small></div>
${pendingBanner}
<div style="margin-bottom:10px">
 <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px"><span style="color:var(--muted)">XP</span><span>${safe(s.xp||0)} / ${nextLvXp} (Lv ${lv+1})</span></div>
 <div class="meter" style="height:8px;border-radius:4px"><i style="width:${xpPct}%;background:linear-gradient(90deg,var(--gold),#ff9800);border-radius:4px"></i></div>
 <div style="font-size:9px;color:var(--muted);margin-top:2px">${xp.into} / ${xp.need} XP to next level</div>
</div>
<div class="panel-title" style="margin-top:8px"><span>STATS</span></div>
<div style="column-count:2;column-gap:12px">${statRows}</div>
<div class="panel-title" style="margin-top:8px"><span>FEATS</span><small>${feats.length}</small></div>
<div>${feats.length?feats.map(f=>`<div style="font-size:11px;padding:3px 0;border-bottom:1px solid var(--line)">⭐ ${safe(f)}</div>`).join(''):'<div style="font-size:11px;color:var(--muted)">No feats yet</div>'}</div>
<div class="panel-title" style="margin-top:8px"><span>SPELLS</span><small>${spells.length}</small></div>
<div>${spells.length?spells.map(sp=>`<div style="font-size:11px;padding:3px 0;border-bottom:1px solid var(--line)">✨ ${safe(sp)}</div>`).join(''):'<div style="font-size:11px;color:var(--muted)">No spells yet</div>'}</div>
<div class="panel-title" style="margin-top:8px"><span>SKILLS</span><small>${skills.length}</small></div>
<div>${skills.length?skills.map(sk=>`<div style="font-size:11px;padding:3px 0;border-bottom:1px solid var(--line)">🔮 ${safe(sk)}</div>`).join(''):'<div style="font-size:11px;color:var(--muted)">No skills yet</div>'}</div>`;
 },
 skillTree:()=>{
  if(!state.characterId) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const st=state.skillTreeData||{};
  const unlocked=st.unlocked||[];
  const unlockable=st.unlockable||[];
  const sp=st.skill_points||0;
  const nodes=state.allSkillNodes||{};
  const activeCat=state.skillTreeCat||'combat';
  const catIcons={combat:'⚔',defense:'🛡',movement:'💨',magic:'✨',stealth:'👤',social:'💬'};
  const catTabs=['combat','defense','movement','magic','stealth','social'].map(c=>`<button class="skill-cat-tab${c===activeCat?' active':''}" data-cat="${c}">${catIcons[c]||''} ${c.charAt(0).toUpperCase()+c.slice(1)}</button>`).join('');
  const catNodes=Object.values(nodes).filter(n=>n.category===activeCat);
  const svgHtml=catNodes.length?_renderSkillTreeSVG(catNodes,unlocked,unlockable,st.stats||{},st.level||1):'<div class="empty-state">No skills in this category yet. <small>Skill data loading...</small></div>';
  return `<div class="panel-title"><span>SKILL TREE</span><small>${sp} skill point${sp!==1?'s':''} available</small></div>
<div class="skill-cat-tabs" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px">${catTabs}</div>
<div id="skillTreeSvgWrap" style="overflow-x:auto;overflow-y:auto;max-height:520px;padding-bottom:8px;border:1px solid var(--line);border-radius:6px;background:#0a0f14">${svgHtml}</div>
<div id="skillNodeInfo" style="margin-top:8px;min-height:60px;background:#0f1620;border:1px solid var(--line);border-radius:5px;padding:10px;font-size:11px"><span style="color:var(--muted)">Click a node to see details.</span></div>`;
 },
 spells:()=>{
  const known=state.sheet?.spells||[];
  const profession=state.sheet?.profession||'';
  const knownHtml=known.length?known.map(name=>{
   const sp=state.allSpells[name];
   if(!sp)return `<div class="spell-row"><span class="rune">✦</span><span><b>${safe(name)}</b></span></div>`;
   const level=sp.level===0?'Cantrip':`Level ${sp.level}`;
   return `<div class="spell-row"><span class="rune">✦</span><span><b>${safe(name)}</b><small>${level} · ${safe(sp.school)} — ${safe(sp.description?.slice(0,80))}...</small></span></div>`;
  }).join(''):'<div class="empty-state">No spells learned yet.</div>';
  const customSpells=state.customSpells||[];
  const customHtml=customSpells.length?`<div class="panel-title" style="margin-top:8px"><span>CUSTOM SPELLS</span><small>${customSpells.length} story spells</small></div>${customSpells.map(sp=>`<div class="spell-row"><span class="rune">🌟</span><span><b>${safe(sp.name)}</b><small>Lv ${sp.level} ${safe(sp.school)} — ${safe(sp.description?.slice(0,80))}...</small></span></div>`).join('')}`:'';
  const learnable=Object.entries(state.allSpells).filter(([name,sp])=>!known.includes(name)&&(!profession||sp.classes.includes(profession))).slice(0,30);
  const learnHtml=learnable.length?learnable.map(([name,sp])=>{
   const level=sp.level===0?'Cantrip':`Level ${sp.level}`;
   return `<button class="spell-row learnable" data-learn-spell="${safe(name)}"><span class="rune">＋</span><span><b>${safe(name)}</b><small>${level} · ${safe(sp.school)} — ${safe(sp.description?.slice(0,70))}...</small></span></button>`;
  }).join(''):'<div class="empty-state">No more spells for this class.</div>';
  return `<div class="panel-title"><span>SPELLBOOK</span><small>${known.length} prepared</small></div>${knownHtml}${customHtml}<div class="panel-title" style="margin-top:8px"><span>FORGE SPELL</span><small style="color:var(--gold)">✨ from story context</small></div><div style="display:flex;gap:6px;margin-bottom:8px"><input id="customSpellInput" type="text" placeholder='e.g. "Shadow ice that slows enemies"...' style="flex:1;background:#141c24;border:1px solid var(--line);color:#e9ecf1;padding:6px 8px;border-radius:4px;font-size:11px"><button id="forgeSpellBtn" class="gold" style="font-size:11px;padding:4px 10px">Forge</button></div><div class="panel-title"><span>LEARN A SPELL</span><small>${safe(profession||'Any class')}</small></div>${learnHtml}`;
 },
 organizations:()=>{
  if(!state.characterId) return `<div class="empty-state">No adventurer yet.<br><button id="goCreateCharacterBtn" class="gold" style="margin-top:10px">Create a character</button></div>`;
  const orgs=state.worldOrgs||[];
  const memberships=state.charMemberships||[];
  const memberIds=new Set(memberships.map(m=>m.id));
  const memberMap={};memberships.forEach(m=>{memberMap[m.id]=m;});
  const worldId=(state.worlds[state.worldIndex]||{}).id;
  const memberHtml=memberships.length?memberships.map(o=>{
   const ranks=o.ranks||[];const rk=o.member_rank||0;
   const rankName=ranks[rk]||`Rank ${rk}`;const nextRank=ranks[rk+1]||null;
   const benefits=o.benefits||{};const myBenefit=benefits[String(rk)]||'';
   return `<div style="background:#0d1520;border:1px solid var(--gold);border-radius:6px;padding:10px;margin-bottom:8px">
    <div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:12px">${safe(o.name)}</b><span style="font-size:9px;background:#1a2a00;color:var(--gold);padding:2px 6px;border-radius:10px">${safe(rankName)}</span></div>
    <div style="font-size:10px;color:var(--muted);margin:4px 0">${safe(o.org_type)} · ${safe(o.focus)}</div>
    ${myBenefit?`<div style="font-size:10px;color:#7ecf7e;padding:3px 0">✓ ${safe(myBenefit)}</div>`:''}
    ${nextRank?`<button class="ghost" data-rankup-org="${o.id}" style="font-size:9px;padding:2px 8px;margin-top:4px">↑ Rank up to ${safe(nextRank)}</button>`:`<div style="font-size:9px;color:var(--gold);padding:3px 0">★ Max rank achieved</div>`}
    <button class="ghost" data-leave-org="${o.id}" style="font-size:9px;padding:2px 8px;color:var(--muted);margin-top:4px">Leave</button>
   </div>`;
  }).join(''):'';
  const availableOrgs=orgs.filter(o=>!memberIds.has(o.id));
  const availHtml=availableOrgs.map(o=>{
   const ranks=o.ranks||[];
   return `<div style="background:#0a0f14;border:1px solid var(--line);border-radius:6px;padding:10px;margin-bottom:6px">
    <div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:12px">${safe(o.name)}</b><span style="font-size:9px;color:var(--muted);border:1px solid var(--line);padding:2px 6px;border-radius:10px">${safe(o.org_type)}</span></div>
    <div style="font-size:10px;color:var(--muted);margin:4px 0">${safe(o.description?.slice(0,80))}...</div>
    <div style="font-size:9px;color:var(--gold);margin-bottom:6px">Ranks: ${ranks.slice(0,3).join(' → ')}${ranks.length>3?' → ...':''}</div>
    <button class="gold" data-join-org="${o.id}" style="font-size:10px;padding:3px 10px">Join</button>
   </div>`;
  }).join('');
  return `<div class="panel-title"><span>MY MEMBERSHIPS</span><small>${memberships.length} organizations</small></div>
${memberHtml||'<div style="font-size:11px;color:var(--muted);padding:4px 0">Not a member of any organization yet.</div>'}
<div class="panel-title" style="margin-top:10px"><span>AVAILABLE ORGANIZATIONS</span><small>${availableOrgs.length}</small></div>
${availHtml||'<div style="font-size:11px;color:var(--muted)">Loading...</div>'}
${worldId?`<div style="margin-top:10px"><button id="generateOrgBtn" class="ghost" style="font-size:10px;padding:4px 12px;width:100%">✨ Generate story organization</button></div>`:''}`;
 },
 worldSystems:()=>{
  const ws=state.worldSystems||{};
  const eco=ws.economy||{};
  const dip=ws.diplomacy||{};
  const factions=dip.factions||[];
  const diplomacy=dip.diplomacy||[];
  const laws=dip.laws||[];
  const prices=eco.market_prices||[];
  const relColor={'war':'#e53935','hostile':'#ef6c00','cold':'#9e9e9e','neutral':'#546e7a','friendly':'#43a047','allied':'#1565c0'};
  const factionsHtml=factions.map(f=>`<div style="display:flex;justify-content:space-between;font-size:11px;padding:4px 0;border-bottom:1px solid var(--line)"><span><b>${safe(f.name)}</b>${f.leader?` · ${safe(f.leader)}`:''}</span><span style="color:var(--gold)">${f.military_strength||0}⚔ ${f.treasury||0}💰</span></div>`).join('')||'<div style="color:var(--muted);font-size:11px">No factions active</div>';
  const dipHtml=diplomacy.map(r=>`<div style="font-size:10px;padding:3px 0"><span>${safe(r.faction_a)}</span><span style="color:${relColor[r.relation]||'#aaa'};margin:0 6px">— ${safe(r.relation)} —</span><span>${safe(r.faction_b)}</span></div>`).join('')||'<div style="color:var(--muted);font-size:11px">No diplomatic records</div>';
  const lawsHtml=laws.map(l=>`<div style="font-size:10px;padding:3px 0;border-bottom:1px solid var(--line)"><b>${safe(l.law_name)}</b>${l.penalty?` · Penalty: ${safe(l.penalty)}`:''}</div>`).join('')||'<div style="color:var(--muted);font-size:11px">No active laws</div>';
  const pricesHtml=prices.map(p=>`<div style="display:flex;justify-content:space-between;font-size:10px;padding:2px 0"><span>${safe(p.item)}</span><span style="color:var(--gold)">${p.current_price}gp</span></div>`).join('')||'<div style="color:var(--muted);font-size:11px">No market data</div>';
  return `<div class="panel-title"><span>ECONOMY</span></div>
<div style="display:flex;gap:12px;padding:4px 0 10px;font-size:11px">
 <span>🏛 Treasury: <b>${eco.treasury||0}gp</b></span>
 <span>⚖ Law: <b>${eco.law_level||50}/100</b></span>
 <span>🗡 Crime: <b>${eco.crime_level||0}/100</b></span>
 <span>👥 Pop: <b>${eco.population||0}</b></span>
</div>
<div class="panel-title"><span>MARKET PRICES</span></div>
<div style="max-height:120px;overflow-y:auto">${pricesHtml}</div>
<div class="panel-title" style="margin-top:8px"><span>FACTIONS</span><small>${factions.length}</small></div>
<div>${factionsHtml}</div>
<div class="panel-title" style="margin-top:8px"><span>DIPLOMACY</span></div>
<div>${dipHtml}</div>
<div class="panel-title" style="margin-top:8px"><span>ACTIVE LAWS</span><small>${laws.length}</small></div>
<div>${lawsHtml}</div>
<div style="margin-top:10px"><button id="refreshWorldSystemsBtn" class="ghost" style="font-size:10px;padding:4px 12px;width:100%">↻ Refresh world data</button></div>`;
 },
};
function showPanel(name){
 $('#detailContent').innerHTML=panels[name]();
 const createBtn=$('#goCreateCharacterBtn'); if(createBtn)createBtn.onclick=goCreateCharacter;
 if(name==='inventory'){
  $$('[data-item-id]').forEach(el=>el.onclick=()=>{
   const item=(state.inventory.items||[]).find(i=>String(i.id)===el.dataset.itemId);if(!item)return;
   const iname=$('#itemName');if(iname)iname.textContent=item.item_name;
   const idesc=$('#itemDesc');const tierInfo=item.weapon_tier_info||{};if(idesc)idesc.textContent=item.equip_slot?`Weapon tier ${item.weapon_tier} · ${tierInfo.era||''} — ${(tierInfo.properties||[]).join(', ')||'No special properties.'}`:(item.description||'A piece of multiverse adventuring gear.');
   const acts=$('#itemActions');if(acts){acts.innerHTML=`<button class="ghost" data-drop-item="${item.id}" style="font-size:9px;padding:2px 8px;color:var(--muted)">🗑 Drop</button>`;const db=acts.querySelector('[data-drop-item]');if(db)db.onclick=async()=>{try{await api(`/api/characters/${state.characterId}/inventory/${item.id}`,{method:'DELETE'});await refreshCharacterState();renderInventory();toast(`Dropped: ${item.item_name}`);}catch(e){toast(e.message);}};}
  });
  $$('[data-unequip-id]').forEach(el=>el.onclick=async()=>{try{await api(`/api/characters/${state.characterId}/unequip`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slot:'weapon'})});await refreshCharacterState();renderInventory();toast('Weapon unequipped');}catch(e){toast(e.message);}});
  $$('[data-equip-weapon]').forEach(el=>el.onclick=async()=>{try{await api(`/api/characters/${state.characterId}/equip`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({weapon_name:el.dataset.equipWeapon})});await refreshCharacterState();toast(`${el.dataset.equipWeapon} equipped`);renderInventory();}catch(error){toast(error.message)}});
 }
 if(name==='inventory'){
  const craftBtn=$('#openCraftBtn');
  if(craftBtn)craftBtn.onclick=()=>_openCraftModal();
 }
 if(name==='skills')$$('[data-feat]').forEach(el=>el.onclick=async()=>{try{const result=await api(`/api/characters/${state.characterId}/feats`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({feat:el.dataset.feat})});state.sheet=result.sheet;toast(`${el.dataset.feat} learned`);showPanel('skills')}catch(error){toast(error.message)}});
 if(name==='spells'){
  $$('[data-learn-spell]').forEach(el=>el.onclick=async()=>{try{const result=await api(`/api/characters/${state.characterId}/spells`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spell:el.dataset.learnSpell})});state.sheet=result.sheet;toast(`${el.dataset.learnSpell} learned`);showPanel('spells')}catch(error){toast(error.message)}});
  const forgeBtn=$('#forgeSpellBtn');
  if(forgeBtn)forgeBtn.onclick=async()=>{
   const inp=$('#customSpellInput');const desc=inp?inp.value.trim():'';
   if(!desc){toast('Describe your spell first');return;}
   forgeBtn.disabled=true;forgeBtn.textContent='Forging…';
   try{
    const result=await api('/api/spells/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId,description:desc,history:state.chatHistory||[]})});
    if(result.name){toast(`✨ ${result.name} forged!`);if(inp)inp.value='';state.customSpells=null;await loadCustomSpells();showPanel('spells');}
    else toast(result.error||'Forge failed');
   }catch(e){toast(e.message);}finally{forgeBtn.disabled=false;forgeBtn.textContent='Forge';}
  };
 }
 if(name==='skillTree'){
  loadSkillTree().then(()=>showPanel('skillTree'));
  $$('.skill-cat-tab').forEach(el=>el.onclick=()=>{state.skillTreeCat=el.dataset.cat;showPanel('skillTree');});
  $$('.skill-svg-node').forEach(el=>el.onclick=()=>{
   const nid=el.dataset.nodeId;const nodes=state.allSkillNodes||{};const node=nodes[nid];
   const info=$('#skillNodeInfo');if(!info||!node)return;
   const st=state.skillTreeData||{};const unlocked=st.unlocked||[];const unlockable=st.unlockable||[];
   const isUnlocked=unlocked.includes(nid);const canUnlock=unlockable.includes(nid);
   const sp=st.skill_points||0;
   const attrText=Object.entries(node.attr_req||{}).map(([a,v])=>`${a.charAt(0).toUpperCase()+a.slice(1)} ${v}+`).join(', ')||'None';
   const parentsText=(node.parents||[]).map(pid=>nodes[pid]?.name||pid).join(', ')||'None';
   info.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><b style="font-size:12px">${safe(node.name)}</b>${isUnlocked?'<span style="color:#43a047;font-size:10px">✓ Unlocked</span>':canUnlock?`<button id="unlockNodeBtn" data-nid="${safe(nid)}" class="gold" style="font-size:10px;padding:2px 8px">Unlock (1pt)</button>`:'<span style="color:var(--muted);font-size:10px">Locked</span>'}</div><div style="font-size:10px;color:var(--muted);margin-bottom:4px">${safe(node.desc||'')}</div><div style="font-size:9px;color:#aaa">Tier ${node.tier||1} · Requires: Lv${node.level_req||1}${attrText!=='None'?' · '+attrText:''}</div>${parentsText!=='None'?`<div style="font-size:9px;color:var(--muted)">Requires: ${safe(parentsText)}</div>`:''}`;
   const unlockBtn=$('#unlockNodeBtn');
   if(unlockBtn)unlockBtn.onclick=async()=>{
    if(sp<1){toast('No skill points available');return;}
    try{const r=await api(`/api/characters/${state.characterId}/skill-tree/unlock`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({node_id:nid})});
     if(r.ok){toast(`${node.name} unlocked!`);state.skillTreeData=null;await loadSkillTree();showPanel('skillTree');}
     else toast(r.error||'Cannot unlock');
    }catch(e){toast(e.message);}
   };
  });
 }
 if(name==='organizations'){
  loadOrganizations();
  $$('[data-join-org]').forEach(el=>el.onclick=async()=>{
   try{const r=await api(`/api/organizations/${el.dataset.joinOrg}/join`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId})});
    if(r.ok){toast('Joined!');state.charMemberships=null;state.worldOrgs=null;await loadOrganizations();showPanel('organizations');}
    else toast(r.error||'Could not join');
   }catch(e){toast(e.message);}
  });
  $$('[data-rankup-org]').forEach(el=>el.onclick=async()=>{
   try{const r=await api(`/api/organizations/${el.dataset.rankupOrg}/rank-up`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId})});
    if(r.ok){toast(`Ranked up to ${r.rank_name||'next rank'}!`);state.charMemberships=null;await loadOrganizations();showPanel('organizations');}
    else toast(r.error||'Cannot rank up');
   }catch(e){toast(e.message);}
  });
  $$('[data-leave-org]').forEach(el=>el.onclick=async()=>{
   if(!confirm('Leave this organization?'))return;
   try{await api(`/api/organizations/${el.dataset.leaveOrg}/leave`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId})});
    toast('Left organization');state.charMemberships=null;await loadOrganizations();showPanel('organizations');
   }catch(e){toast(e.message);}
  });
  const genOrgBtn=$('#generateOrgBtn');
  if(genOrgBtn)genOrgBtn.onclick=async()=>{
   genOrgBtn.disabled=true;genOrgBtn.textContent='Generating…';
   const world=state.worlds[state.worldIndex];
   try{const r=await api('/api/organizations/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({world_id:world?.id,world_name:world?.name||'',history:state.chatHistory||[]})});
    if(r.ok){toast(`✨ ${r.name} generated!`);state.worldOrgs=null;await loadOrganizations();showPanel('organizations');}
    else toast(r.error||'Generation failed');
   }catch(e){toast(e.message);}finally{genOrgBtn.disabled=false;genOrgBtn.textContent='✨ Generate story organization';}
  };
 }
 if(name==='worldSystems'){
  loadWorldSystems();
  const refBtn=$('#refreshWorldSystemsBtn');
  if(refBtn)refBtn.onclick=async()=>{refBtn.disabled=true;refBtn.textContent='Refreshing…';state.worldSystems={};await loadWorldSystems();showPanel('worldSystems');refBtn.disabled=false;};
 }
}

function toggleBackstoryEdit(){
 const display=$('#backstoryDisplay');const editBox=$('#backstoryEditBox');const btn=$('#editBackstoryBtn');
 if(!display||!editBox)return;
 const editing=!editBox.hidden;
 if(editing){cancelBackstoryEdit();}
 else{display.hidden=true;editBox.hidden=false;if(btn)btn.textContent='✕ Cancel';}
}
function cancelBackstoryEdit(){
 const display=$('#backstoryDisplay');const editBox=$('#backstoryEditBox');const btn=$('#editBackstoryBtn');const ta=$('#backstoryTextarea');
 if(display)display.hidden=false;if(editBox)editBox.hidden=true;if(btn)btn.textContent='✏ Edit';
 if(ta&&state.sheet)ta.value=state.sheet.backstory||'';
}
async function saveBackstory(){
 const ta=$('#backstoryTextarea');if(!ta||!state.characterId)return;
 const newText=ta.value;
 const btn=ta.closest('div')?.querySelector('.gold');
 if(btn){btn.disabled=true;btn.textContent='Saving…';}
 try{
  await api(`/api/characters/${state.characterId}/field`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({field:'backstory',value:newText})});
  state.sheet.backstory=newText;
  const display=$('#backstoryDisplay');const editBox=$('#backstoryEditBox');const editBtn=$('#editBackstoryBtn');
  if(display){display.innerHTML=safe(newText)||'<em>No backstory yet — click Edit to add one.</em>';display.hidden=false;}
  if(editBox)editBox.hidden=true;if(editBtn)editBtn.textContent='✏ Edit';
  toast('Backstory saved');
 }catch(e){toast(e.message);if(btn){btn.disabled=false;btn.textContent='💾 Save';}}
}

function renderInventory(){
 const dc=$('#detailContent');
 if(dc&&(dc.querySelector('.inventory-grid')||dc.querySelector('.armory-grid')))showPanel('inventory');
}
async function travelToWorld(worldId){
 if(!worldId)return;
 const already=state.worlds.findIndex(w=>w.id===worldId);
 if(already>=0){state.worldIndex=already;updateWorld();setScale('local');toast(`Entered ${safe(state.worlds[already].name)}`);return;}
 try{
  const w=await api(`/api/worlds/${worldId}`);
  const entry=typeof toWorldEntry==='function'?toWorldEntry(w):w;
  state.worlds.unshift(entry);state.worldIndex=0;
  updateWorld();setScale('local');
  toast(`Traveled to ${safe(w.name)}`);
 }catch(e){toast(e.message);}
}
function worldTagsText(world){
 const r=world.ratings||{};
 return `${world.space} · Magic ${r.magic ?? '?'} · Tech ${r.technology ?? '?'} · Weapon ${r.weapon ?? '?'} · ${world.reality_type}`;
}
function updateWorld(){
 const w=state.worlds[state.worldIndex]; if(!w)return;
 $('#worldName').textContent=w.name;$('#worldTags').textContent=worldTagsText(w);$('#locationName').textContent=w.place;state.scale=w.theme;setScale(state.scale);
 if(state.scale!=='universe')loadLocations();
}

// ═══ Map hierarchy: Local → Country → Continent → Universe ═══
// loc_type values: 'local'|'area' → Local tab (buildings/locations in a city/village);
// 'country' → Country tab (regions/areas within a country);
// 'continent'|'kingdom'|'empire'|... → Continent tab
const CONTINENT_TYPES=new Set(['continent','kingdom','empire','nation','republic','duchy','realm','federation','territory','dominion','sultanate','commonwealth','confederation']);
function _isContinentType(t){return CONTINENT_TYPES.has((t||'').toLowerCase())}
function renderMapNodes(){
 const scale=state.scale;
 let shown;
 if(scale==='local') shown=state.locations.filter(l=>!l.loc_type||l.loc_type==='local'||l.loc_type==='area');
 else if(scale==='country') shown=state.locations.filter(l=>l.loc_type==='country');
 else if(scale==='continent') shown=state.locations.filter(l=>_isContinentType(l.loc_type));
 else shown=[];
 $('#mapNodes').innerHTML=shown.map(loc=>{
  const tier=_isContinentType(loc.loc_type)?'macro':loc.loc_type==='country'?'mid':'micro';
  const icon=(!loc.loc_type||loc.loc_type==='local'||loc.loc_type==='area')?_buildingIcon(loc.name):(TERRAIN_ICONS[loc.terrain]||'⌂');
  const visited=state.visitedWorldIds.has(loc.id)||state.visitedWorldIds.has(String(loc.id));
  const fogStyle=visited?'':'opacity:0.35;filter:grayscale(1)';
  const label=visited?safe(loc.name):'???';
  return `<button class="map-node map-node-${tier}" style="--x:${loc.x}%;--y:${loc.y}%;${fogStyle}" data-loc-id="${loc.id}" data-label="${label}" title="${label}">${icon}</button>`;
 }).join('');
 $$('#mapNodes [data-loc-id]').forEach(el=>el.onclick=(ev)=>{ev.stopPropagation();const loc=state.locations.find(l=>String(l.id)===el.dataset.locId);if(loc){move(loc.x,loc.y);showNodePreview(loc,el);}});
}
async function loadLocations(){
 const world=state.worlds[state.worldIndex]; if(!world)return;
 $('#mapNodes').innerHTML='';
 try{
  state.locations=await api(`/api/worlds/${world.id}/locations`);
  renderMapNodes();
  if(state.pendingStartScene){state.pendingStartScene=false;}
  // Seed local map from opening backstory when starting a new game with no local locations
  const hasLocal=state.locations.some(l=>!l.loc_type||l.loc_type==='local'||l.loc_type==='area');
  if(!hasLocal&&state.openingText&&!state._backstorySeeded){state._backstorySeeded=true;seedLocalFromBackstory(state.openingText).catch(()=>{});}
 }catch(error){state.locations=[];renderMapNodes()}
}
async function _aiDescribePlace(prompt){
 const world=state.worlds[state.worldIndex];
 try{
  const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:prompt,extra_context:playerContextLine(),session_id:state.sessionId,world_id:world?.id,user_name:'System',character_name:'Worldweaver',participants:['Worldweaver'],temperature:0.9})});
  const data=await r.json();
  if(r.ok&&data.reply){
   const chatLog=$('#chatLog');
   chatLog.insertAdjacentHTML('beforeend',chatMsg('gm',fmtChat(data.reply),data.id));
   chatLog.scrollTop=chatLog.scrollHeight;
   speakReply(data.reply);
  }
 }catch{}
}
async function enterLocation(loc){
 state.visitedWorldIds.add(loc.id);state.visitedWorldIds.add(String(loc.id));
 renderMapNodes();
 const world=state.worlds[state.worldIndex];
 const chatLog=$('#chatLog');
 // ── Continent/Kingdom → switch to Country tab and describe ──
 if(_isContinentType(loc.loc_type)){
  setScale('country');
  state._activeCountry=loc;
  $('#mapLocName').textContent=loc.name;$('#mapLocSub').textContent=`${loc.loc_type||'Territory'} · ${world?.name||''}`;
  chatLog.insertAdjacentHTML('beforeend',`<div class="chat-msg gm"><div class="msg-body"><b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action">📌 Entering ${safe(loc.name)} — ${safe(loc.loc_type||'territory')} of ${safe(world?.name||'the realm')}.</em></div></div></div>`);
  chatLog.scrollTop=chatLog.scrollHeight;
  await _aiDescribePlace(`Describe the ${loc.loc_type||'territory'} of "${loc.name}" in ${world?.name||'this world'}. What notable regions, cities, or landmarks does it contain? What is its culture, government, and defining character? 2 vivid paragraphs.`);
  return;
 }
 // ── Country/Region → switch to Local tab and describe ──
 if(loc.loc_type==='country'){
  setScale('local');
  $('#mapLocName').textContent=loc.name;$('#mapLocSub').textContent=`Region · ${world?.name||''}`;
  chatLog.insertAdjacentHTML('beforeend',`<div class="chat-msg gm"><div class="msg-body"><b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action">📌 Entering the region of ${safe(loc.name)}.</em></div></div></div>`);
  chatLog.scrollTop=chatLog.scrollHeight;
  await _aiDescribePlace(`Describe the region/area of "${loc.name}" in ${world?.name||'this world'}. What towns, villages, or notable buildings does it contain? What is everyday life like here? 1-2 paragraphs.`);
  return;
 }
 // ── Local location → scene image + content panel ──
 const panel=$('#mapLocationPanel'),img=$('#mapLocImg'),loading=$('#mapLocLoading');
 $('#mapLocName').textContent=loc.name;
 $('#mapLocSub').textContent=`${loc.terrain} · ${world?.name||''}`;
 panel.hidden=false;loading.style.display='flex';
 // Open location content overlay
 openLocContent(loc);
 if(state.locationImageCache[loc.id]){
  const cached=state.locationImageCache[loc.id];
  img.src=cached;img.style.opacity='1';loading.style.display='none';
  const mapEl=$('#map');mapEl.style.backgroundImage=`url('${cached}')`;mapEl.style.backgroundSize='cover';mapEl.style.backgroundPosition='center';
  return;
 }
 img.style.opacity='0';
 const character=state.sheet;
 const useOpening=state.openingText&&!state.openingTextUsed&&state.locations[0]&&loc.id===state.locations[0].id;
 if(useOpening)state.openingTextUsed=true;
 const partyLine=state.partyChars.length>1?` Party members present: ${state.partyChars.slice(1).map(c=>`${c.name} (${c.race} ${c.profession})`).join(', ')}.`:'';
 const prompt=useOpening?`${world?.name||'A realm'}: ${state.openingText.slice(0,280)}. The scene shows ${loc.terrain} terrain at ${loc.name}.`:`${world?.name||'A realm'}, ${loc.terrain} region called ${loc.name}. ${loc.description||''} A ${character?.race||'traveller'} ${character?.profession||'adventurer'} named ${character?.name||'the hero'} stands in the scene.`;
 const stopTimer=startGenTimer(loading);
 try{
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:'Cinematic',width:1024,height:576,save_to_chat:false,cache_key:`loc:${world?.id||0}:${loc.id}:scene`})}).finally(stopTimer);
  const url=result.url||result.path;
  if(url){
   state.locationImageCache[loc.id]=url;
   _saveImgCache(state.locationImageCache);
   img.src=url;img.onload=()=>{img.style.opacity='1'};
   const mapEl=$('#map');mapEl.style.backgroundImage=`url('${url}')`;mapEl.style.backgroundSize='cover';mapEl.style.backgroundPosition='center';
   if(useOpening){
    chatLog.insertAdjacentHTML('beforeend',`<div class="chat-msg gm"><div class="msg-body"><b>WORLDWEAVER</b><img src="${safe(url)}" class="chat-scene-img" alt="Opening scene: ${safe(loc.name)}"><span class="chat-scene-caption">📍 ${safe(loc.name)} · ${safe(loc.terrain)}</span></div></div>`);
    chatLog.scrollTop=chatLog.scrollHeight;
    await _aiDescribePlace(`Describe the ${loc.terrain} location "${loc.name}" in ${world?.name||'this world'} as the player first arrives. Paint a vivid picture of the atmosphere — the sights, sounds, smells, and the feeling of this place. Describe any notable people, creatures, merchants, guards, or beings visible here.${partyLine} Keep it to 2-3 immersive paragraphs, written in second person ("You see...", "You smell...").`);
   }
  }
 }catch(error){toast(`Scene generation failed: ${error.message}`)}
 loading.style.display='none';
}
$('#exitSceneBtn').onclick=()=>$('#sceneOverlay').classList.remove('open');
$('#mapLocCloseBtn').onclick=()=>{$('#mapLocationPanel').hidden=true};

// ── Location Content Panel ──────────────────────────────────────────────────
let _lcpActiveLoc=null;
let _lcpContent=null;
let _lcpTab='npcs';
const LOC_CONTENT_RARITY_ICONS={common:'',uncommon:'🟢',rare:'🔵',legendary:'🟠'};
const ITEM_TYPE_ICONS={currency:'💰',material:'🪨',equipment:'⚔',consumable:'🧪',luxury:'💎',misc:'📦'};
const NPC_MOOD_ICONS={friendly:'😊',neutral:'😐',suspicious:'🤨',cautious:'😟',cheerful:'😄',weary:'😩',desperate:'😰',mysterious:'🎭'};

function openLocContent(loc){
 _lcpActiveLoc=loc;_lcpContent=null;_lcpTab='npcs';
 const ov=$('#locContentOverlay');if(!ov)return;
 ov.classList.remove('hidden');
 const icon=_buildingIcon(loc.name)||(TERRAIN_ICONS[loc.terrain]||'⌂');
 $('#lcpIcon').textContent=icon;
 $('#lcpName').textContent=loc.name;
 $('#lcpSub').textContent=`${loc.terrain||'Unknown'} · ${(state.worlds[state.worldIndex]||{}).name||'World'}`;
 $$('.lcp-tab').forEach(t=>t.classList.toggle('active',t.dataset.lcpTab==='npcs'));
 _renderLcpLoading('Scouting location…');
 const world=state.worlds[state.worldIndex];
 const wid=world?.id||0;
 api(`/api/locations/${loc.id}/content/generate?world_id=${wid}&terrain=${encodeURIComponent(loc.terrain||'Plains')}&loc_name=${encodeURIComponent(loc.name)}`,{method:'POST'})
  .then(content=>{_lcpContent=content;_renderLcpTab(_lcpTab);})
  .catch(()=>{const b=$('#lcpBody');if(b)b.innerHTML=`<div class="lcp-empty">⚠ Could not load location content.</div>`;});
}
function _renderLcpLoading(msg){const b=$('#lcpBody');if(b)b.innerHTML=`<div class="lcp-loading">${safe(msg)}</div>`;}
function _renderLcpTab(tab){
 _lcpTab=tab;
 $$('.lcp-tab').forEach(t=>t.classList.toggle('active',t.dataset.lcpTab===tab));
 if(!_lcpContent){_renderLcpLoading('Loading…');return;}
 const body=$('#lcpBody');if(!body)return;
 const loc=_lcpActiveLoc;
 const world=state.worlds[state.worldIndex];
 const wid=world?.id||0;
 let html='';
 if(tab==='npcs'){
  const npcs=_lcpContent.npcs||[];
  if(!npcs.length){html=`<div class="lcp-empty">👤 No notable NPCs in this area.</div>`;}
  else html=npcs.map(n=>{
   const d=n.data||{};const mood=d.mood||'neutral';const prof=d.profession||'Wanderer';
   const moodIcon=NPC_MOOD_ICONS[mood]||'😐';
   return `<div class="lcp-card">
    <div class="lcp-card-icon">${moodIcon}</div>
    <div class="lcp-card-body">
     <div class="lcp-card-name">${safe(n.name)}</div>
     <div class="lcp-card-sub">${safe(prof)} · <span style="text-transform:capitalize">${safe(mood)}</span></div>
     ${n.description?`<div class="lcp-card-desc">${safe(n.description)}</div>`:''}
     <div class="lcp-card-actions">
      <button class="lcp-btn lcp-btn-talk" onclick="lcpTalkNpc(${JSON.stringify(n.name)},${JSON.stringify(prof)})">💬 Talk</button>
      ${d.has_quest?`<button class="lcp-btn lcp-btn-quest" onclick="_lcpOpenTab('quests')">📜 Has Quest</button>`:''}
     </div>
    </div>
   </div>`;
  }).join('');
 }
 else if(tab==='enemies'){
  const enemies=_lcpContent.enemies||[];const boss=_lcpContent.boss;
  if(boss){const bd=boss.data||{};const pct=Math.min(100,Math.round((bd.hp||100)/5));
   html+=`<div class="lcp-boss-banner"><div class="lcp-boss-skull">💀</div><div class="lcp-boss-info">
    <strong>${safe(boss.name)}</strong><small>${safe(boss.description||'')}</small>
    <div class="lcp-hp-bar" style="margin:5px 0 4px"><div class="lcp-hp-fill" style="width:${pct}%;background:#ff7700"></div></div>
    <small style="color:#cc8830">Level ${bd.level||'?'} · ${bd.hp||'?'} HP · Reward: ${safe(bd.reward||'')}</small><br>
    <button class="lcp-btn lcp-btn-boss" style="margin-top:6px" onclick="lcpFightEnemy(${JSON.stringify(boss.name)},${bd.level||5},${bd.hp||200},true)">💀 Challenge Boss</button>
   </div></div>`;}
  if(!enemies.length&&!boss)html+=`<div class="lcp-empty">🕊 No enemies detected.</div>`;
  else html+=enemies.map(e=>{const d=e.data||{};const pct=Math.min(100,Math.round((d.hp||50)/2));
   const tIcons={humanoid:'🗡',beast:'🐺',undead:'💀',elemental:'⚡',construct:'🤖',giant:'👹'};
   return `<div class="lcp-card">
    <div class="lcp-card-icon">${tIcons[d.type]||'👾'}</div>
    <div class="lcp-card-body">
     <div class="lcp-card-name">${safe(e.name)} <small style="color:var(--muted)">×${d.count||1}</small></div>
     <div class="lcp-card-sub">Level ${d.level||1} ${d.type||'creature'} · ${d.hp||'?'} HP</div>
     <div class="lcp-hp-bar"><div class="lcp-hp-fill" style="width:${pct}%"></div></div>
     <div class="lcp-card-actions" style="margin-top:5px">
      <button class="lcp-btn lcp-btn-fight" onclick="lcpFightEnemy(${JSON.stringify(e.name)},${d.level||1},${d.hp||40},false)">⚔ Fight</button>
      <span class="lcp-gold-badge">💰 ${d.gold_drop||0}g drop</span>
     </div>
    </div>
   </div>`;
  }).join('');
 }
 else if(tab==='loot'){
  const loot=_lcpContent.loot||[];
  if(!loot.length)html=`<div class="lcp-empty">📦 Nothing of value here.</div>`;
  else{
   html=loot.map(l=>{const d=l.data||{};const itype=d.item_type||'misc';
    const icon=ITEM_TYPE_ICONS[itype]||'📦';const rarity=l.rarity||'common';
    return `<div class="lcp-card" id="loot-card-${l.id}">
     <div class="lcp-card-icon">${icon}</div>
     <div class="lcp-card-body">
      <div class="lcp-card-name">${safe(l.name)} <span class="lcp-rarity-${rarity}">${LOC_CONTENT_RARITY_ICONS[rarity]||''} ${rarity}</span></div>
      <div class="lcp-card-sub">${itype.charAt(0).toUpperCase()+itype.slice(1)} · Qty:${l.quantity||1} · ${l.value||0}g</div>
      <div class="lcp-card-actions"><button class="lcp-btn lcp-btn-take" onclick="lcpCollectLoot(${l.id},${loc.id},${wid})">✋ Take</button></div>
     </div>
    </div>`;
   }).join('');
   html+=`<div class="lcp-take-all-row"><button class="lcp-btn lcp-btn-take" onclick="lcpCollectAllLoot(${loc.id},${wid})">✋ Take All</button></div>`;
  }
 }
 else if(tab==='quests'){
  const quests=_lcpContent.quests||[];
  if(!quests.length)html=`<div class="lcp-empty">📜 No quests available here.</div>`;
  else html=quests.map(q=>{const d=q.data||{};
   return `<div class="lcp-card" id="quest-card-${q.id}">
    <div class="lcp-card-icon">📜</div>
    <div class="lcp-card-body">
     <div class="lcp-card-name">${safe(q.name)}</div>
     <div class="lcp-card-sub">Given by: ${safe(d.giver||'Unknown')}</div>
     <div class="lcp-card-desc">${safe(q.description||'')}</div>
     <div class="lcp-card-sub" style="color:#c9a84c">🏆 Reward: ${safe(d.reward_desc||'Unknown')}</div>
     <div class="lcp-card-actions" style="margin-top:5px">
      <button class="lcp-btn lcp-btn-quest" onclick="lcpAcceptQuest(${q.id},${loc.id})">✦ Accept Quest</button>
     </div>
    </div>
   </div>`;
  }).join('');
 }
 html+=`<div class="lcp-refresh-row"><button class="lcp-btn-refresh" onclick="lcpRefreshContent()">↺ Refresh Location</button></div>`;
 body.innerHTML=html;
}
function _lcpOpenTab(tab){_renderLcpTab(tab);}
function lcpTalkNpc(name,profession){
 const ci=$('#chatInput');if(ci){ci.value=`[Talking to ${name}, a ${profession}] `;ci.focus();}
 $('#locContentOverlay')?.classList.add('hidden');toast(`💬 Speaking with ${name}`);
}
function lcpFightEnemy(name,level,hp,isBoss){
 const ci=$('#chatInput');
 if(ci){ci.value=`[${isBoss?'Boss fight':'Combat'}: ${name} — Level ${level}, ${hp} HP] I draw my weapon and attack!`;ci.focus();}
 $('#locContentOverlay')?.classList.add('hidden');toast(`⚔ Engaging ${name}!`);sfx('combat');
}
async function lcpCollectLoot(lootId,locId,worldId){
 const charId=state.sheet?.id||0;
 const btn=document.querySelector(`#loot-card-${lootId} .lcp-btn-take`);
 if(btn){btn.disabled=true;btn.textContent='…';}
 try{
  const result=await api(`/api/locations/${locId}/loot/collect?loot_id=${lootId}&character_id=${charId}`,{method:'POST'});
  if(result.collected){
   const card=document.getElementById(`loot-card-${lootId}`);
   if(card){card.style.opacity='0.4';card.querySelector('.lcp-card-actions').innerHTML=`<span style="color:var(--muted);font-size:10px">✓ Collected</span>`;}
   if(result.item_type==='currency'&&result.gold>0){
    if(state.inventory?.economy)state.inventory.economy.gold=(state.inventory.economy.gold||0)+result.gold;
    toast(`💰 Collected ${result.gold} gold!`);
   }else toast(`✋ Took ${result.name}${result.quantity>1?' ×'+result.quantity:''}!`);
   sfx('loot');
   if(_lcpContent?.loot){const item=_lcpContent.loot.find(l=>l.id===lootId);if(item)item._depleted=true;}
  }
 }catch(e){toast('Failed to collect item');if(btn){btn.disabled=false;btn.textContent='✋ Take';}}
}
async function lcpCollectAllLoot(locId,worldId){
 const loot=(_lcpContent?.loot||[]).filter(l=>!l._depleted);
 for(const l of loot)await lcpCollectLoot(l.id,locId,worldId);
}
async function lcpAcceptQuest(questId,locId){
 const charName=state.sheet?.name||'';
 const btn=document.querySelector(`#quest-card-${questId} .lcp-btn-quest`);
 if(btn){btn.disabled=true;btn.textContent='…';}
 try{
  const result=await api(`/api/locations/${locId}/quests/accept?quest_id=${questId}&character_name=${encodeURIComponent(charName)}&character_id=${state.characterId||0}`,{method:'POST'});
  if(result.accepted){
   const card=document.getElementById(`quest-card-${questId}`);
   if(card){card.querySelector('.lcp-card-actions').innerHTML=`<span style="color:var(--gold);font-size:10px">✦ Quest accepted!</span>`;}
   toast(`📜 Quest accepted: ${result.title}`);
   try{const q=await api(`/api/quests/active?character_name=${encodeURIComponent(charName)}&character_id=${state.characterId||''}`);state.quests=q||[];renderQuests();}catch{}
   if(_lcpContent?.quests){const q=_lcpContent.quests.find(q=>q.id===questId);if(q)q._accepted=true;}
  }
 }catch(e){toast('Failed to accept quest');if(btn){btn.disabled=false;btn.textContent='✦ Accept Quest';}}
}
async function lcpRefreshContent(){
 if(!_lcpActiveLoc)return;
 _lcpContent=null;_renderLcpLoading('Refreshing location…');
 const world=state.worlds[state.worldIndex];const wid=world?.id||0;const loc=_lcpActiveLoc;
 try{
  const content=await api(`/api/locations/${loc.id}/content/generate?world_id=${wid}&terrain=${encodeURIComponent(loc.terrain||'Plains')}&loc_name=${encodeURIComponent(loc.name)}&force=true`,{method:'POST'});
  _lcpContent=content;_renderLcpTab(_lcpTab);toast('↺ Location content refreshed!');
 }catch(e){const b=$('#lcpBody');if(b)b.innerHTML=`<div class="lcp-empty">⚠ Refresh failed.</div>`;}
}
document.addEventListener('click',e=>{
 const t=e.target.closest('.lcp-tab');
 if(t&&t.dataset.lcpTab)_renderLcpTab(t.dataset.lcpTab);
});
document.getElementById('lcpClose')?.addEventListener('click',()=>$('#locContentOverlay')?.classList.add('hidden'));
document.getElementById('locContentOverlay')?.addEventListener('click',e=>{
 if(e.target.id==='locContentOverlay')$('#locContentOverlay')?.classList.add('hidden');
});

// ── Web Audio ambient sound helper ──
let _audioCtx=null;
function _getAudioCtx(){if(!_audioCtx){try{_audioCtx=new(window.AudioContext||window.webkitAudioContext)();}catch{}}return _audioCtx;}
function sfx(name){
 try{
  const ctx=_getAudioCtx();if(!ctx)return;
  if(ctx.state==='suspended')ctx.resume();
  const osc=ctx.createOscillator(),gain=ctx.createGain();
  osc.connect(gain);gain.connect(ctx.destination);
  const t=ctx.currentTime;
  const configs={
   travel:{type:'sine',freq:440,freqEnd:220,dur:0.4,vol:0.06},
   universe:{type:'sine',freq:180,freqEnd:80,dur:0.8,vol:0.05},
   combat:{type:'sawtooth',freq:280,freqEnd:140,dur:0.3,vol:0.07},
   loot:{type:'triangle',freq:880,freqEnd:1320,dur:0.25,vol:0.06},
   levelup:{type:'sine',freq:440,freqEnd:880,dur:0.6,vol:0.08},
  };
  const c=configs[name]||configs.travel;
  osc.type=c.type;osc.frequency.setValueAtTime(c.freq,t);osc.frequency.linearRampToValueAtTime(c.freqEnd,t+c.dur);
  gain.gain.setValueAtTime(c.vol,t);gain.gain.linearRampToValueAtTime(0,t+c.dur);
  osc.start(t);osc.stop(t+c.dur);
 }catch{}
}
const SCALE_LABELS={local:'LOCAL MAP',country:'COUNTRY MAP',continent:'CONTINENT MAP',universe:'UNIVERSE MAP'};
function setScale(scale){
 const prev=state.scale;state.scale=scale;
 hideNodePreview();
 $('#map').className=`map map-${scale}`;$('#scaleLabel').textContent=SCALE_LABELS[scale]||`${scale.toUpperCase()} MAP`;
 $$('[data-scale]').forEach(b=>b.classList.toggle('active',b.dataset.scale===scale));
 if(scale!==prev)sfx(scale==='universe'?'universe':'travel');
 if(scale==='universe')loadUniverseNodes();else renderMapNodes();
}
function move(x,y){state.x=Math.max(4,Math.min(96,x));state.y=Math.max(6,Math.min(92,y));const p=$('#playerToken');p.style.setProperty('--x',state.x+'%');p.style.setProperty('--y',state.y+'%');_checkProximity();}
function _checkProximity(){
  if(state.scale==='universe')return;
  $$('#mapNodes .map-node').forEach(el=>{
    const loc=state.locations.find(l=>String(l.id)===el.dataset.locId);
    if(!loc)return;
    const dx=loc.x-state.x,dy=loc.y-state.y;
    el.classList.toggle('nearby',Math.sqrt(dx*dx+dy*dy)<9);
  });
}
function showNodePreview(loc,nodeEl){
  const visited=state.visitedWorldIds.has(loc.id)||state.visitedWorldIds.has(String(loc.id));
  const fogged=!visited;
  const icon=(!loc.loc_type||loc.loc_type==='local'||loc.loc_type==='area')?_buildingIcon(loc.name):(TERRAIN_ICONS[loc.terrain]||'⌂');
  const cachedImg=state.locationImageCache[loc.id];
  const name=fogged?'???':loc.name;
  const terrain=fogged?'Unknown region':(loc.terrain||'Unknown');
  const desc=!fogged&&loc.description&&loc.description!=='Mentioned in story'&&loc.description!==`Generated ${loc.loc_type||'local'} location`?loc.description:'';
  const preview=$('#mapNodePreview');
  preview.innerHTML=`
    <div class="mnp-img-wrap">
      <img id="mnpImg" src="${safe(cachedImg||'')}" style="opacity:${cachedImg?'1':'0'}" alt="">
      <div class="mnp-loading" id="mnpLoading" style="display:${cachedImg?'none':'flex'}">${fogged?'⬛ UNDISCOVERED':'Generating scene…'}</div>
    </div>
    <div class="mnp-body">
      <span class="mnp-name">${icon} ${safe(name)}</span>
      <span class="mnp-sub">${safe(terrain)}</span>
      ${desc?`<p class="mnp-desc">${safe(desc)}</p>`:''}
    </div>
    <div class="mnp-actions">
      <button class="mnp-enter" id="mnpEnterBtn">${fogged?'🔍 Discover':'⚔ Enter Location'}</button>
      <button class="mnp-close" id="mnpCloseBtn">✕</button>
    </div>`;
  // Position near the node
  const mapEl=$('#map'),mapRect=mapEl.getBoundingClientRect();
  const nx=(loc.x/100)*mapEl.clientWidth,ny=(loc.y/100)*mapEl.clientHeight;
  const pw=215,ph=200;
  let left=nx+26,top=ny-ph/2;
  if(left+pw>mapEl.clientWidth-6)left=nx-pw-26;
  if(left<4)left=4;
  if(top<4)top=4;
  if(top+ph>mapEl.clientHeight-4)top=mapEl.clientHeight-ph-4;
  preview.style.left=left+'px';preview.style.top=top+'px';
  preview.classList.remove('hidden');
  $$('#mapNodes .map-node').forEach(el=>el.classList.toggle('preview-active',el.dataset.locId===String(loc.id)));
  $('#mnpEnterBtn').onclick=()=>{hideNodePreview();enterLocation(loc);};
  $('#mnpCloseBtn').onclick=hideNodePreview;
  // Lazy-load thumbnail if not cached
  if(!fogged&&!cachedImg){
    const world=state.worlds[state.worldIndex];
    const stopThumbTimer=startGenTimer($('#mnpLoading'));
    if(world)_genLocationThumbnail(loc,world,loc.terrain||'Plains').catch(()=>{}).then(()=>{
      stopThumbTimer();
      const url=state.locationImageCache[loc.id];
      const img=$('#mnpImg'),ld=$('#mnpLoading');
      if(url&&img){img.src=url;img.style.opacity='1';if(ld)ld.style.display='none';}
    });
  }
  state._previewLocId=loc.id;
}
function hideNodePreview(){
  const p=$('#mapNodePreview');
  if(p){p.classList.add('hidden');p.innerHTML='';}
  $$('#mapNodes .map-node').forEach(el=>el.classList.remove('preview-active'));
  state._previewLocId=null;
}

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
function saveSessionToStorage(){localStorage.setItem(SESSION_KEY,JSON.stringify({sessionId:state.sessionId,worldId:state.worlds[0]?.id,characterId:state.characterId,openingText:state.openingText||null}))}
function toWorldEntry(w){const locs=(w.locations||w.world_json?.locations||[]);const first=locs[0];const sp=w.space_alignment||'';const theme=sp==='sci-fi'||sp==='futuristic'?'universe':sp==='ancient_civilization'||sp==='prehistoric'?'country':'local';return {id:w.id,name:w.name,ratings:w.ratings||{},reality_type:w.reality_type||'Prime Reality',space:sp||'unknown',place:first?first.name:(w.name||'Unknown Location'),theme,startX:first?first.x:50,startY:first?first.y:50}}

// ── Chat content formatter: **action**, *action*, "dialogue", Name: line ──
// Screenplay format: "Liam: Hello" → name badge + dialogue; **text** → action narration
function fmtChat(raw){
 const s=String(raw??'');
 // Process line by line to handle "Name: dialogue" screenplay format
 const lines=s.split(/\r?\n/);
 const nameColonRe=/^([A-Z][a-zA-Z0-9 '\-]{1,30}):\s*(.+)/;
 return lines.map(line=>{
  // Check for screenplay dialogue: "Name: text"
  const nc=nameColonRe.exec(line.trim());
  if(nc){
   const spkr=safe(nc[1]);
   const rest=fmtInline(nc[2]);
   return `<div class="chat-line-speech"><span class="chat-speaker-name">${spkr}:</span> ${rest}</div>`;
  }
  // Otherwise apply inline formatting
  const formatted=fmtInline(line);
  return formatted?`<div class="chat-line">${formatted}</div>`:'';
 }).filter(Boolean).join('');
}
function fmtInline(s){
 s=String(s??'');
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
  $('#chatInput').value=text;if(window._chatInputGrow)window._chatInputGrow();
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
    const r=await fetch('/api/memory/facts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fact:text,source:'chat-pin',memory_type:'episodic',importance:0.9,session_id:state.sessionId})});
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
   const stopChatImgTimer=startGenTimer(resultEl.firstElementChild,'Generating');
   b.disabled=true;
   try{
    const endpoint='/api/media/image';
    const payload={prompt:text.slice(0,200),style:styleMap[mtype]||'Cinematic',width:mtype==='video'?1024:512,height:mtype==='video'?576:768,save_to_chat:false};
    const res=await api(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).finally(stopChatImgTimer);
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
  const chatLog=$('#chatLog');
  chatLog.innerHTML=history.length?history.map(m=>chatMsg(m.role==='user'?'player':'gm',fmtChat(m.content),m.id)).join(''):'<p class="gm">The portal hums, waiting for your first move.</p>';
  if(history.length>=40){
   const btn=document.createElement('button');
   btn.className='ghost';btn.id='loadEarlierBtn';btn.style.cssText='width:100%;font-size:10px;padding:4px;margin-bottom:6px;color:var(--muted)';
   btn.textContent='⬆ Load earlier messages';
   chatLog.prepend(btn);
   btn.onclick=()=>_loadEarlierChat(history[0]?.id);
  }
  chatLog.scrollTop=chatLog.scrollHeight;
 }catch{}
}
async function _loadEarlierChat(beforeId){
 if(!beforeId)return;
 try{
  const earlier=await api(`/api/chat/history?session_id=${encodeURIComponent(state.sessionId)}&limit=40&before_id=${beforeId}`);
  if(!earlier.length){const btn=$('#loadEarlierBtn');if(btn)btn.remove();return;}
  const chatLog=$('#chatLog');
  const html=earlier.map(m=>chatMsg(m.role==='user'?'player':'gm',fmtChat(m.content),m.id)).join('');
  const oldBtn=$('#loadEarlierBtn');
  if(oldBtn)oldBtn.remove();
  const prevScroll=chatLog.scrollHeight-chatLog.scrollTop;
  chatLog.insertAdjacentHTML('afterbegin',html);
  chatLog.scrollTop=chatLog.scrollHeight-prevScroll;
  if(earlier.length>=40){
   const btn=document.createElement('button');
   btn.className='ghost';btn.id='loadEarlierBtn';btn.style.cssText='width:100%;font-size:10px;padding:4px;margin-bottom:6px;color:var(--muted)';
   btn.textContent='⬆ Load earlier messages';
   chatLog.prepend(btn);
   btn.onclick=()=>_loadEarlierChat(earlier[0]?.id);
  }
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
$('#genLocBtn').onclick=()=>generateMapLocations(state.scale||'local');
$('#advanceTimeBtn').onclick=async()=>{
 try{
  await api(`/api/world/clock/advance?session_id=${encodeURIComponent(state.sessionId||'default')}&minutes=30`,{method:'POST'});
  await updateClock();
  if(Math.random()<0.25) triggerRandomEvent();
 }catch{}
};
async function triggerRandomEvent(){
 try{
  const data=await api(`/api/world/events/random?session_id=${encodeURIComponent(state.sessionId||'default')}`,{method:'POST'});
  const event=data.event||data;const effect=data.effect||null;
  if(event&&typeof event==='string'){
   $('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm','🎲 <i>Random Event:</i> '+safe(event)));
   $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
  }
  if(effect&&state.characterId&&state.sheet){
   if(effect.hp_change&&effect.hp_change!==0){
    const {maxHp,maxMana}=derivedResources(state.sheet);
    const hpSt=getHpState(state.characterId,maxHp,maxMana);
    setHpState(state.characterId,hpSt.currentHp+effect.hp_change,hpSt.currentMp,maxHp,maxMana);
    toast(`${effect.hp_change>0?'+':''}${effect.hp_change} HP from event`);
    try{await api(`/api/characters/${state.characterId}/hp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:effect.hp_change,reason:(event||'event').toString().slice(0,50)})});}catch{}
    renderParty();if($('#detailContent').innerHTML.includes('Health'))showPanel('character');
   }
   if(effect.xp_change&&effect.xp_change>0){try{const r=await api(`/api/characters/${state.characterId}/xp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:effect.xp_change,reason:`Random event: ${(event||'').toString().slice(0,40)}`})});if(r.sheet){state.sheet=r.sheet;renderParty();}toast(`+${effect.xp_change} XP from event`);}catch{}}
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
  $('#chatInput').value=btn.dataset.opt;if(window._chatInputGrow)window._chatInputGrow();
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
async function bindSession({sessionId,worldId,characterId,openingText}){
 state.hasActiveGame=true;
 state.sessionId=sessionId||'default';
 if(openingText){state.openingText=openingText;state.openingTextUsed=false;}
 let world=null;
 if(worldId){try{world=toWorldEntry(await api(`/api/worlds/${worldId}`))}catch{}}
 state.worlds=world?[world,...state.flavorWorlds.filter(f=>f.id!==world.id)]:state.flavorWorlds;
 state.worldIndex=0;
 if(characterId){state.characterId=characterId;await refreshCharacterState()}
 state.partyChars=[];state.partySheets={};
 loadPartyFromStorage();
 await loadChatHistory();
 saveSessionToStorage();
 updateWorld();if(world){move(world.startX??50,world.startY??50)}renderParty();renderQuests();showPanel('character');
 // Cache saved characters for story detection
 try{state._savedCharCache=await api('/api/characters');}catch{}
 try{const active=await api(`/api/combat/active?session_id=${encodeURIComponent(state.sessionId)}`);if(active)openCombat(active)}catch{}
 updateClock();
}
async function initPlay(){
 try{
  const [flavorWorlds,characterId,weaponTiers,spellData,weaponData]=await Promise.all([ensureWorlds(),getExistingCharacterId(),api('/api/weapons/tiers'),api('/api/spells'),api('/api/weapons/dnd')]);
  state.flavorWorlds=flavorWorlds; state.characterId=characterId; state.weaponTiers=weaponTiers;
  state.allSpells=spellData.spells||{}; state.dndWeapons=weaponData.weapons||{}; state.dndWeaponCategories=weaponData.categories||[];
  if(state.characterId){await refreshCharacterState();loadNpcMemories().catch(()=>{});}
 }catch(error){toast(`Play mode running offline: ${error.message}`)}
 renderParty();renderQuests();renderActions();showPanel('character');
 const saved=loadSessionFromStorage();
 if(saved){try{await bindSession(saved);hidePlayHub();return}catch{/* fall through to start screen */}}
 state.worlds=state.flavorWorlds;state.worldIndex=0;updateWorld();
 showPlayHub();
}

// ═══ Play hub: New Game (category -> scenario) or Load Saved Game ═══
function showStartStep(name){$$('.start-step').forEach(s=>s.hidden=(s.id!==`startStep-${name}`))}
function showPlayHub(){$('#playHub').hidden=false;$('#gameArea').hidden=true;showStartStep('choice');$('#hubCloseBtn').hidden=!state.hasActiveGame;document.body.classList.remove('game-active','sidebar-open')}
function hidePlayHub(){$('#playHub').hidden=true;$('#gameArea').hidden=false;state.hasActiveGame=true;document.body.classList.add('game-active');document.body.classList.remove('sidebar-open')}
$('#sidebarToggleBtn').onclick=()=>document.body.classList.toggle('sidebar-open');
$('#gameHelpBtn').onclick=()=>openView('help');
$('#hubCloseBtn').onclick=hidePlayHub;
$('#switchGameBtn').onclick=showPlayHub;
$$('.back-btn').forEach(b=>b.onclick=()=>showStartStep(b.dataset.back));

// ── Game topbar: Back and Close buttons ──────────────────────────────────────
$('#gameBackBtn').onclick=()=>{
  // Return to scenario selection (category step) without destroying the session
  showPlayHub();
  showStartStep('category');
  // Ensure category grid is populated
  if(categoriesCache){
    const sel=$('#worldCategorySelect');
    if(sel&&!sel.options.length){
      sel.innerHTML='<option value="all">🌐 All Worlds</option>'+categoriesCache.map(c=>`<option value="${safe(c.key)}">${safe(c.label)} (${c.scenarios.length})</option>`).join('');
      sel.onchange=()=>renderScenarioCards(categoriesCache,sel.value);
    }
    renderScenarioCards(categoriesCache,$('#worldCategorySelect')?.value||'all');
  } else {
    // Load categories if not yet fetched
    api('/api/scenarios/categories').then(cats=>{
      categoriesCache=cats;
      const sel=$('#worldCategorySelect');
      sel.innerHTML='<option value="all">🌐 All Worlds</option>'+cats.map(c=>`<option value="${safe(c.key)}">${safe(c.label)} (${c.scenarios.length})</option>`).join('');
      sel.onchange=()=>renderScenarioCards(categoriesCache,sel.value);
      renderScenarioCards(cats,'all');
    }).catch(()=>{});
  }
};
$('#gameCloseBtn').onclick=()=>{showPlayHub();showStartStep('choice');};

let categoriesCache=null;
// ── Player character creation step ───────────────────────────────────────────
function launchPlayerStep(payload){
 state.pendingGamePayload=payload;
 const form=$('#playerCharForm');
 if(form)form.reset();
 const panel=$('#importExistingCharPanel');
 if(panel)panel.style.display='none';
 // Populate existing character dropdown
 api('/api/characters').then(chars=>{
  state._savedCharCache=chars;
  if(panel&&chars.length)panel.style.display='block';
  const sel=$('#existingCharSelect');
  if(!sel)return;
  sel.innerHTML=chars.length
   ?chars.map(c=>`<option value="${c.id}" data-char='${JSON.stringify({name:c.name||'',age:c.age||25,gender:c.gender||'',profession:c.profession||'',backstory:c.backstory||''}).replace(/'/g,'&#39;')}'>${safe(c.name)} · ${safe(c.race||'')} ${safe(c.profession||'')} Lv${c.level||1}${c.scenario?` — ${safe(String(c.scenario).slice(0,40))}`:''}</option>`).join('')
   :'<option value="">No saved characters yet</option>';
 }).catch(()=>{});
 showStartStep('player');
}

$('#playerCharForm').onsubmit=async e=>{
 e.preventDefault();
 const fd=new FormData(e.currentTarget);
 const name=(fd.get('charName')||'').trim();
 if(!name){toast('Enter your character name');return}
 const btn=e.currentTarget.querySelector('button.gold');
 if(btn)btn.disabled=true;
 try{
  // Each story gets its own character, even when the name matches a saved one.
  const charData={name,age:parseInt(fd.get('charAge'))||25,gender:fd.get('charGender')||'',profession:fd.get('charProfession')||'',backstory:fd.get('charBackstory')||'',scenario:state.pendingGamePayload?.scenario_name||''};
  const result=await api('/api/characters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(charData)});
  state.characterId=result.id;
  state.sheet=charData;
  await _doBeginGame(charData);
 }catch(error){toast(error.message)}
 finally{if(btn)btn.disabled=false}
};

$('#importExistingCharBtn').onclick=()=>{
 const panel=$('#importExistingCharPanel');
 if(panel)panel.style.display=panel.style.display==='none'?'block':'none';
};

$('#useExistingCharBtn').onclick=async()=>{
 const sel=$('#existingCharSelect');
 if(!sel||!sel.value){toast('Select a character first');return}
 try{
  const charData=JSON.parse(sel.selectedOptions[0]?.dataset?.char||'{}');
  state.characterId=parseInt(sel.value);
  try{await refreshCharacterState();}catch{}
  await _doBeginGame(state.sheet||charData);
 }catch(error){toast(error.message)}
};

async function _doBeginGame(charInfo){
 const payload=state.pendingGamePayload;
 if(!payload)return;
 const charName=(charInfo.name||'').trim();
 // Replace "the User" / "User" placeholder and the scenario's default protagonist with the actual character name
 if(charName&&payload.custom_text){
  const defaultProt=payload.scenario_name?SCENARIO_PROTAGONISTS[payload.scenario_name]:'';
  payload.custom_text=payload.custom_text
   .replace(/\bthe User\b/g,charName)
   .replace(/\bUser\b/g,charName);
  if(defaultProt)payload.custom_text=payload.custom_text.replace(new RegExp(`\\b${defaultProt}\\b`,'g'),charName);
 }
 // Append full character profile as AI context (stripped from display later)
 const bgParts=[];
 if((charInfo.name||'').trim()) bgParts.push('Name: '+charInfo.name.trim());
 if(charInfo.age) bgParts.push('Age: '+charInfo.age);
 if((charInfo.gender||'').trim()) bgParts.push('Gender: '+charInfo.gender.trim());
 if((charInfo.profession||'').trim()) bgParts.push('Profession: '+charInfo.profession.trim());
 if((charInfo.backstory||'').trim()) bgParts.push('Backstory: '+charInfo.backstory.trim());
 if(bgParts.length){
  payload.custom_text=(payload.custom_text||'')+'\n\n[Character background: '+bgParts.join('. ')+']';
 }
 const party=(SCENARIO_PARTY[payload.scenario_name]||[]);
 if(party.length){
  const partyDesc=party.map(p=>p.name+' ('+p.role+': '+p.desc+')').join('; ');
  payload.custom_text=(payload.custom_text||'')+'\n\n[Party members present at scenario start: '+partyDesc+']';
 }
 payload._charName=charName;
 try{
  await _startGameSession(payload);
 }catch(error){toast(error.message)}
}

async function _startGameSession(payload){
  const result=await api('/api/scenarios/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const world=toWorldEntry(result.world);
  state.sessionId=result.session_id;
  state.worlds=[world,...state.flavorWorlds.filter(f=>f.id!==world.id)];
  state.worldIndex=0;
  if(!state.characterId){try{const cid=await getExistingCharacterId();if(cid){state.characterId=cid;await refreshCharacterState();}}catch{}}
  // Build opening: use the scenario text (with char name) as the opening scene
  let opening;
  if(payload.custom_text){
   // Strip injected AI-only annotations from what's shown in chat
   const displayText=payload.custom_text
    .replace(/\n\n\[Character background:[^\]]*\]/s,'')
    .replace(/\n\n\[Party members present[^\]]*\]/s,'')
    .trim();
   opening=displayText.length>600?displayText.slice(0,597)+'…':displayText;
  }else{
   opening=`${world.name}. ${payload._charName?payload._charName+' begins their journey.':'The story begins.'}`;
  }
  state.openingText=opening;state.openingTextUsed=false;
  saveSessionToStorage();
  try{await api('/api/chat/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'assistant',content:opening,session_id:state.sessionId})})}catch{}
  // Reload so the new game starts from clean state; the saved session is picked up on load.
  location.reload();
}

async function beginGame(payload){
 try{
  await _startGameSession(payload);
 }catch(error){toast(error.message)}
}
// ── Scenario cover images ─────────────────────────────────────────────────────
// _scCovers holds pre-generated persistent covers loaded from /api/scenarios/covers.
// _scImgCache holds in-session generated fallbacks (not persisted).
const _SC_COVERS_KEY='sc-covers-cache';
let _scCovers=(()=>{try{const r=localStorage.getItem(_SC_COVERS_KEY);return r?JSON.parse(r):{};}catch{return {};}})();
const _scImgCache={};
let _scImgQ=[],_scImgBusy=0;
function _saveScCovers(){try{localStorage.setItem(_SC_COVERS_KEY,JSON.stringify(_scCovers));}catch{}}

async function _loadScenarioCovers(){
 try{const data=await api('/api/scenarios/covers');if(data&&typeof data==='object'){Object.assign(_scCovers,data);_saveScCovers();}}
 catch(e){}
}

function _scDrain(){
 if(_scImgBusy>=2||!_scImgQ.length)return;
 const{name,prompt,style,opening,category,img}=_scImgQ.shift();
 if(_scImgCache[name]){img.src=_scImgCache[name];img.onload=()=>img.classList.add('sc-loaded');_scDrain();return}
 _scImgBusy++;
 // Try to generate and save a persistent cover via the covers API first
 api('/api/scenarios/covers/generate',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({name,opening:opening||'',category:category||'',force:false})})
 .then(r=>{
  const u=r.url;
  if(u){_scImgCache[name]=u;_scCovers[name]=u;_saveScCovers();img.src=u;img.onload=()=>img.classList.add('sc-loaded')}
 })
 .catch(()=>{
  // Fallback: generate ephemeral image via media API
  return api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({prompt,style:style||'Fantasy Art',width:512,height:384,save_to_chat:false})})
  .then(r=>{const u=r.url||r.path;if(u){_scImgCache[name]=u;img.src=u;img.onload=()=>img.classList.add('sc-loaded')}})
  .catch(()=>{});
 })
 .finally(()=>{_scImgBusy--;_scDrain()});
}

function _scQueueImg(name,prompt,img,style,opening,category){
 // If a pre-generated cover exists, use it immediately
 if(_scCovers[name]){img.src=_scCovers[name];img.onload=()=>img.classList.add('sc-loaded');return}
 if(_scImgCache[name]){img.src=_scImgCache[name];img.onload=()=>img.classList.add('sc-loaded');return}
 _scImgQ.push({name,prompt,style:style||'Fantasy Art',opening:opening||'',category:category||'',img});
 _scDrain();
}

let _scObserver=null;
// Protagonist character names for each prebuilt scenario
const SCENARIO_PROTAGONISTS={
 'Ninja Village':'Kaito','Magic Academy':'Lyra','Pirate Seas':'Riven',
 'Cyberpunk City':'Nyx','Dragon Realm':'Ash','Hero Academy':'Hikaru',
 'Medieval Kingdom':'Aldric','The Wrongly Accused':'Seraph','The Traitor\'s Escape':'Dax',
 'The Suitor\'s Tournament':'Celia','Blade for Hire':'Talon','The Prince\'s Champion':'Kira',
 'Fifteen Years a Prisoner':'Orion','Human and the Elven Queen':'Morgan',
 'Ivywood Dormitory':'Ember','Wandering Blades':'Zane','The Abandoned Party':'Freya',
 'Space Station':'Nova','Demon Slayer Corps':'Ren','Post-Apocalypse':'Rex',
 'Zombie Outbreak':'Sage','Haunted Precinct':'Quinn','Deep Space Frontier':'Ara',
 'Crown & Shadows':'Isolde','The Sterling Family':'Blake','Office Rivalry':'Avery',
 'Twenty Years Gone':'Lena','Blood & Loyalty':'Marco','Ridgewood University':'Cassie',
 'Second Marriage':'Diana','Dragon Riders':'Faelen','Witch Trials':'Mira',
 'The Heist':'Ghost','Fallen Kingdom':'Brennan','The Oracle\'s Apprentice':'Vesper',
 'Shipwrecked':'Coral','Vampire Court':'Lucian','The Wild Hunt':'Briar',
 'Time Rift':'Echo','Alien Contact':'Juno','Bounty Hunter':'Steel',
 'The Last Mage':'Cyrus','Rebellion':'Flint','Underground Arena':'Crix',
 'The Forgotten God':'Aria','Prison Break':'Vox','War Correspondent':'Kai',
 'Royal Scandal':'Elara','The Cure':'Dex','Galactic Senate':'Zara',
 'The Cult':'Silas','River Crossing':'Ida','The Inheritance':'Jules',
 'Island Survival':'Finn','Cold Case':'Reeve','The Duel':'Theron',
 'Academy for Villains':'Shade','Midnight Market':'Coin','The Siege':'Ward',
 'Fae Bargain':'Puck','The Exiled Prince':'Daric','Deep Jungle':'Rook',
 'Haunted Circus':'Milo','The Healer':'Wren','Underground Railroad':'Iris'
};

// Key named party members / major characters for each prebuilt scenario.
// Injected as AI context so the story opens with the full cast introduced.
const SCENARIO_PARTY={
 'Ninja Village':[
  {name:'Captain Hiroshi',role:'ANBU Captain',desc:'gave you the mission, reads people like scrolls, owes you a debt he has never acknowledged'},
  {name:'Yuki',role:'Medical Ninja',desc:'your team healer, calm under fire, hiding grief behind competence'},
  {name:'Ryo',role:'Rival Ninja',desc:'faster than you and knows it, respects results not words'}
 ],
 'Magic Academy':[
  {name:'Professor Aldric',role:'Theory Professor',desc:'the only teacher who takes your anomalous test result seriously'},
  {name:'Sera',role:'Student (House of Shadow)',desc:'top of the class, distrusts you, watches everything'},
  {name:'Pip',role:'Outcast Student',desc:'knows every secret passage and forgotten rule in the Academy'}
 ],
 'Pirate Seas':[
  {name:'Captain Vane',role:'Pirate Captain',desc:'magnetic, brilliant, tells you exactly as much as you need and no more'},
  {name:'Cook',role:'Ship\'s Cook',desc:'only honest crew member, former Marine, feeds everyone and trusts no one above deck'},
  {name:'Navigator Ren',role:'Navigator',desc:'reads stars and people equally, the one keeping this crew alive'}
 ],
 'Cyberpunk City':[
  {name:'Cipher',role:'Hacker',desc:'your contact who set up the job, paranoid with good reason'},
  {name:'Mako',role:'Street Samurai',desc:'hired muscle, loyal to credits but increasingly to the crew'},
  {name:'Doc Voss',role:'Medtech',desc:'patches wounds, asks no questions, charges fair rates'}
 ],
 'Dragon Realm':[
  {name:'Wyrmologist Cass',role:'Dragon Scholar',desc:'the one who can explain what your bond means, fears what it implies'},
  {name:'Rider Davan',role:'Senior Dragon Rider',desc:'established, territorial, cannot decide if you are a threat or a gift'},
  {name:'Scale Smith Brenn',role:'Armour Crafter',desc:'makes the gear that keeps riders alive, respects the bond, not the politics'}
 ],
 'Hero Academy':[
  {name:'Principal Ozawa',role:'Academy Principal',desc:'knows exactly why your Quirk manifested late, not saying yet'},
  {name:'Yumi',role:'Classmate',desc:'already has a hero name planned, sees you as competition and potential partner'},
  {name:'Instructor Steele',role:'Combat Trainer',desc:'pushes everyone past limits, believes failure is curriculum'}
 ],
 'Medieval Kingdom':[
  {name:'Knight-Commander Aldus',role:'Royal Knight',desc:'the one who drafted you, old soldier, reads duty as religion'},
  {name:'Bard Elise',role:'Court Bard',desc:'travels everywhere, knows everything, sells information in songs'},
  {name:'Thief Corren',role:'Guild Thief',desc:'pressed into service same as you, quick fingers, quicker to disappear'}
 ],
 'The Wrongly Accused':[
  {name:'Warden Cho',role:'Prison Warden',desc:'follows the law precisely, would release you if the law told them to'},
  {name:'Childhood Friend Lian',role:'Investigator',desc:'believes you, risking their position to prove it'},
  {name:'Ghost of Elder Huo',role:'Ancestor Spirit',desc:'dead sect elder who witnessed the theft, can only communicate in riddles'}
 ],
 'The Traitor\'s Escape':[
  {name:'Princess Vael',role:'Deposed Royal',desc:'the client who is not what she was described as, dangerous in ways you are still learning'},
  {name:'Loyalist Spy Maren',role:'Court Informant',desc:'planted near the princess, allegiance genuinely unclear'},
  {name:'Old Mentor Brax',role:'Retired Mercenary',desc:'your former teacher, warned you against this job and helped you take it anyway'}
 ],
 'The Suitor\'s Tournament':[
  {name:'Princess Isolde',role:'Princess',desc:'your host and the prize the tournament is built around, deeply unimpressed by everyone so far'},
  {name:'Herald Tomis',role:'Tournament Herald',desc:'manages every rule, the only neutral party, knows which suitors are cheating'},
  {name:'Rival Suitor Davan',role:'Foreign Prince',desc:'charming, well-funded, playing a longer game than the tournament'}
 ],
 'Blade for Hire':[
  {name:'Princess Vael',role:'Client-in-Disguise',desc:'the merchant you were hired to guard, actually exiled royalty'},
  {name:'Mercenary Captain Reith',role:'Rival Merc',desc:'competing contract, not necessarily an enemy'},
  {name:'Old Retainer Sora',role:'Loyal Servant',desc:'has served the princess since birth, would die for her and may have to'}
 ],
 'The Prince\'s Champion':[
  {name:'Prince Davan',role:'The Prince',desc:'chose you personally over the official list, has his reasons, keeping them'},
  {name:'Court Healer Lyss',role:'Royal Healer',desc:'independent, the prince\'s most trusted confidant, evaluating you'},
  {name:'Commander Vane',role:'Knight\'s Order Captain',desc:'was not consulted on the prince\'s choice, has not forgotten'}
 ],
 'Fifteen Years a Prisoner':[
  {name:'Warden Cho',role:'Prison Warden',desc:'fair by the rules, the rules have kept you here fifteen years'},
  {name:'Old Ally Mira',role:'Former Comrade',desc:'found you, got herself imprisoned to pass a message, time is running out'},
  {name:'Rebel Leader Sable',role:'Resistance Commander',desc:'wants to use your freedom for a cause you have not agreed to yet'}
 ],
 'Human and the Elven Queen':[
  {name:'Queen Aelindra',role:'Elven Queen',desc:'ancient, precise, treating you as an experiment in human diplomacy'},
  {name:'Half-Elf Guide Sil',role:'Border Guide',desc:'assigned to you, neither fully trusted by either side, your only honest source'},
  {name:'Elven Advisor Theron',role:'Court Advisor',desc:'opposed your mission from the start, politely, persistently'}
 ],
 'Ivywood Dormitory':[
  {name:'Dorm Roommate Jess',role:'Roommate',desc:'has been here three years, knows every campus secret, decides in week one whether to like you'},
  {name:'Professor Nori',role:'Faculty Advisor',desc:'assigned to you personally, the scholarship had conditions they are going to explain when ready'},
  {name:'Rival Student Cade',role:'Student',desc:'comes from money, resents merit, good in a crisis when it suits them'}
 ],
 'Wandering Blades':[
  {name:'Guild Quartermaster Holt',role:'Quartermaster',desc:'assigned your party and the job, knows more about why than they\'re saying'},
  {name:'Party Healer Wren',role:'Cleric',desc:'keeps you alive, keeps score, still waiting for an apology from the former leader'},
  {name:'Rogue Dex',role:'Scout',desc:'heard about your expulsion from the last party, curious, cautious'}
 ],
 'The Abandoned Party':[
  {name:'New Ally Cass',role:'Former Enemy',desc:'was with the dungeon faction your old party fought, knows the layout, has their own agenda'},
  {name:'Wandering Healer Yuki',role:'Healer',desc:'no guild ties, no past with your old party, the only clean slate you have'},
  {name:'Guildmaster Vane',role:'Guild Commander',desc:'still waiting for your report on what happened three years ago'}
 ],
 'Space Station':[
  {name:'Engineer Reva',role:'Chief Engineer',desc:'has kept the station running through three command changes, trusts systems over people'},
  {name:'Dr. Sato',role:'Station Scientist',desc:'was here before the last three captains, knows what actually happened to them'},
  {name:'AI Entity ARIA',role:'Station AI',desc:'assists with everything, logged everything, bound by protocols that may be outdated'}
 ],
 'Demon Slayer Corps':[
  {name:'Hashira Riku',role:'Water Hashira',desc:'your direct superior, unorthodox style himself, believes in yours despite saying otherwise'},
  {name:'Fellow Slayer Hana',role:'Slayer',desc:'passed Final Selection same season as you, the only one who witnessed your first kill'},
  {name:'Crow Handler Momo',role:'Kakushi Support',desc:'delivers orders, retrieves the wounded, knows every slayer\'s real weakness'}
 ],
 'Post-Apocalypse':[
  {name:'Mechanic Voss',role:'Engineer',desc:'keeps the Vault\'s generators running, knows which systems are actually failing'},
  {name:'Doctor Sable',role:'Vault Physician',desc:'has the full medical records for everyone born here, including you'},
  {name:'Scout Ren',role:'Surface Scout',desc:'the only person who goes outside, brings back things the Overseer doesn\'t report'}
 ],
 'Zombie Outbreak':[
  {name:'Medic Yara',role:'Field Medic',desc:'has the last remaining antibiotics, making impossible calls about who gets them'},
  {name:'Ex-Cop Mads',role:'Former Officer',desc:'knows the city layout, used to operating in chaos, trust issues with authority including their own'},
  {name:'Scientist Orlov',role:'Virologist',desc:'knows what caused the outbreak, hasn\'t decided who to tell yet'}
 ],
 'Haunted Precinct':[
  {name:'Partner Detective Ash',role:'Detective',desc:'senior partner, should have retired, keeps finding reasons not to'},
  {name:'Medium Reva',role:'Psychic Consultant',desc:'officially unofficial, the department pretends she doesn\'t exist, calls her every time'},
  {name:'Coroner Mira',role:'Forensic Pathologist',desc:'finds things in autopsies that shouldn\'t be there, documents everything anyway'}
 ],
 'Deep Space Frontier':[
  {name:'Xenobiologist Dr. Vael',role:'Scientist',desc:'filed the report that started all this, trying to control what happens next'},
  {name:'Alien Diplomat Thren',role:'First Contact Envoy',desc:'arriving on a schedule only they know, the reason the survey team transferred'},
  {name:'Engineer Sable',role:'Chief Engineer',desc:'has read the previous survey reports, sharing what they found selectively'}
 ],
 'Crown & Shadows':[
  {name:'Court Advisor Maren',role:'Senior Advisor',desc:'briefed you, is testing you, has survived four monarchs by being indispensable'},
  {name:'Spymaster Vane',role:'Intelligence Chief',desc:'was not told you were being appointed, finding out what you know'},
  {name:'Heir Apparent Davan',role:'Royal Heir',desc:'your age, sharper than they appear, watching the new appointment with open interest'}
 ],
 'The Sterling Family':[
  {name:'Sterling Patriarch',role:'Family Head',desc:'controls the money, sets the rules, enforces both with equal precision'},
  {name:'Sterling Sibling Ash',role:'Family Member',desc:'the only one who was honest with you about what this family is'},
  {name:'Family Lawyer Reith',role:'Legal Counsel',desc:'knows where every asset is and what it cost, present at every critical moment'}
 ],
 'Office Rivalry':[
  {name:'Manager Holt',role:'Department Manager',desc:'playing you and your rival against each other deliberately, calling it healthy competition'},
  {name:'Rival Coworker Blake',role:'Competitor',desc:'has been here longer, knows the politics, taking the rivalry personally'},
  {name:'Assistant Yuki',role:'Team Assistant',desc:'observes everything, says little, the most accurate source of information in the building'}
 ],
 'Twenty Years Gone':[
  {name:'Former Partner Ash',role:'Old Friend',desc:'stayed, built a life, unsure whether to be angry or relieved you\'re back'},
  {name:'What They Left Behind',role:'Family Member',desc:'grew up without you, formed their own opinion, not adjusting it for your return'},
  {name:'Person Who Knew Why',role:'Witness',desc:'knows exactly why you left, has been waiting for someone to ask'}
 ],
 'Blood & Loyalty':[
  {name:'Underboss Reith',role:'Family Second',desc:'Marco\'s right hand, loyal to the family not the person, watching the new addition'},
  {name:'Family Lawyer Sable',role:'Fixer',desc:'makes problems disappear legally, has a threshold for what they\'ll make disappear'},
  {name:'Old Guard Voss',role:'Veteran Member',desc:'was here before Marco, remembers how the last outsider was brought in'}
 ],
 'Ridgewood University':[
  {name:'Roommate Jess',role:'Housemate',desc:'returning student, knows the campus and the unwritten rules, decides fast about people'},
  {name:'Professor Nori',role:'Academic Advisor',desc:'assigned to your case specifically, one of the few who knows your full file'},
  {name:'Campus Security Mads',role:'Security Officer',desc:'has seen every kind of trouble this campus produces, can read who causes which kind'}
 ],
 'Second Marriage':[
  {name:'Partner\'s Child Ash',role:'Stepchild',desc:'old enough to have an opinion, young enough to still be forming it about you'},
  {name:'Former In-Law Reith',role:'Ex-Family Member',desc:'still present in the partner\'s life, made a point of meeting you early'},
  {name:'Mutual Friend Yuki',role:'Family Friend',desc:'was friends with both before, trying to stay friends with both after, struggling'}
 ],
 'Dragon Riders':[
  {name:'Wyrmologist Cass',role:'Dragon Scholar',desc:'explains the bond\'s implications, terrified of what yours means for the program'},
  {name:'Senior Rider Davan',role:'Established Rider',desc:'your dragon\'s first choice before it chose you, has not fully processed this'},
  {name:'Scale Smith Brenn',role:'Armour Crafter',desc:'already measuring your dragon for kit, the most practical person in the facility'}
 ],
 'Witch Trials':[
  {name:'Investigator Holt',role:'Church Inquisitor',desc:'believes in the law if not the accusations, looking for the actual explanation'},
  {name:'Village Healer Yara',role:'Herbalist',desc:'half the accused are her patients, she knows what they were actually doing'},
  {name:'Former Accuser Ash',role:'Key Witness',desc:'started the accusations, wants to stop them, cannot without admitting why they began'}
 ],
 'The Heist':[
  {name:'Fixer Reith',role:'Coordinator',desc:'planned the job, knows every exit, only shares information on a need-to-know basis'},
  {name:'Tech Specialist Yuki',role:'Systems Expert',desc:'handles the alarms and locks, nervous, the most honest member of the crew'},
  {name:'Driver Mads',role:'Getaway Driver',desc:'outside the whole time, knows every route, the last person anyone suspects'}
 ],
 'Fallen Kingdom':[
  {name:'Old Mentor Voss',role:'Former General',desc:'taught you, believed in the king, is not sure the kingdom is worth what\'s being asked to restore it'},
  {name:'Resistance Leader Sable',role:'Rebel Commander',desc:'has held the resistance together since the fall, paying personal costs that show'},
  {name:'Spy Reva',role:'Double Agent',desc:'inside the usurper\'s court, information that comes at a price you won\'t like'}
 ],
 'The Oracle\'s Apprentice':[
  {name:'The Oracle',role:'Mentor',desc:'tells you what you need to hear rather than what you want to, in sequences that only later make sense'},
  {name:'Fellow Apprentice Ash',role:'Rival Student',desc:'has been training longer, resents being surpassed in the Oracle\'s attention, brilliant'},
  {name:'Pilgrim Yara',role:'Seeker',desc:'arrived with a question only the Oracle will answer, your first real test case'}
 ],
 'Shipwrecked':[
  {name:'Ship\'s Navigator Ren',role:'Survivor',desc:'knows these waters, their charts are gone but the knowledge isn\'t'},
  {name:'Passenger Ash',role:'Civilian',desc:'was travelling for reasons they haven\'t explained, more capable than they look'},
  {name:'Ship\'s Cook Momo',role:'Survivor',desc:'has the most practical skills on this island and the most even temper'}
 ],
 'Vampire Court':[
  {name:'Ancient Vael',role:'Elder Vampire',desc:'one of the oldest at court, chose your petition for reasons not yet disclosed'},
  {name:'Court Liaison Ash',role:'Human Liaison',desc:'human, navigates the court for mortals, keeps score of who owes what'},
  {name:'Rival Claimant Maren',role:'Competing Petitioner',desc:'wants what you want, playing by different rules'}
 ],
 'The Wild Hunt':[
  {name:'Hunt Master Davan',role:'Hunt Leader',desc:'bound to run the Hunt regardless of cost, respects those who can keep up'},
  {name:'Fae Scout Puck',role:'Trickster Guide',desc:'your assigned guide, their help always costs something, usually worth it'},
  {name:'Mortal Companion Ash',role:'Fellow Hunter',desc:'also caught up in this, also not fully sure how, the most honest thing in the forest'}
 ],
 'Time Rift':[
  {name:'Temporal Agent Voss',role:'Agency Handler',desc:'assigned to your case, working from a protocol written before this scenario was possible'},
  {name:'Local Contact Yuki',role:'Period Contact',desc:'native to this time, knows you don\'t belong here, helping for reasons that become clearer'},
  {name:'Rival Traveller Sable',role:'Competitor',desc:'arrived separately, same goal, fundamentally different approach'}
 ],
 'Alien Contact':[
  {name:'First Contact Lead Dr. Vael',role:'Linguist',desc:'has been preparing for this her entire career, the weight is showing'},
  {name:'Alien Envoy Thren',role:'First Contact Representative',desc:'patient, watching every reaction, communicating in layers'},
  {name:'Military Liaison Mads',role:'Security Officer',desc:'there to control the situation, not convinced that\'s possible'}
 ],
 'Bounty Hunter':[
  {name:'Fixer Reith',role:'Contract Broker',desc:'finds the jobs, takes the cut, provides information that may not be complete'},
  {name:'Partner Ash',role:'Hunting Partner',desc:'works with you sometimes, has their own list, cleaner methods than yours or dirtier depending'},
  {name:'Informant Yuki',role:'Network Contact',desc:'knows where people hide, charges fair rates, stays out of the actual work'}
 ],
 'The Last Mage':[
  {name:'Ancient Archive ARIA',role:'Magical Repository',desc:'holds the last recorded knowledge of the old mages, selective about what it shares and when'},
  {name:'Hunter Voss',role:'Mage Hunter',desc:'sent to find you, finding you increasingly complicated'},
  {name:'Young Mage Ash',role:'Student',desc:'found you first, learning from you, reason enough not to disappear'}
 ],
 'Rebellion':[
  {name:'Commander Sable',role:'Rebel Leader',desc:'founded the rebellion on a principle they have been asked to compromise every year since'},
  {name:'Spy Reva',role:'Intelligence Officer',desc:'inside the empire\'s structure, the information comes at a cost to them they don\'t mention'},
  {name:'Soldier Voss',role:'Veteran Fighter',desc:'has been in longer than you, knows what the rebellion has asked people to give'}
 ],
 'Underground Arena':[
  {name:'Arena Master Holt',role:'Promoter',desc:'owns your contract, respects fighters, operates in a world without rules and enforces his own'},
  {name:'Trainer Yara',role:'Combat Coach',desc:'has taken broken fighters and made something out of them, sees something in you'},
  {name:'Rival Mads',role:'Top Fighter',desc:'current champion, earned it, watching the new entry with professional attention'}
 ],
 'The Forgotten God':[
  {name:'Ancient Priest Voss',role:'Last Believer',desc:'kept the faith when everyone else stopped, waiting for you specifically'},
  {name:'Scholar Reva',role:'Mythologist',desc:'studies forgotten religions academically, was not expecting any of this to be real'},
  {name:'Skeptic Ash',role:'Witness',desc:'cannot explain what they saw, will not say it was what it looked like'}
 ],
 'Prison Break':[
  {name:'Cell Neighbour Yuki',role:'Inmate',desc:'knows the facility\'s rhythms better than the guards, waiting to see if you\'re worth including'},
  {name:'Corrupt Guard Mads',role:'Officer',desc:'has a price, has lines they won\'t cross, figuring out which category you fall in'},
  {name:'Outside Contact Reva',role:'External Ally',desc:'has resources you need, their own reasons for getting you out, timeline is not negotiable'}
 ],
 'War Correspondent':[
  {name:'Local Fixer Yuki',role:'Field Fixer',desc:'keeps you alive in territory you don\'t know, has opinions about the story you should be telling'},
  {name:'Rival Journalist Ash',role:'Competitor',desc:'same conflict, different outlet, overlapping sources, more experience and less caution'},
  {name:'Military Liaison Mads',role:'Embedded Officer',desc:'controls your access, invested in a specific narrative, not entirely wrong about the danger'}
 ],
 'Royal Scandal':[
  {name:'Royal Chamberlain Reith',role:'Palace Administrator',desc:'knows everything about the palace, sharing selectively, chose you for this role with intent'},
  {name:'Implicated Noble Vael',role:'Scandal Figure',desc:'at the centre of what happened, their account is true in the ways that matter to them'},
  {name:'Court Journalist Ash',role:'Press Contact',desc:'already has the story half-written, will publish with or without your cooperation'}
 ],
 'The Cure':[
  {name:'Lead Researcher Dr. Sato',role:'Scientist',desc:'found the compound, knows the side effects, trying to find a way around the choice'},
  {name:'Test Subject Ash',role:'Patient',desc:'volunteered because there was no other option, coherent enough to consent, most of the time'},
  {name:'Funder Reith',role:'Sponsor',desc:'paid for the research, owns the results legally, has decided what happens with them'}
 ],
 'Galactic Senate':[
  {name:'Senior Senator Vael',role:'Political Mentor',desc:'assigned as your guide, old enough to have caused several of the problems you\'re addressing'},
  {name:'Opposition Senator Maren',role:'Political Rival',desc:'your most consistent opponent, frequently correct, never cooperative'},
  {name:'Intelligence Liaison Ash',role:'Agency Contact',desc:'provides information the official channels don\'t carry, with terms attached'}
 ],
 'The Cult':[
  {name:'Cult Leader Silas',role:'Leader',desc:'believes everything they say, which makes them more dangerous not less'},
  {name:'Doubting Member Yuki',role:'Insider',desc:'been here three years, finding cracks in the doctrine, needs someone to trust'},
  {name:'Outside Investigator Ash',role:'Researcher',desc:'building a case, needs access you have, cannot guarantee your safety'}
 ],
 'River Crossing':[
  {name:'Guide Voss',role:'River Guide',desc:'knows every crossing point, working from a map last updated before recent events'},
  {name:'Fellow Traveller Yuki',role:'Co-traveller',desc:'crossing for different reasons, your paths align for now, diverge later'},
  {name:'Border Official Mads',role:'Authority',desc:'controls the official crossing, the reason you\'re looking for another one'}
 ],
 'The Inheritance':[
  {name:'Family Lawyer Reith',role:'Estate Lawyer',desc:'executor of the will, knows what was left and why it was structured this way'},
  {name:'Other Heir Ash',role:'Contesting Heir',desc:'was not expecting to share, recalibrating'},
  {name:'Family Retainer Yuki',role:'Household Staff',desc:'worked for the deceased their entire life, the most accurate source of what actually happened here'}
 ],
 'Island Survival':[
  {name:'Navigator Ren',role:'Survival Expert',desc:'keeps their head, knows which problems to solve in which order'},
  {name:'Fellow Survivor Ash',role:'Survivor',desc:'resourceful in ways you wouldn\'t predict from looking at them'},
  {name:'Injured Passenger Yuki',role:'Dependent',desc:'cannot help physically yet, has specific knowledge that changes what survival means here'}
 ],
 'Cold Case':[
  {name:'Partner Detective Ash',role:'Detective',desc:'worked this case before, transferred out, agreed to come back when you asked'},
  {name:'Original Witness Yuki',role:'Witness',desc:'gave a statement years ago that doesn\'t fully hold together on re-reading, available to talk'},
  {name:'Forensic Lead Dr. Mira',role:'Forensics',desc:'found something new in the archived evidence, that\'s why the case is open again'}
 ],
 'The Duel':[
  {name:'Second Voss',role:'Your Second',desc:'rules of the duel, your safety, managing both under conditions that keep changing'},
  {name:'Opponent\'s Second Ash',role:'Opposing Second',desc:'equally bound by the rules, equally aware they\'re being tested'},
  {name:'Mediator Reith',role:'Neutral Party',desc:'required to be present, trying to find the version of this where nobody dies'}
 ],
 'Academy for Villains':[
  {name:'Headmaster Vane',role:'Academy Head',desc:'built this institution on a philosophy you are about to test'},
  {name:'Instructor Mads',role:'Combat Trainer',desc:'was a villain before this, took the job to give students options he didn\'t have'},
  {name:'Rival Student Ash',role:'Top of Class',desc:'arrived with a fully formed plan for their career, you\'re not in it, they noticed you anyway'}
 ],
 'Midnight Market':[
  {name:'Market Elder Holt',role:'Senior Trader',desc:'has been here since before the market had its current name, decides who gets full access'},
  {name:'Source Yuki',role:'Information Broker',desc:'trades in what people want to know, more careful than they appear'},
  {name:'Enforcer Mads',role:'Market Security',desc:'keeps the peace by rules nobody fully understands, they enforce them consistently anyway'}
 ],
 'The Siege':[
  {name:'Commander Vane',role:'Garrison Commander',desc:'has held this position through two previous sieges, knows exactly what the walls can take'},
  {name:'Quartermaster Holt',role:'Supply Officer',desc:'counting days until provisions run out, that number is accurate and not public knowledge'},
  {name:'Scout Reva',role:'Intelligence Officer',desc:'slips through the lines, brings information that changes the situation and the options'}
 ],
 'Fae Bargain':[
  {name:'Fae Advisor Puck',role:'Trickster Guide',desc:'bound to help you by the bargain\'s terms, finding ways to be technically helpful'},
  {name:'Mortal Contact Ash',role:'Human Liaison',desc:'has dealt with Fae before, knows which rules are real and which are theatre'},
  {name:'Elder Fae Vael',role:'Ancient Authority',desc:'set the terms of the bargain, interested in whether you understand what you agreed to'}
 ],
 'The Exiled Prince':[
  {name:'Loyal Guard Reva',role:'Protector',desc:'chose exile over duty to the new regime, their reasons are not entirely about you'},
  {name:'Local Contact Yuki',role:'Underground Connection',desc:'provides safe passage and information, running their own operation simultaneously'},
  {name:'Rival Claimant Ash',role:'Competition',desc:'also exiled, also trying to return, would work with you if the terms were right'}
 ],
 'Deep Jungle':[
  {name:'Guide Voss',role:'Jungle Expert',desc:'knows this terrain in a way that cannot be explained from maps alone'},
  {name:'Researcher Dr. Yuki',role:'Expedition Scientist',desc:'the official reason for the expedition, has begun to suspect the actual reason'},
  {name:'Local Elder Momo',role:'Indigenous Guide',desc:'agreed to help for reasons not yet shared, the person who actually knows what\'s in here'}
 ],
 'Haunted Circus':[
  {name:'Ringmaster Vane',role:'Circus Director',desc:'knows the circus\'s history and has decided how much to tell you'},
  {name:'Acrobat Ash',role:'Performer',desc:'has been here through the events that made this circus what it is, watched everyone leave'},
  {name:'Roustabout Yuki',role:'Crew Member',desc:'sets up and tears down, sees everything, the most reliable source of what actually happens overnight'}
 ],
 'The Healer':[
  {name:'Senior Healer Mira',role:'Mentor',desc:'trained you, believes in your potential, bound by the same limits they\'re teaching you to work around'},
  {name:'Patient Ash',role:'Difficult Case',desc:'your most demanding assignment, the case that is teaching you what healing actually requires'},
  {name:'Administrator Holt',role:'Clinic Director',desc:'manages the resources, sets the cases, the reason you sometimes have to choose who gets help'}
 ],
 'Underground Railroad':[
  {name:'Station Master Mara',role:'Network Coordinator',desc:'runs this section of the network, careful, experienced, never uses more words than the situation requires'},
  {name:'Conductor Voss',role:'Route Guide',desc:'knows the paths, the safe houses, the timing, what happens when things go wrong'},
  {name:'Freedperson Ash',role:'Traveller',desc:'en route to safety, carrying information about what\'s behind and information you need to hear'}
 ]
};

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
  const _sceneHint=op.length>20?op.slice(0,120).replace(/['"<>&]/g,''):'';
  const _scPrompt=_sceneHint?`${s.catLabel} scene: ${s.name} — ${_sceneHint}, cinematic rpg illustration, atmospheric lighting, detailed environment, no text`:`${s.catLabel} rpg scene, ${s.name}, cinematic illustration, atmospheric, detailed`;
  const _scStyle={fantasy:'Fantasy Art',anime:'Anime Portrait',zombie:'Dark Fantasy',supernatural:'Dark Fantasy',mystery:'Dark Fantasy',apocalyptic:'Dark Fantasy',cyberpunk:'Cyberpunk',alien_space:'Sci-Fi',drama:'Cinematic',game:'Fantasy Art'}[s.catKey]||'Fantasy Art';
  const protagonist=SCENARIO_PROTAGONISTS[s.name]||'';
  const storyTitle=protagonist?`${safe(s.name)} <span class="scenario-card-protagonist">· ${safe(protagonist)}'s story</span>`:`${safe(s.name)}`;
  return `<div class="scenario-card" data-cat="${safe(s.catKey)}" data-name="${safe(s.name)}" data-type="${safe(s.type)}">
   <div class="scenario-card-img" style="background:${COLORS[s.catKey]||'#141c24'}" data-prompt="${safe(_scPrompt)}" data-style="${safe(_scStyle)}" data-opening="${safe(op.slice(0,200))}" data-category="${safe(s.catKey)}"><span>${ICONS[s.catKey]||'⚔'}</span><img src="" alt=""></div>
   <div class="scenario-card-body">
    <div class="scenario-card-genre">${safe(s.catLabel)}</div>
    <div class="scenario-card-name">${storyTitle}</div>
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
  const go=()=>{
   state.pendingCategory=cats.find(c=>c.key===card.dataset.cat);
   const pv=card.querySelector('.scenario-card-preview');
   const openingText=pv?pv.textContent.trim():'';
   launchPlayerStep({category:card.dataset.cat,scenario_name:card.dataset.name,scenario_type:card.dataset.type,custom_text:openingText||undefined});
  };
  const pb=card.querySelector('.scenario-card-play');if(pb)pb.onclick=e=>{e.stopPropagation();go()};
  const mb=card.querySelector('.scenario-card-more');
  if(mb)mb.onclick=e=>{
   e.stopPropagation();
   // Fill the Opening Scenario textarea with this card's full opening text
   const pv=card.querySelector('.scenario-card-preview');
   const fullText=pv?pv.textContent.trim():'';
   const ta=$('#openingScenarioText');
   if(ta&&fullText){
    ta.value=fullText;
    // Trigger resize if auto-grow is active
    ta.dispatchEvent(new Event('input'));
    // Scroll to and flash the textarea so the user sees it was filled
    ta.scrollIntoView({behavior:'smooth',block:'center'});
    ta.classList.remove('flash');
    requestAnimationFrame(()=>requestAnimationFrame(()=>{ta.classList.add('flash');setTimeout(()=>ta.classList.remove('flash'),800);}));
    ta.focus();
   }
   mb.title='Story copied to Opening Scenario below';
  };
  card.onclick=go;
 });
 if(_scObserver)_scObserver.disconnect();
 // Apply any already-loaded pre-generated covers immediately
 $$('#scenarioCardsGrid .scenario-card').forEach(card=>{
  const name=card.dataset.name;const url=_scCovers[name];if(!url)return;
  const img=card.querySelector('.scenario-card-img img');
  if(img&&!img.classList.contains('sc-loaded')){img.src=url;img.onload=()=>img.classList.add('sc-loaded');}
 });
 _scObserver=new IntersectionObserver(entries=>{entries.forEach(entry=>{
  if(!entry.isIntersecting)return;
  const imgDiv=entry.target;_scObserver.unobserve(imgDiv);
  const img=imgDiv.querySelector('img'),card=imgDiv.closest('.scenario-card');
  if(!img||!card)return;
  if(_scCovers[card.dataset.name]){
   img.src=_scCovers[card.dataset.name];img.onload=()=>img.classList.add('sc-loaded');return;
  }
  _scQueueImg(card.dataset.name,imgDiv.dataset.prompt,img,imgDiv.dataset.style||'Fantasy Art',
   imgDiv.dataset.opening||'',imgDiv.dataset.category||'');
 })},{threshold:0.1,rootMargin:'60px'});
 $$('#scenarioCardsGrid .scenario-card-img').forEach(el=>_scObserver.observe(el));
}

$('#startNewGameBtn').onclick=async()=>{
 try{
  if(!categoriesCache)categoriesCache=await api('/api/scenarios/categories');
  // Load pre-generated covers (non-blocking — renders cards with whatever is ready)
  _loadScenarioCovers().then(()=>{
   // Re-inject any covers that loaded after initial render
   $$('#scenarioCardsGrid .scenario-card').forEach(card=>{
    const name=card.dataset.name;
    const url=_scCovers[name];
    if(!url)return;
    const img=card.querySelector('.scenario-card-img img');
    if(img&&!img.classList.contains('sc-loaded')){img.src=url;img.onload=()=>img.classList.add('sc-loaded');}
   });
  });
  const sel=$('#worldCategorySelect');
  sel.innerHTML='<option value="all">🌐 All Worlds</option>'+categoriesCache.map(c=>`<option value="${safe(c.key)}">${safe(c.label)} (${c.scenarios.length})</option>`).join('');
  sel.onchange=()=>renderScenarioCards(categoriesCache,sel.value);
  renderScenarioCards(categoriesCache,'all');
  showStartStep('category');
 }catch(error){toast(error.message)}
};
function _activeCatKey(){const v=$('#worldCategorySelect')?.value;return(v&&v!=='all')?v:state.pendingCategory?.key||'fantasy'}
$('#customScenarioForm').onsubmit=e=>{e.preventDefault();const text=new FormData(e.currentTarget).get('text')||'';if(!text.trim()){toast('Write a scenario first');return}launchPlayerStep({category:_activeCatKey(),scenario_name:text.slice(0,40),scenario_type:'custom',custom_text:text})};

$('#showTemplatesBtn').onclick=async()=>{await loadTemplateList();showStartStep('templates')};
async function loadTemplateList(){
 try{const templates=await api('/api/scenario-templates');$('#templateList').innerHTML=templates.length?templates.map(t=>`<button data-template-id="${t.id}"><b>${safe(t.name)}</b><small>${safe(t.scenario.slice(0,60))}</small></button>`).join(''):'<div class="empty-state">No saved templates yet.</div>';
  $$('#templateList [data-template-id]').forEach(btn=>{
   const template=templates.find(t=>String(t.id)===btn.dataset.templateId);
   btn.onclick=async()=>{try{const rendered=await api('/api/scenario-templates/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:template.name,scenario:template.scenario})});launchPlayerStep({category:state.pendingCategory?.key||'fantasy',scenario_name:template.name,scenario_type:'custom',custom_text:rendered.scenario})}catch(error){toast(error.message)}};
  });
 }catch(error){$('#templateList').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}
}
$('#newTemplateForm').onsubmit=async e=>{e.preventDefault();const formEl=e.currentTarget;const payload=Object.fromEntries(new FormData(formEl).entries());try{await api('/api/scenario-templates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast('Template saved');formEl.reset();loadTemplateList()}catch(error){toast(error.message)}};

$('#randomScenarioBtn').onclick=async()=>{await rollRandomScenario();showStartStep('random')};
async function rollRandomScenario(){try{const result=await api('/api/random/prompts');state.randomScenarioText=result.scenario;$('#randomScenarioText').textContent=result.scenario}catch(error){$('#randomScenarioText').textContent=error.message}}
$('#rerollScenarioBtn').onclick=rollRandomScenario;
$('#useRandomScenarioBtn').onclick=()=>launchPlayerStep({category:_activeCatKey(),scenario_name:'Random Scenario',scenario_type:'custom',custom_text:state.randomScenarioText});

async function loadSavedGame(save){try{await bindSession({sessionId:save.session_id,worldId:save.world_id,characterId:save.character_id});location.reload()}catch(error){toast(error.message)}}
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
$('#map').addEventListener('click',e=>{
  if(e.target.closest('button')||e.target.closest('.map-node-preview'))return;
  hideNodePreview();
  // Blur any focused input so WASD/arrow keys work immediately after clicking the map
  if(document.activeElement&&document.activeElement!==document.body)document.activeElement.blur();
  const r=e.currentTarget.getBoundingClientRect();
  const nx=(e.clientX-r.left)/r.width*100,ny=(e.clientY-r.top)/r.height*100;
  move(nx,ny);
  const rip=$('#mapMoveRipple');
  if(rip){rip.style.left=(e.clientX-r.left)+'px';rip.style.top=(e.clientY-r.top)+'px';rip.classList.remove('ripple-active');void rip.offsetWidth;rip.classList.add('ripple-active');}
});
// ── Help view: sections come from /api/help, built from the game's own data ──
let _helpSections=null;
// Pictures are generated one at a time, only for entries scrolled into view.
let _helpPicQueue=[],_helpPicBusy=false,_helpPicObserver=null,_helpPicOff=false;
function _helpPicHtml(sec,id,image,canPicture,icon,alt,extraClass){
  const cls='help-pic'+(extraClass?' '+extraClass:'');
  if(image)return `<img class="${cls}" src="${safe(image)}" alt="${safe(alt)}" loading="lazy">`;
  if(canPicture)return `<div class="${cls} help-pic-pending" data-help-pic="${safe(sec)}/${safe(id)}" data-alt="${safe(alt)}"><span>${safe(icon||'✦')}</span><small>Picture loads when viewed</small></div>`;
  return '';
}
async function _helpPicNext(){
  if(_helpPicBusy)return;
  const el=_helpPicQueue.shift();if(!el)return;
  if(!el.isConnected){_helpPicNext();return;}
  if(_helpPicOff){const sm=el.querySelector('small');if(sm)sm.textContent='Picture unavailable';_helpPicNext();return;}
  _helpPicBusy=true;
  const [section,id]=el.dataset.helpPic.split('/');
  const stop=startGenTimer(el.querySelector('small'),'Painting');
  try{
    const r=await api('/api/help/picture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({section,id})});
    stop();
    const target=section==='sections'?_helpSections.find(x=>x.id===id):_helpSections.find(x=>x.id===section)?.entries.find(e=>e.id===id);
    if(target)target.image=r.url;
    if(el.isConnected)el.outerHTML=`<img class="${el.className.replace(' help-pic-pending','')}" src="${safe(r.url)}" alt="${safe(el.dataset.alt||'')}">`;
  }catch(error){stop();_helpPicOff=true;const sm=el.querySelector('small');if(sm)sm.textContent='Picture unavailable';}
  _helpPicBusy=false;_helpPicNext();
}
function _helpWatchPictures(){
  if(_helpPicObserver)_helpPicObserver.disconnect();
  _helpPicQueue=[];
  if(!('IntersectionObserver' in window))return;
  _helpPicObserver=new IntersectionObserver(items=>{
    for(const it of items){if(it.isIntersecting){_helpPicObserver.unobserve(it.target);_helpPicQueue.push(it.target);}}
    _helpPicNext();
  },{rootMargin:'100px'});
  $$('#helpContent [data-help-pic]').forEach(el=>_helpPicObserver.observe(el));
}
function _helpEntryHtml(sec,e){
  const stats=Object.entries(e.stats||{}).map(([k,v])=>`<span class="help-stat"><b>${safe(v)}</b>${safe(k)}</span>`).join('');
  const rows=Object.entries(e.fields||{}).map(([k,v])=>`<div class="help-field"><dt>${safe(k)}</dt><dd>${safe(v)}</dd></div>`).join('');
  const links=(e.links||[]).map(l=>l.view
    ?`<button type="button" class="help-link help-link-app" data-help-view="${safe(l.view)}">${safe(l.label)} ↗</button>`
    :`<button type="button" class="help-link" data-help-goto="${safe(l.section)}/${safe(l.entry||'')}">${safe(l.label)}</button>`).join('');
  return `<article class="help-entry" id="help-${safe(sec.id)}-${safe(e.id)}">
    ${_helpPicHtml(sec.id,e.id,e.image,e.can_picture,e.icon,e.name)}
    <h3><span class="help-icon">${safe(e.icon||'')}</span>${safe(e.name)}</h3>
    ${e.summary?`<p>${safe(e.summary)}</p>`:''}
    ${stats?`<div class="help-stats">${stats}</div>`:''}
    ${rows?`<dl>${rows}</dl>`:''}
    ${e.example?`<div class="help-example"><b>Example</b>${safe(e.example)}</div>`:''}
    ${links?`<div class="help-links"><small>See also</small>${links}</div>`:''}
  </article>`;
}
function renderHelp(){
  if(!_helpSections)return;
  const words=($('#helpSearch').value||'').toLowerCase().split(/\s+/).filter(Boolean);
  const text=e=>(e.name+' '+e.summary+' '+(e.example||'')+' '+Object.entries(e.fields||{}).concat(Object.entries(e.stats||{})).map(([k,v])=>k+' '+v).join(' ')).toLowerCase();
  const matches=e=>{const hay=text(e);return words.every(w=>hay.includes(w));};
  let shown=0;
  const html=_helpSections.map(sec=>{
    const entries=words.length?sec.entries.filter(matches):sec.entries;
    if(!entries.length)return '';
    shown+=entries.length;
    // Long reference sections start collapsed; a search opens whatever matched.
    const open=words.length||sec.entries.length<=16;
    const banner=words.length?'':_helpPicHtml('sections',sec.id,sec.image,sec.can_picture,sec.icon,sec.title,'help-banner');
    return `<details class="help-section" id="help-${safe(sec.id)}"${open?' open':''}><summary><b><span class="help-icon">${safe(sec.icon||'')}</span>${safe(sec.title)}</b><small>${entries.length}${words.length?` of ${sec.entries.length}`:''}</small><span>${safe(sec.intro||'')}</span></summary>${banner}<div class="help-entries">${entries.map(e=>_helpEntryHtml(sec,e)).join('')}</div></details>`;
  }).join('');
  $('#helpContent').innerHTML=html||'<div class="empty-state">Nothing matches that search.</div>';
  const total=_helpSections.reduce((n,s)=>n+s.entries.length,0);
  $('#helpCount').textContent=words.length?`${shown} of ${total} entries`:`${total} entries`;
  _helpWatchPictures();
}
function helpGoto(sectionId,entryId){
  if($('#helpSearch').value){$('#helpSearch').value='';renderHelp();}
  const sec=document.getElementById('help-'+sectionId);if(!sec)return;
  sec.open=true;
  const target=entryId?document.getElementById(`help-${sectionId}-${entryId}`):sec;
  if(!target)return;
  target.scrollIntoView({behavior:'smooth',block:entryId?'center':'start'});
  if(entryId){target.classList.add('help-flash');setTimeout(()=>target.classList.remove('help-flash'),1600);}
}
async function loadHelp(){
  if(_helpSections){renderHelp();return;}
  try{
    _helpSections=await api('/api/help');
    $('#helpNav').innerHTML=_helpSections.map(s=>`<button type="button" data-help-section="${safe(s.id)}"><span class="help-icon">${safe(s.icon||'')}</span>${safe(s.title)}</button>`).join('');
    $('#helpNav').onclick=e=>{const btn=e.target.closest('[data-help-section]');if(btn)helpGoto(btn.dataset.helpSection,'');};
    $('#helpContent').addEventListener('click',e=>{
      const go=e.target.closest('[data-help-goto]');
      if(go){const [sec,entry]=go.dataset.helpGoto.split('/');helpGoto(sec,entry);return;}
      const view=e.target.closest('[data-help-view]');
      if(view)openView(view.dataset.helpView);
    });
    // Sections opened by hand reveal new picture placeholders.
    $('#helpContent').addEventListener('toggle',e=>{if(e.target.open)_helpWatchPictures();},true);
    $('#helpSearch').oninput=renderHelp;
    renderHelp();
  }catch(error){$('#helpContent').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`;}
}
function closeTopDialog(){
  for(const id of ['levelUpModal','questRewardModal','craftModal','saveLoadModal','recruitModal']){const m=document.getElementById(id);if(m&&!m.hidden){m.hidden=true;return true;}}
  const opts=document.getElementById('mediaOptsModal');if(opts){opts.remove();return true;}
  const loc=document.getElementById('locContentOverlay');if(loc&&!loc.classList.contains('hidden')){loc.classList.add('hidden');return true;}
  if(document.body.classList.contains('sidebar-open')&&document.body.classList.contains('game-active')&&document.querySelector('#view-play.active')){document.body.classList.remove('sidebar-open');return true;}
  return false;
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&closeTopDialog()){e.preventDefault();e.stopPropagation();}},true);
document.addEventListener('keydown',e=>{const active=document.activeElement;const tag=active?.tagName;if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||active?.isContentEditable)return;if(e.key==='Escape'){hideNodePreview();return;}const keys={w:[0,-3],ArrowUp:[0,-3],s:[0,3],ArrowDown:[0,3],a:[-3,0],ArrowLeft:[-3,0],d:[3,0],ArrowRight:[3,0]};if(keys[e.key]){e.preventDefault();move(state.x+keys[e.key][0],state.y+keys[e.key][1])}if('1234'.includes(e.key))setScale(['local','country','continent','universe'][+e.key-1])});
$('#portal').onclick=crossPortal;
$('#zoomIn').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.min(140,state.zoom+10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#zoomOut').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.max(70,state.zoom-10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
// ── Save/Load modal ──
function _openSaveModal(){
 let modal=$('#saveLoadModal');
 if(!modal){
  modal=document.createElement('div');
  modal.id='saveLoadModal';
  modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:950;display:flex;align-items:center;justify-content:center';
  modal.innerHTML=`<div style="background:var(--panel);border:1px solid var(--line);border-radius:8px;width:min(460px,95vw);max-height:80vh;display:flex;flex-direction:column">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--line)">
      <b style="color:var(--gold)">Save / Load Game</b>
      <button id="closeSaveModal" style="background:none;border:none;color:#e9ecf1;font-size:18px;cursor:pointer">✕</button>
    </div>
    <div style="padding:12px 16px;border-bottom:1px solid var(--line)">
      <form id="newSaveForm" style="display:flex;gap:6px">
        <input id="saveNameInput" placeholder="Save name…" style="flex:1;padding:6px 8px;background:#0d1117;border:1px solid var(--line);border-radius:4px;color:#e9ecf1;font-size:12px">
        <button type="submit" class="gold" style="font-size:11px;padding:6px 12px">Save</button>
      </form>
    </div>
    <div id="saveSlotList" style="overflow-y:auto;flex:1;padding:12px 16px;display:flex;flex-direction:column;gap:6px">
      <div class="empty-state">Loading saves…</div>
    </div>
  </div>`;
  document.body.appendChild(modal);
  modal.querySelector('#closeSaveModal').onclick=()=>modal.hidden=true;
  modal.onclick=e=>{if(e.target===modal)modal.hidden=true;};
  modal.querySelector('#newSaveForm').onsubmit=async e=>{
    e.preventDefault();
    const name=modal.querySelector('#saveNameInput').value.trim();
    if(!name)return;
    const world=state.worlds[state.worldIndex];
    saveSessionToStorage();
    try{
      await api('/api/game-saves',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({save_name:name,character_id:state.characterId||null,session_id:state.sessionId,world_id:world?.id||null,notes:`Lv ${state.sheet?.calc_lv||1} · ${world?.name||'Unknown'}`})});
      modal.querySelector('#saveNameInput').value='';
      toast(`Saved: ${name}`);
      _loadSaveSlots(modal);
    }catch(e){toast(e.message);}
  };
 }
 modal.hidden=false;
 _loadSaveSlots(modal);
}
async function _loadSaveSlots(modal){
 const list=modal.querySelector('#saveSlotList');
 try{
  const url=state.characterId?`/api/game-saves?character_id=${state.characterId}`:'/api/game-saves';
  const saves=await api(url);
  if(!saves.length){list.innerHTML='<div class="empty-state">No saves yet. Enter a name above and click Save.</div>';return;}
  list.innerHTML=saves.map(s=>`<div style="display:flex;align-items:center;gap:8px;background:#0d1117;border:1px solid var(--line);border-radius:4px;padding:7px 10px">
    <div style="flex:1;min-width:0"><b style="font-size:12px">${safe(s.save_name)}</b><small style="display:block;color:var(--muted);font-size:10px">${safe(s.notes||'')} · ${safe((s.created_at||'').slice(0,16))}</small></div>
    <button data-load-save="${s.id}" class="ghost" style="font-size:10px;padding:3px 8px">Load</button>
    <button data-del-save="${s.id}" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:14px;line-height:1" title="Delete">✕</button>
  </div>`).join('');
  list.querySelectorAll('[data-del-save]').forEach(btn=>btn.onclick=async()=>{
    try{await api(`/api/game-saves/${btn.dataset.delSave}`,{method:'DELETE'});_loadSaveSlots(modal);}catch(e){toast(e.message);}
  });
  list.querySelectorAll('[data-load-save]').forEach(btn=>btn.onclick=async()=>{
    // Just close modal — world/character state is already tracked in state
    modal.hidden=true;
    toast('Save slot loaded — resuming from this state');
  });
 }catch(e){list.innerHTML=`<div class="empty-state">${safe(e.message)}</div>`;}
}
$('#saveBtn').onclick=()=>_openSaveModal();
$('#journalBtn').onclick=()=>toast('Quest journal opened');
function playerContextLine(){
 const world=state.worlds[state.worldIndex]; const s=state.sheet;
 const bits=[`World: ${world?.name}`,`Reality: ${world?.reality_type}`,`Location: ${world?.place||'Unknown'}`,`Map scale: ${state.scale}`];
 if(s){
  bits.push(`Player character: ${s.name}, Level ${s.calc_lv||s.level||1} ${s.race||''} ${s.profession||''}`.trim());
  const {maxHp,maxMana}=derivedResources(s);const hpCtx=state.characterId?getHpState(state.characterId,maxHp,maxMana):{currentHp:maxHp,currentMp:maxMana};
  bits.push(`HP: ${hpCtx.currentHp}/${maxHp}, MP: ${hpCtx.currentMp}/${maxMana}`);
  const equipped=(state.inventory.items||[]).filter(i=>i.equip_slot).map(i=>i.item_name);
  if(equipped.length)bits.push(`Equipped: ${equipped.join(', ')}`);
  if(s.reality_signature?.universe_tag)bits.push(`Reality signature: ${s.reality_signature.universe_tag} (${s.reality_signature.reality_type})`);
 }
 if(state.quests.length)bits.push(`Active quests: ${state.quests.map(q=>q.title).join('; ')}`);
 if(state.partyChars.length){
  const partyDetail=state.partyChars.map(c=>{
   const sh=state.partySheets[c.id];
   if(sh){const {maxHp,maxMana}=derivedResources(sh);const hpSt2=getHpState(c.id,maxHp,maxMana);return `${c.name} (Lv${sh.calc_lv||sh.level||c.level} ${c.race||''} ${c.profession||''}, HP ${hpSt2.currentHp}/${maxHp})`;}
   return `${c.name} (Lv${c.level||1} ${c.race||''} ${c.profession||''})`;
  });
  bits.push(`Party: ${partyDetail.join(', ')}`);
 }
 const memEntries=Object.entries(state.npcMemories||{});
 if(memEntries.length){
  const memStr=memEntries.slice(0,5).map(([name,facts])=>`${name}: ${facts.slice(-2).join('; ')}`).join(' | ');
  bits.push(`NPC memory: ${memStr}`);
 }
 return `[${bits.join(' | ')}]`;
}
async function awardXP(amount,reason=''){
 if(!state.characterId||!amount)return;
 const prevLv=state.sheet?.calc_lv||1;
 try{
  const result=await api(`/api/characters/${state.characterId}/xp`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount,reason})});
  if(result.sheet){state.sheet=result.sheet;renderParty();}
  const newLv=result.sheet?.calc_lv||result.new_level||prevLv;
  if(result.levelled_up||result.leveled_up||newLv>prevLv){
   await levelUp(newLv,result.level_up_choices);
  }else{
   toast(`+${amount} XP`);
  }
 }catch{}
}
async function openLevelUpModal(){
 if(!state.characterId){toast('No character selected');return;}
 try{
  const r=await api(`/api/characters/${state.characterId}/level-up/open`);
  if(!r.has_pending){toast(r.message||'No level-up available yet. Earn XP to level up!');return;}
  showLevelUpModal(r.new_level, r.choices);
 }catch(e){toast(e.message||'Could not open level-up');}
}
async function levelUp(newLevel, inlineChoices){
 const s=state.sheet;
 const {maxHp,maxMana}=derivedResources(s||{});
 if(state.characterId)setHpState(state.characterId,maxHp,maxMana,maxHp,maxMana);
 state.pendingLevelUp=true;
 sfx('levelup');
 const chatLog=$('#chatLog');
 chatLog.insertAdjacentHTML('beforeend',chatMsg('gm',`<div style="border:1px solid var(--gold);border-radius:6px;padding:10px;margin:4px 0;text-align:center"><div style="font-size:16px;color:var(--gold);font-weight:bold;letter-spacing:1px">⬆ LEVEL UP! ⬆</div><div style="margin:4px 0"><b>${safe(s?.name||'Adventurer')}</b> reached <b>Level ${newLevel}</b></div><div style="font-size:10px;color:var(--muted)">${safe(s?.race||'')} ${safe(s?.profession||'')} · HP ${maxHp} · MP ${maxMana}</div></div>`));
 chatLog.scrollTop=chatLog.scrollHeight;
 toast(`Level up! Now level ${newLevel}`);
 renderParty();
 if($('#detailContent').innerHTML.includes('EXPERIENCE'))showPanel('character');
 // Fetch or use inline choices for the level-up modal
 let choices=inlineChoices;
 if(!choices&&state.characterId){
  try{const r=await api(`/api/characters/${state.characterId}/level-up/pending`);if(r.has_pending)choices=r.choices;}catch{}
 }
 if(choices)showLevelUpModal(newLevel,choices);
}
function showLevelUpModal(newLevel,choices){
 const modal=$('#levelUpModal');if(!modal)return;
 const s=state.sheet||{};
 const STAT_LABELS={strength:'Strength',dexterity:'Dexterity',intelligence:'Intelligence',wisdom:'Wisdom',constitution:'Constitution',speed:'Speed',luck:'Luck',charisma_stat:'Charisma'};
 $('#lvlUpTitle').textContent=`LEVEL ${newLevel}!`;
 $('#lvlUpSub').textContent=`${safe(s.name||'Adventurer')} · ${safe(s.race||'')} ${safe(s.profession||'Adventurer')}`;

 const isAsi=choices.is_asi_level;
 const hitDie=choices.hit_die||8;
 const conMod=choices.con_mod||0;
 const profBonus=choices.proficiency_bonus||2;
 const conModStr=conMod>=0?`+${conMod}`:String(conMod);
 const statOpts=(choices.stat_options||Object.keys(STAT_LABELS));
 const picked={asi_mode:'one',stat_asi:'',stat_a:'',stat_b:'',stat:'',feat:'',spell:'',tree_node:'',story_ability:'',profession:''};

 // ── HP & proficiency info banner ──
 let html=`<div style="background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:6px;padding:10px;display:flex;gap:12px;flex-wrap:wrap">`;
 html+=`<div style="flex:1;min-width:120px"><div style="font-size:9px;color:var(--muted);text-transform:uppercase">HP Gain</div><div style="color:var(--green);font-weight:700">d${hitDie} ${conModStr} CON</div><div style="font-size:9px;color:var(--muted)">(${choices.hp_gain_min||1}–${choices.hp_gain_max||hitDie} HP)</div></div>`;
 html+=`<div style="flex:1;min-width:120px"><div style="font-size:9px;color:var(--muted);text-transform:uppercase">Proficiency Bonus</div><div style="color:var(--gold);font-weight:700">+${profBonus}</div></div>`;
 if(isAsi) html+=`<div style="flex:1;min-width:120px"><div style="font-size:9px;color:var(--muted);text-transform:uppercase">ASI Level</div><div style="color:#ffd700;font-weight:700">Ability Score Improvement</div></div>`;
 html+=`</div>`;

 // ── Attribute points ──
 if(isAsi){
  html+=`<div style="border:1px solid var(--gold);border-radius:6px;padding:10px" id="asiSection">
   <div style="font-size:11px;color:var(--gold);text-transform:uppercase;margin-bottom:8px">⬆ Ability Score Improvement <small style="color:var(--muted)">(choose one option)</small></div>
   <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">
    <button class="lvl-asi-mode-btn active-choice" data-mode="one" style="font-size:10px;padding:4px 10px;background:#2a1e0a;border:1px solid var(--gold);border-radius:4px;cursor:pointer;color:var(--gold)">+2 to One Stat</button>
    <button class="lvl-asi-mode-btn" data-mode="split" style="font-size:10px;padding:4px 10px;background:var(--panel);border:1px solid var(--line);border-radius:4px;cursor:pointer;color:#ccc">+1 to Two Stats</button>
    <button class="lvl-asi-mode-btn" data-mode="feat" style="font-size:10px;padding:4px 10px;background:var(--panel);border:1px solid var(--line);border-radius:4px;cursor:pointer;color:#ccc">Take a Feat</button>
   </div>
   <div id="asiContent">
    <div style="font-size:10px;color:var(--muted);margin-bottom:6px">Choose one stat to increase by 2:</div>
    <div style="display:flex;flex-wrap:wrap;gap:6px">${statOpts.map(st=>`<button class="ghost lvl-stat-asi" data-stat="${safe(st)}" style="font-size:10px;padding:4px 10px">${safe(STAT_LABELS[st]||st)}</button>`).join('')}</div>
   </div>
  </div>`;
 } else {
  html+=`<div style="border:1px solid var(--line);border-radius:6px;padding:10px"><div style="font-size:11px;color:var(--gold);text-transform:uppercase;margin-bottom:8px">⬆ Attribute Point <small style="color:var(--muted)">(choose 1 stat +1)</small></div><div style="display:flex;flex-wrap:wrap;gap:6px">${statOpts.map(st=>`<button class="ghost lvl-stat-pick" data-stat="${safe(st)}" style="font-size:10px;padding:4px 10px">${safe(STAT_LABELS[st]||st)}</button>`).join('')}</div></div>`;
 }

 // ── Feat choices (at ASI levels, as alternative) ──
 if(!isAsi && choices.feat_choices?.length){
  html+=`<div style="border:1px solid var(--line);border-radius:6px;padding:10px"><div style="font-size:11px;color:var(--gold);text-transform:uppercase;margin-bottom:8px">⭐ Feat <small style="color:var(--muted)">(choose 1 or skip)</small></div><div style="display:flex;flex-direction:column;gap:6px">${(choices.feat_choices||[]).map(f=>{const fn=f.name||f;const fd=(f.desc||'');const fb=f.bonus||{};const bstr=Object.entries(fb).map(([k,v])=>`+${v} ${STAT_LABELS[k]||k}`).join(', ');return`<button class="ghost lvl-feat-pick" data-feat="${safe(fn)}" style="font-size:10px;padding:6px 10px;text-align:left"><b>${safe(fn)}</b>${fd?`<br><span style="color:var(--muted);font-size:9px">${safe(fd)}</span>`:''} ${bstr?`<span style="color:var(--green);font-size:9px"> · ${safe(bstr)}</span>`:''}</button>`}).join('')}</div></div>`;
 }

 // ── Spell choices ──
 if(choices.spell_choices?.length){
  html+=`<div style="border:1px solid #9c27b0;border-radius:6px;padding:10px"><div style="font-size:11px;color:#bb86fc;text-transform:uppercase;margin-bottom:8px">✨ Spell <small style="color:var(--muted)">(choose 1 or skip)</small></div><div style="display:flex;flex-direction:column;gap:6px">${choices.spell_choices.map(sp=>{const spn=sp.name||sp;const spd=sp.desc||'';const spl=sp.level??0;const sps=sp.school||'';return`<button class="ghost lvl-spell-pick" data-spell="${safe(spn)}" style="font-size:10px;padding:6px 10px;text-align:left"><b>${safe(spn)}</b> <span style="color:#bb86fc;font-size:9px">${spl===0?'Cantrip':`Lv${spl}`} ${safe(sps)}</span>${spd?`<br><span style="color:var(--muted);font-size:9px">${safe(spd.substring(0,80))}${spd.length>80?'…':''}</span>`:''}</button>`}).join('')}</div></div>`;
 }

 // ── Skill tree node choices ──
 if(choices.tree_node_choices?.length){
  html+=`<div style="border:1px solid #00bcd4;border-radius:6px;padding:10px"><div style="font-size:11px;color:#00e5ff;text-transform:uppercase;margin-bottom:8px">🌳 Skill Tree <small style="color:var(--muted)">(unlock 1 node or skip)</small></div><div style="display:flex;flex-direction:column;gap:6px">${choices.tree_node_choices.map(n=>`<button class="ghost lvl-tree-pick" data-nodeid="${safe(n.id)}" style="font-size:10px;padding:6px 10px;text-align:left"><b>${safe(n.icon||'')} ${safe(n.name)}</b> <span style="color:#00bcd4;font-size:9px">${safe(n.category)} T${safe(String(n.tier))}</span><br><span style="color:var(--muted);font-size:9px">${safe((n.desc||'').substring(0,80))}</span></button>`).join('')}</div></div>`;
 }

 // ── Profession choices ──
 if(choices.profession_choices?.length){
  html+=`<div style="border:1px solid var(--line);border-radius:6px;padding:10px"><div style="font-size:11px;color:var(--gold);text-transform:uppercase;margin-bottom:8px">👑 Profession <small style="color:var(--muted)">(choose 1 or keep current)</small></div><div style="display:flex;flex-wrap:wrap;gap:6px">${choices.profession_choices.map(p=>`<button class="ghost lvl-prof-pick" data-prof="${safe(p)}" style="font-size:10px;padding:4px 10px">${safe(p)}</button>`).join('')}</div></div>`;
 }

 // ── Story abilities section (loaded async) ──
 html+=`<div style="border:1px solid #e91e63;border-radius:6px;padding:10px" id="storyGiftsSection"><div style="font-size:11px;color:#f06292;text-transform:uppercase;margin-bottom:8px">✦ Story Abilities <small style="color:var(--muted)">(choose 1 or skip)</small></div><div id="storyGiftsBody" style="color:var(--muted);font-size:11px;text-align:center;padding:8px">⏳ Generating story abilities…</div></div>`;

 const body=$('#lvlUpBody');body.innerHTML=html;

 // Wire up ASI mode toggle
 if(isAsi){
  $$('.lvl-asi-mode-btn').forEach(btn=>{
   btn.onclick=()=>{
    picked.asi_mode=btn.dataset.mode;
    $$('.lvl-asi-mode-btn').forEach(b=>{b.classList.remove('active-choice');b.style.background='var(--panel)';b.style.borderColor='var(--line)';b.style.color='#ccc';});
    btn.classList.add('active-choice');btn.style.background='#2a1e0a';btn.style.borderColor='var(--gold)';btn.style.color='var(--gold)';
    // Update asiContent
    const ac=$('#asiContent');if(!ac)return;
    if(picked.asi_mode==='one'){
     ac.innerHTML=`<div style="font-size:10px;color:var(--muted);margin-bottom:6px">Choose one stat to increase by 2:</div><div style="display:flex;flex-wrap:wrap;gap:6px">${statOpts.map(st=>`<button class="ghost lvl-stat-asi" data-stat="${safe(st)}" style="font-size:10px;padding:4px 10px">${safe(STAT_LABELS[st]||st)}</button>`).join('')}</div>`;
     $$('.lvl-stat-asi').forEach(b=>b.onclick=()=>{picked.stat_asi=b.dataset.stat;$$('.lvl-stat-asi').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
    } else if(picked.asi_mode==='split'){
     ac.innerHTML=`<div style="font-size:10px;color:var(--muted);margin-bottom:6px">First stat +1:</div><div style="display:flex;flex-wrap:wrap;gap:6px" id="asiSplitA">${statOpts.map(st=>`<button class="ghost lvl-stat-a" data-stat="${safe(st)}" style="font-size:10px;padding:4px 10px">${safe(STAT_LABELS[st]||st)}</button>`).join('')}</div><div style="font-size:10px;color:var(--muted);margin:8px 0 6px">Second stat +1:</div><div style="display:flex;flex-wrap:wrap;gap:6px" id="asiSplitB">${statOpts.map(st=>`<button class="ghost lvl-stat-b" data-stat="${safe(st)}" style="font-size:10px;padding:4px 10px">${safe(STAT_LABELS[st]||st)}</button>`).join('')}</div>`;
     $$('.lvl-stat-a').forEach(b=>b.onclick=()=>{picked.stat_a=b.dataset.stat;$$('.lvl-stat-a').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
     $$('.lvl-stat-b').forEach(b=>b.onclick=()=>{picked.stat_b=b.dataset.stat;$$('.lvl-stat-b').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
    } else {
     const fcs=choices.feat_choices||[];
     if(!fcs.length){ac.innerHTML=`<div style="color:var(--muted);font-size:11px">No feats available.</div>`;return;}
     ac.innerHTML=`<div style="display:flex;flex-direction:column;gap:6px">${fcs.map(f=>{const fn=f.name||f;const fd=f.desc||'';const bstr=Object.entries(f.bonus||{}).map(([k,v])=>`+${v} ${STAT_LABELS[k]||k}`).join(', ');return`<button class="ghost lvl-feat-pick" data-feat="${safe(fn)}" style="font-size:10px;padding:6px 10px;text-align:left"><b>${safe(fn)}</b>${fd?`<br><span style="color:var(--muted);font-size:9px">${safe(fd)}</span>`:''} ${bstr?`<span style="color:var(--green);font-size:9px"> · ${safe(bstr)}</span>`:''}</button>`}).join('')}</div>`;
     $$('.lvl-feat-pick').forEach(b=>b.onclick=()=>{picked.feat=b.dataset.feat;$$('.lvl-feat-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
    }
   };
  });
  // Wire initial ASI +2 mode buttons
  $$('.lvl-stat-asi').forEach(b=>b.onclick=()=>{picked.stat_asi=b.dataset.stat;$$('.lvl-stat-asi').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
 }

 // Wire non-ASI stat
 $$('.lvl-stat-pick').forEach(b=>b.onclick=()=>{picked.stat=b.dataset.stat;$$('.lvl-stat-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
 // Wire non-ASI feat
 $$('.lvl-feat-pick').forEach(b=>b.onclick=()=>{picked.feat=b.dataset.feat;$$('.lvl-feat-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
 // Wire spells
 $$('.lvl-spell-pick').forEach(b=>b.onclick=()=>{picked.spell=b.dataset.spell;$$('.lvl-spell-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
 // Wire tree nodes
 $$('.lvl-tree-pick').forEach(b=>b.onclick=()=>{picked.tree_node=b.dataset.nodeid;$$('.lvl-tree-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
 // Wire professions
 $$('.lvl-prof-pick').forEach(b=>b.onclick=()=>{picked.profession=b.dataset.prof;$$('.lvl-prof-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});

 modal.hidden=false;

 // Async load story gifts
 if(state.characterId){
  api(`/api/characters/${state.characterId}/level-up/story-gifts`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>{
   const gb=$('#storyGiftsBody');if(!gb)return;
   const gifts=(r.gifts||[]);
   if(!gifts.length){gb.innerHTML='<div style="color:var(--muted);font-size:11px">No story abilities available yet.</div>';return;}
   gb.innerHTML=`<div style="display:flex;flex-direction:column;gap:6px">${gifts.map(g=>{const bn=Object.entries(g.bonus||{}).map(([k,v])=>`+${v} ${STAT_LABELS[k]||k}`).join(', ');return`<button class="ghost lvl-story-pick" data-ability="${safe(JSON.stringify(g))}" style="font-size:10px;padding:6px 10px;text-align:left"><b>${safe(g.name||'?')}</b> <span style="color:#f06292;font-size:9px">${safe(g.type||'')}</span>${bn?`<span style="color:var(--green);font-size:9px"> · ${safe(bn)}</span>`:''}<br><span style="color:var(--muted);font-size:9px">${safe((g.desc||'').substring(0,100))}</span></button>`}).join('')}</div>`;
   $$('.lvl-story-pick').forEach(b=>b.onclick=()=>{picked.story_ability=b.dataset.ability;$$('.lvl-story-pick').forEach(x=>x.classList.remove('active-choice'));b.classList.add('active-choice');});
  }).catch(()=>{const gb=$('#storyGiftsBody');if(gb)gb.innerHTML='<div style="color:var(--muted);font-size:11px">Story abilities unavailable.</div>';});
 }

 const claimBtn=$('#lvlUpClaimBtn');
 if(claimBtn)claimBtn.onclick=async()=>{
  // Validate the user has made required choices
  if(isAsi){
   if(picked.asi_mode==='one'&&!picked.stat_asi){toast('Pick a stat for +2 ASI');return;}
   if(picked.asi_mode==='split'&&(!picked.stat_a||!picked.stat_b)){toast('Pick two stats for split ASI');return;}
   if(picked.asi_mode==='feat'&&!picked.feat){toast('Pick a feat');return;}
  } else {
   if(!picked.stat){toast('Pick an attribute to boost');return;}
  }
  try{
   const payload={};
   if(isAsi){
    if(picked.asi_mode==='one') payload.stat_asi=picked.stat_asi;
    else if(picked.asi_mode==='split'){payload.stat_a=picked.stat_a;payload.stat_b=picked.stat_b;}
    else if(picked.asi_mode==='feat') payload.feat=picked.feat;
   } else {
    payload.stat=picked.stat;
   }
   if(!isAsi&&picked.feat) payload.feat=picked.feat;
   if(picked.spell) payload.spell=picked.spell;
   if(picked.tree_node) payload.tree_node=picked.tree_node;
   if(picked.story_ability) payload.story_ability=picked.story_ability;
   if(picked.profession) payload.profession=picked.profession;
   const r=await api(`/api/characters/${state.characterId}/level-up/claim`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   if(r.sheet){state.sheet=r.sheet;state.pendingLevelUp=false;renderParty();showPanel('character');}
   toast(`Level-up claimed! ${(r.applied||[]).join(' · ')}`);
   modal.hidden=true;
  }catch(e){toast(e.message||'Claim failed');}
 };
 modal.onclick=e=>{if(e.target===modal)modal.hidden=true;};
}
function renderInventory(){
 const dc=$('#detailContent');
 if(dc&&(dc.querySelector('.inventory-grid')||dc.querySelector('.armory-grid')))showPanel('inventory');
}
function _openCraftModal(){
 const items=(state.inventory.items||[]).filter(it=>!it.equip_slot);
 if(items.length<2){toast('Need at least 2 bag items to craft');return;}
 let modal=$('#craftModal');
 if(!modal){
  modal=document.createElement('div');
  modal.id='craftModal';
  modal.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:950;display:flex;align-items:center;justify-content:center';
  document.body.appendChild(modal);
 }
 const optHtml=items.map(it=>`<option value="${it.id}">${safe(it.item_name)} (tier ${it.weapon_tier||0})</option>`).join('');
 modal.innerHTML=`<div style="background:var(--panel);border:1px solid var(--line);border-radius:8px;width:min(380px,95vw);padding:16px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <b style="color:var(--gold)">⚗ Craft Items</b>
    <button id="closeCraftModal" style="background:none;border:none;color:#e9ecf1;font-size:18px;cursor:pointer">✕</button>
  </div>
  <p style="font-size:11px;color:var(--muted);margin-bottom:10px">Combine two items into a higher-tier crafted weapon. Both source items are consumed.</p>
  <div style="display:flex;flex-direction:column;gap:8px">
    <select id="craftItemA" style="padding:6px 8px;background:#0d1117;border:1px solid var(--line);border-radius:4px;color:#e9ecf1;font-size:12px">${optHtml}</select>
    <select id="craftItemB" style="padding:6px 8px;background:#0d1117;border:1px solid var(--line);border-radius:4px;color:#e9ecf1;font-size:12px">${optHtml}</select>
  </div>
  <button id="doCraftBtn" class="gold" style="width:100%;margin-top:12px;padding:8px">⚗ Craft</button>
 </div>`;
 modal.hidden=false;
 modal.querySelector('#closeCraftModal').onclick=()=>{modal.hidden=true;};
 modal.querySelector('#doCraftBtn').onclick=async()=>{
  const a=+modal.querySelector('#craftItemA').value,b=+modal.querySelector('#craftItemB').value;
  if(a===b){toast('Select two different items');return;}
  try{
   const result=await api(`/api/characters/${state.characterId}/craft`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item_id_a:a,item_id_b:b})});
   modal.hidden=true;
   sfx('loot');
   await refreshCharacterState();
   renderInventory();
   toast(`Crafted: ${result.item_name} (tier ${result.weapon_tier})`);
  }catch(e){toast(e.message);}
 };
}
async function travelToWorld(worldId){
 if(!worldId)return;
 const already=state.worlds.findIndex(w=>w.id===worldId);
 if(already>=0){
  state.worldIndex=already;updateWorld();setScale('local');
  saveSessionToStorage();
  _recordWorldVisit(worldId);
  toast(`Entered ${safe(state.worlds[already].name)}`);return;
 }
 try{
  const w=await api(`/api/worlds/${worldId}`);
  const entry=typeof toWorldEntry==='function'?toWorldEntry(w):w;
  state.worlds.unshift(entry);state.worldIndex=0;
  updateWorld();setScale('local');
  saveSessionToStorage();
  _recordWorldVisit(worldId);
  toast(`Traveled to ${safe(w.name)}`);
 }catch(e){toast(e.message);}
}
function _recordWorldVisit(worldId){
 if(!worldId)return;
 const loc=state.worlds.find(w=>w.id===worldId);
 api(`/api/worlds/${worldId}/visit`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_id:state.characterId||null,location_name:loc?.place||''})}).catch(()=>{});
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
 }catch{
  $('#chatAvatar').classList.remove('speaking');
  if(!speakReply._warnedOnce){speakReply._warnedOnce=true;toast('Voice unavailable — check TTS settings');}
 }
}
speakReply._warnedOnce=false;
$('#voiceToggleBtn').onclick=()=>{
 state.voiceEnabled=!state.voiceEnabled;
 localStorage.setItem('companion-voice',state.voiceEnabled);
 $('#voiceToggleBtn').classList.toggle('active',state.voiceEnabled);
 $('#voiceToggleBtn').innerHTML=state.voiceEnabled?'🔊 Voice on':'🔈 Voice off';
 if(!state.voiceEnabled)stopChatAudio();
};
$('#voiceToggleBtn').classList.toggle('active',state.voiceEnabled);
$('#voiceToggleBtn').innerHTML=state.voiceEnabled?'🔊 Voice on':'🔈 Voice off';

// ── Exit speaker (narrator mode) ──
const _exitSpBtn=$('#exitSpeakerBtn');
if(_exitSpBtn)_exitSpBtn.onclick=()=>{state.activeSpeaker=null;updateSpeakerUI();renderParty();toast('Returned to narrator mode');};

// ── Recruit companion modal ──
async function openRecruitModal(){
  const modal=$('#recruitModal');if(!modal)return;
  modal.hidden=false;
  const list=$('#recruitCharList');if(!list)return;
  list.innerHTML='<div style="color:var(--muted);font-size:11px">Loading characters…</div>';
  try{
    const chars=await api('/api/characters');
    state._savedCharCache=chars;
    const world=state.worlds[state.worldIndex];
    // Sort: characters from current world first
    const sorted=[...chars].sort((a,b)=>{
      const aw=a.origin_world||a.origin||'';const bw=b.origin_world||b.origin||'';
      const wn=world?.name||'';
      return (bw.includes(wn)?1:0)-(aw.includes(wn)?1:0);
    });
    if(!sorted.length){list.innerHTML='<div style="color:var(--muted);font-size:11px">No saved characters yet. Create one in the Characters tab.</div>';return;}
    list.innerHTML=sorted.map(ch=>{
      const inParty=!!state.partyChars.find(p=>p.id===ch.id);
      const av=ch.photo_path?`<img src="${safe(ch.photo_path)}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;flex-shrink:0">`:`<div style="width:36px;height:36px;border-radius:50%;background:var(--line);display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0">${safe((ch.name||'?').slice(0,2).toUpperCase())}</div>`;
      return`<div style="display:flex;align-items:center;gap:10px;padding:8px;background:#141c24;border-radius:6px;border:1px solid var(--line)">
        ${av}
        <div style="flex:1;min-width:0">
          <div style="font-weight:bold;font-size:12px">${safe(ch.name)}</div>
          <div style="font-size:10px;color:var(--muted)">${safe(ch.race||'')} ${safe(ch.profession||'')} · LV ${safe(ch.level||1)}</div>
          <div style="font-size:10px;color:var(--muted)">${safe(String(ch.scenario||ch.origin_world||ch.origin||'Unknown world').slice(0,40))}</div>
        </div>
        <button data-recruit-id="${ch.id}" class="${inParty?'ghost':'gold'}" style="font-size:10px;padding:4px 10px;flex-shrink:0" ${inParty?'disabled':''}>
          ${inParty?'In party':'+ Add'}
        </button>
        ${inParty||ch.id===state.characterId?'':`<button data-delete-char="${ch.id}" class="ghost" title="Delete this saved character" style="font-size:11px;padding:4px 8px;flex-shrink:0">🗑</button>`}
      </div>`;
    }).join('');
    $$('[data-recruit-id]').forEach(btn=>btn.onclick=async()=>{
      const cid=+btn.dataset.recruitId;
      const ch=chars.find(c=>c.id===cid);if(!ch)return;
      addCharToParty(ch);
      btn.textContent='In party';btn.disabled=true;btn.className='ghost';
    });
    $$('[data-delete-char]').forEach(btn=>btn.onclick=async()=>{
      const cid=+btn.dataset.deleteChar;
      const ch=chars.find(c=>c.id===cid);if(!ch)return;
      if(!confirm(`Delete "${ch.name}" (level ${ch.level||1}) permanently? Their inventory and quests are deleted too.`))return;
      try{await api(`/api/characters/${cid}`,{method:'DELETE'});toast(`${ch.name} deleted`);openRecruitModal();}catch(err){toast(err.message);}
    });
  }catch(err){list.innerHTML=`<div style="color:var(--muted);font-size:11px">${safe(err.message)}</div>`;}
}
const _addMemberBtn=$('.add-member');
if(_addMemberBtn)_addMemberBtn.onclick=openRecruitModal;
const _closeRecruit=$('#closeRecruitModal');
if(_closeRecruit)_closeRecruit.onclick=()=>{const m=$('#recruitModal');if(m)m.hidden=true;};
const _recruitModal=$('#recruitModal');
if(_recruitModal)_recruitModal.onclick=e=>{if(e.target===_recruitModal)_recruitModal.hidden=true;};

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
 const cid=state.characterId?`&character_id=${state.characterId}`:'';
 const cname=state.sheet?.name?`&character_name=${encodeURIComponent(state.sheet.name)}`:'';
 const a=document.createElement('a');
 a.href=`/api/chat/export/zip?session_id=${sid}${cid}${cname}`;
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
  $('#chatInput').value=transcript;if(window._chatInputGrow)window._chatInputGrow();
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
$('#chatLog').addEventListener('click',e=>{
  const btn=e.target.closest('.llm-retry');if(!btn)return;
  btn.closest('.chat-msg')?.remove();
  state._retryPending=true;$('#chatInput').value=btn.dataset.retry;$('#chatForm').requestSubmit();
});
$('#chatForm').onsubmit=async e=>{
  e.preventDefault();
  const input=$('#chatInput'),msg=input.value.trim();if(!msg)return;

  // ── /help command: show all chat commands ──
  if(/^\/help\b/i.test(msg)){
    input.value='';
    const HELP_HTML=`<div style="font-size:11px;line-height:1.8">
<b style="color:var(--gold);font-size:13px">⚔ Chat Commands</b><br>
<code style="color:#8fb7c8">/place Name, Terrain, Description</code> — Add a location to the map<br>
<small style="color:var(--muted)">Names with kingdom/empire/federation → Continent map; province/district/county → Country map; others → Local map</small><br>
<small style="color:var(--muted)">Terrain: Forest, City, Ruins, Underground, Ocean, Mountains, Plains, Desert, Swamp</small><br>
<code style="color:#8fb7c8">*add location: Name, local|country|continent|universe*</code> — Add location via chat<br>
<code style="color:#8fb7c8">/help</code> — Show this command list<br>
<hr style="border-color:var(--line);margin:6px 0">
<b style="color:var(--gold)">Map Tabs</b><br>
<kbd>1</kbd> <b>Local</b> — buildings &amp; places in the same city/village (click to see scene image)<br>
<kbd>2</kbd> <b>Country</b> — regions &amp; districts within the country<br>
<kbd>3</kbd> <b>Continent</b> — kingdoms, empires, nations across the world<br>
<kbd>4</kbd> <b>Universe</b> — all worlds &amp; realms<br>
<small style="color:var(--muted)">Backstory buildings auto-populate the Local map; AI mentions of kingdoms/regions are auto-added</small><br>
<hr style="border-color:var(--line);margin:6px 0">
<b style="color:var(--gold)">Dialogue Format (in AI replies)</b><br>
<code>Name: Hello there.</code> — Character dialogue (name in gold)<br>
<code>**Name draws their sword.**</code> — Action / narration text<br>
<hr style="border-color:var(--line);margin:6px 0">
<b style="color:var(--gold)">Party</b><br>
Click a party member card — Speak as that character<br>
✕ Narrator — Return to GM narrator mode<br>
+ Add Member — Recruit a saved character as companion<br>
<hr style="border-color:var(--line);margin:6px 0">
<button type="button" class="ghost" onclick="openView('help')" style="padding:5px 12px;cursor:pointer">? Open the full Help — rules, classes, races, feats, spells, tags</button></div>`;
    const chatLog=$('#chatLog');
    chatLog.insertAdjacentHTML('beforeend',`<div class="chat-msg gm"><div class="msg-body"><b>WORLDWEAVER</b>${HELP_HTML}</div></div>`);
    chatLog.scrollTop=chatLog.scrollHeight;
    return;
  }

  // ── /place command: add location to correct map level ──
  if(/^\/place\b/i.test(msg)){
    input.value='';
    const body=msg.replace(/^\/place\s*/i,'').trim();
    const parts=body.split(',').map(s=>s.trim());
    const locName=parts[0];
    if(!locName){toast('Usage: /place Name, Terrain, Description');return;}
    const rawTerrain=parts[1]||'';
    const desc=parts.slice(2).join(',').trim();
    const TERRAIN_WORDS={forest:'Forest',wood:'Forest',jungle:'Forest',cave:'Underground',cavern:'Underground',dungeon:'Underground',mine:'Underground',ocean:'Ocean',sea:'Ocean',lake:'Ocean',river:'Ocean',port:'Ocean',coast:'Ocean',city:'City',town:'City',village:'City',market:'City',inn:'City',tavern:'City',castle:'Ruins',fortress:'Ruins',ruin:'Ruins',tower:'Ruins',temple:'Ruins',shrine:'Ruins',mountain:'Mountains',peak:'Mountains',hill:'Mountains',plains:'Plains',field:'Plains',meadow:'Plains',desert:'Desert',swamp:'Swamp',marsh:'Swamp'};
    const tKey=rawTerrain.toLowerCase().replace(/[^a-z]/g,'');
    const terrain=TERRAIN_WORDS[tKey]||(rawTerrain?rawTerrain.charAt(0).toUpperCase()+rawTerrain.slice(1):'Plains');
    // Auto-detect loc_type from name keywords
    const nameDesc=`${locName} ${desc}`.toLowerCase();
    const loc_type=_isContinentType(nameDesc.match(/\b(\w+)\b/g)?.find(w=>CONTINENT_TYPES.has(w))||'')?'continent':/\b(country|province|district|county|shire|region|canton|prefecture|march)\b/.test(nameDesc)?'country':'local';
    const world=state.worlds[state.worldIndex];
    if(!world){toast('Start a game first');return;}
    const existing=new Set(state.locations.map(l=>l.name.toLowerCase()));
    if(existing.has(locName.toLowerCase())){toast(`${locName} already on map`);return;}
    const x=10+Math.random()*80,y=10+Math.random()*80;
    try{
      const loc=await api(`/api/worlds/${world.id}/locations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:locName,terrain,x,y,description:desc||`Added by player: ${locName}`,loc_type})});
      if(loc&&loc.id){
        state.locations.push(loc);
        const tabForType={continent:'continent',country:'country',local:'local'};
        const targetScale=tabForType[loc_type]||'local';
        if(state.scale!==targetScale)setScale(targetScale);else renderMapNodes();
        const chatLog=$('#chatLog');
        const tabLabel={continent:'Continent map',country:'Country map',local:'Local map'}[loc_type]||'map';
        chatLog.insertAdjacentHTML('beforeend',`<div class="chat-msg gm"><div class="msg-body"><b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action">📍 ${safe(locName)} added to the ${tabLabel} (${safe(terrain)}).</em>${desc?` <span style="color:var(--muted);font-size:11px">${safe(desc)}</span>`:''}</div></div></div>`);
        chatLog.scrollTop=chatLog.scrollHeight;
        toast(`📍 ${locName} → ${tabLabel}`);
      }
    }catch(err){toast(`Failed to add location: ${err.message}`);}
    return;
  }

  // ── *add location: NAME, MAP* inline command (also passes through to AI) ──
  {
    const addLocRe=/\*add\s+location\s*:\s*([^,*\n]+),\s*(local|country|continent|universe)\s*\*/gi;
    let alm;
    while((alm=addLocRe.exec(msg))!==null){
      const locName=alm[1].trim(), mapLevel=alm[2].toLowerCase();
      const world2=state.worlds[state.worldIndex];
      if(world2&&locName){
        const lt=mapLevel==='continent'?'continent':mapLevel==='country'?'country':'local';
        const existing2=new Set(state.locations.map(l=>l.name.toLowerCase()));
        if(!existing2.has(locName.toLowerCase())){
          const x2=10+Math.random()*80,y2=10+Math.random()*80;
          api(`/api/worlds/${world2.id}/locations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:locName,terrain:'Plains',x:x2,y:y2,description:'Added by player',loc_type:lt})})
          .then(loc=>{if(loc&&loc.id){state.locations.push(loc);renderMapNodes();toast(`📍 ${locName} → ${mapLevel} map`);}})
          .catch(()=>{});
        }
      }
    }
  }

  const sp=state.activeSpeaker;
  const playerLabel=sp?`<b style="color:var(--gold)">${safe(sp.name)}:</b> `:'';
  const isRetry=state._retryPending===true;state._retryPending=false;
  if(!isRetry)$('#chatLog').insertAdjacentHTML('beforeend',chatMsg('player',playerLabel+fmtChat(msg)));
  input.value='';if(input.tagName==='TEXTAREA'){input.style.height='auto';}$('#aiStatus').textContent='Thinking…';
  // typing indicator bubble
  const typingId='typing-'+Date.now();
  $('#chatLog').insertAdjacentHTML('beforeend',`<div class="chat-msg gm" id="${typingId}"><div class="msg-body"><span class="typing-dots"><span></span><span></span><span></span></span></div></div>`);
  $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
  try{
    const world=state.worlds[state.worldIndex];
    let charName,extraCtx;
    if(sp){
      charName=sp.name;
      const partyList=state.partyChars.map(c=>c.name).join(', ');
      extraCtx=`${playerContextLine()} | ACTIVE SPEAKER: You are now roleplaying exclusively as ${sp.name}, a ${sp.race||''} ${sp.profession||''}. Respond in first person from ${sp.name}'s perspective — their personality, emotions, knowledge and worldview. Do NOT break character. Party: ${partyList}.${sp.backstory?` Backstory: ${sp.backstory.slice(0,600)}`:''}`;
    } else {
      charName='Worldweaver';extraCtx=playerContextLine();
    }
    const payload={content:msg,extra_context:extraCtx,session_id:state.sessionId,world_id:world?.id,user_name:'Player',character_name:charName,participants:sp?[sp.name]:['Worldweaver'],temperature:.75,retry:isRetry};
    const replyLabel=sp?`<b style="color:var(--gold)">${safe(sp.name)}</b> `:'<b>WORLDWEAVER</b> ';
    const streamResp=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!streamResp.ok||!streamResp.body){
      const te2=document.getElementById(typingId);if(te2)te2.remove();
      const fallResp=await api('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const reply=fallResp?.reply||fallResp?.content||'';
      if(isLlmError(reply)){$('#chatLog').insertAdjacentHTML('beforeend',llmErrorBubble(reply,msg));}
      else if(reply){$('#chatLog').insertAdjacentHTML('beforeend',chatMsg('gm',replyLabel+fmtChat(reply)));speakReply(reply);detectStoryChars(reply);const _ds=detectScaleFromChat(reply);if(_ds&&_ds!==state.scale)setScale(_ds);addLocationsFromChat(reply);addLocationsFromChat(msg);}
      $('#aiStatus').textContent=llmStatus(sp,reply);
      saveSessionToStorage();$('#chatLog').scrollTop=$('#chatLog').scrollHeight;return;
    }
    // replace typing indicator with live streaming bubble
    const typingEl=document.getElementById(typingId);
    let fullReply='',msgId=null;
    const streamBubbleId='stream-'+Date.now();
    if(typingEl)typingEl.outerHTML=`<div class="chat-msg gm" id="${streamBubbleId}"><div class="msg-body">${replyLabel}<span id="${streamBubbleId}-txt"></span></div></div>`;
    const txtEl=document.getElementById(`${streamBubbleId}-txt`);
    const reader=streamResp.body.getReader();const dec=new TextDecoder();
    let buf='';
    while(true){
      const{done,value}=await reader.read();
      if(done)break;
      buf+=dec.decode(value,{stream:true});
      const lines=buf.split('\n');buf=lines.pop();
      for(const line of lines){
        if(!line.startsWith('data:'))continue;
        const raw=line.slice(5).trim();
        if(raw==='[DONE]')break;
        try{
          const chunk=JSON.parse(raw);
          if(chunk.id)msgId=chunk.id;
          if(chunk.text){fullReply+=chunk.text;if(txtEl)txtEl.innerHTML=fmtChat(fullReply);}
        }catch{}
      }
    }
    // update bubble id with server message id for actions
    if(msgId){const el=document.getElementById(streamBubbleId);if(el)el.dataset.msgId=msgId;}
    $('#aiStatus').textContent=llmStatus(sp,fullReply);
    if(isLlmError(fullReply)){const eb=document.getElementById(streamBubbleId);if(eb)eb.outerHTML=llmErrorBubble(fullReply,msg);$('#chatLog').scrollTop=$('#chatLog').scrollHeight;return;}
    if(fullReply){speakReply(fullReply);detectStoryChars(fullReply);const _ds=detectScaleFromChat(fullReply);if(_ds&&_ds!==state.scale)setScale(_ds);addLocationsFromChat(fullReply);addLocationsFromChat(msg);loadNpcMemories().catch(()=>{});}
    saveSessionToStorage();
    // Auto-generate story quest every 8 AI replies if character active
    state._chatReplyCount=(state._chatReplyCount||0)+1;
    if(state.characterId&&state._chatReplyCount%8===0&&state.quests.length<4){
      try{
        const w=state.worlds[state.worldIndex];
        const r=await api('/api/quests/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({character_name:state.sheet?.name,character_id:state.characterId,world_id:w?.id,session_id:state.sessionId,quest_type:'story'})});
        if(r.quest&&r.quest.id){
          const q=r.quest;
          state.quests.push({id:q.id,title:q.title,description:q.description||'',type:q.type,xp_reward:q.xp,reward:q.reward_data?.label||q.reward||'',progress:0,status:'active'});
          renderQuests();
          const cl=$('#chatLog');
          const qIcon=q.reward_data?.icon||'📜';
          cl.insertAdjacentHTML('beforeend',chatMsg('gm',`<b>WORLDWEAVER</b><div class="chat-line"><em class="chat-action">${qIcon} New Story Quest: "<b>${safe(q.title)}</b>"</em> <span style="color:var(--muted);font-size:10px">Reward: ${safe(q.reward_data?.label||q.reward||'—')}</span></div>`));
          cl.scrollTop=cl.scrollHeight;
        }
      }catch{}
    }
    (async()=>{const _ap=$('.detail-tabs button.active')?.dataset?.panel;if(_ap==='character'||_ap==='inventory'){try{await refreshCharacterState();if(_ap==='inventory')renderInventory();else showPanel('character');}catch{}}})();
  }catch(error){
    const typingEl=document.getElementById(typingId);if(typingEl)typingEl.remove();
    $('#chatLog').insertAdjacentHTML('beforeend',llmErrorBubble(error.message||'The game server could not be reached.',msg));
    $('#aiStatus').textContent='Start LM Studio on port 1234';
  }
  $('#chatLog').scrollTop=$('#chatLog').scrollHeight;
};

// ═══ AI Companion-style workspace navigation and studios ═══
function openView(name){$$('.app-view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.side-nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));document.body.classList.toggle('sidebar-open',name!=='play');if(name==='play'){$('#playHub').hidden=state.hasActiveGame;$('#gameArea').hidden=!state.hasActiveGame;document.body.classList.toggle('game-active',!!state.hasActiveGame)}if(name==='characters')loadCharacterStudio();if(name==='explore')loadExplore();if(name==='worlds')loadWorlds();if(name==='knowledge'){loadLore();loadKnowledgeDocs()}if(name==='media')loadMediaTab();if(name==='settings'){checkModelStatus();loadSettingsExtras()}if(name==='help')loadHelp()}
$$('.side-nav button').forEach(button=>button.onclick=()=>openView(button.dataset.view));

let studioOptions={};
function fillSelect(selector,values){const el=$(selector);if(!el)return;const list=Array.isArray(values)?values:Object.keys(values||{});el.innerHTML=list.map(value=>`<option value="${safe(value)}">${safe(value)}</option>`).join('')}
async function loadCharacterStudio(){try{if(!Object.keys(studioOptions).length){studioOptions=await api('/api/options');initCharFormV6();}const characters=await api('/api/characters');$('#characterLibrary').innerHTML=characters.length?characters.map(c=>{const av=c.photo_path?`<img src="${safe(c.photo_path)}" class="char-avatar-img" alt="portrait">`:`<span class="entity-avatar">${safe((c.name||'?').slice(0,2).toUpperCase())}</span>`;const isActive=String(c.id)===String(state.characterId);return`<article class="entity-card">${av}<div><b>${safe(c.name)}</b><small>${safe(c.gender?c.gender+' · ':'')}${safe(c.race||'Unknown ancestry')} · ${safe(c.profession||'Adventurer')}</small></div><em>LV ${safe(c.level||1)}</em><button data-use-char="${c.id}" class="ghost" style="font-size:9px;padding:3px 8px;${isActive?'color:var(--gold);border-color:var(--gold)':''}">${isActive?'Active':'Use'}</button></article>`}).join(''):'<div class="empty-state">No saved characters yet. Create your first companion.</div>';$$('[data-use-char]').forEach(btn=>btn.onclick=async()=>{const cid=+btn.dataset.useChar;if(state.characterId===cid)return;state.characterId=cid;await refreshCharacterState();renderParty();renderQuests();loadCharacterStudio();toast('Adventurer switched — ready for play')});if(typeof v6LoadSavedChars==='function')v6LoadSavedChars();}catch(error){$('#characterLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#refreshCharacters').onclick=loadCharacterStudio;$('#newCharacterBtn').onclick=()=>{const v6name=$('#characterFormV6')?.elements?.name;if(v6name){v6name.scrollIntoView({behavior:'smooth'});v6name.focus();}};

async function loadWorlds(){try{const items=await api('/api/worlds');$('#worldLibrary').innerHTML=items.length?items.map(w=>`<article class="entity-card"><span class="entity-avatar">◎</span><div><b>${safe(w.name)}</b><small>${safe(w.space_alignment||'multiverse')} · ${safe(w.reality_type||'Prime Reality')} · Magic ${safe(w.ratings?.magic ?? w.magic_level)}</small></div><em>${safe(w.time_of_day||'Active')}</em><span style="display:flex;gap:4px;margin-left:auto"><button class="ghost" data-travel-world="${w.id}" style="font-size:9px;padding:2px 8px">Travel</button><button class="ghost" data-del-world="${w.id}" style="font-size:9px;padding:2px 6px;color:var(--muted)">✕</button></span></article>`).join(''):'<div class="empty-state">No database worlds yet. The four play-map realities remain available.</div>';$$('[data-travel-world]').forEach(btn=>btn.onclick=async()=>{const wid=+btn.dataset.travelWorld;try{const w=await api(`/api/worlds/${wid}`);if(!state.worlds.find(x=>x.id===wid)){const entry=typeof toWorldEntry==='function'?toWorldEntry(w):w;state.worlds.unshift(entry);state.worldIndex=0;}else{state.worldIndex=state.worlds.findIndex(x=>x.id===wid);}updateWorld();setScale('local');toast(`Traveling to ${safe(w.name)}`)}catch(e){toast(e.message)}});$$('[data-del-world]').forEach(btn=>btn.onclick=async()=>{const wid=+btn.dataset.delWorld;if(!confirm('Delete this world?'))return;try{await api(`/api/worlds/${wid}`,{method:'DELETE'});toast('World deleted');loadWorlds();}catch(e){toast(e.message)}});}catch(error){$('#worldLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
$('#worldForm').onsubmit=async event=>{event.preventDefault();const formEl=event.currentTarget;const raw=Object.fromEntries(new FormData(formEl).entries());const payload={name:raw.name,magic:raw.magic,tech:raw.tech,space:raw.space,reality_type:raw.reality_type||'Prime Reality',num_locs:Number(raw.num_locs||8),ratings:{science:Number(raw.ratings_science||5),technology:Number(raw.ratings_technology||4),magic:Number(raw.ratings_magic||5),weapon:Number(raw.ratings_weapon||3),power:Number(raw.ratings_power||5),civilization:Number(raw.ratings_civilization||4),danger:Number(raw.ratings_danger||4),horror:Number(raw.ratings_horror||2)}};try{await api('/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`${payload.name} created`);formEl.reset();loadWorlds()}catch(error){toast(error.message)}};$('#refreshWorlds').onclick=loadWorlds;

async function loadLore(){try{const items=await api('/api/knowledge/lorebook');$('#loreLibrary').innerHTML=items.length?items.map(item=>`<article class="entity-card"><span class="entity-avatar">◇</span><div><b>${safe(item.title)}</b><small>${safe((item.content||'').slice(0,90))}</small></div><span style="display:flex;gap:4px;align-items:center"><em data-lore-toggle="${item.id}" style="cursor:pointer;user-select:none" title="Toggle">${item.enabled===0?'Off':'Active'}</em><button class="ghost" data-lore-del="${item.id}" style="font-size:9px;padding:2px 6px;color:var(--muted)">✕</button></span></article>`).join(''):'<div class="empty-state">No lorebook entries. Add rules, locations, and secrets here.</div>';$$('[data-lore-del]').forEach(btn=>btn.onclick=async()=>{try{await api(`/api/knowledge/lorebook/${btn.dataset.loreDel}`,{method:'DELETE'});loadLore();}catch(e){toast(e.message)}});$$('[data-lore-toggle]').forEach(em=>em.onclick=async()=>{const id=em.dataset.loreToggle;const isActive=em.textContent==='Active';try{await api(`/api/knowledge/lorebook/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:isActive?0:1})});em.textContent=isActive?'Off':'Active';}catch(e){toast(e.message)}});}catch(error){$('#loreLibrary').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
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
 const progressEl=$('#importResult');
 const step=label=>{if(progressEl)progressEl.innerHTML=`<div class="empty-state" style="color:var(--gold)">${safe(label)}</div>`;};
 step('Identifying characters…');
 const inferred=await inferAndImportCharacters(messages);
 step('Importing session history…');
 const {sessionId,count}=await loadMessagesIntoNewSession(messages);
 const characterName=inferred[0]?.name||'';
 step('Saving memory facts…');
 let memoryCount=0;
 if(messages.length)memoryCount=await importMemoryFacts([{fact:`Imported ${messages.length} messages from ${sourceLabel}.`}],characterName);
 step('Done!');
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
 const stopMediaTimer=startGenTimer(preview.firstElementChild,'Generating image');
 try{
  const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:payload.prompt,style:payload.style,save_to_chat:false})}).finally(stopMediaTimer);
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
async function loadBackups(){try{const items=await api('/api/settings/backups');$('#backupList').innerHTML=items.length?items.map(b=>`<article class="entity-card"><span class="entity-avatar">⛁</span><div><b>${safe(b.name||b.path||'Backup')}</b><small>${safe(b.created_at||'')}</small></div><button class="ghost" data-restore-backup="${safe(b.path||b.name||'')}" style="font-size:9px;padding:2px 8px">Restore</button></article>`).join(''):'<div class="empty-state">No backups yet.</div>';$$('[data-restore-backup]').forEach(btn=>btn.onclick=async()=>{const p=btn.dataset.restoreBackup;if(!confirm(`Restore backup "${p}"? This will overwrite current data.`))return;try{await api('/api/settings/restore',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p})});toast('Restore complete — reload to apply changes');}catch(e){toast(e.message)}});}catch(error){$('#backupList').innerHTML=`<div class="empty-state">${safe(error.message)}</div>`}}
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
 const wn=(weaponName||'').toLowerCase();
 if(/bow|crossbow|gun|rifle|pistol|sniper|cannon|musket|blaster|phaser|laser|sling|dart|javelin|thrown|ranged/.test(wn))return 5;
 if(/spear|halberd|lance|pike|glaive|polearm|trident|reach/.test(wn))return 2;
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
  if(state.characterId){refreshCharacterState().then(()=>renderParty()).catch(()=>{});}
  if(won&&reward.xp_awarded){awardXP(reward.xp_awarded,`Combat — Round ${combatState.round_number}`);}
  // Fix #1: persist HP changes from combat
  if(state.characterId&&state.sheet){
   const playerUnit=combatState.units.find(u=>u.stats?.is_human);
   if(playerUnit){
    const {maxHp,maxMana}=derivedResources(state.sheet);
    const hpSt=getHpState(state.characterId,maxHp,maxMana);
    const finalHp=typeof playerUnit.hp==='number'?playerUnit.hp:hpSt.currentHp;
    setHpState(state.characterId,finalHp,hpSt.currentMp,maxHp,maxMana);
    renderParty();
    if($('#detailContent').innerHTML.includes('Health'))showPanel('character');
   }
  }
  // Restore used spell slots that were spent in combat (tracked optimistically)
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

// ── Mobile swipe navigation ──
(function(){
  const VIEWS=['play','characters','explore','worlds','knowledge','media','settings'];
  let _tx=0,_ty=0;
  document.addEventListener('touchstart',e=>{const t=e.changedTouches[0];_tx=t.clientX;_ty=t.clientY;},{passive:true});
  document.addEventListener('touchend',e=>{
    // Ignore if touch started inside a scrollable element or input
    const t=e.changedTouches[0];
    const dx=t.clientX-_tx,dy=t.clientY-_ty;
    if(Math.abs(dx)<60||Math.abs(dx)<Math.abs(dy)*1.5)return;
    const activeBtn=document.querySelector('.side-nav button.active');
    if(!activeBtn)return;
    const cur=activeBtn.dataset.view,idx=VIEWS.indexOf(cur);
    if(idx<0)return;
    const next=dx<0?VIEWS[Math.min(idx+1,VIEWS.length-1)]:VIEWS[Math.max(idx-1,0)];
    if(next!==cur)openView(next);
  },{passive:true});
})();

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
const V6_CHAR_TAGS=["Mom","Daughter","Wife","Girlfriend","Ex-Girlfriend","Sister","Aunt","Cousin","Grandmother","Mother-in-law","Boyfriend","Husband","Father","Brother","Son","Uncle","Grandfather","Fiance(e)","Crush","Secret Admirer","Childhood Friend","Bestie","Best Friend","Rival","Frenemy","Co-worker","Boss","Employee","Neighbour","Roommate","Classmate","Teacher","Student","Mentor","Apprentice","Landlord","Client","Partner","Futa","MILF","DILF","Curvy","Tomboy","Tsundere","Yandere","Kuudere","Dandere","Bad Boy","Bad Girl","Good Girl","Good Boy","Nerd","Jock","Goth","Punk","Teen","Young Adult","Adult","Mature","Elder","Office","School","Fantasy","Sci-Fi","Modern","Historical","Post-Apocalyptic","Supernatural","Mafia","Crime","Mystery","Horror","Romance","Drama","Comedy","Slice of Life","Isekai","Harem","Reverse Harem","Protagonist","Antagonist","Love Interest","Villain","Anti-Hero","Companion","Slave","Master","Servant","Royalty","Commoner","Alien","Robot","Angel","Demon","Vampire","Werewolf","Ghost","Witch","God/Goddess","Love","Jealousy","Betrayal","Loyalty","Revenge","Redemption","Adventure","Survival","Family","Cheater","Innocent","Seductive","Dangerous","Protective","Possessive","Submissive","Dominant","Magic","NSFW","Erotic","Bondage","Sugar Daddy","Sugar Mommy","Forbidden","Taboo","Obsessive","Stalker","Exhibitionist","Voyeur","Step-Mom","Step-Dad","Step-Sister","Step-Brother","Maid","Butler","Nurse","Prisoner","Kidnapper","Arranged Marriage","Fake Dating","Friends to Lovers","Enemies to Lovers","Second Chance","Age Gap","Neko","Kitsune","Alien GF","Starfleet","Jaffa","Custom"];
const V6_BODY_TYPES=["Slim","Athletic","Average","Muscular","Curvy","Voluptuous","Petite","Tall","Short","Stocky","Elegant","Rugged","Thicc","Toned","Hourglass","Pear","Slender","Plus-size","Statuesque","Wiry","Custom"];
const V6_GENDERS=["Male","Female","Non-binary","Futa / Futanari","Androgynous","Gender-fluid","Custom"];
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
  const bonuses=V6_RACE_BONUSES[race]||{};
  const bstat=(k)=>Math.min(20,stat()+(bonuses[k]||0));
  const gCatM=g==='Female'||g==='Futa / Futanari'?'f':g==='Non-binary'||g==='Androgynous'||g==='Gender-fluid'?'n':'m';
  const mRng=(V6_RACE_MEASUREMENTS[race]||V6_RACE_MEASUREMENTS['_default'])[gCatM];
  const mRnd=(lo,hi)=>lo+Math.floor(Math.random()*(hi-lo+1));
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
    bust_chest:`${mRnd(...mRng.bust)}"`,
    waist:`${mRnd(...mRng.waist)}"`,
    hips:`${mRnd(...mRng.hip)}"`,
    languages:['Common'],
    strength:bstat('strength'),dexterity:bstat('dexterity'),intelligence:bstat('intelligence'),wisdom:bstat('wisdom'),constitution:bstat('constitution'),speed:stat(),luck:stat(),charisma_stat:bstat('charisma_stat'),
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

// ═══ Dynamic map: universe nodes, chat-driven locations, scale detection ═══
async function loadUniverseNodes(){
  $('#mapNodes').innerHTML='';
  $('#locationName').textContent='Universe';
  try{
    const [worlds,visitedRows]=await Promise.all([
      api('/api/worlds'),
      state.characterId?api(`/api/worlds/visited?character_id=${state.characterId}`).catch(()=>[]):Promise.resolve([])
    ]);
    const visitedIds=new Set(visitedRows.map(r=>r.world_id));
    // Always mark currently active worlds as visited
    state.worlds.forEach(w=>{if(w.id)visitedIds.add(w.id);});
    state.visitedWorldIds=visitedIds;
    if(!worlds.length){$('#mapNodes').innerHTML='<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:var(--muted);font-size:11px;text-align:center">No saved worlds yet.<br>Create worlds in the World tab.</div>';return;}
    const cols=4;
    $('#mapNodes').innerHTML=worlds.map((w,i)=>{
      const xi=i%cols,yi=Math.floor(i/cols);
      const x=12+xi*22,y=14+yi*26;
      const icon={fantasy:'⚔',sci_fi:'🚀',cyberpunk:'⚡',supernatural:'👁',apocalyptic:'☢',zombie:'🧟',mystery:'🔍',drama:'💔',alien_space:'🛸'}[w.space_alignment]||'🌍';
      const visited=visitedIds.has(w.id);
      const fogStyle=visited?'':'filter:blur(2px);opacity:0.4;border-color:var(--line)';
      const fogTitle=visited?`${safe(w.name)} — ${safe(w.space_alignment||'unknown')} · ${safe(w.reality_type||'Prime')}`:'??? — Undiscovered Realm';
      return `<button class="map-node" style="--x:${x}%;--y:${y}%;border-color:var(--purple);background:#1a103a;font-size:16px;width:42px;height:42px;${fogStyle}" data-uni-world="${w.id}" data-label="${visited?safe(w.name):'???'}" title="${fogTitle}">${visited?icon:'?'}</button>`;
    }).join('');
    $$('#mapNodes [data-uni-world]').forEach(el=>el.onclick=async()=>{
      const wid=parseInt(el.dataset.uniWorld);
      const found=state.worlds.find(w=>w.id===wid);
      if(found){state.worldIndex=state.worlds.indexOf(found);updateWorld();setScale('local');return;}
      try{
        el.style.opacity='0.5';
        const w=await api(`/api/worlds/${wid}`);
        const entry=typeof toWorldEntry==='function'?toWorldEntry(w):w;
        state.worlds.unshift(entry);state.worldIndex=0;
        updateWorld();setScale('local');
        toast(`Traveled to ${safe(w.name)}`);
      }catch(e){toast(e.message);}finally{el.style.opacity='';}
    });
    $('#locationName').textContent=`Universe — ${worlds.length} realm${worlds.length!==1?'s':''}`;
  }catch(err){$('#mapNodes').innerHTML='';}
}

function detectScaleFromChat(text){
  const t=(text||'').toLowerCase();
  if(/\b(universe|multiverse|cosmos|star system|galaxy|dimension|parallel world|alternate (world|reality)|void between worlds|astral plane|realm between|realities|the void)\b/.test(t))return'universe';
  if(/\b(world map|continent|kingdom|nation|empire|federation|world of|across the (land|realm|world|kingdom)|the known world|great war|realm-wide)\b/.test(t))return'continent';
  if(/\b(province|district|county|region|country|neighboring (city|town|village)|surrounding (area|lands?)|travelling (to|towards|through)|journeyed? to|rode (to|through)|arrived at|ventured (to|into)|headed (to|towards))\b/.test(t))return'country';
  return null;
}

async function addLocationsFromChat(text){
  const world=state.worlds[state.worldIndex];
  if(!world||state.scale==='universe')return;
  const existing=new Set(state.locations.map(l=>l.name.toLowerCase()));
  const toAdd=[];let m;
  // *add location: NAME, MAP* explicit command
  const addRe=/\*add\s+location\s*:\s*([^,*\n]+),\s*(local|country|continent|universe)\s*\*/gi;
  while((m=addRe.exec(text))!==null){const n=m[1].trim(),lt=m[2].toLowerCase()==='continent'?'continent':m[2].toLowerCase()==='country'?'country':'local';if(n.length>=2&&n.length<=50&&!existing.has(n.toLowerCase())){toAdd.push({name:n,loc_type:lt,terrain:'Plains'});existing.add(n.toLowerCase());}}
  // Continent level: kingdoms, empires, island chains, etc.
  const cRe=/\b(?:Kingdom|Empire|Republic|Duchy|Federation|Nation|Realm|Dominion|Commonwealth|Sultanate|Territory|Confederation|Principality|Queendom)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})|([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:Kingdom|Empire|Republic|Duchy|Federation|Islands?|Archipelago|Nation|Realm|Territory|Lands|Continent|Peninsula|Steppes|Wastes|Expanse)\b/g;
  while((m=cRe.exec(text))!==null){const n=(m[1]||m[2]||'').trim();if(n.length>=3&&n.length<=40&&!existing.has(n.toLowerCase())){const ct=/island|isle|archipe/i.test(n)?'Ocean':/mount|peak|highland|ridge/i.test(n)?'Mountains':/forest|wood|grove/i.test(n)?'Forest':/desert|arid|waste|sand/i.test(n)?'Desert':/swamp|marsh|bog|fen/i.test(n)?'Wetlands':'Plains';toAdd.push({name:n,loc_type:'continent',terrain:ct});existing.add(n.toLowerCase());}}
  // Country/region level: provinces, districts, counties, valleys, etc.
  const pRe=/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:Province|District|County|Shire|Region|March|Canton|Prefecture|Valley|Pass|Coast|Highlands?|Lowlands?|Borderlands?|Foothills?)\b/g;
  while((m=pRe.exec(text))!==null){const n=m[1].trim();if(n.length>=3&&n.length<=35&&!existing.has(n.toLowerCase())){const pt=/mountain|highland|peak|vale|hill|ridge/i.test(n)?'Mountains':/forest|wood|grove|thicket/i.test(n)?'Forest':/swamp|marsh|bog|fen/i.test(n)?'Wetlands':/coast|bay|shore|sea|port/i.test(n)?'Ocean':/desert|arid|sand/i.test(n)?'Desert':'Plains';toAdd.push({name:n,loc_type:'country',terrain:pt});existing.add(n.toLowerCase());}}
  // Local terrain features: "the Ancient Forest", "Crystal Desert", "Dark Dungeon" etc.
  const terrainWords='forest|jungle|woodland|woods|dungeon|cavern|cave|crypt|tomb|ruins?|ruin|desert|wasteland|badlands|swamp|marsh|bog|mire|fen|island|isle|islet|sea|ocean|lake|river|bay|cove|harbor|harbour|beach|shore|coast|volcano|crater|glacier|tundra|canyon|gorge|cliff|valley|dale|glen|meadow|moor|heath|plain|steppe|mountain|peak|summit|ridge|plateau';
  const terrRe=new RegExp(`\\b(?:the\\s+)?([A-Z][a-z]+(?:\\s+(?:of\\s+the\\s+)?[A-Z][a-z]+)?(?:\\s+[A-Z][a-z]+)?)\\s+(${terrainWords})s?\\b|\\b(${terrainWords})s?\\s+of\\s+([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)?)\\b`,'gi');
  while((m=terrRe.exec(text))!==null){
    const raw=m[1]?`${m[1]} ${m[2]}`:`${m[4]} ${m[3]}`;
    const n=raw.replace(/^(the|a|an)\s+/i,'').trim();
    if(n.length>=4&&n.length<=45&&!existing.has(n.toLowerCase())){
      const lc=n.toLowerCase();
      const terr=/forest|jungle|wood|grove/i.test(lc)?'Forest':/dungeon|cave|cavern|crypt|tomb|underground/i.test(lc)?'Underground':/ruins?/i.test(lc)?'Ruins':/desert|waste|badland/i.test(lc)?'Desert':/swamp|marsh|bog|mire|fen/i.test(lc)?'Wetlands':/island|isle|sea|ocean|bay|cove|harbor|beach|shore|coast/i.test(lc)?'Ocean':/volcano|crater/i.test(lc)?'Volcano':/glacier|tundra/i.test(lc)?'Tundra':/mountain|peak|summit|ridge|cliff|canyon/i.test(lc)?'Mountains':/valley|dale|glen|meadow|moor|plain/i.test(lc)?'Plains':'Plains';
      const lt=state.scale==='continent'?'continent':state.scale==='country'?'country':'local';
      toAdd.push({name:n,loc_type:lt,terrain:terr});existing.add(lc);
    }
  }
  // Local/building level: "X Tavern", "X Castle", "X Library" etc.
  const lRe=/\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:district|village|hamlet|town|city|temple|shrine|altar|castle|ruins|cave|dungeon|tavern|market|inn|pub|port|keep|tower|manor|gate|bridge|outpost|citadel|settlement|encampment|camp|hall|arena|palace|sanctuary|spire|grove|crossing|waypoint|fortress|barracks|library|academy|school|cafe|restaurant|shop|office|garden|beach|hotel|dojo|gym|hospital|workshop|barn|stable|dormitory|dorm|lighthouse|lighthouse|pier|dock|mill|forge|blacksmith|bakery|cathedral|chapel|monastery|abbey|cloister|graveyard|cemetery|necropolis|vault|catacombs?|labyrinth|maze|colosseum|amphitheater|bazaar|souq|emporium)\b/gi;
  while((m=lRe.exec(text))!==null){const n=m[1].trim();if(n.length>=3&&n.length<=35&&!existing.has(n.toLowerCase())){toAdd.push({name:n,loc_type:'local',terrain:'City'});existing.add(n.toLowerCase());}}
  const deduped=toAdd.slice(0,6);
  if(!deduped.length)return;
  for(const entry of deduped){
    const lc=(entry.name+' '+entry.terrain).toLowerCase();
    const t=entry.terrain!=='Plains'?entry.terrain:entry.loc_type==='local'?(/forest|grove|jungle/i.test(lc)?'Forest':/cave|dungeon|crypt|underground/i.test(lc)?'Underground':/ruins?/i.test(lc)?'Ruins':/port|sea|ocean|bay|harbor|beach/i.test(lc)?'Ocean':'City'):(/forest|wood/i.test(lc)?'Forest':/mountain|peak|highland/i.test(lc)?'Mountains':/desert|arid/i.test(lc)?'Desert':/swamp|marsh/i.test(lc)?'Wetlands':/coast|sea|ocean/i.test(lc)?'Ocean':'Plains');
    const x=15+Math.random()*70,y=15+Math.random()*70;
    try{
      const loc=await api(`/api/worlds/${world.id}/locations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:entry.name,terrain:t,x,y,description:'Mentioned in story',loc_type:entry.loc_type})});
      if(loc&&loc.id){
        state.locations.push(loc);
        const mapLabel={local:'Local',country:'Country',continent:'Continent'}[entry.loc_type]||entry.loc_type;
        toast(`📍 ${entry.name} → ${mapLabel} map`);
        _genLocationThumbnail(loc,world,t).catch(()=>{});
      }
    }catch{}
  }
  renderMapNodes();
}

// ═══ Random location generator ═══
async function generateMapLocations(scale){
  const world=state.worlds[state.worldIndex];
  if(!world){toast('No world selected');return;}
  const existing=new Set(state.locations.filter(l=>(l.loc_type||'local')===scale||(scale==='local'&&!l.loc_type)).map(l=>l.name.toLowerCase()));
  // Word banks per scale
  const ADJ_FANTASY=['Ancient','Broken','Crystal','Cursed','Dark','Dead','Dread','Ember','Eternal','Fading','Fallen','Forsaken','Frozen','Ghost','Golden','Hidden','Hollow','Iron','Jade','Lost','Mystic','Obsidian','Sacred','Shadow','Silver','Silent','Shattered','Sunken','Twilight','Wandering','Whispering','Wild','Withered','Wraithborn'];
  const ADJ_NATURE=['Ash','Birch','Blackwood','Briar','Cedar','Crimson','Dusty','Fernwood','Grey','Misty','Mossy','Muddy','Oak','Pine','Red','Rocky','Rusty','Sandy','Scarlet','Stony','Verdant','Vine','Willowy'];
  function pick(arr){return arr[Math.floor(Math.random()*arr.length)];}
  function adjName(){return Math.random()<0.6?pick(ADJ_FANTASY)+' ':pick(ADJ_NATURE)+' ';}
  const localTemplates=[
    ()=>({name:adjName()+pick(['Dungeon','Catacombs','Vault','Crypt','Tomb']),terrain:'Underground'}),
    ()=>({name:adjName()+pick(['Forest','Grove','Jungle','Thicket','Woodland']),terrain:'Forest'}),
    ()=>({name:adjName()+pick(['Village','Hamlet','Settlement','Outpost']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Ruins','Keep','Citadel','Fortress','Watchtower']),terrain:'Ruins'}),
    ()=>({name:adjName()+pick(['Desert','Dunes','Wasteland','Badlands','Sands']),terrain:'Desert'}),
    ()=>({name:pick(['Sea of','Bay of','Cove of','Isle of','Shores of'])+' '+pick(['Storms','Silence','Shadows','Echoes','Fate','Mist','Sorrow','Whispers']),terrain:'Ocean'}),
    ()=>({name:adjName()+pick(['Island','Islet','Atoll']),terrain:'Ocean'}),
    ()=>({name:adjName()+pick(['Swamp','Marshland','Bog','Mire','Fens']),terrain:'Wetlands'}),
    ()=>({name:adjName()+pick(['Peak','Summit','Ridge','Cliffs','Highlands']),terrain:'Mountains'}),
    ()=>({name:adjName()+pick(['Shrine','Temple','Altar','Sanctum','Chapel']),terrain:'City'}),
    ()=>({name:adjName()+pick(['Tavern','Inn','Hall','Market','Bazaar']),terrain:'City'}),
    ()=>({name:adjName()+pick(['Cave','Cavern','Grotto','Hollow']),terrain:'Underground'}),
    ()=>({name:adjName()+pick(['Tower','Spire','Lighthouse','Beacon']),terrain:'Ruins'}),
    ()=>({name:adjName()+pick(['Valley','Dale','Glen','Ravine']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Volcano','Crater','Caldera']),terrain:'Volcano'}),
    ()=>({name:adjName()+pick(['Glacier','Icefield','Tundra','Frostlands']),terrain:'Tundra'}),
    ()=>({name:adjName()+pick(['Graveyard','Cemetery','Necropolis']),terrain:'Ruins'}),
    ()=>({name:adjName()+pick(['Port','Harbor','Docks','Wharf']),terrain:'Ocean'}),
  ];
  const countryTemplates=[
    ()=>({name:adjName()+pick(['Valley','Vale','Dale','Basin','Glen']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Forest','Woodlands','Greenwood','Wildwood']),terrain:'Forest'}),
    ()=>({name:adjName()+pick(['Highlands','Mountains','Range','Peaks']),terrain:'Mountains'}),
    ()=>({name:adjName()+pick(['Coast','Shores','Seaboard','Strand']),terrain:'Ocean'}),
    ()=>({name:adjName()+pick(['Desert','Wastelands','Barrens','Dunes']),terrain:'Desert'}),
    ()=>({name:adjName()+pick(['Marshes','Wetlands','Fens','Moors']),terrain:'Wetlands'}),
    ()=>({name:adjName()+pick(['Province','County','Shire','District','Region']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Borderlands','Marches','Frontier','Outlands']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Foothills','Lowlands','Flats','Plains']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Archipelago','Islands','Isle Chain']),terrain:'Ocean'}),
  ];
  const continentTemplates=[
    ()=>({name:adjName()+pick(['Kingdom','Realm','Dominion','Sovereignty']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Empire','Imperium','Confederation','Federation']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Republic','Nation','Commonwealth','Alliance']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Lands','Territories','Wilds','Expanse']),terrain:'Plains'}),
    ()=>({name:pick(['The','Great','Grand'])+' '+pick(['Desert','Sea','Ocean','Forest','Steppe','Tundra','Glacier','Void','Abyss','Rift']),terrain:'Desert'}),
    ()=>({name:adjName()+pick(['Continent','Peninsula','Subcontinent','Landmass']),terrain:'Plains'}),
    ()=>({name:adjName()+pick(['Archipelago','Island Chain','Sea Islands']),terrain:'Ocean'}),
    ()=>({name:adjName()+pick(['Wastes','Barrens','Desolation','Expanse']),terrain:'Desert'}),
  ];
  const templates=scale==='continent'?continentTemplates:scale==='country'?countryTemplates:localTemplates;
  const count=scale==='continent'?5:scale==='country'?6:8;
  const toAdd=[];
  let tries=0;
  while(toAdd.length<count&&tries<count*5){
    tries++;
    const tpl=templates[Math.floor(Math.random()*templates.length)];
    const entry=tpl();
    if(!existing.has(entry.name.toLowerCase())){toAdd.push({...entry,loc_type:scale});existing.add(entry.name.toLowerCase());}
  }
  if(!toAdd.length){toast('No new locations to add');return;}
  toast(`Generating ${toAdd.length} locations…`);
  let added=0;
  for(let i=0;i<toAdd.length;i++){
    const entry=toAdd[i];
    const angle=(i/toAdd.length)*2*Math.PI;
    const r=15+Math.random()*50;
    const x=Math.max(8,Math.min(92,Math.round(50+r*Math.cos(angle))));
    const y=Math.max(8,Math.min(92,Math.round(50+r*Math.sin(angle))));
    try{
      const loc=await api(`/api/worlds/${world.id}/locations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:entry.name,terrain:entry.terrain,x,y,description:`Generated ${scale} location`,loc_type:scale})});
      if(loc&&loc.id){state.locations.push(loc);added++;_genLocationThumbnail(loc,world,entry.terrain).catch(()=>{});}
    }catch{}
  }
  renderMapNodes();
  if(added)toast(`✦ ${added} locations added to ${scale} map`);
}

// ═══ Seed Local map from scenario backstory ═══
// Called once when a new game starts with no existing local locations.
// Extracts building/place names from opening text and adds them to the Local map.
async function seedLocalFromBackstory(text){
  const world=state.worlds[state.worldIndex];
  if(!world||!text)return;
  const existing=new Set(state.locations.map(l=>l.name.toLowerCase()));
  const BT='home|house|manor|mansion|penthouse|office|shop|store|market|cafe|restaurant|tavern|inn|pub|bar|academy|school|library|dungeon|cave|garden|palace|temple|church|castle|fortress|tower|beach|hotel|arena|dojo|gym|barn|port|hallway|hall|courtyard|grove|jungle|forest|warehouse|vault|clinic|hospital|workshop|laboratory|lab|dormitory|dorm|bedroom|kitchen|ballroom|plaza';
  const toSeed=[];let m;
  // Pattern: "[the] CapName BuildingType"
  const re1=new RegExp(`\\b(?:the\\s+)?([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)?)\\s+(${BT})\\b`,'g');
  while((m=re1.exec(text))!==null){
    const name=(m[1]+' '+m[2]).replace(/^the\s+/i,'').trim();
    if(name.length>=4&&name.length<=50&&!existing.has(name.toLowerCase())){toSeed.push(name);existing.add(name.toLowerCase());}
  }
  // Pattern: "BuildingType of [the] CapName"
  const re2=new RegExp(`\\b(${BT})\\s+of\\s+(?:the\\s+)?([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)?)\\b`,'g');
  while((m=re2.exec(text))!==null){
    const name=(m[2]+' '+m[1]).trim();
    if(name.length>=4&&name.length<=50&&!existing.has(name.toLowerCase())){toSeed.push(name);existing.add(name.toLowerCase());}
  }
  const limited=toSeed.slice(0,8);
  if(!limited.length)return;
  for(let i=0;i<limited.length;i++){
    const name=limited[i];
    const angle=(i/limited.length)*2*Math.PI;
    const r=22+Math.random()*28;
    const x=Math.max(10,Math.min(90,Math.round(50+r*Math.cos(angle))));
    const y=Math.max(10,Math.min(90,Math.round(50+r*Math.sin(angle))));
    try{
      const loc=await api(`/api/worlds/${world.id}/locations`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,terrain:'City',x,y,description:'Location from scenario backstory',loc_type:'local'})});
      if(loc&&loc.id)state.locations.push(loc);
    }catch{}
  }
  renderMapNodes();
  if(limited.length)toast(`📍 ${limited.length} locations seeded from backstory`);
}

async function _genLocationThumbnail(loc,world,terrain){
  if(state.locationImageCache[loc.id])return;
  _enqueueThumb(async()=>{
    if(state.locationImageCache[loc.id])return; // double-check after queue wait
    try{
      const prompt=`Fantasy landscape: ${loc.name}, ${terrain} terrain, ${world?.name||'fantasy world'} setting. Scenic vista, atmospheric, painterly.`;
      const result=await api('/api/media/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,style:'Fantasy Art',width:256,height:144,cache_key:`loc:${world?.id||0}:${loc.id}:thumb`})});
      if(result.url){
        state.locationImageCache[loc.id]=result.url;
        _saveImgCache(state.locationImageCache);
        // Refresh map node thumbnail if still visible
        const node=document.querySelector(`[data-loc-id="${loc.id}"] .node-thumb`);
        if(node){node.style.backgroundImage=`url('${result.url}')`;node.style.backgroundSize='cover';}
      }
    }catch{}
  });
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
  // Set initial measurement ranges and language order for default race/gender
  setTimeout(()=>{v6UpdateMeasurementRanges();v6UpdateRaceLanguages();},0);
  // Live measurement validation on input
  ['v6bust','v6waist','v6hips'].forEach(id=>{
    const inp=$('#'+id);
    if(inp)inp.addEventListener('input',()=>v6UpdateMeasurementRanges());
  });
  fillV6Sel('#v6weaponSelect',V6_WEAPON_TYPES);
  fillV6Sel('#v6magicSelect',V6_MAGIC_TYPES);
  fillV6Sel('#v6powerSelect',V6_POWER_SYSTEMS);
  fillV6Sel('#v6emotionSelect',V6_EMOTION_STYLES);
  fillV6Sel('#v6traitsSelect',V6_TRAITS_LIST);
  fillV6Sel('#v6quirksSelect',V6_QUIRKS_LIST);
  fillV6Sel('#v6skillsSelect',V6_SKILLS_LIST);
  fillV6Sel('#v6tagsSelect',V6_CHAR_TAGS);
  fillV6Sel('#v6sharedTags',V6_CHAR_TAGS);
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
  const multiKeys=['weapon_training','magic_type','power_system','abilities','traits','quirks','emotion_styles','languages','skills','tags'];
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

// v6 random measurements (race/gender-aware)
const _v6rm=$('#v6randMeasure');
if(_v6rm)_v6rm.onclick=()=>{
  const raceEl=$('#v6raceSelect');const race=raceEl?raceEl.value:'Human';
  const form=$('#characterFormV6');const gVal=form?form.elements['gender']?.value:'';
  const gCat=gVal==='Female'||gVal==='Futa / Futanari'?'f':gVal==='Non-binary'||gVal==='Androgynous'||gVal==='Gender-fluid'?'n':'m';
  const ranges=(V6_RACE_MEASUREMENTS[race]||V6_RACE_MEASUREMENTS['_default'])[gCat];
  const rnd=(lo,hi)=>lo+Math.floor(Math.random()*(hi-lo+1));
  const b=$('#v6bust'),w=$('#v6waist'),h=$('#v6hips');
  if(b)b.value=`${rnd(...ranges.bust)}"`;
  if(w)w.value=`${rnd(...ranges.waist)}"`;
  if(h)h.value=`${rnd(...ranges.hip)}"`;
};

// v6 random backstory/scenario/goals
async function v6RandPrompts(){
  const form=$('#characterFormV6');if(!form)return{};
  const race=(form.elements['race']||{}).value||'Human';
  const prof=(form.elements['profession']||{}).value||'Adventurer';
  try{return await api(`/api/random/prompts?race=${encodeURIComponent(race)}&profession=${encodeURIComponent(prof)}`);}
  catch{return{};}
}
const _v6rb=$('#v6randBackstory');
if(_v6rb)_v6rb.onclick=async()=>{const r=await v6RandPrompts();const el=$('#characterFormV6')?.elements['backstory'];if(el&&r.backstory)el.value=r.backstory;};
const _v6rs2=$('#v6randScenario');
if(_v6rs2)_v6rs2.onclick=async()=>{const r=await v6RandPrompts();const el=$('#characterFormV6')?.elements['scenario'];if(el&&r.scenario)el.value=r.scenario;};
const _v6rg2=$('#v6randGoals');
if(_v6rg2)_v6rg2.onclick=async()=>{const r=await v6RandPrompts();const el=$('#characterFormV6')?.elements['goals'];if(el&&r.goals)el.value=r.goals;};

// v6 multi-character generation
let _v6multiChars=[];
const _v6gen=$('#v6genGroup');
if(_v6gen)_v6gen.onclick=()=>{
  if(!Object.keys(studioOptions).length){toast('Loading options…');return;}
  const num=Math.min(10,Math.max(2,Number($('#v6multiNum').value)||3));
  const group=$('#v6groupName')?.value||'The Party';
  const sharedTagEl=$('#v6sharedTags');
  const sharedTags=sharedTagEl?Array.from(sharedTagEl.selectedOptions).map(o=>o.value):[];
  _v6multiChars=Array.from({length:num},()=>{
    const ch=v6BuildRandom();
    ch.scenario=`Member of: ${group}`;
    if(sharedTags.length)ch.tags=[...new Set([...(ch.tags||[]),...sharedTags])];
    return ch;
  });
  const res=$('#v6multiResults');
  if(!res)return;
  res.innerHTML=_v6multiChars.map((ch,i)=>`
    <div class="v6-multi-card" id="mc-card-${i}">
      <div style="display:flex;align-items:center;justify-content:space-between;cursor:pointer;padding:4px 0" onclick="document.getElementById('mc-edit-${i}').hidden=!document.getElementById('mc-edit-${i}').hidden;this.querySelector('.mc-toggle').textContent=document.getElementById('mc-edit-${i}').hidden?'▶ Edit':'▼ Collapse'">
        <h4 style="margin:0;font-size:12px">${i+1}. ${safe(ch.name)} <span style="color:var(--muted);font-weight:normal">— ${safe(ch.race)} ${safe(ch.gender)}, ${safe(ch.profession)}</span></h4>
        <span class="mc-toggle" style="font-size:10px;color:var(--gold)">▶ Edit</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px;color:var(--muted);margin-bottom:6px">
        <span>Age: ${ch.age} &nbsp;|&nbsp; ${safe(ch.alignment)}</span><span>Body: ${safe(ch.body_type)} ${safe(ch.height)}</span>
        <span>STR ${ch.strength} DEX ${ch.dexterity} INT ${ch.intelligence}</span>
        <span>WIS ${ch.wisdom} CON ${ch.constitution} CHA ${ch.charisma_stat}</span>
        <span>⚔ ${(ch.weapon_training||[]).join(', ')||'—'}</span>
        <span>✨ ${(ch.magic_type||[]).join(', ')||'—'}</span>
      </div>
      <div id="mc-edit-${i}" hidden style="border-top:1px solid var(--line);padding-top:8px;display:grid;gap:6px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
          <label style="font-size:10px">Name<input class="mc-f" data-i="${i}" data-k="name" value="${safe(ch.name)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Age<input type="number" class="mc-f" data-i="${i}" data-k="age" value="${ch.age}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Gender<input class="mc-f" data-i="${i}" data-k="gender" value="${safe(ch.gender)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Race<input class="mc-f" data-i="${i}" data-k="race" value="${safe(ch.race)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Profession<input class="mc-f" data-i="${i}" data-k="profession" value="${safe(ch.profession)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Alignment<input class="mc-f" data-i="${i}" data-k="alignment" value="${safe(ch.alignment)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Body Type<input class="mc-f" data-i="${i}" data-k="body_type" value="${safe(ch.body_type)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Height<input class="mc-f" data-i="${i}" data-k="height" value="${safe(ch.height)}" style="width:100%;margin-top:2px"></label>
          <label style="font-size:10px">Looks (1-10)<input type="number" min="1" max="10" class="mc-f" data-i="${i}" data-k="looks" value="${ch.looks}" style="width:100%;margin-top:2px"></label>
        </div>
        <label style="font-size:10px">Backstory<textarea class="mc-f" data-i="${i}" data-k="backstory" rows="2" style="width:100%;resize:vertical;margin-top:2px">${safe(ch.backstory||'')}</textarea></label>
        <label style="font-size:10px">Tags (comma-separated)<input class="mc-f" data-i="${i}" data-k="tags_raw" value="${(ch.tags||[]).join(', ')}" style="width:100%;margin-top:2px"></label>
      </div>
    </div>
  `).join('');
  // Live-edit event delegation
  res.oninput=e=>{
    const el=e.target.closest('.mc-f');if(!el)return;
    const i=Number(el.dataset.i),k=el.dataset.k;
    if(!_v6multiChars[i])return;
    if(k==='tags_raw')_v6multiChars[i].tags=el.value.split(',').map(s=>s.trim()).filter(Boolean);
    else if(k==='age'||k==='looks')_v6multiChars[i][k]=Number(el.value);
    else _v6multiChars[i][k]=el.value;
  };
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

// ═══ AiChat Pro — Preset Source, Race Info, Photo, Import/Export, Saved Chars ═══
const V6_PRESET_SOURCES=["All (Combined)","D&D 5e (Standard)","Fairy Tail","One Piece","Naruto","Bleach","Soul Land","Dragon Ball","Jujutsu Kaisen","Demon Slayer","Hunter x Hunter","Mass Effect","Baldur's Gate 3","DC Comics","Marvel Comics","Elder Scrolls","Witcher","Star Trek","Stargate","Babylon 5","Custom (No Preset)"];
const V6_PRESETS={
  "Fairy Tail":{races:["Human","Exceed","Demon","Dragon"],eye_colors:["Brown","Blue","Green","Red","Gold","Scarlet"],hair_colors:["Pink","Blonde","Scarlet Red","Blue","White","Black","Silver"],traits:["Dragon Slayer","Celestial Mage","Requip Master","S-Class Mage"],abilities:["Fire Dragon Slayer","Ice Make","Requip","Celestial Spirit Magic","Dragon Force","Fairy Law"],backgrounds:["Fairy Tail Guild","Sabertooth","Lamia Scale"]},
  "One Piece":{races:["Human","Fishman","Giant","Mink","Cyborg"],eye_colors:["Black","Brown","Blue","Red","Gold"],hair_colors:["Black","Green","Blonde","Orange","Blue","Pink","White"],traits:["Haki User","Devil Fruit User","Swordsman","Navigator"],abilities:["Observation Haki","Armament Haki","Conqueror's Haki","Gear Fifth"],backgrounds:["Pirate Crew","Marine","Revolutionary Army"]},
  "Naruto":{races:["Human","Otsutsuki","Jinchuriki"],eye_colors:["Black","Blue","Green","Red (Sharingan)","White (Byakugan)","Purple (Rinnegan)"],hair_colors:["Blonde","Black","Pink","Red","White","Silver"],traits:["Ninjutsu Master","Taijutsu Expert","Sage","Jinchuriki"],abilities:["Rasengan","Chidori","Shadow Clone","Sharingan","Sage Mode","Susanoo"],backgrounds:["Hidden Leaf","Akatsuki","Hidden Sand"]},
  "Bleach":{races:["Human","Shinigami","Hollow","Arrancar","Quincy"],eye_colors:["Brown","Blue","Green","Gold","Red"],hair_colors:["Orange","Black","White","Red","Blue","Silver"],traits:["Zanpakuto Wielder","Kido Master","Captain-class"],abilities:["Shikai","Bankai","Cero","Flash Step","Getsuga Tensho"],backgrounds:["Soul Society","Hueco Mundo","Wandenreich"]},
  "Dragon Ball":{races:["Human","Saiyan","Namekian","Android","Majin"],eye_colors:["Black","Blue","Green","Red"],hair_colors:["Black","Gold","Blue","Silver","White"],traits:["Super Saiyan","Ultra Instinct","Ki Master"],abilities:["Kamehameha","Spirit Bomb","Instant Transmission","Fusion Dance"],backgrounds:["Z-Fighters","Frieza Force","Capsule Corp"]},
  "Jujutsu Kaisen":{races:["Human","Cursed Spirit","Special Grade"],eye_colors:["Black","Blue","Purple","Red"],hair_colors:["Black","White","Pink","Silver","Orange"],traits:["Sorcerer","Domain Expansion User","Six Eyes"],abilities:["Domain Expansion","Infinity","Ten Shadows","Black Flash"],backgrounds:["Jujutsu High","Gojo Clan","Zen'in Clan"]},
  "Demon Slayer":{races:["Human","Demon","Upper Moon"],eye_colors:["Brown","Red","Blue","Purple","Gold"],hair_colors:["Black","Red","Yellow","Pink","White","Blue"],traits:["Breath User","Hashira","Mark Bearer"],abilities:["Water Breathing","Thunder Breathing","Flame Breathing","Sun Breathing"],backgrounds:["Demon Slayer Corps","Hashira","Upper Moons"]},
  "Soul Land":{races:["Human","Spirit Beast","God Realm Being"],eye_colors:["Blue","Gold","Purple","Red","Silver"],hair_colors:["Black","Blue","Silver","White","Purple","Gold"],traits:["Spirit Master","Titled Douluo","Twin Spirit User"],abilities:["Spirit Ring Absorption","Twin Spirits","Domain Expansion","Clear Sky Hammer"],backgrounds:["Shrek Academy","Spirit Hall","Tang Sect"]},
  "Hunter x Hunter":{races:["Human","Chimera Ant"],eye_colors:["Brown","Red","Blue","Green","Gold"],hair_colors:["Black","White","Silver","Green","Blonde"],traits:["Hunter","Nen User","Enhancer","Specialist"],abilities:["Nen","Jajanken","Bungee Gum","Godspeed"],backgrounds:["Hunter Association","Phantom Troupe","Zoldyck Family"]},
  "Mass Effect":{races:["Human","Asari","Turian","Salarian","Krogan","Quarian","Drell"],eye_colors:["Brown","Blue","Green","Glowing"],hair_colors:["Black","Brown","Blonde","Red","Bald"],traits:["Biotic","Tech Specialist","Soldier","Vanguard"],abilities:["Singularity","Charge","Overload","Tactical Cloak","Nova"],backgrounds:["Alliance Navy","Spectre","Cerberus","N7"]},
  "Baldur's Gate 3":{races:["Human","Elf","Dwarf","Halfling","Gnome","Half-Elf","Half-Orc","Tiefling","Dragonborn","Githyanki","Drow"],eye_colors:["Brown","Blue","Green","Gold","Red","Violet"],hair_colors:["Black","Brown","Blonde","White","Silver","Red"],traits:["Fighter","Wizard","Rogue","Cleric","Warlock","Paladin","Bard","Druid","Monk"],abilities:["Action Surge","Eldritch Blast","Sneak Attack","Divine Smite","Wild Shape","Rage"],backgrounds:["Noble","Soldier","Sage","Criminal","Folk Hero","Urchin"]},
  "DC Comics":{races:["Human","Kryptonian","Amazonian","Atlantean","Martian","Metahuman"],eye_colors:["Blue","Brown","Green","Red","Glowing"],hair_colors:["Black","Brown","Blonde","Red","White"],traits:["Super Strength","Flight","Speed Force","Magic User"],abilities:["Heat Vision","Super Speed","Power Ring","Lasso of Truth"],backgrounds:["Justice League","Gotham","Themyscira"]},
  "Marvel Comics":{races:["Human","Mutant","Inhuman","Asgardian","Eternal","Symbiote Host"],eye_colors:["Blue","Brown","Green","Red","Gold"],hair_colors:["Brown","Black","Blonde","Red","White","Silver"],traits:["Super Soldier","Mutant","Sorcerer","Cosmic Being"],abilities:["Adamantium Claws","Repulsor Beams","Mjolnir","Web-Slinging","Telepathy"],backgrounds:["Avengers","X-Men","S.H.I.E.L.D.","Wakanda"]},
  "Elder Scrolls":{races:["Nord","Imperial","Breton","Redguard","Dunmer","Altmer","Bosmer","Orc","Khajiit","Argonian"],eye_colors:["Blue","Brown","Green","Red","Gold","Yellow"],hair_colors:["Blonde","Brown","Black","Red","White","Grey"],traits:["Dragonborn","Warrior","Mage","Thief","Assassin"],abilities:["Thu'um","Destruction Magic","Restoration","Conjuration","Enchanting"],backgrounds:["Companions","Thieves Guild","Dark Brotherhood","College of Winterhold"]},
  "Witcher":{races:["Human","Elf","Dwarf","Witcher (mutated)","Sorceress"],eye_colors:["Yellow (cat)","Blue","Green","Brown","Violet"],hair_colors:["White","Black","Red","Brown","Blonde"],traits:["Witcher Senses","Sign Caster","Swordmaster","Monster Hunter"],abilities:["Igni","Aard","Quen","Yrden","Axii"],backgrounds:["School of Wolf","School of Cat","Lodge of Sorceresses","Nilfgaard"]},
  "Star Trek":{races:["Human","Vulcan","Klingon","Romulan","Andorian","Betazoid","Trill","Bajoran","Cardassian","Ferengi","Orion","Borg Drone"],eye_colors:["Brown","Blue","Green","Black","All-black","Cybernetic"],hair_colors:["Black","Brown","Blonde","Bald","White","Silver"],traits:["Logical","Warrior","Telepathic","Cunning","Cybernetic"],abilities:["Mind Meld","Nerve Pinch","Bat'leth Mastery","Telepathy","Assimilation"],backgrounds:["Starfleet","Klingon Empire","Romulan Senate","Borg Collective","Bajoran Militia"]},
  "Stargate":{races:["Tau'ri (Human)","Jaffa","Tok'ra","Goa'uld Host","Wraith","Ancient (Alteran)","Asgard (SG)","Athosian"],eye_colors:["Brown","Blue","Green","Glowing gold","Yellow slit"],hair_colors:["Brown","Black","Blonde","Bald","White","Silver"],traits:["Warrior","Ancient Gene Carrier","Tok'ra Blended","Wraith Hybrid"],abilities:["Staff Weapon Mastery","Zat'nik'tel","Healing Device","Ancient Tech","Life Draining"],backgrounds:["SGC (Earth)","Free Jaffa Nation","Tok'ra Council","Atlantis Expedition","Wraith Hive"]},
  "Babylon 5":{races:["Human","Minbari","Narn","Centauri (B5)","Vorlon","Drazi","Shadow Agent"],eye_colors:["Brown","Blue","Grey","Red","Dark","Glowing"],hair_colors:["Brown","Black","Blonde","None","Fan-shaped"],traits:["Ranger","Telepath","Warrior Caste","Religious Caste"],abilities:["Pike Fighting","Telepathy","Vorlon Enhancement","Shadow Technology"],backgrounds:["Earth Alliance","Minbari Federation","Narn Regime","Centauri Republic","Rangers","Psi Corps"]}
};
const V6_IMAGE_STYLES=["Realistic Photo","Fantasy Art","Anime","3D Render","Sci-Fi","Cartoon","Oil Painting","Watercolour","Pixel Art","Comic Book","Cyberpunk","Steampunk","Dark Fantasy","Studio Portrait","Cinematic","Manga","Chibi","Concept Art","Gothic","Pin-Up","Noir","Boudoir","NSFW Art","Furry Art","Custom"];
const V6_DND_RACE_INFO={
  "Human":{lore:"Versatile and adaptable, the most common race.",height:'5\'6"–6\'2"',speed:30,size:"Medium",languages:["Common"]},
  "Elf":{lore:"Ancient, graceful folk with keen senses and long memories.",height:'5\'4"–6\'0"',speed:30,size:"Medium",languages:["Common","Elvish"]},
  "High Elf":{lore:"Supremely intelligent elves with innate magical gifts.",height:'5\'4"–6\'0"',speed:30,size:"Medium",languages:["Common","Elvish"]},
  "Wood Elf":{lore:"Fleet-footed forest-dwellers with preternatural stealth.",height:'5\'4"–6\'0"',speed:35,size:"Medium",languages:["Common","Elvish"]},
  "Drow":{lore:"Subterranean elves shrouded in shadow and dark magic.",height:'5\'2"–5\'10"',speed:30,size:"Medium",languages:["Common","Elvish","Undercommon"]},
  "Dwarf":{lore:"Stout and resilient, masters of stone and metal craft.",height:'4\'4"–4\'10"',speed:25,size:"Medium",languages:["Common","Dwarvish"]},
  "Halfling":{lore:"Small, nimble folk with remarkable luck and cheer.",height:'2\'9"–3\'1"',speed:25,size:"Small",languages:["Common","Halfling"]},
  "Gnome":{lore:"Clever, curious inventors with a knack for illusion.",height:'3\'0"–3\'6"',speed:25,size:"Small",languages:["Common","Gnomish"]},
  "Half-Elf":{lore:"Born between two worlds, naturally charismatic.",height:'5\'2"–6\'0"',speed:30,size:"Medium",languages:["Common","Elvish","one extra"]},
  "Half-Orc":{lore:"Fierce and enduring, with savage strength.",height:'5\'10"–6\'4"',speed:30,size:"Medium",languages:["Common","Orc"]},
  "Tiefling":{lore:"Infernal heritage grants dark powers and striking looks.",height:'5\'6"–6\'0"',speed:30,size:"Medium",languages:["Common","Infernal"]},
  "Aasimar":{lore:"Touched by celestial power and divine radiance.",height:'5\'6"–6\'2"',speed:30,size:"Medium",languages:["Common","Celestial"]},
  "Dragonborn":{lore:"Descendants of dragons with draconic breath weapons.",height:'6\'0"–6\'8"',speed:30,size:"Medium",languages:["Common","Draconic"]},
  "Goliath":{lore:"Mountain-born titans of prodigious strength.",height:'7\'0"–8\'0"',speed:30,size:"Medium",languages:["Common","Giant"]},
  "Tabaxi":{lore:"Cat-folk from distant jungles, driven by curiosity.",height:'5\'8"–6\'2"',speed:30,size:"Medium",languages:["Common"]},
  "Warforged":{lore:"Living constructs forged for war, seeking purpose.",height:'5\'10"–6\'6"',speed:30,size:"Medium",languages:["Common"]},
  "Changeling":{lore:"Shapeshifters of mercurial nature and fluid identity.",height:'5\'6"–6\'0"',speed:30,size:"Medium",languages:["Common"]},
  "Firbolg":{lore:"Giant-kin who dwell peacefully in forest depths.",height:'7\'0"–8\'0"',speed:30,size:"Medium",languages:["Common","Elvish","Giant"]},
  "Genasi":{lore:"Mortals with an elemental spirit—fire, water, earth, or air.",height:'5\'4"–6\'2"',speed:30,size:"Medium",languages:["Common","Primordial"]},
  "Lizardfolk":{lore:"Cold-blooded reptilians guided by practicality and survival.",height:'5\'8"–6\'2"',speed:30,size:"Medium",languages:["Common","Draconic"]},
  "Kenku":{lore:"Cursed bird-folk who mimic sounds they've heard.",height:'5\'0"–5\'6"',speed:30,size:"Medium",languages:["Common","Auran"]},
  "Triton":{lore:"Aquatic guardians of the sea's darkness.",height:'5\'0"–5\'8"',speed:30,size:"Medium",languages:["Common","Primordial"]},
  "Neko / Cat Person":{lore:"Feline-human hybrids with sharp senses and agile grace.",height:'5\'0"–5\'10"',speed:35,size:"Medium",languages:["Common"]},
  "Kitsune / Fox Person":{lore:"Fox spirits with shapeshifting gifts and innate magic.",height:'5\'2"–5\'10"',speed:35,size:"Medium",languages:["Common"]},
  "Wolf Person":{lore:"Pack-oriented wolf-folk with keen instincts.",height:'5\'8"–6\'4"',speed:35,size:"Medium",languages:["Common"]},
  "Cat Person (Neko)":{lore:"Playful cat-folk with fast reflexes and a curious nature.",height:'5\'0"–5\'10"',speed:35,size:"Medium",languages:["Common"]},
  "Vulcan":{lore:"Highly logical humanoids from a desert world, with exceptional mental discipline.",height:'5\'8"–6\'2"',speed:30,size:"Medium",languages:["Common","Vulcan"]},
  "Klingon":{lore:"Proud warrior species who value honour and combat above all.",height:'5\'10"–6\'6"',speed:30,size:"Medium",languages:["Common","Klingon"]},
  "Jaffa":{lore:"Warriors who carry a Goa'uld symbiote for extended life and strength.",height:'6\'0"–6\'6"',speed:30,size:"Medium",languages:["Common","Goa'uld"]}
};

// Race/gender-specific body measurements per race (bust/waist/hip in inches, [min,max])
// Mirrors character_data.py RACE_MEASUREMENTS exactly
(()=>{
  const D={m:{bust:[34,46],waist:[28,38],hip:[32,40]},f:{bust:[30,42],waist:[24,34],hip:[32,44]},n:{bust:[30,44],waist:[24,36],hip:[30,42]}};
  const S={m:{bust:[22,32],waist:[18,26],hip:[22,30]},f:{bust:[20,30],waist:[16,24],hip:[22,32]},n:{bust:[20,30],waist:[16,26],hip:[20,30]}};
  const L={m:{bust:[44,56],waist:[34,46],hip:[38,48]},f:{bust:[38,50],waist:[30,40],hip:[38,50]},n:{bust:[40,54],waist:[32,44],hip:[38,48]}};
  const H={m:{bust:[38,52],waist:[30,42],hip:[34,44]},f:{bust:[34,46],waist:[26,36],hip:[34,46]},n:{bust:[36,48],waist:[28,40],hip:[34,46]}};
  const Sl={m:{bust:[30,40],waist:[24,32],hip:[28,36]},f:{bust:[28,38],waist:[22,28],hip:[30,40]},n:{bust:[28,38],waist:[22,30],hip:[28,38]}};
  window.V6_RACE_MEASUREMENTS={
    // D&D standard (default)
    'Human':D,'Elf':D,'High Elf':D,'Wood Elf':D,'Drow':D,'Half-Elf':D,'Aasimar':D,'Tiefling':D,
    'Changeling':D,'Warforged':D,'Githyanki':D,'Tortle':D,'Genasi':D,'Genasi (Fire)':D,'Genasi (Water)':D,
    'Lizardfolk':D,'Kenku':D,'Triton':D,'Snake Person (Lamia)':D,'Dragon Person (Ryujin)':D,
    'Dog Person (Inu)':D,'Wolf Person':D,'Fox Person (Kitsune)':D,'Horse Person (Centaur)':D,
    'Vulcan':D,'Romulan':D,'Andorian':D,'Betazoid':D,'Trill':D,'Bajoran':D,'Cardassian':D,
    'Orion':D,'Caitian':D,'El-Aurian':D,'Changeling (ST)':D,'Q (Omnipotent)':D,
    'Tau\'ri (Human)':D,'Tok\'ra':D,'Goa\'uld Host':D,'Ancient (Alteran)':D,'Ori (Ascended)':D,'Athosian':D,'Lucian':D,
    'Minbari':D,'Centauri (B5)':D,'Drazi':D,'Pak\'ma\'ra':D,'Shadow Agent':D,
    // Dwarf — medium-default build
    'Dwarf':D,
    // Small races
    'Gnome':S,'Halfling':S,'Ferengi':S,'Asgard (SG)':S,
    // Large races
    'Goliath':L,'Bear Person':L,'Firbolg':L,'Vorlon':L,
    // Heavy/muscular races
    'Dragonborn':H,'Half-Orc':H,'Klingon':H,'Jaffa':H,'Narn':H,
    'Shark Person':H,'Tiger Person':H,'Lion Person':H,'Borg Drone':H,'Wraith':H,
    // Slim races
    'Cat Person (Neko)':Sl,'Rabbit Person (Usagi)':Sl,'Bird Person (Harpy)':Sl,'Deer Person':Sl,
    'Neko / Cat Person':Sl,'Kitsune / Fox Person':Sl,'Tabaxi':Sl,
    // Default fallback key
    '_default':D
  };
})();

// Race stat bonuses applied to random generation
const V6_RACE_BONUSES={
  'Human':{strength:1,dexterity:1,intelligence:1,wisdom:1,constitution:1,charisma_stat:1},
  'Elf':{dexterity:2,intelligence:1},'High Elf':{dexterity:2,intelligence:1},
  'Wood Elf':{dexterity:2,wisdom:1},'Drow':{dexterity:2,charisma_stat:1},
  'Dwarf':{constitution:2},'Halfling':{dexterity:2},'Gnome':{intelligence:2},
  'Half-Elf':{charisma_stat:2,dexterity:1,wisdom:1},'Half-Orc':{strength:2,constitution:1},
  'Tiefling':{charisma_stat:2,intelligence:1},'Aasimar':{charisma_stat:2,wisdom:1},
  'Dragonborn':{strength:2,charisma_stat:1},'Goliath':{strength:2,constitution:1},
  'Tabaxi':{dexterity:2,charisma_stat:1},'Warforged':{constitution:2,strength:1},
  'Firbolg':{wisdom:2,strength:1},'Genasi':{constitution:2},'Lizardfolk':{constitution:2,wisdom:1},
  'Triton':{strength:1,constitution:1,charisma_stat:1},'Kenku':{dexterity:2,wisdom:1},
  'Changeling':{charisma_stat:2},'Neko / Cat Person':{dexterity:2,charisma_stat:1},
  'Kitsune / Fox Person':{dexterity:2,charisma_stat:2},'Wolf Person':{strength:2,constitution:1},
  'Cat Person (Neko)':{dexterity:2,charisma_stat:1},
  'Klingon':{strength:2,constitution:2},'Vulcan':{intelligence:2,wisdom:2},'Jaffa':{strength:2,constitution:1}
};

// Init preset source select
const _v6ps=$('#v6presetSrc');
if(_v6ps){
  _v6ps.innerHTML=V6_PRESET_SOURCES.map(s=>`<option value="${safe(s)}">${safe(s)}</option>`).join('');
  _v6ps.onchange=()=>v6ApplyPreset(_v6ps.value);
}
// Init photo style select
const _v6phSel=$('#v6photoStyle');
if(_v6phSel) _v6phSel.innerHTML=V6_IMAGE_STYLES.map(s=>`<option value="${safe(s)}">${safe(s)}</option>`).join('');

function v6ApplyPreset(src){
  const preset=V6_PRESETS[src];
  const raceEl=$('#v6raceSelect');
  if(preset&&raceEl){
    const races=[...preset.races,'Custom'];
    raceEl.innerHTML=races.map(r=>`<option value="${safe(r)}">${safe(r)}</option>`).join('');
  } else if(raceEl){
    fillV6Sel('#v6raceSelect',Object.keys(studioOptions.races||{}));
  }
  if(preset&&preset.hair_colors) fillV6Sel('#v6hairSelect',[...preset.hair_colors,'Custom']);
  else fillV6Sel('#v6hairSelect',V6_HAIR_OPTS);
  if(preset&&preset.eye_colors) fillV6Sel('#v6eyesSelect',[...preset.eye_colors,'Custom']);
  else fillV6Sel('#v6eyesSelect',V6_EYES_OPTS);
  const abRow=$('#v6abilitiesRow'),abSel=$('#v6abilitiesSelect');
  if(preset&&preset.abilities&&abSel){
    abRow.style.display='';
    abSel.innerHTML=preset.abilities.map(a=>`<option value="${safe(a)}">${safe(a)}</option>`).join('');
  } else if(abRow){ abRow.style.display='none'; }
  if(preset&&preset.traits) fillV6Sel('#v6traitsSelect',[...preset.traits,'Custom']);
  else fillV6Sel('#v6traitsSelect',V6_TRAITS_LIST);
  if(preset&&preset.backgrounds) fillV6Sel('#v6bgSelect',[...preset.backgrounds,'Custom']);
  else fillV6Sel('#v6bgSelect',studioOptions.backgrounds||[]);
}

function v6UpdateRaceInfo(race){
  const div=$('#v6raceInfo');if(!div)return;
  const info=V6_DND_RACE_INFO[race];
  if(!info){div.style.display='none';return;}
  div.style.display='';
  div.innerHTML=`<b style="color:var(--gold)">🛡️ ${safe(race)}</b>&nbsp;<span style="color:var(--muted)">${safe(info.lore||'')}</span><br>`+
    `<span>📏 ${safe(info.height||'?')} &nbsp;|&nbsp; 👟 ${info.speed||30}ft &nbsp;|&nbsp; ⚖️ ${safe(info.size||'?')} &nbsp;|&nbsp; 🗣️ ${(info.languages||[]).join(', ')}</span>`;
}
function v6GetGenderCat(){
  const form=$('#characterFormV6');
  const gVal=form?form.elements['gender']?.value:'';
  return gVal==='Female'||gVal==='Futa / Futanari'?'f':gVal==='Non-binary'||gVal==='Androgynous'||gVal==='Gender-fluid'?'n':'m';
}

function v6UpdateMeasurementRanges(){
  const raceEl=$('#v6raceSelect');
  const race=raceEl?raceEl.value:'Human';
  const gCat=v6GetGenderCat();
  const rng=(V6_RACE_MEASUREMENTS[race]||V6_RACE_MEASUREMENTS['_default'])[gCat];
  const fields=[
    {id:'v6bust',   key:'bust',  label:'Bust/Chest'},
    {id:'v6waist',  key:'waist', label:'Waist'},
    {id:'v6hips',   key:'hip',   label:'Hips'}
  ];
  fields.forEach(({id,key,label})=>{
    const inp=$('#'+id);if(!inp)return;
    const [lo,hi]=rng[key];
    inp.placeholder=`${lo}"–${hi}"`;
    // Update or create range hint
    let hint=inp.nextElementSibling;
    if(!hint||!hint.classList.contains('v6-meas-range')){
      hint=document.createElement('small');
      hint.className='v6-meas-range';
      hint.style.cssText='display:block;font-size:9px;color:var(--muted);margin-top:1px';
      inp.after(hint);
    }
    hint.textContent=`Valid: ${lo}"–${hi}"`;
    // Validate current value
    const cur=parseFloat(inp.value);
    if(inp.value&&!isNaN(cur)){
      inp.style.borderColor=(cur<lo||cur>hi)?'#c0392b':'';
    } else {
      inp.style.borderColor='';
    }
  });
}

function v6UpdateRaceLanguages(){
  const raceEl=$('#v6raceSelect');
  const race=raceEl?raceEl.value:'Human';
  const info=V6_DND_RACE_INFO[race];
  const raceNativeLangs=new Set(info?info.languages:[]);
  const sel=$('#v6langSelect');if(!sel)return;
  // Re-sort: native langs first, then rest
  const allLangs=V6_LANGUAGES;
  const native=allLangs.filter(l=>raceNativeLangs.has(l));
  const rest=allLangs.filter(l=>!raceNativeLangs.has(l));
  const sorted=[...native,...rest];
  // Remember current selection
  const selected=new Set(Array.from(sel.selectedOptions).map(o=>o.value));
  // If nothing selected yet and there are native langs, default-select them
  const defaultSelect=selected.size===0&&native.length>0;
  sel.innerHTML=sorted.map(l=>{
    const isNative=raceNativeLangs.has(l);
    const isSel=selected.has(l)||(defaultSelect&&isNative);
    return `<option value="${safe(l)}"${isSel?' selected':''}${isNative?' data-native="1"':''} style="${isNative?'color:var(--gold)':''}">` +
           `${isNative?'★ ':''}${safe(l)}</option>`;
  }).join('');
}

function v6OnRaceOrGenderChange(){
  const raceEl=$('#v6raceSelect');
  if(raceEl)v6UpdateRaceInfo(raceEl.value);
  v6UpdateMeasurementRanges();
  v6UpdateRaceLanguages();
}

const _v6raceSelEl=$('#v6raceSelect');
if(_v6raceSelEl)_v6raceSelEl.addEventListener('change',()=>v6OnRaceOrGenderChange());

// Also wire gender change to update measurement ranges and language sort
const _v6genderSelEl=$('#v6genderSelect');
if(_v6genderSelEl)_v6genderSelEl.addEventListener('change',()=>v6UpdateMeasurementRanges());

// Total Random button
const _v6totalRnd=$('#v6totalRandom');
if(_v6totalRnd)_v6totalRnd.onclick=()=>{if(!Object.keys(studioOptions).length){toast('Loading options…');return;}v6FillForm(v6BuildRandom());toast('Total random character generated');};

// Photo generation via Pollinations.ai
const _v6genPhoto=$('#v6genPhoto');
if(_v6genPhoto)_v6genPhoto.onclick=()=>{
  const form=$('#characterFormV6');if(!form)return;
  const fd=new FormData(form);
  const style=($('#v6photoStyle')||{}).value||'Fantasy Art';
  const prompt=`${style} character portrait, ${fd.get('gender')||''} ${fd.get('race')||''} ${fd.get('profession')||''}, ${fd.get('hair')||''} hair, ${fd.get('eyes')||''} eyes, ${fd.get('body_type')||''} build, ${fd.get('skin')||''} skin, detailed, high quality`;
  const url=`https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=512&height=768&nologo=true&nofeed=true`;
  const prev=$('#v6photoPreview');
  if(prev)prev.innerHTML=`<div style="font-size:10px;color:var(--muted);margin-bottom:4px" id="v6photoStatus">Generating…</div><img src="${url}" style="max-width:220px;border-radius:6px;border:1px solid var(--line)" onload="document.getElementById('v6photoStatus')&&(document.getElementById('v6photoStatus').textContent='Generated!')" onerror="document.getElementById('v6photoStatus')&&(document.getElementById('v6photoStatus').textContent='Generation failed — check connection')">`;
  const ph=$('#v6photoPath');if(ph)ph.value=url;
};

// Photo upload
const _v6pu=$('#v6photoUpload');
if(_v6pu)_v6pu.onchange=e=>{
  const f=e.target.files[0];if(!f)return;
  const r=new FileReader();
  r.onload=ev=>{
    const prev=$('#v6photoPreview');
    if(prev)prev.innerHTML=`<img src="${ev.target.result}" style="max-width:220px;border-radius:6px;border:1px solid var(--line)">`;
    const ph=$('#v6photoPath');if(ph)ph.value=ev.target.result;
  };
  r.readAsDataURL(f);
};

// Import JSON
const _v6impBtn=$('#v6importJson');
if(_v6impBtn)_v6impBtn.onclick=()=>{
  const row=$('#v6importRow');if(row)row.style.display=row.style.display==='none'?'':'none';
};
const _v6impFile=$('#v6importFile');
if(_v6impFile)_v6impFile.onchange=e=>{
  const f=e.target.files[0];if(!f)return;
  const r=new FileReader();
  r.onload=ev=>{
    try{
      const ch=JSON.parse(ev.target.result);
      ['weapon_training','magic_type','power_system','traits','quirks','skills','emotion_styles','tags','languages','abilities'].forEach(k=>{if(typeof ch[k]==='string')try{ch[k]=JSON.parse(ch[k]);}catch{ch[k]=[ch[k]];}});
      if(ch.measurements&&typeof ch.measurements==='string'){try{const m=JSON.parse(ch.measurements);Object.assign(ch,m);}catch{}}
      if(ch.personality&&typeof ch.personality==='string'&&!ch.tags){try{ch.tags=JSON.parse(ch.personality);}catch{}}
      v6FillForm(ch);toast('Character imported');
      const row=$('#v6importRow');if(row)row.style.display='none';
      e.target.value='';
    }catch{toast('Invalid JSON file');}
  };
  r.readAsText(f);
};

// Reset All
const _v6resetAll=$('#v6resetAll');
if(_v6resetAll)_v6resetAll.onclick=()=>{
  const form=$('#characterFormV6');if(form)form.reset();
  ['str','dex','int','wis','con','spd','lck','cha'].forEach(k=>{const el=$(`#v6${k}Val`);if(el)el.textContent='10';});
  const lks=$('#v6lksVal');if(lks)lks.textContent='5';
  const prev=$('#v6photoPreview');if(prev)prev.innerHTML='';
  const ph=$('#v6photoPath');if(ph)ph.value='';
  toast('Form reset');
};

// Saved Characters list
async function v6LoadSavedChars(){
  const div=$('#v6savedChars');if(!div)return;
  div.innerHTML='<div class="empty-state">Loading…</div>';
  try{
    const chars=await api('/api/characters');
    if(!chars||!chars.length){div.innerHTML='<div class="empty-state">No characters saved yet.</div>';return;}
    div.innerHTML=chars.slice(0,50).map(c=>`
      <div class="entity-row" id="v6sc_${c.id}" style="flex-direction:column;align-items:flex-start;gap:4px">
        <span class="entity-name">${safe(c.name||'?')} — Lv${c.level||1} ${safe(c.race||'')} ${safe(c.profession||'')}</span>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          <button class="ghost" style="font-size:9px;padding:3px 7px" onclick="v6LoadChar(${c.id})">📋 Load</button>
          <button class="ghost" style="font-size:9px;padding:3px 7px" onclick="v6ExportChar(${c.id})">📤 Export</button>
          <button class="ghost" style="font-size:9px;padding:3px 7px" onclick="v6GenCharPhoto(${c.id})">🎨 Photo</button>
          <button class="ghost" style="font-size:9px;padding:3px 7px;color:#c44" onclick="v6DelChar(${c.id})">🗑️ Delete</button>
        </div>
      </div>`).join('');
  }catch{div.innerHTML='<div class="empty-state">Error loading characters.</div>';}
}
const _v6refSaved=$('#v6refreshSaved');
if(_v6refSaved)_v6refSaved.onclick=v6LoadSavedChars;

window.v6LoadChar=async(id)=>{
  try{
    const chars=await api('/api/characters');
    const ch=chars.find(c=>c.id===id);if(!ch){toast('Character not found');return;}
    ['weapon_training','magic_type','power_system','traits','quirks','skills','emotion_styles','tags','languages','abilities'].forEach(k=>{
      if(typeof ch[k]==='string')try{ch[k]=JSON.parse(ch[k]);}catch{ch[k]=[ch[k]];}
    });
    if(ch.measurements&&typeof ch.measurements==='string'){try{const m=JSON.parse(ch.measurements);Object.assign(ch,m);}catch{}}
    if(ch.personality&&typeof ch.personality==='string'&&!ch.tags){try{ch.tags=JSON.parse(ch.personality);}catch{}}
    v6FillForm(ch);toast(`${ch.name||'Character'} loaded`);
    const form=$('#characterFormV6');if(form)form.scrollIntoView({behavior:'smooth',block:'start'});
  }catch{toast('Load failed');}
};

window.v6ExportChar=async(id)=>{
  try{
    const chars=await api('/api/characters');
    const ch=chars.find(c=>c.id===id);if(!ch)return;
    const name=(ch.name||'character').replace(/\s+/g,'_');
    const blob=new Blob([JSON.stringify(ch,null,2)],{type:'application/json'});
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${name}.json`;a.click();
  }catch{toast('Export failed');}
};

window.v6DelChar=async(id)=>{
  if(!confirm('Delete this character?'))return;
  try{
    await api(`/api/characters/${id}`,{method:'DELETE'});
    toast('Character deleted');v6LoadSavedChars();await loadCharacterStudio();
  }catch{toast('Delete failed');}
};

window.v6GenCharPhoto=async(id)=>{
  try{
    const chars=await api('/api/characters');
    const ch=chars.find(c=>c.id===id);if(!ch)return;
    const style=($('#v6photoStyle')||{}).value||'Fantasy Art';
    const prompt=`${style} character portrait, ${ch.gender||''} ${ch.race||''} ${ch.profession||''}, ${ch.hair||''} hair, ${ch.eyes||''} eyes, detailed, high quality`;
    const url=`https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=512&height=768&nologo=true&nofeed=true`;
    const row=$(`#v6sc_${id}`);
    if(row){const img=document.createElement('img');img.src=url;img.style.cssText='max-width:180px;border-radius:4px;border:1px solid var(--line);margin-top:6px';row.appendChild(img);}
    toast('Generating photo…');
  }catch{toast('Photo generation failed');}
};

// ─── Chat textarea: auto-grow + Enter to submit ───
(()=>{
  const ta=$('#chatInput');
  if(!ta||ta.tagName!=='TEXTAREA')return;
  const grow=()=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,120)+'px';};
  ta.addEventListener('input',grow);
  ta.addEventListener('keydown',e=>{
    if(e.key==='Escape'){e.preventDefault();ta.blur();return;} // Escape releases focus → WASD/arrows work again
    e.stopPropagation(); // block document-level WASD/arrow map handlers while typing
    if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('#chatForm').requestSubmit();}
  });
  // expose for programmatic value sets (voice, option chips)
  window._chatInputGrow=grow;
})();
