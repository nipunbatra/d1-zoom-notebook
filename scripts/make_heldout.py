"""New synthetic test fixtures, fixed before new-test inference. Never overwrites."""
from pathlib import Path
import hashlib, json, random
from PIL import Image, ImageDraw
from make_benchmark import code,count,thermal,chart,table,circuit,spatial,gauge,text,ORANGE

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"data/test-tasks.json"
CASES=[
    ("text","Small text",code,[{"value":"R582"},{"value":"M614"}],["R528","R582","M641","M614","R852"]),
    ("count","Counting",count,[{"n":7},{"n":13}],["5","7","9","11","13"]),
    ("thermal","Thermal colorbar",thermal,[{"top":54},{"top":76}],["18","36","47","54","76"]),
    ("chart","Chart reading",chart,[{"value":42},{"value":58}],["24","42","48","58","71"]),
    ("table","Table lookup",table,[{"value":26},{"value":31}],["19","21","26","31","23"]),
    ("circuit","Circuit continuity",circuit,[{"gap_x":210},{"gap_x":320}],["broken","continuous"]),
    ("spatial","Spatial relation",spatial,[{"position":(371,137)},{"position":(463,229)}],["above","below","left","right"]),
    ("gauge","Analog gauge",gauge,[{"value":20},{"value":90}],["10","20","30","70","80","90"]),
]

def generate():
    if DEST.exists():raise FileExistsError("Keeping frozen test fixtures; use a new filename for another test.")
    tasks=[];rng=random.Random(2026111703)
    for family,label,maker,settings,options in CASES:
        for v in range(2):
            part,q,truth,_,facts=maker(v,**settings[v]);im=Image.new("RGB",(1800,1200),"#e9ede7");d=ImageDraw.Draw(im)
            text(d,(60,38),"Visual inspection board",32);text(d,(60,88),"Inspect the orange-outlined panel.",24)
            for y in (190,525,860):
                for x in (65,520,975,1430):
                    d.rectangle((x,y,x+290,y+215),fill="#dce3db",outline="#c9d2c8",width=2)
                    for j in range(5):d.line((x+25,y+35+j*29,x+250-(j%2)*55,y+35+j*29),fill="#c4cec2",width=5)
            size=(720,420) if v==0 else (360,210)
            x=rng.randrange(80,1800-size[0]-80);y=rng.randrange(180,1200-size[1]-60)
            box=[x,y,x+size[0],y+size[1]]
            im.paste(part.resize(size,Image.Resampling.LANCZOS),(x,y));d.rectangle((x-6,y-6,box[2]+6,box[3]+6),outline=ORANGE,width=6)
            case_id=f"{family}-{v+1:02d}";path=ROOT/"data/images"/("test-"+case_id+".png");im.save(path)
            choices=list(options);rng.shuffle(choices);choices={o:o for o in choices};choices["uncertain"]="The evidence is missing, clipped, or too unclear to answer."
            tasks.append(dict(id=case_id,family=label,label=label,variant=["Larger panel","Smaller panel"][v],question=q,
                route_target="the entire orange-outlined panel, including all its contents and labels",choices=choices,truth=truth,
                evidence={"bounds":box,"explanation":"New generated test answer; excluded from inference and controller decisions.","facts":facts},
                image_path="images/"+path.name,image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size=list(im.size),
                source="New synthetic test fixture, same task families; not a natural image or measurement.",split="test"))
    DEST.write_text(json.dumps(tasks,indent=2)+"\n");print("Created16 new test fixtures; seed2026111703.")

if __name__=="__main__":generate()
