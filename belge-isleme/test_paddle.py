from paddleocr import PaddleOCR

try:
    # use_angle_cls yerine yeni parametre olan use_textline_orientation kullanıyoruz
    ocr = PaddleOCR(use_textline_orientation=True, lang='tr',enable_mkldnn=False)
    
    # ocr() yerine predict() kullanıyoruz ve cls=True parametresini siliyoruz!
    result = ocr.predict('D:/kbb belge-işleme/belge-isleme/data/raw_files/belge01.pdf')
    print(result)
except Exception as e:
    print(f"PaddleOCR Hatası: {e}")