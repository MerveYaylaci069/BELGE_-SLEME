
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



os.environ['USERPROFILE'] = r'C:/PaddleTest'
os.environ['HOME'] = r'C:/PaddleTest'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.makedirs(r'C:/PaddleTest', exist_ok=True)


from infrastructure.kuyruk_adaptor import KuyrukDinleyici
from infrastructure.onbellek_adaptor import OnbellekliMotor
from infrastructure.ocr_adapters import (
    TesseractAdapter,
    EasyOcrAdapter,
    PaddleOcrAdapter,
    RapidOcrAdapter,
)


MOTOR_KURUCULARI = {
    "Tesseract": lambda: TesseractAdapter(name="Tesseract-varsayilan"),
    "EasyOCR": lambda: EasyOcrAdapter(name="EasyOCR-tr"),
    "PaddleOCR": lambda: PaddleOcrAdapter(name="PaddleOCR-tr"),
    "RapidOCR": lambda: RapidOcrAdapter(name="RapidOCR-onnx"),
}


_kurulu_motorlar: dict = {}


def motoru_getir(motor_adi: str):
    if motor_adi not in _kurulu_motorlar:
        print(f"  [{motor_adi}] motor yükleniyor...")
        ic_motor = MOTOR_KURUCULARI[motor_adi]()
        _kurulu_motorlar[motor_adi] = OnbellekliMotor(ic_motor)
    return _kurulu_motorlar[motor_adi]


def gorevi_isle(gorev: dict) -> None:
    belge_yolu = gorev["belge_yolu"]
    motor_adi = gorev["motor_adi"]
    cikti_yolu = gorev["cikti_yolu"]

    print(f"İşleniyor: {belge_yolu} x {motor_adi}")

    motor = motoru_getir(motor_adi)
    metin = motor.extract_text(belge_yolu)  

    os.makedirs(os.path.dirname(cikti_yolu), exist_ok=True)
    with open(cikti_yolu, "w", encoding="utf-8") as f:
        f.write(metin)

    print(f"  tamamlandı -> {cikti_yolu}")


def main() -> int:
    p = argparse.ArgumentParser(description="RabbitMQ kuyruğundan OCR görevlerini işleyen worker")
    p.add_argument("--host", default="localhost", help="RabbitMQ sunucu adresi")
    args = p.parse_args()

    dinleyici = KuyrukDinleyici(host=args.host)
    dinleyici.dinlemeye_basla(gorevi_isle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())