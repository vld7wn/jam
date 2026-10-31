from pathlib import Path
from PIL import Image
import json

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'model'/'паук'/'Спрайт-лист паука и теневого героя.png'
out=ROOT/'spider-game'/'public'/'assets'/'jam2d'
out.mkdir(parents=True,exist_ok=True)
for actor in ('spider','human'): (out/actor).mkdir(exist_ok=True)
image=Image.open(source).convert('RGBA')
w,h=image.size; px=image.load(); seen=bytearray(w*h); stack=[]
for x in range(w): stack.extend((x,(h-1)*w+x))
for y in range(h): stack.extend((y*w,y*w+w-1))
while stack:
 i=stack.pop()
 if seen[i]: continue
 seen[i]=1; x=i%w; y=i//w; r,g,b,a=px[x,y]
 if min(r,g,b)<244: continue
 px[x,y]=(r,g,b,0)
 if x: stack.append(i-1)
 if x+1<w: stack.append(i+1)
 if y: stack.append(i-w)
 if y+1<h: stack.append(i+w)

def row_cells(count,y0,y1,margin=4):
 return [(round(i*1536/count)+margin,y0,round((i+1)*1536/count)-margin,y1) for i in range(count)]

# Spider rows follow the source's actual horizontal pose bands.
spider={
 'walk':row_cells(8,5,170,5), 'idle':row_cells(8,5,170,5),
 'turn_left':row_cells(8,177,340,5), 'turn_right':row_cells(8,177,340,5)[::-1],
 'jump':row_cells(8,177,340,5), 'web':row_cells(8,342,461,5),
}
# Human poses are individually isolated from the irregularly arranged illustration.
human_poses=[
 (1292,659,1425,869),(932,711,1019,989),(1029,703,1182,892),(1172,713,1308,847),
 (696,718,811,863),(803,730,912,910),(379,816,470,1008),(485,819,567,1004),
 (152,851,231,993),(245,866,373,971),(1353,878,1519,1000),(764,929,910,1002),
]
human={
 'run':[human_poses[i] for i in [0,2,3,5,6,7,0,2]],
 'walk':[human_poses[i] for i in [1,6,7,5,1,6,7,5]],
 'idle':[human_poses[1]]*8,
 'attack':[human_poses[i] for i in [4,3,0,2,4,3,0,2]],
 'fall':[human_poses[i] for i in [8,9,10,11,10,9,8,11]],
 'collision':[human_poses[i] for i in [0,8,9,10,11,9,8,0]],
}

def make_frame(box):
 x,y,x2,y2=box; crop=image.crop((x,y,x2,y2)); bounds=crop.getchannel('A').getbbox()
 if bounds: crop=crop.crop(bounds)
 if crop.width==0 or crop.height==0: return Image.new('RGBA',(512,512),(0,0,0,0))
 scale=min(474/crop.width,474/crop.height); crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.LANCZOS)
 frame=Image.new('RGBA',(512,512),(0,0,0,0)); frame.alpha_composite(crop,((512-crop.width)//2,(512-crop.height)//2)); return frame

manifest={'version':1,'frameWidth':512,'frameHeight':512,'frames':8,'fps':12,'actors':{'spider':{},'human':{}},'source':'model/паук/Спрайт-лист паука и теневого героя.png'}
for actor,states in [('spider',spider),('human',human)]:
 for state,cells in states.items():
  sheet=Image.new('RGBA',(4096,512),(0,0,0,0))
  for i in range(8): sheet.alpha_composite(make_frame(cells[i%len(cells)]),(i*512,0))
  rel=f'{actor}/{state}.png'; sheet.save(out/rel,optimize=True)
  manifest['actors'][actor][state]={'file':rel,'loop':state in {'idle','walk','run','turn_left','turn_right'}}
image.save(out/'spider-shadow-reference-atlas.png',optimize=True)
manifest['atlas']='spider-shadow-reference-atlas.png'
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Sliced:',{a:list(s) for a,s in manifest['actors'].items()})
