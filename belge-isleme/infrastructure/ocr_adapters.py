import pymupdf as fitz
import pytesseract
from PIL import Image
import io
import numpy as np
import easyocr
import cv2
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from core.interfaces import IOcrEngine
from paddleocr import PaddleOCR
from rapidocr_onnxruntime import RapidOCR

# Çevre değişkeni (PATH) aramak yerine, doğrudan senin bilgisayarındaki tesseract.exe yolunu veriyoruz:
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

class TesseractAdapter(IOcrEngine):
    """
    PDF sayfalarını görüntüye çevirip Tesseract OCR ile okuyan gerçek adaptör.
    """
    def __init__(self, name="Tesseract-Gercek"):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            pdf_belgesi = fitz.open(file_path)
            tum_metin = ""
            
            for sayfa_no in range(len(pdf_belgesi)):
                sayfa = pdf_belgesi.load_page(sayfa_no)
                pix = sayfa.get_pixmap(dpi=300) 
                
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # lang="tur" parametresi ile Türkçe okuma yapıyoruz
                metin = pytesseract.image_to_string(img, lang="tur")
                tum_metin += metin + "\n"
                
            return tum_metin.strip()
            
        except Exception as hata:
            print(f"Tesseract Hatası ({file_path}): {hata}")
            return ""


class EasyOcrAdapter(IOcrEngine):
    """
    EasyOCR kullanan adaptör. (olcum.py içindeki hatayı gidermek için eklendi)
    """
    def __init__(self, name="EasyOCR-tr"):
        self._name = name
        # GPU yoksa CPU ile çalışması için gpu=False
        self.reader = easyocr.Reader(['tr', 'en'], gpu=False)

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            pdf_belgesi = fitz.open(file_path)
            tum_metin = ""
            for sayfa_no in range(len(pdf_belgesi)):
                sayfa = pdf_belgesi.load_page(sayfa_no)
                pix = sayfa.get_pixmap(dpi=300)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                sonuclar = self.reader.readtext(img_array, detail=0)
                tum_metin += " ".join(sonuclar) + "\n"
            return tum_metin.strip()
        except Exception as hata:
            print(f"EasyOCR Hatası ({file_path}): {hata}")
            return ""


class PaddleOcrAdapter(IOcrEngine):
    """
    Baidu'nun geliştirdiği, özellikle Türkçe ve karmaşık tablolarda 
    çok başarılı olan PaddleOCR adaptörü.
    """
    def __init__(self, name="PaddleOCR-TR"):
        self._name = name

        os.environ['USERPROFILE'] = r'C:/PaddleTest'
        # show_log=False ekleyerek o gereksiz kalabalık terminal çıktılarını tamamen susturduk!
        self.ocr_motoru = PaddleOCR(use_angle_cls=True, lang='tr', enable_mkldnn=False, show_log=False)

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            pdf_belgesi = fitz.open(file_path)
            tum_metin = ""
            
            for sayfa_no in range(len(pdf_belgesi)):
                sayfa = pdf_belgesi.load_page(sayfa_no)
                pix = sayfa.get_pixmap(dpi=300)
                
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4: 
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                
                # Motoru çalıştırıyoruz
                sonuc = self.ocr_motoru.ocr(img_array, cls=True)
                
                # Çıktıyı PaddleOCR'ın güncel liste formatına göre doğru şekilde okuyoruz
                if sonuc and sonuc[0]:
                    for satir in sonuc[0]:
                        if satir:
                            tum_metin += satir[1][0] + "\n"
                    
            return tum_metin.strip()
        except Exception as hata:
            print(f"PaddleOCR Hatası ({file_path}): {hata}")
            return ""

class RapidOcrAdapter(IOcrEngine):
    """
    ONNX tabanlı çalışan, inanılmaz hızlı ve hafif bir OCR motoru.
    """
    def __init__(self, name="RapidOCR-ONNX"):
        self._name = name
        self.ocr_motoru = RapidOCR()

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            pdf_belgesi = fitz.open(file_path)
            tum_metin = ""
            
            for sayfa_no in range(len(pdf_belgesi)):
                sayfa = pdf_belgesi.load_page(sayfa_no)
                pix = sayfa.get_pixmap(dpi=300)
                
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                # RapidOCR doğrudan numpy dizisini kabul eder
                sonuc, _ = self.ocr_motoru(img_array)
                
                if sonuc:
                    for satir in sonuc:
                        tum_metin += satir[1] + "\n"
                        
            return tum_metin.strip()
        except Exception as hata:
            print(f"RapidOCR Hatası ({file_path}): {hata}")
            return ""


class MockOcrAdapter(IOcrEngine):
    """
    Yöntem B'yi test edebilmek için geçici olarak tuttuğumuz sahte adaptör.
    """
    def __init__(self, name: str, simulated_text: str):
        self._name = name
        self.simulated_text = simulated_text
        
    def get_name(self) -> str:
        return self._name
        
    def extract_text(self, file_path: str) -> str:
        return self.simulated_text

class DoctrAdapter(IOcrEngine):
    """
    Mindee DocTR motoru. Belge analizinde ve düzen (layout) korumada mükemmeldir.
    """
    def __init__(self, name="DocTR-PyTorch"):
        self._name = name
        # Import işlemini init içine alıyoruz ki kurulmamışsa programı en başta çökertmesin
        from doctr.models import ocr_predictor
        self.predictor = ocr_predictor(pretrained=True)

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            from doctr.io import DocumentFile
            # DocTR doğrudan PDF okuma yeteneğine sahiptir
            doc = DocumentFile.from_pdf(file_path)
            sonuc = self.predictor(doc)
            
            tum_metin = ""
            # DocTR hiyerarşik veri döner: Sayfalar -> Bloklar -> Satırlar -> Kelimeler
            for page in sonuc.pages:
                for block in page.blocks:
                    for line in block.lines:
                        satir_metni = " ".join([word.value for word in line.words])
                        tum_metin += satir_metni + "\n"
            return tum_metin.strip()
        except Exception as hata:
            print(f"DocTR Hatası ({file_path}): {hata}")
            return ""


class KerasOcrAdapter(IOcrEngine):
    """
    Dağınık ve düzensiz metinleri bulmada etkili TensorFlow tabanlı motor.
    """
    def __init__(self, name="KerasOCR"):
        self._name = name
        import keras_ocr
        self.pipeline = keras_ocr.pipeline.Pipeline()

    def get_name(self) -> str:
        return self._name

    def extract_text(self, file_path: str) -> str:
        try:
            import fitz
            import numpy as np
            import cv2
            
            pdf_belgesi = fitz.open(file_path)
            tum_metin = ""
            images = []
            
            # Keras-OCR resim listesi bekler, PDF'i resimlere çevirip listeye ekliyoruz
            for sayfa_no in range(len(pdf_belgesi)):
                sayfa = pdf_belgesi.load_page(sayfa_no)
                pix = sayfa.get_pixmap(dpi=300)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                images.append(img_array)
            
            # Tüm resimleri aynı anda modele veriyoruz
            tahminler = self.pipeline.recognize(images)
            
            for sayfa_tahmini in tahminler:
                for text, box in sayfa_tahmini:
                    tum_metin += text + " "
                tum_metin += "\n"
                
            return tum_metin.strip()
        except Exception as hata:
            print(f"KerasOCR Hatası ({file_path}): {hata}")
            return ""