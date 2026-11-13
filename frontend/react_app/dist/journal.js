// Journal: quests, notes, memory, people and key moments for the current story.
// Loaded after game.js and shares its globals ($, api, safe, toast, state, ...).
const J={tab:'quests',q:'',noteTag:'',noteKind:'',memType:'',memView:'story',editing:null,seq:0,counts:null,previewQuery:''};
const JTABS=[['quests','Quests'],['notes','Notes'],['memory','Memory'],['people','People'],['moments','Moments']];
const jsid=()=>state.sessionId||'default';
const jenc=encodeURIComponent;
const jsend=(method,body)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const jdate=iso=>{const d=new Date(iso);return isNaN(d)?'':d.toLocaleDateString(undefined,{month:'short',day:'numeric'});};
const jempty=text=>`<div class="journal-empty">${safe(text)}</div>`;
const jbody=()=>$('#journalBody');
const jfilterWords=text=>{const w=J.q.toLowerCase().split(/\s+/).filter(Boolean);const t=String(text).toLowerCase();return w.every(x=>t.includes(x));};

function openJournal(tab){
  const drawer=$('#journalDrawer');if(!drawer)return;
  if(tab)J.tab=tab;
  drawer.hidden=false;document.body.classList.add('journal-open');
  $('#journalStory').textContent=state.worlds?.[state.worldIndex]?.name||'';
  renderJournal();
}
function closeJournal(){
  const drawer=$('#journalDrawer');if(!drawer)return;
  drawer.hidden=true;document.body.classList.remove('journal-open');
}
function toggleJournal(){const d=$('#journalDrawer');if(d&&!d.hidden)closeJournal();else openJournal();}

async function jRefreshCounts(){
  try{J.counts=await api(`/api/journal/overview?session_id=${jenc(jsid())}&quests=${(state.quests||[]).length}`);}catch{}
  JTABS.forEach(([id])=>{
    const el=document.querySelector(`[data-jtab="${id}"] i`);if(!el||!J.counts)return;
    const n={quests:J.counts.quests,notes:J.counts.notes,memory:J.counts.memory.story,people:'',moments:J.counts.moments}[id];
    el.textContent=n?n:'';
  });
}

function renderJournal(){
  $('#journalTabs').innerHTML=JTABS.map(([id,label])=>`<button type="button" role="tab" class="${J.tab===id?'active':''}" data-jtab="${id}" aria-selected="${J.tab===id}">${label}<i></i></button>`).join('');
  $('#journalSearch').value=J.q;
  $('#journalSearch').placeholder={quests:'Search quests…',notes:'Search notes…',memory:'Search memories…',people:'Search people…',moments:'Search moments…'}[J.tab];
  $('#journalNotice').hidden=jsid()!=='default';
  const seq=++J.seq;
  const draw={quests:jQuests,notes:jNotes,memory:jMemory,people:jPeople,moments:jMoments}[J.tab];
  Promise.resolve(draw(seq)).catch(e=>{if(seq===J.seq)jbody().innerHTML=jempty(e.message||'Could not load this tab.');});
  jRefreshCounts();
}

/* ── Quests ───────────────────────────────────────────────────────── */
function jQuestCard(q,i){
  const type=q.type||q.quest_type||'quest';
  const progress=Math.max(0,Math.min(100,q.progress||0));
  const xp=q.xp_reward||q.xp||'';
  return `<article class="jcard" data-idx="${i}">
    <div class="jcard-head"><b>${safe(q.title||'Quest')}</b><span class="jchip">${safe(type)}</span>${xp?`<span class="jchip jchip-gold">${safe(xp)} XP</span>`:''}</div>
    ${q.description?`<p>${safe(q.description)}</p>`:''}
    ${q.hint?`<p class="jhint">Hint: ${safe(q.hint)}</p>`:''}
    <div class="jprogress" title="${progress}% complete"><span style="width:${progress}%"></span></div>
    <div class="jrow"><small>${progress}%${q.reward?` · Reward: ${safe(q.reward)}`:''}</small>
      <span class="jbtns"><button type="button" class="ghost" data-jact="q-progress" data-idx="${i}" data-n="${Math.min(100,progress+25)}"${progress>=100?' disabled':''}>+25%</button>
      <button type="button" class="gold" data-jact="q-complete" data-idx="${i}">Complete</button>
      <button type="button" class="ghost" data-jact="q-abandon" data-idx="${i}">Abandon</button></span></div>
  </article>`;
}
async function jQuests(seq){
  const quests=(state.quests||[]).map((q,i)=>[q,i]).filter(([q])=>jfilterWords(`${q.title} ${q.description||''} ${q.hint||''} ${q.type||q.quest_type||''}`));
  let history=[];
  try{history=await api(`/api/quests/history?character_name=${jenc(state.sheet?.name||'')}&character_id=${state.characterId||''}&limit=30`);}catch{}
  if(seq!==J.seq)return;
  history=history.filter(q=>jfilterWords(`${q.title} ${q.description||''}`));
  jbody().innerHTML=`<div class="jbar"><button type="button" class="gold" data-jact="q-generate">✦ New quest from the story</button><small>Quests are generated from your recent chat.</small></div>
    ${quests.length?quests.map(([q,i])=>jQuestCard(q,i)).join(''):jempty(J.q?'No quests match that search.':'No active quests. Generate one from the story so far.')}
    ${history.length?`<details class="jfold"><summary>Finished quests <small>${history.length}</small></summary>${history.map(q=>`<article class="jcard jcard-done"><div class="jcard-head"><b>${safe(q.title)}</b><span class="jchip">${safe(q.status)}</span><small>${safe(q.reward||'')}</small></div></article>`).join('')}</details>`:''}`;
}

/* ── Notes ────────────────────────────────────────────────────────── */
function jNoteForm(n){
  const kinds=['note','clue','todo','recap'];
  return `<form class="jform" data-jform="note" ${n?`data-id="${n.id}"`:''}>
    <input name="title" placeholder="Title" maxlength="120" value="${safe(n?.title||'')}">
    <textarea name="body" rows="${n?6:3}" placeholder="What do you want to remember? Clues, plans, names, promises…">${safe(n?.body||'')}</textarea>
    <div class="jrow"><input name="tags" placeholder="Tags, comma separated" value="${safe((n?.tags||[]).join(', '))}">
      <select name="kind">${kinds.map(k=>`<option value="${k}"${(n?.kind||'note')===k?' selected':''}>${k}</option>`).join('')}</select></div>
    <div class="jbtns"><button class="gold">${n?'Save changes':'Add note'}</button>${n?'<button type="button" class="ghost" data-jact="cancel-edit">Cancel</button>':''}</div>
  </form>`;
}
async function jNotes(seq){
  const params=`session_id=${jenc(jsid())}&q=${jenc(J.q)}&tag=${jenc(J.noteTag)}&kind=${jenc(J.noteKind)}`;
  const data=await api(`/api/journal/notes?${params}`);
  if(seq!==J.seq)return;
  const cards=data.items.map(n=>J.editing?.kind==='note'&&J.editing.id===n.id?`<article class="jcard">${jNoteForm(n)}</article>`:
    `<article class="jcard${n.pinned?' jcard-pinned':''}"><div class="jcard-head"><b>${n.pinned?'📌 ':''}${safe(n.title||'Untitled')}</b><span class="jchip">${safe(n.kind)}</span><small>${jdate(n.updated_at)}</small></div>
      ${n.body?`<p class="jtext">${safe(n.body)}</p>`:''}
      <div class="jrow"><span class="jtags">${n.tags.map(t=>`<button type="button" class="jtag${J.noteTag===t?' on':''}" data-jact="note-tag" data-tag="${safe(t)}">#${safe(t)}</button>`).join('')}</span>
      <span class="jbtns"><button type="button" class="ghost" data-jact="note-pin" data-id="${n.id}" data-pinned="${n.pinned?0:1}">${n.pinned?'Unpin':'Pin'}</button>
      <button type="button" class="ghost" data-jact="note-edit" data-id="${n.id}">Edit</button>
      <button type="button" class="ghost" data-jact="note-delete" data-id="${n.id}">Delete</button></span></div></article>`).join('');
  jbody().innerHTML=`${jNoteForm(null)}
    <div class="jbar"><button type="button" class="ghost" data-jact="recap">✦ Write a recap of the story so far</button>
      <select data-jfilter="noteKind"><option value="">All kinds</option>${data.kinds.map(k=>`<option value="${k}"${J.noteKind===k?' selected':''}>${k}</option>`).join('')}</select>
      ${J.noteTag?`<button type="button" class="jtag on" data-jact="note-tag" data-tag="">#${safe(J.noteTag)} ✕</button>`:''}</div>
    ${cards||jempty(J.q||J.noteTag||J.noteKind?'No notes match.':'No notes yet. Jot down clues, plans and promises as you play. You can also add any chat message with the 📝 button.')}`;
}

/* ── Memory ───────────────────────────────────────────────────────── */
const JLEVELS=[['minor','Minor'],['normal','Normal'],['important','Important']];
function jMemoryForm(m){
  return `<form class="jform" data-jform="memory" ${m?`data-id="${m.id}"`:''}>
    <textarea name="fact" rows="${m?3:2}" maxlength="600" placeholder="A fact the storyteller should remember, e.g. “Marta owes me a favour.”">${safe(m?.fact||'')}</textarea>
    <div class="jrow"><select name="memory_type">${memTypes().map(t=>`<option value="${t}"${(m?.memory_type||'general')===t?' selected':''}>${t}</option>`).join('')}</select>
      <select name="level">${JLEVELS.map(([v,l])=>`<option value="${v}"${(m?.level||'normal')===v?' selected':''}>${l}</option>`).join('')}</select>
      ${m?'':`<label class="jcheck"><input type="checkbox" name="pinned"> Pin</label><label class="jcheck" title="Applies to every story"><input type="checkbox" name="shared"> All stories</label>`}</div>
    <div class="jbtns"><button class="gold">${m?'Save changes':'Remember this'}</button>${m?'<button type="button" class="ghost" data-jact="cancel-edit">Cancel</button>':''}</div>
  </form>`;
}
let _jMemTypes=['episodic','semantic','procedural','preference','event','general'];
const memTypes=()=>_jMemTypes;
function jMemoryCard(m,legacy){
  const edit=J.editing?.kind==='memory'&&J.editing.id===m.id;
  if(edit)return `<article class="jcard">${jMemoryForm(m)}</article>`;
  return `<article class="jcard jmem${m.pinned?' jcard-pinned':''}">
    <div class="jrow"><button type="button" class="jstar${m.pinned?' on':''}" data-jact="mem-pin" data-id="${m.id}" data-pinned="${m.pinned?0:1}" title="${m.pinned?'Pinned: never fades':'Pin so it never fades'}">${m.pinned?'★':'☆'}</button>
      <p class="jtext">${safe(m.fact)}</p></div>
    <div class="jrow"><span class="jtags"><span class="jchip">${safe(m.memory_type)}</span><span class="jchip">${m.origin==='auto'?'auto-captured':'saved by you'}</span><span class="jchip">${m.scope==='shared'?'all stories':'this story'}</span>${m.character_name?`<span class="jchip">${safe(m.character_name)}</span>`:''}</span>
      <span class="jbtns">${legacy?`<button type="button" class="gold" data-jact="mem-adopt" data-id="${m.id}">Use in this story</button>`
        :`<select data-jact="mem-level" data-id="${m.id}" title="How strongly the storyteller favours this">${JLEVELS.map(([v,l])=>`<option value="${v}"${m.level===v?' selected':''}>${l}</option>`).join('')}</select><button type="button" class="ghost" data-jact="mem-edit" data-id="${m.id}">Edit</button>`}
      <button type="button" class="ghost" data-jact="mem-delete" data-id="${m.id}">Forget</button></span></div></article>`;
}
async function jMemory(seq){
  const params=`session_id=${jenc(jsid())}&q=${jenc(J.q)}&memory_type=${jenc(J.memType)}&view=${J.memView}`;
  const [data,preview]=await Promise.all([
    api(`/api/journal/memory?${params}`),
    J.memView==='story'?api(`/api/journal/memory/preview?session_id=${jenc(jsid())}&character_name=${jenc(state.sheet?.name||'')}&q=${jenc(J.previewQuery)}`).catch(()=>({context:''})):Promise.resolve(null),
  ]);
  if(seq!==J.seq)return;
  _jMemTypes=data.types;
  const legacy=data.counts.legacy;
  const types=[''].concat(data.types);
  jbody().innerHTML=`
    <p class="jintro">These are the facts the storyteller can recall in this story. Pinned and important ones are considered first, and the most relevant are added to every reply. Anything you forget here is gone for good.</p>
    ${J.memView==='story'?`<details class="jfold" open><summary>What the storyteller sees right now</summary>
      <div class="jpreview">${preview.context?safe(preview.context):'<em>Nothing from memory yet — it fills as the story goes on or when you save facts below.</em>'}</div>
      <div class="jrow"><input data-jpreview placeholder="Try a message to see what would be recalled, e.g. “I ask Marta about the ring”" value="${safe(J.previewQuery)}"><button type="button" class="ghost" data-jact="mem-preview">Check</button></div></details>
      ${jMemoryForm(null)}`:`<div class="jbar"><button type="button" class="ghost" data-jact="mem-view" data-view="story">← Back to this story's memories</button><small>Older automatic memories not tied to any story. Bring back the ones that belong here.</small></div>`}
    <div class="jchips">${types.map(t=>`<button type="button" class="jtag${J.memType===t?' on':''}" data-jact="mem-type" data-type="${t}">${t||'all'}</button>`).join('')}</div>
    ${data.items.length?data.items.map(m=>jMemoryCard(m,J.memView==='legacy')).join(''):jempty(J.q||J.memType?'No memories match.':J.memView==='legacy'?'Nothing left over.':'No memories yet.')}
    ${J.memView==='story'&&legacy?`<div class="jbar"><button type="button" class="ghost" data-jact="mem-view" data-view="legacy">Older memories (${legacy})</button><small>Automatic memories saved before stories were separated.</small></div>`:''}`;
}

/* ── People ───────────────────────────────────────────────────────── */
function jTrustColor(t){return `hsl(${Math.round(t*1.2)},62%,46%)`;}
async function jPeople(seq){
  const data=await api(`/api/journal/people?session_id=${jenc(jsid())}&character_id=${state.characterId||''}`);
  if(seq!==J.seq)return;
  const people=data.items.filter(p=>jfilterWords(`${p.name} ${p.bond} ${p.mood} ${p.facts.join(' ')}`));
  jbody().innerHTML=`<p class="jintro">Everyone you have dealt with in this story, how they feel about you, and what you know about them. Trust changes with what you say and do.</p>
    ${people.map(p=>`<article class="jcard">
      <div class="jcard-head"><b>${safe(p.name)}</b>${p.bond?`<span class="jchip">${safe(p.bond.replace('_',' '))}</span>`:''}${p.mood?`<span class="jchip">${safe(p.mood)}</span>`:''}${p.interactions?`<small>${p.interactions} exchanges</small>`:''}</div>
      ${p.trust==null?'':`<div class="jprogress" title="Trust ${p.trust}/100"><span style="width:${p.trust}%;background:${jTrustColor(p.trust)}"></span></div><small>Trust ${p.trust}/100</small>`}
      ${p.facts.length?`<ul class="jlist">${p.facts.slice(0,6).map(f=>`<li>${safe(f)}</li>`).join('')}</ul>`:''}
      ${p.events.length?`<div class="jtags">${p.events.map(e=>`<span class="jchip" title="${safe(e.note||'')}">${safe(e.sentiment)} ${e.trust_delta>0?'+':''}${e.trust_delta}</span>`).join('')}</div>`:''}
      <form class="jform jinline" data-jform="npc-fact" data-name="${safe(p.name)}"><input name="fact" placeholder="Add something you learned about ${safe(p.name)}" maxlength="300"><button class="ghost">Add</button></form>
    </article>`).join('')||jempty(J.q?'No one matches.':'No one yet. People appear once you talk to them.')}`;
}

/* ── Moments ──────────────────────────────────────────────────────── */
async function jMoments(seq){
  const items=await api(`/api/chat/moments?session_id=${jenc(jsid())}`);
  if(seq!==J.seq)return;
  const list=items.filter(m=>jfilterWords(m.content));
  jbody().innerHTML=`<p class="jintro">Key moments you starred in the chat (hover a message and press ⭐). Keep the ones that matter as notes or memories.</p>
    ${list.map(m=>`<article class="jcard"><p class="jtext">${safe(String(m.content).slice(0,700))}</p>
      <div class="jrow"><small>${m.role==='user'?'You':'Storyteller'} · ${jdate(m.created_at)}</small><span class="jbtns">
      <button type="button" class="ghost" data-jact="moment-note" data-id="${m.id}">Add to notes</button>
      <button type="button" class="ghost" data-jact="moment-memory" data-id="${m.id}">Remember</button>
      <button type="button" class="ghost" data-jact="moment-unstar" data-id="${m.id}">Remove</button></span></div></article>`).join('')||jempty(J.q?'No moments match.':'No starred moments yet.')}`;
}

/* ── Actions ──────────────────────────────────────────────────────── */
async function jDo(label,fn){
  try{await fn();}catch(e){toast(e.message||`${label} failed`);}
  renderJournal();
}
async function jAction(el){
  const act=el.dataset.jact,id=+el.dataset.id,idx=+el.dataset.idx;
  switch(act){
    case 'q-generate':{el.disabled=true;el.textContent='Writing…';await generateQuest();return renderJournal();}
    case 'q-complete':await completeQuest(idx);return renderJournal();
    case 'q-abandon':if(!confirm('Abandon this quest?'))return;await abandonQuest(idx);return renderJournal();
    case 'q-progress':{const q=state.quests[idx];if(!q)return;return jDo('Update',async()=>{if(q.id)await api(`/api/quests/${q.id}/progress`,jsend('POST',{progress:+el.dataset.n}));q.progress=+el.dataset.n;renderQuests();});}
    case 'note-edit':J.editing={kind:'note',id};return renderJournal();
    case 'mem-edit':J.editing={kind:'memory',id};return renderJournal();
    case 'cancel-edit':J.editing=null;return renderJournal();
    case 'note-pin':return jDo('Pin',()=>api(`/api/journal/notes/${id}`,jsend('PATCH',{pinned:el.dataset.pinned==='1'})));
    case 'note-delete':if(!confirm('Delete this note?'))return;return jDo('Delete',()=>api(`/api/journal/notes/${id}`,{method:'DELETE'}));
    case 'note-tag':J.noteTag=el.dataset.tag===J.noteTag?'':el.dataset.tag;return renderJournal();
    case 'recap':{el.disabled=true;const stop=startGenTimer(el,'Writing the recap');try{await api('/api/journal/recap',jsend('POST',{session_id:jsid()}));toast('Recap added to your notes');}catch(e){toast(e.message);}stop();return renderJournal();}
    case 'mem-pin':return jDo('Pin',()=>api(`/api/journal/memory/${id}`,jsend('PATCH',{pinned:el.dataset.pinned==='1'})));
    case 'mem-delete':if(!confirm('Forget this memory? The storyteller will no longer recall it.'))return;return jDo('Forget',()=>api(`/api/journal/memory/${id}`,{method:'DELETE'}));
    case 'mem-adopt':return jDo('Restore',()=>api(`/api/journal/memory/${id}/adopt?session_id=${jenc(jsid())}`,{method:'POST'}));
    case 'mem-type':J.memType=el.dataset.type;return renderJournal();
    case 'mem-view':J.memView=el.dataset.view;J.memType='';return renderJournal();
    case 'mem-preview':J.previewQuery=document.querySelector('[data-jpreview]').value.trim();return renderJournal();
    case 'moment-unstar':return jDo('Remove',()=>api(`/api/chat/messages/${id}/moment`,{method:'DELETE'}));
    case 'moment-note':case 'moment-memory':{
      const m=(await api(`/api/chat/moments?session_id=${jenc(jsid())}`)).find(x=>x.id===id);if(!m)return;
      return jDo('Save',async()=>{
        if(act==='moment-note')await api('/api/journal/notes',jsend('POST',{session_id:jsid(),title:'Key moment',body:m.content,tags:['moment']}));
        else await api('/api/journal/memory',jsend('POST',{session_id:jsid(),fact:String(m.content).slice(0,600),memory_type:'episodic',level:'important'}));
        toast(act==='moment-note'?'Added to notes':'The storyteller will remember this');
      });}
  }
}
async function jSubmit(form){
  const kind=form.dataset.jform,fd=new FormData(form),id=form.dataset.id;
  if(kind==='note'){
    const body={title:fd.get('title'),body:fd.get('body'),tags:String(fd.get('tags')||''),kind:fd.get('kind')};
    return jDo('Save',async()=>{
      if(id)await api(`/api/journal/notes/${id}`,jsend('PATCH',body));
      else await api('/api/journal/notes',jsend('POST',{...body,session_id:jsid()}));
      J.editing=null;
    });
  }
  if(kind==='memory'){
    return jDo('Save',async()=>{
      if(id)await api(`/api/journal/memory/${id}`,jsend('PATCH',{fact:fd.get('fact'),memory_type:fd.get('memory_type'),level:fd.get('level')}));
      else await api('/api/journal/memory',jsend('POST',{session_id:jsid(),fact:fd.get('fact'),memory_type:fd.get('memory_type'),level:fd.get('level'),pinned:fd.has('pinned'),shared:fd.has('shared'),character_name:state.sheet?.name||''}));
      J.editing=null;
    });
  }
  if(kind==='npc-fact'){
    const fact=String(fd.get('fact')||'').trim();if(!fact)return;
    return jDo('Save',()=>api('/api/npc-memory',jsend('POST',{character_id:state.characterId||0,npc_name:form.dataset.name,fact,session_id:jsid()})));
  }
}

document.addEventListener('DOMContentLoaded',()=>{
  const drawer=$('#journalDrawer');if(!drawer)return;
  $('#journalClose').onclick=closeJournal;
  $('#journalTabs').onclick=e=>{const b=e.target.closest('[data-jtab]');if(!b)return;J.tab=b.dataset.jtab;J.q='';J.editing=null;renderJournal();};
  let searchTimer=null;
  $('#journalSearch').oninput=e=>{J.q=e.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(()=>{const seq=++J.seq;({quests:jQuests,notes:jNotes,memory:jMemory,people:jPeople,moments:jMoments}[J.tab])(seq).catch(()=>{});},200);};
  jbody().addEventListener('click',e=>{const el=e.target.closest('[data-jact]');if(!el||el.tagName==='SELECT')return;e.preventDefault();jAction(el);});
  jbody().addEventListener('change',e=>{
    const el=e.target;
    if(el.dataset.jfilter==='noteKind'){J.noteKind=el.value;renderJournal();}
    else if(el.dataset.jact==='mem-level'){jDo('Update',()=>api(`/api/journal/memory/${el.dataset.id}`,jsend('PATCH',{level:el.value})));}
  });
  jbody().addEventListener('submit',e=>{e.preventDefault();jSubmit(e.target);});
  jbody().addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.matches('[data-jpreview]')){e.preventDefault();J.previewQuery=e.target.value.trim();renderJournal();}});
  document.addEventListener('keydown',e=>{
    const tag=document.activeElement?.tagName;
    if(e.key.toLowerCase()!=='j'||e.ctrlKey||e.metaKey||e.altKey||['INPUT','TEXTAREA','SELECT'].includes(tag)||document.activeElement?.isContentEditable)return;
    if(!document.querySelector('#gameArea')||$('#gameArea').hidden)return;
    toggleJournal();
  });
});
