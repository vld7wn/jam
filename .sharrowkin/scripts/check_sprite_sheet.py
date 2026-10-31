from pathlib import Path
from PIL import Image, ImageDraw
import json
p=Path(__file__).resolve().parents[2]/'spider-game/public/assets/jam2d/manifest.json'
root=p.parent; d=json.loads(p.read_text(encoding='utf-8'))
expected={'spider':{'idle','walk','turn_left','turn_right','jump','web'},'human':{'idle','walk','run','attack','collision','fall'}}
assert {a:set(s) for a,s in d['actors'].items()}==expected, d['actors']
assert (d['frameWidth'],d['frameHeight'],d['frames'],d['fps'])==(512,512,8,12)
for actor,states in d['actors'].items():
 for state,v in states.items():
  im=Image.open(root/v['file']).convert('RGBA')
  assert im.size==(4096,512),(actor,state,im.size)
  frames=[im.crop((i*512,0,(i+1)*512,512)) for i in range(8)]
  boxes=[f.getchannel('A').getbbox() for f in frames]
  assert all(boxes),(actor,state,'empty-frame')
  assert max(b[2]-b[0] for b in boxes)>40,(actor,state,'too-small')
  print('PASS',actor,state,im.size)
# checker composite visual contact sheet
keys=[(a,s,v['file']) for a,states in d['actors'].items() for s,v in states.items()]
board=Image.new('RGB',(4*256,((len(keys)+3)//4)*290),(45,50,58)); draw=ImageDraw.Draw(board)
for j,(actor,state,file) in enumerate(keys):
 sheet=Image.open(root/file).convert('RGBA'); fr=sheet.crop((0,0,512,512)); fr.thumbnail((230,245))
 x=(j%4)*256; y=(j//4)*290; board.paste(fr,(x+(256-fr.width)//2,y),fr); draw.text((x+8,y+248),f'{actor}: {state}',fill='white')
board.save(root/'sprite-preview.png')
