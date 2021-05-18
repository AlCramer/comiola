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
    img = Image.open( os.path.join(proj_dir,'%s.%s' % (fn,ext)) )
    if mode != '':
        _img = img.convert(mode)
        img.close()
        img = _img
    pool.append(ImgRec(fn,img))
    return img

def get_img_ar(fn,mode):
    (w,h) = get_img(fn,mode).size
    return float(h)/w

def get_assets_dir(kind):
    # "kind" is either "res" or "faq"
    if getattr(sys, 'frozen', False):
        return kind
    elif __file__:
        app_path = os.path.dirname(__file__)
        return os.path.join(app_path,kind)

res_pool = {}
def get_res(fn):
    img = res_pool.get(fn)
    if img is None:
        fp = os.path.join( get_assets_dir('res'), fn+'.png')
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
    path = os.path.join( get_assets_dir('res'), fontname + '.ttf')
    font = ImageFont.truetype(path,fontsize)
    font_pool[key] = font
    return font

