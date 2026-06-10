"""
Folder Icon Changer - Aplicação para alterar o ícone de pastas no Windows
Requer: pip install pillow
"""

import os
import sys
import ctypes
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageTk, ImageDraw, ImageFilter


# ─────────────────────────────────────────────
#  CONSTANTES DE COR / TEMA ESCURO
# ─────────────────────────────────────────────
BG          = "#0b1020"
SURFACE     = "#121827"
SURFACE2    = "#1a2436"
ACCENT      = "#14b8a6"
ACCENT_DARK = "#0f8f87"
ACCENT_GLOW = "#22d3ee"
TEXT        = "#f8fafc"
TEXT_DIM    = "#94a3b8"
SUCCESS     = "#4ade80"
DANGER      = "#f87171"
BORDER      = "#2f3b52"
AMBER       = "#ffb84d"

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)


# ─────────────────────────────────────────────
#  LÓGICA PRINCIPAL: ALTERAR ÍCONE NO WINDOWS
# ─────────────────────────────────────────────

def image_to_ico(src_path: str, dst_ico: str):
    """Converte qualquer imagem para .ico com múltiplos tamanhos."""
    img = Image.open(src_path).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = []
    for s in sizes:
        resized = img.resize(s, Image.LANCZOS)
        icons.append(resized)
    icons[0].save(dst_ico, format="ICO", sizes=[i.size for i in icons],
                  append_images=icons[1:])


def set_folder_icon(folder_path: str, ico_path: str) -> str:
    """
    Define o ícone de uma pasta via desktop.ini.
    Retorna uma mensagem de status.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError("Caminho selecionado não é uma pasta válida.")

    # Copia o .ico para dentro da pasta com nome fixo
    dst_ico = folder / "folder_icon.ico"
    shutil.copy2(ico_path, dst_ico)

    # Cria / sobrescreve desktop.ini
    ini_path = folder / "desktop.ini"
    ini_content = (
        "[.ShellClassInfo]\n"
        f"IconResource=folder_icon.ico,0\n"
        "[ViewState]\n"
        "Mode=\nVid=\nFolderType=Generic\n"
    )
    ini_path.write_text(ini_content, encoding="utf-8")

    # Atributos necessários
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_SYSTEM = 0x04
    FILE_ATTRIBUTE_READONLY = 0x01

    ctypes.windll.kernel32.SetFileAttributesW(str(ini_path),
        FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    ctypes.windll.kernel32.SetFileAttributesW(str(dst_ico),
        FILE_ATTRIBUTE_HIDDEN)
    ctypes.windll.kernel32.SetFileAttributesW(str(folder),
        FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_SYSTEM)

    # Notifica o Explorer para atualizar ícones
    SHCNE_UPDATEDIR = 0x00001000
    SHCNF_PATHW     = 0x0005
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW,
                                         str(folder), None)
    return f"Ícone aplicado com sucesso em '{folder.name}'!"


def reset_folder_icon(folder_path: str) -> str:
    """Remove o ícone personalizado e restaura o padrão."""
    folder = Path(folder_path)
    for f in ["desktop.ini", "folder_icon.ico"]:
        target = folder / f
        if target.exists():
            ctypes.windll.kernel32.SetFileAttributesW(str(target), 0x80)  # NORMAL
            target.unlink()
    ctypes.windll.kernel32.SetFileAttributesW(str(folder), 0x10)  # DIRECTORY
    SHCNE_UPDATEDIR = 0x00001000
    SHCNF_PATHW     = 0x0005
    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW,
                                         str(folder), None)
    return f"Ícone de '{folder.name}' restaurado para o padrão!"


# ─────────────────────────────────────────────
#  WIDGETS PERSONALIZADOS
# ─────────────────────────────────────────────

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=180, height=44,
                 bg=ACCENT, hover=ACCENT_DARK, fg=TEXT, radius=12,
                 font=FONT_BODY, **kwargs):
        super().__init__(parent, width=width, height=height,
                         background=parent["bg"], highlightthickness=0,
                         bd=0, **kwargs)
        self._bg = bg
        self._hover = hover
        self._fg = fg
        self._text = text
        self._cmd = command
        self._r = radius
        self._btn_w = width
        self._btn_h = height
        self._font = font
        self._draw(bg)
        self.bind("<Enter>", lambda e: self._draw(hover))
        self.bind("<Leave>", lambda e: self._draw(bg))
        self.bind("<Button-1>", lambda e: self._click())
        self.bind("<ButtonRelease-1>", lambda e: self._draw(hover))

    def _draw(self, color):
        self.delete("all")
        r = self._r
        w, h = self._btn_w, self._btn_h
        self.create_arc(0,     0,     2*r, 2*r, start=90,  extent=90,  fill=color, outline=color)
        self.create_arc(w-2*r, 0,     w,   2*r, start=0,   extent=90,  fill=color, outline=color)
        self.create_arc(0,     h-2*r, 2*r, h,   start=180, extent=90,  fill=color, outline=color)
        self.create_arc(w-2*r, h-2*r, w,   h,   start=270, extent=90,  fill=color, outline=color)
        self.create_rectangle(r, 0, w-r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h-r, fill=color, outline=color)
        self.create_text(w//2, h//2, text=self._text, fill=self._fg,
                         font=self._font)

    def _click(self):
        self._draw(ACCENT_GLOW)
        if self._cmd:
            self.after(80, self._cmd)

    def configure(self, **kw):
        if "text" in kw:
            self._text = kw.pop("text")
            self._draw(self._bg)
        super().configure(**kw)


class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=SURFACE, **kwargs)
        self._dot = tk.Label(self, text="●", bg=SURFACE, fg=TEXT_DIM,
                             font=("Segoe UI", 12))
        self._dot.pack(side="left", padx=(12, 6), pady=6)
        self._lbl = tk.Label(self, text="Pronto.", bg=SURFACE, fg=TEXT_DIM,
                             font=FONT_SMALL, anchor="w")
        self._lbl.pack(side="left", fill="x", expand=True, pady=6)

    def set(self, msg, color=TEXT_DIM):
        self._lbl.config(text=msg, fg=color)
        self._dot.config(fg=color)

    def ok(self, msg):   self.set(msg, SUCCESS)
    def err(self, msg):  self.set(msg, DANGER)
    def info(self, msg): self.set(msg, ACCENT_GLOW)


# ─────────────────────────────────────────────
#  JANELA PRINCIPAL
# ─────────────────────────────────────────────

class FolderIconChanger(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Folder Icon Changer - IDS")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._set_window_icon()
        self._center(700, 600)

        # Estado
        self._folder_path = tk.StringVar()
        self._image_path  = tk.StringVar()
        self._preview_img = None   # referência para evitar GC
        self._ico_tmp     = Path(os.environ.get("TEMP", ".")) / "_fic_tmp.ico"

        self._build_ui()

    def _set_window_icon(self):
        """Usa o ícone do projeto na janela e na barra de tarefas."""
        icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "folder_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

    # ── posicionamento central ─────────────────
    def _center(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── construção da UI ───────────────────────
    def _build_ui(self):
        # ── Cabeçalho ──────────────────────────
        header = tk.Frame(self, bg=SURFACE, padx=24, pady=20)
        header.pack(fill="x")

        tk.Label(header, text="Folder Icon Changer",
                 font=FONT_TITLE, bg=SURFACE, fg=TEXT).pack(side="left")
        tk.Label(header, text="IDS - Windows - v1.0",
                 font=FONT_SMALL, bg=SURFACE, fg=AMBER).pack(side="right",
                                                              anchor="s", pady=6)

        # ── Separador ──────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Conteúdo principal ─────────────────
        body = tk.Frame(self, bg=BG, padx=28, pady=20)
        body.pack(fill="both", expand=True)

        # ┌── Selecionar Pasta ──────────────────
        self._section(body, "1. Selecione a Pasta")

        folder_row = tk.Frame(body, bg=BG)
        folder_row.pack(fill="x", pady=(4, 14))

        self._folder_entry = self._entry(folder_row, self._folder_path,
                                         placeholder="Arraste ou navegue até a pasta…")
        self._folder_entry.pack(side="left", fill="x", expand=True, ipady=8)

        RoundedButton(folder_row, "Procurar", self._pick_folder,
                      width=130, height=40, bg=SURFACE2, hover=BORDER).pack(
                      side="right", padx=(10, 0))

        # ┌── Selecionar Imagem ─────────────────
        self._section(body, "2. Selecione a Imagem")

        img_row = tk.Frame(body, bg=BG)
        img_row.pack(fill="x", pady=(4, 14))

        self._img_entry = self._entry(img_row, self._image_path,
                                      placeholder="PNG, JPG, BMP, ICO, WEBP…")
        self._img_entry.pack(side="left", fill="x", expand=True, ipady=8)

        RoundedButton(img_row, "Procurar", self._pick_image,
                      width=130, height=40, bg=SURFACE2, hover=BORDER).pack(
                      side="right", padx=(10, 0))

        # ┌── Prévia ────────────────────────────
        self._section(body, "3. Prévia")

        preview_wrap = tk.Frame(body, bg=SURFACE, bd=0,
                                highlightbackground=BORDER, highlightthickness=1)
        preview_wrap.pack(fill="x", pady=(4, 18))

        self._canvas = tk.Canvas(preview_wrap, width=644, height=180,
                                  bg=SURFACE, highlightthickness=0)
        self._canvas.pack()
        self._draw_placeholder()

        # ┌── Botões de ação ────────────────────
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x")

        RoundedButton(btn_row, "Aplicar Ícone", self._apply,
                      width=200, height=46, bg=ACCENT, hover=ACCENT_DARK,
                      font=("Segoe UI", 11, "bold")).pack(side="left")

        RoundedButton(btn_row, "Restaurar Padrão", self._reset,
                      width=200, height=46, bg=SURFACE2, hover=BORDER).pack(
                      side="left", padx=(14, 0))

        RoundedButton(btn_row, "Abrir Pasta", self._open_folder,
                      width=155, height=46, bg=SURFACE2, hover=BORDER).pack(
                      side="right")

        # ── Barra de status ────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self.status = StatusBar(self)
        self.status.pack(fill="x")

    # ── helpers de UI ─────────────────────────
    def _section(self, parent, text):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(4, 0))
        tk.Label(f, text=text, font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=ACCENT_GLOW).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                               expand=True, padx=(10, 0), pady=6)

    def _entry(self, parent, var, placeholder=""):
        e = tk.Entry(parent, textvariable=var, font=FONT_MONO,
                     bg=SURFACE2, fg=TEXT, insertbackground=ACCENT,
                     relief="flat", bd=0,
                     highlightbackground=BORDER, highlightthickness=1,
                     highlightcolor=ACCENT, disabledforeground=TEXT_DIM)
        # Placeholder behavior
        if placeholder:
            e.var_ref = var
            if not var.get():
                e.insert(0, placeholder)
                e.config(fg=TEXT_DIM)

            def on_focus_in(ev, _e=e, _ph=placeholder):
                if _e.get() == _ph:
                    _e.delete(0, "end")
                    _e.config(fg=TEXT)

            def on_focus_out(ev, _e=e, _ph=placeholder, _v=var):
                if not _e.get():
                    _e.insert(0, _ph)
                    _e.config(fg=TEXT_DIM)

            e.bind("<FocusIn>", on_focus_in)
            e.bind("<FocusOut>", on_focus_out)
        return e

    def _draw_placeholder(self):
        self._canvas.delete("all")
        self._canvas.create_text(322, 90, text="Nenhuma imagem selecionada ainda…",
                                  fill=TEXT_DIM, font=FONT_BODY)

    # ── seleção de pasta ──────────────────────
    def _pick_folder(self):
        path = filedialog.askdirectory(title="Selecione a pasta")
        if path:
            self._folder_path.set(path)
            self._folder_entry.config(fg=TEXT)
            self.status.info(f"Pasta: {path}")

    # ── seleção de imagem ─────────────────────
    def _pick_image(self):
        types = [("Imagens", "*.png *.jpg *.jpeg *.bmp *.ico *.webp *.gif *.tiff"),
                 ("Todos os arquivos", "*.*")]
        path = filedialog.askopenfilename(title="Selecione a imagem", filetypes=types)
        if path:
            self._image_path.set(path)
            self._img_entry.config(fg=TEXT)
            self._load_preview(path)

    # ── preview ───────────────────────────────
    def _load_preview(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            # Fundo checkered para mostrar transparência
            checker = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sq = 16
            draw = ImageDraw.Draw(checker)
            for y in range(0, img.height, sq):
                for x in range(0, img.width, sq):
                    c = "#2a2a3a" if (x // sq + y // sq) % 2 == 0 else "#1e1e2e"
                    draw.rectangle([x, y, x+sq-1, y+sq-1], fill=c)
            checker.paste(img, mask=img)

            # Redimensiona para caber no canvas (180px alto)
            max_w, max_h = 640, 176
            ratio = min(max_w / checker.width, max_h / checker.height)
            new_size = (int(checker.width * ratio), int(checker.height * ratio))
            thumb = checker.resize(new_size, Image.LANCZOS)

            self._preview_img = ImageTk.PhotoImage(thumb)
            self._canvas.delete("all")
            cx = 322
            cy = 90
            self._canvas.create_image(cx, cy, anchor="center",
                                       image=self._preview_img)
            self.status.info(f"Imagem: {Path(path).name} "
                             f"({img.width}×{img.height}px)")
        except Exception as ex:
            self.status.err(f"Erro ao carregar imagem: {ex}")
            self._draw_placeholder()

    # ── aplicar ícone ─────────────────────────
    def _apply(self):
        folder = self._folder_path.get().strip()
        image  = self._image_path.get().strip()

        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Atenção", "Selecione uma pasta válida primeiro.")
            return
        if not image or not os.path.isfile(image):
            messagebox.showwarning("Atenção", "Selecione uma imagem válida primeiro.")
            return

        self.status.info("Convertendo e aplicando ícone…")
        self.update_idletasks()

        def worker():
            try:
                ico_path = str(self._ico_tmp)
                if Path(image).suffix.lower() == ".ico":
                    ico_path = image
                else:
                    image_to_ico(image, ico_path)
                msg = set_folder_icon(folder, ico_path)
                self.after(0, lambda: self.status.ok(msg))
                self.after(0, lambda: messagebox.showinfo("Sucesso!", msg))
            except Exception as ex:
                self.after(0, lambda: self.status.err(f"Erro: {ex}"))
                self.after(0, lambda: messagebox.showerror("Erro", str(ex)))

        threading.Thread(target=worker, daemon=True).start()

    # ── restaurar ─────────────────────────────
    def _reset(self):
        folder = self._folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Atenção", "Selecione uma pasta válida primeiro.")
            return
        try:
            msg = reset_folder_icon(folder)
            self.status.ok(msg)
            messagebox.showinfo("Restaurado", msg)
        except Exception as ex:
            self.status.err(f"Erro: {ex}")
            messagebox.showerror("Erro", str(ex))

    # ── abrir pasta no Explorer ───────────────
    def _open_folder(self):
        folder = self._folder_path.get().strip()
        if folder and os.path.isdir(folder):
            os.startfile(folder)
        else:
            messagebox.showwarning("Atenção", "Nenhuma pasta selecionada.")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────


if __name__ == "__main__":
    app = FolderIconChanger()
    app.mainloop()
