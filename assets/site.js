fetch('data/reviews.json')
.then(r=>r.json())
.then(data=>{
  const normalize=s=>(s||'')
    .toString()
    .normalize('NFKD')
    .replace(/[’‘]/g,"'")
    .replace(/[^a-zA-Z0-9]+/g,' ')
    .toLowerCase()
    .trim();

  const cleanTitle=s=>(s||'').replace(/^(the|a|an)\s+/i,'');
  data.sort((a,b)=>
    cleanTitle(a.title).localeCompare(cleanTitle(b.title),undefined,{sensitivity:'base'}) ||
    a.title.localeCompare(b.title,undefined,{sensitivity:'base'})
  );

  const q=document.getElementById('q');
  const box=document.getElementById('reviews');
  const count=document.getElementById('count');

  const prettyDate=s=>{
    if(!s) return 'Publication date to be established';
    const m=s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if(!m) return s;
    const d=new Date(Number(m[1]),Number(m[2])-1,Number(m[3]));
    return d.toLocaleDateString(undefined,{year:'numeric',month:'long',day:'numeric'});
  };

  function haystack(r){
    return normalize([
      r.title,
      r.id,
      r.rating,
      r.sermon_spiritual_topic,
      r.primary_scripture,
      ...(r.scripture_references||[]),
      r.publication_date||''
    ].join(' '));
  }

  function scriptureSlug(s){
    return normalize(s).replace(/\s+/g,'-');
  }

  function draw(){
    const terms=normalize(q.value).split(/\s+/).filter(Boolean);
    const rows=data.filter(r=>{
      if(!terms.length) return true;
      const h=haystack(r);
      return terms.every(t=>h.includes(t));
    });

    count.textContent=rows.length+' review'+(rows.length===1?'':'s');
    if(!rows.length){
      box.innerHTML='<p class="empty-state">No matching reviews. Try fewer words, a film title, a Bible reference, or a sermon topic.</p>';
      return;
    }

    box.innerHTML=rows.map(r=>{
      const scriptures=(r.scripture_references||[]).map(s=>
        `<a href="scripture.html#${scriptureSlug(s)}">${s}</a>`
      ).join(' · ');
      return `<article class="card">
        <p class="kicker">${r.id} · ${r.verification_status}</p>
        <h2><a href="${r.page}">${r.title}</a></h2>
        <p>${prettyDate(r.publication_date)} · ${r.rating||'Rating not recorded'}</p>
        <p>${r.sermon_spiritual_topic||''}</p>
        <p class="scriptures">${scriptures}</p>
      </article>`;
    }).join('');
  }

  q.addEventListener('input',draw);
  draw();
});