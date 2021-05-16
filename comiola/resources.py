import os
import sys
from PIL import Image, ImageFont

proj_dir = ''

class ImgRec:
    def __init__(self,fn,img):
        self.fn = fn
        self.img = img
        self.live = True

pool = []

def clear_refs():
    global pool
    for ir in pool:
        ir.live = False

def close_unneeded():
    global pool
    _pool = []
    for ir in pool:
        if ir.live:
            _pool.append(ir)
        else:
            ir.img.close()
    pool = _pool

def get_img(fn,mode):
    global pool
    for ir in pool:
        if ir.fn == fn:
            ir.live = True
            #print('reusing %s' % fn)
            return ir.img
    ext = 'png' if mode == 'RGBA' else 'jpg'
    img = Image.open('%s/%s.%s' % (proj_dir,fn,ext))
    if mode != '':
        _img = img.convert(mode)
        img.close()
        img = _img
    pool.append(ImgRec(fn,img))
    return img

def get_img_ar(fn,mode):
    (w,h) = get(fn,mode).size
    return float(h)/w

res_pool = {}
def get_res(fn):
    img = res_pool.get(fn)
    if img is None:
        fp = os.path.join( os.path.dirname(__file__),
                'res', fn + '.png')
        fp = os.path.abspath(fp)
        img = Image.open(fp).convert('RGBA')
        res_pool[fn] = img
    return img

# text elements: we pool fonts
font_pool = {}

def get_font(fontname,fontsize):
    # get font for a text element
    key = fontname+fontsize
    font =  font_pool.get(key) 
    if font is not None:
        return font
    fontsize = int( fontsize[:-2] )
    path = os.path.join( os.path.dirname(__file__),
        'res', fontname + '.ttf')
    font = ImageFont.truetype(os.path.abspath(path),fontsize)
    font_pool[key] = font
    return font
