import tkinter as tk
from PIL import ImageTk,Image,ImageDraw

import scripts
from scripts import Pt,Ani
import resources as res
from controls import *

class Display:
    def __init__(self,can,do_commit,validate_view,tabcntrl,set_fdd_visible):
        self.can = can
        self.do_commit = do_commit
        self.tabcntrl = tabcntrl
        self.validate_view = validate_view
        self.set_fdd_visible = set_fdd_visible
        can.bind("<Button-1>", self.on_mousedown)
        can.bind("<Double-Button-1>", self.on_doubleclick)
        can.bind("<ButtonRelease-1>", self.on_mouseup)
        can.bind("<Motion>", self.on_mousemove)
        self.img_tk = None
        # width & height of image (non-scaled)
        self.w_img = 0
        self.h_img = 0
        # padding. We sprites on an image that's 
        # basically the bg, surrounded by this padding.
        self.pad = 100
        # position and scale for canvas
        self.xoff = -80
        self.yoff = -80
        self.scale_im_to_can = 1.0
        # index of shot we're currently showing
        self.ixshot = -1
        # the handles
        self.handles = []
        # selected animation, pt, or text element 
        self.sel_ani = None
        self.sel_pt = None
        # Some operations require mutiple point selections.
        # These record the first selection, and what action we're doing
        self.first_sel_pt = None
        self.action = ''
        # drag pt
        self.drag_pt = None
        # used in move-canvas operation
        self.dragS = None
        self.marS = None
        # last handle selected
        self.last_h_selected = None

    # canvas coords -> image coords
    def to_im_coords(self,x,y):
        s = self.scale_im_to_can
        return (
                int( (x-self.xoff)/s ) - self.pad,
                int( (y-self.yoff)/s ) - self.pad
                )

    # image coords-> canvas coord
    def from_im_coords(self,x,y):
        s = self.scale_im_to_can
        return (
                int(s*(x+self.pad))+self.xoff,
                int(s*(y+self.pad))+self.yoff,
                )

    def set_pt_selected(self,pt):
        if pt is None:
            self.sel_pt = None
            self.sel_ani = None
            self.last_h_selected = None
        else:
            self.sel_pt = pt
            self.sel_ani = pt.ani
            self.last_h_selected = pt.handle

    def on_doubleclick(self,ev):
        (x,y) = self.to_im_coords(ev.x,ev.y)
        hits = []
        for h in self.handles:
            if h.is_hit(x,y):
                hits.append(h)
        if len(hits) == 0:
            self.on_h_selected(None,ev)
        if len(hits) > 1 and self.last_h_selected is not None:
            for i in range(0,len(hits)-1):
                if hits[i] == self.last_h_selected:
                    self.on_h_selected(hits[i+1],ev)
                    return
        self.on_h_selected(hits[0],ev)

    def on_mousedown(self,ev):
        (x,y) = self.to_im_coords(ev.x,ev.y)
        h = self.last_h_selected
        if h is not None and h.is_hit(x,y):
            self.on_h_selected(h,ev)
            return
        for h in self.handles:
            if h.is_hit(x,y):
                self.on_h_selected(h,ev)
                return
        self.on_h_selected(None,ev)

    def deselect_all(self):
        self.sel_ani = None
        self.sel_pt = None
        self.first_sel_pt = None
        self.action = ''
        self.validate_view()

    def on_h_selected(self,h,ev):
        # a handle was selected. De-selection is also handled here
        # (h of None means de-select).
        self.set_fdd_visible(False)
        if self.sel_ani is not None:
            if not self.do_commit():
                return
        # set up for move-canvas
        self.dragS = (ev.x, ev.y)
        self.marS = (self.xoff,self.yoff)
        self.last_h_selected = h
        if h is None:
            self.deselect_all()
            return
        # the handle's point is our drag point
        self.drag_pt = h.pt
        # Does clicking the handle set our selected ani & pt? 
        if h.selectable:
            self.sel_pt = h.pt
            self.sel_ani = h.pt.ani
        # pass the event onto the selected controller for handling
        (x,y) = self.to_im_coords(ev.x,ev.y)
        h.pt.cntrl.on_mousedown(h.pt,x,y)
        self.validate_view()

    def on_mouseup(self,ev):
        #print('display. on_mouseup')
        if self.drag_pt is not None:
            (x,y) = self.to_im_coords(ev.x,ev.y)
            self.drag_pt.cntrl.on_mouseup(self.drag_pt,x,y)
        # mouse-up ends drag
        self.dragS = None
        self.marS = None
        self.drag_pt = None

    def on_mousemove(self,ev):
        #print('display. on_mousemove')
        if self.drag_pt is not None:
            # dragging a pt
            (x,y) = self.to_im_coords(ev.x,ev.y)
            self.drag_pt.cntrl.on_mousemove(self.drag_pt,x,y)
            self.draw_edit()
            return
        if self.dragS is not None:
            # moving cavas
            xdelta = ev.x - self.dragS[0]
            ydelta = ev.y - self.dragS[1]
            self.xoff = self.marS[0] + xdelta
            self.yoff = self.marS[1] + ydelta
            self.draw_edit()

    def draw_spr(self,pt,img,img_dst):
        w = pt.w
        h = pt.h
        pad = self.pad
        (x0,y0) = (
            int(pt.x + pad - w/2), 
            int(pt.y + pad - h/2)
            )
        img = img.resize((int(w),int(h)),Image.ANTIALIAS)
        if pt.rot != 0.0:
            _img = img.rotate(pt.rot)
            img.close()
            img = _img
        img_dst.paste(img,(x0,y0),mask=img)
        img.close()

    def draw_te_bg(self,te,pt,draw_pil,img_pil):
        # get (x0,y0,x1,y1) for bg. 
        (x0,y0,x1,y1) = te.get_bb_bg(pt.x,pt.y)
        (x0,y0) = self.to_draw_coords(x0,y0)
        (x1,y1) = self.to_draw_coords(x1,y1)
        bgspec = te.bgspec
        if bgspec != 'null':
            if bgspec.startswith('#'):
                draw_pil.rectangle((x0,y0,x1,y1), fill=bgspec)
            else:
                img = res.get_res(bgspec)
                w = int(x1-x0+1)
                h = int(y1-y0+1)
                img = img.resize((w,h),Image.ANTIALIAS)
                img_pil.paste(img,(x0,y0),mask=img)
                img.close()

    def draw_te_text(self,te,pt,draw_pil):
        (x0,y0,x1,y1) = te.get_bb_text(pt.x,pt.y)
        draw_pil.text( 
            self.to_draw_coords(x0,y0),
            te.get_text(),
            fill=te.fontcolor,
            font=res.get_font(te.fontname,te.fontsize))

    def draw_edit(self):
        self.can.delete("all")
        if scripts.cnt_shots() == 0:
            return
        s = self.shot
        # create "img_dst": the (pil) image we will draw upon. It's
        # the bg, surrounded by padding.
        pad = self.pad
        img_bg = s.get_bg_pil()
        (w_bg,h_bg) = img_bg.size
        pad = self.pad
        (w_dst, h_dst) = ( w_bg + 2*pad, h_bg + 2*pad)
        img_dst = Image.new("RGB",(w_dst,h_dst), (0x45,0x45,0x45))
        # paste bg image
        img_dst.paste(img_bg,(pad,pad))
        # get shot animations, split into 2 groups: "spr" and "txt"
        (spr_anis,txt_anis) = s.partition_anis()
        # draw sprite images
        for ani in spr_anis:
            for pt in ani.path:
                self.draw_spr(pt,res.get_img(ani.fnlst[0],'RGBA'),img_dst)
        # draw text-element bg images.
        draw_pil = ImageDraw.Draw(img_dst)
        for ani in txt_anis:
            for pt in ani.path:
                self.draw_te_bg(ani.te,pt,draw_pil,img_dst)
        # draw the sprite controlls
        for ani in spr_anis:
            ani.cntrl.draw(draw_pil)
        # draw cam 
        s.cam.cntrl.draw(draw_pil)
        # draw text-element controls and txt
        for ani in txt_anis:
            ani.cntrl.draw(draw_pil)
            for pt in ani.path:
                self.draw_te_text(ani.te,pt,draw_pil)
        # if ani is selected, redraw (it should be on top in Z order)
        if self.sel_ani is not None:
            self.sel_ani.cntrl.draw(draw_pil)
        # resize img_dst
        sc = self.scale_im_to_can
        img_dst = img_dst.resize( (int(w_dst * sc), 
            int(h_dst*sc)),Image.ANTIALIAS)
        # blit image to canvas
        # tk requires that the image be bound to a static var,
        # hence self.img_tk
        self.img_tk = ImageTk.PhotoImage(img_dst)
        self.can.create_image(self.xoff, self.yoff,
            anchor=tk.NW,image=self.img_tk)
        img_dst.close()

    def edit_shot(self,ix):
        self.handles = []
        if ix >= scripts.cnt_shots():
            ix = scripts.cnt_shots() - 1
        self.ixshot = ix
        self.shot = scripts.get_shot(ix)
        if self.shot is not None:
            img = self.shot.get_bg_pil()
            (self.w_img,self.h_img) = img.size
            # build the controllers for cam & sprites
            AniCntrl(self.shot.cam,"cam")
            for ani in self.shot.anis:
                AniCntrl(ani,"sprite")
        res.clear_refs()
        self.tabcntrl.show_tab('Shots')
        self.validate_view()
        res.close_unneeded()

    def sprite_selected(self):
        return (self.sel_ani is not None and
            self.sel_ani != self.shot.cam)

    def to_draw_coords(self,x,y):
        return (int(x+self.pad), int(y+self.pad))

