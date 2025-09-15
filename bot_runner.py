from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time
import sys
import os

class BotReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()
        # Список папок, которые нужно игнорировать
        self.ignored_dirs = {
            '__pycache__',
            '.git',
            'venv',
            'env',
            'logs',
            '.idea',
            '.vscode',
            'node_modules'
        }
    
    def start_bot(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Запуск бота...")
        self.process = subprocess.Popen([sys.executable, 'main.py'])
    
    def should_ignore(self, path):
        """Проверка, нужно ли игнорировать путь"""
        # Разбиваем путь на части
        parts = path.split(os.sep)
        # Проверяем каждую часть пути
        for part in parts:
            if part in self.ignored_dirs:
                return True
        return False
    
    def on_modified(self, event):
        # Проверяем, что это Python файл и путь не в игнорируемых папках
        if event.src_path.endswith('.py') and not self.should_ignore(event.src_path):
            print(f"Обнаружено изменение в {event.src_path}")
            self.start_bot()

if __name__ == "__main__":
    path = '.'
    event_handler = BotReloader()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()