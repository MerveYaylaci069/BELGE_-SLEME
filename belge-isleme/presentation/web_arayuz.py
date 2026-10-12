import os
import sys
import time

os.environ['USERPROFILE'] = r'C:/PaddleTest'
os.environ['HOME'] = r'C:/PaddleTest'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import streamlit as st
import pandas as pd

KOK_DIZIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if KOK_DIZIN not in sys.path:
    sys.path.insert(0, KOK_DIZIN)

from application.kalite_olcum import KaliteOlcumServisi
from infrastructure.file_adapters import YerelDosyaOkuyucu
from infrastructure.onbellek_adaptor import OnbellekliMotor
from infrastructure.ocr_adapters import (
    TesseractAdapter,
    EasyOcrAdapter,
    PaddleOcrAdapter,
    RapidOcrAdapter,
)

GECICI_DIZIN = os.path.join(KOK_DIZIN, "temp_uploads")
os.makedirs(GECICI_DIZIN, exist_ok=True)
os.environ['USERPROFILE'] = r'C:/PaddleTest'
os.environ['HOME'] = r'C:/PaddleTest'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

MOTOR_KURUCULARI = {
    "Tesseract": lambda: TesseractAdapter(name="Tesseract-varsayilan"),
    "EasyOCR": lambda: EasyOcrAdapter(name="EasyOCR-tr"),
    "PaddleOCR": lambda: PaddleOcrAdapter(name="PaddleOCR-tr"),
    "RapidOCR": lambda: RapidOcrAdapter(name="RapidOCR-onnx"),
    # DocTR/KerasOCR eklediysen aynı desende buraya bir satır ekle:
    # "DocTR": lambda: DoctrAdapter(name="DocTR-PyTorch"),
}


@st.cache_resource(show_spinner="Motor yükleniyor...")
def motoru_getir(motor_adi: str):
    ic_motor = MOTOR_KURUCULARI[motor_adi]()
    return OnbellekliMotor(ic_motor)


def kisa_motor_adi(tam_ad: str) -> str:

    return tam_ad.split("-")[0]


def yuklenen_dosyayi_kaydet(yuklenen_dosya) -> str:
    hedef_yol = os.path.join(GECICI_DIZIN, yuklenen_dosya.name)
    with open(hedef_yol, "wb") as f:
        f.write(yuklenen_dosya.getbuffer())
    return hedef_yol


# SAYFA AYARI + TASARIM (renk/tipografi/geometrik imza)

st.set_page_config(
    page_title="Belge İşleme · KBB",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --zemin: #0D1B2A;
    --yuzey: #16283C;
    --yuzey-acik: #1E3A54;
    --cizgi: rgba(255,255,255,0.07);
    --lacivert: #2E5C8A;
    --altin: #C9A227;
    --yesil: #3E8E6B;
    --metin: #EDEFF2;
    --metin-soluk: #92A3B8;
    --kirmizi: #C4574A;
}

.stApp { background-color: var(--zemin); color: var(--metin); }

/* Üst araç çubuğu (Deploy şeridi) — Streamlit varsayılan siyahını değiştir */
header[data-testid="stHeader"] {
    background-color: var(--zemin) !important;
    border-bottom: 1px solid var(--cizgi);
}
div[data-testid="stToolbar"] { color: var(--metin) !important; }
div[data-testid="stDecoration"] { display: none; }
[data-testid="stAppDeployButton"] button {
    background-color: var(--yuzey-acik) !important;
    color: var(--metin) !important;
    border: 1px solid var(--cizgi) !important;
}
[data-testid="stMainMenu"] { color: var(--metin) !important; }
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3 { font-family: 'Source Serif 4', serif !important; letter-spacing: -0.01em; }

/* Üst şerit - sade, kurumsal ince ayraç */
.gecmeli-ayrac {
    height: 3px;
    margin: 0 0 2rem 0;
    background: linear-gradient(90deg, var(--altin) 0%, var(--lacivert) 55%, transparent 100%);
    border-radius: 2px;
    opacity: 0.9;
}

/* Başlık bloğu */
.kbb-baslik-blok {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.1rem 1.4rem;
    background: linear-gradient(135deg, var(--yuzey) 0%, var(--yuzey-acik) 100%);
    border: 1px solid var(--cizgi);
    border-left: 4px solid var(--altin);
    border-radius: 10px;
    margin-bottom: 0.9rem;
}
.kbb-baslik-ikon {
    font-size: 2rem;
    line-height: 1;
}
.kbb-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.74rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--altin);
    margin-bottom: 0.2rem;
}
.kbb-title { font-size: 1.85rem; font-weight: 700; color: var(--metin); margin: 0 0 0.25rem 0; }
.kbb-subtitle { color: var(--metin-soluk); font-size: 0.95rem; margin-bottom: 0; }

/* Kartlar */
.kbb-kart {
    background: var(--yuzey);
    border: 1px solid var(--cizgi);
    border-radius: 10px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}
.kbb-kart-baslik {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--metin-soluk);
    border-bottom: 1px solid var(--cizgi);
    padding-bottom: 0.5rem;
    margin-bottom: 0.75rem;
}
.kbb-kart-baslik::before {
    content: "";
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--altin);
    margin-right: 0.5rem;
}

/* Streamlit bileşen yeniden renklendirme */
section[data-testid="stSidebar"] {
    background-color: #0A1420;
    border-right: 1px solid var(--cizgi);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

div[data-testid="stMetric"] {
    background: var(--yuzey);
    border: 1px solid var(--cizgi);
    border-top: 2px solid var(--altin);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div {
    color: var(--metin) !important;
    font-family: 'Source Serif 4', serif !important;
    font-size: 1rem !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.2 !important;
}
div[data-testid="stMetricLabel"] {
    color: var(--metin-soluk);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
div[data-testid="stMetricDelta"] { color: var(--yesil) !important; }

.stButton > button, .stDownloadButton > button {
    background-color: var(--lacivert);
    color: var(--metin);
    font-weight: 600;
    font-size: 0.92rem;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 0.55rem 1.1rem;
    transition: background-color 0.15s ease, border-color 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #3B72A8;
    border-color: var(--altin);
    color: var(--metin);
}
.stButton > button:disabled, .stDownloadButton > button:disabled {
    background-color: var(--yuzey-acik);
    color: var(--metin-soluk);
    border-color: var(--cizgi);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    border-bottom: 1px solid var(--cizgi);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 0.03em;
    color: var(--metin-soluk);
}
.stTabs [aria-selected="true"] {
    color: var(--altin) !important;
    font-weight: 600;
}

textarea, .stTextArea textarea {
    background-color: #0A1420 !important;
    color: var(--metin) !important;
    border: 1px solid var(--cizgi) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
}

[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--cizgi);
}

[data-testid="stFileUploaderDropzone"] {
    background: var(--yuzey) !important;
    border: 1.5px dashed var(--cizgi) !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] {
    background: var(--yuzey);
    border: 1px solid var(--cizgi);
    border-radius: 8px;
}

.stProgress > div > div > div > div { background-color: var(--altin); }

.kbb-rozet {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 5px;
    background: rgba(46,92,138,0.25);
    color: #8FB6DE;
    border: 1px solid rgba(46,92,138,0.5);
    margin: 0 0.25rem 0.25rem 0;
}
</style>
""", unsafe_allow_html=True)

# BAŞLIK
st.markdown('''
<div class="kbb-baslik-blok">
    <div class="kbb-baslik-ikon">📜</div>
    <div>
        <div class="kbb-eyebrow">Konya Büyükşehir Belediyesi</div>
        <div class="kbb-title">Belge İşleme — OCR Kalite Arayüzü</div>
        <div class="kbb-subtitle">Taranmış belgelerden metin çıkar, motorları karşılaştır.</div>
    </div>
</div>
''', unsafe_allow_html=True)
st.markdown('<div class="gecmeli-ayrac"></div>', unsafe_allow_html=True)

# KENAR ÇUBUĞU
with st.sidebar:
    st.markdown('<div class="kbb-kart-baslik">OCR Motorları</div>', unsafe_allow_html=True)

    if "secili_motorlar" not in st.session_state:
        st.session_state["secili_motorlar"] = list(MOTOR_KURUCULARI.keys())

    buton_kol1, buton_kol2 = st.columns(2)
    if buton_kol1.button("Tümünü Seç", use_container_width=True):
        st.session_state["secili_motorlar"] = list(MOTOR_KURUCULARI.keys())
    if buton_kol2.button("Tümünü Kaldır", use_container_width=True):
        st.session_state["secili_motorlar"] = []

    secili_motorlar = st.multiselect(
        "Kullanılacak motorlar (Metin Çıkarma VE Karşılaştırma'da ortak)",
        list(MOTOR_KURUCULARI.keys()),
        default=st.session_state["secili_motorlar"],
        key="secili_motorlar",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div class="kbb-kart-baslik">Önbellek</div>', unsafe_allow_html=True)
    st.caption(
        "Aynı belge + motor kombinasyonu daha önce işlendiyse, "
        "OCR tekrar çalışmaz — sonuç diskten anında okunur."
    )
    if os.path.exists(os.path.join(KOK_DIZIN, "data", "onbellek", "ocr_sonuclari.json")):
        st.markdown('<span class="kbb-rozet">önbellek aktif</span>', unsafe_allow_html=True)

    st.markdown("---")

# ANA İÇERİK — SEKMELER
sekme_cikar, sekme_karsilastir = st.tabs(["📤  Metin Çıkarma", "📊  Karşılaştırma"])

# SEKME 1: Metin Çıkarma
with sekme_cikar:
    kol1, kol2 = st.columns([1, 1], gap="large")

    with kol1:
        st.markdown('<div class="kbb-kart-baslik">1 · Belge</div>', unsafe_allow_html=True)
        belge_dosyasi = st.file_uploader(
            "Belge seç",
            type=["pdf", "jpg", "jpeg", "png", "tiff", "tif"],
            label_visibility="collapsed",
        )

        if belge_dosyasi is not None:
            if st.session_state.get("son_yuklenen_ad") != belge_dosyasi.name:
                st.session_state.pop("sonuclar_metin", None)
                st.session_state.pop("son_belge_yolu", None)
                st.session_state.pop("karsilastirma_satirlari", None)
                st.session_state.pop("karsilastirma_atlanan", None)
                st.session_state["son_yuklenen_ad"] = belge_dosyasi.name
        else:
            st.session_state.pop("son_yuklenen_ad", None)
            st.session_state.pop("sonuclar_metin", None)
            st.session_state.pop("son_belge_yolu", None)
            st.session_state.pop("karsilastirma_satirlari", None)
            st.session_state.pop("karsilastirma_atlanan", None)

        st.markdown('<div class="kbb-kart-baslik" style="margin-top:1rem;">2 · Motorlar</div>', unsafe_allow_html=True)
        if secili_motorlar:
            rozetler = " ".join(f'<span class="kbb-rozet">{m}</span>' for m in secili_motorlar)
            st.markdown(rozetler, unsafe_allow_html=True)
        else:
            st.warning("Kenar çubuğundan en az bir motor seç (veya 'Tümünü Seç'e bas).")
        st.caption("Motor seçimi kenar çubuğundan yapılır — her iki sekmede ortaktır.")

        kuyruk_ile_isle = st.checkbox(
            "🐇 Arka planda RabbitMQ kuyruğu ile işle",
            value=False,
            help="İşaretlersen belge doğrudan burada değil, RabbitMQ kuyruğuna gönderilir. "
                 "En az bir 'python worker.py' çalışıyor olmalı, yoksa sonuç asla gelmez.",
        )

        calistir = st.button(
            "🔍  Metni Çıkar",
            disabled=(belge_dosyasi is None or not secili_motorlar),
            use_container_width=True,
        )

    with kol2:
        st.markdown('<div class="kbb-kart-baslik">Sonuç</div>', unsafe_allow_html=True)

        if calistir:
            belge_yolu = yuklenen_dosyayi_kaydet(belge_dosyasi)
            st.session_state["son_belge_yolu"] = belge_yolu
            st.session_state["sonuclar_metin"] = {}

            if kuyruk_ile_isle:
                # ---- KUYRUK MODU ----
                # OCR'ı burada ÇALIŞTIRMIYORUZ — kuyruk_adaptor.py üzerinden
                # RabbitMQ'ya "şunu şununla işle" mesajı atıyoruz, sonra
                # worker.py'nin ürettiği .txt dosyasının diskte belirmesini
                # BEKLİYORUZ (polling). Gerçek OCR, bu Streamlit sürecinde
                # değil, ayrı bir worker.py sürecinde çalışıyor.
                from infrastructure.kuyruk_adaptor import KuyrukYayinlayici

                belge_adi_govde = os.path.splitext(os.path.basename(belge_yolu))[0]
                cikti_dizini = os.path.join(KOK_DIZIN, "data", "kuyruk_ciktilari")
                os.makedirs(cikti_dizini, exist_ok=True)

                yayinlayici = KuyrukYayinlayici(host="localhost")
                beklenen_ciktilar = {}
                for m_adi in secili_motorlar:
                    cikti_yolu = os.path.join(cikti_dizini, f"{belge_adi_govde}__{m_adi}.txt")
                    if os.path.exists(cikti_yolu):
                        os.remove(cikti_yolu)
                    yayinlayici.gorev_gonder(belge_yolu=belge_yolu, motor_adi=m_adi, cikti_yolu=cikti_yolu)
                    beklenen_ciktilar[m_adi] = cikti_yolu
                yayinlayici.kapat()

                ilerleme = st.progress(0.0, text="Kuyruğa gönderildi, worker.py'nin işlemesi bekleniyor...")
                MAKS_BEKLEME_SN = 300
                baslangic = time.time()

                while True:
                    tamamlanan = {m: yol for m, yol in beklenen_ciktilar.items() if os.path.exists(yol)}
                    oran = len(tamamlanan) / len(beklenen_ciktilar)
                    ilerleme.progress(oran, text=f"{len(tamamlanan)}/{len(beklenen_ciktilar)} motor tamamlandı...")

                    if len(tamamlanan) == len(beklenen_ciktilar):
                        for m_adi, cikti_yolu in tamamlanan.items():
                            with open(cikti_yolu, "r", encoding="utf-8") as f:
                                metin = f.read()
                            st.session_state["sonuclar_metin"][m_adi] = {
                                "metin": metin, "sure": time.time() - baslangic,
                            }
                        ilerleme.progress(1.0, text="Tamamlandı.")
                        break

                    if time.time() - baslangic > MAKS_BEKLEME_SN:
                        st.error(
                            f"{MAKS_BEKLEME_SN} saniyede sonuç gelmedi. "
                            "En az bir 'python worker.py' terminali açık ve çalışır durumda mı kontrol et."
                        )
                        break

                    time.sleep(1)

            else:
                # ---- DOĞRUDAN MOD (kuyruk yok) ----
                ilerleme = st.progress(0.0, text="Başlıyor...")
                for i, m_adi in enumerate(secili_motorlar):
                    ilerleme.progress(i / len(secili_motorlar), text=f"{m_adi} ile taranıyor...")
                    motor = motoru_getir(m_adi)
                    baslangic = time.time()
                    metin = motor.extract_text(belge_yolu)
                    sure = time.time() - baslangic
                    st.session_state["sonuclar_metin"][m_adi] = {"metin": metin, "sure": sure}
                ilerleme.progress(1.0, text="Tamamlandı.")

        if "sonuclar_metin" in st.session_state and st.session_state["sonuclar_metin"]:
            belge_adi = os.path.basename(st.session_state["son_belge_yolu"])

            for m_adi, veri in st.session_state["sonuclar_metin"].items():
                with st.expander(f"📄 {m_adi}  ·  {veri['sure']:.2f} sn", expanded=(len(st.session_state["sonuclar_metin"]) == 1)):
                    st.text_area("Sonuç", veri["metin"], height=220, key=f"txt_{m_adi}", label_visibility="collapsed")
                    st.download_button(
                        f"⬇️ {m_adi} metnini indir",
                        data=veri["metin"],
                        file_name=f"{os.path.splitext(belge_adi)[0]}_{m_adi}.txt",
                        mime="text/plain",
                        key=f"btn_{m_adi}",
                        use_container_width=True,
                    )
        else:
            st.markdown(
                '<div class="kbb-kart" style="text-align:center; color:var(--metin-soluk);">'
                'Bir belge seçip "Metni Çıkar"a bas.</div>',
                unsafe_allow_html=True,
            )

# SEKME 2: Karşılaştırma
with sekme_karsilastir:
    if "son_belge_yolu" not in st.session_state:
        st.info("Önce **Metin Çıkarma** sekmesinde bir belge işle.")
    else:
        kol1, kol2 = st.columns([1, 1], gap="large")

        with kol1:
            st.markdown('<div class="kbb-kart-baslik">Yer-gerçeği</div>', unsafe_allow_html=True)
            st.caption("Belgenin doğru metnini içeren, elle yazılmış .txt dosyası.")
            yer_gercegi_dosyasi = st.file_uploader(
                "Yer-gerçeği TXT",
                type=["txt"],
                label_visibility="collapsed",
                key="gt_uploader",
            )

            karsilastir_tikla = st.button(
                "📊  Seçili Motorları Karşılaştır",
                disabled=(yer_gercegi_dosyasi is None or not secili_motorlar),
                use_container_width=True,
            )
            if not secili_motorlar:
                st.warning("Kenar çubuğundan en az bir motor seç.")

        with kol2:
            if karsilastir_tikla:
                dosya_okuyucu = YerelDosyaOkuyucu()
                gt_yolu = yuklenen_dosyayi_kaydet(yer_gercegi_dosyasi)
                belge_yolu = st.session_state["son_belge_yolu"]
                belge_adi = os.path.basename(belge_yolu)

                satirlar, atlanan = [], []
                ilerleme = st.progress(0.0, text="Başlıyor...")

                for i, motor_adi in enumerate(secili_motorlar):
                    ilerleme.progress((i) / len(secili_motorlar), text=f"{motor_adi} çalışıyor...")
                    try:
                        motor = motoru_getir(motor_adi)
                        servis = KaliteOlcumServisi(ocr_motoru=motor, dosya_okuyucu=dosya_okuyucu)
                        sonuc = servis.belgeyi_degerlendir(
                            belge_adi=belge_adi, dosya_yolu=belge_yolu, yer_gercegi_yolu=gt_yolu,
                        )
                        satirlar.append({
                            "belge": sonuc.belge_adi,
                            "yöntem": sonuc.yontem_adi,
                            "doğruluk": sonuc.dogruluk_orani,
                            "kayıp_oran": sonuc.kayip_orani,
                            "tr_hata": sonuc.turkce_karakter_hatasi,
                            "süre(sn)": sonuc.sure_saniye,
                        })
                    except Exception as hata:
                        atlanan.append(f"{motor_adi}: {hata}")

                ilerleme.progress(1.0, text="Tamamlandı.")
                st.session_state["karsilastirma_satirlari"] = satirlar
                st.session_state["karsilastirma_atlanan"] = atlanan

            if "karsilastirma_satirlari" in st.session_state:
                satirlar = st.session_state["karsilastirma_satirlari"]
                atlanan = st.session_state.get("karsilastirma_atlanan", [])

                if atlanan:
                    st.warning("Atlanan motorlar:\n\n" + "\n".join(f"- {a}" for a in atlanan))

                if satirlar:
                    en_iyi = max(satirlar, key=lambda r: r["doğruluk"])
                    o1, o2, o3 = st.columns(3)
                    o1.metric("En yüksek doğruluk", kisa_motor_adi(en_iyi["yöntem"]), f"%{en_iyi['doğruluk']:.1f}")
                    o2.metric("En düşük kayıp oran", kisa_motor_adi(min(satirlar, key=lambda r: r["kayıp_oran"])["yöntem"]))
                    o3.metric("En hızlı", kisa_motor_adi(min(satirlar, key=lambda r: r["süre(sn)"])["yöntem"]))

                    df = pd.DataFrame(satirlar)
                    df_gosterim = df.copy()
                    df_gosterim["doğruluk"] = df_gosterim["doğruluk"].map(lambda v: f"%{v:.1f}")
                    df_gosterim["kayıp_oran"] = df_gosterim["kayıp_oran"].map(lambda v: f"%{v:.1f}")
                    df_gosterim["süre(sn)"] = df_gosterim["süre(sn)"].map(lambda v: f"{v:.2f}")

                    st.dataframe(df_gosterim, hide_index=True, use_container_width=True)
                else:
                    st.error("Hiçbir motor sonuç üretemedi.")