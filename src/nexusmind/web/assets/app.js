const form=document.querySelector('#chat'),conversation=document.querySelector('#conversation'),statusLine=document.querySelector('#status'),send=document.querySelector('#send');
let config;
function node(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
const messages={no_results:'Aucune donnée pour cette version ou cette langue.',needs_clarification:'Précise le champion, le sort ou l’identifiant de l’objet souhaité.',out_of_scope:'Les données disponibles ne suffisent pas pour cette question.',insufficient_evidence:'Les passages trouvés ne permettent pas une réponse fiable.',quota_exceeded:'Le quota de réponses est atteint.',unavailable:'Le coach est momentanément indisponible.',invalid_generation:'La réponse n’a pas passé la vérification des références.'};
function show(result){
  const card=node('article');
  if(result.status==='answered'){
    for(const claim of result.claims){
      card.append(node('div',claim.kind==='sourced_fact'?'Fait sourcé':'Hypothèse de coaching',claim.kind==='sourced_fact'?'tag':'tag hypothesis'),node('p',claim.text));
    }
    if(result.exercise)card.append(node('h2','À essayer'),node('p',result.exercise));
  }else card.append(node('h2',messages[result.status]||'La demande n’a pas pu être traitée.'));
  if(result.candidates?.length)card.append(node('p',result.candidates.map(x=>`${x.entity_type} : ${x.entity_id}`).join(' · ')));
  if(result.sources?.length){
    const sources=node('div',undefined,'sources');sources.append(node('h2','Sources'));
    for(const source of result.sources){
      const a=node('a',`${source.source_name} · ${source.title||source.entity_id} · ${source.section}`);
      const url=new URL(source.source_url);
      if(url.protocol==='https:'){a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';}
      sources.append(a,node('p',`Version : ${source.patch==='unversioned'?'non liée à un patch':source.patch} · ${source.locale} · collecté le ${source.retrieved_at}`,'muted'));
      if(source.source_revision)sources.append(node('p',`Révision : ${source.source_revision}`,'muted'));
      if(source.attribution)sources.append(node('p',source.attribution,'muted'));
      if(source.license_url){
        const rights=node('a',source.license_name||'Conditions de réutilisation');
        const rightsUrl=new URL(source.license_url);
        if(rightsUrl.protocol==='https:'){rights.href=rightsUrl.href;rights.target='_blank';rights.rel='noopener noreferrer';}
        sources.append(rights);
      }
      sources.append(node('p',source.text,'muted'));
    }
    card.append(sources);
  }
  if(result.limitations?.length){
    const limits=node('details',undefined,'limits');limits.append(node('summary','Limites de cette réponse'));
    for(const text of result.limitations)limits.append(node('p',text));card.append(limits);
  }
  conversation.append(card);card.scrollIntoView({behavior:'smooth',block:'nearest'});
}
fetch('/api/config').then(r=>r.json()).then(data=>{config=data;document.querySelector('#patch').textContent=`Corpus ${data.patch} · ${data.locale}`;}).catch(()=>{statusLine.textContent='Impossible de joindre le coach.';send.disabled=true;});
form.addEventListener('submit',async event=>{event.preventDefault();if(!config)return;const question=document.querySelector('#question').value.trim();if(!question)return;conversation.append(node('article',question,'question'));send.disabled=true;statusLine.textContent='Le coach prépare une réponse sourcée…';try{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:question,patch:config.patch,locale:config.locale,level:document.querySelector('#level').value,corpus:document.querySelector('#corpus').value})});const result=await response.json();show(result);statusLine.textContent='';}catch{statusLine.textContent='Connexion interrompue. Tu peux réessayer.';}finally{send.disabled=false;}});
const matchForm=document.querySelector('#postgame'),matchButton=document.querySelector('#analyze'),matchStatus=document.querySelector('#match-status'),matchResult=document.querySelector('#match-result');
const metricNames={duration:'Durée',kills:'Éliminations',deaths:'Morts',assists:'Assistances',cs:'Farm total',cs_per_minute:'Farm par minute',kda:'Ratio KDA',kill_participation_percent:'Participation aux éliminations',gold_earned:'Or gagné',vision_score:'Score de vision',champion_damage:'Dégâts aux champions',gold_difference_near_10m:'Écart d’or vers 10 min',cs_difference_near_10m:'Écart de farm vers 10 min',enemy_objectives_after_death:'Objectifs ennemis dans les 90 s après une mort'};
const unitNames={seconds:'s',kills:'',deaths:'',assists:'',minions:'CS','minions/minute':'CS/min',ratio:'',percent:'%',gold:'or',score:'',damage:'',events:'événements'};
function showMatch(report){matchResult.replaceChildren();if(!['ok','partial'].includes(report.status)){const message={authentication_failed:'Riot refuse l’accès aux données. Vérifie la configuration de la clé sur le serveur.',rate_limited:'Le quota Riot est atteint. Attends avant de réessayer.',no_matches:'Aucune partie disponible dans cette région.',not_found:'Joueur ou partie introuvable.'}[report.status]||'Les données de partie sont momentanément indisponibles.';matchResult.append(node('p',message));return;}const card=node('article');card.append(node('h2',`${report.champion||'Champion non renseigné'} · ${report.won===true?'Victoire':report.won===false?'Défaite':'Résultat non renseigné'}`),node('p',`Version de partie ${report.game_version||'non renseignée'}`,'muted'));const grid=node('div',undefined,'metrics');for(const [key,metric] of Object.entries(report.metrics)){const item=node('div',undefined,'metric');item.append(node('span',metricNames[key]||key),node('strong',metric.value===null?'Non disponible':`${metric.value} ${unitNames[metric.unit]??metric.unit}`));if(metric.timestamp_ms!==null)item.append(node('small',`Observation à ${(metric.timestamp_ms/60000).toFixed(2)} min`));grid.append(item);}card.append(grid);if(report.death_timestamps_ms.length)card.append(node('p','Morts à revoir : '+report.death_timestamps_ms.map(t=>`${Math.floor(t/60000)}:${String(Math.floor(t/1000)%60).padStart(2,'0')}`).join(' · ')));for(const tip of report.recommendations)card.append(node('p',tip));for(const limit of report.limitations)card.append(node('p',limit,'muted'));card.append(node('div',report.sources.map(s=>`${s.source} · collecté le ${s.retrieved_at}`).join(' | '),'sources muted'));matchResult.append(card);}
matchForm.addEventListener('submit',async event=>{event.preventDefault();matchButton.disabled=true;matchStatus.textContent='Récupération et analyse de ta partie…';try{const response=await fetch('/api/postgame',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({riot_id:document.querySelector('#riot-id').value.trim(),region:document.querySelector('#region').value})});showMatch(await response.json());matchStatus.textContent='';}catch{matchStatus.textContent='Connexion interrompue.';}finally{matchButton.disabled=false;}});
