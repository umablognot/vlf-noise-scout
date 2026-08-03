# Donanım (v2 — kazanç düzeltmeli)

İki kanal **elektriksel olarak aynı** olmalıdır. Sol kanal ana VLF antenidir;
sağ kanal odadaki yerel paraziti ölçen küçük referans probudur.

## v1'de neden ses gelmiyordu

İlk sürüm tek J201'i doğrudan ses kartının Line-In girişine bağlıyordu. Bu
zincirin kazanç bütçesi ölçüldüğünde:

| Kalem | Katkı |
|---|---:|
| Anten (≈10–20 pF) ile gate düğümü (≈15 pF) arasındaki kapasitif bölücü | −6 dB |
| J201 common-source, bypass edilmemiş 2.2 kΩ source direnci, yüksüz | +15 dB |
| 22 kΩ drain ile Line-In giriş direnci (10–20 kΩ) arasındaki bölücü | −6…−10 dB |
| **Toplam** | **≈ 0 dB** |

Karşılaştırma için: klasik doğal radyo alıcıları (Romero E202, INSPIRE,
McGreevy) 60–80 dB kazançla çalışır. Wenzel'in tek-JFET "Super Tiny" tasarımı
da **mikrofon** girişine takılır; mic girişi Line-In'den 30–40 dB daha
hassastır. Bu proje stereo gerektirdiği için Line-In şart, dolayısıyla kazancın
devrede üretilmesi gerekiyor.

v2 iki değişiklik yapar:

1. JFET'in source direncini kısmen bypass ederek bandın içinde +23 dB kazanç
   alır (50 Hz'de bilerek daha az kazanç bırakır).
2. Arkasına bir TL072 katı koyar: yüksek giriş empedansı sayesinde drain /
   Line-In bölücü kaybı tamamen ortadan kalkar, üstüne ayarlanabilir +40 dB
   gelir.

Bant içi toplam: **≈ +63 dB**, trimpot ile ~+27 dB'ye kadar indirilebilir.
50 Hz'de toplam: **≈ 0 dB**. Yani şebeke, banda göre 60 dB bastırılmış olarak
ADC'ye ulaşır — kırpılma riski v1'e göre çok daha düşüktür.

## Kanal şeması

Aşağıdaki blok **kanal başına** birebir tekrarlanır. `V+` ve `Vmid` iki kanalda
ortaktır.

```text
   KADEME 1 — 2N5457 yüksek empedanslı ön yükselteç
   ================================================

                             V+
                              │
                            20k (R7)
                              │
                              ├──────── C4 4.7nF ────► KADEME 2
                              │
                            Drain
                          ┌───┴───┐
    Anten ── 1M (R1) ──── │2N5457 │
                    │     │  Q1   │
                  20M     └───┬───┘
                (2x10M)    Source
                   (R3)       │
                    │         ├──── 510Ω (R5) ──── GND
                   GND        │
                              └──── 1µF (C5) ───── GND


   KADEME 2 — TL072 kazanç katı (IC'nin bir yarısı)
   =================================================

                              ┌───────────┐
     C4'ten ────────────┬─────┤+          │
                        │     │   TL072   ├──┬── 1k (R15) ── C8 1µF ──► TRS
                     100k(R12)│           │  │
                        │   ┌─┤−          │  │
                       Vmid │ └───────────┘  │
                            │                │
                            ├── 1k (R13) ── 470nF (C7) ── Vmid
                            │
                            └── 100k trimpot (R14) ───────┘
```

`R14` çıkıştan `−` girişe geri besleme yapar; `R13`+`C7` ise `−` girişten
`Vmid`'e gider. Kazanç bant içinde `1 + R14/R13`, DC'ye doğru 1'e düşer —
50 Hz bastırması buradan gelir.

## Ortak besleme ve orta nokta (Vmid)

```text
   V+ ──┬── 10k (R20) ──┬── 10k (R21) ── GND
        │               │
     100µF (C11)      Vmid
        │               │
       GND           100µF (C10)
                        │
                       GND

   V+ ── 100nF (C3) ── GND     (TL072'nin besleme bacaklarına yakın)
```

`Vmid`, tek beslemeli TL072 için yapay sıfır noktasıdır. TRS sleeve **gerçek
GND'ye** bağlanır, `Vmid`'e değil.

## Besleme seçimi

| Seçenek | Gerilim | Ömür (≈3.2 mA çekiş) | Not |
|---|---|---|---|
| 8×AA pil yuvası | 12 V | ~30 gün | **7–10 günlük yayın için önerilen** |
| 9 V blok pil | 9 V | ~6 gün | Prototip için yeterli; TL072 bu gerilimde datasheet'in ±5 V alt sınırının altında kalır |
| 2×9 V seri | 18 V | ~6 gün | Spec içinde ama ömür kısa |

Tek 9 V ile kalıcı olarak çalışacaksan TL072 yerine **TL062** (düşük güç, JFET
girişli) veya **NE5532** (min ±3 V) kullan. Kademe 1 zaten +23 dB kazanç
verdiğinden bu op-amp'lerin gürültü farkı antene indirgendiğinde önemsizdir.

Analog devreyi **asla** PC'nin USB 5 V hattından besleme. Anahtarlamalı adaptör
gürültüsü doğrudan banda biner.

## Bias kontrolü — JFET toleransı geniştir

2N5457'nin IDSS'i 1–5 mA arasında değişir. Devreyi kurduktan sonra drain
gerilimini ölç:

- **Vd, V+ değerinin %40–70'i arasında olmalı.** (9 V'ta 3.6–6.3 V; 12 V'ta
  4.8–8.4 V.)
- Vd çok düşükse (JFET fazla akım çekiyor): `R5`'i büyüt (1 kΩ, gerekirse
  2.2–4.7 kΩ).
- Vd V+'a yapışıksa (akım yok): önce JFET bacak dizilişini kontrol et;
  bacaklar doğruysa JFET'i yedeğiyle değiştir.

Bu kontrolü **iki kanalda ayrı ayrı** yap. İki kanalın aynı Vd'de olması
gerekmez; NLMS kazanç farkını kendisi öğrenir.

## Stereo çıkış

```text
TRS uç / Tip       Ana anten kanalının C8 sonrası
TRS halka / Ring   Referans kanalının C8 sonrası
TRS gövde / Sleeve Ortak GND (Vmid değil)
```

`C5` ve `C8` için film veya bipolar kapasitör önerilir. Polar elektrolitik
kullanılacaksa pozitif ucu daha yüksek DC potansiyelli tarafa gelmelidir.

## Gate direnci (R3)

Bu istasyonda kanal başına **2× 10 MΩ seri = 20 MΩ** kullanıldı; 10 MΩ en
kolay bulunan yüksek değerdir. Tek 22 MΩ pratikte aynı davranır. Daha yüksek
değerler (47 MΩ) alt bant tepkisini biraz genişletir ama perakende bulması
zordur.

Seri bağlarken lehim noktalarını temiz tut; bu empedans seviyesinde kir ve nem
gate kaçağı yaratır.

## JFET bacakları

Aynı parça adı bile üretici ve kılıfa göre farklı bacak dizilişiyle gelebilir.
Kart üzerindeki fiziksel yönü bu dokümandan tahmin etme; satın aldığın
parçanın veri sayfasından gate/drain/source uçlarını doğrula. Buradaki
2N5457'lerde diziliş, düz yüz sana bakarken soldan sağa D–S–G çıktı.

Alternatif JFET'ler (J201, BF245B, 2SK170) çalışır fakat IDSS'leri çok
farklıdır; `R5`'i yukarıdaki Vd kuralına göre yeniden seçmen gerekir.

## Mekanik düzen

- Yüksek empedanslı gate bağlantıları kısa tutulmalı.
- Gate düğümündeki lehim artığı/akı temizlenmeli.
- Kademe 1'i antenin tabanına yerleştir; kademe 2 aynı kutuda olabilir.
- Kutudan ses kartına kadar **ekranlı** kablo kullan; ekran sleeve GND'ye.
- PC kasasını, güç kablolarını ve monitörü ana antenden 2–3 metre uzağa koy.
- Metal sap ile topraklı folyo ekran arasında en az 10–20 cm bırak.

## Neden 1 MΩ giriş direnci?

Gate akımını ve küçük statik boşalmaları sınırlar. Ayrıca JFET'in giriş
kapasitansı ve devre stray'i (toplam ≈15 pF) ile birlikte ~10 kHz civarında
bir kutup oluşturur — yani bandın üst ucunu zaten yumuşatır. Bu direnç yıldırım
veya dış anten güvenliği **sağlamaz**.

## Güvenlik

- Bu bir yıldırım yakalama/paratoner sistemi değildir.
- Anteni bina dışına, çatıya veya balkondan dışarı uzatma.
- Priz fazı, nötr, koruma toprağı, elektrik panosu, kalorifer ve su borusuna
  bağlama.
- Fırtına sırasında devreye fiziksel müdahale etme.
