import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox as msgbox

import scripts
import controls
from display import Display
import widgets
from widgets import TabCntrl
from uicolors import *

# tkinter requires this call to come befor the imports of the gui
# components
win = tk.Tk()
win.title('Comiola')

# ui components
import uibanner
import uimenu
import uishots
import uitext
import uisequences

# the display
display = None
# the tabcntrl
tabcntrl = None
# file dropdown control; and visibility status
file_dropdown = None
# menu bar
menu = None

def on_close_window():
    if scripts.script_changed():
        action  = msgbox.askyesnocancel('Exit Comiola','Save project?')
        if action is None:
            return
        if action:
            if do_commit():
                scripts.save_script(scripts.proj_name)
            else:
                return
    win.destroy()

win.protocol('WM_DELETE_WINDOW',on_close_window)

def validate_view():
    # disable all buttons: components will re-enable as appropriate
    for b in widgets.bpool:
        if not b.always_enabled:
            b.set_enabled(False)
    uibanner.validate_view()
    uimenu.validate_view()
    uishots.validate_view()
    uitext.validate_view()
    uisequences.validate_view()
    display.draw_edit()

def do_commit():
    if scripts.script_open():
        if not uibanner.do_commit():
            return False
        if not uimenu.do_commit():
            return False
        if not uishots.do_commit():
            return False
        if not uitext.do_commit():
            return False
        if not uisequences.do_commit():
            return False
    return True

def on_tab_select(name):
    # called when used selects a tab: return False to cancel
    # the event
    if not do_commit():
        return False
    # unset selections as needed
    if name == 'Shots':
        display.sel_te = None
    elif name == 'Text':
        display.sel_ani = None
        display.sel_pt = None
    validate_view()
    return True

def set_fdd_visible(visible):
    global menu, fdd_visible
    menu.update()
    if visible:
        file_dropdown.place(x=0,y=menu.winfo_y())
        file_dropdown.lift()
        uibanner.fdd_visible = True
    else:
        file_dropdown.place_forget()
        uibanner.fdd_visible = False

def make_gui(win):
    global display,tabcntrl,goto_label
    global file_dropdown, menu

    # bannner
    banner = tk.Frame(win,bg=col_cntrl_bg,
            highlightthickness=0)
    banner.grid(row=0,column=0,columnspan=2,sticky=(tk.NE+tk.SW),pady=2)
    uibanner.make_banner(banner)
    uibanner.set_fdd_visible = set_fdd_visible

    # file dropdown
    file_dropdown = tk.Frame(master=win, width=200, height=100,
            bg=col_cntrl_bg)
    file_dropdown.place(anchor=tk.NW)
    uibanner.make_file_dropdown(file_dropdown)
    
    # menu
    menu = tk.Frame(master=win,bg="black",
            highlightthickness=0)
    menu.grid(row=1,column=0,sticky=tk.W+tk.E)
    uimenu.make_menu(menu)

    # control panel. This is tab control with 2 panes:
    # "shotcntrls" and "textcntrls"
    tabcontainer = tk.Frame(master=win, width=200, height=100,
            bg=col_cntrl_bg)
    tabcontainer.grid(row=1,column=1,rowspan=2,sticky=(tk.NE+tk.SW))
    tabcntrl = TabCntrl(tabcontainer,
            ["Shots","Text","Sequences"],
            [uishots.make_shotcntrls, 
                uitext.make_textcntrls,
                uisequences.make_seqcntrls],
            on_tab_select)

    # display
    can = tk.Canvas(master=win, width=500, height=400, 
            highlightthickness=0, bg=col_display_bg)
    can.grid(row=2,column=0,sticky=(tk.NW+tk.SE))
    display = Display(can,do_commit,validate_view,tabcntrl,set_fdd_visible)
    scripts.display = controls.display = display

    # display is globally visible to all components
    uibanner.display = display
    uimenu.display = display
    uishots.display = display
    uitext.display = display
    uisequences.display = display

    # file-dropdown in banner should be closed
    set_fdd_visible(False)

    # expansion behavior
    tabcontainer.columnconfigure(0, weight=1)
    win.columnconfigure(0, weight=1)
    win.rowconfigure(2, weight=1)


def main():
    make_gui(win)
    validate_view()
    win.mainloop()

# start dev code. This assumes you built a project and want to go
# straight to it (avoids the hassle of File/Open).
def dev():
    make_gui(win)
    scripts.open_project('C:/Users/Al/mycomics/cp','MyProject',False)
    uibanner.proj_dir.set(scripts.proj_filepath)
    display.edit_shot(0)
    win.mainloop()
# end dev code

if __name__ == '__main__':
    #main()
    dev()

