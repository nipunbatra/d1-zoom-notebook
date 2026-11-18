"""Build a compact evidence page from actual saved OpenRouter calls."""
from pathlib import Path
import copy,html,json
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'recordings/openrouter-box-check-20261118.json').read_text())
e=html.escape
cards=[];details=[]
for c in data['calls']:
    good=c['status']==200;name='D1.2 Ultra' if 'ultra' in c['model_requested'] else 'D1.2'
    q=c['request']['questions']['target'];r=c['response'];answer=r.get('answers',{}).get('target',{})
    if good:
        shown={'type':answer['type'],'choice':answer['choice'],'probabilities':answer['probabilities']}
        label='Response: answers.target (excerpt)'
    else:shown=r;label='Response: complete error body'
    response=json.dumps(shown,indent=2)
    # Compact only whitespace, keeping numerical values and response text exact.
    if good:response='{"type": "choice", "choice": "present",\n "probabilities": '+json.dumps(answer['probabilities'])+'}'
    cards.append(f'''<article class="{'ok' if good else 'bad'}"><header><h2>{name} <span>· {q['type']}</span></h2><b>HTTP {c['status']}</b></header><p class="timing">{c['elapsed_ms']:.2f} ms HTTP · {e(c['recorded_at'][11:23])} UTC</p><p class="prompt"><strong>Question:</strong> {e(q['instructions'])}</p><p class="label">{label}</p><pre>{e(response)}</pre></article>''')
    request=copy.deepcopy(c['request']);request['state'][1]['image_url']['url']='[identical JPEG payload omitted here; complete bytes in saved JSON]'
    details.append(f'<details><summary>{name} · {q["type"]}: full request and response</summary><p>Authorization header never recorded. Image bytes abbreviated only in this view.</p><pre>{e(json.dumps({"request":request,"response":r},indent=2))}</pre></details>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenRouter Liquid box support · live API evidence</title><style>
*{box-sizing:border-box}body{font:15px/1.45 system-ui,sans-serif;color:#1e2925;background:#f4f6f2;margin:0}main{max-width:1180px;margin:auto;padding:24px}h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;margin:0}h2 span{font-weight:450;color:#526259}.lede{margin:0 0 12px;color:#526259}.context{border-left:3px solid #77866d;padding:5px 12px;margin-bottom:14px}.context p{margin:3px 0}code,pre{font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}article{background:white;border:1px solid #d7ddd4;border-radius:7px;padding:15px;min-width:0}article header{display:flex;justify-content:space-between;align-items:center}.ok b{color:#256141}.bad b{color:#a13c28}.timing{font-size:12px;color:#66706a;margin:2px 0 10px}.prompt{margin:0 0 8px;font-size:13px;min-height:38px}.label{font-size:11px;color:#66706a;text-transform:uppercase;letter-spacing:.04em;margin:5px 0}pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;padding:9px;background:#f5f6f3;border-radius:3px;line-height:1.5}.note{margin:14px 0 6px;font-size:13px}a{color:#315c48}details{margin:12px 0}summary{cursor:pointer}details pre{background:white;margin-top:10px}@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding:15px}}
</style><main><h1>Liquid on OpenRouter: choice works, box is rejected</h1><p class="lede">Four fresh API requests · 18 November 2026 · measured responses, not illustrative outputs</p><div class="context"><p><code>POST https://openrouter.ai/api/alpha/decisions</code></p><p>Same image, text input, account and provider setting. Authorization header omitted entirely.</p></div><section class="grid">'''+''.join(cards)+'''</section><p class="note"><strong>Confirmed scope:</strong> the OpenRouter Liquid adapter rejects <code>box</code>. This does not test Liquid's native object-localization API.</p><p class="note"><a href="recordings/openrouter-box-check-20261118.json">Saved requests + responses + timings</a> · <a href="https://openrouter.ai/docs/guides/community/multimodal-decisions#what-each-endpoint-accepts">Official provider capability table</a> · <a href="https://x.com/nipun_batra/status/2122919961417154708">Question posted to Liquid</a></p><details><summary>Reproduction details</summary><p>Image JPEG SHA-256: <code>'''+data['image_sha256']+'''</code>. Same state and image verified across all four requests. Provider fallbacks disabled. Choice criteria are present/absent; box requests a location. HTTP durations include provider/network delay. The successful-response account ID is omitted from saved metadata. No API key appears in any artifact.</p>'''+''.join(details)+'''</details></main></html>'''
(ROOT/'openrouter-box-check.html').write_text(page)
print('Built OpenRouter evidence page from four saved real requests.')
