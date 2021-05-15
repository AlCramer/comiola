import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox as msgbox
import os
import webbrowser

import scripts
import controls
from controls import AniCntrl 
from widgets import *
from uicolors import *

# the display
display = None

# Set in "make_gui": control file_dropdown
set_fdd_visible = None

# GUI string vars's
proj_dir = tk.StringVar()
ixgoto = tk.StringVar()
# file dropdown
new_project_name = tk.StringVar()
saveas_name = tk.StringVar()


# tkinter id for goto_label
goto_label = None

def validate_view():
    on_buts = [on_file,new_project,open_project,on_file_cancel,on_faq]
    if scripts.script_open():
        on_buts.append(save_project)
        on_buts.append(saveas_project)
        on_buts.append(close_project)
    if scripts.cnt_shots() == 0:
        ixgoto.set('')
        goto_label.peer['text'] ='of 0'
    else:
        on_buts.append(goto)
        ixgoto.set('%d' % (1+display.ixshot))
        goto_label.peer['text'] = 'of %d' % scripts.cnt_shots()
    if display.ixshot > 0:
        on_buts.append(goto_prv)
    if display.ixshot < scripts.cnt_shots() -1:
        on_buts.append(goto_nxt)
    for b in on_buts:
        enable_but(b)

def do_commit():
    return True

def goto():
    try:
        ixmax = scripts.cnt_shots()-1
        ix = int(ixgoto.get().strip()) -1
        if ix < 0:
            ix = 0
        elif ix > ixmax:
            ix = ixmax
        display.edit_shot(ix)
    except ValueError:
        msgbox.showerror('Comiola','"goto" value must be a number')


def goto_prv():
    ix = display.ixshot-1
    if ix >= 0:
        display.edit_shot(ix)

def goto_nxt():
    ix = display.ixshot +1
    if ix <= scripts.cnt_shots()-1:
        display.edit_shot(ix)

def new_project():
    name = new_project_name.get()
    if name == '':
        msgbox.showerror('Comiola','You must enter a name for the project')
        return
    d = tkinter.filedialog.askdirectory()
    if d is not None and d != '':
        if scripts.open_project(d,name,True):
            proj_dir.set(scripts.proj_filepath)
        set_fdd_visible(False)
        display.validate_view()

def open_project():
    fp = tkinter.filedialog.askopenfilename()
    if fp == '':
        return
    (head,tail) = os.path.split(fp)
    if scripts.open_project(head,tail,False):
        proj_dir.set(scripts.proj_filepath)
        set_fdd_visible(False)
        display.edit_shot(0)
        display.validate_view()

def save_project():
    scripts.save_script(scripts.proj_name)
    set_fdd_visible(False)

def saveas_project():
    name = saveas_name.get().strip()
    if name == '':
        msgbox.showerror('Comiola',
            'You must enter a name for "saveas"')
        return
    scripts.save_script(name)
    proj_dir.set(scripts.proj_filepath)
    set_fdd_visible(False)

def close_project():
    if not scripts.script_changed():
        set_fdd_visible(False)
        scripts.close_project()
        display.validate_view()
        return

    action  = msgbox.askyesnocancel('Comiola','Save project?')
    set_fdd_visible(False)
    if action is None:
        # user choose "Cancel"
        return
    if action:
        # user choose "Yes" (save project)
        if not do_commit():
            # could not commit (bad values). Error was reported
            return
        scripts.save_script(scripts.proj_name)
    scripts.close_project()
    display.validate_view()

# file button toggles visibility of file-dropdown, so we
# must track state.
fdd_visible = False

def on_file():
    set_fdd_visible(not fdd_visible)

def on_file_cancel():
    set_fdd_visible(False)

def on_faq():
    webbrowser.open_new_tab(
        os.path.join( os.path.dirname(__file__),
        'faq', 'faq.htm')
    )
    
# helpers for "make_gui"
def make_banner(container):
    global display,goto_label

    proj_dir_ui = Entry(proj_dir,40,[4,4])
    goto_label = Lab('of 0','banner',[4,4])
    terms = [
        But("File",on_file,'banner',[4,4]),
        proj_dir_ui,
        But('GOTO',goto,'banner',[4,2]),
        Entry(ixgoto,4,[2,4]),
        goto_label,
        But('<',goto_prv,'banner',[4,4]),
        But('>',goto_nxt,'banner',[4,4]),
        But('Help',on_faq,'banner',[16,4])
    ]
    build_row(container,terms)

def make_file_dropdown(container):
    rows = [
        [
            But('New',new_project,'cntrls',[4,4]),
            Lab('Name:','cntrls',[4,1]),
            Entry(new_project_name,14,[1,4])
        ],
        [
            But('Open',open_project,'cntrls',[4,4])
        ],
        [
            But('Save',save_project,'cntrls',[4,4])
        ],
        [
            But('Save as',saveas_project,'cntrls',[4,4]),
            Lab('Name:','cntrls',[4,1]),
            Entry(saveas_name,14,[1,4])
        ],
        [
            But('Close',close_project,'cntrls',[4,4])
        ],
        [
            But('Cancel',on_file_cancel,'cntrls',[4,4])
        ]
    ]
    build_table(container,rows)

