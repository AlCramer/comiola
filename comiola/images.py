from PIL import Image, ImageDraw, ImageOps, ImageFont
import os
import shutil

'''
Panel creation: we accept an image, split as needed,
and turn it into 1 or more panels (p0.jpg, p1.jpg, etc.)
'''

w_shot = 600
h_shot = 600

MIN_GUTTER = 10

class Reg:
    def __init__(self,x0,y0,x1,y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.ixrow = -1
        self.ixcol = -1

    def str(self):
        return '%d,%d %d,%d' % (self.x0, self.y0, self.x1, self.y1)

    def equals(self,rx):
        return (self.x0 == rx.x0 and
            self.y0 == rx.y0 and
            self.x1 == rx.x1 and
            self.y1 == rx.y1)

    def assign(self,rx):
        self.x0 = rx.x0
        self.y0 = rx.y0
        self.x1 = rx.x1
        self.y1 = rx.y1

    def contains(self,x,y):
        return (self.x0 <= x and x <= self.x1 and
                self.y0 <= y and y <= self.y1)

    def clone(self):
        return Reg(self.x0,self.y0,self.x1,self.y1)

    @classmethod
    def from_CWH(cls,xc,yc,w,h):
        # set from center/width/height
        return Reg(
            xc - int(w/2),
            yc - int(h/2),
            xc + int(w/2),
            yc + int(h/2))

    def get_w(self):
        return self.x1 - self.x0 + 1

    def get_h(self):
        return self.y1 - self.y0 + 1

    def get_CWH(self):
        w = self.x1 - self.x0 + 1
        h = self.y1 - self.y0 + 1
        return (
            self.x0 + int(w/2),
            self.y0 + int(h/2),
            w,
            h)

    def get_tween(self,r_dst,ixframe,nframes):
        # get region between self and rx
        if nframes == 1:
            return self.clone()
        (xc_src,yc_src,w_src,h_src) = self.get_CWH()
        (xc_dst,yc_dst,w_dst,h_dst) = r_dst.get_CWH()
        scale = float(ixframe)/(nframes-1)
        return Reg.from_CWH(
            xc_src + int(.5+scale*(xc_dst - xc_src)),
            yc_src + int(.5+scale*(yc_dst - yc_src)),
            w_src + int(.5+scale*(w_dst - w_src)),
            h_src + int(.5+scale*(h_dst - h_src))
            )

    def serialize(self):
        lst = []
        lst.append('%d' % self.x0)
        lst.append('%d' % self.y0)
        lst.append('%d' % self.x1)
        lst.append('%d' % self.y1)
        return ','.join(lst)

    @classmethod
    def unserialize(cls,src):
        lst = src.split(',')
        return Reg(
            int(lst[0]),
            int(lst[1]),
            int(lst[2]),
            int(lst[3]))
        

    def expand(self,rx):
        # expand self to include rx
        self.x0 = min(self.x0,rx.x0)
        self.x1 = max(self.x1,rx.x1)
        self.y0 = min(self.y0,rx.y0)
        self.y1 = max(self.y1,rx.y1)

    def xlate(self,xdelta,ydelta):
        self.x0 += xdelta
        self.y0 += ydelta
        self.x1 += xdelta
        self.y1 += ydelta

    def xlate_scale(self,xdelta,ydelta,scale):
        self.x0 = int( (self.x0 + xdelta)*scale )
        self.y0 = int( (self.y0 + ydelta)*scale )
        self.x1 = int( (self.x1 + xdelta)*scale )
        self.y1 = int( (self.y1 + ydelta)*scale )

    def _print(self):
        print ("(%d %d %d %d) ixrow:%d ixcol:%d" %\
                (self.x0,self.y0,self.x1,self.y1,self.ixrow,self.ixcol))

class Im:
    def __init__(self,fn):
        self.fn = fn
        self.im_pil = Image.open(fn)
        (self.w,self.h) = self.im_pil.size
        self.pix = self.im_pil.convert('L').load()
        
MIN_PIX_FG = 10
EPSILON = 20

def set_validity(regs):
    # mark regions as valid or invalid. Test is based on
    # aspect ratio: reject regions that are tall & skinny or
    # short and wide.
    for r in regs:
        lo_dim = min(r.x1-r.x0, r.y1-r.y0)
        hi_dim = max(r.x1-r.x0, r.y1-r.y0)
        r.valid = lo_dim/float(hi_dim) > .2

    
def merge_regions(mode,regs):
    if len(regs) <= 1:
        return regs
    
    # merge regions if gutter too small
    r = regs[0]
    _regs = [r]
    for i in range(1,len(regs)):
        rx = regs[i]
        if mode == 'vert':
            merge = rx.x0 - r.x1 < MIN_GUTTER
        else:
            merge = rx.y0 - r.y1 < MIN_GUTTER
        if merge:
            r.expand(rx)
        else:
            _regs.append(rx)
            r = rx
            
    regs = _regs
    set_validity(regs)
    
    # If region and its successor(s) are invalid, merge
    _regs = []
    i = 0
    while i < len(regs):
        r = regs[i]
        _regs.append(r)
        i += 1
        if not r.valid:
            # find "E": index of last invalid reg after "reg[i]"
            E = i -1
            while E<len(regs) and not regs[E].valid:
                E += 1
            E -= 1
            # merge invalid sequence
            r.expand(regs[E])
            i = E + 1

    regs = _regs
    set_validity(regs)
    
    if not regs[0].valid:
        # merge with next reg
        regs[1].expand(regs[0])
        regs = regs[1:]
    if len(regs) == 1:
        return regs
    if not regs[-1].valid:
        # merge with prev reg
        regs[len(regs)-2].expand(regs[-1])
        regs = regs[:-1]
    if len(regs) == 1:
        return regs
    
    # Find valid/invalid/valid sequences & merge into single region
    _regs = []
    i = 0
    while i < len(regs):
        _regs.append(regs[i])
        if (i+2 < len(regs) and
            regs[i].valid and
            (not regs[i+1].valid) and
            regs[i+2].valid):
            regs[i].expand(regs[i+2])
            i += 3
        else:
            i += 1
    return _regs

def split_vert(im,src):
    # split region "rsrc" along vertical gutters
    regs = []
    cur_r = None
    for x in range(src.x0,src.x1+1):
        _sum = 0
        ub = min(src.y0 + 6,src.y1)
        for y in range(src.y0,ub+1):
            _sum += im.pix[x,y]
        v_bg = int (_sum / (ub-src.y0 +1))
        n_pix_fg = 0
        for y in range(src.y0,src.y1+1):
            if abs(im.pix[x,y] - v_bg) > EPSILON:
                n_pix_fg += 1
                if n_pix_fg > MIN_PIX_FG:
                    break
        if n_pix_fg < MIN_PIX_FG:
            # a white line
            cur_r = None
        else:
            if cur_r is None:
                cur_r = Reg(x,src.y0,x,src.y1)
                regs.append(cur_r)
            else:
                cur_r.x1 = x
    if len(regs) == 0:
        return [src]
    # merge regions as needed
    regs = merge_regions('vert',regs)
    # assign col indices
    for i in range(0,len(regs)):
        regs[i].ixcol = i
    return regs

def split_hor(im,src):
    # split region "rsrc" along horizontal gutters
    regs = []
    cur_r = None
    for y in range(src.y0,src.y1+1):
        _sum = 0
        ub = min(src.x0 + 6,src.x1)
        for x in range(src.x0,ub+1):
            _sum += im.pix[x,y]
        v_bg = int (_sum / (ub-src.x0 +1))
        n_pix_fg = 0
        for x in range(src.x0,src.x1+1):
            if abs(im.pix[x,y] - v_bg) > EPSILON: 
                n_pix_fg += 1
                if n_pix_fg > MIN_PIX_FG:
                    break
        if n_pix_fg < MIN_PIX_FG:
            # a white line
            cur_r = None
        else:
            if cur_r is None:
                cur_r = Reg(src.x0,y,src.x1,y)
                regs.append(cur_r)
            else:
                cur_r.y1 = y
    if len(regs) == 0:
        return [src]
    # merge regions as needed
    regs = merge_regions('hor',regs)
    # assign row indices
    for i in range(0,len(regs)):
        regs[i].ixrow = i
    return regs

def get_regions(im):
    r = Reg(0,0,im.w-1,im.h-1)
    panel_regs = []
    cols = split_vert(im,r)
    if len(cols) > 1:
        for ixcol in range(0,len(cols)):
            regs = split_hor(im,cols[ixcol])
            for ixrow in range(0,len(regs)):
                r = regs[ixrow]
                r.ixcol = ixcol
                r.ixrow = ixrow
                panel_regs.append(r)
    else:
        rows = split_hor(im,r)
        for ixrow in range(0,len(rows)):
            regs = split_vert(im,rows[ixrow])
            for ixcol in range(0,len(regs)):
                r = regs[ixcol]
                r.ixcol = ixcol
                r.ixrow = ixrow
                panel_regs.append(r)
    # sort
    for i in range(0,len(panel_regs)-1):
        for j in range(i+1,len(panel_regs)):
            rI = panel_regs[i]
            rJ = panel_regs[j]
            if ((rJ.ixrow < rI.ixrow) or 
                ((rJ.ixrow == rI.ixrow) and
                    (rJ.ixcol < rI.ixcol))):
                panel_regs[i] = rJ
                panel_regs[j] = rI

    return panel_regs

##def reformat_image(w,h,im):
##    # reformat image so it fits inside rectangle (w,h)
##    (src_w,src_h) = im.size
##    src_ar = float(src_h)/src_w
##    dst_ar = float(h)/w
##    if src_ar > dst_ar:
##        # scale by height
##        h_dst = h
##        top_mar = 0
##        scale = float(h)/src_h
##        w_dst = int(src_w*scale)
##        left_mar = int((w-w_dst)/2)
##    else:
##        # scale by width
##        w_dst = w
##        left_mar = 0
##        scale = float(w)/src_w
##        h_dst = int(src_h*scale)
##        top_mar = int((h-h_dst)/2)
##    dst = Image.new("RGB",(w,h), (255,255,255))
##    src = im.resize((w_dst,h_dst)).convert('RGBA')
##    dst.paste(src,(left_mar,top_mar),mask=src)
##    return dst

def reformat_image(w,h,im):
    # reformat image so that:
    # width of tall, skinny images is at most "w"
    # height of short, wide images is at most "h"
    # if image fits within (w,h), just return copy of original
    (src_w,src_h) = im.size
    if (src_w <= w) and (src_h <= h):
        return im.copy()
    src_ar = float(src_h)/src_w
    dst_ar = float(h)/w
    if src_ar < dst_ar:
        # scale by height
        h_dst = h
        scale = float(h)/src_h
        w_dst = int(src_w*scale)
    else:
        # scale by width
        w_dst = w
        scale = float(w)/src_w
        h_dst = int(src_h*scale)
    return im.resize((w_dst,h_dst))


def write_panels(fsrc,fnbase,outdir,im_recs,opts):
    # options are:
    # "w": panel width
    # "h": panel height
    # "trim_mar": trim margins
    # "split_pan": split panels
    # "ext": extension for output files ('png' or 'jpg')
    w_wanted = opts['w']
    split_pan = opts['split_pan']
    trim_mar = opts['trim_mar']
    im = Im(fsrc)
    # the file "fsrc" is broken into 1 or more regions, each
    # becomes a panel.
    if not (trim_mar or split_pan):
        # Use the whole image
        regs = [Reg(0,0,im.w-1,im.h-1)]
    else:
        # split into panels
        regs = get_regions(im)
        if not split_pan:
            # knit panels back into single region. Result is
            # original image with margins trimmed.
            if len(regs) > 1:
                r0 = regs[0]
                for r in regs[1:]:
                    r0.expand(r)
                regs = [r0]   
    # write out the images for the panels.
    view_w = opts['w']
    view_h = opts['h']
    for i in range(0,len(regs)):
        r = regs[i]
        r_im = im.im_pil.crop((r.x0,r.y0,r.x1,r.y1))
        r_im = reformat_image(view_w, view_h,r_im)
        if len(regs) == 1:
            fn = fnbase
        else:
            fn = '%s.%d' % (fnbase,(i+1))
        path = '%s/%s.%s' % (outdir,fn,opts['ext'])
        r_im.save(path,optimize=True)
        # compute cam0 for panel 
        (im_w, im_h) = r_im.size
        im_recs.append( (fn,im_w,im_h) )

def ut_write_panels():
    # this test presumes the devtest directory exits.
    im_recs = []
    with open('devtest/dollhouse.png','rb') as fim:
        write_panels(fim,"dollhouse","devtest/out",im_recs,
                {'w':600, 'h':600, 'split_pan':True, 'trim_mar':True})
    for imr in im_recs:
        print('%s %s' % (imr[0], imr[1].str()))

#ut_write_panels()

def ut_get_tween():
    r_src = Reg(100,100,200,200)
    r_dst = Reg(100,100,400,400)
    nframes = 4
    print('r_src: ' + r_src.str())
    print('r_dst: ' + r_dst.str())
    print("tweens:")
    for i in range(0,4):
        r_tw = r_src.get_tween(r_dst,i,nframes)
        print(r_tw.str())

#ut_get_tween()
