import os
from PIL import ImageTk,Image,ImageDraw,ImageFont,ImageOps
import tkinter as tk
import imageio
import images
import io
import math
import imgpool as ip
from scripts import get_shot

# the display is global: this set in comiola.py
display = None

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

