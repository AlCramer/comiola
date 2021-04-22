import tkinter as tk
from PIL import ImageTk,Image,ImageDraw

import scripts
from scripts import Pt,Ani
import imgpool as ip
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
        # position and scale for canvas
        self.xmar = 20
        self.ymar = 20
        self.scale_im_to_can = 1.0
        # index of shot we're currently showing
        self.ixshot = -1
        # selected animation, pt, or text element 
        self.sel_ani = None
        self.sel_pt = None
        self.sel_te = None
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
                int( (x-self.xmar)/s ),
                int( (y-self.ymar)/s )
                )

    # image coords-> canvas coord
    def from_im_coords(self,x,y):
        s = self.scale_im_to_can
        return (
                int(s*x)+self.xmar,
                int(s*y)+self.ymar
                )

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

    def on_h_selected(self,h,ev):
        # a handle was selected. De-selection is also handled here
        # (h of None means de-select).
        self.set_fdd_visible(False)
        if self.sel_ani is not None:
            if not self.do_commit():
                return
        # set up for move-canvas
        self.dragS = (ev.x, ev.y)
        self.marS = (self.xmar,self.ymar)
        self.last_h_selected = h
        if h is None:
            # de-select all
            self.sel_ani = None
            self.sel_pt = None
            self.sel_te = None
            self.validate_view()
            return
        # the handle's point is our drag point
        self.drag_pt = h.pt
        # Does clicking the handle set our selected ani & pt? 
        if h.sel_te is not None:
            self.sel_pt = None
            self.sel_ani = None
            self.sel_te = h.sel_te
            self.tabcntrl.show_tab('Text')
        else:
            self.sel_te = None
            if h.sel_pt is not None:
                self.sel_pt = h.sel_pt
                self.tabcntrl.show_tab('Shots')
            if h.sel_ani is not None:
                self.sel_ani = h.sel_ani
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
            self.xmar = self.marS[0] + xdelta
            self.ymar = self.marS[1] + ydelta
            self.draw_edit()

    def draw_spr(self,pt,img,img_dst):
        w = pt.w
        h = pt.h
        (x0,y0) = self.from_im_coords(pt.x - w/2, pt.y - h/2)
        w *= self.scale_im_to_can
        h *= self.scale_im_to_can
        img = img.resize((int(w),int(h)),Image.ANTIALIAS)
        if pt.rot != 0.0:
            _img = img.rotate(pt.rot)
            img.close()
            img = _img
        img_dst.paste(img,(int(x0),int(y0)),mask=img)
        img.close()


    # TODO: remove old version
    def __draw_edit(self):
        self.can.delete("all")
        if scripts.cnt_shots() == 0:
            return
        s = self.shot
        # create "img_dst": the (pil) image we will draw upon;
        # also prepare a pil draw object.
        img_bg = s.get_bg_pil()
        (w_bg,h_bg) = img_bg.size
        scale = self.scale_im_to_can
        w_dst = int(scale*w_bg) + max(0,2*self.xmar)
        h_dst = int(scale*h_bg) + max(0,2*self.ymar)
        img_dst = Image.new("RGB",(w_dst,h_dst),(0x45,0x45,0x45))
        # paste bg image
        w_bg *= self.scale_im_to_can
        h_bg *= self.scale_im_to_can
        img_bg = img_bg.resize((int(w_bg),int(h_bg)), Image.ANTIALIAS)
        (x0,y0) = self.from_im_coords(0,0)
        img_dst.paste(img_bg,(x0,y0))
        # draw camera, sprites, and text element controllers.
        draw_pil = ImageDraw.Draw(img_dst)
        # better UX: if no pt or te is selected, camera is draw
        # last; otherwise it's drawn first.
        drew_cam = False
        if self.sel_pt is not None or self.sel_te is not None:
            s.cam.cntrl.draw(draw_pil)
            drew_cam = True
        # draw the sprite images and controllers
        for spr in s.sprites:
            for pt in spr.path:
                self.draw_spr(pt,ip.get(spr.fnlst[0],'RGBA'),img_dst)
                spr.cntrl.draw(draw_pil)
        # draw the text element controllers (will draw text
        # as well)
        for te in s.textels:
            te.cntrl.draw(draw_pil, img_dst)
        # draw cam as needed
        if not drew_cam:
            s.cam.cntrl.draw(draw_pil)
        # blit image to canvas
        # tk requires that the image be bound to a static var,
        # hence self.img_tk
        self.img_tk = ImageTk.PhotoImage(img_dst)
        self.can.create_image(0,0,
            anchor=tk.NW,image=self.img_tk)
        img_dst.close()

    def draw_edit(self):
        self.can.delete("all")
        if scripts.cnt_shots() == 0:
            return
        s = self.shot
        # create "img_dst": the (pil) image we will draw upon;
        # also prepare a pil draw object.
        img_bg = s.get_bg_pil()
        (w_bg,h_bg) = img_bg.size
        scale = self.scale_im_to_can
        w_dst = int(scale*w_bg) + max(0,2*self.xmar)
        h_dst = int(scale*h_bg) + max(0,2*self.ymar)
        img_dst = Image.new("RGB",(w_dst,h_dst),(0x45,0x45,0x45))
        # paste bg image
        w_bg *= self.scale_im_to_can
        h_bg *= self.scale_im_to_can
        img_bg = img_bg.resize((int(w_bg),int(h_bg)), Image.ANTIALIAS)
        (x0,y0) = self.from_im_coords(0,0)
        img_dst.paste(img_bg,(x0,y0))
        # draw sprite images
        for spr in s.sprites:
            for pt in spr.path:
                self.draw_spr(pt,ip.get(spr.fnlst[0],'RGBA'),img_dst)
        # draw the text element controllers (will draw text
        # as well)
        draw_pil = ImageDraw.Draw(img_dst)
        for te in s.textels:
            te.cntrl.draw(draw_pil, img_dst)
        # draw the sprite controlls
        for spr in s.sprites:
            #for pt in spr.path:
            spr.cntrl.draw(draw_pil)
        # draw cam 
        s.cam.cntrl.draw(draw_pil)
        # if sprite or te is selected, redraw (its on top in Z order)
        if self.sel_te is not None:
            self.sel_te.cntrl.draw(draw_pil, img_dst)
        if self.sel_ani is not None:
            self.sel_ani.cntrl.draw(draw_pil)
        # blit image to canvas
        # tk requires that the image be bound to a static var,
        # hence self.img_tk
        self.img_tk = ImageTk.PhotoImage(img_dst)
        self.can.create_image(0,0,
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
            for spr in self.shot.sprites:
                AniCntrl(spr,"sprite")
            for te in self.shot.textels:
                TextElCntrl(te)
        ip.clear_refs()
        self.tabcntrl.show_tab('Shots')
        self.validate_view()
        ip.close_unneeded()

    def sprite_selected(self):
        return (self.sel_ani is not None and
            self.sel_ani != self.shot.cam)

