"""Validate recorded input pixels, crop geometry and the labelled reading fixture."""
from pathlib import Path
from html.parser import HTMLParser
import base64, io, json, math, re
from PIL import Image

root=Path(__file__).resolve().parents[1]
nb=json.loads((root/'d1_crop_walkthrough.ipynb').read_text())
def text(v):return ''.join(v) if isinstance(v,list) else v
class Frame(HTMLParser):
    source=None
    def handle_starttag(self,tag,attrs):
        if tag=='iframe':self.source=dict(attrs).get('srcdoc')
viewer_cell=next(c for c in reversed(nb['cells']) if c['cell_type']=='code' and 'viewer = BUNDLE[' in text(c['source']))
output=next(o for o in viewer_cell['outputs'] if 'text/html' in o.get('data',{}))
parser=Frame();parser.feed(text(output['data']['text/html']))
s=parser.source;start=s.index('=',s.index('const DATA'))+1
gallery,_=json.JSONDecoder().raw_decode(s[start:].lstrip())
assert len(gallery['examples'])==5
def decode(url):return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGB')
cells='top_left top top_right left centre right bottom_left bottom bottom_right'.split()
checked=0
for example in gallery['examples']:
    original=decode(example['original_url']);assert list(original.size)==example['original_size']
    full=[0,0,*original.size];last_grid=None;seen=set();stopped=False
    for frame in example['frames']:
        l,t,r,b=win=frame['window'];assert 0<=l<r<=original.width and 0<=t<b<=original.height
        if win!=full and tuple(win) not in seen:
            assert last_grid and last_grid[0]!='not_visible'
            choice,parent=last_grid;x,y,xx,yy=parent;w,h=xx-x,yy-y;row,col=divmod(cells.index(choice),3)
            expected=[x+math.floor(max(0,col*w/3-w/6)),y+math.floor(max(0,row*h/3-h/6)),
                      x+math.ceil(min(w,(col+1)*w/3+w/6)),y+math.ceil(min(h,(row+1)*h/3+h/6))]
            assert win==expected,(example['id'],win,expected)
            seen.add(tuple(win))
        for box in frame['boxes']:
            x,y,xx,yy=box['bounds'];assert 0<=x<xx<=original.width and 0<=y<yy<=original.height
        if not frame.get('response'):continue
        assert not stopped,'Model call after not_visible'
        assert frame['response']['model']=='liquid/d1.2-20261116'
        expected=original.crop(win)
        if example.get('max_input_edge'):expected.thumbnail((example['max_input_edge'],)*2,Image.Resampling.LANCZOS)
        encoded=io.BytesIO();expected.save(encoded,format='JPEG',quality=95)
        actual=base64.b64decode(frame['input_url'].split(',')[1])
        assert encoded.getvalue()==actual,(example['id'],frame['title'],'input pixels differ')
        grid=frame['response']['answers'].get('grid')
        if grid:
            choice=grid['choice'];last_grid=(choice,win)
            if choice=='not_visible':
                stopped=True;assert not frame['boxes']
            else:
                row,col=divmod(cells.index(choice),3);w,h=r-l,b-t
                expected=[l+col*w/3,t+row*h/3,l+(col+1)*w/3,t+(row+1)*h/3]
                assert len(frame['boxes'])==1
                assert all(abs(a-v)<1e-7 for a,v in zip(frame['boxes'][0]['bounds'],expected))
        checked+=1
    print(example['id'],len(seen),'crop windows checked')
label=next(x for x in gallery['examples'] if x['id']=='label')
calls=[f for f in label['frames'] if f.get('response')]
assert label['truth_code']=='B742' and label['truth_bounds']==[1228,954,1304,979]
first=calls[0]['response']['answers']['reading']['probabilities']
assert first['B742']==first['B174']==max(first.values())
assert all(f['response']['answers']['reading']['choice']=='B742' for f in calls)
assert calls[2]['response']['answers']['reading']['probabilities']['B742']>.99
for c in nb['cells']:
    for o in c.get('outputs',[]):assert o['output_type']!='error' and o.get('name')!='stderr'
    if c['cell_type']=='code':compile(text(c['source']),'<notebook>','exec')
for path in [root/'index.html',root/'d1_crop_walkthrough.ipynb']:
    data=path.read_text();assert '/Users/nipun' not in data and '"user_id":' not in data
    assert not re.search(r'sk-or-[A-Za-z0-9_-]{30,}',data)
print('PASS:',checked,'actual model inputs, crop paths, mapped cells, stopping branches, tie and known reading answer.')
