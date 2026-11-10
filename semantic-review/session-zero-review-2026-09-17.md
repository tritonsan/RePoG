# Session 0 ve oyuna devir incelemesi

17 Eylül 2026 · İncelenen commit: `2ed60778ed22a7e9983da126f2453759900c139b`.

Bu incelemenin üzerine eklenen dokuz tasarım değişikliği ve F01–F13'ün tamamını
birleştiren uygulama sırası:
[Session 0 tasarımı ve birleşik plan](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/session-zero-integrated-plan-2026-09-17.md>).
Bu ek, uygulanmış değişiklik veya yeni test sonucu değildir.

Session 0'ın tasarımı güçlü: oyuncunun tercihlerini dünya, karakter, anlatım ve
oyun kurallarının sahiplerine dağıtıyor; gerçek hazırlanmış içeriği başlangıçtan
önce inceletiyor. Ancak **kurulumu tamamlamak ile o kurulumdan sağlıklı biçimde
oynamaya devam etmek aynı ölçüde güvence altında değil**. İlk kalıcı hamleden
sonra hata veren kontroller ve kayda alınmasına rağmen sonraki GM bağlamında
okunması garanti edilmeyen tercihler var.

Bu çalışma Designer incelemesidir. Ürün kodu, iş akışları ve canlı kampanya
değiştirilmedi. Yalnız bu rapor ve geçici sentetik kampanyalarla çalışan deney
dosyaları oluşturuldu. Bulguların kanıt düzeyi ayrı belirtilmiştir: çalışan
entegrasyonda yeniden üretim, izole kontrol deneyi veya kaynak sözleşmesi açığı.
Gerçek oyuncuyla görüşme, süre/yorgunluk ölçümü ve yeni bağlamda anlatı oynatımı
yapılmadı.

## Kararların oyundaki karşılığı

| Session 0 kararı | Kalıcı sahibi | Oyun sırasında kullanım | Sonuç |
| --- | --- | --- | --- |
| Anlatım sesi, POV, tempo, kaçınılacak alışkanlıklar | Etkin `play_profile.yaml`; açıklama için `storytelling.md` | GM profilini her tur okuyor | Açık bağlantı var; edebî başarısı ayrıca oynatımla ölçülmeli |
| Yetenek modeli ve karakterin yapabilecekleri | `player.md`, `rules.md` | GM'nin sürekli bağlamı; karşı koymayı aynı ölçekte değerlendirme | Açık bağlantı var |
| Zar ve kayıt sıklığı | Profil, mekanik kayıtları | Kalıcı işlem zar referansı isteyebiliyor; profil distill politikasını belirliyor | Çalışan araç bağlantısı var |
| Ayrıntılı eşya/zaman/yol takibi | Profil, `mechanics_state.json` | Kural tablosu işlemleri zorunlu sayıyor | Profil ile etkin mekanik altyapısı arasında doğrulama açığı var; F08 |
| İçerik sınırları ve yaratım yetkisi | `boundaries.md` | İki kısa blok sürekli okunuyor | Açık bağlantı var |
| İstenen kişisel deneyim, sınanmayacak karakter yönleri, somut GM davranışları | `player.md`, `boundaries.md` | İlgili bölümler için açık ve zorunlu okuma yolu yok | Kaydedilme ile uygulanma arasında boşluk var; F06 |
| Karakter–dünya karşılıklı bağlantısı | `player_ties.md`, dünya/karakter sahipleri, ilk açılış hazırlığı | İlk açılışta açık; sonraki act değerlendirmesinde daha zayıf | Kısmi bağlantı; F07, F13 |
| NPC bağımsızlığı | Karakter Agency Card, `active_cast.md`, ilişki ve bilgi sahipleri | Diyalog, bulunabilirlik ve sahne dışı hareket playbook'ları | Açık bağlantı var |
| Hazırlığın kabulü ve başlangıç kanıtı | Kurulum kararı/kapıları, kilitli profil, başlangıç snapshot'ı | Readiness ve tam kontrol | İlk normal değişimle çatışıyor; F01–F04 |

Olumlu bağlantıların kaynakları: [GM bağlamı](</D:/Repog/Codex RePoG/public/RePoG/workflows/gm/WORKFLOW.md:30>),
[kayıt politikası](</D:/Repog/Codex RePoG/public/RePoG/tools/rpg_state.py:419>),
[zar referansı](</D:/Repog/Codex RePoG/public/RePoG/tools/rpg_state.py:622>),
[NPC diyaloğu](</D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/dialogue_social.md:8>) ve
[sahne dışı hareket](</D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/travel_downtime.md:59>).

## Önce düzeltilmesi gerekenler

### F01 — P1: Başlangıç kanıtı yaşayan kampanyayı donduruyor

**Kanıt: tam Deep v8 entegrasyonunda yeniden üretildi; genel rota kontrolü ayrıca izole sınandı.**
Hazır sentetik kampanya tam kontrolde sıfır hata verdi. Oyuncunun bir teslimat
işini kabul etmesini `commit-durable` ile kaydetmek başarılı oldu:
`narration_allowed=true`, continuity revision `0 → 1`. Sonraki tam kontrolde
`deep_v8_readiness_evidence_stale` ve `ready_snapshot_stale` oluştu.

Deep kontrolü başlangıç snapshot'ının dosya kümesini ve byte içeriklerini hâlâ
canlı kampanyayla karşılaştırıyor. Hazırlık aşamasının son çıktı hash'i de canlı
dosyalardan yeniden doğrulanıyor. Böylece geçmişte neyin onaylandığını kanıtlayan
kayıt, oyunun bugün de aynı kalması şartına dönüşüyor. OOC bilgilendirmesini
`boundaries.md` içine kaydetme ve kullanılmış açılışı `consumed` yapma gibi
zorunlu devir işlemleri de bu sözleşmeyle çelişiyor.

Genel Quick/Standard/Companion snapshot kontrolü ise başlangıçtaki continuity
revision'ını bugünkü revision'a eşit istiyor. İzole Quick kontrolünde `0`
geçerken `1` aynı hatayı verdi; bu üç rotanın tam oyun akışı ayrı ayrı sınanmadı.

**Düzeltme:** Kabul edilmiş hazırlığı kendi değişmez paketi ve setup revision'ı
üzerinden doğrulamak; canlı oyun sürekliliğini ayrı doğrulamak. Hem snapshot
karşılaştırması hem Stage 9 canlı hash kontrolü ele alınmalı. Her hamlede yeni
başlangıç snapshot'ı almak sorunu gizler ve başlangıç kanıtının anlamını bozar.

Kaynak: [canlı dosya karşılaştırması](</D:/Repog/Codex RePoG/public/RePoG/tools/session_zero_state.py:1110>),
[hazır durumdaki sürekli kontrol](</D:/Repog/Codex RePoG/public/RePoG/tools/session_zero_state.py:1290>),
[Stage 9 hash'i](</D:/Repog/Codex RePoG/public/RePoG/tools/session_zero_state.py:1314>),
[genel snapshot kimliği](</D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:1651>).

### F02 — P1: Güncel Deep v9, hazır olduğu anda başka doğrulama yoluna sapıyor

**Kanıt: tam lifecycle fixture'ı schema 9 ile yeniden üretildi.** Kurulum
testinin mevcut bütün assertion'ları ve canonical ready doğrulaması geçti;
hemen ardından tam kontrol `ready_snapshot_stale` verdi.

Özel Deep snapshot yolu yalnız `schema_version == 8` koşuluyla seçiliyor.
Dağıtım şablonu v9 ve Deep akışı v8+ için devam ettiği hâlde, v9 genel kontrol
yoluna düşüyor. Bu yol Deep'in hazır olmadan önce alınan aday snapshot'ında
`ready=true/complete` bekliyor.

**Düzeltme:** Rota seçimini ortak ve açık bir Deep akış koşulunda toplamak;
güncel dağıtım şablonuyla final gate sonrası tam kontrolü test etmek.

Kaynak: [sürüm ayrımı](</D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:1703>),
[güncel şablon](</D:/Repog/Codex RePoG/public/RePoG/campaign/setup_profile.yaml:1>).

### F03 — P1: Onaylanmış Deep tercihinin düzeltilmesi yeniden incelemeye dönemiyor

**Kanıt: hazırlık onayından sonra, hem ready öncesinde hem sonrasında yeniden üretildi.**
`01_player_fantasy_tone_and_non_goals` değişikliği revision 59 ve 60'ta aynı
`state_invalid` sonucuyla reddedildi: `09_design_direction_review` kararı,
`first_act_design_complete` kapısından önce kaydedilmiş sayılıyor. İlgili kayıt
dosyalarının değişmeden kalması olumlu; istenen düzeltme yolu ise çalışmıyor.

Üst karar değişince bağımlı kapılar geçersizleşiyor; eski onay kararları güncel
onaymış gibi doğrulanmaya devam ediyor. İşlem kendi geçersizleştirdiği geçmiş
onaya takılıyor.

**Düzeltme:** Eski onay kanıtını tarihsel tutup güncel geçerliliğini kapılarla
birlikte atomik olarak düşürmek. Yeni onayı yeni girdi revision/hash'ine bağlamak.
Aynı kabul cevabının yeni hazırlık için tekrar verilmesi, `created_revision` ve
`no_change` davranışı da sınanmalı; yalnız hata kontrolünü gevşetmek yetmez.

Kaynak: [onay bağımlılığı kontrolü](</D:/Repog/Codex RePoG/public/RePoG/tools/session_zero_state.py:943>).

### F04 — P1: Kapalı World Voices, sıradan ilerlemeden sonra hata üretiyor

**Kanıt: F01'deki tam entegrasyonda ayrıca yeniden üretildi.**
`world_voices.mode=off`, `artifacts={}` ve indeks revision'ı 0 iken ilk başarılı
kalıcı işlemden sonra `world_voices_continuity_stale` oluştu. Tam kontrol,
dosyanın bulunmasını denetimi çalıştırmak için yeterli görüyor; World Voices
kontrolü kapalı/boş durumda da genel revision eşitliği arıyor.

**Düzeltme:** Kapalı ve hiç kullanılmamış isteğe bağlı yüzeyi uykuda tutmak.
Etkin içerik için son ilgili değişimin ve gerçek bağımlılıkların geçerliliğini
kontrol etmek. İlgisiz her turda boş indeksi yazmak gerekmemeli; mevcut etkin
içerik kontrolleri topluca kapatılmamalı.

Kaynak: [koşulsuz revision eşitliği](</D:/Repog/Codex RePoG/public/RePoG/tools/check_world_voices.py:170>),
[tam kontrol çağrısı](</D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:4539>).

### F05 — P1: Standard v9 karar sayısı sözleşmeleri çakışıyor

**Kanıt: aktif rota talimatları ile çalışan doğrulayıcının karşılaştırması.**
Standard v9, 20 modül ve 20–29 karar istiyor; modül 1–19'un semantik yönergelerini
ortak playbook'tan alıyor. Oradaki açık bölünmeler sıradan `fictional` karakter
yolunda hesabı 30'a çıkarıyor: 20 temel; M1'de 1, M3'te 1, M4'te 2, M5'te 3,
M6'da 1, M7'de 1 ve M15'te 1 ek karar. Sayısal/bantlı yolda türetilen sınır ve ek
olmaması bazı kararları azaltabilir; her olası kurulumun en az 30 olduğu iddia
edilmiyor. Fakat açıkça desteklenen bu yol, doğrulayıcının 29 üst sınırıyla
uyuşmuyor. Eski bütçe talimatını dışlamak, miras alınan ayrı karar gerekliliklerini
tek başına açıklığa kavuşturmuyor.

**Düzeltme:** Karar hesabının tek sahibi olmalı. Hazır olmayı tamamlanmış gerekli
kararlara bağlamak; sayıyı ilerleme/yorgunluk göstergesi olarak kullanmak daha
sağlam. Bağımsız izin veya karakter kararlarını sırf kotaya sığdırmak için
gizlice tek karar saymamak gerekir.

Kaynak: [v9 rota](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_v9.md:4>),
[bölünmüş kararlar](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_deep.md:57>),
[sert üst sınır](</D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:938>).

### F06 — P1: Kişisel deneyim ve tematik sınırlar için zorunlu kullanım yolu eksik

**Kanıt: kaynaklarda okuma sözleşmesi açığı; oynatımda ihlal gözlenmedi.**
Kurulum karakterin neyi sınansın/neye dokunulmasın istediğini özellikle soruyor.
`Player Experience Contract`, `Change Appetite` ve somut `Good/Bad GM Behavior`
bölümleri bunun kalıcı kayıtları. GM'nin sürekli okumaları ise profil,
güncel sahne, karakterler, içerik sınırları, yaratım yetkisi ve yetenek modelini
açıkça kapsıyor; bu deneyim bölümlerini aynı açıklıkla bağlamıyor.

Yeni bağlamdaki GM bütün zorunlu okumaları yerine getirip yine de örneğin
“aile bağımı ihanet sınavına dönüştürme” tercihine veya reddedilen bir anlatıcı
davranışına ulaşmayabilir. Genel içerik sınırı bu özel tematik tercihin yerine
geçmez. Profildeki `avoid_habits` bazı üslup tercihlerini taşır; sınırlar
dosyasındaki tüm somut GM davranışlarının yerine geçtiği tanımlanmamış.

**Düzeltme:** Mevcut sahiplerden gelen küçük bir etkin deneyim sözleşmesi.
Korunan tematik sınırlar ve geçerli sonuç sınırları sürekli erişilebilir;
istenen sınanma/etkinlik yönleri sahne ve baskı seçerken okunur olmalı. Brief
yalnız sahibine bağlantı versin; ikinci bağımsız gerçek kaydı oluşmasın. Her tur
tüm Session 0 konuşmasını okumak veya yeni anlam denetleyicisi eklemek gerekmez.

Kaynak: [istenen deneyim](</D:/Repog/Codex RePoG/public/RePoG/campaign/player.md:13>),
[değişim isteği/sınırı](</D:/Repog/Codex RePoG/public/RePoG/campaign/player.md:135>),
[somut GM davranışları](</D:/Repog/Codex RePoG/public/RePoG/campaign/boundaries.md:177>),
[mevcut zorunlu okumalar](</D:/Repog/Codex RePoG/public/RePoG/workflows/gm/WORKFLOW.md:51>).

## Diğer önemli bağlantı ve görüşme iyileştirmeleri

### F07 — P2: Karakter–dünya bağı ilk açılıştan sonraki act'lere açıkça taşınmıyor

**Kanıt: sonraki act hazırlığına özgü okuma açığı.** İlk açılışın karşılıklılık
hazırlığı ve tüketilme yaşam döngüsü açık. Distill, `player_ties.md` dosyasını
kalıcı gerçek sahibi olarak tanıyor; dolayısıyla dosya sistemden tamamen kopuk
değil. Ancak yeni act'in carry-forward okumaları, kabul edilen kişisel deneyim
ve karşılıklılık bölümlerini özellikle istemiyor. Horizon ve gösterilmiş
beklentilerin taşınması, oyuncunun başlangıçta istediği deneyimi yeniden
değerlendirmenin yerine geçmiyor.

**Düzeltme:** Act hazırlığında hangi kişisel bağların/deneyimlerin hâlâ geçerli,
oyuncunun yönüyle değişmiş veya şimdilik uykuda olduğunu mevcut sahiplerden
değerlendirmek. Açık ret yeni yön için kanıt olmalı; aynı kişisel kancayı farklı
kılıkla zorlamak veya her act'te yeniden görüşme yapmak gerekmemeli.

Kaynak: [ilk açılış uyumu](</D:/Repog/Codex RePoG/public/RePoG/campaign/first_session.md:45>),
[kalıcı sahiplerin tanınması](</D:/Repog/Codex RePoG/public/RePoG/workflows/distill/WORKFLOW.md:87>),
[carry-forward okumaları](</D:/Repog/Codex RePoG/public/RePoG/workflows/distill/WORKFLOW.md:373>).

### F08 — P2: Takip tercihi kabul edilip gereken mekanik kayıt etkinleşmeyebiliyor

**Kanıt: izole profil doğrulaması ve gerçek mekanik işlem çağrısı.** Boş modül
listesi ve kapalı mekanik kayıtla `quantified`, `conditions`, `step` ve
`route_time` seçimleri profil kontrolünden hatasız geçti. Geçerli bir
`advance_time` işlemi “deterministic mechanics are not enabled” ile reddedildi;
aynı işlem kayıt etkinleştirilince başarılı oldu.

Bu deney bütün hazır kampanyanın kontrolden geçtiğini iddia etmez. Gösterdiği
açık, profil doğrulamasının etkin mekanik gereksinimini yalnız modül listesinden
çıkarması; takip seçimlerinin aynı garantiye bağlanmamasıdır.

**Düzeltme:** Kabul edilen takip bayrakları ve modüllerden gereken asgari
mekanik kaydı birlikte türetmek; hazır olma sınırında ilgili ilk işlemin
çalışabileceğini doğrulamak. Oyuncunun onaylamadığı ek mekanikleri açmamak.

Kaynak: [tek yönlü etkinlik kontrolü](</D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:1545>),
[işlemde etkinlik şartı](</D:/Repog/Codex RePoG/public/RePoG/tools/resolve_mechanic.py:479>),
[takip yükümlülükleri](</D:/Repog/Codex RePoG/public/RePoG/campaign/rules.md:102>).

### F09 — P2: Standard seyahat tercihleri kapalı Deep paketine bırakılıyor

Standard'da Deep paketleri boş kalıyor. Devralınan M11 yönergesi ise mesafenin
bedeli, harita bilgisi ve hareketin iz bırakması seçimlerini `location_network`
paketine bırakıyor. Standard için bu tercihlerin açık görüşme sahibi kalmıyor.
**Öneri:** Ortak kısa seyahat kararı Standard'da da bulunsun; Deep paketi yalnız
ayrıntı eklesin. Bu prosedür açığıdır, gözlenmiş bir oyun sonucu değildir.

Kaynak: [Standard kapsamı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_v9.md:6>),
[M11 devri](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_deep.md:336>).

### F10 — P2: Deep Agent Seats seçiminin zorunluluğu manifestte karşılık bulmuyor

Stage 7 playbook'u `07_agent_seats` için açık `off/on_demand` seçimi istiyor;
manifestte Stage 7'nin diğer beş kararı var. Tamamlanma kontrolü manifesti
izlediği için bu seçim olmadan geçebiliyor. Bilinmeyen karar kimliği
kaydedilebildiğinden “kaydetmek imkânsız” değil; zorunlu tamamlanma garantisi
eksik. Kapalı varsayılanın izinsiz açıldığı gösterilmedi.
**Öneri:** Kararı ve sahiplerini manifeste eklemek; zorunlu playbook kararlarının
manifestle eşleşmesini sınamak.

Kaynak: [zorunlu seçim](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/deep_v8/07_runtime_experience_contract.md:19>),
[manifest](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/deep_v8/manifest.json:809>),
[tamamlanma kontrolü](</D:/Repog/Codex RePoG/public/RePoG/tools/session_zero_state.py:1752>).

### F11 — P2: Deep dışındaki rotaların finalization sırası iki farklı anlatılıyor

Finalization playbook'u bütün rotaları `in_progress/false` tutuyor; sonraki
readiness değişimini yalnız Deep final gate'ine bağlıyor. Üst workflow ise
snapshot öncesinde son readiness alanlarının yazılmasını istiyor. Dolayısıyla
Quick/Standard/Companion için “hiç talimat yok” değil, çelişen talimat var.
**Öneri:** Aday ön kontrolü, kilit, readiness geçişi, snapshot ve son kontrol
sırasını rota bazında tek tabloda tanımlamak; helper davranışıyla aynı tutmak.

Kaynak: [finalization](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/finalization.md:157>),
[üst workflow](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/WORKFLOW.md:635>).

### F12 — P2: Deep kritik kararlarının sahiplerine yazılma zamanı tutarsız

Router aynı turda semantik sahip güncellemesini yalnız güvenlik, araştırma izni
ve yaratım yetkisi için açıkça istiyor; Deep README, aşama yönergeleri ve manifest
bütün kritik kararlar için istiyor. Veri kaybı yeniden üretilmedi; oturumu
kesip geri dönmede hangi kaydın güncel olduğu belirsizleşebilir.
**Öneri:** Kritik kararlara tek ve açık anında kayıt kuralı; diğer hazırlık
çıktılarının materialization zamanını ayrıca korumak.

Kaynak: [router](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/WORKFLOW.md:103>),
[Deep kuralı](</D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/deep_v8/README.md:36>).

### F13 — P2: Bağ şablonu güncel NPC gerçeklerinin ikinci kopyasını teşvik ediyor

`player_ties.md` rutin, bulunabilirlik, sonraki hareket, bilinen bilgi ve güncel
baskı istiyor. Bunlar karakter notu, active cast, bilgi/ilişki veya world domain
sahiplerinde zaten yaşıyor. Dolu kampanyada çelişki gözlenmedi; şablon çoğaltma
riski taşıyor.
**Öneri:** Burada kabul edilmiş bağın kökeni, kişisel anlamı ve yaratım sınırı
kalsın. Değişen gerçekler kendi sahiplerine bağlantı olsun; başlangıç örneği
tutulacaksa tarihsel olduğu açık olsun.

Kaynak: [canlı bağ alanları](</D:/Repog/Codex RePoG/public/RePoG/campaign/player_ties.md:105>),
[bilgi ve baskı alanları](</D:/Repog/Codex RePoG/public/RePoG/campaign/player_ties.md:139>),
[sahiplik haritası](</D:/Repog/Codex RePoG/public/RePoG/workflows/reference/authority-map.md:233>).

## Session 0'ın yönlendirme kalitesini artıracak tasarım

Her önemli karar için şu zincir görülebilmeli:
**oyuncunun kabulü → tek kalıcı sahip → ne zaman okunacağı → oyunda hangi
kararı etkilediği → oyuncu değiştirirse neyin geçersizleşeceği.**
Bu bir yeni dosya veya oyuncuya doldurtulacak alan listesi olmak zorunda değil;
mevcut kararların ve iş akışlarının bağlantı ölçütü olmalı.

1. **İnceleme kartında somut karşılık gösterme.** Örneğin “sakin araştırma”
   tercihinin ilk yerde hangi etkinliğe alan açtığı; “dünya benden bağımsız
   olsun” kararının NPC'nin işi ve bulunabilirliğinde nasıl karşılık bulduğu.
   Sonucu veya gizli bilgiyi ifşa etmeden hazırlanmış seçeneği göstermek.
2. **Açılışı birden fazla geçerli oyuncu yönüne hazırlama.** Kancayı kabul,
   ret, gündelik işle ilgilenme ve ayrılma yolları aynı kabul edilen dünyada
   anlamlı olmalı. Bunlar olay ağacı veya zorunlu sahne kotası değildir.
3. **Tercih ile vaat edilmiş sonucu ayırma.** “Yetenekli dedektif gibi
   hissetmek” soruşturma ve yetkinlik fırsatları doğurur; bütün çıkarımların
   doğru olmasını veya olayın önceden çözülmesini gerektirmez.
4. **Kabulün yeniden ele alınmasını görünür kılma.** Aşama özetleri neyin
   kilitlendiğini, hangi sıradan varsayımların yapıldığını ve hangi önemli
   seçimin kaldığını kısa biçimde söylesin. Süre/yorgunluk iddiası ölçümden
   önce yapılmasın. Deep'in 43 çekirdek kaydı, 43 zorunlu yeni soru demek değildir.
5. **Act sınırında deneyimi yeniden bağlama.** İlk tercihleri taşımak, oyuncunun
   oyun içinde keşfettiği yeni yönü bastırmamalı. İstenen faaliyet, korunacak
   tematik sınır ve bağımsız dünya hareketi birlikte ele alınmalı.

Korunması gerekenler: Quick v9 slot 9 ve Standard v9 modül 20'nin gerçek
hazırlık incelemesiyle başlangıç onayını birleştirmesi; Deep temel karakter
bilgilerinin Stage 5'te oynanabilir karakter kartına aktarılması; sesin soyut
etiketler yerine örnek anlatımlarla seçilmesi; sıradan varsayımların görünür
olması ve önceden cevaplanmış soruların tekrar sorulmaması.

## Doğrulama ve önerilen uygulama sırası

Mevcut `test_setup_v9.py` ve `test_session_zero_state_v8.py` odaklı çalışması:
**32 geçti**. Bununla birlikte mevcut tam Deep lifecycle testi hazır statü
sonucunda bitiyor; final aggregate kontrolü, ilk kalıcı hamle ve onay sonrası
düzeltme aynı senaryoda bulunmuyor. Yeşil test sonucu bu sınırların çalıştığını
kanıtlamıyor.

| Bu incelemede çalıştırılan deney | Sonuç |
| --- | --- |
| Deep v8 tam kurulum + ilk tam kontrol | 0 hata |
| Aynı kampanyada ilk kalıcı hamle | Başarılı; revision 1; anlatım izni var |
| Hamleden sonraki tam kontrol | 3 hata: iki readiness/snapshot, bir kapalı World Voices |
| Deep v9 tam kurulum + canonical ready doğrulaması | Başarılı |
| Deep v9 hazır durumda tam kontrol | 1 hata: `ready_snapshot_stale` |
| Onaylı tercihi ready öncesi/sonrası değiştirme | İkisinde de `state_invalid`; kayıtlar değişmedi |
| Genel snapshot kontrolünde revision 0 → 1 | Geçerli → `ready_snapshot_stale` |
| Dört takip seçiminin izole profil doğrulaması | Kapalı mekanikle hatasız |
| Aynı zaman işlemi, mekanik kapalı/açık | Reddedildi / başarılı |

Kanıtlar: [lifecycle deneyi](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-17-session-zero-audit/probe_session_zero.py>),
[sonuç JSON'u](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-17-session-zero-audit/probe_session_zero_results.json>),
[profil deneyi](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-17-session-zero-audit/profile_probe.py>),
[profil sonuçları](</D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-17-session-zero-audit/profile_probe_results.json>).
JSON içindeki sentetik kampanya yolları deneyin geçici yollarıdır; kampanyalar
deney sonunda temizlenmiştir.

Önerilen uygulama sırası:

1. **Devir ve yeniden düzenleme:** F01–F04 ve F11; hazır olmak, açılışı tüketmek,
   ilk gerçek hamleyi kaydetmek ve sonradan tercih düzeltmek aynı entegrasyonda
   çalışmalı. Değişmez hazırlık kanıtına müdahale yine reddedilmeli.
2. **Kararın etkisi ve sahiplik:** F06–F08 ve F13; sürekli bağlam küçük kalmalı,
   sonraki act kabul edilen deneyimle yeniden ilişkilendirilmeli.
3. **Görüşme rotalarının tutarlılığı:** F05, F09, F10, F12; modül/karar hesabı,
   zorunlu seçimler ve kayıt zamanı tek sözleşmeden izlenmeli.

Kabul testi yalnız `ready=true` ile bitmemeli: güncel Quick, Standard ve Deep;
desteklenen legacy yollar ve ortak snapshot mantığını kullanan Companion için
kurulum → açılış/handoff kaydı → ilk kalıcı değişim → yapılandırılmış ilk tam
kontrol sınırı → yeniden açma zinciri sınanmalı. Deep için düzeltme → eski
onayın geçersizleşmesi → yeni hazırlık → aynı kabul sözüyle yeni onay da olmalı.

Anlatı tarafında ayrı, yeni bağlamda bir oynatım gerekir: özel bir istenen
etkinlik, dokunulmayacak tematik sınır ve reddedilmiş GM davranışı yalnız gerçek
sahiplerinde saklanır. Açılış tüketildikten sonra ve bir act geçişinden sonra
GM'nin bunları bulması ve uygulaması değerlendirilir. Oyuncu ilk kancayı
reddeder; NPC kendi işiyle meşgul olur; sakin oyun ve farklı bir yön seçmek
mümkün kalır. Amaç aynı olayları üretmek değil, kabul edilen deneyim sınırları
içinde anlamlı biçimde uyum sağlamaktır. Normal tura ek model, semantik puanlayıcı
veya bütün kampanyayı tarayan bir kontrol önerilmiyor.
