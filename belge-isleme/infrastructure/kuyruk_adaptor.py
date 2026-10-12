
import json
import pika


class KuyrukYayinlayici:
    """Üretici (producer) tarafı — kuyruğa iş mesajı ATAR.
    kuyruga_gonder.py ve (isteğe bağlı olarak) web_arayuz.py bunu kullanır.
    """

    def __init__(self, host: str = "localhost", kuyruk_adi: str = "ocr_gorevleri"):
        self.kuyruk_adi = kuyruk_adi
        self._baglanti = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self._kanal = self._baglanti.channel()
        # durable=True: RabbitMQ yeniden başlasa bile kuyruk (ve içindeki
        # mesajlar, delivery_mode=2 ile birlikte) kaybolmaz.
        self._kanal.queue_declare(queue=self.kuyruk_adi, durable=True)

    def gorev_gonder(self, belge_yolu: str, motor_adi: str, cikti_yolu: str) -> None:
        mesaj = json.dumps({
            "belge_yolu": belge_yolu,
            "motor_adi": motor_adi,
            "cikti_yolu": cikti_yolu,
        }, ensure_ascii=False)

        self._kanal.basic_publish(
            exchange="",
            routing_key=self.kuyruk_adi,
            body=mesaj.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,  # mesaj diske yazılsın (kalıcı), RabbitMQ çökse bile kaybolmasın
            ),
        )

    def kapat(self) -> None:
        self._baglanti.close()


class KuyrukDinleyici:
    """Tüketici (worker) tarafı — kuyruktan iş mesajı OKUR ve her mesaj
    için verilen fonksiyonu çalıştırır. worker.py bunu kullanır."""

    def __init__(self, host: str = "localhost", kuyruk_adi: str = "ocr_gorevleri"):
        self.kuyruk_adi = kuyruk_adi
        self._baglanti = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self._kanal = self._baglanti.channel()
        self._kanal.queue_declare(queue=self.kuyruk_adi, durable=True)
        # prefetch_count=1: bu worker, bir mesajı BİTİRMEDEN yenisini almaz.
        # Birden fazla worker.py aynı anda çalışırken, işi ADİL şekilde
        # (kim boşta ise ona) dağıtır — bir worker 10 mesaj birden kapıp
        # diğerlerini aç bırakmaz.
        self._kanal.basic_qos(prefetch_count=1)

    def dinlemeye_basla(self, isleyici_fonksiyon) -> None:
        """isleyici_fonksiyon(gorev: dict) -> None imzasında bir fonksiyon
        bekler. Her mesaj başarıyla işlenince ACK (onay) gönderilir; hata
        alırsa, mesaj başarısız-deneme sayısı görevin İÇİNE gömülerek
        yeniden kuyruğa YAYINLANIR (basit basic_nack(requeue=True) DEĞİL —
        çünkü o, deneme sayısını hiç takip etmiyor, dead-letter-exchange
        kurulumu olmadan sonsuz döngüye sebep olabiliyordu)."""

        MAKS_DENEME = 3  # bir görev bu kadar denendikten sonra hâlâ hata veriyorsa VAZGEÇ

        def _geri_cagirma(ch, method, properties, body):
            gorev = json.loads(body.decode("utf-8"))
            deneme_sayisi = gorev.get("_deneme_sayisi", 1)

            try:
                isleyici_fonksiyon(gorev)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as hata:
                # Orijinal mesajı kuyruktan çıkarıyoruz (ack) — kendi
                # deneme-sayaçlı YENİ mesajımızı bilerek biz yayınlayacağız,
                # RabbitMQ'nun otomatik requeue mekanizmasına güvenmiyoruz.
                ch.basic_ack(delivery_tag=method.delivery_tag)

                if deneme_sayisi >= MAKS_DENEME:
                    print(f"[VAZGEÇİLDİ] {MAKS_DENEME} denemeden sonra hâlâ hata: {gorev} -> {hata}")
                else:
                    print(f"[HATA] ({deneme_sayisi}/{MAKS_DENEME}) Görev işlenemedi, tekrar denenecek: {gorev} -> {hata}")
                    gorev["_deneme_sayisi"] = deneme_sayisi + 1
                    ch.basic_publish(
                        exchange="",
                        routing_key=self.kuyruk_adi,
                        body=json.dumps(gorev, ensure_ascii=False).encode("utf-8"),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )

        self._kanal.basic_consume(queue=self.kuyruk_adi, on_message_callback=_geri_cagirma)
        print(f"Dinleniyor: '{self.kuyruk_adi}' kuyruğu. Çıkmak için CTRL+C.")
        try:
            self._kanal.start_consuming()
        except KeyboardInterrupt:
            self._kanal.stop_consuming()
            self._baglanti.close()