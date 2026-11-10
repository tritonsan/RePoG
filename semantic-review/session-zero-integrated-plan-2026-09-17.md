# Session 0: tasarım tercihi ve birleşik uygulama planı

Durum notu: Bu plan daha sonra kullanıcı onayıyla uygulandı.
[Uygulama ve doğrulama raporu](session-zero-implementation-2026-09-17.md).
Aşağıdaki öneri dili planın yazıldığı andaki değerlendirmeyi korur.

17 Eylül 2026. Kaynak sürüm: `2ed60778ed22a7e9983da126f2453759900c139b`.
Bu belge [13 bulguluk teknik incelemeyi](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/session-zero-review-2026-09-17.md>)
tamamlar. F01–F13 gözlenen hataları ve sözleşme açıklarını; aşağıdaki D01–D09
ise benim önerdiğim tasarım değişikliklerini belirtir. Tasarım önerileri henüz
uygulanmadı veya oyuncuyla karşılaştırmalı olarak sınanmadı. Bu tur yalnız
rapor ve plan düzenlendi.

Ben Session 0'ı, oyuncuyla neyin yaşanmaya değer olduğunu seçip bunun oynanabilir
karşılığını hazırladığımız bir görüşme olarak kurardım. Başarı ölçüsü;
cevapların kaybolmaması, hazırlanan dünyayı değiştirmesi, oyunda gerektiğinde
okunması ve oyuncunun sonradan yönünü değiştirebilmesi olurdu.

## D01 — Derinliği soru sayısıyla değil, ortak tasarım miktarıyla anlatırdım

Quick, Standard ve Deep seçimini korurdum; oyuncunun açık seçim yapması ve daha
önce verdiği cevabın tekrar sorulmaması zaten doğru. Seçeneklerin açıklamasını
şöyle kurardım:

| Yol | Oyuncuyla çalışma biçimi | Hazırlık kapsamı |
| --- | --- | --- |
| Quick | Temel yönleri seçer; GM'nin yetkisi içindeki önerilerini kısa bir bütün olarak inceler | Oynanabilir ilk ölçek ve dışarıya açılacak bağlantılar |
| Standard | Karakter, dünya karşılığı, oynama biçimi ve başlangıç üzerinde anlamlı alternatifleri birlikte tartar | İlk act'i taşıyan ilişkiler, yerler ve bağımsız süreçler |
| Deep | Seçilen önemli alanları birlikte ayrıntılandırır; ilgisiz alanlarda ayrıntı üretmez | Seçilen temalara göre daha derin nedenler, bağlantılar ve koşullu genişlemeler |

Yeni RPG başlangıcında deneyim seçiminden sonra kısa kampanya niyetini alır,
derinlik önerisini bunun üzerine yapardım. Oyuncu fikrini ilk mesajında verdiyse
aynı soru tekrar gelmez. Ardından derinlik ayrı ve açık seçilir; öneri otomatik
kabul değildir. Bu, mevcut “önce derinlik, sonra pitch” kuralının bilinçli
yeniden tasarımıdır; mevcut akışta uygulanacak bir istisna değildir. Kısa niyet
onaylanmış dünya hazırlığı veya izinsiz araştırma başlatmaz. Companion'ın giriş
akışı bu RPG değişikliğinin kapsamına alınmaz.

Üç yol da aynı izin, kayıt, oynanabilirlik ve devir güvencesini taşır. Quick'in
anlamı sınırları tahmin etmek olmaz; Deep'in anlamı her alanı doldurmak olmaz.
Deep zaten aşama temelli; bunu yeni icat olarak sunmuyorum. Değişiklik, yeni
Quick/Standard sözleşmesinde de hazır olmayı sabit cevap toplamından ayırmak.

Oyuncuya ilerleme aşağıdaki anlaşılır bölümlerle gösterilir. Bunlar altı soru
veya altı mesaj vaadi değildir; içerideki bağımsız izinler ayrı kalır.

| Bölüm | Oyuncunun işi | GM'nin işi |
| --- | --- | --- |
| Niyet, sınırlar ve yetki | İstenen deneyim, istenmeyen yönler, kaynak ve yazarlık izinleri | Bilinen cevapları toplamak; gerekli araştırmayı izin sınırında yapmak |
| Karakter çekirdeği | Kim olduğu, şu an istediği, bilerek koruduğu veya sınanmasını istediği yönler | Açık bırakılanı açık tutmak; dünya henüz yokken toplumsal konum uydurmamak |
| Karakteri karşılayan dünya ve yetenekler | Dünyanın önemli niteliğini ve güvenilir yetkinliği seçmek | İnce dünya çekirdeğini kurup yetenek modelini bununla uyumlu hâle getirmek |
| Yaşayan bağlar ve hareket alanı | İstenen bağ/yalıtılmışlık ve başlangıç erişimi | Bağımsız işler, ilişkiler, yerler ve nedensel hareket hazırlamak |
| Oynama ve anlatım biçimi | Takip, risk, ritim, ses ve istenen isteğe bağlı yüzeyler | Tercihleri çalışan ayarlara çevirmek; bedelleri açık göstermek |
| Tasarımı ve gerçek hazırlığı görme | Önce yönü, sonra hazırlanmış somut karşılığı incelemek | İki mevcut kabul sınırını korumak; son kabulden sonra yeni içerik eklememek |

Bu görünür akış Deep'in dünya çekirdeği → karakterin kurallarla gerçekleşmesi
→ ekoloji bağımlılığını bozmaz. İç aşama adları ve şema alanları oyuncuya iş
olarak verilmez.

**Yerleşim:** setup router/contract ve yeni kurulumların sürümlü rota tanımları.
**Kabul ölçütü:** Uzun cevap veren oyuncu gereksiz tekrar yaşamaz; kısa cevap
veren oyuncunun izinleri tahmin edilmez; geçerli bir Standard hazırlığı sırf
30 ayrı karar kaydedildiği için reddedilmez. Mevcut kurulumların sayım ve onay
sözleşmesi sessizce değiştirilmez. **Bağlı bulgular:** F05, F10–F12.

## D02 — Soru sırasından önce cevabın neyi gerçekten çözdüğünü izlerdim

Erken verilen cevapları kabul etme, `mix/change/defer` ve tek önemli soru kuralı
zaten var. Eksik olanı, aşağıdaki durumlarda tutarlı davranış olarak açardım:

- Açık tercih, yalnız öneri, kararsızlık ve önceki kabulle çelişki ayrılır.
- Tek mesaj birçok açık cevap içerirse hepsi kendi sahibine işlenir; bir sonraki
  soru yalnız kalan ve gerçekten gerekli karara gider. Yazma sırası mevcut
  bağımlılık ve işlem sözleşmesine uyar; ilerideki aşama izinsiz tamamlanmaz.
- “Bilmiyorum” onay sayılmaz. GM yetkisi içindeki sıradan konuda gerekçeli öneri
  sunar; henüz gerekli olmayan konu ertelenir. Korunan seçim, gerekli olduğunda
  açıklığa kavuşmadan ona bağlı gerçek üretilmez.
- İki cevap birlikte mümkünse sahte çelişki yaratılmaz. “Sakin oyun, ayrıntılı
  kaynak takibi” geçerlidir. Birbirini dışlayan iki açık karar varsa yalnız o
  uyuşmazlık sorulur; tüm modül yeniden açılmaz.
- “Yeter”, “ara verelim” veya “kaldığımız yerden” için mevcut karar özeti;
  açık karar, bekleyen öneri ve sonraki bağımlılığı taşır. Ham görüşme geçmişi
  yeni bağlamın zorunlu girdisi olmaz.

“Yeter” yeni ayrıntı dallarını durdurur; eksik izinleri veya readiness'i kabul
etmiş sayılmaz. Yalnız başlamayı gerçekten engelleyen açık seçimler çözülür;
rota kendiliğinden değiştirilmez. “Ara” denince yeni soru gelmez. “Bilmiyorum”
ile “ara vermek istiyorum” aynı tepkiyi üretmez.

**Yerleşim:** Mevcut `session_zero.md` karar/erteleme kayıtları ve Deep ledger;
yeni genel amaçlı kullanıcı profili ya da yorumlayıcı araç yok.
**Kabul ölçütü:** Çok cevaplı mesaj, kararsız cevap, çelişki ve gerçek yeni
bağlamda sürdürme için dört ayrı değerlendirme; izin kayması ve tekrar yok.

Dayanak: [mevcut görüşme sözleşmesi](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/WORKFLOW.md:83>).

## D03 — Yazarlık sınırını erkene alır, karakterin gereksiz ayrıntılarını ertelerdim

Quick karakteri yetki kararından önce ele alıyor. Güncel üst kural korunan
bilgiyi uydurmayı zaten engelliyor; yine de yeni akışta içerik ve yazarlık
sınırını karakter adına yeni bilgi önermeden önce yerleştirirdim. Oyuncunun
kendiliğinden verdiği karakter bilgisini alır, aynı bilgiyi tekrar sormazdım.

Başlangıç çekirdeği: kim, şu an ne istiyor, neyi güvenilir biçimde yapabiliyor,
neyin sınanmasını istiyor ve ne korunmalı? Bunlar tek dev soruya toplanmaz.
Boy, kilo, beden ölçüleri ve eksiksiz görünüş kartı ise yalnız oyuncu önemsiyorsa
veya yaklaşan çözümleme gerçekten gerektiriyorsa ayrıntılanır. Genel görünüş
ve oyuncunun verdiği ayırt edici özellikler yeterli olabilir. Belirtilmemiş
bedensel ayrıntıdan engel, avantaj veya NPC hükmü çıkarılmaz.

Quick'in ortak metnindeki “sınanacak/dokunulmayacak yönü vaat edilen tondan
türet” kuralını kaldırırdım. Ton kişisel iznin yerine geçemez. “Bunu sonra
keşfetmek istiyorum” cevabı, GM'nin kendine sınama izni vermesi değildir.

**Yerleşim:** Quick/Standard karakter yönergeleri, `player.md` ve mevcut
`boundaries.md`; Deep'in karakter tohumu → gerçekleşme ayrımı korunur.
**Kabul ölçütü:** Kilosunu vermeyen bir karakter oynanabilir; eksik alan
uydurulmaz. “Ailemi ihanet konusu yapma” kaydı yeni bağlamda da bulunur.
**Bağlı bulgu:** F06.

Dayanak: [Quick sırası ve çıkarım sınırı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_quick_v9.md:15>),
[Quick kişisel sınama çıkarımı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_quick.md:95>),
[Standard görünüş sorusu](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_deep.md:117>).

## D04 — Seçilmemiş, ertelenmiş ve reddedilmiş unsurları ayırırdım

Mevcut router bütün seçilmeyen adayları uykuda tutmayı istiyor. Dünya
bağımsızlığını korumak için yararlı; açık ret için uygun değil.

| Oyuncunun sözü | Tasarım karşılığı |
| --- | --- |
| “Limanı seçiyorum.” | Diğer adaylar yalnız bu seçimden dolayı yasaklanmaz; kabul edilen kapsam içindeyse geri planda kalabilir |
| “Lonca siyaseti istemiyorum.” | Bu deneyim yönü reddedilmiştir; başka adla yeni kanca olarak sunulmaz |
| “Lonca meselesi sonra olabilir.” | Ertelenir; kabul edilen bir koşulla daha sonra anlamlı olabilir |
| “Lonca bu dünyada hiç olmasın.” | Dünya öncülüne ilişkin açık karardır; kaynak/canon sözleşmesiyle çatışıyorsa tek uyuşmazlık açıklığa kavuşturulur |

İstenmeyen oyun odağı ile dünyanın var olan bir olgusunu silmek aynı işlem
değildir. Kurulumdaki ret kendi kapsamıyla `palette.md`, `boundaries.md` veya
ilgili deneyim sahibine gider; yeni bir yasaklar veritabanı gerekmez.

**Kabul ölçütü:** Reddedilen deneyim sonraki hazırlıkta ve act'te geri gelmez;
sırf seçilmeyen seçenek de yanlışlıkla evrenden silinmez.

Dayanak: [adayları koruma kuralı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/WORKFLOW.md:158>),
[mevcut palette sahibi](</D:/Repog/Codex RePoG/public/RePoG/campaign/palette.md:22>).

## D05 — Oynama biçimini az sayıda somut sonuç üzerinden seçtirirdim

Bağlama uygun kartlar, mekaniklerin açık kabulü ve takip ile gerilimin
ayrılması zaten var. Ben kartları çok sayıda ayarın kısa adlarını içeren bir
paket yerine, seçimin yaşanacak farkını açıklayan öneriler olarak düzenlerdim:
“Yolculukta erzak ve geçen zaman kayda girecek; azaldığında sonraki seçimin
değişecek.” Ardından gereken bağımsız tercih kendi sırasında alınır.

Çözümleme biçimi belirsiz kalırsa kısa bir oyun dışı örnek kullanılabilir:
aynı eylemde güvenilir yetkinlik, gerçek karşı koyma ve kayıtlı zarın rolü.
İnce dünya çekirdeği ve temel yetkinlik bilindikten sonra, ayrıntılı ekolojiye
geçmeden bu belirsizliği çözmek sonraki hazırlığın yanlış sisteme dayanmasını önler.
Bu zorunlu prova veya yeni onay turu olmaz. Örnek kurgu ilerletmez; karakter
adına karar vermez; gerçek zar, kaynak harcaması veya continuity kaydı yapmaz.

Dashboard, görsel, World Voices ve Agent Seats'in her biri bağımsız kalır.
Oyuncu istemediyse kapalı kalır; gerekli teknik kayıt yalnız kabul edilen
özellikten türetilir. Sonradan açılabilecek bir yüzeyin bütün ayarlarını
başlangıç görüşmesine taşımam.

**Kabul ölçütü:** Takip seçilince gereken ilk işlem çalışır; kapalı yüzey normal
oyunu engellemez. Sakin ama ayrıntılı takipli oyun geçerli bir kombinasyondur.
**Bağlı bulgular:** F04, F08–F10.

Dayanak: [mevcut sistem kartı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_quick.md:132>),
[takip yükümlülükleri](</D:/Repog/Codex RePoG/public/RePoG/campaign/rules.md:102>).

## D06 — Hazırlığı nedensel yeterliliğe göre büyütürdüm

İnce dünya çekirdeği, bağımsız NPC ve tarafsız eylem alanı zaten doğru
mekanizmalar. Bunların etrafındaki “her seçilen unsur için üç-dört yan koşul”
gibi genel kotaları kaldırırdım. Önemli ayrıntı, bir seçimin sonucunu, kişinin
davranışını veya dünyanın hareketini açıklıyorsa üretilir. Her meseleye zorla
karşı akım veya büyük örgüt eklemek gerekmez.

Hazırlık kendi içinde şu durumlarla sınanır: oyuncu ilgilenir; ilgilenmez;
gündelik bir iş yapar; başka yere gider. Bunlar dört yazılmış olay dalı değildir.
Mevcut yerin, insanların ve süreçlerin bu tercihler altında hâlâ anlamlı olup
olmadığını kontrol etme biçimidir. Açılışı reddetmek aynı talebi başka NPC'den
getirmemeli. Dünyanın gerçek sonuçları da oyuncuyu geri çekmek için
hızlandırılmamalı veya silinmemeli.

Hazırlanmayan uzak yer bilinmez kalabilir; kabul edilen seyahat ve kaynak
kuralları geçerlidir. “Her yere gidebilirsin” diye doğrulanmamış geniş bir dünya
vaat edilmez. Dünya tasarımına katılma yetkisi, oyuncuya gizli olayları ve
çözümleri seçtirmek anlamına gelmez.

**Kabul ölçütü:** İlk kancanın reddi, sakin başlangıç ve kapsam dışına çıkış
senaryoları oynanabilir; tüm dünya karakterin etrafında dönmez.
**Bağlı bulgular:** F07, F09, F13.

Dayanak: [mevcut ayrıntı kotası](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/WORKFLOW.md:158>),
[mevcut oyun içi ret davranışı](</D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_arc_transition.md:37>).

## D07 — Son incelemede cevapların oyuna ne kattığını görünür kılardım

Mevcut tasarım kabulünü ve gerçek hazırlığın tek seferde kabulünü korurum.
İkincisini yeniden bir soru listesi yapmam. Hazır içeriğin kısa gösterimi,
oyuncunun önemli seçimlerinden birkaçının somut karşılığını da açıklar:

- İstenen araştırmacı deneyimi, gerçek bir erişim/araç/iletişim fırsatı bulmuş mu?
- Sınanması istenen yön için fırsat var mı; korunacak yön aynı anda korunuyor mu?
- Dünyanın oyuncudan bağımsız süreci ve sakin/gündelik eylem olanağı var mı?

Bu bölüm bütün mekanik ayrıntıları veya gizli bilgiyi açıklamaz; başarı sonucu
vaat etmez. Seçimler yalnız açılışın sıfatlarını değiştiriyorsa hazırlık yeterli
değildir. Karar kendi sahibinde, fırsat ilgili yer/karakter/durum sahibinde,
hazırlık gerekçesi mevcut `first_session.md` içinde kalır.

Sesin örnekle seçilmesi ve Deep Stage 9'daki kurgu ilerletmeyen anlatı kanıtı
zaten var. Eklediğim şey, seçilmiş sesin neden işe yaradığını mevcut
`storytelling.md` referansında korumak ve değerlendirmede başka sahne işlevine
taşımak: sakin diyalogdaki ses, bir sonucu veya keşfi anlatırken de oyuncunun
iradesini koruyor mu? Her kurulum için üç yeni örnek zorunluluğu konmaz;
gerektiğinde mevcut inceleme içinde kalibrasyon yapılır.

**Kabul ölçütü:** Aynı dünya çekirdeğinde iki farklı kabul edilmiş oyuncu
deneyimi anlamlı biçimde farklı eylem fırsatları yaratır. Reddedilmiş anlatıcı
alışkanlığı farklı sahne türünde geri dönmez. **Bağlı bulgular:** F06, F07.

Dayanak: [gerçek hazırlık incelemesi](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/preparation_review_v9.md:15>),
[mevcut anlatı kanıtı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/deep_v8/09_first_act_preparation.md:25>).

## D08 — Kabul edilen deneyimi oyunun küçük ama sürekli başvurduğu bir sözleşme yapardım

Yeni bir tercih dosyası açmam. `player.md` deneyimi ve tematik sınırı,
`boundaries.md` somut GM davranışı ve yetkiyi, etkin profil çalışma ayarlarını
taşır. `session_brief.md` ilgili başlıklara bağlantı verir; kendi başına
aynı gerçeğin ikinci kopyası olmaz.

Korunacak sınırlar sürekli erişilebilir; istenen faaliyet ve sınanma yönleri
sahne/baskı seçerken okunur. Act hazırlığında açık oyuncu yönüyle neyin değiştiği,
neyin hâlâ geçerli olduğu ve neyin şimdilik uykuda kalacağı ele alınır.
`current_goal`, oyuncunun o andaki hedefidir; bütün kampanya deneyiminin yerine
geçmez. Bir süre sessiz kalmak da kalıcı tercih değişikliği sayılmaz.

**Kabul ölçütü:** Önceki konuşmayı görmeyen yeni GM bağlamı, ilk açılıştan sonra
ve act geçişinden sonra korunan sınırları bulur; bunu bütün kampanyayı taramadan
yapar. **Bağlı bulgular:** F06, F07, F13.

## D09 — Değişiklik yapmayı kapsamına uygun, olağan bir işlem hâline getirirdim

OOC ve sınırı her zaman değiştirebilme zaten var. Uygulama şu farkı korumalı:

| İstek | Etki |
| --- | --- |
| “Bu konuşmayı biraz kısalt.” | Yerel anlatım yönlendirmesi; otomatik kalıcı tercih değildir |
| “Bundan sonra anlatım daha kısa olsun.” | Gelecek anlatım için kalıcı profil/davranış değişikliği |
| “Ailemi artık bu tür çatışmanın içine sokma.” | Tematik sınır hemen daralır; ona bağlı oynanmamış hazırlık uyarlanır |
| “Zarı artık ben atayım.” | Çözümleme ayarı ve ilgili çalışma sözleşmesi değişir |
| “Bu sahne hiç yaşanmamış olsun.” | Açık kurgu revizyonu; etkilenen sahipler birlikte ele alınır, yalnız özete yazılmaz |

Değişiklik yalnız ilgili sahipleri ve bağımlı hazırlığı etkiler. Normal bir
üslup değişikliği bütün Session 0'ı yeniden açmaz. Daralan sınırın uygulanması
bekletilmez; önemli sonuçları belirsiz bir revizyonda yalnız gereken açıklama
istenir. Tarihsel başlangıç onayı, şu an geçerli tercih olarak kullanılmaz.

**Kabul ölçütü:** Yerel ve kalıcı istek ayrımı, yeni bağlamda kalıcılık, ayar
değişikliğinin çalışan işlemi ve onay sonrası yeniden düzenleme birlikte
sınanır. **Bağlı bulgular:** F01, F03, F06, F11.

## Örnek görüşme davranışı

Oyuncu: “Küçük bir liman kasabasında eski bir gemi tamircisi olayım. Sakin
araştırma hoşuma gider; ailemi ihanet konusu yapmayalım. Zar konusunda
kararsızım. Lonca siyaseti istemiyorum.”

GM'nin yapacağı: liman/meslek/istenen faaliyet/aile sınırı/istenmeyen siyaseti
ayrı mevcut sahiplerine kaydetmek; zarı kararsız bırakmak; yaş, kilo, gizli
geçmiş veya aileye tehdit uydurmamak. Henüz çözülmemiş izinler kendi sırasında
alınır. Araştırma tercihi otomatik gizli katil, zorunlu ana görev veya yetkinlik
garantisi oluşturmaz.

Daha sonra çözümleme seçimi geldiğinde, yalnız bu belirsizliğe döner:
“Tamir bildiğin rutin işleri doğrudan başarabilirsin. Gerçek belirsizlikte
sonucu kurulu koşullara göre değerlendirmemi mi, açık bir zarla çözmemizi mi
istersin?” Bu örnek nihai soru metni değildir; daha önce verilmiş cevapları
yeniden istememe ve tek bağımsız karara odaklanma davranışını gösterir.

Hazırlık incelemesinde, oyuncunun onayladığı dünyada gerçekten oluşturulmuşsa
tamir bilgisinin işe yaradığı bir erişim veya inceleme fırsatı gösterilir.
Henüz üretilmemiş hazırlık varmış gibi sunulmaz. Oyuncu fırsatı reddederse
kendi seçtiği işi yapabilir; atölye ve kasaba rutinleri anlamlı kalır.

## Tek uygulama paketinin iş sırası

Tek kapsam aşağıdaki altı iş paketidir. Bunlar ayrı ürün girişimleri veya
her biri için yeni bir onay turu değildir; uygulamanın bağımlılık ve test
sırasıdır. Önceki 13 bulgunun tamamı burada yer alır.

| İş | Kapsam | Başlıca değişecek yüzeyler | Tamamlanma kanıtı |
| --- | --- | --- | --- |
| P01 — Sağlam devir ve düzeltme | F01–F04, F11; D09'un temeli | `session_zero_state.py`, `check_state.py`, World Voices kontrolü, finalization | Hazır → açılışın tüketilmesi/OOC kaydı → ilk durable → gerçek tam kontrol geçer; değişmez kanıta müdahale ve eski onayı tekrar kullanma reddedilir |
| P02 — Ortak karar sözleşmesi | F05, F10, F12; D01, D02, D03 | Sürümlü router/playbook/manifest, setup kontrolü, karar özetleri | Yeni rota gerekli kararlarla tamamlanır; eksik izin geçmez; çok cevaplı mesaj ve durup devam etme tutarlı; mevcut rota onayları korunur |
| P03 — Kabulün çalışan hazırlığa dönüşmesi | F08, F09; D04, D05, D06 | Sistem/seyahat/ekoloji yönergeleri, profil–mekanik kontrolü, palette/default eşlemesi | Açılan takip işlemi çalışır; ret geri dönmez; kapalı seçenek kapalıdır; ilgisiz ayrıntı kotası yoktur |
| P04 — Gerçek hazırlık ve ses kalibrasyonu | D07; D03–D06'nın görünür karşılığı | Hazırlık incelemesi, mevcut anlatı kanıtı, first-session/storytelling | Kabul edilmiş seçimler somut hazırlıkta görülür; gizli bilgi sızmaz; hazırlık örneği oyun turu sayılmaz; değişmeyen paket tekrar onaylatılmaz |
| P05 — Oyunda ve sonraki act'te devamlılık | F06, F07, F13; D08, D09 | GM bağlamı, mevcut owner başlıkları, brief referansları, distill/next-act | Yeni bağlam sınırları bulur; ret ve yeni yön sonraki act'i etkiler; bağ dosyası canlı NPC bilgisinin kopyası olmaz |
| P06 — Birleşik kanıt | F01–F13 ve D01–D09 | Hedefli Python testleri, mevcut değerlendirme protokolüne bağlı sentetik oynatım | Aşağıdaki yapısal ve davranışsal kontroller ayrı sonuçlarla raporlanır |

Uygulamada yeni authoritative kampanya dosyası, anlatı motoru veya sıradan
tura ikinci bir model eklenmez. Kararların anlamını model belirler; araçların
görevi işlem, revision, izin kaydı, referans ve yapısal tutarlılıktır.

### Sürüm ve kapsam kararı

Soru sırası/sayımı veya zorunlu karar kümesi değişen yeni kurulum sözleşmesi
sürümlenir. Aktif v6–v9 kurulumlar ve mevcut Deep ledger kendi kabul edilmiş
sözleşmesini korur; yeni manifest maddeleri eski tamamlanmış kurulumları
kendiliğinden eksik yapmaz. Yeni dağıtım yeni sözleşmeye başlar. Mevcut bir
kampanyada geçiş istenirse eski cevaplar eşlenir, yalnız gerçekten yeni ve
gerekli kararlar sorulur; geçmiş onay yeni sözleşmenin onayı sayılmaz.

Snapshot/canlı süreklilik ve kapalı özellik hataları desteklenen mevcut
sürümlerde de geriye uyumlu düzeltilir. Ortak kontrol kullanan Companion için
regresyon testi yapılır; RPG tasarım değişikliği Companion görüşmesini yeniden
yazma kapsamına dönüştürülmez. Canlı kişisel kampanyalar test malzemesi olmaz.

### Tamamlanma sınaması

| Sınama | Aranan kanıt |
| --- | --- |
| Güncel Quick/Standard/Deep ve desteklenen eski rota | Kurulumdan ilk oyun kaydına ve yapılandırılmış kontrol sınırına kesintisiz geçiş |
| Onay sonrası düzeltme | İlgili onay/evidence geçersizleşir; eski kanıt korunur; yeniden kabul mümkün olur; ilgisiz kararlar tekrar sorulmaz |
| Başlangıç kanıtı bütünlüğü | Normal oyun ilerlemesi geçer; geçmiş snapshot/report değiştirilmesi geçmez |
| Az cevap / çok cevap / kararsızlık | Gereksiz tekrar ve izinsiz çıkarım yok; gerekli açık karar kaybolmaz |
| Açık ret / seçmeme / erteleme | Üçü farklı ve kendi kapsamıyla korunur |
| Gerçek seçenek etkisi | Aynı dünya çekirdeğinde iki farklı oyuncu deneyimi farklı oynanabilir fırsatlar üretir; başarı önceden yazılmaz |
| İlk kancayı reddetme ve sakin oyun | Yeniden paketlenmiş dayatma yok; bağımsız NPC ve dünya işleyişi sürer |
| Sesin başka sahneye taşınması | Diyalog, keşif ve sonuç anlatımında seçilmiş davranış korunur; metin kalıbı kopyalanmaz |
| Gerçek yeni bağlam / act geçişi | Owner kaynakları yeterlidir; görüşme transcript'i veya yeni uydurulmuş özet gerekmez |
| Yerel ve kalıcı OOC değişiklik | Etki kapsamı doğru; sınır hemen uygulanır; kalıcı karar yeniden açılışta korunur |
| İsteğe bağlı özellikler ve Companion | Kapalı özellik ilgisiz işlem yüklemez; ortak kontrol düzeltmesi diğer deneyimi bozmaz |

Yapısal test sonucu ile anlatı başarısı ayrı raporlanır. Davranışsal oynatım,
[mevcut değerlendirme protokolünü](</D:/Repog/Codex RePoG/public/RePoG/evaluation/README.md:8>)
izler: sentetik çalışma alanı, gerçek kalıcı işlemler, gerektiğinde önceki
konuşmayı almayan yeni bağlam, dondurulmuş kanıt ve sonradan bağımsız okuma.
Çalıştırılmayan bölüm `not_verified`, ölçülmeyen süre `not_measured` kalır.
Bir kısa örnekten daha iyi hikâye veya daha hızlı kurulum sonucu çıkarılmaz.
