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
proj_file_header = 'comiola 0.1'

# the display is global: this set in comiola.py
display = None

class Pt:
    def __init__(self,x,y,
        param=0.0, z=0.0, rot=0.0, w=0.0, h=0.0):
        self.x = float(x)
        self.y = float(y)
        self.param = float(param)
        self.z = float(z)
        self.rot = float(rot)
        self.w = float(w)
        self.h = float(h)

    def clone(self):
        return Pt(self.x,self.y,self.param,self.z,self.rot,self.w,self.h)

    def serialize(self):
        return ('%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f' %
            (self.x,self.y,self.param,self.z,self.rot,self.w,self.h))

    @classmethod
    def unserialize(cls,src):
        lst = src.split(',')
        return Pt(*(src.split(',')))

    def set_xy(self,x,y):
        self.x = x
        self.y = y

    def set_wh(self,w,h):
        self.w = w
        self.h = h


class Ani:
    def __init__(self,kind,tS,tE,cycles,frames_per_cell):
        # kind: "spr","cam","txt"
        self.kind = kind
        self.tS = float(tS)
        self.tE = float(tE)
        self.cycles = float(cycles)
        self.frames_per_cell = float(frames_per_cell)
        self.path = []
 
    def clone(self):
        cl = Ani(self.kind, self.tS, self.tE,
                self.cycles,self.frames_per_cell)
        for p in self.path:
            cl.path.append(p.clone())
        if self.kind == 'spr':
            cl.fnlst = self.fnlst[:]
        elif self.kind == 'te':
            cl.te = self.te.clone()
        return cl

    def serialize(self):
        lst = [self.kind]
        lst.append('%.3f' % self.tS)
        lst.append('%.3f' % self.tE)
        lst.append('%.3f' % self.cycles)
        lst.append('%.3f' % self.frames_per_cell)
        for p in self.path:
            lst.append(p.serialize())
        return ' '.join(lst)

    @classmethod
    def unserialize(cls,src):
        lst = src.split(' ')
        ani = Ani(*lst[0:5])
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
        pt.ani = self
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
    def __init__(self,fontname,fontsize,fontcolor,
            bgspec='null',
            w_txt = 0.0,
            h_txt = 0.0,
            w_bg = 0.0,
            h_bg = 0.0,
            yoff_bg = 0.0):
        self.fontname = fontname
        self.fontsize = fontsize
        self.fontcolor = fontcolor
        self.bgspec = bgspec
        self.w_txt = float(w_txt)
        self.h_txt = float(h_txt)
        self.w_bg = float(w_bg)
        self.h_bg = float(h_bg)
        self.yoff_bg = float(yoff_bg)
        # use get_text and set_text for this value.
        self._text = ''

    def get_text(self):
        return self._text

    def set_text(self,text):
        self._text = text
        self.set_layout()

    def clone(self):
        cl = TextEl(
            self.fontname,self.fontsize,self.fontcolor, self.bgspec,
            self.w_txt, self.h_txt, self.w_bg, self.h_bg, self.yoff_bg)
        cl._text = self._text
        return cl

    def serialize(self):
        return '%s %s %s %s %.3f %.3f %.3f %.3f %.3f' % (
            self.fontname, self.fontsize,self.fontcolor, self.bgspec,
            self.w_txt, self.h_txt,
            self.w_bg, self.h_bg, self.yoff_bg)

    @classmethod
    def unserialize(cls,src):
        return TextEl(*src.split(' '))

    def set_layout(self):
        # measure text
        im = Image.new('RGB',(600,600))
        draw = ImageDraw.Draw(im)
        draw.text((0,0),self._text,fill=(255,255,255),
                font=get_font(self.fontname,self.fontsize))
        (x0,y0,x1,y1) = im.getbbox()
        # we provide a margin so the bg is a bit larger 
        # than the text.
        mar = 10
        (self.w_txt, self.h_txt) = (x1+1, y1+1) 
        (self.w_bg, self.h_bg) = (
            self.w_txt + 2*mar,
            self.h_txt + 2*mar) 
        self.yoff_bg = 0

    def get_bb_bg(self,xc,yc):
        # given (x,y) of center, get bounding box for bg
        w = int(self.w_bg/2)
        h = int(self.h_bg/2)
        yoff = int(self.yoff_bg)
        return (xc-w, yc-h+yoff, xc+w, yc+h+yoff)

    def get_bb_text(self,xc,yc):
        # given (x,y) of center, get bounding box for text
        w = int(self.w_txt/2)
        h = int(self.h_txt/2)
        return (xc-w, yc-h, xc+w, yc+h)

class Shot:
    # A shot is:
    # "tks" -- weight (number of ticks) for this shot.
    # "cam" -- an Ani representing the camera 
    # "bgspec" -- bg spec for the shot. Either a color value ('#ff0000')
    #             or a filename (minus file extension)
    # "anis" -- list of Ani objects for the sprites & text
    def __init__(self,tks,bgspec,cam=None):
        self.tks = float(tks)
        self.bgspec = bgspec
        self.cam = cam
        self.anis = []

    def clone(self):
        sh = Shot(self.tks, self.bgspec, self.cam.clone())
        for e in self.anis:
            sh.sprAnis.append(e.clone())
        return sh

    def has_bg_illo(self):
        return not self.bgspec.startswith('#')

    def get_bg_pil(self):
        bgspec = self.bgspec
        if bgspec.startswith('#'):
            return Image.new("RGB",(600,600),bgspec)
        else:
            return ip.get(bgspec,'').copy()

    def preload(self):
        if self.has_bg_illo():
            ip.get(self.bgspec,'')
        for ani in self.anis:
            if (ani.kind == 'spr'):
                for fn in ani.fnlst:
                    ip.get(fn,'RGBA')
            elif ani.kind == 'txt':
                get_font(ani.te.fontname,ani.te.fontsize)

    def serialize(self):
        return '%.3f %s' % (self.tks,self.bgspec)

    @classmethod
    def unserialize(cls,src):
        return Shot(*(src.split(' ')))

    def partition_anis(self):
        # split ani's into two sets, "spr" and "txt"
        spr = []
        txt = []
        for a in self.anis:
            if a.kind=='spr':
                spr.append(a)
            else:
                txt.append(a)
        return [spr,txt]

class Script:
    def __init__(self):
        self.time = 10.0
        self.shots = []

    def cnt_shots(self):
        return len(self.shots)

    def serialize(self):
        lines = [proj_file_header]
        lines.append('%f' % self.time)
        for s in self.shots:
            lines.append(s.serialize())
            lines.append(s.cam.serialize())
            for ani in s.anis:
                lines.append(ani.serialize())
                if ani.kind == 'spr':
                    lines.append(','.join(ani.fnlst))
                elif ani.kind == 'txt':
                    lines.append(ani.te.serialize())
                    lines.append(ani.te._text.replace(' ','^'))
            lines.append('')
        return '\n'.join(lines)

    @classmethod
    def unserialize(cls,src):
        lines = src.split('\n')
        s = Script()
        # line0 is version: currently ignored
        s.time = float(lines[1])
        # remaining lines are shots, delimited by blank lines
        i = 2
        while i < len(lines) and lines[i].strip() != '':
            sh = Shot.unserialize(lines[i])
            s.shots.append(sh)
            i += 1
            # get camera
            sh.cam = Ani.unserialize(lines[i])
            i += 1
            # get anis
            while i < len(lines) and lines[i] != '':
                ani = Ani.unserialize(lines[i])
                i += 1
                sh.anis.append(ani)
                if ani.kind == 'txt':
                    ani.te = TextEl.unserialize(lines[i])
                    i += 1
                    ani.te._text = lines[i].replace('^',' ')
                    i += 1
                elif ani.kind == 'spr':
                    ani.fnlst = lines[i].split(',')
                    i += 1
            # skip blank line delim
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

def close_project():
    global script, proj_dir, proj_name, proj_filepath
    script = Script()
    proj_dir = ''
    proj_name = ''
    proj_filepath = ''

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
        script0_serialized = script.serialize()

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
                script = Script.unserialize(src)
                script0_serialized = script.serialize()
        except:
            msgbox.showerror('Comiola',
                'Could not read "%s/%s"' % (d,name))
            proj_filepath = ''
            return False
    ip.proj_dir = proj_dir
    return True

def close_project():
    global script, proj_dir, proj_name, proj_filepath
    script = Script()
    proj_dir = ''
    proj_name = ''
    proj_filepath = ''

def extend_script(newshots,add_after):
    # rebuild the shot list, including the new shots
    # add_after == -1 means include at head
    shots = script.shots
    _shots = []
    if add_after != -1:
        _shots = shots[0:add_after+1]
    _shots.extend(newshots)
    if add_after + 1 < len(shots):
        _shots.extend(shots[add_after+1 : ])
    script.shots = _shots

def add_shots(fnames,add_after,split,trim):
    imrecs = []
    for fn in fnames:
        (head,tail) = os.path.split(fn)
        root = tail.split('.')[0]
        with open(fn,'rb') as fim:
            images.write_panels(fim,root,proj_dir,imrecs,
{'w':600, 'h':600, 'split_pan':split, 'trim_mar':trim,'ext':'jpg'})
    shots = []
    for imr in imrecs:
        (fn,im_w,im_h) = imr
        cam_w = min(im_w,im_h)
        cam = Ani('cam',0.0,1.0,1.0,4)
        xc = int(im_w/2)
        yc = int(im_h/2)
        cam.path.append(Pt(xc,yc, 0.0, 0.0,0.0,cam_w,cam_w))
        shots.append(Shot(10.0,fn,cam))

    # rebuild the shot list, including the new shots
    extend_script(shots,add_after)

def add_blank_shot(ixafter,color):
    cam = Ani('cam',0.0,1.0,1.0,4)
    cam_w = 600
    cam.path.append(Pt(300, 300, 0.0, 0.0,0.0,cam_w,cam_w))
    extend_script( [Shot(10.0,color,cam)], ixafter)

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

def add_ani(kind,ixshot,te=None,fnlst=None):
    ani = Ani(kind,0.0,1.0,1.0,4)
    ani.te = te
    ani.fnlst = fnlst
    get_shot(ixshot).anis.append(ani)
    return ani

def delete_ani(ixshot,ani):
    s = get_shot(ixshot)
    s.anis.remove(ani)

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

