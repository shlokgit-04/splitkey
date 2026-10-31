async function refresh(){
  const r = await (await fetch('/api/state')).json();
  document.getElementById('vstatus').textContent = r.vaults.length ? `${r.shares} vaults · threshold ${r.threshold}` : 'no key on file';
  const vg = document.getElementById('vaults'); vg.innerHTML = '';
  r.vaults.forEach(v => {
    const on = r.collected.includes(v.id);
    const d = document.createElement('div'); d.className = 'vault' + (on ? ' collected' : '');
    d.innerHTML = `<h3>${v.label}</h3><div class="share">share #${v.x}: ${v.share_hex.slice(0,10)}…</div><button data-id="${v.id}">${on ? 'collected ✓' : 'collect share'}</button>`;
    vg.appendChild(d);
  });
  vg.querySelectorAll('button').forEach(b => b.onclick = async () => { await fetch('/api/collect/' + b.dataset.id, {method:'POST'}); refresh(); });
  const need = r.collected.length, total = r.threshold;
  document.getElementById('meterfill').style.width = Math.min(100, need / total * 100) + '%';
  document.getElementById('metertext').textContent = `${need} / ${total} shares collected`;
  document.getElementById('audit').innerHTML = r.audit.map(a => `<li><span>${a.ts}</span><b>${a.event}</b> ${a.detail}</li>`).join('');
  document.getElementById('proof').innerHTML = r.vaults.length
    ? r.vaults.map(v => `<li><span>${v.label}</span>holds 1 of ${r.threshold} needed shares · share alone reveals nothing</li>`).join('')
    : '<li>split a key first</li>';
}
document.getElementById('btn-split').onclick = async () => {
  const key = document.getElementById('key').value;
  if (!key) return alert('paste a master key first');
  await fetch('/api/split', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key})});
  document.getElementById('key').value = ''; refresh();
};
document.getElementById('btn-demo').onclick = async () => {
  await fetch('/api/demo', {method:'POST'}); refresh();
};
document.getElementById('btn-run').onclick = async () => {
  const out = document.getElementById('agent-out');
  const need = !document.querySelector('.vault.collected');
  const r0 = await (await fetch('/api/state')).json();
  if (!r0.enough) {
    for (const v of r0.vaults) { if (r0.collected.length < r0.threshold) await fetch('/api/collect/' + v.id, {method:'POST'}); }
    await fetch('/api/reconstruct', {method:'POST'});
  }
  const r = await (await fetch('/api/agent/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: document.getElementById('msg').value})})).json();
  if (r.ok) { out.classList.remove('hidden'); out.textContent = 'ciphertext: ' + r.full; } else { out.classList.remove('hidden'); out.textContent = r.error; }
  refresh();
};
document.getElementById('btn-zero').onclick = async () => { await fetch('/api/zeroize', {method:'POST'}); refresh(); };
refresh();
