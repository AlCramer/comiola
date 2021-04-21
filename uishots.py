import tkinter as tk
import tkinter.messagebox as msgbox
import os

import scripts
import controls
import images
from controls import AniCntrl 
from widgets import *
from uicolors import *

# the display
display = None

# GUI string vars's
add_after = tk.StringVar()
add_blank_color = tk.StringVar()
add_blank_color.set('#ffffff')
shot_bgcolor = tk.StringVar()
playS = tk.StringVar()
playE = tk.StringVar()
play_secs = tk.StringVar()
script_secs = tk.StringVar()
shot_secs = tk.StringVar()
vid_secs = tk.StringVar()
shot_tks = tk.StringVar()
panel_split = tk.IntVar()
panel_trim = tk.IntVar()

def validate_view():
    panel_split.set(0)
    panel_trim.set(0)
    if scripts.script_open():
        enable_but(add_shots)
        enable_but(add_blank_shot)
    if scripts.cnt_shots() == 0:
        add_after.set('')
        vid_secs.set('')
        shot_secs.set('')
        play_secs.set('')
        playS.set('')
        playE.set('')
        shot_tks.set('')
        shot_bgcolor.set('#ffffff')

    else:
        add_after.set('%d' % scripts.cnt_shots())
        scr = scripts.script
        vid_secs.set('%.1f' % scr.time)
        if script_secs.get().strip() == '':
            script_secs.set('%.1f' % scr.time)
        if shot_secs.get().strip() == '':
            shot_secs.set('2.0')
        if play_secs.get().strip() == '':
            play_secs.set('%.1f' % (scr.time/2))
        if playS.get().strip() == '':
            playS.set('1')
        if playE.get().strip() == '':
            playE.set('1')
        shot_tks.set('%.1f' % display.shot.tks)
        if not display.shot.has_bg_illo():
            enable_but(set_shot_bgcolor)
            shot_bgcolor.set(display.shot.get_bgspec())
        on_buts = [clone_shot, set_tks, add_sprite, delete_sprite,
            play_shot, play_seq, play_script, create_video]
        if display.ixshot > 0:
            on_buts.append(set_cam_cont)
        for b in on_buts:
            enable_but(b)

def do_commit():
    if display.ixshot == -1:
        return True
    try:
        display.shot.tks = float(shot_tks.get())
    except ValueError:
        msgbox.showerror('Comiola','"Ticks" value must be a number')
    return True

def set_tks():
    try:
        display.shot.tks = float(shot_tks.get())
    except ValueError:
        msgbox.showerror('Comiola','"Ticks" value must be a number')

def clone_shot():
    ix = display.ixshot
    if ix != -1:
        scripts.clone_shot(ix)
        display.edit_shot(ix + 1)

def play_shot():
    if not display.do_commit():
        return
    ix = display.ixshot
    if ix == -1:
        return
    try:
        v = float(shot_secs.get())
        scripts.animate_shots(ix,ix+1,v)
    except ValueError:
        msgbox.showerror('Comiola','"Secs" value must be a number')
        validate_view()

def play_seq():
    if not display.do_commit():
        return
    try:
        S = max(0,int(playS.get()) -1)
        E = min(int(playE.get()), scripts.cnt_shots())
    except ValueError:
        msgbox.showerror('Comiola','Shot number(s) must be integers')
        return 
    try:
        secs = float(play_secs.get())
    except ValueError:
        msgbox.showerror('Comiola','"Secs" must be a number')
        return 
    scripts.animate_shots(S,E,secs)

def play_script():
    N = scripts.cnt_shots()
    if N == 0:
        return
    if not display.do_commit():
        return
    try:
        v = float(script_secs.get())
    except ValueError:
        msgbox.showerror('Comiola','"Secs" value must be a number')
        return
    scripts.animate_shots(0,N,v)

vid_status_msg = tk.StringVar()

def create_video():
    N = scripts.cnt_shots()
    if N == 0:
        return
    if not do_commit():
        return
    try:
        v = float(vid_secs.get())
        scripts.script.time = v
        scripts.make_mp4(vid_status_msg.peer)
    except ValueError:
        msgbox.showerror('Comiola','"Secs" value must be a number')

def add_sprite():
    names = tk.filedialog.askopenfilenames(
        initialdir=scripts.proj_dir)
    if names == '':
        return
    for fn in names:
        if not fn.lower().endswith('.png'):
            msgbox.showerror('Comiola',
                "File must be PNG with transparent background")
            return
    # write image to project dir as needed; get fn roots
    roots = []
    for fn in names:
        print(fn)
        scripts.install_sprite(fn)
        (head,tail) = os.path.split(fn)
        roots.append(tail[:-4])
    # initial position is center of image
    xc = display.xmar + int(display.w_img/2)
    yc = display.ymar + int(display.h_img/2)
    spr = scripts.add_sprite(xc,yc,display.ixshot,roots)
    AniCntrl(spr,"sprite")
    display.draw_edit()

def delete_sprite():
    if display.sprite_selected():
        scripts.delete_sprite(display.ixshot,display.sel_ani)
        display.sel_ani = None
        display.validate_view()

def set_shot_bgcolor():
    c = shot_bgcolor.get()
    if not isHexColor(c):
        msgbox.showerror('Comiola',
        'Background color must be an HTML style color code')
        return
    display.shot.set_bgspec(c)
    display.validate_view()

def get_ixafter():
    # Convention: no "add_after" value means insert at end
    nshots = scripts.cnt_shots()
    ixafter =  nshots - 1
    vstr = add_after.get().strip()
    if vstr != '':
        try:
            ixafter = int(vstr)
        except:
            msgbox.showerror('Comiola','"after" must be a shot index (or -1)')
            return None
    if ixafter < -1:
        ixafter = -1
    if ixafter > nshots -1:
        ixafter = nshots -1
    return ixafter

def add_shots():
    names = tk.filedialog.askopenfilenames()
    if names == '':
        return
    ixafter = get_ixafter()
    if ixafter is None:
        return
    scripts.add_shots(names,ixafter,
            panel_split.get() == 1,
            panel_trim.get() ==1)
    display.edit_shot(ixafter+1)

def add_blank_shot():
    ixafter = get_ixafter()
    if ixafter is None:
        return
    color = add_blank_color.get()
    if not isHexColor(color):
        msgbox.showerror('Comiola',
'"Color" value must be an HTML-style hex color ("#ff000", etc.)')
        return
    scripts.add_blank_shot(ixafter,color)
    display.edit_shot(ixafter+1)

def set_cam_cont():
    # camera continuity: this shot starts with same camera position/size
    # that ended last shot.
    s = scripts.get_shot(display.ixshot)
    prv = scripts.get_shot(display.ixshot-1)
    s.cam.path[0].x = prv.cam.path[-1].x
    s.cam.path[0].y = prv.cam.path[-1].y
    s.cam.path[0].z = prv.cam.path[-1].z
    s.cam.path[0].w = prv.cam.path[-1].w
    s.cam.path[0].h = prv.cam.path[-1].h
    s.cam.path[0].rot = prv.cam.path[-1].rot
    display.draw_edit()

def make_shotcntrls(container):
    global vid_status_msg
    vid_status_msg = Lab('','cntrls',[2,1])

    rows = [
        [
            But('Add Shots',add_shots,'cntrls',[4,4]),
            Lab('after','cntrls',[4,1]),
            Entry(add_after,4,[1,4]),
            Check(panel_split,'split',[4,4]),
            Check(panel_trim,'trim',[4,4])
        ],
        [
            But('Add Blank Shot',add_blank_shot,'cntrls',[4,4]),
            Lab('after','cntrls',[4,1]),
            Entry(add_after,4,[1,4]),
            Lab('color:','cntrls',[4,1]),
            Entry(add_blank_color,7,[1,4]),
        ],
        [Header("Current Shot:")],
        [ But('Clone Shot', clone_shot,'cntrls',[4,4])],
        [
            But('Set Ticks', set_tks,'cntrls',[4,2]),
            Entry(shot_tks,6,[2,4])
        ],
        [
            Lab('Sprites:','cntrls',[4,4]),
            But('Add',add_sprite,'cntrls',[4,4]),
            But('Delete',delete_sprite,'cntrls',[4,4])
        ],
        [
            But('Set Bg. Color:',set_shot_bgcolor,'cntrls',[4,1]),
            Entry(shot_bgcolor,6,[4,2]),
        ],
        [
            But('Set Cam Continuity',set_cam_cont,'cntrls',[4,1]),
        ],
        [Header("Animation:")],
        [
            But('Play This Shot',play_shot,'cntrls',[4,4]),
            Lab('secs:','cntrls',[2,1]),
            Entry(shot_secs,6,[1,2])
        ],
        [
            But('Play',play_seq,'cntrls',[4,4]),
            Entry(playS,6,[4,2]),
            Lab('..','cntrls',[2,2]),
            Entry(playE,6,[2,1]),
            Lab('secs:','cntrls',[4,1]),
            Entry(play_secs,6,[1,4])
        ],
        [
            But('Play All',play_script,'cntrls',[4,4]),
            Lab('secs:','cntrls',[4,1]),
            Entry(script_secs,6,[1,4])
        ],
        [
            But('Create Video',create_video,'cntrls',[4,4]),
            Lab('secs:','cntrls',[4,1]),
            Entry(vid_secs,6,[1,4])
        ],
        [vid_status_msg]

    ]
    build_table(container,rows)

