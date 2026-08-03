# Kaynakça ve esin haritası

Bu klasör dış projelerin README veya şemalarını kopyalamaz. Bağlantı, yazar ve
bu projede hangi fikri doğruladığı kaydedilir. Kaynakların kendi lisans ve telif
koşulları geçerlidir; VLF Noise Scout kodu bu repo için yeniden yazılmıştır.

## Doğal radyo ve minimal alıcı

1. **Charles Wenzel / Techlib — VLF Whistler Reception**
   <https://techlib.com/electronics/vlfwhistle.htm>

   Tek JFET’li, kayıt cihazı/mikrofon girişine bağlanabilen minimal doğal radyo
   yaklaşımı ve yüksek empedanslı kısa whip fikri.

2. **Peculiar Games — VLF Receiver**
   <https://www.peculiar-games.com/electronics/vlf-receiver>

   Basit JFET dongle’ın telefon/kayıt girişinde pratik çalışması; sferic ve
   tweek ses örnekleri. Bu repo sayfadaki metin, görsel veya şemayı kopyalamaz.

3. **Natural Radio Lab — Equipment & Software**
   <https://naturalradiolab.com/equipment-software/>

   Doğal VLF için temel alıcının yüksek kazançlı ses yükselteci ve E/H alan
   anteninden oluşabileceği; şebeke gürültüsünün ana pratik sorun olduğu.

4. **DL4YHF — Spectrum Lab for Natural Radio**
   <https://www.qsl.net/dl4yhf/speclab/natradio.htm>

   50/60 Hz ve harmonik giderimi, 22.05/44.1/48 kHz örnekleme ve iki anteni
   stereo kanallarda karşılaştırma pratiği.

5. **NASA — Building and Testing a Portable VLF Receiver**
   <https://ntrs.nasa.gov/citations/20150002522>

   İnsan yapımı VLF girişimi ve 50/60 Hz harmoniklerinin saha alıcılarında
   baskın problem oluşu.

## Referans anteni ve adaptif iptal

6. **Cohen et al. (2010) — Mitigation of 50–60 Hz power line interference in
   geophysical data**
   <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2010RS004420>

   ELF/VLF verisinde adaptif filtreyle şebeke girişimi izleme ve azaltma.

7. **Mitchell, Robertson, Sault — Reference antenna RFI cancellation**
   <https://arxiv.org/abs/1004.0938>

   İstenen sinyal yolundan girişimi kaldırmak için yardımcı/referans anten
   kullanma; referans gürültüsünün ve sinyal sızıntısının sınırları.

8. **Widrow-style adaptive noise cancellation overview / UCSD**
   <https://isn.ucsd.edu/courses//492/2005/LMS/>

   Ana sensör + gürültüye yakın referans sensörü + LMS yapısı.

9. **Liu et al. (2017) — Double-loop VLF/ULF noise suppression**
   <https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-map.2016.0807>

   VLF/ULF sisteminde iki sensörden alınan verilerle girişim azaltma örneği.

## Donanım

10. **onsemi — 2N5457/2N5458 JFET datasheet**
    <https://www.onsemi.com/pdf/datasheet/2n5457-d.pdf>

    Yüksek giriş empedanslı genel amaçlı JFET davranışı ve üreticiye göre pin
    kontrolünün gereği. Bu istasyonda 2N5457 kullanıldı; farklı bir JFET
    kullanılacaksa kendi veri sayfasından pin dizilişi ve IDSS kontrol
    edilmelidir.

11. **C-Media CM6206 datasheet**
    <https://www.alldatasheet.com/html-pdf/944238/CMEDIA/CM6206/1762/8/CM6206.html>

    Ayrı `LINL` ve `LINR` stereo Line-In girişleri. Her CM6206 ürününün bu
    uçları sokete çıkardığı varsayılmamalıdır.



## Web yayını

12. **GitHub Docs — What is GitHub Pages?**
    <https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages>

    Pages’in HTML/CSS/JavaScript için statik barındırma oluşu.

13. **Cloudflare Docs — Tunnel**
    <https://developers.cloudflare.com/tunnel/>

    Yerel HTTP servisini inbound port açmadan public hostname’e bağlama.

14. **FastAPI — StreamingResponse**
    <https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse>

    Sonsuz/uzun HTTP gövdesini async generator ile akıtma.

15. **FFmpeg device documentation**
    <https://www.ffmpeg.org/ffmpeg-devices.html>

    ALSA giriş adlandırması, stereo kanal ve 48 kHz yakalama.

16. **python-sounddevice documentation**
    <https://python-sounddevice.readthedocs.io/>

    PortAudio tabanlı iki kanallı callback yakalama.

17. **MDN — HTML audio**
    <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/audio>

    Tarayıcıda HTTP(S) audio kaynağı ve MP3 fallback.

18. **MDN — AnalyserNode**
    <https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode>

    Web Audio FFT verisiyle gerçek zamanlı spektrum çizimi.

## Kopyalama beyanı

- Harici kod kopyalanmadı.
- Harici README metinleri repoya alınmadı.
- Harici görsel veya şema yeniden yayımlanmadı.
- Standart elektronik topolojileri ve matematiksel yöntemler kaynakları
  belirtilerek bağımsız uygulanmıştır.
