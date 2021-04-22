import tkinter as tk
import tkinter.messagebox as msgbox

import scripts
import controls
from controls import TextElCntrl 
from widgets import *
from uicolors import *

# the display
display = None

# the text box
textbox = None

# GUI string vars's
# text cntrl
fontname = tk.StringVar()
fontsize = tk.StringVar()
fontcolor = tk.StringVar()
colorbg = tk.StringVar()

def validate_view():
    enable_but(text_apply)
    if display.sel_te is None:
        fontcolor.set('#000000')
        fontname.set('comics')
        fontsize.set('24pt')
        colorbg.set('')
        textbox.set('')
    else:
        te = display.sel_te
        fontcolor.set(te.fontcolor)
        fontname.set(te.fontname)
        fontsize.set(te.fontsize)
        textbox.set(te.text)
        enable_but(delete_te)

def do_commit():
    return True

def text_apply():
    if display.ixshot == -1:
        return
    text = textbox.get().strip()
    if display.sel_te is None:
        # create new te and select
        te = scripts.add_te(
            float(display.w_img/2),
            float(display.h_img/2),
            display.ixshot,
            text,
            fontname.get(),
            fontsize.get(),
            fontcolor.get())
        TextElCntrl(te)
        display.sel_ani = None
        display.sel_pt = None
        display.sel_te = te
    else:
        # apply to selected
        color = fontcolor.get()
        if color == '':
            # defaults to black
            color = '#000000'
        else:
            if not isHexColor(color):
                msgbox.showerror('Comiola',
'"Color" value must be an HTML-style hex color ("#ff000", etc.)')
                return
        te = display.sel_te
        te.fontname = fontname.get()
        te.fontsize = fontsize.get()
        te.fontcolor = color
        te.set_text(text, te.lo_text.x, te.lo_text.y)
    display.validate_view()

def on_bal_select(fn):
    if display.sel_te is not None:
        display.sel_te.bgspec = fn
        display.validate_view()

def on_colorbg():
    if display.sel_te is not None:
        c = colorbg.get()
        # empty means: no bg; we record this as "null"
        if c == '':
            c = 'null'
        elif not isHexColor(c):
            msgbox.showerror('Comiola',
'"Color" value must be an HTML-style hex color ("#ff000", etc.)')
            return
        display.sel_te.bgspec = c
        display.validate_view()


def delete_te():
    if display.sel_te is not None:
        scripts.delete_te(display.ixshot,display.sel_te)
        display.validate_view()

def make_textcntrls(container):
    global textbox
    textbox = Textbox(30,10,[4,4])
    fontnames = ('comics','serif','sans-serif')
    fontsizes = ('12pt','16pt','24pt','32pt')
    rows = [
        [
            textbox
        ],
        [
            Lab('Font:','cntrls',[4,1]),
            Dropdown(fontname,fontnames,[1,4]),
            Dropdown(fontsize,fontsizes,[1,4]),
        ],
        [
            Lab('Color:','cntrls',[4,1]),
            Entry(fontcolor,6,[1,4]),
            But('Apply',text_apply,'cntrls',[4,4])
        ],
        [
            Header('Background:')
        ],
        [
            ImgBut('lspeach1.s',lambda: on_bal_select('lspeach1'),[2,2]),
            ImgBut('lspeach2.s',lambda: on_bal_select('lspeach2'),[2,2]),
            ImgBut('lthought1.s',lambda: on_bal_select('lthought1'),[2,2]),
            ImgBut('lthought2.s',lambda: on_bal_select('lthought2'),[2,2]) 
        ],
        [
            ImgBut('rspeach1.s',lambda: on_bal_select('rspeach1'),[2,2]),
            ImgBut('rspeach2.s',lambda: on_bal_select('rspeach2'),[2,2]),
            ImgBut('rthought1.s',lambda: on_bal_select('rthought1'),[2,2]),
            ImgBut('rthought2.s',lambda: on_bal_select('rthought2'),[2,2]) 
        ],
        [
            ImgBut('colorbg',on_colorbg,[2,2]),
            Lab('Color:','cntrls',[4,1]),
            Entry(colorbg,6,[1,4]),
        ],
        [
            But('Delete Selected',delete_te,'cntrls',[4,4])
        ]
    ]
    build_table(container,rows)

