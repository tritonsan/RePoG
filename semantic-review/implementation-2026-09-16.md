# Mimari iyileştirmeler — 16 Eylül 2026

Temel ayrım korunuyor: model kurgusal anlamı ve anlatımı üretir; küçük yerel
yardımcılar dosya kapsamını, biçimi, revision'ı ve güvenli kaydı denetler. Çalışma,
kanonik RePoG kaynağında yapıldı; mevcut kişisel kampanyalar taşınmadı.

## Uygulanan değişiklikler

- RPG yazıcısı değişen `current_state.yaml` ve mekanik durum adaylarını kayıt
  öncesinde denetliyor. Geçersiz sahne modu, eksik sahne alanı, yinelenen anahtar
  ve yanlış liste biçimi yetkili dosyalar/revision/log değişmeden reddediliyor.
  Bu dar yapısal kontrol tam YAML veya anlatı doğrulayıcısı değildir; Markdown
  içeriğinin doğruluğu modelin sorumluluğunda kalır.
- RPG, Companion, Deep Session 0, World Voices, Agent Seat ve snapshot işlemleri
  ortak işletim sistemi kilidini kullanıyor. Çok dosyalı Companion, Session 0 ve
  World Voices kayıtlarında kalıcı işlem günlüğü/kurtarma var. RPG eski günlüğünü
  kurtarmayı sürdürüyor. Süreç sonlandırma, stale revision, eşzamanlı yazma,
  bozuk günlük ve Windows junction durumları sınandı. Elektrik kesintisinde
  fiziksel disk dayanıklılığı garantisi verilmez.
- Companion'ın değişen Markdown sahipleri ve log işareti aynı semantic işleme
  katılabiliyor. Önce notu yazıp sonra başarısız state kaydı yapma ihtiyacı kalktı.
  Eski çağrılar geçerli; private state, public View'a otomatik taşınmıyor.
- İlerleme/ödül için tek karar tablosu var. `none`, eşleşmeyen kapanış ve ertelenmiş
  ödülle sakin devam durumları açık. Yetkinlik vaadi ve sayısal sınır arasındaki
  istisna açıkça kaydedilmek zorunda.
- AGENTS 7.790 kelimeden 1.499 kelimeye, GM omurgası yaklaşık 2.850'den 2.023
  kelimeye indi. Ayrıntılar tetiklenen referanslara taşındı; ikinci GM kopyası
  kanonik belgeye yönlendiriyor. Bu ölçü metin hacmidir, token veya hız ölçümü değil.
- Yeni schema-v9 Quick dokuz, Standard 20–29 içerik kararı kullanıyor. Tasarım
  onayı ardından hazırlanmış içeriğin tek kabulü var. Eski Quick/Standard
  sözleşmeleri değişmedi; Deep state/manifest v8, yeni setup profile v9 ile uyumlu.
- Testler ürünle aynı depoya geri bağlandı. Sabit tarihsel test sayısı vaadi
  kaldırıldı. CI üç işletim sisteminde test ve gerçek ZIP denetimi çalıştırıyor.
- Paketleyici hem dosyaları hem izin politikasını aynı immutable commit'ten alıyor.
  Dört Agent Seat şeması paketleniyor; gerçek lifecycle verisiyle şema ve
  portable/local intent-resolution dönüşümleri sınanıyor. Kaynak ZIP'i ile
  doğrulanmış oyuncu ZIP'i belgelerde ayrılıyor.
- GM paketi 16 senaryoya genişledi; 36 turluk RPG ve 12 konuşmalık Companion
  dizileri, bağımsız değerlendirme ve ölçüm kayıt protokolü eklendi.

## Tekrarlanabilir kontroller

```text
python -m pip install -r requirements-dev.txt
python -B -m pytest
python -B tools/verify_workspace.py --json
python -B tools/build_distribution.py --target <new-directory>/RePoG --archive <new-path>/RePoG.zip --json
```

Paket komutu commit edilmiş HEAD'i kullanır; kaydedilmemiş düzenlemeler ve test
dosyaları oyuncu arşivine girmez. ZIP manifesti kaynak commit'i ve dosya hash'lerini
taşır. Testler geliştirme bağımlılıkları kullanır; oyuncu yardımcıları standart
Python kitaplığıyla çalışır.

## Doğrulama sınırları

Yerel ortam Windows/Python 3.10. Normal sembolik bağlantı oluşturma izni yok;
ilgili test bu nedenle atlanır. Windows junction testi gerçekten çalıştırılır.
macOS/Linux sonuçları ancak uzak CI tamamlandığında doğrulanmış sayılır.

Uzun anlatı denemeleri sentetik `fiction_only` pilotlardır. Gerçek runtime
persistence, model token kullanımı, medyan/p95 yanıt gecikmesi veya gerçek oyuncu
memnuniyeti kanıtı değildir. Host'un ajan sayısı sınırı yüzünden devam bölümlerinde
model bağlamı korunur; snapshot yeniden okumaları gerçek yeni-bağlam testinin
yerini tutmaz. Seri/paralel hız karşılaştırması yapılmadığı için performans artışı
iddiası yoktur. Bu sınırlar kayıtların içinde de korunmalıdır.
