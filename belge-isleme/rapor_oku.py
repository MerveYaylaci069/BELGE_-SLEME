import os


os.environ['USERPROFILE'] = 'C:\\PaddleTest'
os.environ['HOME'] = 'C:\\PaddleTest'


import pymupdf as fitz
from infrastructure.ocr_adapters import PaddleOcrAdapter
import time

def dev_raporu_parcala_ve_oku(ana_pdf_yolu: str, bolum_sayfa_sayisi: int = 200):
    print("🚀 PaddleOCR Motoru Yükleniyor...")
    motor = PaddleOcrAdapter()
    
    doc = fitz.open(ana_pdf_yolu)
    toplam_sayfa = len(doc)
    print(f"📄 Belge bulundu: Toplam {toplam_sayfa} sayfa.")

    ciktilar_klasoru = "rapor_ciktilari"
    os.makedirs(ciktilar_klasoru, exist_ok=True)

    for i in range(0, toplam_sayfa, bolum_sayfa_sayisi):
        baslangic = i
        bitis = min(i + bolum_sayfa_sayisi - 1, toplam_sayfa - 1)
        isim_sablonu = f"Bolum_{baslangic+1}-{bitis+1}"
        
        yeni_pdf = fitz.open()
        yeni_pdf.insert_pdf(doc, from_page=baslangic, to_page=bitis)
        gecici_pdf_yolu = os.path.join(ciktilar_klasoru, f"{isim_sablonu}.pdf")
        yeni_pdf.save(gecici_pdf_yolu)
        yeni_pdf.close()
        
        print(f"\n⏳ İşleniyor: {gecici_pdf_yolu} (Bu işlem 10-15 dakika sürebilir, lütfen kapatmayın...)")
        t0 = time.time()
        cikarilan_metin = motor.extract_text(gecici_pdf_yolu)
        gecen_sure = time.time() - t0
        
        
        txt_yolu = os.path.join(ciktilar_klasoru, f"{isim_sablonu}_METIN.txt")
        with open(txt_yolu, "w", encoding="utf-8") as f:
            f.write(cikarilan_metin)
            
        print(f"✅ Bitti! {txt_yolu} kaydedildi. (Geçen süre: {gecen_sure/60:.1f} dakika)")


if __name__ == "__main__":
   "
    dosya_adi = "data/raw_files/2025FaaliyetRaporu.pdf" 
    dev_raporu_parcala_ve_oku(dosya_adi)