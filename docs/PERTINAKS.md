# Pertinaks kurulum rehberi — kalıcı ve 96 kHz'e hazır istasyon

> English version: [PERTINAKS.en.md](PERTINAKS.en.md)

Breadboard prototip içindir, yaşam yeri değildir: bu projede haftalar süren
arızaların neredeyse tamamı temas sorunlarından çıktı (içi kopuk jumper, yarı
oturmuş soket bacağı, yer değiştiren jak telleri). Kalıcı istasyon lehimli
delikli plakete (pertinaks) kurulur ve kutuya alınır.

Devrenin şeması ve parça değerleri için [`hardware/README.md`](../hardware/README.md),
adım adım elektriksel doğrulama için [`hardware/commissioning.md`](../hardware/commissioning.md).
Bu rehber yalnızca fiziksel kurulumu ve 96 kHz ayarını anlatır.

---

## 1. Malzeme

Devre parçalarına ek olarak:

- 5×10 cm delikli plaket (tek plaket iki kanala yeter)
- 8 pinli DIP soket ×1 — **TL072 lehimlenmez, sokete takılır**
- Bara teli: tek damarlı çıplak tel (V+, GND, Vmid hatları için)
- İzoleli ince tel (bara üzerinden geçen bağlantılar için)
- Kablo bağı 3–4 adet (dış kabloların gerginlik alması için)
- Havya, lehim, yan keski, multimetre

Kesilen direnç bacaklarını atma — kısa köprüler için birebir.

## 2. Üç dakikalık lehim okulu

1. Havya ucu temiz ve kalaylı olsun (ıslak süngerde sil, ucuna az lehim yedir).
2. Ucu **hem pada hem bacağa** aynı anda değdir, 2 saniye ısıt.
3. Lehimi havyaya değil **birleşim noktasına** değdir; kendiliğinden aksın.
4. Havyayı çek, 2–3 saniye kıpırdatma.
5. Doğru lehim **parlak ve koni biçimlidir.** Mat/top gibi = soğuk lehim → tekrar ısıt.
6. Her 5–6 lehimde bir, multimetre bip kademesiyle **komşu padlara kısa devre
   kontrolü** yap — pertinaksın bir numaralı hatası lehim köprüsüdür.
7. Bacakları lehimden **sonra** kes.

**Statik:** JFET'leri en son tak; her ele alışta önce topraklı bir metale
(kalorifer peteği) dokun. TL072 sokete gireceği için lehim ısısından korunur.

## 3. Yerleşim planı

Plaketi yatay tut (uzun kenar önde). Bölgeler soldan sağa, sinyal akışı
yönünde: **sol = besleme · orta-sol = JFET katları · merkez = TL072 soketi ·
sağ = çıkışlar.** Kanal 1 ön yarıda, Kanal 2 arka yarıda.

```
   ARKA KENAR  ────────────────────────────────────────────
   [K2: Q2 R7b R5b C5b R1b R3b C4b]       [K2 trimpot]
   V+ barası ═══════════════════════════════════════════
   Vmid barası ═════════════╗  ┌──────┐  ═══════════════
   GND barası ══════════════║══│SOKET │══════════════════
                            ║  │TL072 │   [R15 C8]→ JAK-SOL
   [K1: Q1 R7 R5 C5 R1 R3 C4]  └──────┘  [R15b C8b]→ JAK-SAĞ
   [pil telleri][C10 C11 R20 R21]         [K1 trimpot]
   ÖN KENAR  ──────────────────────────────────────────────
```

Üç kural:

1. **Üç bara teli** (V+, GND, Vmid) plaketi boydan boya geçsin; her parça en
   yakın noktadan baraya lehimlenir, uzun zikzak bağlantı olmaz. Bara
   üzerinden geçmek zorunda kalan her bağlantı **izoleli** telle yapılır.
2. **Soket merkezde**, çentik yönünü plaket üzerine kalemle çiz — çip her
   takılışta o çizgiye bakılır. TL072 pin haritası:

   | Pin | İşlev | | Pin | İşlev |
   |---|---|---|---|---|
   | 1 | OUT A (Kanal 1 çıkış) | | 8 | V+ |
   | 2 | IN− A | | 7 | OUT B (Kanal 2 çıkış) |
   | 3 | IN+ A | | 6 | IN− B |
   | 4 | GND | | 5 | IN+ B |

3. Dışarı giden her tel (pil, jak, ANT1, ANT2) plaket kenarındaki bir
   **delikten önce geçirilip** sonra lehimlenir ve kablo bağıyla plakete
   sabitlenir — çekme kuvveti lehime değil plakete gelir.

Lehime başlamadan bütün parçaları plakete **lehimsiz** yerleştirip fotoğraf
çek. Lehimden sonra kaydırmak yok.

## 4. Lehim sırası ve kontrol noktaları

Breadboard prototipin varsa en sona kadar bozma; parçaları kademe kademe taşı
ki her adımda çalışan bir referansın olsun. Hedef değerler
[`commissioning.md`](../hardware/commissioning.md) ile aynıdır.

☐ **4.1** DIP soketi lehimle (çentik yönünü çiz). İçi boş kalsın.

☐ **4.2** Besleme: pil telleri (delikten geçir) → V+ ve GND baraları.
C11, R20, R21, C10.
**✔ KN1:** pil tak, anahtar aç: V+ ≈ 12–13 V, Vmid ≈ yarısı. Anahtarı kapat.

☐ **4.3** Kanal 1 Kademe 1: Q1 (D-S-G yönünü veri sayfasından doğrula), R7,
R5, C5, C4, R1, R3 (2×10M seri). ANT1 telini delikten geçirip R1'in ucuna
lehimle.
**✔ KN2:** anahtar aç: drain = V+'ın %40–70'i (12 V'ta 4.8–8.4 V).

☐ **4.4** Kanal 1 Kademe 2: soket pin 8 → V+ ve pin 4 → GND köprüleri,
C3 100nF sokete yakın (pin 8 padı ile GND arası), C4 → pin 3, R12
(pin 3 → Vmid), trimpot 1 (silecek + bir uç → pin 1, diğer uç → pin 2),
R13 + C7 (pin 2 → Vmid), R15 + C8 → JAK-SOL teli (delikten geçir). Jak toprak
teli → GND barası. TL072'yi sokete tak (çentik çizgiye).
**✔ KN3:** pin 1 DC ≈ Vmid.
**✔ KN4:** trimpot minimumda, jak PC'ye takılı: pin 3 padına tırnak sürt →
`probe_check.py`'de SOL kanal fırlamalı. Sonra anten bağlıyken trimpotla SOL
seviyesini −30…−20 dBFS'e getir.

☐ **4.5** Kanal 2: 4.3–4.4'ün kopyası; soketin 5-6-7 pinleri kullanılır.
JAK-SAĞ teli delikten. Referans prob → ANT2.
**✔ KN5:** iki kanal canlı, kanal korelasyonu ≠ +1.000, SAĞ seviye trimpotla
−40…−30 dBFS.

☐ **4.6** Kutuya yerleştir: plaket dibe, kablolar tek delikten çıkar, pil
yuvası yanına. Kapak kapanmadan KN4 ve KN5'i bir kez daha doğrula.

## 5. 96 kHz'e geçiş — verici avı için

48 kHz örneklemede tavan 24 kHz'dir ve MSK vericilerinin çoğu menzil dışında
kalır. 96 kHz tavanı 48 kHz'e çıkarır; TBB (26.7 kHz) dahil tüm katalog
menzile girer. **Donanım değişikliği gerekmez:** JFET katı yüzlerce kHz
geçirir, TL072 3 MHz kazanç-bant çarpanıyla 40 dB kazançta ~30 kHz bant verir.
Tek kural: verici avı sırasında trimpotu tavana çekme (~30–35 dB bölgesinde
tut), yoksa bant daralır.

☐ **5.1** Windows girişini 96 kHz'e al: `mmsys.cpl` → Kayıt → Hat Girişi →
Özellikler → Gelişmiş → **"2 kanal, 16 bit, 96000 Hz"** → Uygula.

☐ **5.2** Doğrula:

```powershell
python server/tools/probe_check.py --device 1 --rate 96000 --seconds 10
```

Başlıkta 96000 Hz yazmalı, spektrum 48 kHz'e kadar uzanmalı.

☐ **5.3** Sunucuyu 96 kHz başlat (`server/.env` dosyasına da yazabilirsin):

```powershell
$env:VLF_DEVICE = "1"
$env:VLF_SAMPLE_RATE = "96000"
$env:VLF_HIGH_CUT_HZ = "20000"
uvicorn vlf_stream.server:app --host 0.0.0.0 --port 8000
```

☐ **5.4** Verici avı:

```powershell
python server/tools/verici_avi.py --device 1 --seconds 60 --json ../data/son_tarama.json
```

`--json` çıktısı web arayüzündeki verici tablosunu besler.

**Dürüst sınır:** web arayüzü MP3 akışıyla beslenir ve MP3 48 kHz'te kalır —
web şelalesinde tavan 24 kHz'dir. 24 kHz üstü vericiler webde değil,
`verici_avi.py` çıktısında görünür. Bu vericiler zaten kulağın üstündedir:
duyulmaz, ölçülür.

## 6. Sık pertinaks hataları

| Belirti | Sebep |
|---|---|
| İki nokta arası istenmeyen sıfır ohm | Lehim köprüsü — büyüteçle bak, havyayla süpür |
| Çalışıp çalışıp kesilme | Soğuk lehim (mat/top görünüm) — yeniden ısıt |
| Çip takınca DC'ler saçma | Soket/çip çentiği çizgiye bakmıyor |
| Bir düğüm tamamen ölü | Bacak lehimlenmeden kesilmiş veya pad kalkmış → komşu delikten köprüle |
| 96k'da probe_check hata veriyor | Windows Gelişmiş sekmesi hâlâ 48000'de |
| Yayında ses yok ama testler çalışıyor | Ortam değişkenleri o terminalde eksik (5.3 bloğunu tam uygula) |
