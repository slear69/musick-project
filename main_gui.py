
import os
import shutil
import hashlib
import customtkinter as ct
import pywinstyles
import vlc
from tkinter import filedialog
from PIL import Image, ImageDraw
from io import BytesIO
from mutagen import File as mf
from vinyl_disk import VinylDisk
 
ct.set_appearance_mode("dark")
 
# the "music" folder sits next to your "ui" folder, e.g. D:\MUSIC\music
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, "music")
AUDIO_EXT = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
os.makedirs(MUSIC_DIR, exist_ok=True)
 
 
def fmt(seconds):
    """123 -> '2:03'"""
    seconds = max(int(seconds), 0)
    return f"{seconds // 60}:{seconds % 60:02d}"
 
def parse_name(filename):
    stem = os.path.splitext(filename)[0]
    if "-" in stem:
        artist , title = stem.split("-",1)
        return title.strip() , artist.strip()
    return stem , "Unknown artist"
 
def make_cover(name, size=(120, 68)):
    """Makes a gradient 'cover' from the file name, so every song gets its own colors."""
    h = hashlib.md5(name.encode()).digest()
    bright = lambda v: 80 + v * 150 // 255          # keep colors from being too dark
    c1 = (bright(h[0]), bright(h[1]), bright(h[2]))
    c2 = (bright(h[3]), bright(h[4]), bright(h[5]))
    w, hgt = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(hgt):
        t = y / max(hgt - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return img

def spuare(img , size = 200):
    w,h = img.size
    s = min(w,h)
    left , top = (w-s)//2,(h-s)//2
    return img.crop((left, top, left + s, top + s)).resize((size, size))

def load_cover(path , fallback_name):
    base = os.path.splitext(path)[0]
    for ext in (".jpg",".jpeg",".png"):
        if os.path.exists(base + ext):
            return spuare(Image.open(base + ext).convert("RGB"))
    try:
        audio = mf(path)
        data = None
        if audio is not None and audio.tags is not None:
            if hasattr(audio.tags, "getall"):                      # mp3
                pics = audio.tags.getall("APIC")
                if pics:
                    data = pics[0].data
            elif "covr" in audio.tags:                             # m4a
                data = bytes(audio.tags["covr"][0])
        if data is None and audio is not None and getattr(audio, "pictures", None):   # flac
            data = audio.pictures[0].data
        if data:
            return spuare(Image.open(BytesIO(data)).convert("RGB"))
    except Exception as e:
        print("couldn't read cover for", path, "-", e)

    return spuare(make_cover(fallback_name))

class App(ct.CTk):
    def __init__(self):
        super().__init__()
        self.vlc_player = None
        self.songs = []          # every song found in the music folder
        self.index = -1          # which song is playing
        self.images = []         # keeps images alive so they don't vanish
        
 
        self.title("My musickplayer")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.attributes("-alpha", 1.0)
        # remove: pywinstyles.apply_style(self, "aero")
        KEY = "#293052"                      # this exact color becomes see-through
        self.attributes("-transparentcolor", KEY)
        self.configure(fg_color=KEY)
        self.configure(fg_color="#636E8A")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
 
        self.sidebar = ct.CTkFrame(self, width=260, fg_color="#192740", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
 
        self.content = ct.CTkFrame(self, fg_color="#24385A", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
 
        self.player = ct.CTkFrame(self, height=90, fg_color="#192740", corner_radius=0)
        self.player.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.player.grid_propagate(False)

        self.disc = VinylDisk(self.sidebar, size=230)
        self.disc.place(x=15, y=190)
        self.drag = False
        self.seek = ct.CTkSlider(self.player , from_=0,to=1,width=600,height=16,command=self.onseek,fg_color="#3a4766",progress_color="#6f8cff",button_color="#ffffff",button_hover_color="#cfd8ff")

        self.seek.set(0)
        self.seek.place(x=450,y=64)
        self.seek.bind("<ButtonPress-1>",self.seek_start,add="+")
        self.seek.bind("<ButtonRelease-1>",self.seek_end,add="+")
        def clicked_btn():
            print("Button clicked!")
 
        # player bar buttons
        self.createbtn(self.resume, self.player, width=10, height=40, padx=700, pady=10, curve=30, txt="▶", size=15)
        self.createbtn(self.pause_track, self.player, width=10, height=40, padx=600, pady=10, curve=30, txt="⏸", size=15)
        self.createbtn(self.next_song, self.player, width=10, height=40, padx=790, pady=10, curve=30, txt="⏭", size=15)
 
        # sidebar buttons
        self.createbtn(clicked_btn, self.sidebar, width=30, height=30, padx=200, pady=10, curve=6, txt="⌂", size=15)
        self.createbtn(clicked_btn, self.sidebar, width=30, height=30, padx=160, pady=10, curve=6, txt="⚙", size=15)
        self.createbtn(self.add_music, self.sidebar, width=190, height=36, padx=45, pady=60, curve=10, txt="➕  Add music", size=14)
        self.createbtn(lambda: os.startfile(MUSIC_DIR), self.sidebar, width=190, height=36,padx=45, pady=104, curve=10, txt="📂  Open music folder", size=14)
        # search bar (packed BEFORE the results so it stays on top)
        self.search = ct.CTkEntry(
            master=self.content,
            placeholder_text="search your music",
            height=44,
            corner_radius=22,
            fg_color="#1c1c26",
            border_color="#3a3a4d",
            border_width=1,
            text_color="white",
            font=ct.CTkFont(size=15)
        )
        self.decore(180,470,120,"ROSE.png")

        self.decore(1000,0,90,"ROSE.png")
        self.decore(25,-25,80,"ado.png")
        
        self.search.pack(fill="x", padx=(10, 100), pady=20)
        self.search.bind("<KeyRelease>", self.on_search)   # local search is free, so live is fine
 
        self.results = ct.CTkScrollableFrame(self.content, fg_color="transparent")
        self.results.pack(fill="both", expand=True, padx=30, pady=(0, 20))
 
        # now-playing area in the bottom bar
        self.np_image = ct.CTkLabel(self.player, text="", width=100, height=56)
        self.np_image.place(x=10, y=17)
        self.np_title = ct.CTkLabel(self.player, text="Nothing playing", width=260, anchor="w",
                                    font=ct.CTkFont(size=14, weight="bold"))
        self.np_title.place(x=120, y=10)
        self.np_artist = ct.CTkLabel(self.player, text="", width=260, anchor="w")
        self.np_artist.place(x=120, y=34)
        self.np_time = ct.CTkLabel(self.player, text="0:00 / 0:00", width=260, anchor="w")
        self.np_time.place(x=120, y=58)
        self.folder_state = tuple(sorted(os.listdir(MUSIC_DIR)))
        self.load_songs()
        self.after(500, self.tick)
        self.after(2000,self.wach_folder)
 
    def createbtn(self, buttondo, section, width, height, padx, pady, curve, txt, size):
        button = ct.CTkButton(
            master=section,
            text=txt,
            command=buttondo,
            width=width,
            font=ct.CTkFont(size=size, weight="normal"),
            height=height,
            fg_color="#455885",
            hover_color="#3D4C7C",
            corner_radius=curve
        )
        button.place(x=padx, y=pady)
 
    def load_songs(self):
        """Reads the music folder and shows every audio file in it."""
        self.songs = []
        for f in sorted(os.listdir(MUSIC_DIR)):
            if f.lower().endswith(AUDIO_EXT):
                title, artist = parse_name(f)
                self.songs.append({
                    "path": os.path.join(MUSIC_DIR, f),
                    "title": title,
                    "artist": artist,
                    "cover": load_cover(os.path.join(MUSIC_DIR, f), f),
                })
        self.on_search()
        
    def wach_folder(self):
        now = tuple(sorted(os.listdir(MUSIC_DIR)))
        if now != self.folder_state:
            self.folder_state = now
            self.load_songs()
        self.after(2000,self.wach_folder)
 
    def on_search(self, event=None):
        q = self.search.get().strip().lower()
        matches = [s for s in self.songs
                   if q in s["title"].lower() or q in s["artist"].lower()]
        self.show_results(matches)
 
    def show_results(self, songs):
        for w in self.results.winfo_children():
            w.destroy()
        self.images.clear()
        if not songs:
            ct.CTkLabel(self.results, justify="left", anchor="w",
                        text=f"No songs found.\nPut audio files in:\n{MUSIC_DIR}"
                        ).pack(anchor="w", padx=10, pady=20)
            return
        for s in songs:
            img = ct.CTkImage(light_image=s["cover"], size=(68, 68))
            self.images.append(img)
            ct.CTkButton(self.results, image=img, compound="left", anchor="w",
                         text=f'{s["title"]}\n{s["artist"]}',
                         font=ct.CTkFont(size=14), height=80,
                         fg_color="#12121a", hover_color="#26263a",
                         command=lambda s=s: self.play_song(s)
                         ).pack(fill="x", pady=2)
 
    def add_music(self):
        """Copies songs you pick from anywhere on your PC into the music folder."""
        files = filedialog.askopenfilenames(
            title="Pick music to add",
            filetypes=[("Audio", "*.mp3 *.wav *.flac *.ogg *.m4a")])
        for f in files:
            shutil.copy(f, MUSIC_DIR)
        if files:
            self.load_songs()
 
    def play_song(self, song):
        if self.vlc_player:
            self.vlc_player.stop()
        self.index = self.songs.index(song)
        self.vlc_player = vlc.MediaPlayer(song["path"])
        self.vlc_player.play()
        self.cur_img = ct.CTkImage(light_image=song["cover"], size=(56, 56))
        self.np_image.configure(image=self.cur_img)
        self.np_title.configure(text=song["title"])
        self.np_artist.configure(text=song["artist"])
        self.np_time.configure(text="0:00 / 0:00")
        self.seek.set(0)
        self.disc.set_cover(song["cover"])
        self.disc.play() 
 
    def resume(self):
        if self.vlc_player:
            self.vlc_player.play()
            self.disc.play()
        elif self.songs:
            self.play_song(self.songs[0])
 
    def pause_track(self):
        if self.vlc_player:
            self.vlc_player.set_pause(1)
            self.disc.pause
 
    def next_song(self):
        if self.songs:
            self.play_song(self.songs[(self.index + 1) % len(self.songs)])
 
    def tick(self):
        """Runs twice a second: updates the clock and moves on when a song ends."""
        p = self.vlc_player
        if p:
            cur_ms = max(p.get_time(), 0)
            total_ms = max(p.get_length(), 0)
            if not self.drag:
                self.np_time.configure(text=f"{fmt(cur_ms // 1000)} / {fmt(total_ms // 1000)}")
                self.seek.set(cur_ms / total_ms if total_ms else 0)
            if p.get_state() == vlc.State.Ended:
                self.next_song()
        self.after(250, self.tick)
 
    def on_close(self):
        if self.vlc_player:
            self.vlc_player.stop()
        self.destroy()

    def onseek(self, value):
        p = self.vlc_player
        if p and self.drag:
            total = max(p.get_length(), 0) // 1000
            self.np_time.configure(text=f"{fmt(value * total)} / {fmt(total)}")

    def seek_start(self,event):
        self.drag = True
    
    def seek_end(self,event):
        self.drag=False
        p = self.vlc_player
        if p and p.get_length() > 0:
            p.set_time(int(self.seek.get() * p.get_length()))

    def decore(self,x,y,size,img):
        SIDE, MAIN = "#192740", "#24385A"     
        size = size
        X, Y = x, y
        src = Image.open(os.path.join(BASE_DIR, img)).convert("RGBA").resize((size, size), Image.LANCZOS)
        bg = Image.new("RGBA",(size , size),MAIN)
        left_w= max(0,min(size,260-X))
        bg.paste(Image.new("RGBA", (left_w, size), SIDE), (0, 0))  
        bg.alpha_composite(src)
        self.rose_img = ct.CTkImage(light_image=bg, dark_image=bg, size=(size, size))
        self.rose_label = ct.CTkLabel(self, image=self.rose_img, text="", fg_color=MAIN)
        self.rose_label.place(x=X , y=Y)
        self.rose_label.lift()
    
App().mainloop()
 
