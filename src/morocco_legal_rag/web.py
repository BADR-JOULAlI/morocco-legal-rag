"""Self-contained industrial web interface for the FastAPI application."""

INDEX_HTML = r"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morocco Legal RAG</title>
  <style>
    :root { --bg:#0B0C0A; --panel:#000000; --ink:#F4F4F0; --muted:#A4A69F; --line:#33352F; --signal:#FFB800; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--ink); font-family:"IBM Plex Mono","JetBrains Mono",Consolas,monospace; }
    header { display:grid; grid-template-columns:2fr 1fr; border-bottom:1px solid var(--line); min-height:210px; }
    .masthead { padding:28px; border-right:1px solid var(--line); }
    h1 { margin:0; color:var(--signal); font-size:clamp(42px,8vw,112px); line-height:.82; letter-spacing:-.08em; }
    .status { padding:28px; display:flex; flex-direction:column; justify-content:flex-end; gap:8px; }
    .status strong { color:var(--signal); }
    main { display:grid; grid-template-columns:minmax(0,3fr) minmax(320px,2fr); min-height:calc(100vh - 210px); }
    .workspace,.evidence { padding:28px; }
    .workspace { border-right:1px solid var(--line); }
    .evidence { border-left:2px solid var(--signal); background:var(--panel); }
    label { display:block; margin:0 0 8px; color:var(--muted); }
    textarea,select,input { width:100%; color:var(--ink); background:#000; border:1px solid var(--line); border-radius:0; padding:14px; font:inherit; }
    textarea:focus,select:focus,input:focus { outline:2px solid var(--signal); outline-offset:2px; }
    textarea { min-height:150px; resize:vertical; }
    .controls { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }
    button { width:100%; background:var(--signal); color:#000; border:1px solid var(--signal); border-radius:0; padding:15px; font:700 16px inherit; cursor:pointer; }
    button:disabled { opacity:.5; cursor:wait; }
    h2 { margin:30px 0 14px; font-size:18px; color:var(--signal); }
    #answer { white-space:pre-wrap; line-height:1.65; }
    .source { padding:18px 0; border-bottom:1px solid var(--line); }
    .source h3 { margin:0 0 8px; font-size:15px; }
    .source p { color:var(--muted); line-height:1.5; font-size:13px; }
    .source a { color:var(--signal); word-break:break-all; }
    footer { border-top:1px solid var(--line); color:var(--muted); padding:16px 28px; font-size:12px; }
    @media (max-width:800px) { header,main { grid-template-columns:1fr; } .masthead,.workspace { border-right:0; } .status { border-top:1px solid var(--line); } .evidence { border-left:0; border-top:2px solid var(--signal); } }
  </style>
</head>
<body>
  <header>
    <div class="masthead"><h1>MOROCCO<br>LEGAL RAG</h1></div>
    <div class="status"><span>État du service</span><strong id="status">Vérification…</strong><span id="index-size"></span></div>
  </header>
  <main>
    <section class="workspace">
      <form id="query-form">
        <label for="question">Question sur les documents indexés</label>
        <textarea id="question" required minlength="3" placeholder="Exemple : quel est le délai de rétractation en cas de démarchage ?"></textarea>
        <div class="controls">
          <div><label for="language">Langue</label><select id="language"><option value="fr">Français</option><option value="ar">العربية</option><option value="darija">الدارجة</option></select></div>
          <div><label for="top-k">Passages recherchés</label><input id="top-k" type="number" min="1" max="20" value="5"></div>
        </div>
        <button id="submit" type="submit">Rechercher</button>
      </form>
      <h2>Réponse documentaire</h2>
      <div id="answer" aria-live="polite">Aucune recherche effectuée.</div>
    </section>
    <aside class="evidence">
      <h2>Preuves et sources</h2>
      <div id="sources">Les passages utilisés apparaîtront ici avec leur page et leur URL.</div>
    </aside>
  </main>
  <footer>Information documentaire uniquement — ne constitue pas un avis juridique. Vérifiez toujours le texte officiel et sa version.</footer>
  <script>
    const statusNode=document.querySelector('#status');
    const sizeNode=document.querySelector('#index-size');
    fetch('/health').then(r=>r.json()).then(data=>{statusNode.textContent=data.status.toUpperCase();sizeNode.textContent=`${data.indexed_chunks} passages indexés`;}).catch(()=>{statusNode.textContent='INDISPONIBLE';});
    const form=document.querySelector('#query-form');
    form.addEventListener('submit',async(event)=>{
      event.preventDefault();
      const button=document.querySelector('#submit');
      const answer=document.querySelector('#answer');
      const sources=document.querySelector('#sources');
      button.disabled=true; answer.textContent='Recherche en cours…'; sources.replaceChildren();
      try {
        const response=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.querySelector('#question').value,language:document.querySelector('#language').value,top_k:Number(document.querySelector('#top-k').value)})});
        if(!response.ok) throw new Error(`Erreur HTTP ${response.status}`);
        const data=await response.json(); answer.textContent=data.answer;
        if(!data.citations.length){sources.textContent='Aucune source suffisamment pertinente.';return;}
        for(const citation of data.citations){
          const article=document.createElement('article');article.className='source';
          const title=document.createElement('h3');title.textContent=citation.title;
          const meta=document.createElement('p');meta.textContent=`Page ${citation.page} · couverture lexicale ${(citation.lexical_coverage*100).toFixed(0)} % · score ${citation.score.toFixed(4)}`;
          const excerpt=document.createElement('p');excerpt.textContent=citation.excerpt;
          article.append(title,meta,excerpt);
          if(citation.url){const link=document.createElement('a');link.href=citation.url;link.target='_blank';link.rel='noreferrer';link.textContent='Ouvrir le document officiel';article.append(link);}
          sources.append(article);
        }
      } catch(error) { answer.textContent=error.message; sources.textContent='La recherche n’a pas pu être exécutée.'; }
      finally { button.disabled=false; }
    });
  </script>
</body>
</html>"""
