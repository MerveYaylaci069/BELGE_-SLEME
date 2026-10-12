import os
os.environ["USERPROFILE"] = "C:\\PaddleTest"

from application.kalite_olcum import KaliteOlcumServisi
from infrastructure.file_adapters import YerelDosyaOkuyucu
from infrastructure.ocr_adapters import (
    TesseractAdapter,
    EasyOcrAdapter,
    PaddleOcrAdapter,
    RapidOcrAdapter,
    DoctrAdapter,
    KerasOcrAdapter,
)
from presentation.terminal_ui import TabloOlusturucu
from infrastructure.onbellek_adaptor import OnbellekliMotor


def ana_kurulum():
    dosya_okuyucu = YerelDosyaOkuyucu()

    adaylar = [
        ("Tesseract", lambda: OnbellekliMotor(TesseractAdapter(name="Tesseract-varsayilan"))),
        ("EasyOCR", lambda: OnbellekliMotor(EasyOcrAdapter(name="EasyOCR-tr"))),
        ("PaddleOCR", lambda: OnbellekliMotor(PaddleOcrAdapter(name="PaddleOCR-tr"))),
        ("RapidOCR", lambda: OnbellekliMotor(RapidOcrAdapter(name="RapidOCR-onnx"))),
        # ("DocTR", lambda: OnbellekliMotor(DoctrAdapter(name="DocTR-PyTorch"))),
    ]

    servisler = []
    for etiket, kurucu in adaylar:
        try:
            motor = kurucu()
            servisler.append(KaliteOlcumServisi(ocr_motoru=motor, dosya_okuyucu=dosya_okuyucu))
            print(f"[OK] {etiket} yüklendi.")
        except Exception as hata:
            print(f"[ATLANDI] {etiket} kurulamadı: {hata}")

    return servisler


def main():
    servisler = ana_kurulum()

    if len(servisler) < 2:
        print(
            "\n[HATA] En az 2 çalışan motor gerekli, "
            f"sadece {len(servisler)} tanesi yüklenebildi. "
            "Yukarıdaki [ATLANDI] satırlarına bakıp eksik kütüphaneleri kurun "
            "(pip install easyocr / paddleocr paddlepaddle / rapidocr_onnxruntime)."
        )
        return

    sonuclar = []
    test_belgeleri = [
        {
            "belge_adi": "belge01.pdf",
            "dosya_yolu": "data/raw_files/belge01.pdf",
            "yer_gercegi": "data/ground_truth/belge01.txt",
        },
        {
            "belge_adi": "egribelge.pdf",
            "dosya_yolu": "data/raw_files/egribelge.pdf",
            "yer_gercegi": "data/ground_truth/egribelge.txt",
        },

        {
            "belge_adi": "tablo01.pdf",
            "dosya_yolu": "data/raw_files/tablo01.pdf",
            "yer_gercegi": "data/ground_truth/tablo01.txt",
        },
        {
            "belge_adi": "tablo03.pdf",
            "dosya_yolu": "data/raw_files/tablo03.pdf",
            "yer_gercegi": "data/ground_truth/tablo03.txt",
        },
        {
                        "belge_adi": "uzunmetin.pdf",
                        "dosya_yolu": "data/raw_files/uzunmetin.pdf",
                        "yer_gercegi": "data/ground_truth/uzunmetin.txt",
        },
        {
                    "belge_adi": "resim.png",
                    "dosya_yolu": "data/raw_files/resim.png",
                    "yer_gercegi": "data/ground_truth/resim.txt",
        },
        {
                    "belge_adi": "resim2.jpg",
                    "dosya_yolu": "data/raw_files/resim2.jpg",
                    "yer_gercegi": "data/ground_truth/resim2.txt",
        }
    ]

    print(f"\nÖlçüm işlemi başlatılıyor... ({len(servisler)} motor x {len(test_belgeleri)} belge)\n")

    for belge in test_belgeleri:
        for servis in servisler:
            sonuc = servis.belgeyi_degerlendir(
                belge_adi=belge["belge_adi"],
                dosya_yolu=belge["dosya_yolu"],
                yer_gercegi_yolu=belge["yer_gercegi"],
            )
            sonuclar.append(sonuc)
            print(f"  işlendi: {belge['belge_adi']} x {sonuc.yontem_adi}")

    TabloOlusturucu.sonuclari_goster(sonuclar)


if __name__ == "__main__":
    main()