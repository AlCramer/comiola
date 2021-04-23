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

class AniState:
    # state of animation
    def __init__(self,ixS,ixE,msecs_frame):
        self.ixshot = ixS
        self.ixE = ixE
        self.msecs_frame = msecs_frame
        self.ixframe = 0
        self.img_pil = None

def get_tween(ani,shot,ixframe):
    # return (z,fn,x0,y0,w,h) for a tween

    # get parameter for "ixframe"; also fn for cell
    fn = ani.fnlst[0]
    param = 0.0
    if shot.nframes > 1:
        # ixfrmS: frame index at which animation starts
        # ixfrmE: frame index at which animation end
        #   (at ixfrmE, param is 1)
        ixfrmS = int(ani.tS * shot.nframes)
        ixfrmE = int(ani.tE * shot.nframes) -1
        if ixframe < ixfrmS:
            param = 0.0
        elif ixframe > ixfrmE:
            param = 1.0
        else:
            if ixfrmE == ixfrmS:
                param = .5
            else:
                param = float(ixframe - ixfrmS)/(ixfrmE - ixfrmS)
                # correct for cycles
                ix = ixframe - ixfrmS
                ix = int(.5 + ix * ani.cycles)
                nfrmAni = ixfrmE - ixfrmS + 1
                ix = ix % nfrmAni
                param = ix / float(nfrmAni-1) 
                if len(ani.fnlst) > 0:
                    ixcell = int(ix/ani.frames_per_cell)
                    ixcell = ixcell % len(ani.fnlst)
                    fn = ani.fnlst[ixcell]

    # get a pt for this spot in the path
    pt = ani.interpolate_pt(param)
    whalf = pt.w/2
    hhalf = pt.h/2
    return (
            pt.z,
            fn,
            pt.rot,
            int(.5 + pt.x - whalf),
            int(.5 + pt.y - hhalf),
            int(.5 + pt.w),
            int(.5 + pt.h)
            )

def get_frame_pil(shot,ixframe):
    # create a pil image for the frame: caller is responsible
    # for closing.

    # img_dst: PIL image which we draw upon (it's the bg for
    # the shot).
    img_dst = shot.get_bg_pil()
    # draw the sprites
    # "tween": (z,fn,x0,y0,w,h) for a sprite
    # We compute tween for each sprite, then sort by Z
    # and draw
    tweens = []
    for spr in shot.sprites:
        tweens.append(get_tween(spr,shot,ixframe))
    tweens.sort()
    for t in tweens:
        (z,fn,rot,x0,y0,w,h) = t
        #print('debug tween. x0: %d y0:%d w:%d h:%d' % (x0,y0,w,h))
        img = ip.get(fn,'RGBA').resize((w,h),Image.ANTIALIAS)
        if rot != 0.0:
            _img = img.rotate(rot)
            img.close()
            img = _img
        img_dst.paste(img,(x0,y0),mask=img)
        #img.close()

    # draw text elements
    draw_pil = ImageDraw.Draw(img_dst)
    for te in shot.textels:
        # bg
        if te.bgspec != 'null':
            spec = te.bgspec
            lo = te.lo_bg
            (x,y,w,h) = (lo.x,lo.y,lo.w,lo.h)
            if spec.startswith('#'):
                (x0,y0,x1,y1) = (
                    int(x-w/2), int(y-h/2),
                    int(x+w/2), int(y+h/2))
                draw_pil.rectangle((x0,y0,x1,y1),fill=spec)
            else:
                (x,y,w,h) = ( int(x-w/2),int(y-h/2),int(w),int(h) )
                img = ip.get_res(spec).resize(
                    (w,h),Image.ANTIALIAS)
                img = img.resize((w,h), Image.ANTIALIAS)
                img_dst.paste(img,(x,y),mask=img)
        # text
        font = get_font(te.fontname,te.fontsize)
        lo = te.lo_text
        (x,y,w,h) = (lo.x,lo.y,lo.w,lo.h)
        (x,y) = ( int(x-w/2),int(y-h/2) )
        draw_pil.text( (x,y),
                te.text, fill=te.fontcolor, font=font) 

    # crop img_dst as per the bg animation and resize
    (z,fn,rot,x0,y0,w,h) = get_tween(shot.cam,shot,ixframe)
    cropped = img_dst.crop((x0, y0, x0+w-1, y0+h-1))
    img_pil = cropped.resize((608,608),Image.ANTIALIAS)
    cropped.close()
    return img_pil

def animate_shot(state):
    global proj_dir
    s = get_shot(state.ixshot)
    # blit the pre-drawn frame
    display.can.delete('all')
    s.cam.im_tk = ImageTk.PhotoImage(state.img_pil)
    display.can.create_image(display.xmar,display.ymar,
            anchor=tk.NW,image=s.cam.im_tk)
    state.img_pil.close()
    # set up for next shot
    if state.ixframe + 1 < s.nframes:
        state.ixframe += 1
    else:
        # advance to next
        state.ixshot += 1
        state.ixframe = 0
        if state.ixshot == state.ixE:
            # done!
            display.can.after(1, display.edit_shot, display.ixshot)
            return
    # schedule the next frame
    display.can.after( state.msecs_frame, animate_shot, state)
    # pre-draw upcoming shot 
    s = get_shot(state.ixshot)
    s.preload()
    state.img_pil = get_frame_pil(s,state.ixframe)

def set_shot_nframes(fps, _time, ixS,ixE):
    #  for each shot in S..E, compute number of frames
    # return total number of frames
    sumTks = 0
    for i in range(ixS, ixE):
        sumTks += get_shot(i).tks
    # fps -> frames per second
    nframes_total = fps * _time
    total_actual = 0
    for i in range(ixS, ixE):
        s = get_shot(i)
        fract = float(s.tks)/sumTks
        s.nframes = int(.5 + fract*nframes_total)
        total_actual += s.nframes
    return total_actual

def animate_shots(ixS,ixE,_time):
    # animate shot sequence ixS..ixE

    # set number of frames for each shot
    fps = 24
    #fps = 48
    set_shot_nframes(fps, _time, ixS,ixE)
    state = AniState(ixS,ixE, int( 1000/fps))
    # construct first frame
    s = get_shot(ixS)
    s.preload()
    state.img_pil = get_frame_pil(s,state.ixframe)
    # kick off the animation
    animate_shot(state)

def animate_script():
    animate_shots(0,len(script.shots),script.time)

def make_mp4(status_msg):
    # set number of frames for each shot
    fps = 24
    N = script.cnt_shots()
    nframes = set_shot_nframes(fps, script.time, 0, N)
    cnt = 0
    fp = '%s/%svideo.mp4' % (proj_dir,proj_name[:-5])
    with imageio.get_writer(fp, fps = fps, mode='I') as writer:
        for i in range(0,N):
            s = get_shot(i)
            s.preload()
            #print('%d. nframes:%d' % (i,s.nframes))
            for j in range(0,s.nframes):
                img_pil = get_frame_pil(s,j)
                buf = io.BytesIO()
                img_pil.save(buf,'PNG')
                img_pil.close()
                buf.seek(0)
                img = imageio.imread(buf)
                writer.append_data(img)
                cnt += 1
                if cnt % 10 == 0:
                    status_msg['text'] = \
                        ('wrote frame %d of %d ...' % (cnt,nframes))
                    status_msg.update()
    status_msg['text'] = ''
    status_msg.update()
    print('Done...')

def dev_test():
    # This devtest tests:
    # Script.unserialize; ani.interpolate_pt; get_tween
    src =\
"""
10.000000

10.00
aniqwfinal 0.000 1.000 1.000 4.000 339.000,300.000,0.000,0.000,0.000,600.000,600.000
anigoose1,goose2,goose3,goose4 0.000 1.000 1.000 4.000 60.000,125.000,0.000,0.000,0.000,180.000,180.000 240.000,123.000,0.783,0.000,0.000,180.000,180.000 671.000,118.000,1.000,0.000,0.000,180.000,180.000
"""
    scr = Script.unserialize(src.strip())
    shot = scr.shots[0]
    ani = shot.sprites[0]
    shot.nframes = 10

    ani.set_path_params()

    print("path")
    for i in range(0,len(ani.path)):
        pt = ani.path[i]
        print("%d. x:%f y:%f param:%f" % (i,pt.x,pt.y,pt.param))

    print("\ninterpolate_pt results:")
    pts = []
    for i in range(0,shot.nframes):
        pts.append( ani.interpolate_pt(float(i)/shot.nframes) )
    for i in range(0,shot.nframes):
        if i == 0:
            dx = 0.0
        else:
            dx = pts[i].x - pts[i-1].x
        print('%d. x: %f w: %f delta_x: %f' % (i,pts[i].x, pts[i].w, dx))

    print("\ntween results:")
    tweens = []
    for i in range(0,shot.nframes):
        tweens.append( get_tween(ani,shot,i))
    for i in range(0,shot.nframes):
        (z,fn,rot,x0,y0,w,h) = tweens[i]
        xc = x0 + w/2
        if i == 0:
            dx = 0.0
        else:
            dx = xc - xc_prv
        print('%d. xc: %f w: %f delta_x: %f %s' % (i,xc, w, dx,fn))
        xc_prv = xc

#dev_test()

