import tkinter as tk
# Импортируем необходимые библиотеки
import tkinter as tk
from tkinter import filedialog
import shutil
import os
import schedule
import time
from datetime import datetime
import threading
# Импортируем другие компоненты

from database import create_connection, create_table
from backup_manager import backup_files


# Функция для запуска расписания в отдельном потоке
def start_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def setup_gui():
    # Создаем окно
    window = tk.Tk()
    window.title("Backup Manager")

    # Функция для выбора пути источника
    def select_source_path():
        path = filedialog.askdirectory()
        source_path_entry.delete(0, tk.END)
        source_path_entry.insert(0, path)

    # Функция для выбора пути назначения
    def select_destination_path():
        path = filedialog.askdirectory()
        destination_path_entry.delete(0, tk.END)
        destination_path_entry.insert(0, path)

    # Функция для установки расписания
    def set_schedule():
        source = source_path_entry.get()
        destination = destination_path_entry.get()
        interval = int(interval_entry.get())

        # Создаем подключение к базе данных в директории назначения
        db_path = os.path.join(destination, 'backup_db.sqlite')
        db_conn = create_connection(db_path)
        create_table(db_conn)

        schedule.every(interval).minutes.do(backup_files, source, destination, db_path)

        # Запускаем расписание в отдельном потоке
        schedule_thread = threading.Thread(target=start_schedule)
        schedule_thread.start()

    # Элементы интерфейса
    tk.Label(window, text="Источник:").grid(row=0, column=0)
    source_path_entry = tk.Entry(window, width=50)
    source_path_entry.grid(row=0, column=1)
    tk.Button(window, text="Выбрать", command=select_source_path).grid(row=0, column=2)

    tk.Label(window, text="Назначение:").grid(row=1, column=0)
    destination_path_entry = tk.Entry(window, width=50)
    destination_path_entry.grid(row=1, column=1)
    tk.Button(window, text="Выбрать", command=select_destination_path).grid(row=1, column=2)

    tk.Label(window, text="Интервал (минуты):").grid(row=2, column=0)
    interval_entry = tk.Entry(window, width=50)
    interval_entry.grid(row=2, column=1)

    tk.Button(window, text="Установить расписание", command=set_schedule).grid(row=3, column=1)

    # Запускаем GUI
    window.mainloop()


def main():
    setup_gui()


if __name__ == "__main__":
    main()
