import tkinter as tk
import tkinter.messagebox as msgbox

import scripts
from widgets import *
from uicolors import *

# the display
display = None

# GUI string vars's
ixS = tk.StringVar()
ixE = tk.StringVar()
add_after = tk.StringVar()

# clipboard
clipboard = None

def validate_view():
    ixS.set('')
    ixE.set('')
    add_after.set('')
    if display.ixshot != -1:
        ixS.set('%d' % (display.ixshot+1))
        ixE.set('%d' % (display.ixshot+1))
        add_after.set('%d' % (display.ixshot+1))
        enable_but(on_cut)
        enable_but(on_copy)
        if clipboard is not None:
            enable_but(on_paste)

def do_commit():
    return True

def get_range():
    try:
        S = int(ixS.get())
    except ValueError:
        msgbox.showerror('Comiola','"Range" values must be numbers')
        return None
    try:
        E = int(ixE.get())
    except ValueError:
        msgbox.showerror('Comiola','"Range" values must be numbers')
        return None
    S -= 1
    E -= 1
    nshots = scripts.cnt_shots()
    if S < 0:
        S = 0
    if S > nshots - 1:
        S = nshots - 1
    if E < 0:
        E = 0
    if E > nshots - 1:
        E = nshots - 1
    return [S,E]

def on_cut():
    global clipboard
    SE = get_range()
    if SE is None:
        return
    (S,E) = SE
    clipboard = scripts.delete_shots(S,E)
    ix = S -1
    if ix < 0:
        ix = 0
    display.edit_shot(ix)

def on_copy():
    global clipboard
    SE = get_range()
    if SE is None:
        return
    (S,E) = SE
    clipboard = scripts.copy_shots(S,E)

def on_paste():
    # Convention: no "add_after" value means insert at end
    nshots = scripts.cnt_shots()
    ixafter =  nshots - 1
    vstr = add_after.get().strip()
    if vstr != '':
        try:
            ixafter = int(vstr)
        except:
            msgbox.showerror('Comiola','"after" must be a shot index (or -1)')
            return 
    if ixafter < -1:
        ixafter = -1
    if ixafter > nshots -1:
        ixafter = nshots -1

    seq = []
    for s in clipboard:
        seq.append(s.clone())
    scripts.extend_script(seq,ixafter)
    display.edit_shot(ixafter+1)

def make_seqcntrls(container):

    rows = [
        [
            Lab('Range:','cntrls',[4,1]),
            Entry(ixS,4,[1,4]),
            Lab('..','cntrls',[4,1]),
            Entry(ixE,4,[1,4]),
        ],
        [
            But('Cut',on_cut,'cntrls',[4,2]),
            But('Copy',on_copy,'cntrls',[4,2]),
            But('Paste',on_paste,'cntrls',[4,2]),
            Lab('after','cntrls',[4,1]),
            Entry(add_after,4,[1,4]),
        ]
    ]

    build_table(container,rows)

