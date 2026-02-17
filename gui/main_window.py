# gui/main_window.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from core.sul_engine import SulArchiver

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SulApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SUL_ARC | Professional Archiver")
        self.geometry("700x500")
        self.resizable(False, False)

        # Сетка
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # === HEADER ===
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.logo_label = ctk.CTkLabel(self.header_frame, text="SUL_ARC", font=("Roboto Medium", 32, "bold"), text_color="#3B8ED0")
        self.logo_label.pack(side="left")
        
        self.ver_label = ctk.CTkLabel(self.header_frame, text="v1.0 Pro", font=("Roboto", 12), text_color="gray")
        self.ver_label.pack(side="left", padx=10, pady=(15, 0))

        # === CONTROLS ===
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_create = ctk.CTkButton(self.controls_frame, text="СОЗДАТЬ АРХИВ (SUL)", command=self.on_create, height=40, font=("Roboto", 14, "bold"))
        self.btn_create.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        self.btn_extract = ctk.CTkButton(self.controls_frame, text="РАСПАКОВАТЬ .SUL", command=self.on_extract, height=40, fg_color="#E04F5F", hover_color="#C03F4F", font=("Roboto", 14, "bold"))
        self.btn_extract.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        # === LOGS ===
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.log_box.insert("0.0", ">>> SYSTEM READY. WAITING FOR COMMANDS...\n")
        self.log_box.configure(state="disabled")

        # === STATUS ===
        self.status_bar = ctk.CTkProgressBar(self)
        self.status_bar.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.status_bar.set(0)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def on_create(self):
        target = filedialog.askdirectory(title="Выберите папку для архивации")
        if not target: return
        
        default_name = f"sul.{os.path.basename(target)}.sul"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".sul",
            initialfile=default_name,
            filetypes=[("SUL Archive", "*.sul")],
            title="Сохранить архив как..."
        )
        
        if not save_path: return
        
        # Строгая проверка имени (на всякий случай дублируем в GUI)
        filename = os.path.basename(save_path)
        if not (filename.startswith("sul.") and filename.endswith(".sul")):
            messagebox.showerror("Ошибка имени", "Имя архива должно быть вида: sul.НАЗВАНИЕ.sul")
            return

        self.run_async(self.process_create, target, save_path)

    def on_extract(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("SUL Archive", "*.sul")],
            title="Выберите SUL архив"
        )
        if not file_path: return

        # Проверка расширения (защита от дурака)
        if not file_path.endswith(".sul") or "sul." not in os.path.basename(file_path):
            messagebox.showerror("Access Denied", "Это не SUL архив! Доступ запрещен.")
            return

        dest_dir = filedialog.askdirectory(title="Куда распаковать?")
        if not dest_dir: return

        self.run_async(self.process_extract, file_path, dest_dir)

    def run_async(self, func, *args):
        self.status_bar.start()
        thread = threading.Thread(target=func, args=args)
        thread.start()

    def process_create(self, src, dest):
        archiver = SulArchiver(log_callback=self.log)
        try:
            archiver.create_archive(src, dest)
            messagebox.showinfo("Успех", "Архив SUL успешно создан!")
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.status_bar.stop()
            self.status_bar.set(1)

    def process_extract(self, src, dest):
        archiver = SulArchiver(log_callback=self.log)
        try:
            archiver.extract_archive(src, dest)
            messagebox.showinfo("Успех", "Данные успешно восстановлены!")
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.status_bar.stop()
            self.status_bar.set(1)