"""Create an analogous reading fixture. Recorded image uses Menlo on macOS."""
from pathlib import Path
import random
from PIL import Image,ImageDraw,ImageFont
(Path(__file__).resolve().parents[1]/"images").mkdir(exist_ok=True)
im=Image.new('RGB',(2000,1400),'#f8f7f2');d=ImageDraw.Draw(im)
# Pillow 10.1+ supplies its default scalable font without a system font dependency.
font=lambda n:ImageFont.load_default(size=n)
d.text((90,60),'WAREHOUSE  /  INSPECTION REGISTER',font=font(34),fill='#25382d')
d.text((90,118),'Training fixture - generated image, not an operational record',font=font(16),fill='#667064')
rng=random.Random(29);target_box=None
for row in range(12):
 for col in range(5):
  x=95+col*375;y=195+row*91
  d.rectangle((x,y,x+330,y+64),outline='#cbd2c5',width=1)
  d.text((x+12,y+9),f'BIN {row+1:02d}-{col+1}',font=font(12),fill='#667064')
  value=''.join(rng.choice('ABCD123478') for _ in range(4))
  if (row,col)==(8,3):
   value='B742';target_box=[x+8,y+31,x+84,y+56]
   d.rectangle(target_box,outline='#c06c22',width=3)
  d.text((x+15,y+36),value,font=font(12),fill='#202b24')
im.save(Path(__file__).resolve().parents[1]/'images/inspection-register.png')
