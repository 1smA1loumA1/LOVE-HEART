"""INFINITE LOVE — a generative, multilingual heart in Tkinter."""
from __future__ import annotations

import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


PHRASES = [
    "I love you", "Je t'aime", "Te amo", "Seni seviyorum", "Ich liebe dich",
    "Ti amo", "Я тебя люблю", "사랑해", "愛してる", "أحبك", "Kocham cię",
    "Eu te amo", "Mahal kita", "ฉันรักคุณ", "אני אוהב אותך", "હું તને પ્રેમ કરું છું",
    "Σ' αγαπώ", "Ik hou van jou", "Jeg elsker deg", "Jag älskar dig", "Rakastan sinua",
    "Te iubesc", "Volim te", "Miluji tě", "Ljubim te", "Ngiyakuthanda",
    "Ninakupenda", "Aishiteru", "Ya lyublyu tebya", "Minä rakastan sinua",
    "Anh yêu em", "我爱你", "我愛你", "Quiero estar contigo", "Mon cœur est à toi",
    "Amore mio", "Miłość", "Amor", "Любовь", "愛", "∞",
]
THEMES = [
    {"name": "RUBY", "colors": ["#651020", "#a51c35", "#e13a56", "#ff7992", "#ffd0d8"]},
    {"name": "ROSE", "colors": ["#681646", "#a72c6c", "#e14f91", "#ff8ab8", "#ffe0ee"]},
    {"name": "EMBER", "colors": ["#641c14", "#a43a24", "#e45b35", "#ff9b68", "#ffe2ba"]},
]
BG = "#060208"


def inside_heart(x: float, y: float) -> bool:
    """Implicit heart, with y increasing upward."""
    return (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0


class Particle:
    def __init__(self, canvas: tk.Canvas, rng: random.Random, index: int, width: int, height: int,
                 colors: list[str], size_factor: float, target: tuple[float, float],
                 font: tkfont.Font, box: tuple[float, float, float, float], phrase: str):
        self.canvas, self.rng, self.index = canvas, rng, index
        self.phrase = phrase
        self.font = font
        self.color = rng.choice(colors[1:])
        self.phase = rng.uniform(0, math.tau)
        self.drift = rng.uniform(.7, 2.3)
        self.twinkle = rng.uniform(1.5, 5.0)
        self.next_respawn = rng.uniform(18.0, 42.0)
        self.respawning_until = 0.0
        self.tx, self.ty = target
        self.box = box
        self.x = width / 2 + (target[0] - width / 2) * 1.055
        self.y = height / 2 + (target[1] - height / 2) * 1.055
        self.glow_id = canvas.create_text(self.x, self.y, text=self.phrase,
                                          fill=colors[0], font=("Georgia", int(font.cget("size")) + 2),
                                          anchor="center", tags="particle")
        self.id = canvas.create_text(self.x, self.y, text=self.phrase,
                                     fill=self.color, font=font, anchor="center", tags="particle")


class InfiniteLove:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("INFINITE LOVE")
        root.configure(bg=BG)
        root.geometry("1180x820")
        root.minsize(680, 520)
        self.rng = random.Random()
        self.theme_index = 0
        self.particles: list[Particle] = []
        self.running = True
        self.fullscreen = False
        self.settings_visible = True
        self.started = time.perf_counter()
        self.last = self.started
        self.assemble = 0.0
        self.heart_size = tk.DoubleVar(value=1.0)
        self.speed = tk.DoubleVar(value=1.0)
        self.density = tk.IntVar(value=360)
        self.message = tk.StringVar(value="")
        self.message.trace_add("write", lambda *_: self.schedule_rebuild())
        self.font_cache: dict[int, tkfont.Font] = {}
        self.center_font_cache: dict[int, tkfont.Font] = {}
        self.center_glow_ids = []
        self.center_id = None
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)
        self.build_controls()
        self.rebuild()
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<space>", self.toggle_pause)
        self.root.after(16, self.tick)

    def build_controls(self):
        self.panel = tk.Frame(self.root, bg="#100810", highlightbackground="#56202e", highlightthickness=1)
        self.panel.place(relx=.025, rely=.04, anchor="nw")
        tk.Label(self.panel, text="INFINITE  LOVE", bg="#100810", fg="#f7d9df",
                 font=("Georgia", 13, "bold")).pack(anchor="w", padx=15, pady=(13, 1))
        tk.Label(self.panel, text="A small universe, made of love", bg="#100810", fg="#a77c87",
                 font=("Georgia", 9, "italic")).pack(anchor="w", padx=15, pady=(0, 12))
        self.slider(self.panel, "HEART SCALE", self.heart_size, .72, 1.22, "%.2f")
        self.slider(self.panel, "MOTION", self.speed, .25, 2.0, "%.2f")
        self.slider(self.panel, "WORD COUNT", self.density, 150, 650, "%d")
        tk.Label(self.panel, text="CENTER MESSAGE", bg="#100810", fg="#c18b98",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15, pady=(8, 3))
        entry = tk.Entry(self.panel, textvariable=self.message, bg="#1b101a", fg="#f9d9e0",
                         insertbackground="#f9d9e0", relief="flat", width=25,
                         font=("Georgia", 10))
        entry.pack(fill="x", padx=15, pady=(0, 10), ipady=5)
        row = tk.Frame(self.panel, bg="#100810")
        row.pack(fill="x", padx=12, pady=(0, 12))
        self.play_btn = self.button(row, "Ⅱ  PAUSE", self.toggle_pause)
        self.play_btn.pack(side="left", padx=3)
        self.button(row, "↻  RESTART", self.restart).pack(side="left", padx=3)
        self.button(row, "◈  THEME", self.cycle_theme).pack(side="left", padx=3)
        self.button(row, "⛶", self.toggle_fullscreen).pack(side="left", padx=3)
        self.button(self.root, "☰", self.toggle_settings).place(relx=.975, rely=.04, anchor="ne")

    def slider(self, parent, label, variable, low, high, fmt):
        tk.Label(parent, text=label, bg="#100810", fg="#c18b98",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15)
        scale = tk.Scale(parent, variable=variable, from_=low, to=high, resolution=(1 if label == "WORD COUNT" else .01),
                         orient="horizontal", length=220, showvalue=True,
                         bg="#100810", fg="#f4ccd5", troughcolor="#46202d",
                         activebackground="#d45470", highlightthickness=0, bd=0,
                         font=("Segoe UI", 8))
        scale.pack(padx=10, pady=(0, 5))
        if label == "WORD COUNT":
            scale.configure(command=lambda _v: self.schedule_rebuild())
        elif label == "HEART SCALE":
            scale.configure(command=lambda _v: self.refresh_targets())

    def button(self, parent, label, command):
        return tk.Button(parent, text=label, command=command, bg="#26121e", fg="#f3dce1",
                         activebackground="#57253a", activeforeground="white", relief="flat",
                         bd=0, padx=9, pady=6, font=("Segoe UI", 8, "bold"), cursor="hand2")

    def schedule_rebuild(self):
        if hasattr(self, "rebuild_job"):
            self.root.after_cancel(self.rebuild_job)
        self.rebuild_job = self.root.after(180, self.rebuild)

    def rebuild(self):
        self.canvas.delete("particle")
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        colors = THEMES[self.theme_index]["colors"]
        self.particles = []
        self.font_cache.clear()
        for i, (x, y, font, box, phrase) in enumerate(self.pack_words(w, h)):
            p = Particle(self.canvas, self.rng, i, w, h, colors, self.heart_size.get(),
                         (x, y), font, box, phrase)
            self.particles.append(p)
        self.create_center_message()

    @staticmethod
    def overlaps(a, b):
        return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

    def pack_words(self, w, h):
        """Pack measured text rectangles inside the heart with a spatial hash."""
        cx, cy = w / 2, h / 2
        scale = min(w * .35, h * .37) * self.heart_size.get()
        gap = 5
        cell = 32
        grid: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
        placed = []

        def grid_cells(box):
            return [(gx, gy) for gx in range(int(box[0] // cell), int(box[2] // cell) + 1)
                    for gy in range(int(box[1] // cell), int(box[3] // cell) + 1)]

        center_w, center_h = scale * .38, scale * .22
        center_box = (cx - center_w / 2, cy - center_h / 2,
                      cx + center_w / 2, cy + center_h / 2)
        reserved = True
        for i in range(self.density.get()):
            phrase = self.rng.choice(PHRASES)
            accepted = None
            # Work down from elegant display sizes; never force a collision to hit density.
            for size in (14, 13, 12, 11, 10, 9):
                if size not in self.font_cache:
                    self.font_cache[size] = tkfont.Font(self.root, family="Georgia", size=size)
                font = self.font_cache[size]
                glow_size = size + 2
                if glow_size not in self.font_cache:
                    self.font_cache[glow_size] = tkfont.Font(self.root, family="Georgia", size=glow_size)
                bounds_font = self.font_cache[glow_size]
                width = bounds_font.measure(phrase)
                height = bounds_font.metrics("linespace")
                rw, rh = width / 2 + gap, height / 2 + gap
                for _ in range(160):
                    u, v = self.rng.uniform(-1.02, 1.02), self.rng.uniform(-1.02, 1.02)
                    if not inside_heart(u, v):
                        continue
                    x, y = cx + u * scale, cy - v * scale
                    box = (x - rw, y - rh, x + rw, y + rh)
                    if any(not inside_heart((px - cx) / scale, (cy - py) / scale)
                           for px in (box[0], box[2]) for py in (box[1], box[3])):
                        continue
                    if reserved and self.overlaps(box, center_box):
                        continue
                    nearby = {id(other): other for key in grid_cells(box)
                              for other in grid.get(key, ())}.values()
                    if any(self.overlaps(box, other) for other in nearby):
                        continue
                    accepted = (x, y, font, box, phrase)
                    break
                if accepted:
                    break
            if accepted:
                placed.append(accepted)
                box = accepted[3]
                for key in grid_cells(box):
                    grid.setdefault(key, []).append(box)
        return placed

    def create_center_message(self):
        self.canvas.delete("center_message")
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        cx, cy = w / 2, h / 2 + 4
        # Two low-intensity text passes create a restrained crimson halo, with no panel.
        self.center_glow_ids = [self.canvas.create_text(cx, cy, text="", fill="#681126",
                                    font=("Georgia", 22, "italic"), justify="center",
                                    anchor="center", tags="center_message")]
        self.center_id = self.canvas.create_text(cx, cy, text="", fill="#ffe5eb",
                                    font=("Georgia", 22, "italic"), justify="center",
                                    anchor="center", tags="center_message")
        self.draw_center(w, h)

    def on_resize(self, _event=None):
        if self.canvas.winfo_width() > 1:
            self.schedule_rebuild()

    def refresh_targets(self):
        self.schedule_rebuild()

    def tick(self):
        now = time.perf_counter()
        dt = min(.05, now - self.last)
        self.last = now
        if self.running and self.particles:
            self.assemble = min(1.0, self.assemble + dt * .22 * self.speed.get())
            eased = self.assemble * self.assemble * (3 - 2 * self.assemble)
            t = now - self.started
            pulse = 1 + .018 * math.sin(t * 2.1) if self.assemble >= 1 else 1
            w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
            for p in self.particles:
                if t >= p.next_respawn and p.respawning_until == 0.0:
                    # Briefly vanish, then reappear a few pixels from their assigned slot.
                    self.canvas.itemconfigure(p.id, state="hidden")
                    self.canvas.itemconfigure(p.glow_id, state="hidden")
                    p.respawning_until = t + .22
                    p.next_respawn = t + self.rng.uniform(22.0, 48.0)
                elif p.respawning_until and t >= p.respawning_until:
                    p.x = p.tx + self.rng.uniform(-2, 2)
                    p.y = p.ty + self.rng.uniform(-2, 2)
                    p.respawning_until = 0.0
                    self.canvas.itemconfigure(p.id, state="normal")
                    self.canvas.itemconfigure(p.glow_id, state="normal")
                tx = w / 2 + (p.tx - w / 2) * pulse
                ty = h / 2 + (p.ty - h / 2) * pulse
                # Controlled easing keeps words close to their collision-free slots.
                amount = min(1, dt * 1.45 * self.speed.get()) * max(.2, eased)
                x = p.x + (tx - p.x) * amount
                y = p.y + (ty - p.y) * amount
                p.x, p.y = x, y
                self.canvas.coords(p.id, x, y)
                self.canvas.coords(p.glow_id, x, y)
                self.canvas.itemconfigure(p.id, fill=p.color)
            self.draw_center(w, h)
        self.root.after(16, self.tick)

    def draw_center(self, w, h):
        text = self.message.get().strip()
        scale = min(w * .35, h * .37) * self.heart_size.get()
        max_width, max_height = scale * .34, scale * .17
        chosen, wrapped = 14, text
        for size in range(26, 13, -1):
            if size not in self.center_font_cache:
                self.center_font_cache[size] = tkfont.Font(self.root, family="Georgia", size=size, slant="italic")
            font = self.center_font_cache[size]
            lines = []
            for paragraph in text.splitlines() or [""]:
                line = ""
                for word in paragraph.split():
                    candidate = f"{line} {word}".strip()
                    if line and font.measure(candidate) > max_width:
                        lines.append(line)
                        line = word
                    else:
                        line = candidate
                lines.append(line)
            rendered = "\n".join(lines)
            if (font.measure(max(lines, key=font.measure, default="")) <= max_width
                    and font.metrics("linespace") * len(lines) <= max_height):
                chosen, wrapped = size, rendered
                break
        cx, cy = w / 2, h / 2 + 4
        glow_font = self.center_font_cache[chosen]
        self.canvas.coords(self.center_glow_ids[0], cx + 1, cy + 1)
        self.canvas.itemconfigure(self.center_glow_ids[0], text=wrapped, font=glow_font)
        self.canvas.coords(self.center_id, cx, cy)
        self.canvas.itemconfigure(self.center_id, text=wrapped, font=glow_font)

    def toggle_pause(self):
        self.running = not self.running
        self.play_btn.configure(text="Ⅱ  PAUSE" if self.running else "▶  PLAY")
        if self.running:
            self.last = time.perf_counter()

    def restart(self):
        self.started, self.last, self.assemble = time.perf_counter(), time.perf_counter(), 0
        self.running = True
        self.play_btn.configure(text="Ⅱ  PAUSE")
        self.rebuild()

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.rebuild()

    def toggle_settings(self):
        self.settings_visible = not self.settings_visible
        if self.settings_visible:
            self.panel.place(relx=.025, rely=.04, anchor="nw")
        else:
            self.panel.place_forget()

    def toggle_fullscreen(self, _event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"

    def exit_fullscreen(self, _event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes("-fullscreen", False)
            return "break"


def main():
    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("clam")
    except tk.TclError:
        pass
    InfiniteLove(root)
    root.mainloop()


if __name__ == "__main__":
    main()
