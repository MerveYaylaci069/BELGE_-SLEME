from abc import ABC, abstractmethod

class IOcrEngine(ABC):
    """
    Sisteme eklenecek tüm OCR motorlarının (Yöntem A, Yöntem B vb.) 
    uyması gereken zorunlu sözleşme (arayüz).
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Kullanılan OCR yönteminin adını döndürür. 
        Tablodaki 'yöntem A', 'yöntem B' başlıklarını dinamik almak için gereklidir.
        Örn: 'Tesseract varsayılan', 'EasyOCR tr'
        """
        pass

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Verilen dosya yolundaki taranmış PDF veya görüntüden metni çıkarır.
        """
        pass


class IFileReader(ABC):
    """
    Yer-gerçeği (ground truth) dosyalarını okumak için kullanılacak arayüz.
    Dosya sistemine bağımlılığı soyutlar.
    """

    @abstractmethod
    def read_text_file(self, file_path: str) -> str:
        """
        Belirtilen .txt dosyasını okur ve içeriğini string olarak döndürür.
        """
        pass