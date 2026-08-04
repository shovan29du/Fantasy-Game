const worlds=[
 {name:'Aethoria Prime',tags:'Fantasy · Magic 8 · Tech 2',place:'Thornwatch Crossing',theme:'local'},
 {name:'Neon Shard-9',tags:'Cyberpunk · Magic 1 · Tech 9',place:'Kairox Undercity',theme:'area'},
 {name:'Earth-Z',tags:'Apocalypse · Science 6 · Threat 9',place:'London Quarantine',theme:'area'},
 {name:'Celestia Drift',tags:'Alien Space · Psionics 7 · Tech 10',place:'The Orison Gate',theme:'universe'}
];
const party=[
 {name:'Ari Solwyn',role:'Human · Spellblade',lv:7,hp:86,initials:'AS'},
 {name:'Kael Ironroot',role:'Dwarf · Vanguard',lv:7,hp:74,initials:'KI'},
 {name:'Nyx-13',role:'Cyborg · Operative',lv:6,hp:91,initials:'N13'},
 {name:'Seraphine',role:'Tiefling · Seer',lv:6,hp:62,initials:'SE'}
];
const quests=[
 {name:'Echoes Beyond the Gate',text:'Enter the violet portal and identify its origin.',progress:'2 / 4 clues'},
 {name:'The Ashen Crown',text:'Recover the crown before the Bone Court.',progress:'Ruins: 1.2 km'},
 {name:'Companion: Broken Code',text:'Help Nyx recover her erased memory.',progress:'Trust 65%'}
];
const actions=[
 {name:'Arc Slash',icon:'⚔',kind:'attack',cost:'2 AP'}, {name:'Fire Bolt',icon:'✦',kind:'attack',cost:'1 mana'},
 {name:'Guard',icon:'◈',kind:'defence',cost:'1 AP'}, {name:'Aegis',icon:'⬡',kind:'defence',cost:'3 mana'},
 {name:'Blink',icon:'⌁',kind:'utility',cost:'2 mana'}, {name:'Inspect',icon:'⌕',kind:'utility',cost:'Free'},
 {name:'Potion',icon:'⚗',kind:'utility',cost:'2 left'}
];
let state={world:0,scale:'local',x:42,y:52,zoom:100,xp:3420,level:7,selected:0,skillPoints:2};
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
function toast(message){const el=$('#toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),1800)}
function renderParty(){
 $('#partyList').innerHTML=party.map((p,i)=>`<div class="party-card ${i===state.selected?'active':''}" data-party="${i}"><div class="portrait">${p.initials}</div><div><strong>${p.name}</strong><small>${p.role}</small><div class="hp"><i style="width:${p.hp}%"></i></div></div><span class="level">LV ${p.lv}</span></div>`).join('');
 $$('[data-party]').forEach(el=>el.onclick=()=>{state.selected=+el.dataset.party;renderParty();toast(`${party[state.selected].name} selected`)})
}
function renderQuests(){
 $('#questList').innerHTML=quests.map((q,i)=>`<div class="quest"><b>${i===0?'✦ ':''}${q.name}</b><p>${q.text}</p><div class="quest-progress"><span>${q.progress}</span><span>›</span></div></div>`).join('')
}
function renderActions(filter='all'){
 const visible=actions.filter(a=>filter==='all'||a.kind===filter);
 $('#actionBar').innerHTML=visible.map((a,i)=>`<button class="action" data-action="${a.name}"><kbd>${i+1}</kbd><span class="icon">${a.icon}</span><b>${a.name}</b><small>${a.cost}</small></button>`).join('');
 $$('[data-action]').forEach(el=>el.onclick=()=>toast(`${el.dataset.action} readied`));
}
const panels={
 character:()=>`<div class="character-hero"><div class="hero-portrait">AS</div><h2>Ari Solwyn</h2><p>Human · Level ${state.level} Spellblade</p></div><div class="xp-row"><div><span>EXPERIENCE</span><span>${state.xp.toLocaleString()} / 4,000</span></div><div class="meter"><i style="width:${state.xp/40}%"></i></div></div><div class="stats">${[['STR',14],['DEX',16],['CON',13],['INT',18],['WIS',12],['CHA',15]].map(s=>`<div class="stat"><b>${s[1]}</b><small>${s[0]} · +${Math.floor((s[1]-10)/2)}</small></div>`).join('')}</div><div class="resource"><div><span>Health</span><b>42 / 48</b></div><div class="meter"><i style="width:87%;background:var(--green)"></i></div></div><div class="resource"><div><span>Mana</span><b>27 / 35</b></div><div class="meter"><i style="width:77%;background:var(--purple)"></i></div></div>`,
 inventory:()=>`<div class="panel-title"><span>INVENTORY</span><small>18 / 30</small></div><div class="inventory-grid">${[['⚔','Runeblade'],['⌁','Longbow'],['◈','Ward shield'],['⚗','Healing potion'],['♦','Portal shard'],['🗝','Iron key'],['✦','Focus crystal'],['◌','Rope'],['▰','Rations'],['◇','Empty'],['◇','Empty'],['◇','Empty']].map((it,i)=>`<button class="item" data-item="${it[1]}">${it[0]}${i===3?'<small>2</small>':''}</button>`).join('')}</div><div class="item-info"><h3 id="itemName">Runeblade</h3><p id="itemDesc">Weapon level 3 · Versatile sword. Deals arcane damage after casting a spell.</p></div>`,
 spells:()=>`<div class="panel-title"><span>SPELLBOOK</span><small>8 prepared</small></div>${[['✦','Fire Bolt','Evocation · Attack','Cantrip'],['⬡','Arcane Aegis','Abjuration · Defence','Level 1'],['⌁','Blink Step','Conjuration · Utility','Level 2'],['☄','Starfall','Evocation · Attack','Level 3'],['◉','Detect Portal','Divination · Utility','Ritual']].map(s=>`<div class="spell-row"><span class="rune">${s[0]}</span><span><b>${s[1]}</b><small>${s[2]}</small></span><em>${s[3]}</em></div>`).join('')}`,
 skills:()=>`<div class="panel-title"><span>SPELLBLADE TREE</span><small>${state.skillPoints} points</small></div><div class="tree"><button class="skill-node unlocked"><b>Arcane Edge</b><small>Unlocked · Passive</small></button><div class="tree-line"></div><button class="skill-node unlocked"><b>Spell Parry</b><small>Unlocked · Active defence</small></button><div class="tree-line"></div><button class="skill-node" id="unlockSkill"><b>Rift Strike</b><small>Cost 1 · Active attack</small></button><div class="tree-line"></div><button class="skill-node locked"><b>Worldcutter</b><small>Requires Rift Strike</small></button></div>`
};
function showPanel(name){$('#detailContent').innerHTML=panels[name]();if(name==='inventory')$$('[data-item]').forEach(el=>el.onclick=()=>{$('#itemName').textContent=el.dataset.item;$('#itemDesc').textContent=el.dataset.item==='Runeblade'?'Weapon level 3 · Versatile sword. Deals arcane damage after casting a spell.':'A useful piece of multiverse adventuring gear.'});if(name==='skills'&&$('#unlockSkill'))$('#unlockSkill').onclick=()=>{if(state.skillPoints){state.skillPoints--;toast('Rift Strike unlocked');showPanel('skills')}else toast('No skill points available')}}
function updateWorld(){const w=worlds[state.world];$('#worldName').textContent=w.name;$('#worldTags').textContent=w.tags;$('#locationName').textContent=w.place;state.scale=w.theme;setScale(state.scale)}
function setScale(scale){state.scale=scale;$('#map').className=`map map-${scale}`;$('#scaleLabel').textContent=`${scale.toUpperCase()} MAP`;$$('[data-scale]').forEach(b=>b.classList.toggle('active',b.dataset.scale===scale));}
function move(x,y){state.x=Math.max(4,Math.min(96,x));state.y=Math.max(6,Math.min(92,y));const p=$('#playerToken');p.style.setProperty('--x',state.x+'%');p.style.setProperty('--y',state.y+'%')}
renderParty();renderQuests();renderActions();showPanel('character');
$$('[data-scale]').forEach(b=>b.onclick=()=>setScale(b.dataset.scale));
$$('.detail-tabs button').forEach(b=>b.onclick=()=>{$$('.detail-tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');showPanel(b.dataset.panel)});
$$('.dock-head button').forEach(b=>b.onclick=()=>{$$('.dock-head button').forEach(x=>x.classList.remove('active'));b.classList.add('active');renderActions(b.dataset.filter)});
$('#map').addEventListener('click',e=>{if(e.target.closest('button'))return;const r=e.currentTarget.getBoundingClientRect();move((e.clientX-r.left)/r.width*100,(e.clientY-r.top)/r.height*100)});
document.addEventListener('keydown',e=>{const active=document.activeElement;if(active&&active.tagName==='INPUT')return;const keys={w:[0,-3],ArrowUp:[0,-3],s:[0,3],ArrowDown:[0,3],a:[-3,0],ArrowLeft:[-3,0],d:[3,0],ArrowRight:[3,0]};if(keys[e.key]){e.preventDefault();move(state.x+keys[e.key][0],state.y+keys[e.key][1])}if('1234'.includes(e.key))setScale(['local','area','world','universe'][+e.key-1])});
$('#portal').onclick=()=>{state.world=(state.world+1)%worlds.length;updateWorld();toast(`Portal crossed: ${worlds[state.world].name}`)};
$$('.map-node').forEach(n=>n.onclick=()=>toast(`${n.dataset.label}: destination marked`));
$('#zoomIn').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.min(140,state.zoom+10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#zoomOut').onclick=()=>{$('#zoomText').textContent=(state.zoom=Math.max(70,state.zoom-10))+'%';$('#map').style.backgroundSize=state.zoom+'%'};
$('#saveBtn').onclick=async()=>{try{const r=await fetch('/api/saves/1',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({state})});if(!r.ok)throw 0;toast('Campaign saved to slot 1')}catch{localStorage.setItem('worldweaver-save',JSON.stringify(state));toast('Saved on this device')}};
$('#journalBtn').onclick=()=>toast('Quest journal opened');
$('#chatToggle').onclick=()=>$('#chatPanel').classList.add('open');$('#closeChat').onclick=()=>$('#chatPanel').classList.remove('open');
$('#chatForm').onsubmit=async e=>{e.preventDefault();const input=$('#chatInput'),msg=input.value.trim();if(!msg)return;$('#chatLog').insertAdjacentHTML('beforeend',`<p class="player"><b>YOU</b>${msg.replace(/[<>]/g,'')}</p>`);input.value='';$('#aiStatus').textContent='Thinking…';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,context:{world:worlds[state.world],location:worlds[state.world].place,level:state.level,party:party.map(p=>p.name),quests}})});const data=await r.json();$('#chatLog').insertAdjacentHTML('beforeend',`<p class="gm"><b>WORLDWEAVER</b>${data.reply.replace(/[<>]/g,'')}</p>`);$('#aiStatus').textContent=data.online?'LM Studio connected':'LM Studio offline'}catch{$('#chatLog').insertAdjacentHTML('beforeend','<p class="gm"><b>WORLDWEAVER</b>The local storyteller cannot be reached.</p>');$('#aiStatus').textContent='Connection unavailable'}$('#chatLog').scrollTop=$('#chatLog').scrollHeight};
