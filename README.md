# VLF Noise Scout

**Ev yapımı, iki kanallı bir doğal radyo (VLF) alıcı istasyonu — canlı web yayınıyla.**
Ankara'da, bir apartman dairesinde, bir paspas sopası ve ~700 TL'lik elektronik
parçayla kuruldu.

> **English:** A homemade dual-channel VLF natural-radio receiving station with a
> live web stream. Built in a flat in Ankara, Türkiye, using a metal mop handle
> as the main E-field antenna and about €20 of components.
> See [README.en.md](README.en.md).

> **📡 Canlı yayın sonlandı:** İstasyonun canlı yayını **7 Ağustos 2026**
> tarihinde sonlandırılmıştır. Kod ve dokümanlar kalıcıdır; istasyonu kendi
> donanımınızla her zaman kurabilirsiniz.
>
> **The live stream has ended:** the station went offline on
> **7 August 2026**. The code and docs stay; you can build your own station
> any time.

---

## Ne yapıyor?

Yıldırımların ürettiği radyo darbeleri (*sferic*), gece iyonosferde seken
kuyruklu sinyaller (*tweek*) ve nadir *whistler*'lar 250 Hz – 12 kHz arasında,
yani **ses bandında** yaşar. Bu yüzden bu frekanslar için klasik bir radyo
gerekmez: anten sinyali doğrudan bilgisayarın ses kartıyla örneklenir.

Bu istasyon şunları yapar:

- **İki bağımsız kanal:** metal sopa (ana anten) ve 10 cm'lik referans prob
- **Adaptif gürültü iptali:** referans probun duyduğu ev içi parazit, ana
  kanaldan çıkarılır (frekans alanında NLMS)
- **Canlı web yayını:** ham ve temiz sesin kesintisiz karşılaştırması
- **Olay modlu waterfall:** sabit uğultu öğrenilip silinir, ekranda yalnızca
  yeni darbeler kalır
- **Geriye dönük kayıt:** son 60 saniye sürekli tamponlanır; duyduktan sonra
  kaydedebilirsiniz
- **Canlı yıldırım haritası:** duyulan sferic'lerin kaynağını gösteren gömülü
  harita (veri: [Blitzortung.org](https://www.blitzortung.org/) gönüllü ağı)
- **Uzak verici taraması:** 96 kHz örneklemede bilinen VLF vericileri için SNR
  ölçümü — sistemin gerçekten çalıştığını şansa bırakmadan kanıtlar

### Ölçülmüş sonuç

3 Ağustos 2026, gündüz, Ankara — 60 saniyelik tarama:

| İstasyon | Frekans | SNR | Durum |
|---|---:|---:|---|
| Alpha F1 🇷🇺 | 11.90 kHz | 12.3 dB | **GÖRÜLDÜ** |
| Alpha F2 🇷🇺 | 12.65 kHz | 11.7 dB | **GÖRÜLDÜ** |
| Alpha F3 🇷🇺 | 14.88 kHz | 8.6 dB | zayıf iz |
| HWU 🇫🇷 | 21.75 kHz | 8.0 dB | zayıf iz |
| GBZ 🇬🇧 | 19.58 kHz | 6.9 dB | zayıf iz |
| DHO38 🇩🇪 | 23.40 kHz | 6.6 dB | zayıf iz |
| TBB 🇹🇷 | 26.70 kHz | 6.6 dB | zayıf iz |
| NAA 🇺🇸 | 24.00 kHz | 5.8 dB | zayıf iz |
| ICV 🇮🇹 | 20.27 kHz | 5.1 dB | zayıf iz |

Alpha (RSDN-20) Rusya'nın seyrüsefer sistemi; diğerleri donanmaların denizaltı
haberleşme vericileri. Hepsi kulağın üstünde — duyulmaz, **ölçülür**.

---

## Donanım

### Malzeme listesi

| Parça | Adet | Not |
|---|---:|---|
| 2N5457 JFET (TO-92) | 4 | J201 muadili; 2 kanal + yedek |
| TL072 (DIP-8) | 2 | çift op-amp, 1 yedek |
| 8 pinli DIP soket | 2 | çip lehimlenmez, sokete takılır |
| Direnç seti (1/4W) | 1 | 20k, 510Ω, 100k, 1k, 1M, 10M değerleri kullanıldı |
| 10 MΩ direnç | 4 | gate biası (2 adet seri = 20 MΩ) |
| 100k çok turlu trimpot (3006) | 2 | kazanç ayarı |
| 1 µF film kondansatör | 6 | kuplaj / source bypass |
| 470 nF film | 2 | geri besleme |
| 100 nF MLCC | 2 | besleme dekuplajı |
| 4.7 nF film | 2 | kademeler arası kuplaj |
| 100 µF elektrolitik | 4 | besleme + Vmid filtresi |
| 8'li AA pil yuvası + piller | 1 | **12 V, sadece pil** |
| Delikli plaket 5×10 cm | 2 | biri VLF için |
| 3.5 mm stereo jak (lehim tipi) | 1 | PC hat girişine |
| Metal sopa (Vileda vb.) | 1 | ana anten |
| İnce tel ~10–40 cm | 1 | referans prob |
| Multimetre | 1 | **zorunlu** |

### Devre (kanal başına, iki kez kurulur)

```
KADEME 1 — JFET ön yükselteç              KADEME 2 — TL072 kazanç katı
                V+ (12V)                       C4'ten ──┬──[+ TL072]──┬── 1k ── 1µF ──► Line In
                 │                                      │            │
               20k (R7)                              100k (R12)      ├── 100k trimpot ──┐
                 │                                      │            │                  │
                 ├──── 4.7nF (C4) ──► KADEME 2        Vmid        [− giriş] ────────────┘
               Drain                                                 │
             ┌───┴───┐                                               └── 1k ── 470nF ── Vmid
 Anten ─1M───│ 2N5457│                    ORTAK BESLEME
        │    └───┬───┘                       V+ ──┬─ 10k ─┬─ 10k ─ GND     Vmid = V+/2
      20M      Source                             │       │
    (2x10M)      ├── 510Ω ── GND               100µF     Vmid ── 100µF ── GND
        │        └── 1µF  ── GND                  │
       GND                                       GND      V+ ── 100nF ── GND (TL072'ye yakın)
```

**Kazanç bütçesi:** JFET katı ≈ +23 dB, TL072 katı ≈ +40 dB (trimpotla ayarlı) →
toplam ≈ **+63 dB**, 50 Hz'de ≈ 0 dB. Şebeke, banda göre ~60 dB bastırılmış gelir.

**Bias kuralı:** drain gerilimi V+'ın %40–70'i olmalı (12 V'ta 4.8–8.4 V).
Düşükse source direncini büyüt, V+'a yapışıksa küçült ve JFET bacaklarını kontrol et.

### Kurulum sırası

1. Besleme + Vmid → **ölç** (V+ ≈ 12–13 V, Vmid ≈ yarısı)
2. Kanal 1 Kademe 1 → **drain gerilimini ölç**
3. Kanal 1 Kademe 2 → çıkış DC'si ≈ Vmid
4. Jak + anten → `probe_check.py` ile canlı test
5. **Kanal 1 çalışmadan Kanal 2'ye geçme**
6. Kanal 2 → stereo doğrulama (korelasyon +1.000 OLMAMALI)

Adım adım kurulum rehberi: [`docs/PERTINAKS.md`](docs/PERTINAKS.md)
(English: [`docs/PERTINAKS.en.md`](docs/PERTINAKS.en.md)).

### Güvenlik

- Bu bir **alıcıdır**, verici değildir; dinlemek lisans gerektirmez
- Anten **bina içinde** kalır — çatıya, balkondan dışarı uzatılmaz
- Priz fazına, nötre, topraklamaya, kalorifere, su borusuna **bağlanmaz**
- **Sadece pil** ile beslenir; adaptör kullanmak anahtarlama gürültüsünü
  doğrudan banda bindirir
- Fırtına sırasında devreye fiziksel müdahale edilmez
- Bu bir yıldırım koruma/tespit sistemi **değildir**

---

## Yazılım

```
server/vlf_stream/     ses yakalama, DSP, MP3 yayını, FastAPI sunucu
server/tools/          probe_check.py · verici_avi.py · canli_seviye.py · compile_translations.py
web/               istasyon arayüzü (17 dil · açık/karanlık tema)
hardware/          BOM, devreye alma kontrol listesi
docs/              kurulum rehberleri, deney protokolü
```

### Kurulum

```bash
cd server
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ffmpeg gerekir:  winget install Gyan.FFmpeg   |   apt install ffmpeg
```

### Çalıştırma

Windows'ta en kolayı: depo kökündeki **`start-server.bat`** dosyasına çift
tıklamak. İlk çalıştırmada sanal ortamı kurar, aygıt listesini gösterir,
numarayı sorar ve sunucuyu başlatır.

Elle çalıştırmak için:

```bash
export VLF_DEVICE=1              # Windows: $env:VLF_DEVICE = "1"
uvicorn vlf_stream.server:app --host 0.0.0.0 --port 8000
```

Aygıt numarası için: `python -c "import sounddevice; print(sounddevice.query_devices())"`
Numaralar Windows'ta aygıt açılıp kapandıkça **değişir**, her seferinde kontrol edin.

Donanımsız denemek için: `VLF_MOCK_MODE=1`

### Teşhis araçları

```bash
python tools/probe_check.py --device 1 --seconds 20 --out kayit.wav
python tools/canli_seviye.py --device 1          # canlı seviye/kırpılma monitörü
python tools/verici_avi.py --device 1 --seconds 60 --json ../data/son_tarama.json
```

`verici_avi.py --json` çıktısı web arayüzündeki verici tablosunu besler.
Tarama için Windows ses girişini **96 kHz**'e almak gerekir (48 kHz'te tavan
24 kHz olur ve üst vericiler menzil dışında kalır).

### Çok dilli arayüz, tema ve font

Arayüz **17 dilde** çalışır: Türkçe, English, Español, 中文, 日本語, Tiếng Việt,
Deutsch, Français, Русский, Azərbaycanca, Қазақша, Монгол, தமிழ், Kurmancî,
Zazakî, Maya t'aan ve فارسی (sağdan sola). Sağ üstteki **açılır menüden** dil
seçilir; tercih tarayıcıda saklanır, hiç seçilmemişse tarayıcı dili otomatik
algılanır. **Açık / karanlık tema** düğmesi aynı şekilde hatırlanır; elle
seçim yapılmamışsa sistem tercihini izler. Metinler **Open Sans** ile dizilir;
şelale/spektrum ekranları her iki temada da koyu kalır (ölçüm ekranı).

Çeviriler gettext (.po/.mo) biçimindedir:

```
web/locales/<kod>/LC_MESSAGES/messages.po   çeviri kaynağı (elle düzenlenir)
web/locales/<kod>/LC_MESSAGES/messages.mo   derlenmiş katalog
web/locales/<kod>.json                      arayüzün çalışırken yüklediği paket
web/locales/messages.pot                    yeni dil için şablon
```

.po dosyalarını düzenledikten sonra .mo ve .json paketlerini tazeleyin:

```bash
python server/tools/compile_translations.py web/locales --sync-po
```

Yeni dil eklemek için: `messages.pot`'tan kopyalayın, 93 anahtarı çevirin,
`web/locales/<kod>/LC_MESSAGES/messages.po` olarak kaydedin; `web/i18n.js`
ve `index.html` dil listesine kodu ekleyin; `--sync-po` ile derleyin.
CI, her dilde anahtar kümesinin eksiksiz olduğunu ve .mo/.json'un .po ile
senkron olduğunu doğrular.


## Canlı yayın nasıl çalışıyor?

GitHub **kodu** barındırır, canlı sesi değil — ses her zaman istasyonun
bulunduğu bilgisayardan gelir:

```
GitHub Pages (arayüz)  ←─ ziyaretçi ─→  Cloudflare Tunnel ─→ ev PC'si
                                                              ├ uvicorn :8000
                                                              └ devre → Line In
```

Ayrıntılı adımlar: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
Tünel kapalıyken arayüz yine açılır; verici tablosu ve tüm açıklamalar
`web/transmitters.json` üzerinden statik olarak çalışır, yalnızca canlı ses olmaz.

---

## Süreç: neler yaşandı

Bu bölüm, aynı şeyi kurmak isteyenlerin zaman kaybetmemesi için yazıldı.
Toplam süre: **iki hafta**, ve zamanın çoğu devre tasarımına değil, **temas
arızalarına** gitti.

### 1. Tasarımdaki kazanç hatası (kurulmadan önce yakalandı)

İlk devre tek bir JFET'i doğrudan ses kartına bağlıyordu. Kazanç bütçesi
hesaplandığında toplam ≈ **0 dB** çıktı: anten/gate kapasitif bölücü −6 dB,
JFET katı +15 dB, drain–Line-In bölücüsü −6…−10 dB. Klasik doğal radyo alıcıları
60–80 dB ile çalışır. Yani devre kurulsaydı hiçbir şey duyulmayacaktı.
İki kademeli ön uca geçildi (+63 dB).

### 2. Metrik yalan söylüyordu

Web arayüzündeki "gürültü azaltma" değeri, bant filtresinin işini adaptif
filtreye yazıyordu: referans prob **tamamen sessizken** bile 46.1 dB "iptal"
gösteriyordu. Ayrıştırıldı — artık *adaptif iptal* ve *bant filtresi* ayrı
raporlanır, aynı test 0.0 dB der.

### 3. Neden Raspberry Pi değil?

Proje başlangıçta Raspberry Pi ile planlanmıştı, ama Pi için alınan C-Media
(CM108) USB ses kartı **mono** çıktı: `arecord -D plughw:...` "Stereo"
yazıyordu — `plug` katmanı mono sesi kopyalayıp iki kanal gibi gösteriyor.
Gerçeği `cat /proc/asound/cardX/stream0` söyler. Bu proje iki bağımsız kanal
olmadan çalışmaz; USB kart yeterli olmayınca **PC'nin dahili stereo hat
girişine (mavi jak) geçildi** ve tüm sistem PC üzerinde koşuyor. Depoda başka
hiçbir yerde Pi geçmez — burası tarihsel not.

### 4. Windows girişi açtırmak

Hat Girişi başta hiç veri üretmedi: `-200.0 dBFS`, yani **tam sıfır**. Sırayla:
girişe fiziksel olarak fiş takılı değilse Realtek jak algılaması aygıtı
"Takılı değil" bırakıyor ve Windows veri yolu açmıyor; `mmsys.cpl` → Kayıt →
devre dışı aygıtları göster → Etkinleştir → Düzeyler 100. Aygıt yalnızca
WDM-KS altında görünüyorsa henüz tam etkin değildir.

### 5. Breadboard cehennemi (asıl zaman kaybı)

Sistem defalarca öldü ve dirildi. Bulunan arızalar, sırasıyla:

- **İçi kopuk jumper kablosu** — dışarıdan sapasağlam, bip testinden bile
  bazen geçiyordu
- **Yarı oturmuş DIP soket bacağı** — DC ölçümleri normal görünürken AC sinyali
  geçirmiyor
- **Boşta kalan kondansatör ucu** — devre "çalışıyor" ama dekuplaj yok
- **Jak tellerinin yer değiştirmesi** — SOL ve SAĞ karışmıştı; günlerce
  "kanal ölü" sanılan şey, boş uca yapılan ölçümlerdi
- **TL072'nin bir yarısının ölmesi** — DC'si normal, AC yükseltmiyor

Teşhis yöntemi olarak şu ikisi çok işe yaradı: **tırnak testi** (kayıt sürerken
bir düğüme tırnak sürtüp çıkışta sıçrama aranır — vücut zayıf bir sinyal
kaynağıdır) ve **Windows Kayıt sekmesindeki yeşil seviye çubuğu** (Python
çalıştırmadan, saniyeler içinde "bu nokta canlı mı" sorusunu cevaplar).

**Sonuç:** breadboard prototip içindir, yaşam yeri değildir. Sistem delikli
plakete lehimlenip kutuya alındıktan sonra temas arızaları bitti.

### 6. Kırpılma tuzağı

Kazanç yükseltilince şebeke sinyali ADC'yi doldurup **sahte harmonikler**
üretiyor ve zayıf uzak vericileri boğuyordu. Üç ayrı taramanın karşılaştırması:

| Ayar | SOL RMS | Kırpılma | Alpha F2 |
|---|---:|---:|---:|
| Yüksek kazanç | −11.6 dBFS | %0.85 | 13.9 dB |
| Düşük kazanç | −27.5 dBFS | %0.00 | 5.5 dB |
| **Orta, kırpılmasız** | **−25.8 dBFS** | **%0.00** | **11.7 dB + 8 istasyon** |

Yani "daha çok kazanç" da "daha az kazanç" da yanlış; doğru olan **kırpılma
sınırının hemen altı**. Bunu bulmak için `canli_seviye.py` yazıldı — trimpotu
çevirirken ekranda anlık RMS/kırpılma görülür, test komutu tekrarlamak gerekmez.

### 7. Gündüz/gece gerçeği

Gündüz, şehir içinde, kapalı mekânda sferic duymak zordur; dakikada 1–2 çıtırtı
normaldir. Tweek **yalnızca gece** oluşur — "J" harfini gündüz aramak boşunadır.
`verici_avi.py` tam bu yüzden yazıldı: gökyüzü sessizken bile 7/24 yayında olan
vericilerle sistemin sağlığı ölçülebilir.

---

## Kaynaklar ve dürüstlük notu

**Bu proje bir ilk değildir.** VLF doğal radyo alıcıları onlarca yıldır
yapılıyor; iki kanallı/referans problu adaptif gürültü iptali de bilinen bir
tekniktir (aktif gürültü kontrolünde standart, VLF'te de uygulanmıştır). Buradaki
katkı yeni bir yöntem değil; **ucuz ev malzemesiyle kurulabilir, adım adım
belgelenmiş ve ölçümle doğrulanmış** bir uygulama.

Beslenilen kaynaklar ve fikirler:

- **Doğal radyo alıcı mimarisi:** klasik E-alan probu + yüksek empedanslı JFET
  tampon + op-amp kazanç katı düzeni (Stephen P. McGreevy'nin VLF alıcı
  çalışmaları ve genel "mini whip" aktif anten literatürü)
- **Adaptif gürültü iptali:** Widrow-Hoff LMS/NLMS ailesi; burada frekans
  alanında, transient korumalı bir varyantı kullanıldı (sferic'in kendisi
  filtreye "öğretilmesin" diye darbe anında adaptasyon dondurulur)
- **Yıldırım konum verisi:** Blitzortung.org gönüllü ağı (ticari olmayan
  kullanım için açık); arayüzde harita olarak gömülüdür
- **VLF verici listeleri:** Alpha/RSDN-20 ve MSK deniz haberleşme
  vericilerinin kamuya açık frekans kayıtları
- **Yapay zekâ desteği:** Projenin ilk kod tabanı bir dil modeline yazdırıldı.
  Sonra ikinci bir modelle (Claude) baştan incelendi; yukarıdaki kazanç hatası
  ve yalancı metrik bu incelemede bulundu. Devre revizyonu, teşhis araçları
  (`probe_check.py`, `canli_seviye.py`, `verici_avi.py`), web arayüzü ve bu
  belge de aynı süreçte, karşılıklı çalışarak üretildi. Bütün ölçümler, lehimler
  ve arıza avı gerçek donanım üzerinde elle yapıldı.

Kod bir dil modeli yardımıyla yazıldığı için **körü körüne güvenilmemeli**;
DSP tarafı birim testleriyle (`server/tests/`) doğrulandı, donanım tarafı ise
ölçümle. Aynı şüpheciliği siz de uygulayın.

## Lisans

MIT — bkz. [LICENSE](LICENSE).
