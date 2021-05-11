from PIL import ImageDraw
import tkinter.messagebox as msgbox
from scripts import Pt,get_font
import imgpool as ip

# the display is global: this set in comiola.py
display = None

# dimension for contrl handle (actually 1/2 the width)
hand_dim = 6

# A handle binds a Pt to a small, clickable shape shown in
# the display. selectable == True means that, when clicked,
# the pt becomes the selected point in the display.
class Handle:
    def __init__(self,pt,selectable):
        self.pt = pt
        pt.handle = self
        self.selectable = selectable
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
        (x0,y0) = display.to_draw_coords(int(p.x - dim), int(p.y - dim))
        (x1,y1) = display.to_draw_coords(int(p.x + dim), int(p.y + dim))
        if shape == 'rect':
            draw_pil.rectangle((x0,y0,x1,y1),fill=color)
        elif shape == 'tri':
            (x0,y0) = display.to_draw_coords(p.x - dim, p.y + dim)
            (x1,y1) = display.to_draw_coords(p.x, p.y - dim)
            (x2,y2) = display.to_draw_coords(p.x + dim, p.y + dim)
            draw_pil.polygon((x0,y0,x1,y1,x2,y2),fill=color)
        else:
            draw_pil.ellipse((x0,y0,x1,y1),fill=color)

# An (x,y) value: representation is float
class XY:
    def __init__(self,x,y,ani):
        self.x = float(x)
        self.y = float(y)
        self.ani = ani

    def clone(self):
        return XY(self.x,self.y,self.ani)

# Control for a point in an Ani path, for sprite and camera
# animations.
class PtCntrl:
    def __init__(self,pt):
        self.pt = pt
        pt.cntrl = self
        self.resizeW = XY(0.0,0.0,pt.ani)
        self.resizeW.cntrl = self
        Handle(pt,True)
        Handle(self.resizeW,False)
        # aspect ratio: when we change pt.w, we change pt.h
        self.ar = pt.h/pt.w
        # (x,y) at start of mousemove
        self.dragS = None
        # clone of "pt" at start of mousemove
        self.dragptS = None

    def draw(self,draw_pil,color):
        p = self.pt
        shape = 'oval' if p == display.sel_pt else 'rect'
        p.handle.draw(draw_pil,color,shape)
        # draw a rectangle showing size
        w = int(p.w/2) - 2
        h = int(p.h/2) - 2
        (x0,y0) = display.to_draw_coords(p.x - w, p.y - h)
        (x1,y1) = display.to_draw_coords(p.x + w, p.y + h)
        draw_pil.rectangle((x0,y0,x1,y1), outline=color)
        if p.ani != display.sel_ani:
            return
        # position and draw the resize handle
        p = self.pt
        self.resizeW.x = p.x + int( p.w/2 - hand_dim/2 )
        self.resizeW.y = p.y
        self.resizeW.handle.draw(draw_pil,color,'tri')
 
    def on_mousedown(self,pt,x,y):
        if display.sel_ani != pt.ani:
            return
        if display.action == 'track':
            self.make_tracking()
        self.dragS = [x,y]
        self.dragptS = self.pt.clone()

    def on_mouseup(self,pt,x,y):
        self.dragS = None

    def on_mousemove(self,pt,x,y):
        if (self.dragS is None or
            display.sel_ani != pt.ani):
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
        if display.sel_ani.kind == 'cam':
            self.validate_cam_path()

    def validate_cam_path(self):
        # ensure a camera path is fully contained within image
        an = display.sel_ani
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

    def make_tracking(self):
        # Create a tracking animation. UI sequence is:
        # 1. user clicks on the tracking cam or sprite, selecting it.
        # 2. user clicks "Track" button in menu. "display.action"
        # is set to "track", and "display.first_sel_pt" is set to
        # the currently selected point.
        # 3. user clicks first point in the "anchor" ani (that's the
        # animation the sprite or camera will follow).
        # This code is called at step 3. At this point display.sel_ani
        # gives the anchor ani
        anchor = display.sel_ani
        # "ani" is the tracking animation.
        ani = display.first_sel_pt.ani
        # "pt": currently selected point. If it's in the path of the
        # anchor, the lock is illegal
        pt = display.sel_pt
        if display.first_sel_pt in anchor.path:
            msgbox.showerror('Comiola',
"Tracking failed: camera (or sprite) can't track itself ")
            return
        # And pt must be the first animation point of the lock-ee
        #if pt != ani.path[0]:
            #msgbox.showerror('Comiola',
                #"Selected point must be first point in animation path")
            #return
        # rebuild the tracker's path
        # anchor_0 is first point in the anchor path
        # ani_0 is first point in the ani path
        anchor_0 = anchor.path[0]
        ani_0 = ani.path[0]
        xoff = (ani_0.x - anchor_0.x)/anchor_0.w
        yoff = (ani_0.y - anchor_0.y)/anchor_0.w
        w_factor = ani_0.w/anchor_0.w
        ani.cntrl.delete_all_pts()
        for px in anchor.path:
            x = px.x + xoff*px.w
            y = px.y + yoff*px.w
            w = px.w*w_factor
            p = Pt(x,y,0.0,0.0,0.0,w,w)
            ani.add_pt(p)
            p.ani = ani
            if ani.kind in ['spr','cam']:
                PtCntrl(p)
            else:
                TxtPtCntrl(p,ani.te)
        ani.cycles = anchor.cycles
        ani.tS = anchor.tS
        ani.tE = anchor.tE
        display.validate_view()








        

# control for an Ani: allows user to modify the path Pts.
class AniCntrl:
    def __init__(self,ani,name):
        self.ani = ani
        ani.cntrl = self
        # "name" used for debugging
        self.name = name
        for p in ani.path:
            p.ani = ani
            if ani.kind in ['spr','cam']:
                PtCntrl(p)
            else:
                TxtPtCntrl(p,ani.te)
        self.dragS = None
        self.dragptS = None

    def add_pt(self):
        ani = self.ani
        p = ani.path[-1]
        p = Pt(p.x + 50,p.y,0.0,p.z,0.0,p.w,p.h)
        ani.add_pt(p)
        p.ani = ani
        if ani.kind in ['spr','cam']:
            PtCntrl(p)
        else:
            TxtPtCntrl(p,ani.te)
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
        basecolor = 'green' if ani.kind == 'cam' else 'red'
        for i in range(0,len(ani.path)):
            p = ani.path[i]
            if ani.kind == 'cam':
                color = get_color('green',i,len(ani.path))
            elif ani.kind == 'spr':
                color = get_color('red',i,len(ani.path))
            else:
                # text element: doesn't change
                color = '#00ffff'
            p.cntrl.draw(draw_pil,color)

# Control for a point in an Ani path, for txt animations.
class TxtPtCntrl:
    def __init__(self,pt,te):
        self.pt = pt
        pt.cntrl = self
        self.te = te
        # resize control bg w and h
        self.bgsize = XY(0,0,pt.ani)
        self.bgsize.cntrl = self
        # y offset control for bg
        self.yoff_bg = XY(0,0,pt.ani)
        self.yoff_bg.cntrl = self
        Handle(pt,True)
        Handle(self.bgsize,False)
        Handle(self.yoff_bg,False)
        # (x,y) at start of mousemove
        self.dragS = None
        # clones of pt & te at start of mousemove
        self.drag_teS = None
        self.drag_ptS = None

    def draw(self,draw_pil,color):
        # draw pt handle
        pt = self.pt
        shape = 'oval' if pt == display.sel_pt else 'rect'
        pt.handle.draw(draw_pil,color,shape)
        if pt.ani != display.sel_ani:
            return
        # position handles
        # get bounding box for bg
        (x0,y0,x1,y1) = self.te.get_bb_bg(self.pt.x,self.pt.y)
        #  bgsize is at lower right corner
        (self.bgsize.x, self.bgsize.y) = (x1,y1)
        # yoff is top center
        (self.yoff_bg.x, self.yoff_bg.y) = ( (x0+x1)/2, y0 )
        # draw handles for resize and yoff
        self.bgsize.handle.draw(draw_pil,color,'tri')
        self.yoff_bg.handle.draw(draw_pil,color,'tri')
        # draw a rectangle showing size
        (x0,y0) = display.to_draw_coords(x0,y0)
        (x1,y1) = display.to_draw_coords(x1,y1)
        draw_pil.rectangle((x0,y0,x1,y1), outline=color)

    def on_mousedown(self,pt,x,y):
        if display.sel_ani != pt.ani:
            return
        self.dragS = [x,y]
        self.drag_teS = self.te.clone()
        self.drag_ptS = self.pt.clone()

    def on_mouseup(self,pt,x,y):
        self.dragS = None

    def on_mousemove(self,pt,x,y):
        if (self.dragS is None or
            display.sel_ani != pt.ani):
            return
        xdelta = x - self.dragS[0]
        ydelta = y - self.dragS[1]
        teS = self.drag_teS
        te = self.te
        if pt == self.bgsize:
            te.w_bg = teS.w_bg + 2*xdelta
            te.h_bg = teS.h_bg + 2*ydelta
        elif pt == self.yoff_bg:
            # resizing offset 
            te.yoff_bg = teS.yoff_bg + ydelta
        elif pt == self.pt:
            # moving (x,y) of point
            ptS = self.drag_ptS
            self.pt.set_xy( ptS.x + xdelta, ptS.y + ydelta )
