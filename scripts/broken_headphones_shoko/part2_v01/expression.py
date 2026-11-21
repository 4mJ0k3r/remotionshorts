"""Keep the approved eyes and draw a new quivering panic mouth beneath them."""
from PIL import Image, ImageDraw
from timing import HERE, SHARED

target=HERE/"panic_wobble.png"
source=SHARED/"art/boy_panic_sweat.png"
with Image.open(source) as original:
    face=original.convert("RGBA")
draw=ImageDraw.Draw(face)
draw.rectangle((345,624,674,839),fill=(22,16,32,0))

def path(vertices,width,color):
    draw.line([(round(x*4),round(y*4)) for x,y in vertices],fill=color,width=round(4*width),joint="curve")

path([(99,174),(107,166),(116,178),(127,168),(139,178),(151,165),(159,173)],7,"#161020")
face.save(target)
