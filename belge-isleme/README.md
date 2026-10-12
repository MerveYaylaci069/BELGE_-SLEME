# belge-isleme — Metin Çıkarma ve Kalite Ölçümü

Konya Büyükşehir Belediyesi Yazılım Ekibi
Geliştiriciler: SELMA BETÜL KOTUK & ÖMER ALİ ALKAN



## Mimari

Katmanlı (clean) mimari — bağımlılık yönü tek taraflı:
`infrastructure → application → core`. `core/` hiçbir dış kütüphaneye
bağımlı değil; yeni bir OCR motoru eklemek `application/` veya `core/`'da
hiçbir satırı değiştirmeden mümkün.

```
olcum.py                        composition root — hangi motorların kullanılacağına
                                 SADECE burada karar veriliyor
core/
├── entities.py                  OlcumSonucu — saf veri modeli
└── interfaces.py                IOcrEngine — her motorun uyduğu sözleşme
application/
└── kalite_olcum.py              KaliteOlcumServisi — karşılaştırma/ölçüm mantığının kalbi
                                  (Levenshtein tabanlı doğruluk, kayıp oran,
                                  Türkçe karakter hatası, süre)
infrastructure/
├── file_adapters.py             YerelDosyaOkuyucu — yer-gerçeği .txt dosyalarını okur
├── ocr_adapters.py               6 motor: Tesseract, EasyOCR, PaddleOCR,
│                                 RapidOCR, DocTR, KerasOCR — hepsi IOcrEngine'i uygular
└── onbellek_adaptor.py          OnbellekliMotor — herhangi bir motoru sarıp
                                  sonucu diske önbellekleyen dekoratör
presentation/
└── terminal_ui.py               TabloOlusturucu — sadece tablo biçimlendirme
data/
├── raw_files/                   ham belgeler (pdf/jpg/png/tiff)
├── ground_truth/                elle yazılmış doğru metinler (<belge_adı>.txt)
└── onbellek/
    └── ocr_sonuclari.json       motor sonuçlarının önbelleği (bkz. aşağı)
```


## web arayüz çalıştırma 

streamlit run presentation/web_arayuz.py

## Kurulum

```powershell
# Sanal ortamı etkinleştir
.\venv\Scripts\activate


# Python bağımlılıkları
pip install pytesseract pymupdf pillow numpy tabulate
pip install easyocr
pip install paddlepaddle==2.6.1 paddleocr==2.7.3
pip install rapidocr_onnxruntime
pip install python-doctr[torch]
pip install keras-ocr
```

⚠️ **PaddleOCR sürüm uyumu önemli.** `paddleocr`'ın en güncel (3.x) sürümü
eski API'yi (`show_log`, `use_angle_cls`) tamamen değiştirdi. Yukarıdaki
sabit sürümler (`paddlepaddle==2.6.1`, `paddleocr==2.7.3`) ile kod
doğrudan uyumlu; kod ayrıca sürüm farkına karşı otomatik yedekli
(`PaddleOcrAdapter.__init__` birden fazla API kombinasyonunu dener).

## Çalıştırma

```powershell
python olcum.py
```

Her motor `try/except` içinde ayrı ayrı kurulur — biri kurulu değilse
(örn. `easyocr` yüklenmemişse) program **çökmez**, sadece o motoru
`[ATLANDI]` diyerek atlar ve kalan motorlarla devam eder:

```
[OK] Tesseract yüklendi.
[ATLANDI] PaddleOCR kurulamadı: <sebep>
[OK] RapidOCR yüklendi.
```

En az 2 çalışan motor gerekir; daha azı varsa program eksik kütüphaneleri
hangi `pip install` komutuyla tamamlayacağını söyler.

## Önbellekleme (`data/onbellek/ocr_sonuclari.json`)

Her motor `OnbellekliMotor` ile sarmalanmış durumda: bir belge + motor
kombinasyonu **daha önce işlendiyse**, OCR tekrar çalıştırılmaz, sonuç
diskten okunur (`[önbellek] ... — OCR atlandı` satırıyla belli olur). Bu,
5-6 motor × büyüyen belge sayısında dakikalarca sürebilen çalıştırmaları
saniyelere indiriyor.

- **Yeni bir belge eklersen** → otomatik olarak sıfırdan işlenir.
- **Var olan bir belgeyi değiştirirsen** (üzerine yeni dosya kaydedersen) →
  dosyanın boyutu/değişiklik tarihi değişeceği için otomatik olarak
  yeniden işlenir, elle bir şey silmene gerek yok.
- **Önbelleği tamamen sıfırlamak istersen** → `data/onbellek/ocr_sonuclari.json`'ı
  sil, bir sonraki çalıştırma her şeyi yeniden işler.
- ⚠️ `süre(sn)` sütunu önbellekten okunan satırlarda ~0.00 çıkar — bu
  hata değil, "bu çalıştırmada OCR gerçekten çalışmadı" demek. Rapor için
  bir belgenin **ilk (önbelleksiz)** çalıştırmasındaki süre değerini esas
  al.

## Ölçüm nasıl okunur

Dört ölçüt, `application/kalite_olcum.py`'de hesaplanıyor:

| Ölçüt | Ne demek |
|---|---|
| **Doğruluk (%)** | `100 - (levenshtein_mesafesi / yer_gerçeği_uzunluğu × 100)` — çıkarılan metin yer-gerçeğine ne kadar benziyor |
| **Kayıp oran (%)** | Yer-gerçeğindeki karakterlerden çıkan metinde hiç görünmeyenlerin oranı |
| **Türkçe karakter hatası** | Aynı konumdaki ı↔i, ş↔s, ğ↔g, ü↔u, ö↔o, ç↔c karışıklığı sayısı |
| **Süre (sn)** | Motorun o belgeyi işlemesi kaç saniye sürdü |

## Bilinen sınırlamalar

- **Tablolu belgelerde `tr_hata` sayısı güvenilir değil.** Sayaç, yer-gerçeği
  ile çıkan metni **aynı konumda** karşılaştırıyor (pozisyonel hizalama).
  OCR bir tabloyu satır/sütun sırasını yer-gerçeğinden farklı şekilde
  okursa metnin tamamı "kaymış" gibi görünüyor ve gerçekçi olmayan yüksek
  hata sayıları (yüzlerce) çıkabiliyor. Tablolu belgelerde bu sayıyı
  yorumlarken dikkatli olun.
- **Dosyası eksik veya yer-gerçeği bulunamayan belgeler** (örn. eksik bir
  PDF) şu an `%0,0` olarak tabloya giriyor ve ORTALAMA'yı yapay şekilde
  düşürüyor — bu bir OCR başarısızlığı değil, veri eksikliği. ORTALAMA'yı
  yorumlarken bu satırları hariç tutun ya da eksik dosya/yer-gerçeğini
  tamamlayın.
- **Yer-gerçeği dosyaları gerçekten elle doğrulanmalı.** Görev tanımının
  vurguladığı gibi, yer-gerçeği bir OCR çıktısından kopyalanırsa ölçüm
  "OCR'ı OCR ile karşılaştırmak" hâline gelir ve anlamsızlaşır.

## Ölçüm sonucu 
 En yüksek ortalama doğruluk: PaddleOCR-tr (%71.8)

belge        EasyOCR-tr    PaddleOCR-tr    RapidOCR-onnx    Tesseract-varsayilan
belge01.pdf  %83.7         %82.2           %82.5            %96.9
belge02.pdf  %22.8         %71.8           %71.6            %8.4
tablo01.pdf  %72.5         %76.6           %68.3            %86.1
tablo03.pdf  %51.0         %46.8           %48.1            %49.5
tablo4.pdf   %93.4         %88.5           %83.5            %98.5
resim.png    %68.7         %65.3           %61.6            %68.1
ORTALAMA     %65.4         %71.8           %69.3            %67.9


## Bulgu notu

> Aşağıdaki taslak, kendi güncel 10+ belgelik ölçümünle doldurulmalı.

- **Temiz taranmış belgelerde**: Tesseract genelde en yüksek doğruluk *ve*
  en hızlı motor — bu tür belgelerde önerilir.
- **Tablolu belgelerde**: hiçbir motor tek başına güvenilir değil; tablo
  yapısını (satır/sütun) koruyan ayrı bir ön işleme adımı olmadan
  doğruluk ciddi düşüyor.
- **EasyOCR**: doğruluk olarak rekabetçi ama belirgin şekilde daha yavaş
  (bazı belgelerde Tesseract'ın 15-30 katı süre).
- **Öneri**: [motor adı], [belge türü] için önerilir çünkü [sayısal gerekçe].
  [Başka motor], [başka durum] için önerilir çünkü [sayısal gerekçe].

## Git ayarı

`venv/` ve `__pycache__/` klasörlerinin `.gitignore`'da olduğundan ve
git tarafından takip edilmediğinden emin olun:

```powershell
git rm -r --cached venv
git rm -r --cached infrastructure/__pycache__
```