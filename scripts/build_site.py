"""Rebuild the standalone page and sync its viewer into the notebook. Stdlib only."""
from pathlib import Path
from html.parser import HTMLParser
import base64, html, json, re, zlib

ROOT=Path(__file__).resolve().parents[1]
NOTEBOOK=ROOT/'d1_crop_walkthrough.ipynb'
nb=json.loads(NOTEBOOK.read_text())
def text(value):return ''.join(value) if isinstance(value,list) else value
class Frame(HTMLParser):
    srcdoc=None
    def handle_starttag(self,tag,attrs):
        if tag=='iframe':self.srcdoc=dict(attrs).get('srcdoc')
viewer_cell=next(c for c in reversed(nb['cells']) if c['cell_type']=='code' and 'viewer = BUNDLE[' in text(c['source']))
output=next(o for o in viewer_cell['outputs'] if 'text/html' in o.get('data',{}))
frame=Frame();frame.feed(text(output['data']['text/html']))
assert frame.srcdoc, 'Execute the notebook first'
old=frame.srcdoc
marker='const DATA'
start=old.index('=',old.index(marker))+1
data,_=json.JSONDecoder().raw_decode(old[start:].lstrip())
template=(ROOT/'src/viewer.html').read_text()
viewer=template.replace('__WALKTHROUGH_DATA__',json.dumps(data).replace('<','\\u003c'))
asset_cell=next(c for c in nb['cells'] if c['cell_type']=='code' and text(c['source']).startswith('#@title Embedded'))
source=text(asset_cell['source'])
packed=re.search(r"base64.b64decode\('([^']+)'\)",source).group(1)
bundle=json.loads(zlib.decompress(base64.b64decode(packed)))
bundle['viewer_template']=template
newpacked=base64.b64encode(zlib.compress(json.dumps(bundle).encode(),9)).decode()
asset_cell['source']=source.replace(packed,newpacked).splitlines(keepends=True)
output['data']['text/html']=['<iframe title="D1 crop walkthrough" sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox" style="width:100%;height:1050px;border:0" srcdoc="'+html.escape(viewer,quote=True)+'"></iframe>']
NOTEBOOK.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n')

code=[]
for i,c in enumerate([c for c in nb['cells'] if c['cell_type']=='code'],1):
    source=text(c['source'])
    if source.startswith('#@title Embedded'):
        code.append('<p class="source-note">Cell 2 contains embedded images and records. Download the notebook to inspect them.</p>');continue
    code.append('<details><summary>Python · cell '+str(i)+'</summary><pre><code>'+html.escape(source)+'</code></pre></details>')
companion='<section class="app" id="code"><details><summary>Notebook code · 10 cells</summary><p class="source-note">The notebook runs offline by default. Optional live mode makes up to five billed calls. Images and saved responses are included.</p>'+''.join(code)+'</details></section>'
page=viewer.replace('<nav id="export-links" class="export-links" aria-label="Downloads"></nav>',
    '<nav id="export-links" class="export-links" aria-label="Downloads"><a href="d1_crop_walkthrough.ipynb" download>Notebook</a><a href="#code">Code</a></nav>')
page=page.replace('</main>','</main>'+companion,1)
(ROOT/'index.html').write_text(page)
print('Built standalone page; synced viewer into notebook.')
