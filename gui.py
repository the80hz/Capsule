import os
import threading
import schedule
import time
import logging

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

import pystray
from PIL import Image

from database import create_connection, create_table
from backup_manager import backup_files


def start_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


class TextHandler(logging.Handler):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        self.text.configure(state='normal')
        self.text.insert(tk.END, msg + '\n')
        self.text.configure(state='disabled')
        self.text.yview(tk.END)


def setup_gui():
    """ Настройка графического интерфейса пользователя. """
    window = tk.Tk()
    window.title("Backup Manager")

    window.resizable(False, False)

    # Установка иконки
    window.iconbitmap('icon.ico')

    # Настройка логгера
    log_text = scrolledtext.ScrolledText(window, height=10, state='disabled')
    text_handler = TextHandler(log_text)
    logging.basicConfig(filename='backup_log.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger().addHandler(text_handler)

    def select_source_path():
        path = filedialog.askdirectory()
        source_path_entry.delete(0, tk.END)
        source_path_entry.insert(0, path)
    tk.Label(window, text="Источник:").grid(row=0, column=0)
    source_path_entry = tk.Entry(window, width=50)
    source_path_entry.grid(row=0, column=1)
    tk.Button(window, text="Выбрать", command=select_source_path).grid(row=0, column=2)

    def select_destination_path():
        path = filedialog.askdirectory()
        destination_path_entry.delete(0, tk.END)
        destination_path_entry.insert(0, path)
    tk.Label(window, text="Назначение:").grid(row=1, column=0)
    destination_path_entry = tk.Entry(window, width=50)
    destination_path_entry.grid(row=1, column=1)
    tk.Button(window, text="Выбрать", command=select_destination_path).grid(row=1, column=2)

    tk.Label(window, text="Интервал (минуты):").grid(row=2, column=0)
    interval_entry = tk.Entry(window, width=50)
    interval_entry.grid(row=2, column=1)

    def create_backup_now():
        try:
            source = source_path_entry.get()
            destination = destination_path_entry.get()
            db_path = os.path.join(destination, 'backup_db.sqlite')

            with create_connection(db_path) as db_conn:
                create_table(db_conn)
                backup_files(source, destination, db_path)

        except Exception as e:
            logging.error(f'"Ошибка", {str(e)}')
            messagebox.showerror("Ошибка", str(e))
    tk.Button(window, text="Создать Копию", command=create_backup_now).grid(row=3, column=1)

    def set_schedule():
        try:
            source = source_path_entry.get()
            destination = destination_path_entry.get()
            interval = int(interval_entry.get())

            db_path = os.path.join(destination, 'backup_db.sqlite')
            with create_connection(db_path) as db_conn:
                create_table(db_conn)
                backup_files(source, destination, db_path)

                schedule.every(interval).minutes.do(backup_files, source, destination, db_path)

                schedule_thread = threading.Thread(target=start_schedule)
                schedule_thread.start()
        except ValueError:
            messagebox.showerror("Ошибка", "Интервал должен быть числом.")
        except Exception as e:
            logging.error(f'"Ошибка", {str(e)}')
            messagebox.showerror("Ошибка", str(e))
        logging.info("Расписание было установлено")

    def delete_schedule():
        logging.info("Расписание было удалено")
        schedule.clear()
        messagebox.showinfo("Информация", "Расписание удалено.")

    def create_or_delete_schedule():
        if schedule_button.cget("text") == "Создать Расписание":
            set_schedule()
            schedule_button.config(text="Удалить Расписание")
        else:
            delete_schedule()
            schedule_button.config(text="Создать Расписание")

    schedule_button = tk.Button(window, text="Создать Расписание", command=create_or_delete_schedule)
    schedule_button.grid(row=3, column=0)

    def toggle_log_window():
        if log_text.winfo_ismapped():
            log_text.grid_remove()
        else:
            log_text.grid(row=4, column=0, columnspan=3, sticky="ew")

    tk.Button(window, text="Показать Лог", command=toggle_log_window).grid(row=3, column=2)

    def exit_application(icon):
        icon.stop()
        delete_schedule()
        window.destroy()

    def on_clicked(icon):
        logging.info("Icon clicked, stopping icon and showing window.")
        icon.stop()
        window.deiconify()  # Показать окно

    def hide_window():
        logging.info("Hiding window and starting tray icon.")

        window.withdraw()

        icon_image = Image.open('icon.ico')
        menu = (
            pystray.MenuItem('Восстановить', on_clicked),
            pystray.MenuItem('Старт Резервной Копии', create_backup_now),
            pystray.MenuItem('Выход', exit_application),
        )
        icon = pystray.Icon("name", icon_image, "title", menu)

        icon.left_click_action = on_clicked
        icon.run()

    window.protocol("WM_DELETE_WINDOW", hide_window)

    window.mainloop()


if __name__ == "__main__":
    setup_gui()
