
import json
import os
from core.interfaces import IOcrEngine


class OnbellekliMotor(IOcrEngine):
    def __init__(self, ic_motor: IOcrEngine, onbellek_dizini: str = "data/onbellek"):
        self._ic_motor = ic_motor
        os.makedirs(onbellek_dizini, exist_ok=True)
        self._onbellek_dosyasi = os.path.join(onbellek_dizini, "ocr_sonuclari.json")
        # DİKKAT: burada dosyayı belleğe alıp saklamıyoruz. Her motor
        # (Tesseract, EasyOCR, PaddleOCR, RapidOCR...) kendi ayrı nesnesi
        # olduğu için, program başında okunan bir kopyayı bellekte tutmak
        # şu hataya yol açıyordu: bir motor kendi eski kopyasını diskin
        # üzerine yazınca, ARADA başka bir motorun eklediği kayıtları
        # SİLİYORDU. Çözüm: her okuma/yazmada dosyayı DİSKTEN TAZE almak.

    def get_name(self) -> str:
        return self._ic_motor.get_name()

    def extract_text(self, file_path: str) -> str:
        anahtar = self._anahtar_uret(file_path)

        guncel_onbellek = self._onbellegi_yukle()
        if anahtar in guncel_onbellek:
            print(f"  [önbellek] {self.get_name()} x {os.path.basename(file_path)} "
                  f"— OCR atlandı, kayıtlı sonuç kullanıldı.")
            return guncel_onbellek[anahtar]

        metin = self._ic_motor.extract_text(file_path)

        # Kaydetmeden HEMEN ÖNCE dosyayı tekrar taze okuyoruz — bu arada
        # başka bir motor kendi sonucunu yazmış olabilir, onu KAYBETMEDEN
        # sadece kendi anahtarımızı ekliyoruz.
        guncel_onbellek = self._onbellegi_yukle()
        guncel_onbellek[anahtar] = metin
        self._onbellegi_kaydet(guncel_onbellek)
        return metin

    def _anahtar_uret(self, file_path: str) -> str:
        """motor + dosya yolu + (boyut, değişiklik-tarihi) -> tekil anahtar.
        Dosya değişirse (boyut ya da mtime farklıysa) anahtar da değişir,
        bu yüzden değişen belgeler otomatik yeniden işlenir."""
        try:
            durum = os.stat(file_path)
            imza = f"{durum.st_size}_{int(durum.st_mtime)}"
        except FileNotFoundError:
            imza = "dosya_yok"
        return f"{self.get_name()}::{file_path}::{imza}"

    def _onbellegi_yukle(self) -> dict:
        if os.path.exists(self._onbellek_dosyasi):
            try:
                with open(self._onbellek_dosyasi, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _onbellegi_kaydet(self, onbellek: dict) -> None:
        with open(self._onbellek_dosyasi, "w", encoding="utf-8") as f:
            json.dump(onbellek, f, ensure_ascii=False, indent=2)