import tkinter as tk
import tkinter.messagebox as msgbox

import scripts
from scripts import Pt
import controls
from controls import AniCntrl 
from controls import PtCntrl 
from widgets import *
from uicolors import *

# the display
display = None

# GUI string vars's
tS = tk.StringVar()
tE = tk.StringVar()
cycles = tk.StringVar()
frames_per_cell = tk.StringVar()
ptZ = tk.StringVar()
rot = tk.StringVar()

def validate_view():
    tS.set('')
    tE.set('')
    cycles.set('')
    frames_per_cell.set('')
    ptZ.set('')
    rot.set('')
    if scripts.cnt_shots() > 0:
        enable_but(zoomin)
        enable_but(zoomout)
        if display.sel_ani is not None:
            tS.set( '%.2f' % display.sel_ani.tS )
            tE.set( '%.2f' % display.sel_ani.tE )
            cycles.set( '%.1f' % display.sel_ani.cycles )
            frames_per_cell.set( '%d' % display.sel_ani.frames_per_cell)
            enable_but(clone_sprite)
            enable_but(add_pt)
            enable_but(delete_pt)
            enable_but(on_z)
            enable_but(on_rot)
        if display.sel_pt is not None:
            ptZ.set('%.1f' % display.sel_pt.z)
            rot.set('%.1f' % display.sel_pt.rot)

def do_commit():
    if display.ixshot == -1:
        return True
    if display.sel_ani is None:
        return True
    try:
        display.sel_ani.tS = float(tS.get())
    except ValueError:
        msgbox.showerror('Comiola','"tS" value must be a number')
        return False
    try:
        display.sel_ani.tE = float(tE.get())
    except ValueError:
        msgbox.showerror('Comiola','"tE" value must be a number')
        return False
    try:
        display.sel_ani.cycles = float(cycles.get())
    except ValueError:
        msgbox.showerror('Comiola','"Reps" value must be a number')
        return False
    try:
        display.sel_ani.frames_per_cell = float(frames_per_cell.get())
    except ValueError:
        msgbox.showerror('Comiola','"Frames-per-Cell" value must be a number')
        return False
    if display.sel_pt is None:
        return True
    try:
        display.sel_pt.z = float(ptZ.get())
    except ValueError:
        msgbox.showerror('Comiola','"Z" value must be a number')
        return False
    try:
        display.sel_pt.rot = float(rot.get())
    except ValueError:
        msgbox.showerror('Comiola','"Rot" value must be a number')
        return False
    return True

def zoomin():
    display.scale_im_to_can += .1
    display.draw_edit()

def zoomout():
    display.scale_im_to_can -= .1
    display.draw_edit()

def clone_sprite():
    ani = display.sel_ani
    if ani is None or ani == display.shot.cam:
        return
    # compute initial position: center of image
    #xc = display.xmar + int(display.w_img/2)
    #yc = display.ymar + int(display.h_img/2)
    #spr = scripts.add_sprite(xc,yc,display.ixshot,ani.fnlst)
    cl = ani.clone()
    cl.xlate_path(25,0)
    display.shot.sprites.append(cl)
    AniCntrl(cl,"sprite")
    display.validate_view()

def add_pt():
    ani = display.sel_ani
    if ani is None:
        msgbox.showerror('Comiola','No animation selected')
    else:
        display.sel_pt = ani.cntrl.add_pt()
        display.validate_view()

def delete_pt():
    ani = display.sel_ani
    pt = display.sel_pt
    if ani is not None and pt is not None:
        if len(ani.path) == 1:
            msgbox.showerror(
                    'Comiola','Cannot delete: at least one point is required')
            return
        ani.cntrl.delete_pt(pt)
        display.sel_pt = ani.path[0]
        display.validate_view()
        return

def on_z():
    if display.sel_pt is None:
        return
    try:
        display.sel_pt.z = float(ptZ.get())
    except ValueError:
        msgbox.showerror('Comiola','"Z" value must be a number')
    display.validate_view()

def on_rot():
    if display.sel_pt is None:
        return
    try:
        display.sel_pt.rot = float(rot.get())
    except ValueError:
        msgbox.showerror('Comiola','"Rotate" value must be a number')
    display.validate_view()

def make_menu(container):
    terms = [
        But('+',zoomin,'menu',[4,4]),
        But('-',zoomout,'menu',[4,16]),
        But('CLONE',clone_sprite,'menu',[4,4]),
        Lab('tS:','menu',[8,1]),
        Entry( tS,4,[4,4]),
        Lab('tE:','menu',[8,1]),
        Entry( tE,4,[4,4]),
        Lab('Reps:','menu',[8,1]),
        Entry( cycles,4,[4,4]),
        Lab('FperCell:','menu',[8,1]),
        Entry( frames_per_cell,4,[4,4]),
        Lab('Pt:','menu',[8,1]),
        But('ADD',add_pt,'menu',[2,2]),
        But('DELETE',delete_pt,'menu',[2,4]),
        But('set Z:',on_z,'menu',[4,2]),
        Entry( ptZ,4,[2,4]),
        But('Rot:',on_rot,'menu',[4,2]),
        Entry( rot,4,[2,4]),
    ]
    build_row(container,terms)

