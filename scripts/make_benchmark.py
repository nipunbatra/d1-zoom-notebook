"""Generate 16 controlled visual tasks. Pillow 13.0.0; no external assets."""
from pathlib import Path
import colorsys, hashlib, json, math, random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
INK, ORANGE = "#293b38", "#d58127"
font = lambda size: ImageFont.load_default(size=size)

def text(draw, xy, value, size=22, fill=INK, anchor=None):
    draw.text(xy, str(value), font=font(size), fill=fill, anchor=anchor)

def panel(title):
    im = Image.new("RGB", (720, 420), "#fbfaf5")
    d = ImageDraw.Draw(im)
    text(d, (26, 18), title, 24)
    d.line((25, 56, 695, 56), fill="#ccd4cd", width=2)
    return im, d

def code(v):
    im, d = panel("Equipment service record")
    value = ["B742", "K193"][v]
    rows = [("DATE", "17 NOV 2026"), ("UNIT", value), ("LOT", "L082"), ("STATUS", "INSPECTED")]
    for i, (label, answer) in enumerate(rows):
        y = 98 + i * 70
        text(d, (55, y), label, 22); text(d, (355, y), answer, 22)
    return im, "Read the four-character UNIT code in the orange-outlined service record.", value, ["B724", "K139", "B742", "K193", "B174"], {"UNIT": value}

def count(v):
    im, d = panel("Fastener tray")
    n = [8, 11][v]
    order = list(range(20)); random.Random(105 + v).shuffle(order)
    screws = set(order[:n]); facts = []
    for i in range(20):
        x, y = 92 + (i % 5) * 133, 105 + (i // 5) * 83
        d.ellipse((x-24,y-24,x+24,y+24), fill="#ccd1ce", outline=INK, width=3)
        if i in screws:
            d.line((x-14,y,x+14,y), fill=INK, width=4); d.line((x,y-14,x,y+14), fill=INK, width=4)
        else:
            d.ellipse((x-10,y-10,x+10,y+10), fill="#fbfaf5", outline=INK, width=2)
        facts.append({"centre": [x,y], "kind": "cross-slot screw" if i in screws else "plain ring"})
    return im, "How many screw heads have a cross-shaped slot in the orange-outlined tray? Do not count the plain rings.", str(n), ["6","8","10","11","12"], {"objects":facts,"cross_slot_count":n}

def thermal(v):
    im, d = panel("Thermal display - simulated")
    top = [48,62][v]; bottom = 18
    for y in range(300):
        for x in range(470):
            z = min(1, .12 + .8*math.exp(-((x-280)**2+(y-120)**2)/11000) + .1*math.sin(x/57))
            rgb = tuple(round(255*c) for c in colorsys.hsv_to_rgb((1-z)*.72,.85,.85))
            im.putpixel((35+x,85+y),rgb)
        z = 1-y/299
        rgb = tuple(round(255*c) for c in colorsys.hsv_to_rgb((1-z)*.72,.85,.85))
        d.line((550,85+y,583,85+y),fill=rgb,width=1)
    for f in (0,.5,1):
        y = 85 + int(300*f)
        d.line((584,y,596,y),fill=INK,width=2)
        text(d,(605,y),f"{top+(bottom-top)*f:g} C",20,anchor="lm")
    return im, "What is the upper endpoint printed on the colorbar in the orange-outlined thermal display, in degrees C? Read the legend, not the brightest image pixel.", str(top), ["18","33","40","48","62"], {"upper_endpoint_C":top,"lower_endpoint_C":bottom,"radiometric":False}

def chart(v):
    im,d=panel("Weekly output")
    values=[24,48,[37,62][v],71]; names=["Alder","Birch","Cedar","Delta"]
    for tick in range(0,81,20):
        y=350-tick*3
        d.line((70,y,680,y),fill="#d7ddd7",width=1);text(d,(55,y),tick,18,anchor="rm")
    for i,(name,value) in enumerate(zip(names,values)):
        x=112+i*147;y=350-value*3
        d.rectangle((x,y,x+72,350),fill="#518b7b")
        text(d,(x+36,y-14),value,20,anchor="mm");text(d,(x+36,377),name,19,anchor="mm")
    return im,"Read the value printed above Cedar's bar in the orange-outlined chart.",str(values[2]),["24","37","48","62","71"],dict(zip(names,values))

def table(v):
    im,d=panel("Service hours")
    columns=["Mon","Tue","Wed","Thu","Fri"]
    values=[[12,19,21,8,14],[9,14,16,22,6],[20,7,15,11,18],[14,9,13,21,[17,24][v]],[23,16,12,19,10]]
    for j in range(7):d.line((52+j*93,80,52+j*93,385),fill="#bac5bd",width=2)
    for i in range(7):d.line((52,80+i*50,610,80+i*50),fill="#bac5bd",width=2)
    for j,name in enumerate(["Row"]+columns):text(d,(98+j*93,105),name,20,anchor="mm")
    for i,row in enumerate(values):
        text(d,(98,155+i*50),"ABCDE"[i],20,anchor="mm")
        for j,n in enumerate(row):text(d,(191+j*93,155+i*50),n,21,anchor="mm")
    return im,"Read the Friday value in row D of the orange-outlined table.",str(values[3][4]),["14","17","21","24","19"],{"columns":columns,"rows":dict(zip("ABCDE",values))}

def circuit(v):
    im,d=panel("Continuity inspection")
    d.rectangle((28,74,692,394),fill="#244e3f")
    path=[(65,300),(155,300),(155,180),(370,180),(370,280),(650,280)]
    d.line(path,fill="#ddba63",width=14)
    for x,y in (path[0],path[-1]):d.ellipse((x-20,y-20,x+20,y+20),fill="#ddba63");d.ellipse((x-7,y-7,x+7,y+7),fill="#244e3f")
    if v == 0:d.rectangle((274,170,280,190),fill="#244e3f")
    return im,"Is there a visible break in the gold-colored copper trace in the orange-outlined circuit panel?",["broken","continuous"][v],["broken","continuous"],{"trace_path":path,"gap": [274,173,281,188] if v==0 else None}

def spatial(v):
    im,d=panel("Symbol relation")
    d.rectangle((345,203,397,255),fill="#367caa")
    cx,cy=[(279,229),(371,321)][v]
    d.polygon([(cx,cy-28),(cx-24,cy+23),(cx+24,cy+23)],fill="#25332f")
    for x,y in [(130,150),(550,130),(140,325),(570,320)]:d.ellipse((x-16,y-16,x+16,y+16),fill="#a3aaa4")
    return im,"Where is the black triangle relative to the blue square in the orange-outlined panel?",["left","below"][v],["above","below","left","right"],{"triangle_centre":[cx,cy],"square_centre":[371,229]}

def gauge(v):
    im,d=panel("Pressure dial (arbitrary units)")
    cx,cy,r=360,340,235; value=[40,70][v]
    d.arc((cx-r,cy-r,cx+r,cy+r),180,360,fill=INK,width=3)
    for n in range(0,101,10):
        a=math.pi*(1-n/100)
        points=[(cx+rr*math.cos(a),cy-rr*math.sin(a)) for rr in (r-15,r)]
        d.line(points,fill=INK,width=3)
        text(d,(cx+(r-38)*math.cos(a),cy-(r-38)*math.sin(a)),n,18,anchor="mm")
    a=math.pi*(1-value/100)
    d.line((cx,cy,cx+(r-58)*math.cos(a),cy-(r-58)*math.sin(a)),fill="#b55c38",width=7)
    d.ellipse((cx-10,cy-10,cx+10,cy+10),fill=INK)
    return im,"Which labeled value does the needle point to in the orange-outlined dial?",str(value),["30","40","50","60","70","80"],{"needle_value":value,"scale":[0,100]}

GENERATORS=[("text","Small text",code),("count","Counting",count),("thermal","Thermal colorbar",thermal),("chart","Chart reading",chart),("table","Table lookup",table),("circuit","Circuit continuity",circuit),("spatial","Spatial relation",spatial),("gauge","Analog gauge",gauge)]

def generate():
    (OUT/"images").mkdir(parents=True,exist_ok=True)
    tasks=[]
    for family,label,maker in GENERATORS:
        for v in range(2):
            part,question,truth,options,facts=maker(v)
            im=Image.new("RGB",(1800,1200),"#e9ede7");d=ImageDraw.Draw(im)
            text(d,(60,38),"Visual inspection board",32);text(d,(60,88),"Inspect the orange-outlined panel.",24)
            for y in (190,525,860):
                for x in (65,520,975,1430):
                    d.rectangle((x,y,x+290,y+215),fill="#dce3db",outline="#c9d2c8",width=2)
                    for j in range(5):d.line((x+25,y+35+j*29,x+250-(j%2)*55,y+35+j*29),fill="#c4cec2",width=5)
            box=[150,360,870,780] if v==0 else [1180,765,1540,975]
            im.paste(part.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]))
            d.rectangle((box[0]-6,box[1]-6,box[2]+6,box[3]+6),outline=ORANGE,width=6)
            task_id=f"{family}-{v+1:02d}";path=OUT/"images"/(task_id+".png");im.save(path)
            random.Random(f"options-{task_id}").shuffle(options)
            choices={o:o for o in options};choices["uncertain"]="The evidence is missing, clipped, or too unclear to answer."
            tasks.append(dict(id=task_id,family=label,label=label,variant=["Larger panel","Smaller panel"][v],question=question,
                route_target="the entire orange-outlined panel, including all its contents and labels",choices=choices,truth=truth,
                evidence={"bounds":box,"explanation":"Answer computed from the fixture specification; withheld from every request.","facts":facts},
                image_path="images/"+path.name,size=list(im.size),image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source="Procedural teaching fixture, not a photograph or measurement."))
    (OUT/"tasks.json").write_text(json.dumps(tasks,indent=2)+"\n")
    print(f"Generated {len(tasks)} tasks across {len(GENERATORS)} families.")

if __name__=="__main__":generate()
