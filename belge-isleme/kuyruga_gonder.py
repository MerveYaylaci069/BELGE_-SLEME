#!/usr/bin/env python3
"""
kuyruga_gonder.py — ÜRETİCİ (producer)
-----------------------------------------
data/raw_files altındaki belgeleri, seçtiğin motorlarla işlenmek üzere
RabbitMQ kuyruğuna atar. Bu betik OCR'ı KENDİSİ ÇALIŞTIRMAZ — sadece
"şunu şununla işle" diye mesaj bırakır. Gerçek işi worker.py yapar.

Kullanım:
    python kuyruga_gonder.py
    python kuyruga_gonder.py --motorlar Tesseract EasyOCR
    python kuyruga_gonder.py --klasor data/raw_files
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.kuyruk_adaptor import KuyrukYayinlayici

DESTEKLENEN_UZANTILAR = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
TUM_MOTORLAR = ["Tesseract", "EasyOCR", "PaddleOCR", "RapidOCR"]
CIKTI_DIZINI = "data/kuyruk_ciktilari"


def argumanlari_ayristir() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OCR görevlerini RabbitMQ kuyruğuna gönderir")
    p.add_argument("--klasor", default="data/raw_files", help="işlenecek belgelerin klasörü")
    p.add_argument("--motorlar", nargs="+", default=TUM_MOTORLAR,
                    help=f"kullanılacak motorlar (varsayılan: hepsi -> {TUM_MOTORLAR})")
    p.add_argument("--host", default="localhost", help="RabbitMQ sunucu adresi")
    return p.parse_args()


def main() -> int:
    args = argumanlari_ayristir()
    os.makedirs(CIKTI_DIZINI, exist_ok=True)

    belgeler = sorted(
        f for f in os.listdir(args.klasor)
        if os.path.splitext(f)[1].lower() in DESTEKLENEN_UZANTILAR
    )
    if not belgeler:
        print(f"[HATA] {args.klasor} içinde desteklenen belge yok.")
        return 1

    yayinlayici = KuyrukYayinlayici(host=args.host)

    gonderilen = 0
    for belge_adi in belgeler:
        belge_yolu = os.path.join(args.klasor, belge_adi)
        for motor_adi in args.motorlar:
            gövde_adi = os.path.splitext(belge_adi)[0]
            cikti_yolu = os.path.join(CIKTI_DIZINI, f"{gövde_adi}__{motor_adi}.txt")

            yayinlayici.gorev_gonder(belge_yolu=belge_yolu, motor_adi=motor_adi, cikti_yolu=cikti_yolu)
            gonderilen += 1
            print(f"  kuyruğa eklendi: {belge_adi} x {motor_adi}")

    yayinlayici.kapat()
    print(f"\nToplam {gonderilen} görev kuyruğa eklendi.")
    print("Şimdi bir veya daha fazla terminalde 'python worker.py' çalıştır.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())