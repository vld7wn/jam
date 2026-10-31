from pathlib import Path
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[2]
out = root / 'spider-game' / 'public' / 'art2d' / 'references'
items = {
    'spider-reference': root / 'model' / 'паук' / 'karakurt.jpg',
    'spider-color': root / 'model' / 'паук' / 'каракурт_цвет.jpg',
    'spider-web': root / 'model' / 'паук' / 'на_паутине.jpg',
    'cocoon-spider': root / 'model' / 'паук' / 'плетение_кокона.jpg',
    'shadow-people': root / 'model' / 'человек' / 'Shadow people.jpg',
    'human-motion': root / 'model' / 'человек' / 'движения.jpg',
    'wall-spider-man': root / 'model' / 'эффекты_на_стене' / 'spider-man.jpg',
    'wall-fingers': root / 'model' / 'эффекты_на_стене' / 'пальцы_из_стены.jpg',
    'spider-skeleton': root / 'model' / 'эффекты_на_стене' / 'паук_скелет.jpg',
    'screamer': root / 'model' / 'скример.jpg',
}
out.mkdir(parents=True, exist_ok=True)
for name, source in items.items():
    image = Image.open(source).convert('RGBA')
    image.thumbnail((900, 700), Image.Resampling.LANCZOS)
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, _ = pixels[x, y]
            luminance = (r * 299 + g * 587 + b * 114) // 1000
            # Keep ink and discard the white paper so drawings can sit on the room walls.
            alpha = max(0, min(235, int((245 - luminance) * 3.3)))
            pixels[x, y] = (25, 34, 43, alpha)
    image.save(out / f'{name}.png', optimize=True)
    print(f'created {out / f"{name}.png"} {image.width}x{image.height}')
