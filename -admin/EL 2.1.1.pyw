# EL 2.2.1 - Shinlinst EternalLock (GUI version, Python)
# Features: Lock/unlock files, password stored as SHA-256 + path MD5
# UI: customtkinter (Windows 11 Fluent style, rounded buttons/entries)
# Multi-threaded: crypto & file ops run in background, UI stays responsive
import os
import sys
import hashlib
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from queue import Queue, Empty

try:
    import customtkinter as ctk
except ImportError:
    print("customtkinter not installed. Run: pip install customtkinter")
    sys.exit(1)

# ---------- Config ----------
BASE_DIR = r"C:\Shinlinst\EternalLock"
CORNER_RADIUS = 6
SECTION_GAP   = 14
CARD_INNER    = 14

# Fonts (ApC style: zh=STFangsong bold, en=Comic Sans MS)
FONT_CN_TITLE = ("STFangsong", 22, "bold")
FONT_CN_LABEL = ("STFangsong", 14, "bold")
FONT_CN_BTN   = ("STFangsong", 14, "bold")
FONT_CN_ENTRY = ("STFangsong", 13, "bold")
FONT_CN_LOG   = ("STFangsong", 13, "bold")

FONT_EN_TITLE = ("Comic Sans MS", 22, "bold")
FONT_EN_LABEL = ("Comic Sans MS", 14)
FONT_EN_BTN   = ("Comic Sans MS", 14)
FONT_EN_ENTRY = ("Comic Sans MS", 13)
FONT_EN_LOG   = ("Comic Sans MS", 13)

# ---------- i18n ----------
TEXTS = {
    "zh": {
        "title":        "Shinlinst EternalLock",
        "file_label":   "文件路径：",
        "browse":       "浏览……",
        "pass_label":   "密码：",
        "lock":         "锁定文件",
        "unlock":       "解锁文件",
        "log_label":    "操作日志：",
        "lang_label":   "语言",
        "tip":          "提示",
        "error":        "错误",
        "select_first": "请先选择文件。",
        "not_found":    "文件不存在，请重新选择。",
        "wrong_pass":   "密码错误，无法解锁。",
        "locked_ok":    "文件锁定成功",
        "unlocked_ok":  "文件解锁成功",
        "op_failed":    "操作失败：",
        "dlg_select":   "选择一个文件",
        "LOG_L_SAVE":   "[锁定] 密码已保存",
        "LOG_L_ATTR":   "[锁定] 正在设置属性…",
        "LOG_L_ICAL":   "[锁定] 正在设置权限…",
        "LOG_L_DONE":   "[锁定] 文件已锁定：",
        "LOG_L_PROC":   "[锁定] 正在处理…",
        "LOG_U_CORRECT":"[解锁] 密码正确",
        "LOG_U_WRONG":  "[解锁] 密码错误",
        "LOG_U_NOPASS": "[解锁] 未检测到密码，直接解锁",
        "LOG_U_ATTR":   "[解锁] 正在还原属性…",
        "LOG_U_ICAL":   "[解锁] 正在还原权限…",
        "LOG_U_DONE":   "[解锁] 文件已解锁：",
        "LOG_U_PROC":   "[解锁] 正在处理…",
    },
    "en": {
        "title":        "Shinlinst EternalLock",
        "file_label":   "File Path:",
        "browse":       "Browse...",
        "pass_label":   "Password:",
        "lock":         "Lock File",
        "unlock":       "Unlock File",
        "log_label":    "Operation Log:",
        "lang_label":   "Language",
        "tip":          "Tip",
        "error":        "Error",
        "select_first": "Please select a file first.",
        "not_found":    "File not found, please reselect.",
        "wrong_pass":   "Wrong password, cannot unlock.",
        "locked_ok":    "File locked successfully",
        "unlocked_ok":  "File unlocked successfully",
        "op_failed":    "Operation failed: ",
        "dlg_select":   "Select a file",
        "LOG_L_SAVE":   "[LOCK] Password saved",
        "LOG_L_ATTR":   "[LOCK] Setting attributes...",
        "LOG_L_ICAL":   "[LOCK] Setting permissions...",
        "LOG_L_DONE":   "[LOCK] File locked: ",
        "LOG_L_PROC":   "[LOCK] Processing...",
        "LOG_U_CORRECT":"[UNLOCK] Password correct",
        "LOG_U_WRONG":  "[UNLOCK] Password wrong",
        "LOG_U_NOPASS": "[UNLOCK] No password detected, unlocking directly",
        "LOG_U_ATTR":   "[UNLOCK] Restoring attributes...",
        "LOG_U_ICAL":   "[UNLOCK] Restoring permissions...",
        "LOG_U_DONE":   "[UNLOCK] File unlocked: ",
        "LOG_U_PROC":   "[UNLOCK] Processing...",
    },
}

# ---------- Crypto ----------
def md5_hex(data: str) -> str:
    return hashlib.md5(data.encode("utf-8")).hexdigest()

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

# ---------- Path helpers ----------
def normalized_path(target_file: str) -> str:
    p = os.path.abspath(target_file)
    if len(p) >= 2 and p[1] == ":":
        p = p[0].upper() + p[1:]
    return p

def password_file_path(target_file: str) -> str:
    norm_utf8 = normalized_path(target_file)
    return os.path.join(BASE_DIR, md5_hex(norm_utf8) + ".txt")

# ---------- Password file I/O ----------
def read_hash(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.find('"sha256"')
        if start == -1:
            return ""
        q1 = content.find('"', start + 8)
        if q1 == -1:
            return ""
        q2 = content.find('"', q1 + 1)
        if q2 == -1:
            return ""
        return content[q1 + 1:q2]
    except Exception:
        return ""

def write_hash(path: str, sha: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"sha256":"' + sha + '"}')

# ---------- Lock / Unlock ----------
def do_lock(target: str, password: str, log: callable, lang: str) -> None:
    T = TEXTS[lang]
    if password:
        sha = sha256_hex(password)
        write_hash(password_file_path(target), sha)
        log(T["LOG_L_SAVE"])

    log(T["LOG_L_ATTR"])
    subprocess.run(["attrib", "+R", "+S", target], check=False, shell=False)
    log(T["LOG_L_ICAL"])
    subprocess.run(["icacls", target, "/deny", "Everyone:(W)"], check=False, shell=False)
    log(T["LOG_L_DONE"] + target)

def do_unlock(target: str, password: str, log: callable, lang: str) -> tuple:
    T = TEXTS[lang]
    pf = password_file_path(target)
    stored = read_hash(pf) if os.path.exists(pf) else None

    if stored is not None:
        if password and sha256_hex(password) == stored:
            log(T["LOG_U_CORRECT"])
        else:
            log(T["LOG_U_WRONG"])
            return False, T["wrong_pass"]
    else:
        log(T["LOG_U_NOPASS"])

    log(T["LOG_U_ATTR"])
    subprocess.run(["attrib", "-R", "-S", target], check=False, shell=False)
    log(T["LOG_U_ICAL"])
    subprocess.run(["icacls", target, "/grant", "Everyone:(W)"], check=False, shell=False)
    log(T["LOG_U_DONE"] + target)
    return True, T["unlocked_ok"]

# ---------- Worker thread ----------
def worker_loop(task_queue: Queue, result_queue: Queue):
    while True:
        try:
            task = task_queue.get(timeout=0.3)
        except Empty:
            continue

        if task is None:
            break

        op, target, password, lang = task

        def log(msg):
            result_queue.put(("LOG", msg))

        if op == "LOCK":
            success = False
            msg = ""
            try:
                do_lock(target, password, log, lang)
                success = True
                msg = TEXTS[lang]["locked_ok"]
            except Exception as e:
                msg = TEXTS[lang]["op_failed"] + str(e)
            result_queue.put(("RESULT", op, success, msg))
        elif op == "UNLOCK":
            success = False
            msg = ""
            try:
                success, msg = do_unlock(target, password, log, lang)
            except Exception as e:
                msg = TEXTS[lang]["op_failed"] + str(e)
            result_queue.put(("RESULT", op, success, msg))

# ---------- GUI ----------
class EternalLockApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._lang = "en"
        self.title("Shinlinst EternalLock")
        self.geometry("652x500")
        self.minsize(520, 430)

        try:
            self.iconbitmap(r"C:\Shinlinst\.icons\EL.ico")
        except Exception:
            pass

        self._busy = False
        self._task_queue = Queue()
        self._result_queue = Queue()
        self._worker = threading.Thread(target=worker_loop,
                                        args=(self._task_queue, self._result_queue),
                                        daemon=True)
        self._worker.start()

        self._build_ui()
        self.after(100, self._poll_queue)

    # ---------- Font helpers ----------
    def _f_title(self):
        return FONT_CN_TITLE if self._lang == "zh" else FONT_EN_TITLE
    def _f_label(self):
        return FONT_CN_LABEL if self._lang == "zh" else FONT_EN_LABEL
    def _f_btn(self):
        return FONT_CN_BTN if self._lang == "zh" else FONT_EN_BTN
    def _f_entry(self):
        return FONT_CN_ENTRY if self._lang == "zh" else FONT_EN_ENTRY
    def _f_log(self):
        return FONT_CN_LOG if self._lang == "zh" else FONT_EN_LOG

    # ---------- UI ----------
    def _build_ui(self):
        T = TEXTS[self._lang]

        # Top bar: title (no language selector - English only)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(14, 0), padx=24)
        self.lbl_title = ctk.CTkLabel(top, text=T["title"], font=self._f_title())
        self.lbl_title.pack(side="left")

        # Button style helper (ApC outlined style with width)
        def _btn(parent, text, width, command, color="white", bg_hover="#E5F1FB",
                 text_color="#000000", border="#E5E5E5"):
            return ctk.CTkButton(
                parent, text=text, width=width, height=32,
                corner_radius=CORNER_RADIUS,
                fg_color=color, hover_color=bg_hover,
                text_color=text_color,
                border_width=1, border_color=border,
                font=self._f_btn(),
                command=command
            )

        # === Input Card (#FAFAFA, ApC style) ===
        input_card = ctk.CTkFrame(self, corner_radius=CORNER_RADIUS, fg_color="#FAFAFA")
        input_card.pack(fill="x", padx=24, pady=(SECTION_GAP, 0))

        inner = ctk.CTkFrame(input_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        # Row 1: File path + Browse
        self.lbl_file = ctk.CTkLabel(inner, text=T["file_label"], width=100, font=self._f_label())
        self.lbl_file.pack(side="left", padx=(0, 8))
        self.var_file = tk.StringVar()
        self.entry_file = ctk.CTkEntry(inner, textvariable=self.var_file,
                                        corner_radius=4, height=32,
                                        fg_color="white", border_color="#E5E5E5",
                                        font=self._f_entry())
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_browse = _btn(inner, T["browse"], 100, self._on_browse)
        self.btn_browse.pack(side="left")

        # Row 2: Password
        row2 = ctk.CTkFrame(input_card, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(4, 0))
        self.lbl_pass = ctk.CTkLabel(row2, text=T["pass_label"], width=100, font=self._f_label())
        self.lbl_pass.pack(side="left", padx=(0, 8))
        self.var_pass = tk.StringVar()
        self.entry_pass = ctk.CTkEntry(row2, textvariable=self.var_pass, show="●",
                                        corner_radius=4, height=32,
                                        fg_color="white", border_color="#E5E5E5",
                                        font=self._f_entry())
        self.entry_pass.pack(side="left", fill="x", expand=True, padx=(0, 8))
        # spacer so password row browse-position matches row1
        ctk.CTkFrame(row2, width=100, height=32, fg_color="transparent").pack(side="left")

        # Row 3: Lock / Unlock buttons (ApC: equal width, packed side-by-side)
        row3 = ctk.CTkFrame(input_card, fg_color="transparent")
        row3.pack(fill="x", padx=14, pady=(12, 4))
        self.btn_lock = _btn(row3, T["lock"], 140, self._on_lock)
        self.btn_lock.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self.btn_unlock = _btn(row3, T["unlock"], 140, self._on_unlock)
        self.btn_unlock.pack(side="left", expand=True, fill="x", padx=(8, 0))

        # === Log Card (ApC style: label outside card, card=#FAFAFA, Edge scrollbar) ===
        self.lbl_log = ctk.CTkLabel(self, text=T["log_label"], anchor="w",
                                      font=self._f_label())
        self.lbl_log.pack(fill="x", padx=24, pady=(SECTION_GAP, 4))

        log_card = ctk.CTkFrame(self, corner_radius=CORNER_RADIUS, fg_color="#FAFAFA")
        log_card.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        log_inner = ctk.CTkFrame(log_card, fg_color="transparent")
        log_inner.pack(fill="both", expand=True, padx=CARD_INNER, pady=CARD_INNER)

        self.text_log = ctk.CTkTextbox(log_inner, corner_radius=4, height=300,
                                       fg_color="white", border_color="#E5E5E5",
                                       font=self._f_log())
        self.text_log.pack(side="left", fill="both", expand=True, padx=(0, 0))

        # Edge-style vertical scrollbar (ApC pattern)
        self.sb_log = ctk.CTkScrollbar(log_inner, orientation="vertical",
                                        command=self.text_log.yview,
                                        corner_radius=8,
                                        height=16,
                                        fg_color="#FAFAFA",
                                        button_color="#BFBFBF",
                                        button_hover_color="#8A8A8A")
        self.sb_log.pack(side="right", fill="y")
        self.text_log.configure(yscrollcommand=self.sb_log.set)

    # ---------- Texts refresh (unused now, English only) ----------
    def _refresh_texts(self):
        T = TEXTS[self._lang]
        self.lbl_title.configure(text=T["title"], font=self._f_title())
        self.lbl_file.configure(text=T["file_label"], font=self._f_label())
        self.lbl_pass.configure(text=T["pass_label"], font=self._f_label())
        self.lbl_log.configure(text=T["log_label"], font=self._f_label())
        self.entry_file.configure(font=self._f_entry())
        self.entry_pass.configure(font=self._f_entry())
        self.text_log.configure(font=self._f_log())
        self.btn_browse.configure(text=T["browse"], font=self._f_btn())
        self.btn_lock.configure(text=T["lock"], font=self._f_btn())
        self.btn_unlock.configure(text=T["unlock"], font=self._f_btn())

    # ---------- Button handlers ----------
    def _on_browse(self):
        T = TEXTS[self._lang]
        path = filedialog.askopenfilename(title=T["dlg_select"])
        if path:
            self.var_file.set(path)

    def _on_lock(self):
        if self._busy:
            return
        T = TEXTS[self._lang]
        target = self.var_file.get().strip()
        password = self.var_pass.get()
        if not target:
            messagebox.showwarning(T["tip"], T["select_first"])
            return
        if not os.path.exists(target):
            messagebox.showwarning(T["tip"], T["not_found"])
            return
        self._set_busy(True)
        self._append_log(T["LOG_L_PROC"])
        self._task_queue.put(("LOCK", target, password, self._lang))

    def _on_unlock(self):
        if self._busy:
            return
        T = TEXTS[self._lang]
        target = self.var_file.get().strip()
        password = self.var_pass.get()
        if not target:
            messagebox.showwarning(T["tip"], T["select_first"])
            return
        if not os.path.exists(target):
            messagebox.showwarning(T["tip"], T["not_found"])
            return
        self._set_busy(True)
        self._append_log(T["LOG_U_PROC"])
        self._task_queue.put(("UNLOCK", target, password, self._lang))

    # ---------- Helpers ----------
    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.btn_lock.configure(state=state)
        self.btn_unlock.configure(state=state)

    def _append_log(self, msg: str):
        self.text_log.insert("end", msg + "\n")
        self.text_log.see("end")

    def _poll_queue(self):
        try:
            while True:
                item = self._result_queue.get_nowait()
                tag = item[0]
                if tag == "LOG":
                    self._append_log(item[1])
                elif tag == "RESULT":
                    _, op, success, msg = item
                    self._set_busy(False)
                    if success:
                        self._append_log(msg)
                        self.var_pass.set("")
                    else:
                        self._append_log(msg)
                        T = TEXTS[self._lang]
                        messagebox.showerror(T["error"], msg)
        except Empty:
            pass
        self.after(100, self._poll_queue)

    def destroy(self):
        self._task_queue.put(None)
        super().destroy()


if __name__ == "__main__":
    app = EternalLockApp()
    app.mainloop()
