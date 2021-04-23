import os
from PIL import ImageTk,Image,ImageDraw,ImageFont,ImageOps
import tkinter as tk
import tkinter.messagebox as msgbox
import imageio
import images
import io
import math
from images import Reg
import imgpool as ip

# header for comiola project file
proj_file_header = 'comiola ver1.0'

# the display is global: this set in comiola.py
display = None

class Pt:
    def __init__(self,x,y,
        param=0.0, z=0.0, rot=0.0, w=0.0, h=0.0):
        self.x = x
        self.y = y
        self.param = param
        self.z = z
        self.rot = rot
        self.w = w
        self.h = h

    def clone(self):
        return Pt(self.x,self.y,self.param,self.z,self.rot,self.w,self.h)

    def serialize(self):
        return ('%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f' %
            (self.x,self.y,self.param,self.z,self.rot,self.w,self.h))

    @classmethod
    def unserialize(cls,src):
        lst = src.split(',')
        return Pt(
            float(lst[0]),
            float(lst[1]),
            float(lst[2]),
            float(lst[3]),
            float(lst[4]),
            float(lst[5]),
            float(lst[6]))

    def move_to(self,x,y):
        self.x = x
        self.y = y

    def set_wh(self,w,h):
        self.w = w
        self.h = h


class Ani:
    def __init__(self,fnlst,tS,tE,cycles,frames_per_cell):
        self.fnlst = fnlst
        self.tS = tS
        self.tE = tE
        self.cycles = cycles
        self.frames_per_cell = frames_per_cell
        self.path = []
        self.is_cam = False
 
    def clone(self):
        cl = Ani(self.fnlst, self.tS, self.tE,
                self.cycles,self.frames_per_cell)
        cl.is_cam = self.is_cam
        for p in self.path:
            cl.path.append(p.clone())
        return cl

    def serialize(self):
        lst = []
        lst.append(','.join(self.fnlst))
        lst.append('%.3f' % self.tS)
        lst.append('%.3f' % self.tE)
        lst.append('%.3f' % self.cycles)
        lst.append('%.3f' % self.frames_per_cell)
        for p in self.path:
            lst.append(p.serialize())
        return  'ani' + ' '.join(lst)

    @classmethod
    def unserialize(cls,src):
        src = src[3:]
        lst = src.split(' ')
        ani = Ani(
            lst[0].split(','),
            float(lst[1]),
            float(lst[2]),
            float(lst[3]),
            float(lst[4]),
            )
        i = 5
        while i<len(lst):
            ani.path.append(Pt.unserialize(lst[i]))
            i += 1
        return ani

    def xlate_path(self,xdelta,ydelta):
        for p in self.path:
            p.x += xdelta
            p.y += ydelta

    def set_path_params(self):
        path = self.path
        if len(path) == 0:
            return
        if len(path) == 1:
            path[0].param = 0.0
            return
        dist = 0.0
        for i in range(1,len(path)):
            p = path[i]
            prv = path[i-1]
            delta = math.sqrt(
                (p.x - prv.x)**2 + (p.y - prv.y)**2 )
            dist += delta
            p.dist = dist
        path[0].dist = 0.0
        for p in path:
            p.param = p.dist/dist

    def add_pt(self,pt):
        self.path.append(pt)
        self.set_path_params()

    def delete_pt(self,pt):
        self.path.remove(pt)
        self.set_path_params()

    def interpolate_pt(self,targ):
        # given a param value "targ" (0<=targ<=1) get
        # corresponding pt.
        path = self.path
        if len(path) == 1:
            return path[0].clone()
        for i in range(1,len(path)):
            p = path[i]
            prv = path[i-1]
            if targ >= prv.param and targ <= p.param:
                dp = targ - prv.param

                # "dv_dp is the derivative dv/dp
                dv_dp = (p.x - prv.x)/(p.param - prv.param)
                x = prv.x + dv_dp * dp  

                dv_dp = (p.y - prv.y)/(p.param - prv.param)
                y = prv.y + dv_dp * dp  

                dv_dp = (p.z - prv.z)/(p.param - prv.param)
                z = prv.z + dv_dp * dp  

                dv_dp = (p.rot - prv.rot)/(p.param - prv.param)
                rot = prv.rot + dv_dp * dp  

                dv_dp = (p.w - prv.w)/(p.param - prv.param)
                w = prv.w + dv_dp * dp  

                dv_dp = (p.h - prv.h)/(p.param - prv.param)
                h = prv.h + dv_dp * dp  

                return Pt(x,y,targ,z,rot,w,h)
        return path[-1].clone()

class TextEl:
    def __init__(self,fontname,fontsize,fontcolor,bgspec='null'):
        self.fontname = fontname
        self.fontsize = fontsize
        self.fontcolor = fontcolor
        self.bgspec = bgspec
        # Note: caller must explicitly set "text" attribute via
        # "set_text"
        self.text = ''
        self.lo_text = Pt(0.0,0.0)
        self.lo_bg = Pt(0.0,0.0)

    def clone(self):
        te = TextEl(
            self.fontname,self.fontsize,self.fontcolor,
            self.bgspec)
        te.text = self.text
        te.lo_text = self.lo_text.clone()
        te.lo_bg = self.lo_bg.clone()
        return te

    def serialize(self):
        s = '%s %s %s %s' % (
            self.fontname, self.fontsize,self.fontcolor, self.bgspec)
        s += ' %s' % self.lo_text.serialize()
        s += ' %s' % self.lo_bg.serialize()
        return 'txt%s\n%s' % (s,self.text.replace('\n','^'))

    @classmethod
    def unserialize(cls,src):
        # 2-line serialization: line1 is element, line2 is content
        lst = src[0][3:].split(' ')
        te = TextEl( lst[0], lst[1], lst[2], lst[3])
        te.lo_text = Pt.unserialize(lst[4])
        te.lo_bg = Pt.unserialize(lst[5])
        te.text = src[1].replace('^','\n')
        return te

    def dump_lo(self):
        # dev method
        lo = self.lo_text
        print( 'lo_text. x:%.2f y:%.2f w:%.2f h:%.2f' %
            (lo.x,lo.y,lo.w,lo.h))
        lo = self.lo_bg
        print( 'lo_bg. x:%.2f y:%.2f w:%.2f h:%.2f' %
            (lo.x,lo.y,lo.w,lo.h))

    def do_layout(self,xc,yc):
        # set layouts for text & bg: xc,yc are coords for text center
        self.lo_text.move_to(xc,yc)
        (w,h) = measure_text(self.text,self.fontname,self.fontsize)
        self.lo_text.set_wh(w,h)
        mar = 10
        self.lo_bg.move_to(xc,yc)
        self.lo_bg.set_wh(w + 2*mar, h + 2*mar)

    def move_to(self,xc,yc):
        xoff = self.lo_bg.x - self.lo_text.x
        yoff = self.lo_bg.y - self.lo_text.y
        self.lo_text.move_to(xc,yc)
        self.lo_bg.move_to(xc+xoff,yc+yoff)

    def set_text(self,text,xc,yc):
        # set text & place center at (xc,yc)
        self.text = text
        self.do_layout(xc,yc)

class Shot:
    # A shot is:
    # "tks" -- weight (number of ticks) for this shot.
    # "cam" -- an Ani representing the camera (it's "fn" attribute gives 
    #          the background image for the shot;
    # "sprites" -- list of Ani objects for the sprites
    # "textels" -- list of text elements. 
    def __init__(self,tks,cam):
        self.tks = tks
        self.cam = cam
        cam.is_cam = True
        self.sprites = []
        self.textels = []

    def clone(self):
        sh = Shot(self.tks, self.cam.clone())
        for e in self.sprites:
            sh.sprites.append(e.clone())
        for e in self.textels:
            sh.textels.append(e.clone())
        return sh

    def has_bg_illo(self):
        return not self.cam.fnlst[0].startswith('#')

    def get_bgspec(self):
        return self.cam.fnlst[0]

    def set_bgspec(self,spec):
        self.cam.fnlst[0] = spec

    def get_bg_pil(self):
        bgspec = self.cam.fnlst[0]
        if bgspec.startswith('#'):
            return Image.new("RGB",(600,600),bgspec)
        else:
            return ip.get(bgspec,'').copy()

    def preload(self):
        if self.has_bg_illo():
            ip.get(self.cam.fnlst[0],'')
        for spr in self.sprites:
            for fn in spr.fnlst:
                ip.get(fn,'RGBA')
        for te in self.textels:
            get_font(te.fontname,te.fontsize)

    def serialize(self):
        terms = ['%.2f' % self.tks]
        terms.append(self.cam.serialize())
        for e in self.sprites:
            terms.append(e.serialize())
        for e in self.textels:
            terms.append(e.serialize())
        return '\n'.join(terms)

    @classmethod
    def unserialize(cls,lines):
        sh = Shot(
            float(lines[0].strip()),
            Ani.unserialize(lines[1].strip())
            )
        i = 2
        while i < len(lines):
            li = lines[i]
            if li.startswith('ani'):
                sh.sprites.append(Ani.unserialize(lines[i].strip()))
                i += 1
            elif li.startswith('txt'):
                sh.textels.append(TextEl.unserialize(lines[i:i+2]))
                i += 2
        return sh

class Script:
    def __init__(self):
        self.time = 10.0
        self.shots = []

    def cnt_shots(self):
        return len(self.shots)

    def serialize(self):
        lst = [proj_file_header]
        lst.append('%f' % self.time)
        for s in self.shots:
            lst.append(s.serialize())
        return '\n\n'.join(lst)

    @classmethod
    def unserialize(cls,src):
        s = Script()
        blks = src.strip().split('\n\n')
        # blks[0] gives version number: currently not used.
        # blks[1] gives video time for the piece
        s.time = float(blks[1])
        i = 2
        while i < len(blks):
            s.shots.append(Shot.unserialize(blks[i].split('\n')))
            i += 1
        return s

script = Script()
proj_dir = ''
proj_name = ''
proj_filepath = ''
# the script, serialized, at project start
script0_serialized = ''

def script_open():
    return proj_dir != ''

def script_changed():
    global script0_serialized
    return  (proj_filepath != '' and 
            script0_serialized != script.serialize())

def cnt_shots():
    return len(script.shots)

def get_shot(ix):
    if ix < 0 or ix >= cnt_shots():
        return None
    else:
        return script.shots[ix]

def save_script(name):
    global proj_name,proj_filepath,script0_serialized
    if name != '':
        if not name.endswith('.cprj'):
            name += '.cprj'
        proj_name = name
        proj_filepath = '%s/%s' % (proj_dir,proj_name)
    with open(proj_filepath,'w') as f:
        f.write(script.serialize())
        script0_serialized = script.serialize().strip()

def open_project(d,name,create):
    global proj_dir,proj_name,proj_filepath,script,script0_serialized
    while d.endswith('/'):
        d = d[-1]
    proj_dir = d
    proj_name = name
    if not proj_name.endswith('.cprj'):
        proj_name += '.cprj'
    proj_filepath = '%s/%s' % (d,proj_name)
    if create:
        script = Script()
        save_script(proj_name)
    else:
        try:
            with open(proj_filepath,'r') as f:
                src = f.read()
                if not src.startswith('comiola ver'):
                    msgbox.showerror('Comiola',
                        '"%s" is not a Comiola project' % proj_filepath)
                    return False
                script = Script.unserialize(src)
                script0_serialized = script.serialize().strip()
        except:
            msgbox.showerror('Comiola',
                'Could not read "%s/%s"' % (d,name))
            proj_filepath = ''
            return False
    ip.proj_dir = proj_dir
    return True

def extend_script(newshots,add_after):
    # rebuild the shot list, including the new shots
    # add_after == -1 means include at head
    shots = script.shots
    _shots = []
    if add_after != -1:
        _shots = shots[0:add_after+1]
    _shots.extend(newshots)
    if add_after + 1 < len(shots) -1:
        _shots.extend(shots[add_after+1 : ])
    script.shots = _shots

def add_shots(fnames,add_after,split,trim):
    imrecs = []
    for fn in fnames:
        print(fn)
        (head,tail) = os.path.split(fn)
        root = tail.split('.')[0]
        print(root)
        with open(fn,'rb') as fim:
            images.write_panels(fim,root,proj_dir,imrecs,
{'w':600, 'h':600, 'split_pan':split, 'trim_mar':trim,'ext':'jpg'})
    shots = []
    for imr in imrecs:
        (fn,im_w,im_h) = imr
        cam_w = min(im_w,im_h)
        cam = Ani([fn],0.0,1.0,1.0,4)
        xc = int(im_w/2)
        yc = int(im_h/2)
        cam.path.append(Pt(xc,yc, 0.0, 0.0,0.0,cam_w,cam_w))
        cam.is_cam = True
        shots.append(Shot(10.0,cam))

    for s in shots:
        print('Wrote %s' % s.cam.fnlst[0])

    # rebuild the shot list, including the new shots
    extend_script(shots,add_after)

def add_blank_shot(ixafter,color):
    cam = Ani([color],0.0,1.0,1.0,4)
    cam_w = 600
    cam.path.append(Pt(300, 300, 0.0, 0.0,0.0,cam_w,cam_w))
    cam.is_cam = True
    extend_script( [Shot(10.0,cam)], ixafter)

def clone_shot(ix):
    extend_script([get_shot(ix).clone()],ix)

def delete_shots(ixS,ixE):
    _shots = []
    deleted = []
    for i in range(0,len(script.shots)):
        if i < ixS or i > ixE:
            _shots.append(script.shots[i])
        else:
            deleted.append(script.shots[i])
    script.shots = _shots
    return deleted

def copy_shots(ixS,ixE):
    _shots = []
    for i in range(ixS,ixE+1):
        _shots.append(script.shots[i].clone())
    return _shots

def install_sprite(fn):
    # write sprite to project dir as needed
    (head,tail) = os.path.split(fn)
    root = tail[:-4]
    print(root)
    if head != proj_dir:
        with Image.open(fn).convert('RGBA') as src:
            src = images.reformat_image(300,300,src)
            src.save('%s/%s.png' % (proj_dir,root))
    # create fipped version as needed
    fpmir = '%s/mir.%s.png' % (proj_dir,root)
    if not os.path.isfile(fpmir):
        fpsrc = '%s/%s.png' % (proj_dir,root)
        with Image.open(fpsrc).convert('RGBA') as src:
            ImageOps.mirror(src).save(fpmir,quality=95)

def add_sprite(xc,yc,ixshot,fnlst):
    ar = ip.get_ar(fnlst[0],'RGBA')
    if ar <= 1.0:
        w = 180
        h = int(.5 + ar*w)
    else:
        h = 180
        w = int(.5 + h/ar)
    spr = Ani(fnlst,0.0,1.0,1.0,4)
    spr.path.append(Pt(xc,yc,0.0, 0.0,0.0,w,h))
    get_shot(ixshot).sprites.append(spr)
    return spr

def delete_sprite(ixshot,spr):
    s = get_shot(ixshot)
    lst = []
    for x in s.sprites:
        if x != spr:
            lst.append(x)
    s.sprites = lst

def add_te(xc,yc,ixshot,text,fontname,fontsize,color):
    te = TextEl(fontname,fontsize,color)
    te.set_text(text,xc,yc)
    get_shot(ixshot).textels.append(te)
    return te

def delete_te(ixshot,te):
    get_shot(ixshot).textels.remove(te)

# text elements: we pool fonts
font_pool = {}

def get_font(fontname,fontsize):
    # get font for a text element
    key = fontname+fontsize
    font =  font_pool.get(key) 
    if font is not None:
        return font
    fontsize = int( fontsize[:-2] )
    #print('./res/%s.ttf' % fontname)
    font = ImageFont.truetype('./res/%s.ttf' % fontname,fontsize)
    font_pool[key] = font
    return font

def measure_text(text,fontname,fontsize):
    # get (w,h) for text
    font = get_font(fontname,fontsize)
    lines = text.split('\n')
    w = 0
    h = 0
    for li in lines:
        wx,hx = font.getsize(li)
        h += hx
        w = max(w,wx)
    return (float(w),float(h))

