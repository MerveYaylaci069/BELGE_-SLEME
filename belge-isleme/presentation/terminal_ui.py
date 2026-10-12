from tabulate import tabulate
from typing import List
from core.entities import OlcumSonucu


class TabloOlusturucu:
    """
    Ölçüm sonuçlarını tabloya döker. Önceki hâli SADECE 2 yöntemi
    destekliyordu (yontemler[0], yontemler[1] sabit) — 3-4 motor
    eklendiğinde geri kalanları sessizce göz ardı ediyordu. Şimdi kaç
    yöntem varsa o kadar sütun açıyor.
    """

    @staticmethod
    def sonuclari_goster(sonuclar: List[OlcumSonucu]):
        if not sonuclar:
            print("Gösterilecek sonuç yok.")
            return

        gruplanmis = {}
        for s in sonuclar:
            gruplanmis.setdefault(s.belge_adi, {})[s.yontem_adi] = s


        yontemler = sorted({s.yontem_adi for s in sonuclar})

        if len(yontemler) < 2:
            print(
                "Tablo oluşturmak için en az 2 farklı yöntem test edilmelidir. "
                f"Şu an sadece şu(nlar) bulundu: {yontemler}"
            )
            return

        TabloOlusturucu._ozet_tablosu(gruplanmis, yontemler)
        TabloOlusturucu._detay_tablosu(gruplanmis, yontemler)

    @staticmethod
    def _ozet_tablosu(gruplanmis: dict, yontemler: List[str]) -> None:
        satirlar = []
        toplamlar = {y: 0.0 for y in yontemler}
        n = 0

        for belge, veriler in gruplanmis.items():
            if not all(y in veriler for y in yontemler):
                continue  # bu belge için tüm motorlar çalışmamışsa satıra dahil etme
            satir = [belge]
            for y in yontemler:
                deger = veriler[y].dogruluk_orani
                satir.append(f"%{deger:.1f}")
                toplamlar[y] += deger
            satirlar.append(satir)
            n += 1

        basliklar = ["belge"] + yontemler

        if len(yontemler) == 2:
            basliklar.append("fark")
            for i, belge in enumerate([s[0] for s in satirlar]):
                a = float(satirlar[i][1].strip("%").replace(",", "."))
                b = float(satirlar[i][2].strip("%").replace(",", "."))
                fark = a - b
                satirlar[i].append(f"+{fark:.1f}" if fark >= 0 else f"{fark:.1f}")

        if n:
            ortalama_satiri = ["ORTALAMA"] + [f"%{toplamlar[y] / n:.1f}" for y in yontemler]
            if len(yontemler) == 2:
                fark = (toplamlar[yontemler[0]] - toplamlar[yontemler[1]]) / n
                ortalama_satiri.append(f"+{fark:.1f}" if fark >= 0 else f"{fark:.1f}")
            satirlar.append(ortalama_satiri)

            en_iyi = max(yontemler, key=lambda y: toplamlar[y])
            print(f"\n→ En yüksek ortalama doğruluk: {en_iyi} (%{toplamlar[en_iyi] / n:.1f})")

        print("\n" + tabulate(satirlar, headers=basliklar, tablefmt="plain", disable_numparse=True))


    @staticmethod
    def _detay_tablosu(gruplanmis: dict, yontemler: List[str]) -> None:
        satirlar = []
        for belge, veriler in gruplanmis.items():
            for y in yontemler:
                if y not in veriler:
                    continue
                s = veriler[y]
                satirlar.append([
                    belge,
                    y,
                    f"%{s.dogruluk_orani:.1f}",
                    f"%{s.kayip_orani:.1f}",
                    s.turkce_karakter_hatasi,
                    f"{s.sure_saniye:.2f}",
                ])

        basliklar = ["belge", "yöntem", "doğruluk", "kayıp_oran", "tr_hata", "süre(sn)"]
        print("\n--- detay ---")
        print(tabulate(satirlar, headers=basliklar, tablefmt="plain", disable_numparse=True) + "\n")