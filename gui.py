import os
import threading
import schedule
import time
import logging

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk

import pystray
from PIL import Image

from database import create_connection, create_table, add_excluded_directory, get_excluded_directories, \
    remove_excluded_directory
from backup_manager import backup_files, restore_backup


def scan_backups(backup_dir):
    """
    Сканирует заданную директорию и возвращает список директорий резервных копий.
    """
    return [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]


def update_backup_options(backup_combobox, backup_dir):
    """
    Сканирует заданную директорию и обновляет выпадающий список с резервными копиями.
    """
    backup_options = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
    backup_combobox['values'] = backup_options


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

    tk.Button(window, text="Создать Копию", command=create_backup_now).grid(row=4, column=1)

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
    schedule_button.grid(row=4, column=0)

    def toggle_log_window():
        if log_text.winfo_ismapped():
            log_text.grid_remove()
        else:
            log_text.grid(row=5, column=0, columnspan=4, sticky="ew")

    tk.Button(window, text="Показать Лог", command=toggle_log_window).grid(row=4, column=2)

    backup_var = tk.StringVar()
    backup_combobox = ttk.Combobox(window, textvariable=backup_var)
    backup_combobox.grid(row=3, column=1)

    tk.Button(window, text="Сканировать копии",
              command=lambda: update_backup_options(backup_combobox, destination_path_entry.get())).grid(row=3,
                                                                                                         column=0)

    # Кнопка для восстановления
    tk.Button(window, text="Восстановить из копии",
              command=lambda: restore_backup(os.path.join(destination_path_entry.get(), backup_var.get()),
                                             source_path_entry.get())).grid(row=3, column=2)

    def manage_excluded_directories():
        """
        Открывает окно для управления исключенными директориями.
        """
        # create db if not exists
        destination = destination_path_entry.get()
        db_path = os.path.join(destination, 'backup_db.sqlite')
        with create_connection(db_path) as conn:
            create_table(conn)

        excluded_window = tk.Toplevel(window)
        excluded_window.title("Управление исключенными директориями")
        excluded_window.resizable(False, False)

        excluded_listbox = tk.Listbox(excluded_window, width=50, height=10)
        excluded_listbox.pack(pady=10, padx=10)

        def refresh_excluded_list():
            """ Обновляет список исключенных директорий в ListBox. """
            excluded_listbox.delete(0, tk.END)
            with create_connection(db_path) as _conn:
                dirs = get_excluded_directories(_conn)
                for _dir in dirs:
                    excluded_listbox.insert(tk.END, _dir)

        def add_directory():
            """ Добавляет новую директорию в список исключенных. """
            directory = filedialog.askdirectory()
            if directory:
                with create_connection(db_path) as _conn:
                    add_excluded_directory(_conn, directory)
                    refresh_excluded_list()

        def remove_directory():
            """ Удаляет выбранную директорию из списка исключенных. """
            selection = excluded_listbox.curselection()
            if selection:
                selected_directory = excluded_listbox.get(selection[0])
                with create_connection(db_path) as _conn:
                    remove_excluded_directory(_conn, selected_directory)
                    refresh_excluded_list()

        # Кнопки для добавления и удаления
        button_frame = tk.Frame(excluded_window)
        button_frame.pack(fill=tk.X, padx=10)

        add_button = tk.Button(button_frame, text="Добавить", command=add_directory)
        add_button.pack(side=tk.LEFT, padx=5, pady=5)

        remove_button = tk.Button(button_frame, text="Удалить", command=remove_directory)
        remove_button.pack(side=tk.LEFT, padx=5, pady=5)

        refresh_excluded_list()  # Загружаем список при открытии окна

    # Добавление кнопки для управления исключенными директориями в основном окне
    tk.Button(window, text="Исключенные директории", command=manage_excluded_directories).grid(row=5, column=0)

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
