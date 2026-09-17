# Anlatı ve süreklilik iyileştirmeleri

17 Eylül 2026. Önceki [20 bulguluk incelemenin](narrative-quality-review-2026-09-17.md)
uygulaması. Kampanya anlamını model belirlemeye devam eder; yerel araçlar yalnız
biçim, kimlik, referans ve kayıt işlemlerini denetler. Normal tura ek bir model,
anlatı puanlayıcısı veya bütün kampanyayı tarayan kontrol eklenmedi.

## Uygulananlar

| İnceleme bulgusu | Değişiklik |
| --- | --- |
| 1–2: act devri ve etkin Compass | Açık act kimliği, önceki act bağlantısı, kapanış/arşiv kanıtı; etkin sorunun, kapsamın ve kapanış koşulunun küçük tur bağlamında tutulması. Kapanış ve ardıl act etkinleştirme ayrı gerçek işlemler; arşiv ve yeni Compass tek owner işleminde. |
| 3: soğuk bilgi keşfi | Yerleşik ad/alias/konu tetikleyicilerinden mevcut owner başlığına veya kimliğine seçici bağlantılar. Eksik indeks kaydı, olayın yaşanmadığı anlamına gelmez. |
| 4: bilgi kaynağı ve zaman | Önemli holder–fact ilişkileri için tek güncel hesap; alınan önerme, tutum, kaynak, öğrenme zamanı ve düzeltme kanıtı. Birinin öğrenmesi diğerlerini otomatik bilgilendirmez. |
| 5: sıkıştırma | Koşul, istisna, neden, belirsizlik, açık yükümlülük ve değişmeyen sınırların korunması; tarih özeti güncel izinlerin yerine geçmez. |
| 6: yarım konuşma | Önemli yanıtsız sorunun gönderimi kaybolacaksa beş yumuşak turu beklemeden mevcut resume anchor ile checkpoint; kurgu revision’ı artırılmaz. |
| 7: offscreen sahipliği | Kişisel süreç karakter notunda, paylaşılan süreç world domain’inde; aynı hareket iki kez değerlendirilmez. |
| 8–10: NPC ve ilişki | Önemli karakterlerde az sayıda bağlamsal ses örneği; geçici ruh hâli ile kanıtlı kalıcı değişim ayrımı; konuya özgü güven, borç, sınır ve kısmi onarım. |
| 11–12: büyük kurgu ve karşılık | İsteğe bağlı Campaign Horizon; yalnız gerçekten gösterilmiş beklentiler için kaynaklı planted/available/paid_off/transformed/retired yaşam döngüsü. Zorunlu ana hikâye veya olay sırası yok. |
| 13–15: yön ve açılış | Takılma, bilinçli ret, yeni yön ve dinlenme ayrımı; sabit kanıt yer değiştirmez; sakin açılışa baskı kotası konmaz. |
| 16–17: ton ve tekrar | Kurallara uyulduğunu NPC ağzından anlatma alışkanlığını azaltan yönergeler; en fazla 8 karakter × 4 örnek hafızası, anlatıcı örneklerinden ayrı tutulur. Çoklu NPC ifade örtüşmesi yalnız uyarıdır. |
| 18: kalite kanıtı | 22 turluk yeni senaryo, gerçek yeni bağlam koşulları, ayrı edebî boyutlar ve kör karşılaştırma protokolü. Gerçekleşmeyen ölçümler boş kalır. |
| 19–20: diyalog ve somutluk | Yanıtın yeni sosyal gerçek yaratması zorunlu değil; sessizlik/tamamlanmış yanıt geçerli. Ayrıntılar eyleme ve yoruma hizmet eder; nesne/duyu/paragraf kotası yok. |

## Kayıt güvenceleri

`tools/narrative_memory.py`, değiştirilmiş thread/hesap adaylarını kayıt öncesinde
kontrol eder. Etkin act’i kapanmadan değiştirme, arşivi kaybetme, kapanmış kimliği
yeniden açma, eski Closure Record’u yeni act’e taşıma ve yanlış işlem revision’ı
reddedilir. Tam sınır kontrolü opening/prep bağlantılarını, bildirilen lookup
hedeflerini ve gelecekteki revision referanslarını da denetler. Normal işlemde
başka lookup dosyaları taranmaz.

Mevcut kampanyalara otomatik migration yapılmaz. Anlamlı act kimliği olmayan eski
kayıtlar çalışmaya devam eder; hazır kampanyanın tam incelemesinde yalnız geçiş
uyarısı verilir. Boş dağıtım şablonu temiz kalır. Stil schema3 korunur; yeni alanlar
isteğe bağlıdır. Owner listesi genişletilmedi; prep/opening ikincil hazırlık
olarak başarılı owner kaydından sonra tamamlanır.

## Gerçek doğrulama ve sınırlar

- Tam Python test çalışması: **409 geçti, 2 atlandı**; süre 73,78 saniye.
  Atlananlar Windows’un gerçek symlink oluşturma izniyle ilgili. Reparse niteliği
  ve mevcut junction testleri ayrıca çalıştı.
- Son incelemede `active → planned` geri dönüşü ve Windows'ta yasak kaynak
  klasörlerinin büyük/küçük harfle aşılması da kapatıldı. Referans, aday ve
  transaction kontrollerinin son odaklı çalışması: **69 geçti, 1 atlandı**.
  Sıradan thread yazımının tam referans taramasını çağırmadığı ayrıca sınandı.
- Boş çalışma alanı: **0 hata, 0 uyarı**; boş konum için beklenen tek bilgi mesajı.
- Gerçek CLI alt süreçleri: kapanış, arşivli yeni act etkinleştirme, yeniden
  denemede idempotency, başarısız adayda owner/revision/log değişmemesi ve
  kurgu revision’ı yaratmayan yanıtsız soru checkpoint’i sınandı.
- [Dar owner okuma deneyi](runs/2026-09-17-narrative-implementation/owner-probe/evaluation.json):
  üç gerçek kayıt işlemi sonrası, önceki konuşmayı almayan yeni okuyucu dört
  sorunun tamamını kayıtlarla tutarlı yanıtladı. Verilen kaynakların byte
  hash’leri, giriş/çıkış işlemleri, yanıtlar ve bağlam kaynağı arşivlendi.

Bu deney tamamlanmış oyun akışı değildir: sentetik kurulum, önceden yazılmış
semantik değişimler ve altı adlandırılmış kaynak kullandı; tam Session 0/Distill
çalıştırılmadı. Büyük kampanyada bağımsız bilgi bulmayı, doğal turdan eksiksiz
kayıt üretmeyi veya uzun vadeli edebî kaliteyi kanıtlamaz. Yeni 22 turluk senaryo
henüz çalıştırılmadı. Kör önce/sonra karşılaştırması ve uzun oyun değerlendirmesi
olmadan anlatım kalitesine sayısal artış iddiası yapılmıyor.
