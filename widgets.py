import tkinter as tk
from PIL import Image, ImageTk
from uicolors import *

# This file defines classes that represent basic widgets: button, entry, label,
# etc. To add a row of widgets to a panel, create a list of But/Entry/Label 
# objects, then call "build_row". To add a table, create a set of such rows
# and call "build_table".

# "button pool": list of all buttons. Used to disable/enable 
# buttons. 
bpool = []
def enable_but(cmd):
    for b in bpool:
        if b.cmd == cmd:
            b.set_enabled(True)
    return None

class But:
    def __init__(self,txt,cmd,cntxt,xpad):
        self.txt = txt
        self.cmd = cmd
        self.cntxt = cntxt
        self.xpad = xpad
        self.always_enabled = False
        self.peer = None
        bpool.append(self)

    def get_peer(self,parent):
        if self.txt == 'Shots':
            debug1 = 1
        if self.peer is None:
            if self.cntxt == 'menu':
                self.peer = tk.Button(parent, text=self.txt,command=self.cmd,
                    bg='black',fg='white',relief=tk.GROOVE,
                    activebackground='black')
            elif self.cntxt == 'tab':
                self.peer = tk.Button(parent, text=self.txt,command=self.cmd,
                    bg=col_tabselected,fg='white',relief=tk.GROOVE,
                    activebackground='blue')
            else:
                self.peer = tk.Button(parent, text=self.txt,command=self.cmd,
                    bg=col_cntrl_bg, fg=col_cntrltext,
                    relief=tk.GROOVE)
        return self.peer

    def set_enabled(self,state):
        if state:
            self.peer['state'] = tk.NORMAL
        else:
            self.peer['state'] = tk.DISABLED

class ImgBut:
    def __init__(self,fn,cmd,xpad):
        self.fn = fn
        self.cmd = cmd
        self.xpad = xpad
        self.peer = None

    def get_peer(self,parent):
        if self.peer is None:
            im_pil = Image.open('./res/%s.png' % self.fn)
            im_pil.thumbnail((48,48),Image.ANTIALIAS)
            im_tk = ImageTk.PhotoImage(im_pil)
            self.peer = tk.Button(parent, image=im_tk,command=self.cmd,
                    relief=tk.GROOVE)
            self.peer.im_tk = im_tk
        return self.peer

class Lab:
    def __init__(self,txt,cntxt,xpad):
        self.txt = txt
        self.xpad = xpad
        self.cntxt = cntxt
        self.peer = None

    def get_peer(self,parent):
        if self.peer is None:
            if self.cntxt == 'menu':
                self.peer = tk.Label(parent,text=self.txt,
                        bg='black',fg='white')
            else:
                self.peer = tk.Label(parent,text=self.txt,
                        bg=col_cntrl_bg,fg=col_cntrllabel)
        return self.peer

class Header:
    def __init__(self,txt):
        self.txt = txt
        self.peer = None
        self.xpad = [2,2]

    def get_peer(self,parent):
        if self.peer is None:
            self.peer = tk.Label(parent,text=self.txt,
                bg=col_cntrl_bg,fg=col_cntrllabel)
        return self.peer

class Entry:
    def __init__(self,tvar,w,xpad):
        self.tvar = tvar
        self.w = w
        self.xpad = xpad
        self.peer = None

    def get_peer(self,parent):
        if self.peer is None:
            self.peer = tk.Entry(
                parent, textvariable=self.tvar,width=self.w,
                bg=col_cntrl_entrybg, fg=col_cntrl_entryfg)
        return self.peer

class Check:
    def __init__(self,tvar,text,xpad):
        self.tvar = tvar
        self.text = text
        self.xpad = xpad
        self.peer = None

    def get_peer(self,parent):
        if self.peer is None:
            self.peer = tk.Checkbutton(
                    parent, variable=self.tvar,text=self.text,
                    bg=col_cntrl_bg,fg=col_cntrllabel)
        return self.peer

class Textbox:
    def __init__(self,w,h,xpad):
        self.w = w
        self.h = h
        self.xpad = xpad
        self.peer = None

    def set(self,text):
        self.peer.delete('1.0', tk.END)
        self.peer.insert('1.0',text)

    def get(self):
        return self.peer.get('1.0','end')

    def get_peer(self,parent):
        if self.peer is None:
            self.peer = tk.Text(
                    parent, width=self.w, height=self.h,
                    relief=tk.GROOVE)
        return self.peer

class Dropdown:
    def __init__(self,tvar,choices,xpad):
        self.tvar = tvar
        self.choices = choices
        self.xpad = xpad
        self.peer = None

    def get_peer(self,parent):
        if self.peer is None:
            self.peer = tk.OptionMenu(
                    parent,self.tvar,*self.choices)
            self.peer['relief'] = tk.GROOVE
            self.peer['bg'] = col_dropdownbg
            self.peer['fg'] = col_dropdownfg
            self.tvar.set(self.choices[0])
        return self.peer

def build_row(tkrow,elements):
    for e in elements:
        e.get_peer(tkrow).pack(side='left',padx=e.xpad)

def build_table(parent,rows):
    for i in range(0,len(rows)):
        rgui = tk.Frame(master=parent,bg=col_cntrl_bg)
        row = rows[i]
        for j in range(0,len(row)):
            e = row[j]
            e.get_peer(rgui).pack(side='left',padx=e.xpad)
        rgui.grid(row=i,column=0,sticky=tk.W,padx=4,pady=2)

class Tab:
    def __init__(self,name,tkselect,tkpane):
        self.name = name
        self.tkselect = tkselect
        self.tkpane = tkpane

class TabCntrl:
    def __init__(self,parent,names,makecntrls,on_tab_select):
        self.parent = parent
        self.on_tab_select = on_tab_select
        # make selector buttons
        tabselector = tk.Frame(master=parent, 
            bg=col_tabbar,
            width=200, height=100) 
        tabselector.grid(row=0,column=0,sticky=tk.W+tk.E)
        selectors = []
        for n in names:
            b = But(n,lambda n=n: self.on_tab(n),'tab',[2,4])
            b.always_enabled = True
            selectors.append(b)
        build_row(tabselector,selectors)
        # make panes
        self.tabs = []
        for i in range(0,len(makecntrls)):
            but = selectors[i]
            pane = tk.Frame(master=parent, width=200, height=100,
                bg=col_cntrl_bg)
            pane.grid(row=1,column=0,sticky=tk.W+tk.E)
            self.tabs.append( Tab(but.txt, but.get_peer(pane), pane) )
            makecntrls[i](pane)
        # set to first tab
        self.show_tab(self.tabs[0].name)

    def on_tab(self,name):
        # used selected a tab
        if not self.on_tab_select(name):
            return 
        self.show_tab(name)

    def show_tab(self,name):
        for t in self.tabs:
            if (t.name == name):
                t.tkpane.grid()
                t.tkselect['bg'] = col_tabselected
            else:
                t.tkpane.grid_remove()
                t.tkselect['bg'] = col_tabunselected

