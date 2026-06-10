1|"""
2|Folder Icon Changer - Aplicação para alterar o ícone de pastas no Windows
3|Requer: pip install pillow
4|"""
5|
6|import os
7|import sys
8|import ctypes
9|import shutil
10|import threading
import json
11|import subprocess
12|import tkinter as tk
13|from tkinter import filedialog, messagebox
14|from pathlib import Path
15|from tkinterdnd2 import TkinterDnD, DND_FILES
16|
17|try:
18|    from PIL import Image, ImageTk, ImageDraw, ImageFilter
19|except ImportError:
20|    import subprocess, sys
21|    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
22|    from PIL import Image, ImageTk, ImageDraw, ImageFilter
23|
24|
25|# ─────────────────────────────────────────────
26|#  CONSTANTES DE COR / TEMA ESCURO
27|# ─────────────────────────────────────────────
28|BG          = "#0b1020"
29|SURFACE     = "#121827"
30|SURFACE2    = "#1a2436"
31|ACCENT      = "#14b8a6"
32|ACCENT_DARK = "#0f8f87"
33|ACCENT_GLOW = "#22d3ee"
34|TEXT        = "#f8fafc"
35|TEXT_DIM    = "#94a3b8"
36|SUCCESS     = "#4ade80"
37|DANGER      = "#f87171"
38|BORDER      = "#2f3b52"
39|AMBER       = "#ffb84d"
HISTORY_FILE = Path(os.environ.get("APPDATA", ".") ) / "folder_icon_changer_history.json"
40|
41|FONT_TITLE  = ("Segoe UI", 22, "bold")
42|FONT_BODY   = ("Segoe UI", 11)
43|FONT_SMALL  = ("Segoe UI", 9)
44|FONT_MONO   = ("Consolas", 10)
45|
46|
47|# ─────────────────────────────────────────────
48|#  LÓGICA PRINCIPAL: ALTERAR ÍCONE NO WINDOWS
49|# ─────────────────────────────────────────────
50|
51|def image_to_ico(src_path: str, dst_ico: str):
52|    """Converte qualquer imagem para .ico com múltiplos tamanhos."""
53|    img = Image.open(src_path).convert("RGBA")
54|    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
55|    icons = []
56|    for s in sizes:
57|        resized = img.resize(s, Image.LANCZOS)
58|        icons.append(resized)
59|    icons[0].save(dst_ico, format="ICO", sizes=[i.size for i in icons],
60|                  append_images=icons[1:])
61|
62|
63|def set_folder_icon(folder_path: str, ico_path: str) -> str:
64|    """
65|    Define o ícone de uma pasta via desktop.ini.
66|    Retorna uma mensagem de status.
67|    """
68|    folder = Path(folder_path)
69|    if not folder.is_dir():
70|        raise ValueError("Caminho selecionado não é uma pasta válida.")
71|
72|    # Copia o .ico para dentro da pasta com nome fixo
73|    dst_ico = folder / "folder_icon.ico"
74|    shutil.copy2(ico_path, dst_ico)
75|
76|    # Cria / sobrescreve desktop.ini
77|    ini_path = folder / "desktop.ini"
78|    ini_content = (
79|        "[.ShellClassInfo]\n"
80|        f"IconResource=folder_icon.ico,0\n"
81|        "[ViewState]\n"
82|        "Mode=\nVid=\nFolderType=Generic\n"
83|    )
84|    ini_path.write_text(ini_content, encoding="utf-8")
85|
86|    # Atributos necessários
87|    FILE_ATTRIBUTE_HIDDEN = 0x02
88|    FILE_ATTRIBUTE_SYSTEM = 0x04
89|    FILE_ATTRIBUTE_READONLY = 0x01
90|
91|    ctypes.windll.kernel32.SetFileAttributesW(str(ini_path),
92|        FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
93|    ctypes.windll.kernel32.SetFileAttributesW(str(dst_ico),
94|        FILE_ATTRIBUTE_HIDDEN)
95|    ctypes.windll.kernel32.SetFileAttributesW(str(folder),
96|        FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_SYSTEM)
97|
98|    # Notifica o Explorer para atualizar ícones
99|    SHCNE_UPDATEDIR = 0x00001000
100|    SHCNF_PATHW     = 0x0005
101|    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW,
102|                                         str(folder), None)
103|    return f"Ícone aplicado com sucesso em '{folder.name}'!"
104|
105|
106|def reset_folder_icon(folder_path: str) -> str:
107|    """Remove o ícone personalizado e restaura o padrão."""
108|    folder = Path(folder_path)
109|    for f in ["desktop.ini", "folder_icon.ico"]:
110|        target = folder / f
111|        if target.exists():
112|            ctypes.windll.kernel32.SetFileAttributesW(str(target), 0x80)  # NORMAL
113|            target.unlink()
114|    ctypes.windll.kernel32.SetFileAttributesW(str(folder), 0x10)  # DIRECTORY
115|    SHCNE_UPDATEDIR = 0x00001000
116|    SHCNF_PATHW     = 0x0005
117|    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW,
118|                                         str(folder), None)
119|    return f"Ícone de '{folder.name}' restaurado para o padrão!"
120|
121|
122|# ─────────────────────────────────────────────
123|#  WIDGETS PERSONALIZADOS
124|# ─────────────────────────────────────────────
125|
126|class RoundedButton(tk.Canvas):
127|    def __init__(self, parent, text, command=None, width=180, height=44,
128|                 bg=ACCENT, hover=ACCENT_DARK, fg=TEXT, radius=12,
129|                 font=FONT_BODY, **kwargs):
130|        super().__init__(parent, width=width, height=height,
131|                         background=parent["bg"], highlightthickness=0,
132|                         bd=0, **kwargs)
133|        self._bg = bg
134|        self._hover = hover
135|        self._fg = fg
136|        self._text = text
137|        self._cmd = command
138|        self._r = radius
139|        self._btn_w = width
140|        self._btn_h = height
141|        self._font = font
142|        self._draw(bg)
143|        self.bind("<Enter>", lambda e: self._draw(hover))
144|        self.bind("<Leave>", lambda e: self._draw(bg))
145|        self.bind("<Button-1>", lambda e: self._click())
146|        self.bind("<ButtonRelease-1>", lambda e: self._draw(hover))
147|
148|    def _draw(self, color):
149|        self.delete("all")
150|        r = self._r
151|        w, h = self._btn_w, self._btn_h
152|        self.create_arc(0,     0,     2*r, 2*r, start=90,  extent=90,  fill=color, outline=color)
153|        self.create_arc(w-2*r, 0,     w,   2*r, start=0,   extent=90,  fill=color, outline=color)
154|        self.create_arc(0,     h-2*r, 2*r, h,   start=180, extent=90,  fill=color, outline=color)
155|        self.create_arc(w-2*r, h-2*r, w,   h,   start=270, extent=90,  fill=color, outline=color)
156|        self.create_rectangle(r, 0, w-r, h, fill=color, outline=color)
157|        self.create_rectangle(0, r, w, h-r, fill=color, outline=color)
158|        self.create_text(w//2, h//2, text=self._text, fill=self._fg,
159|                         font=self._font)
160|
161|    def _click(self):
162|        self._draw(ACCENT_GLOW)
163|        if self._cmd:
164|            self.after(80, self._cmd)
165|
166|    def configure(self, **kw):
167|        if "text" in kw:
168|            self._text = kw.pop("text")
169|            self._draw(self._bg)
170|        super().configure(**kw)
171|
172|
173|class StatusBar(tk.Frame):
174|    def __init__(self, parent, **kwargs):
175|        super().__init__(parent, bg=SURFACE, **kwargs)
176|        self._dot = tk.Label(self, text="●", bg=SURFACE, fg=TEXT_DIM,
177|                             font=("Segoe UI", 12))
178|        self._dot.pack(side="left", padx=(12, 6), pady=6)
179|        self._lbl = tk.Label(self, text="Pronto.", bg=SURFACE, fg=TEXT_DIM,
180|                             font=FONT_SMALL, anchor="w")
181|        self._lbl.pack(side="left", fill="x", expand=True, pady=6)
182|
183|    def set(self, msg, color=TEXT_DIM):
184|        self._lbl.config(text=msg, fg=color)
185|        self._dot.config(fg=color)
186|
187|    def ok(self, msg):   self.set(msg, SUCCESS)
188|    def err(self, msg):  self.set(msg, DANGER)
189|    def info(self, msg): self.set(msg, ACCENT_GLOW)
190|
191|
192|# ─────────────────────────────────────────────
193|#  JANELA PRINCIPAL
194|# ─────────────────────────────────────────────
195|
196|class FolderIconChanger(TkinterDnD.Tk):
197|    def __init__(self):
198|        super().__init__()
199|
200|        self.title("Folder Icon Changer - IDS")
201|        self.configure(bg=BG)
202|        self.resizable(False, False)
203|        self._set_window_icon()
204|        self._center(700, 600)
205|
206|        # Estado
207|        self._folder_path = tk.StringVar()
208|        self._image_path  = tk.StringVar()
209|        self._preview_img = None   # referência para evitar GC
210|        self._ico_tmp     = Path(os.environ.get("TEMP", ".")) / "_fic_tmp.ico"
211|
212|        self._build_ui()
        self._load_history()
213|
214|    def _set_window_icon(self):
215|        """Usa o ícone do projeto na janela e na barra de tarefas."""
216|        icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "folder_icon.ico"
217|        if icon_path.exists():
218|            try:
219|                self.iconbitmap(str(icon_path))
220|            except tk.TclError:
221|                pass
222|
223|    # ── posicionamento central ─────────────────
224|    def _center(self, w, h):
225|        sw = self.winfo_screenwidth()
226|        sh = self.winfo_screenheight()
227|        x = (sw - w) // 2
228|        y = (sh - h) // 2
229|        self.geometry(f"{w}x{h}+{x}+{y}")
230|
231|    # ── construção da UI ───────────────────────
232|    def _build_ui(self):
233|        # ── Cabeçalho ──────────────────────────
234|        header = tk.Frame(self, bg=SURFACE, padx=24, pady=20)
235|        header.pack(fill="x")
236|
237|        tk.Label(header, text="Folder Icon Changer",
238|                 font=FONT_TITLE, bg=SURFACE, fg=TEXT).pack(side="left")
239|        tk.Label(header, text="IDS - Windows - v1.0",
240|                 font=FONT_SMALL, bg=SURFACE, fg=AMBER).pack(side="right",
241|                                                              anchor="s", pady=6)
242|
243|        # ── Separador ──────────────────────────
244|        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
245|
246|        # ── Conteúdo principal ─────────────────
247|        body = tk.Frame(self, bg=BG, padx=28, pady=20)
248|        body.pack(fill="both", expand=True)
249|
250|        # ┌── Selecionar Pasta ──────────────────
251|        self._section(body, "1. Selecione a Pasta")
252|
253|        folder_row = tk.Frame(body, bg=BG)
254|        folder_row.pack(fill="x", pady=(4, 14))
255|
256|        self._folder_entry = self._entry(folder_row, self._folder_path,
257|                                         placeholder="Arraste ou navegue até a pasta…")
258|        self._folder_entry.pack(side="left", fill="x", expand=True, ipady=8)
259|        
260|        self._folder_entry.drop_target_register(DND_FILES)
261|        self._folder_entry.dnd_bind('<<Drop>>', self._on_folder_drop)
262|
263|        RoundedButton(folder_row, "Procurar", self._pick_folder,
264|                      width=130, height=40, bg=SURFACE2, hover=BORDER).pack(
265|                      side="right", padx=(10, 0))
266|
267|        # ┌── Selecionar Imagem ─────────────────
268|        self._section(body, "2. Selecione a Imagem")
269|
270|        img_row = tk.Frame(body, bg=BG)
271|        img_row.pack(fill="x", pady=(4, 14))
272|
273|        self._img_entry = self._entry(img_row, self._image_path,
274|                                      placeholder="PNG, JPG, BMP, ICO, WEBP…")
275|        self._img_entry.pack(side="left", fill="x", expand=True, ipady=8)
276|        
277|        self._img_entry.drop_target_register(DND_FILES)
278|        self._img_entry.dnd_bind('<<Drop>>', self._on_image_drop)
279|
280|        # BOTÃO GALERIA
281|        RoundedButton(img_row, "Galeria", self._open_gallery,
282|                      width=130, height=40, bg=SURFACE2, hover=BORDER).pack(
283|                      side="right", padx=(10, 0))
284|
285|        RoundedButton(img_row, "Procurar", self._pick_image,
286|                      width=130, height=40, bg=SURFACE2, hover=BORDER).pack(
287|                      side="right", padx=(10, 0))
288|
289|        # ┌── Prévia ────────────────────────────
290|        self._section(body, "3. Prévia")
291|
292|        preview_wrap = tk.Frame(body, bg=SURFACE, bd=0,
293|                                highlightbackground=BORDER, highlightthickness=1)
294|        preview_wrap.pack(fill="x", pady=(4, 18))
295|
296|        self._canvas = tk.Canvas(preview_wrap, width=644, height=180,
297|                                  bg=SURFACE, highlightthickness=0)
298|        self._canvas.pack()
299|        self._draw_placeholder()
300|
301|        # ┌── Botões de ação ────────────────────
302|        btn_row = tk.Frame(body, bg=BG)
303|        btn_row.pack(fill="x")
304|
305|        RoundedButton(btn_row, "Aplicar Ícone", self._apply,
306|                      width=200, height=46, bg=ACCENT, hover=ACCENT_DARK,
307|                      font=("Segoe UI", 11, "bold")).pack(side="left")
308|
309|        RoundedButton(btn_row, "Restaurar Padrão", self._reset,
310|                      width=200, height=46, bg=SURFACE2, hover=BORDER).pack(
311|                      side="left", padx=(14, 0))
312|
313|        RoundedButton(btn_row, "Abrir Pasta", self._open_folder,
314|                      width=155, height=46, bg=SURFACE2, hover=BORDER).pack(
315|                      side="right")
316|
317|        # ── Barra de status ────────────────────
318|        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
319|        self.status = StatusBar(self)
320|        self.status.pack(fill="x")
321|
322|    # ── helpers de UI ─────────────────────────
323|    def _section(self, parent, text):
324|        f = tk.Frame(parent, bg=BG)
325|        f.pack(fill="x", pady=(4, 0))
326|        tk.Label(f, text=text, font=("Segoe UI", 10, "bold"),
327|                 bg=BG, fg=ACCENT_GLOW).pack(side="left")
328|        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
329|                                               expand=True, padx=(10, 0), pady=6)
330|
331|    def _entry(self, parent, var, placeholder=""):
332|        e = tk.Entry(parent, textvariable=var, font=FONT_MONO,
333|                     bg=SURFACE2, fg=TEXT, insertbackground=ACCENT,
334|                     relief="flat", bd=0,
335|                     highlightbackground=BORDER, highlightthickness=1,
336|                     highlightcolor=ACCENT, disabledforeground=TEXT_DIM)
337|        # Placeholder behavior
338|        if placeholder:
339|            e.var_ref = var
340|            if not var.get():
341|                e.insert(0, placeholder)
342|                e.config(fg=TEXT_DIM)
343|
344|            def on_focus_in(ev, _e=e, _ph=placeholder):
345|                if _e.get() == _ph:
346|                    _e.delete(0, "end")
347|                    _e.config(fg=TEXT)
348|
349|            def on_focus_out(ev, _e=e, _ph=placeholder, _v=var):
350|                if not _e.get():
351|                    _e.insert(0, _ph)
352|                    _e.config(fg=TEXT_DIM)
353|
354|            e.bind("<FocusIn>", on_focus_in)
355|            e.bind("<FocusOut>", on_focus_out)
356|        return e
357|
358|    def _draw_placeholder(self):
359|        self._canvas.delete("all")
360|        self._canvas.create_text(322, 90, text="Nenhuma imagem selecionada ainda…",
361|                                  fill=TEXT_DIM, font=FONT_BODY)
362|
363|    # ── seleção de pasta ──────────────────────
364|    def _pick_folder(self):
365|        path = filedialog.askdirectory(title="Selecione a pasta")
366|        if path:
367|            self._folder_path.set(path)
368|            self._folder_entry.config(fg=TEXT)
369|            self.status.info(f"Pasta: {path}")
370|
371|    def _on_folder_drop(self, event):
372|        path = event.data.strip('{}') # Remove braces if path has spaces
373|        if os.path.isdir(path):
374|            self._folder_path.set(path)
375|            self._folder_entry.config(fg=TEXT)
376|            self.status.info(f"Pasta arrastada: {path}")
377|        else:
378|            self.status.err("O item arrastado não é uma pasta válida.")
379|
380|    # ── seleção de imagem ─────────────────────
381|    def _pick_image(self):
382|        types = [("Imagens", "*.png *.jpg *.jpeg *.bmp *.ico *.webp *.gif *.tiff"),
383|                 ("Todos os arquivos", "*.*")]
384|        path = filedialog.askopenfilename(title="Selecione a imagem", filetypes=types)
385|        if path:
386|            self._image_path.set(path)
387|            self._img_entry.config(fg=TEXT)
388|            self._load_preview(path)
389|
390|    def _on_image_drop(self, event):
391|        path = event.data.strip('{}')
392|        if os.path.isfile(path):
393|            self._image_path.set(path)
394|            self._img_entry.config(fg=TEXT)
395|            self._load_preview(path)
396|        else:
397|            self.status.err("O item arrastado não é um arquivo de imagem válida.")
398|
399|    # ── preview ───────────────────────────────
400|    def _load_preview(self, path):
401|        try:
402|            img = Image.open(path).convert("RGBA")
403|            # Fundo checkered para mostrar transparência
404|            checker = Image.new("RGBA", img.size, (0, 0, 0, 0))
405|            sq = 16
406|            draw = ImageDraw.Draw(checker)
407|            for y in range(0, img.height, sq):
408|                for x in range(0, img.width, sq):
409|                    c = "#2a2a3a" if (x // sq + y // sq) % 2 == 0 else "#1e1e2e"
410|                    draw.rectangle([x, y, x+sq-1, y+sq-1], fill=c)
411|            checker.paste(img, mask=img)
412|
413|            # Redimensiona para caber no canvas (180px alto)
414|            max_w, max_h = 640, 176
415|            ratio = min(max_w / checker.width, max_h / checker.height)
416|            new_size = (int(checker.width * ratio), int(checker.height * ratio))
417|            thumb = checker.resize(new_size, Image.LANCZOS)
418|
419|            self._preview_img = ImageTk.PhotoImage(thumb)
420|            self._canvas.delete("all")
421|            cx = 322
422|            cy = 90
423|            self._canvas.create_image(cx, cy, anchor="center",
424|                                       image=self._preview_img)
425|            self.status.info(f"Imagem: {Path(path).name} "
426|                             f"({img.width}×{img.height}px)")
427|        except Exception as ex:
428|            self.status.err(f"Erro ao carregar imagem: {ex}")
429|            self._draw_placeholder()
430|
431|    # ── aplicar ícone ─────────────────────────
432|    def _apply(self):
433|        folder = self._folder_path.get().strip()
434|        image  = self._image_path.get().strip()
435|
436|        if not folder or not os.path.isdir(folder):
437|            messagebox.showwarning("Atenção", "Selecione uma pasta válida primeiro.")
438|            return
439|        if not image or not os.path.isfile(image):
440|            messagebox.showwarning("Atenção", "Selecione uma imagem válida primeiro.")
441|            return
442|
443|        self.status.info("Convertendo e aplicando ícone…")
444|        self.update_idletasks()
445|
446|        def worker():
447|            try:
448|                ico_path = str(self._ico_tmp)
449|                if Path(image).suffix.lower() == ".ico":
450|                    ico_path = image
451|                else:
452|                    image_to_ico(image, ico_path)
453|                msg = set_folder_icon(folder, ico_path)
454|                self.after(0, lambda: self.status.info(msg))
455|                self.after(0, lambda: messagebox.showinfo("Sucesso!", msg))
                self._save_history()
456|            except Exception as ex:
457|                self.after(0, lambda: self.status.err(f"Erro: {ex}"))
458|                self.after(0, lambda: messagebox.showerror("Erro", str(ex)) )
459|
460|        threading.Thread(target=worker, daemon=True).start()
461|
462|    # ── restaurar ─────────────────────────────
463|    def _reset(self):
464|        folder = self._folder_path.get().strip()
465|        if not folder or not os.path.isdir(folder):
466|            messagebox.showwarning("Atenção", "Selecione uma pasta válida primeiro.")
467|            return
468|        try:
469|            msg = reset_folder_icon(folder)
470|            self.status.ok(msg)
471|            messagebox.showinfo("Restaurado", msg)
            self._save_history()
472|        except Exception as ex:
473|            self.status.err(f"Erro: {ex}")
474|            messagebox.showerror("Erro", str(ex))
475|
476|    # ── abrir pasta no Explorer ───────────────
477|    def _open_folder(self):
478|        folder = self._folder_path.get().strip()
479|        if folder and os.path.isdir(folder):
480|            os.startfile(folder)
481|        else:
482|            messagebox.showwarning("Atenção", "Nenhuma pasta selecionada.")
483|
484|    # ── galeria de ícones ─────────────────────
485|    def _open_gallery(self):
486|        gallery_win = tk.Toplevel(self)
487|        gallery_win.title("Galeria de Ícones")
488|        gallery_win.configure(bg=BG)
489|        gallery_win.geometry("500x400")
490|        gallery_win.resizable(False, False)
491|
492|        container = tk.Frame(gallery_win, bg=BG, padx=20, pady=20)
493|        container.pack(fill="both", expand=True)
494|
495|        tk.Label(container, text="Selecione um ícone da coleção", 
496|                 font=FONT_BODY, bg=BG, fg=TEXT).pack(pady=(0, 20))
497|
498|        icons_dir = Path(__file__).parent / "branding" / "icon-options"
499|        
500|        if not icons_dir.exists():
501|