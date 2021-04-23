from PIL import ImageDraw
from scripts import Pt,measure_text,get_font
import imgpool as ip

# the display is global: this set in comiola.py
display = None

# dimension for contrl handle (actually 1/2 the width)
hand_dim = 6

# A handle binds a Pt to a small, clickable shape shown in
# the display. Users click & drag handles to change the 
# (x,y) attributes of a Pt.
class Handle:
    def __init__(self,pt,sel_pt,sel_ani,sel_te):
        self.pt = pt
        pt.handle = self
        self.sel_pt = sel_pt
        self.sel_ani = sel_ani
        self.sel_te = sel_te
        display.handles.append(self)

    def is_hit(self,x,y):
        hd = hand_dim/display.scale_im_to_can
        p = self.pt
        return (
            (x >= p.x - hd) and
            (x <= p.x + hd) and
            (y >= p.y - hd) and
            (y <= p.y + hd))

    def draw(self,draw_pil,color,shape):
        # draw to PIL image
        dim = hand_dim
        # need to scale "dim" to get correct size when img is blitted
        # to canvas.
        dim = int(dim/display.scale_im_to_can)
        p = self.pt 
        (x0,y0) = display.from_im_coords(int(p.x - dim), int(p.y - dim))
        (x1,y1) = display.from_im_coords(int(p.x + dim), int(p.y + dim))
        if shape == 'rect':
            draw_pil.rectangle((x0,y0,x1,y1),fill=color)
        elif shape == 'tri':
            (x0,y0) = display.from_im_coords(p.x - dim, p.y + dim)
            (x1,y1) = display.from_im_coords(p.x, p.y - dim)
            (x2,y2) = display.from_im_coords(p.x + dim, p.y + dim)
            draw_pil.polygon((x0,y0,x1,y1,x2,y2),fill=color)
        else:
            draw_pil.ellipse((x0,y0,x1,y1),fill=color)

# An (x,y) value: representation is float
class XY:
    def __init__(self,x,y):
        self.x = float(x)
        self.y = float(y)

    def clone(self):
        return XY(self.x,self.y)

# Control for a point: it displays and modifies the (x,y,w,h)
# attributes of a point.
class PtCntrl:
    def __init__(self,pt,ani):
        self.pt = pt
        self.ani = ani
        pt.cntrl = self
        self.resizeW = XY(0.0,0.0)
        self.resizeW.cntrl = self
        Handle(pt,pt,ani,None)
        Handle(self.resizeW,None,None,None)
        # aspect ratio: when we change pt.w, we change pt.h
        self.ar = pt.h/pt.w
        # (x,y) at start of mousemove
        self.dragS = None
        # clone of "pt" at start of mousemove
        self.dragptS = None

    def set_resize_handle(self):
        p = self.pt
        self.resizeW.x = p.x + int( p.w/2 - hand_dim/2 )
        self.resizeW.y = p.y
 
    def draw(self,draw_pil,color):
        self.set_resize_handle()
        shape = 'oval' if self.pt == display.sel_pt else 'rect'
        # draw handles for pt and resize
        self.pt.handle.draw(draw_pil,color,shape)
        self.resizeW.handle.draw(draw_pil,color,'tri')
        # draw a rectangle showing size
        p = self.pt
        w = int(p.w/2) - 2
        h = int(p.h/2) - 2
        (x0,y0) = display.from_im_coords(p.x - w, p.y - h)
        (x1,y1) = display.from_im_coords(p.x + w, p.y + h)
        draw_pil.rectangle((x0,y0,x1,y1), outline=color)
 
    def on_mousedown(self,pt,x,y):
        self.dragS = [x,y]
        self.dragptS = self.pt.clone()

    def on_mouseup(self,pt,x,y):
        self.dragS = None

    def on_mousemove(self,pt,x,y):
        if self.dragS is None:
            return
        xdelta = x - self.dragS[0]
        ydelta = y - self.dragS[1]
        ptS = self.dragptS
        if pt == self.resizeW:
            # resizing width 
            self.pt.w = ptS.w +2*xdelta
            self.pt.h = self.ar * self.pt.w
        elif pt == self.pt:
            # moving (x,y) of point
            self.pt.x = ptS.x +xdelta
            self.pt.y = ptS.y +ydelta
        if self.ani.is_cam:
            self.ani.cntrl.validate_cam_path()

# control for an Ani: allows user to modify the path Pts.
class AniCntrl:
    def __init__(self,ani,name):
        self.ani = ani
        ani.cntrl = self
        # "name" used for debugging
        self.name = name
        for p in ani.path:
            PtCntrl(p,ani)
        self.dragS = None
        self.dragptS = None

    def add_pt(self):
        ani = self.ani
        p = ani.path[-1]
        p = Pt(p.x + 50,p.y,0.0,p.z,0.0,p.w,p.h)
        ani.add_pt(p)
        PtCntrl(p,ani)
        return p

    def delete_all_pts(self):
        for p in self.ani.path:
            display.handles.remove(p.handle)
        self.ani.path = []

    def delete_pt(self,p):
        self.ani.delete_pt(p)
        display.handles.remove(p.handle)

    def draw(self,draw_pil):
        def get_color(color,ix,N):
            rgb = [0,0,0]
            delta = 0 if N == 1 else 126.0/(N-1)
            if color == 'red':
                rgb[0] = 126 + int(delta*ix)
            elif color == 'green':
                rgb[1] = 126 + int(delta*ix)
            elif color == 'blue':
                rgb[2] = 126 + int(delta*ix)
            return "#%02x%02x%02x" % (rgb[0],rgb[1],rgb[2])
 
        ani = self.ani
        basecolor = 'green' if ani.is_cam else 'red'
        for i in range(0,len(ani.path)):
            p = ani.path[i]
            p.cntrl.draw(draw_pil,
                    get_color(basecolor,i,len(ani.path)))

    def validate_cam_path(self):
        # ensure a camera path is fully contained within image
        an = self.ani
        w_img = display.w_img
        h_img = display.h_img
        wmax = min(w_img,h_img)
        for pt in an.path:
            pt.w = min(wmax,pt.w)
            pt.h = pt.w
            w = pt.w
            # top bound...
            _min = int(w/2)
            if pt.y < _min:
                pt.y = _min
            # left bound
            if pt.x < _min:
                pt.x = _min
            # bottom bound
            _max = h_img - int(w/2)
            if pt.y > _max:
                pt.y = _max
            # right bound
            _max = w_img - int(w/2)
            if pt.x > _max:
                pt.x = _max

# Control for a TextElement
class TextElCntrl:
    def __init__(self,te):
        self.te = te
        te.cntrl = self
        te.lo_text.cntrl = self
        # resize control bg w and h
        self.bgsize = XY(0,0)
        self.bgsize.cntrl = self
        # y offset control for bg
        self.yoff = XY(0,0)
        self.yoff.cntrl = self
        Handle(self.te.lo_text,None,None,te)
        Handle(self.bgsize,None,None,None)
        Handle(self.yoff,None,None,None)
        # (x,y) at start of mousemove
        self.dragS = None
        # clones of layouts at start of mousemove
        self.drag_lo_bgS = None
        self.drag_lo_textS = None

    def set_resize_handle(self):
        lo = self.te.lo_bg
        #  bgsize is at lower right corner
        self.bgsize.x = int( lo.x + lo.w/2 ) 
        self.bgsize.y = int( lo.y + lo.h/2) 
        # yoff is top cenlor
        self.yoff.x = int(lo.x)
        self.yoff.y = int( lo.y - lo.h/2 ) 
 
    def draw(self,draw_pil, img_pil):
        self.set_resize_handle()
        # draw the te bg.
        te = self.te
        display.draw_te_bg(te,te.lo_bg,draw_pil,img_pil)
        # draw handles for te.lo_text, resize, and yoff
        shape = 'oval' if self.te == display.sel_te else 'rect'
        color = '#00ffff'
        te.lo_text.handle.draw(draw_pil,color,shape)
        self.bgsize.handle.draw(draw_pil,color,'tri')
        self.yoff.handle.draw(draw_pil,color,'tri')
        # draw a rectangle showing size
        lo = te.lo_bg
        w = lo.w/2 - 2
        h = lo.h/2 - 2
        (x0,y0) = display.from_im_coords(lo.x-w, lo.y-h)
        (x1,y1) = display.from_im_coords(lo.x+w, lo.y+h)
        draw_pil.rectangle((x0,y0,x1,y1), outline=color)
        # draw the text
        display.draw_te_text(te,te.lo_text,draw_pil)

    def on_mousedown(self,pt,x,y):
        self.dragS = [x,y]
        self.drag_lo_bgS = self.te.lo_bg.clone()
        self.drag_lo_textS = self.te.lo_text.clone()

    def on_mouseup(self,pt,x,y):
        self.dragS = None

    def on_mousemove(self,pt,x,y):
        if self.dragS is None:
            return
        xdelta = x - self.dragS[0]
        ydelta = y - self.dragS[1]
        loS = self.drag_lo_bgS
        if pt == self.bgsize:
            # resizing bg 
            self.te.lo_bg.set_wh(
                loS.w +2*xdelta,
                loS.h +2*ydelta)
        elif pt == self.yoff:
            # resizing offset 
            self.te.lo_bg.y = loS.y + ydelta
        elif pt == self.te.lo_text:
            # moving (x,y) of point
            loS = self.drag_lo_textS
            self.te.move_to( loS.x + xdelta, loS.y + ydelta )
