import time
import Levenshtein
from core.entities import OlcumSonucu
from core.interfaces import IOcrEngine, IFileReader

class KaliteOlcumServisi:
    """
    Belge işleme ve kalite ölçüm kurallarının koşturulduğu Use Case sınıfı.
    """
    
    def __init__(self, ocr_motoru: IOcrEngine, dosya_okuyucu: IFileReader):
        self.ocr_motoru = ocr_motoru
        self.dosya_okuyucu = dosya_okuyucu

    def belgeyi_degerlendir(self, belge_adi: str, dosya_yolu: str, yer_gercegi_yolu: str) -> OlcumSonucu:
        """
        Belirtilen dosya için OCR işlemini başlatır, süreyi ölçer ve 
        yer-gerçeği ile kıyaslayarak metrikleri hesaplar.
        """
        baslangic_zamani = time.time()
        cikarilan_metin = self.ocr_motoru.extract_text(dosya_yolu)
        sure = time.time() - baslangic_zamani
        
        gercek_metin = self.dosya_okuyucu.read_text_file(yer_gercegi_yolu)
        
        if not gercek_metin:
            return OlcumSonucu(belge_adi, self.ocr_motoru.get_name(), 0.0, 0.0, 0, sure)

        gercek_uzunluk = len(gercek_metin)
        
        mesafe = Levenshtein.distance(gercek_metin, cikarilan_metin)
        maks_uzunluk = max(gercek_uzunluk, len(cikarilan_metin))
        dogruluk = ((maks_uzunluk - mesafe) / maks_uzunluk) * 100 if maks_uzunluk > 0 else 0.0
        
        edit_islemleri = Levenshtein.editops(gercek_metin, cikarilan_metin)
        kayip_sayisi = 0
        turkce_hata = 0

        
        turkce_karisim_ciftleri = {
            ("ı", "i"), ("i", "ı"), ("İ", "I"), ("I", "İ"), ("İ", "i"), ("i", "İ"),
            ("ş", "s"), ("s", "ş"), ("Ş", "S"), ("S", "Ş"),
            ("ğ", "g"), ("g", "ğ"), ("Ğ", "G"), ("G", "Ğ"),
            ("ü", "u"), ("u", "ü"), ("Ü", "U"), ("U", "Ü"),
            ("ö", "o"), ("o", "ö"), ("Ö", "O"), ("O", "Ö"),
            ("ç", "c"), ("c", "ç"), ("Ç", "C"), ("C", "Ç"),
        }

        for islem, gercek_idx, cikarilan_idx in edit_islemleri:
            if islem == 'delete':
                kayip_sayisi += 1
               
            elif islem == 'replace':
                gercek_karakter = gercek_metin[gercek_idx]
                cikan_karakter = cikarilan_metin[cikarilan_idx]
                if (gercek_karakter, cikan_karakter) in turkce_karisim_ciftleri:
                    turkce_hata += 1

        kayip_orani = (kayip_sayisi / gercek_uzunluk) * 100 if gercek_uzunluk > 0 else 0.0

        return OlcumSonucu(
            belge_adi=belge_adi,
            yontem_adi=self.ocr_motoru.get_name(),
            dogruluk_orani=dogruluk,
            kayip_orani=kayip_orani,
            turkce_karakter_hatasi=turkce_hata,
            sure_saniye=sure
        )