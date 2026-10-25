import customtkinter as ct
from PIL import Image,ImageDraw

class VinylDisk(ct.CTkLabel):
    SS = 2
    def __init__(self,master,size=220,fps=30,speed=3):
        super().__init__(master , text="",fg_color="transparent",width=size,height=size)
        self.size = size
        self.delay = int(1000 / fps)
        self.speed = speed          # degrees per frame (higher = faster)
        self.angle = 0
        self.spinning = False
        self._job = None
        self._ctk = None
        self._prev = None    

        n = size*self.SS
        self.n = n
        self.cover_d = int(n*0.46)
        self.cover_off = (n-self.cover_d)//2
        self.base = self._make_vinyl(n)
        self.mask = Image.new("L",(self.cover_d,self.cover_d),0)
        ImageDraw.Draw(self.mask).ellipse((0, 0, self.cover_d - 1, self.cover_d - 1), fill=255)
        self.cover = None
        self._render()

    def _make_vinyl(self,n):
        img = Image.new("RGBA",(n,n),(0,0,0,0))
        d = ImageDraw.Draw(img)
        d.ellipse((0,0,n-1,n-1),fill=(16,16,20,255))
        r_out,r_in = n*0.48,n*0.27
        r = r_out
        while r>r_in:
            d.ellipse((n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r), outline=(30, 30, 38, 255), width=1)
            r -= n*0.012
        shine = Image.new("RGBA",(n,n),(0,0,0,0))
        sd = ImageDraw.Draw(shine)
        for start in (15,195):
            sd.pieslice((0,0,n - 1,n-1),start , start + 35 , fill=(255,255,255,26))
        img = Image.alpha_composite(img,shine)
        d = ImageDraw.Draw(img)
        rr = self.cover_d/2 + n*0.02
        d.ellipse((n / 2 - rr, n / 2 - rr, n / 2 + rr, n / 2 + rr), fill=(38, 38, 48, 255))
        d.ellipse((0, 0, n - 1, n - 1), outline=(60, 60, 72, 255), width=max(2, n // 150))
        return img

    def _render(self):
        frame = self.base.rotate(self.angle,resample=Image.BICUBIC)
        if self.cover is not None:
             frame.paste(self.cover, (self.cover_off, self.cover_off), self.mask)        
        d = ImageDraw.Draw(frame)
        h = self.n * 0.018
        c = self.n / 2
        d.ellipse((c - h, c - h, c + h, c + h), fill=(16, 16, 20, 255), outline=(90, 90, 105, 255))
        frame = frame.resize((self.size, self.size), Image.LANCZOS)

        self._perv = self._ctk
        self._ctk = ct.CTkImage(light_image=frame, dark_image=frame, size=(self.size, self.size))
        self.configure(image=self._ctk)

    def _spin(self):
        if not self.spinning:
            self._job=None
            return
        self.angle = (self.angle - self.speed) % 360     
        self._render()
        self._job = self.after(self.delay, self._spin)

    def set_cover(self,pil_image):
        if pil_image is None:
            self.cover = None
        else:
            self.cover = pil_image.convert("RGBA").resize((self.cover_d, self.cover_d), Image.LANCZOS)
        self._render()

    def play(self):
        if not self.spinning:
            self.spinning = True
            self._job = self.after(self.delay, self._spin)
 
    def pause(self):
        self.spinning = False
   