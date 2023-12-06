# Импортируем необходимые библиотеки
import tkinter as tk
from tkinter import filedialog
import shutil
import os
import schedule
import time
from datetime import datetime
import threading


# Функция для копирования файлов с версионированием
def backup_files(source, destination):
    # Получаем текущее время для создания уникальной папки версии
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_path = os.path.join(destination, timestamp)

    # Копирование файлов
    if not os.path.exists(version_path):
        os.makedirs(version_path)
    for file_name in os.listdir(source):
        full_file_name = os.path.join(source, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, version_path)


# Функция для запуска расписания в отдельном потоке
def start_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Графический интерфейс пользователя
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

        schedule.every(interval).minutes.do(backup_files, source, destination)

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


# Запуск GUI
setup_gui()
