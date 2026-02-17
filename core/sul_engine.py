# core/sul_engine.py
import os
import json
import struct
import time
from .sul_crypto import SulCrypto

class SulArchiver:
    SIGNATURE = b'SUL_ARC'
    VERSION = 1

    def __init__(self, log_callback=print):
        self.log = log_callback

    def _validate_filename(self, filename):
        base = os.path.basename(filename)
        if not (base.startswith("sul.") and base.endswith(".sul")):
            raise ValueError("Нарушение стандарта SUL! Имя должно быть 'sul.name.sul'")

    def create_archive(self, source_path, output_path):
        self._validate_filename(output_path)
        
        file_manifest = []
        file_data_blob = bytearray()
        
        self.log(f"[*] Начало архивации: {source_path}")
        
        # 1. Сбор файлов
        if os.path.isfile(source_path):
            files_to_process = [source_path]
            root_dir = os.path.dirname(source_path)
        else:
            files_to_process = []
            root_dir = source_path
            for root, _, files in os.walk(source_path):
                for file in files:
                    files_to_process.append(os.path.join(root, file))

        total_files = len(files_to_process)
        self.log(f"[*] Найдено файлов: {total_files}")

        # 2. Обработка файлов
        current_offset = 0
        for idx, filepath in enumerate(files_to_process):
            rel_path = os.path.relpath(filepath, root_dir)
            
            try:
                with open(filepath, 'rb') as f:
                    raw_data = f.read()
                
                # КОДИРОВАНИЕ SUL
                encoded_data = SulCrypto.encode_data(raw_data)
                size_encoded = len(encoded_data)
                
                # Запись в общий блоб
                file_data_blob.extend(encoded_data)
                
                # Добавление в манифест
                file_manifest.append({
                    'path': rel_path,
                    'size': size_encoded, # Размер в архиве
                    'orig_size': len(raw_data),
                    'offset': current_offset
                })
                
                current_offset += size_encoded
                self.log(f"  [+] Добавлен: {rel_path} ({len(raw_data)} -> {size_encoded} bytes)")
                
            except Exception as e:
                self.log(f"  [!] Ошибка с файлом {rel_path}: {e}")

        # 3. Подготовка метаданных
        meta_json = json.dumps(file_manifest).encode('utf-8')
        # Метаданные тоже шифруем, чтобы никто не прочитал структуру папок
        meta_encrypted = SulCrypto._transform(meta_json) 
        meta_len = len(meta_encrypted)

        # 4. Запись итогового файла
        with open(output_path, 'wb') as f:
            # [SIGNATURE 7b] [VER 1b] [META_LEN 4b]
            header = self.SIGNATURE + struct.pack('B', self.VERSION) + struct.pack('I', meta_len)
            f.write(header)
            f.write(meta_encrypted)
            f.write(file_data_blob)

        self.log(f"✅ Архив SUL успешно создан: {output_path}")

    def extract_archive(self, archive_path, output_dir):
        self.log(f"[*] Чтение архива: {archive_path}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(archive_path, 'rb') as f:
            # 1. Проверка сигнатуры
            sig = f.read(7)
            if sig != self.SIGNATURE:
                raise ValueError("CRITICAL: Это не формат SUL_ARC! Операция прервана.")
            
            ver = struct.unpack('B', f.read(1))[0]
            if ver != self.VERSION:
                self.log(f"[!] Предупреждение: Версия архива {ver}, ожидалась {self.VERSION}")

            # 2. Чтение метаданных
            meta_len = struct.unpack('I', f.read(4))[0]
            meta_encrypted = f.read(meta_len)
            
            try:
                meta_json = SulCrypto._transform(meta_encrypted).decode('utf-8')
                manifest = json.loads(meta_json)
            except:
                raise ValueError("Ошибка: Метаданные повреждены или взломаны.")

            # 3. Чтение данных
            data_blob = f.read() # Читаем остаток
            
            self.log(f"[*] Извлечение {len(manifest)} файлов...")
            
            for entry in manifest:
                rel_path = entry['path']
                offset = entry['offset']
                size = entry['size']
                
                # Извлекаем кусок зашифрованных данных
                chunk = data_blob[offset : offset + size]
                
                # ДЕКОДИРОВАНИЕ SUL
                try:
                    original_data = SulCrypto.decode_data(chunk)
                except Exception as e:
                    self.log(f"  [!] Ошибка декодирования {rel_path}: {e}")
                    continue

                # Сохранение
                dest_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                with open(dest_path, 'wb') as out_f:
                    out_f.write(original_data)
                
                self.log(f"  [v] Распакован: {rel_path}")

        self.log("✅ Распаковка завершена успешно.")