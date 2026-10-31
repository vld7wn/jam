from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[2]
im=Image.open(root/'model'/'паук'/'Спрайт-лист паука и теневого героя.png').convert('RGBA')
w,h=im.size;p=im.load();seen=bytearray(w*h);comps=[]
for y in range(h):
 for x in range(w):
  r,g,b,a=p[x,y]
  if min(r,g,b)>=244:p[x,y]=(r,g,b,0)
for y in range(h):
 for x in range(w):
  i=y*w+x
  if seen[i] or p[x,y][3]<32:continue
  seen[i]=1;q=[i];x0=x1=x;y0=y1=y;area=0
  while q:
   j=q.pop();xx=j%w;yy=j//w;area+=1;x0=min(x0,xx);x1=max(x1,xx);y0=min(y0,yy);y1=max(y1,yy)
   for ny in range(max(0,yy-1),min(h,yy+2)):
    for nx in range(max(0,xx-1),min(w,xx+2)):
     k=ny*w+nx
     if not seen[k] and p[nx,ny][3]>=32:seen[k]=1;q.append(k)
  if area>1200 and y0>460:comps.append((area,x0,y0,x1+1,y1+1))
comps.sort(key=lambda c:(c[2],c[1]))
out=Image.new('RGBA',(6*256,((len(comps)+5)//6)*300),(38,43,52,255));d=ImageDraw.Draw(out)
for i,(area,x0,y0,x1,y1) in enumerate(comps):
 crop=im.crop((x0,y0,x1,y1));crop.thumbnail((235,255));x=(i%6)*256;y=(i//6)*300
 out.alpha_composite(crop,(x+(256-crop.width)//2,y));d.text((x+5,y+263),f'{i}: {x0},{y0}-{x1},{y1} / {area}',fill='white')
out.convert('RGB').save(root/'spider-game'/'public'/'assets'/'jam2d'/'human-components.png')
print('Components',len(comps));print(*[(i,c[1:]) for i,c in enumerate(comps)],sep='\n')
