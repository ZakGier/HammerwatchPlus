"""python grid.py <out.png> <z> <cols> <name=png> ... -> a labelled grid sheet (review aid)."""
import sys
from PIL import Image, ImageDraw


def grid(items, path, z=4, cols=8):
    cw, ch = 24 * z + 10, 24 * z + 20
    rows = (len(items) + cols - 1) // cols
    out = Image.new("RGBA", (cols * cw, rows * ch), (28, 28, 34, 255))
    d = ImageDraw.Draw(out)
    for i, (name, im) in enumerate(items):
        x, y = (i % cols) * cw + 5, (i // cols) * ch + 2
        out.alpha_composite(im.resize((im.width * z, im.height * z), Image.Resampling.NEAREST), (x, y))
        d.text((x, y + 24 * z + 3), name[:17], fill=(230, 230, 230, 255))
    out.save(path)


if __name__ == "__main__":
    grid([(a.split("=")[0], Image.open(a.split("=")[1]).convert("RGBA")) for a in sys.argv[4:]], sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
