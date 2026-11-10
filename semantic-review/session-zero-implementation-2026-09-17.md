# Session 0 uygulaması — 17 Eylül 2026

Kapsam: [teknik incelemedeki](session-zero-review-2026-09-17.md) F01–F13 ve
[birleşik plandaki](session-zero-integrated-plan-2026-09-17.md) D01–D09.
Değişiklikler kullanıcının uygulama onayıyla `public/RePoG` ürün deposunda yapıldı.
Başlangıç commit'i `2ed60778ed22a7e9983da126f2453759900c139b`.
Bu rapor yerel çalışma ağacını anlatır; yayımlanmış sürüm iddiası değildir.
Kişisel kampanyalar değiştirilmedi. `campaign/` içindeki değişiklikler boş dağıtım
şablonuna aittir. Sentetik oyun kayıtları testlerin geçici dizinlerinde üretildi.

## Uygulanan akış

Yeni RPG kurulumları schema 10 kullanıyor. Quick'in dokuz, Standard'ın yirmi
zorunlu karar alanı var; bunlar soru veya mesaj sayısı değil. Hazırlık ancak
gerekli alanlar gerçekten çözüldüğünde ve tasarım/hazırlık onayları doğru sırada
alındığında tamamlanıyor. Uzun bir mesajın birçok kararı çözmesi ya da görüşmenin
29 kararı aşması artık yeni kurulumları geçersiz kılmıyor. Mevcut v1–v9
kurulumları kendiliğinden taşınmıyor; Companion'ın sayım sözleşmesi korunuyor.

Deneyim seçiminden sonra kısa RPG niyeti alınıyor, ardından derinlik açıkça
seçiliyor. Önceden verilmiş cevap tekrar sorulmuyor. Derinlik öncesi kayıt bir
giriş notu: karar sayısını, setup revision'ını veya profil kilidini ilerletmiyor.
Seçilen rota cevabı kendi normal karar sınırında sahipleniyor; Deep başlangıç
kaydıyla revision uyuşmazlığı oluşmuyor.

Erken cevap, öneri, kararsızlık, çelişki, ret ve erteleme ayrıldı. Yazarlık ve
tematik izinler karakter adına ayrıntı üretmeden önce ele alınıyor. Görünüşün
gereksiz ayrıntıları zorunlu değil. Ton, kişisel bir yönü sınama izni sayılmıyor.
Reddedilen bir deneyim sonraki sahnede başka kılıkla geri getirilmiyor.

Hazırlıkta roster, yan koşul veya act büyüklüğü kotası yerine nedensel yeterlilik
aranıyor. Son inceleme, önemli tercihlerin hangi somut oynama olanağını yarattığını
gösteriyor. Oyuncunun açılışı reddetmesi, gündelik işle ilgilenmesi veya ayrılması
hazırlığı anlamsızlaştırmamalı; bunlar yazılmış zorunlu olay dalları değil.

## Teknik bulguların karşılığı

| Bulgu | Uygulanan değişiklik |
| --- | --- |
| F01 | Başlangıç snapshot'ı tarihsel kanıt oldu. Normal continuity ilerlemesi, açılışın tüketilmesi ve güncel sahip değişiklikleri kurulumu geçersiz kılmıyor. Snapshot içeriğinin hash bütünlüğü denetlenmeye devam ediyor. Yeni v10 başlangıcı hashesiz v1/v2 kanıtla geçemiyor. |
| F02 | Deep doğrulama yolu schema 8, 9 ve 10 için aynı kanonik ledger üzerinden çalışıyor. |
| F03 | Değiştirilen Deep kararları ve kapılar geçmişini koruyor. Yeniden onay, yeni incelemenin revision/digest'ine bağlanıyor; eski onay tekrar kullanılamıyor, aynı cevap yeni hazırlık için yeniden kabul edilebiliyor. |
| F04 | World Voices kendi son ilgili revision'ını tutuyor. İlgisiz oyun turları boş güncelleme gerektirmiyor; sonraki gerçek işlem güncel kampanyaya bağlanıyor. Güncel olaya bağlı yeni ileti kabul edilirken gelecekteki olay ve eksik kaynak reddediliyor. |
| F05 | Yeni Quick/Standard v10'da sabit karar toplamı kaldırıldı. v9 kabul sözleşmesi uyumluluk için değişmedi; eski kurulumlara sessizce yeni kurallar uygulanmıyor. |
| F06 | Yeni GM bağlamı deneyim/tematik sınır ve somut GM davranışı sahiplerini doğrudan okuyor. Olumlu deneyim tercihleri sahne ve fırsat seçimine bağlandı. |
| F07 | Act geçişi ve sonraki hazırlık, güncel deneyimi, açık yön değişikliğini ve bağımsız dünya süreçlerini birlikte kullanıyor. Tüketilmiş ilk hazırlık yeni act'in otoritesi değil. |
| F08 | Ayrıntılı envanter, zaman, seyahat veya yara takibi seçilirse modül listesi boş olsa da çalışan mekanik kayıt zorunlu. Profil ve gerekli boş kayıt birlikte etkinleştirilebiliyor. |
| F09 | Standard seyahat tercihleri kendi alanına alındı; kapalı Deep paketine bırakılmıyor. |
| F10 | Deep schema 10'da açık Agent Seats kararı ve profil karşılığı doğrulanıyor. Schema 8/9'un 43 kararına ek gereksinim yüklenmiyor; schema 10'da 44 karar var. |
| F11 | Deep'in atomik son hazır kapısı ile diğer rotaların aday hazır metadata → snapshot → son denetim sırası ayrıldı. Başarısız aday oynatılmıyor. |
| F12 | Kabul edilen kritik kararın mevcut sahibine aynı kabul turunda yazılması açıklandı; yalnız türetilmiş/zenginleştirici hazırlık ertelenebiliyor. |
| F13 | `player_ties.md`, güncel NPC çalışma durumu/ilişki/bilgi kopyaları yerine geçmiş bağ öncülünü ve gerçek sahip bağlantılarını tutuyor. |

## Oyun sonrası değişiklikler

Yeni OOC playbook'u geçici anlatım talimatını, kalıcı tercihi, mekanik ayarı ve
kurgu revizyonunu ayırıyor. Kalıcı üslup değişikliği Session 0'ı yeniden açmıyor;
kurgu revision'ı veya olay kaydı üretmiyor. Gerçek retcon ise etkilenen güncel
sahiplerin normal RPG işlemiyle birlikte değiştirilmesini gerektiriyor.

Bütünleşik test, işlem içindeki tam denetimin kendi hazırlanmış journal'ını
yarım işlem sandığını yakaladı. Artık yalnız aynı süreç/thread'deki etkin
`validate_applied` çağrısının tam uygulanmış, hash'leri doğru kendi journal'ı
tanınıyor. Diğer, bozuk veya kesintiye uğramış kayıtlar hâlâ recovery gerektiriyor.
Geçersiz ayar bütün yazma grubunu geri alıyor; genel bir denetimi atlama seçeneği
eklenmedi. Bu tam denetim açık bakım sınırına ait; sıradan oyun turuna eklenmedi.

## Doğrulama

Kesin sonuçlar ve kaynak hash'leri
[uygulama koşusunda](runs/2026-09-17-session-zero-implementation/) tutuluyor.
Testler, modelin görüşmeyi başarıyla yaptığı iddiasından ayrı değerlendirildi.

- Deep 8/9/10 için gerçek kurulum kanıtı, hazır geçişi, oyun ilerlemesi ve
  açılış tüketimi; hazır olmadan önce/sonra değişiklik ve yeniden onay.
- Quick/Standard v10 için materyalize sahiplerden ön denetim, profil kilidi,
  snapshot, gerçek durable işlem ve idempotent tekrar.
- Aynı kampanyada kalıcı kısa anlatım ve zaman takibi ayarı; kurgu dosyaları ve
  olay kaydı değişmeden kabul, ardından ilk gerçek zaman işleminin çalışması.
- Eksik/açık/defaulted zorunlu alan, eski/yanlış sıralı onay, değişmiş başlangıç
  kanıtı, gelecekteki World Voices kaynağı ve bozuk işlem kayıtları için red testleri.
- Temiz dizin ve ZIP dağıtımı; v10 playbook'ları, OOC yönergesi ve değerlendirme
  senaryosunun pakete girmesi, özel çalışma dosyalarının dışarıda kalması.

**Tam sonuç:** `python -m pytest -q` → **484 passed, 2 skipped**, 109,71 saniye.
İki atlama, Windows ortamının sembolik bağlantı oluşturma izninden kaynaklanıyor.
Temiz dizin/ZIP dağıtım testi bu toplamın içinde. `python tools/verify_workspace.py
--json` → **0 hata, 0 uyarı**; boş şablonda konumun henüz seçilmemiş olduğuna
ilişkin bir bilgi kaydı var. `git diff --check` temiz.

Kanıtlar: [tam pytest çıktısı](runs/2026-09-17-session-zero-implementation/pytest-full.txt),
[çalışma alanı denetimi](runs/2026-09-17-session-zero-implementation/workspace-verification.json),
[test edilen kaynak hash'leri](runs/2026-09-17-session-zero-implementation/candidate-source-manifest.json).

Yeni bağlam deneyi önceki görüşmeyi görmeyen ayrı aktörle, dondurulmuş sentetik
bir sonraki-act durumundan yapıldı. Aktör yalnız mevcut kaynakları okudu;
tercihleri, aileyle ilgili sınırı, güncel kısa anlatım ayarını ve NPC'nin kendi
siparişini buldu. Oyuncu adına ders verme kararı almadı, eski açılışı tekrarlamadı.
Tam komutlar, okunan kaynak hash'leri ve yanıt
[aktör kanıtında](runs/2026-09-17-session-zero-implementation/fresh-context-probe.md).
Bağımsız değerlendirme [ayrı kaydedildi](runs/2026-09-17-session-zero-implementation/fresh-context-evaluation.md):
57 değişen kaynak, 19 deney paketi dosyası ve aktörün 20 kaynak hash'i eşleşiyor.
Kaynak erişimi ve bu tek devam yanıtında somut bir ihlal bulunmadı. Aktörün
komutları kanıt dosyasında kopyalanmış durumda; bağımsız ham host transcript
aktarımı, model/ayar kimliği ve süre ölçümü yok. Bu sınırlama değerlendirmede korunuyor.

Bu dar deney tam Session 0 görüşmesi, on turluk oynatım, gerçek act geçişi veya
model eliyle OOC/retcon kalıcılık sınaması değildir. Bunlar için senaryo eklendi;
çalıştırılmayan dallar başarılı sayılmadı. Önce/sonra karşılaştırmalı anlatı
kalitesi veya süre iyileşmesi ölçülmedi. Deterministik işlem testleri bu anlamsal
sınamaların yerine geçmez.
