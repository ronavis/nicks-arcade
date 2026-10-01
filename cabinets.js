'use strict';
let cabinets = [], selectedCabinet = null, assignmentGame = null, expectedCabinets = [], editingCabinet = null;
const cabinetPicture = c => c.photoId ? `${apiBase}/cabinet-photos/${c.photoId}` : window.ARCADE_CABINET_ART?.[c.code]?.image || 'images/cabinet-default.png';
const cabinetJSON = (method, body) => ({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
async function refreshCabinets() { cabinets = (await api('/admin/cabinets')).cabinets; }
function cabinetImage(c) { const im=node('img','cabinet-photo'); im.src=cabinetPicture(c); im.alt=c.name; im.loading='lazy'; return im; }
function cabinetButton(text, action, style='secondary') { const b=node('button',style,text); b.type='button'; b.addEventListener('click',action); return b; }
function renderCabinets() {
  const query=$('cabinet-search').value.trim().toLowerCase();
  const filtered=cabinets.filter(c=>`${c.name} ${c.code}`.toLowerCase().includes(query));
  $('cabinet-grid').replaceChildren(...filtered.map(c=>{
    const b=cabinetButton('',()=>{selectedCabinet=c.id; renderCabinets(); $('cabinets-dialog').scrollTop=0; $('cabinet-detail-heading').focus({preventScroll:true});},'cabinet-tile');
    b.setAttribute('aria-pressed',String(c.id===selectedCabinet));
    b.append(cabinetImage(c),node('strong','',c.name),node('small','',`${c.gameIds.length} assigned game${c.gameIds.length===1?'':'s'}`)); return b;
  }));
  if (!filtered.length) $('cabinet-grid').append(node('p','','No cabinets match. Try another name or add a cabinet.'));
  const c=cabinets.find(c=>c.id===selectedCabinet);
  $('cabinet-layout').classList.toggle('has-selection',!!c);
  const panel=$('cabinet-detail'); panel.hidden=!c; panel.replaceChildren(); if(!c)return;
  const back=cabinetButton('Back to cabinets',()=>{selectedCabinet=null;renderCabinets();$('cabinet-search').focus();},'text-button cabinet-back');
  const title=node('h3','',c.name); title.id='cabinet-detail-heading'; title.tabIndex=-1;
  const heading=node('div','cabinet-detail-top'); heading.append(cabinetImage(c),title);
  const actions=node('div','cabinet-actions'); actions.append(cabinetButton('Edit cabinet',()=>openCabinetEditor(c)),cabinetButton('Add games',()=>openCabinetGames(c),'primary'));
  panel.append(back,heading);
  if(!c.photoId&&window.ARCADE_CABINET_ART?.[c.code]?.note)panel.append(node('p','small',window.ARCADE_CABINET_ART[c.code].note));
  panel.append(actions,node('h4','','Games on this cabinet'));
  const games=c.gameIds.map(gameById).filter(Boolean);
  if(!games.length)panel.append(node('p','cabinet-empty','No games assigned yet. Add games from your collection or the marquee catalog.'));
  for(const game of games){
    const row=node('div','cabinet-game-row'),art=node('img');art.src=artworkUrl(game);art.alt='';
    const info=node('div');const other=cabinets.filter(other=>other.id!==c.id&&other.gameIds.includes(game.id)).length;
    info.append(node('strong','',game.title),node('small','',other?`Also on ${other} other cabinet${other===1?'':'s'}`:'Only on this cabinet'));
    if(!game.record)info.append(node('small','','Be the first to set a record'));
    if(!game.eligible)info.append(node('small','','Outside eligible game collection'));
    const manage=cabinetButton('Assign cabinets',()=>openCabinetAssignment(game),'text-button');
    row.append(art,info,manage);panel.append(row);
  }
  panel.append(node('p','small','Assignments do not change scores or game eligibility.'));
}
async function openCabinets(){
  if(!state.user?.admin)return;
  if(document.fullscreenElement)await document.exitFullscreen();
  $('account-dialog').close(); $('cabinet-message').textContent='Loading cabinets…'; $('cabinets-dialog').showModal();
  try{await refreshCabinets();selectedCabinet=null;renderCabinets();$('cabinet-message').textContent='';}catch(e){$('cabinet-message').textContent=e.message;}
}
function openCabinetEditor(c=null){
  editingCabinet=c?{...c}:null;
  $('cabinet-editor-heading').textContent=c?'Edit cabinet':'Add cabinet';
  $('cabinet-name').value=c?.name||'';$('cabinet-file').value='';$('cabinet-editor-message').textContent='';
  $('cabinet-editor').showModal();
}
$('cabinet-form').addEventListener('submit',async event=>{
  event.preventDefault(); const button=$('save-cabinet');button.disabled=true;$('close-cabinet-editor').disabled=true;
  const file=$('cabinet-file').files[0];
  try{
    if(file&&file.size>40*1024*1024)throw new Error('Choose a photo under 40 MB.');
    const r=await api(`/admin/cabinets${editingCabinet?'/'+encodeURIComponent(editingCabinet.id):''}`,cabinetJSON(editingCabinet?'PATCH':'POST',{name:$('cabinet-name').value,revision:editingCabinet?.revision}));
    cabinets=r.cabinets;selectedCabinet=r.id;$('cabinet-search').value='';editingCabinet={...cabinets.find(c=>c.id===r.id)};
    if(file){
      const body=new FormData();body.set('photo',file);body.set('revision',editingCabinet.revision);
      $('cabinet-editor-message').textContent='Cabinet saved. Uploading photo…';
      try{cabinets=(await api(`/admin/cabinets/${r.id}/photo`,{method:'POST',body})).cabinets;}
      catch(e){renderCabinets();throw new Error(`Cabinet name saved; photo was not saved. ${e.message}`);}
    }
    renderCabinets();$('cabinet-editor').close();$('cabinet-message').textContent='Cabinet saved.';
  }catch(e){$('cabinet-editor-message').textContent=e.message;}finally{button.disabled=false;$('close-cabinet-editor').disabled=false;}
});
$('cabinet-editor').addEventListener('cancel',e=>{if($('save-cabinet').disabled)e.preventDefault();});
async function openCabinetAssignment(game){
  if(!state.user?.admin)return;
  assignmentGame=game;$('assignment-message').textContent='Loading…';$('assignment-list').replaceChildren();$('save-assignment').disabled=true;$('assignment-heading').textContent=`${game.title}: cabinets`; $('assignment-dialog').showModal();
  try{
    await refreshCabinets();expectedCabinets=cabinets.filter(c=>c.gameIds.includes(game.id)).map(c=>c.id);
    $('assignment-list').replaceChildren(...cabinets.map(c=>{
      const label=node('label','cabinet-check'),check=node('input');check.type='checkbox';check.value=c.id;check.checked=expectedCabinets.includes(c.id);
      label.append(check,cabinetImage(c),node('span','',c.name));return label;
    }));
    $('assignment-message').textContent=cabinets.length?'':'Add a cabinet in Manage cabinets first.';$('save-assignment').disabled=false;
  }catch(e){$('assignment-message').textContent=e.message;}
}
$('assignment-form').addEventListener('submit',async event=>{
  event.preventDefault();const b=$('save-assignment');b.disabled=true;
  try{
    const cabinetIds=[...$('assignment-list').querySelectorAll('input:checked')].map(c=>c.value);
    cabinets=(await api(`/admin/games/${encodeURIComponent(assignmentGame.id)}/cabinets`,cabinetJSON('PUT',{cabinetIds,expectedCabinetIds:expectedCabinets}))).cabinets;
    renderCabinets();renderArcadeGames();$('assignment-dialog').close();$('cabinet-message').textContent='Cabinet assignments saved. Score history is unchanged.';
  }catch(e){$('assignment-message').textContent=e.message;}finally{b.disabled=false;}
});
let cabinetSearchVersion=0;
function openCabinetGames(c){selectedCabinet=c.id;$('cabinet-game-search').value='';$('cabinet-add-title').textContent=`Add games to ${c.name}`;$('cabinet-add-dialog').showModal(); searchCabinetGames();}
async function searchCabinetGames(){
  const version=++cabinetSearchVersion;const q=$('cabinet-game-search').value.trim();const target=$('cabinet-game-results');target.replaceChildren();$('cabinet-add-message').textContent='';
  const owned=state.allGames.filter(g=>g.title.toLowerCase().includes(q.toLowerCase()));
  const render=(game,isCatalog=false)=>{
    const row=node('div','cabinet-game-row'),img=node('img');img.src=artworkUrl(game);img.alt='';
    const info=node('div');info.append(node('strong','',game.title),node('small','',isCatalog?'Adds to your eligible games too':'In your game collection'));
    const assigned=!isCatalog&&cabinets.find(c=>c.id===selectedCabinet)?.gameIds.includes(game.id);
    const add=cabinetButton(assigned?'Assigned':'Add',async()=>{
      add.disabled=true;
      try{
        let chosen=game;
        if(isCatalog){chosen=(await api('/admin/games',cabinetJSON('POST',{catalogId:game.id}))).game;await refreshBoard();}
        await refreshCabinets();const expected=cabinets.filter(c=>c.gameIds.includes(chosen.id)).map(c=>c.id);
        cabinets=(await api(`/admin/games/${encodeURIComponent(chosen.id)}/cabinets`,cabinetJSON('PUT',{expectedCabinetIds:expected,cabinetIds:[...new Set([...expected,selectedCabinet])]}))).cabinets;
        renderCabinets();add.textContent='Assigned';$('cabinet-add-message').textContent=`${chosen.title} assigned.`;
      }catch(e){$('cabinet-add-message').textContent=e.message;add.disabled=false;}
    });add.disabled=assigned;row.append(img,info,add);target.append(row);
  };
  owned.slice(0,30).forEach(g=>render(g));
  if(q.length<2){$('cabinet-add-message').textContent='Search at least two letters to include the wider marquee catalog.';return;}
  try{
    const result=await api(`/game-catalog?q=${encodeURIComponent(q)}`);if(version!==cabinetSearchVersion)return;
    const normalize=t=>t.toLowerCase().replace(/[^a-z0-9]/g,'');const keys=new Set(state.allGames.map(g=>normalize(g.title)));
    result.games.filter(g=>!keys.has(normalize(g.title))).forEach(g=>render(g,true));
    if(!target.children.length)$('cabinet-add-message').textContent='No matching games. Try another title.';
  }catch(e){if(version===cabinetSearchVersion)$('cabinet-add-message').textContent=e.message;}
}
let cabinetSearchTimer;
$('cabinet-game-search').addEventListener('input',()=>{++cabinetSearchVersion;clearTimeout(cabinetSearchTimer);cabinetSearchTimer=setTimeout(searchCabinetGames,250);});
$('cabinet-search').addEventListener('input',renderCabinets);
$('add-cabinet').addEventListener('click',()=>openCabinetEditor());
$('tv-cabinets-button').addEventListener('click',openCabinets);$('account-cabinets').addEventListener('click',openCabinets);
for(const [button,dialog] of [['close-cabinets','cabinets-dialog'],['close-cabinet-editor','cabinet-editor'],['close-assignment','assignment-dialog'],['close-cabinet-add','cabinet-add-dialog']]) $(button).addEventListener('click',()=>$(dialog).close());

let inventoryPreview=null, inventoryCSV='', inventoryVersion=0;
function resetInventoryPreview(){++inventoryVersion;inventoryPreview=null;inventoryCSV='';$('commit-inventory-import').disabled=true;$('inventory-import-results').replaceChildren();$('inventory-import-message').textContent='';}
$('open-inventory-import').addEventListener('click',()=>{resetInventoryPreview();$('inventory-import-file').value='';$('inventory-import-dialog').showModal();});
$('close-inventory-import').addEventListener('click',()=>{$('inventory-import-dialog').close();resetInventoryPreview();});
$('inventory-import-file').addEventListener('change',resetInventoryPreview);
$('preview-inventory-import').addEventListener('click',async()=>{
  resetInventoryPreview();const version=inventoryVersion;const file=$('inventory-import-file').files[0];
  try{
    if(!file)throw new Error('Choose your Excel or CSV file first.');
    const excel=file.name.toLowerCase().endsWith('.xlsx');
    if(!excel&&!file.name.toLowerCase().endsWith('.csv'))throw new Error('Choose an Excel .xlsx workbook or CSV file.');
    if(file.size>(excel?2097152:262144))throw new Error(excel?'Choose an Excel workbook under 2 MB.':'Choose a CSV file under 256 KB.');
    $('inventory-import-message').textContent='Checking your spreadsheet…';
    let result;
    if(excel){const body=new FormData();body.append('mode','preview');body.append('file',file);result=await api('/admin/inventory-import',{method:'POST',body});}
    else result=await api('/admin/inventory-import',cabinetJSON('POST',{mode:'preview',csv:await file.text()}));
    if(version!==inventoryVersion)return;
    inventoryCSV=result.csv;inventoryPreview=result;
    const target=$('inventory-import-results');
    for(const error of result.errors)target.append(node('p','import-row-error',error));
    for(const row of result.rows){
      const line=node('div','cabinet-game-row'),im=node('img');im.src=artworkUrl(gameById(row.id)||row);im.alt='';im.loading='lazy';
      const text=node('div');text.append(node('strong','',`${row.row}. ${row.title}`),node('small','',`${row.action} · ${row.kind==='time'?'Lowest time wins':'Highest score wins'}`),node('small','',row.cabinets.join(', ')||'No cabinet assigned'));
      if(!row.eligible)text.append(node('small','','Remains outside the eligible collection'));
      line.append(im,text);target.append(line);
    }
    const c=result.counts;
    $('inventory-import-message').textContent=result.errors.length?`Fix ${result.errors.length} row error(s) and preview again. Nothing has been saved.`:`${c.games} new games · ${c.cabinets} new cabinets · ${c.assignments} new assignments. ${Object.values(c).some(Boolean)?'Review the list, then import.':'Everything is already in your collection.'}`;
    $('commit-inventory-import').disabled=result.errors.length>0||!Object.values(c).some(Boolean);
  }catch(e){if(version===inventoryVersion)$('inventory-import-message').textContent=e.message;}
});
$('commit-inventory-import').addEventListener('click',async()=>{
  if(!inventoryPreview)return;
  const controls=['commit-inventory-import','preview-inventory-import','inventory-import-file','close-inventory-import'];controls.forEach(id=>$(id).disabled=true);
  try{
    await api('/admin/inventory-import',cabinetJSON('POST',{mode:'commit',csv:inventoryCSV,previewHash:inventoryPreview.previewHash}));
    inventoryPreview=null;await refreshBoard();await refreshCabinets();renderCabinets();renderArcadeGames();
    $('inventory-import-message').textContent='Import complete. Games and cabinets are ready; score history is unchanged.';
    $('cabinet-message').textContent='Spreadsheet imported.';
  }catch(e){inventoryPreview=null;$('inventory-import-message').textContent=`${e.message} Preview again to check what remains to import.`;}
  finally{controls.filter(id=>id!=='commit-inventory-import').forEach(id=>$(id).disabled=false);}
});

function renderFeaturedCabinets(game) {
  const target=$('featured-cabinets'); target.replaceChildren();
  const assigned=game?.cabinets||[];
  target.classList.toggle('unassigned',!assigned.length);
  if(!assigned.length)return;
  target.append(node('p','cabinet-strip-label','PLAY IT ON'));
  const row=node('div','cabinet-strip-row');
  for(const c of assigned.slice(0,4)){
    const button=cabinetButton('',()=>openWhereToPlay(game),'featured-cabinet');
    const im=cabinetImage(c);im.loading='eager';
    const crop=node('div','cabinet-crop');crop.dataset.cabinet=c.code||'';
    const framing=!c.photoId&&window.ARCADE_CABINET_ART?.[c.code]?.crop;
    if(framing){crop.style.setProperty('--cabinet-fit',framing.fit);crop.style.setProperty('--cabinet-scale',framing.scale);crop.style.setProperty('--cabinet-origin-y',`${framing.originY}%`);}
    crop.append(im);button.append(crop,node('span','',c.name.replace(/ Cabinet$/,'')));
    button.setAttribute('aria-label',`Find ${game.title} on ${c.name}`);row.append(button);
  }
  target.append(row);
  if(assigned.length>4)target.append(cabinetButton(`View all ${assigned.length} cabinets`,()=>openWhereToPlay(game),'cabinet-strip-more'));
}
function openWhereToPlay(game) {
  $('where-to-play-heading').textContent=`Where to play ${game.title}`;
  $('where-to-play-list').replaceChildren(...game.cabinets.map(c=>{
    const card=node('div','where-cabinet');card.append(cabinetImage(c),node('strong','',c.name));return card;
  }));
  $('where-to-play-dialog').showModal();
}
$('close-where-to-play').addEventListener('click',()=>$('where-to-play-dialog').close());
