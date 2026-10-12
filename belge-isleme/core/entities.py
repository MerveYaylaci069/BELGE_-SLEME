from dataclasses import dataclass

@dataclass
class OlcumSonucu:
    """
    Bir belgenin tek bir OCR yöntemiyle analiz edildikten sonraki
    ölçüm metriklerini tutan saf veri yapısı.
    """
    belge_adi: str
    yontem_adi: str
    dogruluk_orani: float
    kayip_orani: float
    turkce_karakter_hatasi: int
    sure_saniye: float