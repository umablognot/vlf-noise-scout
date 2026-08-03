# 7–10 günlük canlı yayın

## Mimari gerçek

GitHub Pages statik dosya barındırır; Python/FFmpeg çalıştırmaz ve evdeki ses
kartını açamaz. Bu projede:

- GitHub Pages: `web/` klasöründeki dinleme arayüzü.
- Ev PC'si: iki kanal yakalama, DSP, MP3 ve `/api/status`.
- Cloudflare Tunnel: modemde port açmadan PC’yi HTTPS olarak yayınlama.

## 1. Sunucuyu yerelde doğrula

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/api/status
```

Aynı ağdaki başka bir cihazdan `http://PC_IP:8000` açıp ham ve temiz yayınları dene.

## 2. Cloudflare Tunnel

Kalıcı 7–10 günlük yayın için rastgele “quick tunnel” yerine adlandırılmış
tunnel ve sabit hostname önerilir. Cloudflare hesabı ve Cloudflare’a bağlı bir
alan adı gerekir.

Özet:

```bash
cloudflared tunnel login
cloudflared tunnel create vlf-noise-scout
cloudflared tunnel route dns vlf-noise-scout live.example.com
```

`%USERPROFILE%\.cloudflared\config.yml`:

```yaml
tunnel: TUNNEL_UUID
credentials-file: C:\\Users\\<kullanici>\\.cloudflared\\TUNNEL_UUID.json
ingress:
  - hostname: live.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Ardından (yönetici olarak açılmış PowerShell'de):

```powershell
cloudflared service install
```

Tünel artık Windows servisi olarak kurulur ve PC her açıldığında kendiliğinden
başlar. Durumunu `services.msc` içinde "cloudflared" olarak görebilirsin.

Resmî kurulum: <https://developers.cloudflare.com/tunnel/setup/>

## 3. GitHub Pages

`web/config.js`:

```js
window.VLF_CONFIG = { backendUrl: "https://live.example.com" };
```

Repoyu GitHub’a gönder. Repository ayarlarında **Pages → Source → GitHub
Actions** seç. `.github/workflows/pages.yml`, `web/` klasörünü yayınlar.

GitHub Pages URL’si genellikle:

```text
https://KULLANICI.github.io/vlf-noise-scout/
```

## 4. CORS’u daralt

İlk testte `VLF_ALLOWED_ORIGINS=*` çalışır. Yayın hazır olduğunda:

```dotenv
VLF_ALLOWED_ORIGINS=https://KULLANICI.github.io
```

Sonra sunucuyu yeniden başlat: `start-server.bat` penceresini kapatıp yeniden
çalıştırman yeterli (`.env` her başlangıçta okunur).

## 5. Süreklilik kontrolü

Uzun süreli yayın için PC tarafında:

- **Uyku modunu kapat:** Denetim Masası → Güç Seçenekleri → uyku “Asla”.
  Ekran kapanabilir, PC uyumamalı.
- Windows Update'in otomatik yeniden başlatmasını yayın haftasında ertele
  (Ayarlar → Windows Update → etkin saatler).
- Mümkünse Ethernet kullan; Wi‑Fi güç tasarrufunu kapat.
- PC kasasını ve kablolarını ana antenden 2–3 metre uzağa koy.
- Ön yükselteç pilleri (8×AA) sürekli çalışmada ~1 haftada zayıflar; gerilim
  9 V'un altına inerse bias kayar. Günde bir `canli_seviye.py` ile seviyeye bak.
- Web’de `clipping`, dinleyici ve uptime değerlerini gözle.
- Sunucu ve tünelin açık kaldığını `http://127.0.0.1:8000/healthz` ile doğrula.

## 6. Kapasite

64 kbit/s akışta varsayılan 12 eşzamanlı dinleyici yaklaşık
0.8 Mbit/s ses yükü oluşturur; HTTP/Tunnel ek yükü ayrıca gelir. Her MP3
kodlayıcı yalnızca kendi kanalında en az bir dinleyici varken veri işler. Ev
bağlantısının upload kapasitesine göre `VLF_MAX_LISTENERS` değerini düşür.

## 7. Gizlilik

Bu sistem mikrofon değil, VLF elektrik alan alıcısıdır; yine de yanlış giriş
seçilirse bir mikrofon yayınlanabilir. Yayına çıkmadan önce:

- Doğru stereo Line-In aygıtını seçtiğini doğrula.
- Konuşmanın veya oda sesinin ham kanalda duyulmadığını kulaklıkla test et.
- Web sayfasında kesin ev adresi paylaşma.
