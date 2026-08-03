# Devreye alma kontrolü (v2)

Her adımı sırayla yap. Bir adım geçmeden sonrakine geçme; sorunun hangi
kademede olduğunu ancak böyle ayırt edebilirsin.

## 1. Ses kartı — lehim yapmadan önce

```powershell
python server/tools/probe_check.py --list
```

Kullanacağın Line-In aygıtı **2 giriş kanalı** göstermeli
(`max_input_channels: 2`). Tek kanal gösteren bir girişle (ucuz USB
dongle'ların çoğu mono mikrofondur) ikili prob mimarisi kurulamaz.

## 2. Enerjisiz kontrol

- V+ ile GND arasında kısa devre olmadığını ölç.
- İki kanalın direnç değerlerini karşılaştır.
- TRS sleeve'in devre GND'sine bağlı olduğunu doğrula — `Vmid`'e değil.
- Metal sapın yalnızca ana kanalın `R1` girişine gittiğini doğrula.
- TL072 soketteyse çentik yönünü kontrol et.

## 3. Besleme ve Vmid

Op-amp'ı soketten çıkar, pili tak.

- `V+` ölçümü pil geriliminde olmalı.
- `Vmid`, `V+`'ın yarısı ±%5 içinde olmalı. Değilse `R20`/`R21` ya da lehim
  hatası var.
- Toplam akım çekişi 5 mA'in altında olmalı (op-amp yokken ~0.4 mA).

## 4. Kademe 1 bias

Op-amp hâlâ dışarıdayken, anten bağlı değilken her kanalın drain gerilimini
ölç.

- **Hedef: `V+` değerinin %40–70'i.** 12 V'ta 4.8–8.4 V; 9 V'ta 3.6–6.3 V.
- Drain `V+`'a yapışıksa: JFET akım çekmiyor. Bacak dizilişini kontrol et;
  bacaklar doğruysa JFET'i yedeğiyle değiştir.
- Drain GND'ye yakınsa: JFET fazla akım çekiyor. `R5`'i büyüt (1 kΩ,
  gerekirse 2.2–4.7 kΩ).

İki kanalın aynı gerilimde olması gerekmez. JFET dağılımı geniştir ve NLMS
kazanç farkını kendisi öğrenir.

## 5. Kademe 2 kazancı

Op-amp'ı yerine tak.

- Çıkış DC seviyesi (`C8` öncesi) `Vmid` civarında olmalı. `V+`'a veya GND'ye
  yapışıksa geri besleme yolu kopuktur.
- Trimpotu ortaya al.
- Gate'e parmağınla dokun: çıkışta belirgin bir 50 Hz artışı görmelisin. Hiç
  tepki yoksa kademe 1 ile kademe 2 arasındaki `C4` bağlantısını kontrol et.

## 6. Gerçek stereo testi

```powershell
python server/tools/probe_check.py --device 1 --seconds 20 --out stereo-test.wav
```

- Ana antene dokununca ağırlıklı olarak sol kanal değişmeli.
- Referans probuna dokununca ağırlıklı olarak sağ kanal değişmeli.
- Araç **kanal korelasyonu = +1.0000** diyorsa ses kartı tek girişi
  kopyalıyordur; devre değil kart sorunludur.

## 7. Seviye ayarı

Hedef: ham RMS seviyesi **−40 ile −20 dBFS** arasında, kırpılan örnek %0.

Kırpılma varsa sırayla:

1. Trimpotu kıs.
2. Ana anteni duvar kablolarından uzaklaştır.
3. PC kasasını ve güç kablolarını uzaklaştır.
4. Topraklı folyo ekranı oda tarafına koy.
5. Son çare olarak ana sapı kısalt.

Seviye −70 dBFS'in altındaysa trimpotu aç; sonuna kadar açıkken hâlâ sessizse
kademe 1 bias'ına geri dön.

Kırpılmış kayıt yazılımla düzeltilemez.

## 8. Referans probu yerleştirme

Probu oda içinde gezdir. Amaç en büyük sağ-kanal seviyesi değil, web
arayüzündeki en yüksek **referans eşleşmesi** ve gerçek sferic darbelerinin
korunmasıdır.

- `%20 altı`: zayıf eşleşme.
- `%20–50`: kullanılabilir başlangıç.
- `%50 üstü`: güçlü ortak parazit; ham/temiz karşılaştır.

Bu değerler kesin kalite puanı değildir; spektral ortalamadır.

Prob ana antene veya pencereye çok yaklaşırsa atmosfer sinyali de referansa
sızar ve yanlışlıkla azaltılabilir. Web arayüzündeki **adaptif iptal** değeri
yükselirken sferic'lerin kaybolmaya başladığını görüyorsan probu geri çek.

## 9. İki metriği karıştırma

Arayüzde iki ayrı sayı var:

- **Adaptif iptal (dB):** yalnızca NLMS'in bant içinde yaptığı bastırma.
  Referans faydasızsa bu değer 0 dB civarında kalır. Gerçek başarı ölçüsü
  budur.
- **Bant filtresi (dB):** 250 Hz–12 kHz dışını atmanın katkısı. Referans
  hiç bağlı olmasa bile yüksek çıkar. Bunu iptal başarısı olarak sunma.

## 10. İlk gerçek kayıt

- Akşam/gece dene.
- LED ışıkları ve gereksiz adaptörleri başlangıçta kapat.
- Önce 5 dakika ham, sonra 15–30 dakika temiz yayın dinle.
- Yakındaki yıldırım için anteni dışarı çıkarmak yerine hava durumu/zaman
  bilgisiyle sferic yoğunluğunu karşılaştır.
