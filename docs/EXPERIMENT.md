# Deney ve kanıt planı

Amaç “her evde whistler garantisi” değil; ev içindeki baskın elektriksel
parazitin referans probuyla ölçülüp azaltılabildiğini ve doğal VLF darbelerinin
korunduğunu tekrarlanabilir biçimde göstermektir.

## Kayıtlar

Her oturumda şunları not et:

- UTC ve yerel saat.
- Ana anten/prob konumu ve yaklaşık mesafeler.
- Açık cihazlar.
- Ham giriş dBFS ve kırpılma.
- Ortalama referans eşleşmesi.
- Temizlemeden önce/sonra gürültü farkı.
- Duyulan olay türü ve zaman damgası.

## A/B sırası

1. 5 dakika `Ham`.
2. Aynı yerleşimle 5 dakika `Temiz`.
3. Referans probunu 50 cm taşı.
4. 5 dakika daha `Temiz`.
5. En iyi konumu sabitleyip gece boyunca çalıştır.

## Yanlış pozitifleri azaltma

- Bir sferic ham ve temiz kanalda aynı zaman damgasında görünmeli.
- Cihaz açıp kapatınca kaybolan düzenli ton doğal sinyal sayılmaz.
- 50 Hz’in tam katlarındaki sürekli çizgiler şebeke harmonikleridir.
- Whistler adayı yalnız sese dayanarak ilan edilmemeli; aşağı kayan
  spektrogram izi ve mümkünse başka istasyonlarla zaman karşılaştırması gerekir.

## Yayın şeffaflığı

- Simülasyon modunu **ANTEN** diye etiketleme.
- DSP ayarlarını ve yazılım commit’ini yayın sayfasında belirt.
- İlginç olayların hem ham hem temiz kısa kesitini sakla.
- Başarısız/geçersiz denemeleri de deney günlüğünde tut.
