import os
from core.interfaces import IFileReader

class YerelDosyaOkuyucu(IFileReader):
    """
    Bilgisayardaki yerel metin dosyalarını okuyan altyapı sınıfı.
    """
    def read_text_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            print(f"Uyarı: Dosya bulunamadı -> {file_path}")
            return ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()