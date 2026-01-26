import os
import shutil
import datetime

def create_backup(source_dir, destination_dir):
    # Проверка существования исходной папки
    if not os.path.exists(source_dir):
        print(f"Ошибка: Исходная папка '{source_dir}' не найдена.")
        return

    # Создание папки назначения, если её нет
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Формирование имени архива с датой и временем
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(source_dir.strip('/'))
    backup_name = f"backup_{base_name}_{timestamp}"
    archive_path = os.path.join(destination_dir, backup_name)

    try:
        # Создание zip-архива
        print(f"Начинаю резервное копирование '{source_dir}'...")
        shutil.make_archive(archive_path, 'zip', source_dir)
        print(f"Бекап успешно создан: {archive_path}.zip")
    except Exception as e:
        print(f"Произошла ошибка при создании бекапа: {e}")

if __name__ == "__main__":
    # Пример использования
    # Замени эти пути на свои
    SOURCE = "/home/illia/Documents"  # Что копируем
    DESTINATION = "/home/illia/Backups" # Куда сохраняем

    create_backup(SOURCE, DESTINATION)
