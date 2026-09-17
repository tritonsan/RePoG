# RePoG — Anlatısal süreklilik ve hikâye kalitesi incelemesi

17 Eylül 2026 · İncelenen ürün commit'i: `849ad5af8e3ef16682e598b924a328a21db948b7`

Bu incelemenin ardından yapılan değişiklikler ve gerçek kontroller ayrı
[uygulama raporunda](narrative-quality-implementation-2026-09-17.md) tutulur.
Buradaki bulgular ve satır konumları yukarıdaki inceleme sürümüne aittir.

RePoG'un kayıt güvenliği, oyuncu iradesi ve yerel nedensellik temeli güçlü. En yüksek getirili sonraki çalışma, kaydedilen bilginin doğru anda bulunmasını, karakterlerin yaşadıklarının sonraki davranışlarına taşınmasını ve act'lerin birbirine anlamlı biçimde bağlanmasını sağlamaktır. Her sahnenin tutarlı olması, kampanyanın bütününün etkili bir hikâye oluşturduğunu tek başına göstermiyor.

Bu rapor Designer incelemesidir. Dağıtım şablonları, iş akışları, ilgili yardımcılar, değerlendirme paketleri ve önceki sentetik pilot incelendi. Kişisel kampanyalar kullanılmadı. Yeni oyun koşusu, yeni model karşılaştırması veya gerçek yeni bağlam testi yapılmadı; mevcut stil yardımcısı yalnız bellekte tanısal örneklerle çalıştırıldı. Pilotun kaynak commit'i `2657663` ve çalışma türü `fiction_only`; güncel HEAD'in yeni oynanış kanıtı sayılmadı. Aşağıdaki arıza örnekleri, özellikle pilot gözlemi olarak işaretlenenler dışında, sınanması gereken senaryolardır. Ürün davranışı değiştirilmedi.

**Kanıt türleri:** “Kontrat boşluğu” mevcut metin/kod bağlantısında doğrulanan eksiklik; “tasarım riski” bunun doğurabileceği fakat bu incelemede oynatılmamış sonuç; “pilot gözlemi” yalnızca kayıtlı sentetik örnekte görülen davranış; “ölçüm açığı” henüz elde edilmemiş kanıttır. P1 ilk uygulama dilimi; P2 onu izleyen kalite geliştirmesidir.

**Korunması gerekenler**

- Model kurgusal anlamı, karakter kararını ve anlatımı üstleniyor; yerel araçlar güvenli ve sınırlı kayıt yapıyor.
- Restart-loss testi, değişen gerçeğin sahibine hemen yazılması, işlem kimliği/revision ve kurtarma zaten var.
- NPC Agency Card, altı eksenli Contrast Pass, sıradan konuşma örneği, bağımsız amaç ve mekânsal varlık gerekçesi zaten var.
- Bilgi sahipleri, şüphe/bilinmeyen ayrımı, oyuncu yazarlığı, gerçek ret ve başarısızlıkla kapanış, dinlenme ve nedensel dünya hareketi zaten korunuyor.
- Sıradan her turda ikinci bir model hakemi, bütün kampanyayı okuma veya bütün dünyayı simüle etme gerekmiyor. Kalite geliştirmeleri bu tasarımı korumalı.

**1. P1 — Yeni act'e geçişte dramatik pusulanın yenilenmesi açık bir adım değil.**
Tür: kontrat boşluğu.

[campaign/threads.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/threads.md:41>) ilk act'in Compass'ını Session 0'da kuruyor. [workflows/gm/playbooks/scene_arc_transition.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_arc_transition.md:17>) act kapanışını bu pusulanın koşuluna bağlıyor. Buna karşılık [campaign/next_act_prep.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/next_act_prep.md:96>) ve [workflows/distill/WORKFLOW.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/distill/WORKFLOW.md:368>) yeni soruyu, yeni kapanış koşulunu ve eski kapanış kaydının ayrılmasını açıkça istemiyor. [tools/check_state.py](<D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:1020>) dolu alanları denetliyor; bunların başlayan act'e ait olduğunu doğrulamıyor.

İlk act'te defter bulunmuşken ikinci act'te eski “defter bulundu mu?” koşulu kalabilir. Eski pusula tarihçelenmeli; yeni act kimliği, açık soru, erişilebilir kapsam ve kapanış koşulları mevcut `threads.md` sahibinde kurulmalı. Hazırlık ve açılış buna referans vermeli. **Doğrulama:** birbirini izleyen iki act'in ayrı koşullarla kapanması; eski koşulun yeni act'i yeniden kapatmaması.

**2. P1 — Act'i kapatan eylemi fark ettirecek bilgi sıcak bağlamda garanti edilmiyor.**
Tür: kontrat boşluğu ve tasarım riski.

[workflows/gm/WORKFLOW.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/WORKFLOW.md:30>) profil, sahne, kadro, küçük brief ve ilgili bilgileri sıcak tutuyor; ödül durumu ayrıca isteniyor. Etkin Compass sorusu ve kapanışı etkileyen koşullar aynı açıklıkta yok. [campaign/session_brief.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/session_brief.md:35>) referans listesinde de bunlar yok. Oysa geçiş playbook'u belirleyici eylemin gerçekleştiği turda tanınmasını istiyor.

Kısa bir konuşma uzun anlaşmazlığı bitirebilir; GM yalnızca yerel yanıtı verip act kapanışını kaçırabilir. Küçük aktif bağlamda Compass kimliği/sahip referansı ve ilgili kapanış tetikleyicileri bulunmalı. Her tur bütün `threads.md` dosyasını yüklemek gerekmez. **Doğrulama:** gerçek yeni bağlamdan sonra tek bir oyuncu cümlesi act'i kapatsın; normal bir sohbet ise yanlışlıkla kapanış sayılmasın.

**3. P1 — Soğuk hafızanın bulunabilirliği fazla örtük.**
Tür: tasarım riski.

[workflows/gm/WORKFLOW.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/WORKFLOW.md:32>) ilgili soğuk notları tetiklenince okumayı söylüyor. [campaign/session_brief.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/session_brief.md:19>) bunun için bir lookup listesi sunuyor; [workflows/reference/authority-map.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/reference/authority-map.md:339>) brief'i isteğe bağlı ve revision'a bağlı hazırlık olarak tanımlıyor. Hangi eski söz, borç, kişi veya bilginin bu sahneyi etkilediğini keşfetmek hâlâ büyük ölçüde modelin hatırlamasına bağlı.

Öneri: mevcut brief/index üzerinde küçük, kaynaklı bağlantılar: kişi/yer/konu sinyali → asıl kayıt → neden şimdi ilgili → son doğrulanmış kaynak. Bu bir gerçek kopyası değil, erişim dizini olmalı. Sahneye dönüşte ve act hazırlığında yenilenmeli; kaynak değiştiğinde ilgili bağlantı geçersiz sayılmalı. **Doğrulama:** başka adla anılan bir NPC'ye dönüş, eski borcun dolaylı anılması ve uzun aradan sonra mekâna geliş. Gerekli eski gerçek bulunmalı, ilgisiz arşiv yüklenmemeli.

**4. P1 — Bilgi sahibi bazında “nereden ve ne zaman öğrendi?” kaydı zayıf.**
Tür: kontrat kapsamı ve tasarım riski.

[campaign/knowledge_boundaries.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/knowledge_boundaries.md:77>) oyuncu bilgisi için kaynak/son doğrulama içeriyor. [campaign/knowledge_boundaries.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/knowledge_boundaries.md:134>) NPC'ler için bilinen, şüphelenilen ve bilinmeyen fact kimlikleri ile doğrulama yöntemi var. Eksik olan, önemli bir *aktör–bilgi* bağlantısının öğrenme kanalı, zamanı ve düzeltme geçmişinin ortak biçimde taşınması.

Bir NPC haberi mektupla öğrenirken diğerinin yalnız söylenti duyması aynı “biliniyor” sonucuna indirgenmemeli. Önemli bağlantılara kısa kaynak olayı, kurgu zamanı ve confirmed/suspected/refuted gibi mevcut ayrımı tamamlayan durum eklenebilir. Yeni bilgi eski inancı değiştirdiğinde önceki iddianın neden geçersiz kaldığı korunmalı. **Doğrulama:** yanlış söylenti, gecikmiş mektup ve düzeltme; yalnız bilgiyi gerçekten alan kişinin tutumu değişsin. Araç yalnız kimlik/bağlantı biçimini denetlesin; kanıtın anlamını model değerlendirsin.

**5. P1 — Sıkıştırma kuralı, gelecekte davranışı belirleyecek ayrıntıları yeterince ayırmıyor.**
Tür: tasarım riski.

[workflows/distill/WORKFLOW.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/distill/WORKFLOW.md:411>) geçmişi silmemeyi, uzun notları güncel gerçek/önemli geçmiş/baskı/sonraki hamleye indirmeyi doğru biçimde istiyor. [campaign/relationship_map.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/relationship_map.md:7>) güncel ilişkiyi geçmişten ayırıyor. Fakat “önemli geçmiş” için korunması gereken ayrıntılar açık değil.

“Araları düzeldi” özeti, özrün hangi konu için kabul edildiğini ve hangi kırgınlığın sürdüğünü kaybettirebilir. Sıkıştırmada davranışı değiştiren neden, koşullu sözün koşulu, kapsam/sınır, güvenilirlik ve yeniden gündeme gelme tetikleyicisi korunmalı; tarihçe referansı kalmalı. Bunlar her not için yeni bir form değil, ilgili kaydı silmeden önce uygulanacak kısa koruma ölçütleri olmalı. **Doğrulama:** üç sıkıştırma ve iki gerçek bağlam değişimi sonrasında kısmen onarılmış ilişkinin kapsamı değişmemeli.

**6. P2 — Soft turda kesintiden sonra ne kadar diyalog ayrıntısının korunacağı açık bir kalite tercihi olmalı.**
Tür: mevcut tasarımın sınırı.

[workflows/gm/playbooks/persistence.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/persistence.md:13>) önemli yeni gerçeği zaten durable sayıyor; bu eksik değil. Ancak [workflows/gm/playbooks/persistence.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/persistence.md:64>) soft ordinary turlarda hiçbir kayıt yapmıyor ve yaklaşık beş soft turda checkpoint öneriyor. [workflows/gm/playbooks/scene_entry_opening.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_entry_opening.md:48>) devamı son anchor'a bağlıyor.

Beklenmedik kapanma ilk birkaç soft turda olursa, yeni kalıcı gerçek oluşmamış olsa bile son soru, konuşma ritmi veya yarım jest kaybolabilir. Durable ölçütünü şişirmek yerine, yarım kalan cevap gibi devamı gerçekten etkileyen anlarda küçük bir resumability checkpoint'i kullanmak değerlendirilmeli. Her tur transcript saklama önerilmiyor. **Doğrulama:** birinci ve dördüncü soft turdan sonra zorunlu kesinti; tekrar sorulan soru, atlanan cevap ve son konuşmacı kaybı ayrı ölçülsün. Ek yazma maliyeti de raporlansın.

**7. P2 — Karakterin kendi sahne dışı hareketi ile dünya domain'i arasındaki sahiplik daha açık olmalı.**
Tür: talimat belirsizliği.

[workflows/reference/authority-map.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/reference/authority-map.md:277>) karakter notunun kendi offscreen trajectory'sini sahiplenmesine izin veriyor; [workflows/reference/authority-map.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/reference/authority-map.md:361>) entity notlarında offscreen trajectory kopyalamamayı söylüyor. [campaign/characters/_template.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/characters/_template.md:41>) ve [tools/check_state.py](<D:/Repog/Codex RePoG/public/RePoG/tools/check_state.py:3288>) aktif karakter trajectory'sini notta bekliyor. Bu doğrudan çalıştırılmış hata değil; “kendi kaydı” ile “domain kopyası” ayrımı örtük.

NPC'nin kişisel işi kendi notunda; birden çok aktörü etkileyen ortak süreç dünya domain'inde kalmalı. Bir hareket domain'e taşınırsa eski alan güncel paralel kopya yerine referans olmalı. **Doğrulama:** sahneden çıkan NPC'nin bir hafta sonraki dönüşü; aynı hareketin iki ayrı değerlendirmeyle iki defa ilerlememesi.

**8. P2 — NPC sesi, bağlama göre değişen ifade biçimleriyle güçlendirilmeli.**
Tür: tasarım geliştirmesi.

[campaign/characters/_template.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/characters/_template.md:15>) karar eksenlerini; [campaign/characters/_template.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/characters/_template.md:166>) kelime seçimi, kaçınılan ses ve sade konuşma örneğini zaten sunuyor. [workflows/gm/playbooks/dialogue_social.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/dialogue_social.md:66>) farklılıkları koruyor. Temel genişletme, daha çok sıfat yerine aynı kişiliğin farklı ilişkiler ve baskılar altında nasıl duyulduğunu göstermektir.

Önemli bir NPC için mevcut notta birkaç kısa örnek yeterli: olağan konuşma, baskı altında ret, güvendiği biriyle konuşma. Örnekler ezberlenecek replikler veya zorunlu jestler olmamalı. Aynı kişi daha sıcak veya kırılgan konuşabilir; karar ilkesi sebepsizce değişmemeli. **Doğrulama:** isimler gizlenerek aynı soruya farklı NPC yanıtlarının ayırt edilebilirliği; aynı NPC'nin farklı sahnelerde hâlâ tanınması.

**9. P2 — Karakter gelişimi ile kişilik kayması ayrılmalı.**
Tür: tasarım geliştirmesi.

Agency Card temel kişiliği, aktif kadro anlık amacı, ilişki haritası mevcut ilişkiyi ayırıyor. [workflows/distill/WORKFLOW.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/distill/WORKFLOW.md:490>) ise genel sesleri düzeltmek ve daha doğal duruşlar eklemek için faydalı bir inceleme veriyor. Eksik olan, karakterde kalıcı değişimin hangi olayla kazanıldığının açık karar ölçütü.

Bir ihanet NPC'yi herkese karşı bambaşka biri yapmamalı. Geçici gerilim, belirli kişiye karşı ilişki değişimi ve kalıcı değer değişimi ayrılmalı. Kalıcı dönüşüm ilgili olayın kaynağına bağlanmalı; değişmeyen temel özellikler korunmalı. Companion tarafındaki [campaign/companion_state.json](<D:/Repog/Codex RePoG/public/RePoG/campaign/companion_state.json:28>) nedenli mevcut durum ayrımı örnek alınabilir; RPG'ye tüm Companion yaşam döngüsü taşınmamalı. **Doğrulama:** korku, yakınlık ve kayıp sahnelerinden sonra aynı karakterin değişimi gerekçeli ve sınırlı kalsın.

**10. P2 — İlişki hafızası tek bir genel güven etiketine sıkışmamalı.**
Tür: tasarım geliştirmesi.

[campaign/relationship_map.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/relationship_map.md:16>) trust/debt/tension için ortak bir hücre ve yönlü ilişki sunuyor. Bu hafif yapı korunabilir; ancak bir olayın ilişkinin hangi konusunu değiştirdiği ve neyi değiştirmediği kaybolmamalı.

“İş becerine güveniyor, para konusunda güvenmiyor; özrünü kabul etti ama anahtarı geri vermedi” gibi bağlama özgü kısa kayıtlar, genel “güven arttı”dan daha oynanabilir. Açık gerilime neden ve giderilme koşulu eklemek yeterli olabilir. [workflows/companion/playbooks/conflict_repair.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/companion/playbooks/conflict_repair.md:13>) bu ayrımı Companion için zaten iyi ifade ediyor. **Doğrulama:** tek özür bütün sorunları sıfırlamasın; oyuncunun yaptığı onarım da sonraki sahnede unutulmasın. NPC duygusu ile oyuncunun ifade etmediği duygular karıştırılmasın.

**11. P1 — Kampanya ufku ile her yeni act arasındaki bağlantı kurulmalı.**
Tür: tasarım riski.

[workflows/worldbuild/deep_v8/08_reciprocity_campaign_horizon.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/deep_v8/08_reciprocity_campaign_horizon.md:19>) ve [workflows/worldbuild/playbooks/rpg_standard_deep.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_deep.md:752>) çok-act'li sorular ve olası sonlar hazırlıyor. Sorun büyük kurgu fikrinin yokluğu değil; [campaign/next_act_prep.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/next_act_prep.md:96>) içinde onu son oyuncu seçimleriyle yeniden ilişkilendiren açık bir adım bulunmaması.

Act sınırında üç kısa cevap yeterli: bu act hangi uzun soruya dokunabilir; oyuncunun seçimleri o soruyu nasıl değiştirdi; bu act'in bağımsız kalacak tarafı ne? Mevcut `threads.md` içinde kampanya ölçeğindeki sorularla act sorusu ayrılabilir. Yakın gelecek somut, uzak gelecek ihtimalli kalmalı. **Doğrulama:** üç act boyunca başlangıç vaadi bilinçli biçimde sürsün, dönüşsün veya kullanıcı kararıyla bırakılsın; sebepsiz silinmesin. Sandbox oyuna zorunlu ana olay örgüsü eklenmesin.

**12. P2 — Kurulan beklentilerin karşılık bulması için yaşam döngüsü eksik.**
Tür: tasarım geliştirmesi.

[campaign/threads.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/threads.md:47>) “Setups awaiting payoff” alanına sahip. [workflows/worldbuild/playbooks/rpg_standard_deep.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/worldbuild/playbooks/rpg_standard_deep.md:772>) karşılığı takvime bağlamamayı doğru söylüyor. Ancak hazırlanmış GM ihtimali, oyuncuya gerçekten gösterilmiş ayrıntı ve sonuçlanmış beklenti aynı biçimde izlenmiyor.

Yalnız önemli birkaç unsur için kaynak/ilk görünüş, ilgili açık soru ve durum tutulmalı: gösterildi, karşılık bulabilir, karşılık buldu, dönüştü, bırakıldı. Gösterilmemiş GM hazırlığı oyuncunun hatırlaması gereken bir ipucu sayılamaz. “Bırakıldı” geçerli sonuç olmalı; her ayrıntı açıklanmak zorunda değil. **Doğrulama:** ilk act'teki küçük söz ikinci act'te farklı ama nedensel karşılık bulsun; rafa kalkmış bir hazırlık sonradan yaşanmış gibi anlatılmasın.

**13. P1 — Yönlendirme, takılma ile bilinçli yön değiştirmeyi ayırmalı.**
Tür: talimatlar arası öncelik boşluğu.

[workflows/gm/playbooks/scene_arc_transition.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_arc_transition.md:31>) uzun süredir ilerlemeyen act'i mevcut baskılarla soruya doğru itmeyi öneriyor. [workflows/gm/playbooks/breather_aftermath.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/breather_aftermath.md:47>) ve [workflows/gm/playbooks/scene_entry_opening.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_entry_opening.md:42>) bilinçli dinlenme ve reddi koruyor.

Önce sebep ayrılmalı: bilgi anlaşılmadı mı, yöntem tükendi mi, oyuncu reddetti mi, başka hedef mi seçti, sakin zaman mı istiyor? Bilgi eksikliğinde bilinen kanıtı anlaşılır kıl; yöntem tükendiyse nedensel alternatif sun; bilinçli ret veya dinlenmede eski plana geri çekme. Oyuncu ilgisi açık söz/davranış kanıtıyla tutulmalı; tek turdan kalıcı zevk veya duygu çıkarılmamalı. **Doğrulama:** aynı kurgu “yardım isteyen takılmış oyuncu” ve “bilerek reddeden oyuncu” dallarında farklı ele alınmalı.

**14. P2 — Esnek ipucu erişimi, sabit kanıtın geçmişini değiştirmemeli.**
Tür: tasarım riski.

[workflows/gm/playbooks/exploration_investigation.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/exploration_investigation.md:36>) tek taşıyıcıya bağımlılığı kırıyor. Bu güçlü bir ilke; fakat henüz kullanılmamış erişim yolu ile yeri/geçmişi kurulmuş delilin taşınması açıkça ayrılabilir.

Muhbir kaçınca başka tanık bulunması makul olabilir; daha önce kasada olduğu belirlenmiş mektubun oyuncu nereye giderse orada belirmesi farklıdır. Esneklik, yeni ve nedensel olarak mümkün erişim yolunda olmalı; sabitlenmiş gerçeğin üzerine yazmamalı. **Doğrulama:** oyuncu planlanmış yolu atladığında rastgele yerin zorla doğru ipucuna dönüşmemesi; makul başka yöntemle ilerleyebilmesi.

**15. P1 — Sakin ilk açılış konusunda açık talimat uyuşmazlığı var.**
Tür: doğrulanmış kontrat uyuşmazlığı.

[workflows/gm/playbooks/scene_entry_opening.md](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/scene_entry_opening.md:37>) ilk açılışta bir etkin baskı göster diyor. [campaign/opening_brief.md](<D:/Repog/Codex RePoG/public/RePoG/campaign/opening_brief.md:158>) breather açılışta baskının boş kalmasını geçerli sayıyor. Üst GM kuralları sakinliği korusa da alt adım gereksiz baskı üretmeye yöneltebilir.

Tek koşullu ifade yeterli: varsa mevcut görünür baskıyı, yoksa sıradan oynanabilir imkânı göster. **Doğrulama:** onaylanmış sakin başlangıç ve beş sakin tur; görev, tehdit veya şüphe icat edilmeden yaşayan bir çevre ve oyuncunun seçebileceği eylemler.

**16. P2 — Kurala uyma açıklaması bazen karakterin ağzından duyuluyor.**
Tür: sınırlı pilot gözlemi.

[semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/07.json](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/07.json:4>) işe katılmanın zorunlu olmadığını tekrar açıklıyor. [semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/29.json](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/29.json:4>) katkının kapsamını ayrıntılı biçimde sayıyor. Tek başına ikisi de uygun olabilir; özellikle oyuncu bunu sorduğunda. Risk, her NPC'nin aynı izin/onay/açıklama diliyle konuşması. Önceki [semantic-review/runs/2026-09-16-candidate-pilot/rpg_evaluation.md](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/rpg_evaluation.md:5>) de tekrar güvenceyi sınırlı bir kalite notu olarak kaydediyor.

İlk açıklamadan sonra özgürlük, NPC'nin kendi işine dönmesi veya ret üzerinde durmamasıyla gösterilebilir. Kaydın doğruluğu arka planda korunurken replik karakterin o andaki amacına hizmet etmeli. **Doğrulama:** aynı sahnenin iki sürümünü kör karşılaştır; açıklık korunurken doğallık, alt metin ve karaktere özgülük gelişiyor mu? Oyuncunun açık güvence talebini susturma.

**17. P2 — Tekrar uyarıları ile edebî kalite birbirinden ayrı ölçülmeli.**
Tür: mevcut aracın kapsam sınırı.

[tools/check_style.py](<D:/Repog/Codex RePoG/public/RePoG/tools/check_style.py:181>) benzer uzunlukları; [tools/check_style.py](<D:/Repog/Codex RePoG/public/RePoG/tools/check_style.py:225>) modelin verdiği kategorileri sayıyor. [campaign/style_state.json](<D:/Repog/Codex RePoG/public/RePoG/campaign/style_state.json:3>) sekiz örneklik sınırlı hafıza tutuyor. Bu araç anlamsal tekdüzeliği, yüzeysel alt metni veya earned motif tekrarını yargılamıyor ve zaten bunu iddia etmiyor.

Diyalog ile anlatıcı bölümlerinin gerektiğinde ayrı örneklenmesi, uzun aradan dönen NPC'nin kalıcı ses örneklerinin yeniden okunması ve monoton işlevin dönemsel insan/model incelemesi daha yararlı. Uyarıdan kaçınmak için sırf çeşitlilik olsun diye metafor, tehdit veya uzun paragraf eklenmemeli. **Doğrulama:** aynı kelimeleri kullanmadan aynı dramatik işi tekrarlayan metin ile anlamı gelişen kasıtlı motif ayrı değerlendirilsin.

**18. P1 — Mevcut kalite kanıtı bu hedefi değerlendirmek için dar.**
Tür: ölçüm açığı.

[tools/gm_replay_suite.json](<D:/Repog/Codex RePoG/public/RePoG/tools/gm_replay_suite.json:26>) dokuz boyutta niyet, nedensellik, oyuncu yazarlığı, NPC iradesi, varlık, ses ayrımı, bilgi sınırı, tempo ve devamı ölçüyor. Bunlar gerekli; ancak çok-act'li bütünlük, kazanılmış karakter dönüşümü, setup/payoff, alt metin ve okuma isteği ayrı ölçülmüyor.

Önceki pilot dokuz boyutta tam puan almış olsa da [semantic-review/runs/2026-09-16-candidate-pilot/rpg_evaluation.md](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/rpg_evaluation.md:7>) gerçek runtime, Distill ve yeni bağlamdan devamı doğrulamadığını açıkça söylüyor. Bu puan edebî kalite tavanı olarak okunmamalı. [evaluation/README.md](<D:/Repog/Codex RePoG/public/RePoG/evaluation/README.md:24>) doğru test protokolünü zaten tarif ediyor; şimdi bunun gerçek uygulanmış kanıtı lazım.

Aynı başlangıçtan eski/yeni sürüm çiftleri, gerçek sahip dosyalarından başlayan yeni aktör, ardışık act'ler ve tercihler yüzünden ayrılan kollar kullanılmalı. Mevcut pilot girdileri sınırları sık sık açıkça hatırlatıyor; aynı niyetlerin doğal ve kısa oyuncu ifadeleriyle de sınanması gerekir. Sonuçlar tek toplam puana indirgenmemeli: kritik çelişkiler, hafıza kaybı, karakter tanınabilirliği, makro bütünlük, dramatik karşılık ve insan tercihi ayrı raporlanmalı.

**19. P2 — Her konuşma turunda yeni sosyal değişim beklemek fazla güçlü bir kural.**
Tür: talimat kapsamı.

[Diyalog playbook'u](<D:/Repog/Codex RePoG/public/RePoG/workflows/gm/playbooks/dialogue_social.md:94>) cevap sonrasında bir sosyal gerçeği veya imkânı değiştirmeyi istiyor. Bunu genel soft-turn ve sıradan sohbet izinleriyle birlikte okuduğumuzda, her selamın yeni güven, her sessizliğin yeni sır doğurması amaçlanmıyor; fakat cümle koşulsuz.

Değişim yalnız nedensel olarak doğuyorsa gösterilmeli. Aynı tavrın sürmesi, kısa konuşmanın bitmesi veya birlikte sessizce çalışma da geçerli bir sonuç olmalı. **Doğrulama:** sıradan selam, yinelenen istek ve sessiz ortak iş; sebepsiz yeni borç, yakınlık veya bilgi üretilmemesi. Bu, NPC'lerin kendi amaçlarıyla inisiyatif almasını engellememeli.

**20. P2 — Somutluk yalnız doğru nesne adı vermenin ötesinde değerlendirilmeli.**
Tür: sınırlı pilot gözlemi ve kalite geliştirmesi.

Pilotun [26. turu](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/26.json:4>) parçaların birleştiği yerdeki boşluğu, [27. turu](<D:/Repog/Codex RePoG/public/RePoG/semantic-review/runs/2026-09-16-candidate-pilot/sustained_rpg/responses/27.json:4>) uygun el aletini ve parçaların yerine oturmasını anlatıyor. Mekân ve temiz başarı korunuyor; ifadeler farklı birçok nesneye taşınabilecek kadar genel kalıyor. Bu, bütün oyunun böyle yazıldığı anlamına gelmez.

Oyuncu özellikle bakıyor veya yapıyorsa, kurguya uygun tek bir ayırt edici malzeme, hareket, mekânsal ilişki veya ses ayrıntısı sonraki eylemi besleyebilir. Her tura duyusal ayrıntı kotası eklenmemeli, bilinmeyen teknik gerçek uydurulmamalı. **Değerlendirme:** okuyucu neyin değiştiğini canlandırabiliyor mu; ayrıntı bir sonraki kararını etkileyebiliyor mu; nesnenin adı değişince metin bütünüyle aynı mı kalıyor?

**Bu incelemede gerçekten çalıştırılan dar kontroller**

Python `-B` ile `tools/check_style.py` içeri aktarıldı; hiçbir ürün state dosyasına kayıt yapılmadı. 36 eski yanıt sırayla, tamamı varsayılan `speaker_type="narrator"`, kategori/sahne/speaker kimliği verilmeden ve bellekte son sekiz fingerprint tutularak değerlendirildi. Bu, pilotun gerçek örnekleme politikasının tekrarı değil, aynı malzemeye uygulanan tanısal taramadır.

| Kontrol | Gözlem | Yorum sınırı |
| --- | --- | --- |
| Önceki pilotun 36 yanıtı | Whitespace ile kelime medyanı 39; 35 yanıt 2–3 paragraf | Kısa yazmak veya benzer paragraf sayısı tek başına kusur değil |
| Aynı yanıtların stil taraması | 15 `length_monotony` bilgi bulgusu; diğer türler yok | Ritme dair sinyal; kötü edebiyat hükmü değil |
| Aynı cümle dört ayrı NPC kimliğinde | Dördünde de sıfır bulgu | Araç farklı konuşmacıları karşılaştırmıyor |
| Aynı NPC'nin aynı cümlesi dördüncü kez | Üç bulgu: uzunluk, cümle başlangıcı, ifade kalıbı | Aynı konuşmacının yakın tekrarını görüyor |
| Araya sekiz anlatıcı kaydı konduktan sonra aynı NPC/cümle | Sıfır bulgu | Global son-sekiz penceresinin geçmişi düşürmesi |

Tarama çekirdeği: `findings, fp = check_style(state, text)`; her çağrıdan sonra `state["history"] = (state["history"] + [fp])[-8:]`. Başlangıçta history, categorical_history ve avoid_phrases boştu. NPC probunda aynı `I check the ledger before I sign any delivery.` cümlesi ve önce farklı, sonra aynı `speaker_id` kullanıldı. Ara anlatıcı örnekleri `The afternoon light reaches table {i}.` biçimindeydi. Pilot uzunluk bulguları: 4, 5, 7, 9, 14, 15, 17, 20, 21, 23, 24, 25, 26, 35, 36. Bunlar 17 ve 18 numaralı bulguların sınırlı tanısal kanıtıdır.

**Önerilen uygulama sırası**

| Dilim | İş | Tamamlanma kanıtı |
| --- | --- | --- |
| 1 — Süreklilik bağlantıları | Yeni act pusulası/kimliği, kapanış tetikleyicilerinin bağlama girişi, sakin açılış uyuşmazlığı, offscreen sahipliğinin açıklığı | İki act geçişi; sakin açılış; eski act'in yeniden kapanmaması |
| 2 — Hatırlama ve karakter | Kaynaklı lookup bağlantıları, bilgi sahibi bazında provenance, sıkıştırmada nedensel ayrıntı, bağlama göre ses ve ilişki kapsamı | Gerçek yeni bağlam, gecikmiş haber, kısmi barışma, uzun aradan dönen NPC |
| 3 — Büyük kurgu | Kampanya sorusu–act bağlantısı, gösterilmiş beklentilerin takibi, takılma/ret ayrımı, nedensel yeniden planlama | Üç act; reddedilmiş hedef; dönüşen tema; ertelenmiş karşılık |
| 4 — Anlatım ve kanıt | Örnekli pozitif anlatım ölçütleri; kural açıklama tonunun azaltılması; kör karşılaştırma ve uzun oyun değerlendirmesi | İnsan tercihi ve somut metin kanıtı; kritik gerileme olmaması |

1. dilim küçük düzeltmelerle başlayabilir. Diğer dilimlerde her yeni kayıt alanı, gerçek bir testte kaybolan bilgiye veya gözlenen davranış sorununa karşılık gelmeli. Hepsini birden zorunlu dosya ve tur kontrolüne çevirmek, hafif çalışma felsefesini zedeler.

**Hedef değerlendirme seti — henüz çalıştırılmadı**

| Senaryo | Beklenen kalite |
| --- | --- |
| İki ayrı act; başarı ve ret ile kapanış | Doğru soru/koşul kimliği; sonuçların karışmaması |
| Bir ve dört soft turdan sonra kesinti | Açık kabul edilen devam sınırının ölçülmesi |
| Üç sıkıştırma, iki gerçek yeni bağlam | Sözün koşulu ve ilişkinin nedeni korunması |
| Yanlış söylenti → kısmi tanıklık → gecikmiş düzeltme | NPC başına doğru bilgi/inanç zamanı |
| Aynı NPC: resmî görüşme, dostla sohbet, baskı altında ret | Tanınabilir ses, bağlama duyarlı ifade |
| İhanet → sınırlı özür → birlikte çalışma | Konuya özgü onarım; toptan reset olmaması |
| Reddedilen ana teklif, seçilmiş bağımsız hedef | Dünya ilerlerken oyuncunun yeni yolunun desteklenmesi |
| Üç act sonra eski söz/nesne geri dönüyor | Kazanılmış karşılık; gösterilmeyen hazırlığın uydurulmaması |
| Planlanan muhbir atlanıyor | Sabit kanıtı taşımadan alternatif araştırma |
| Sakin açılış ve uzun breather | Gerilimsiz ama kendine özgü, yaşayan sahne |
| Aynı içerikten iki anlatım sürümü | Doğallık, açıklık, alt metin, sahne mekânının anlaşılması |
| Kasıtlı motif ile mekanik tekrar karşılaştırması | Anlamlı tekrarın yanlışlıkla cezalandırılmaması |

İlk sınama için üç kısa act ve birkaç gerçek yeni bağlam noktası yeterli bir başlangıç olabilir; örneğin toplam 60–90 tur bir tasarım önerisidir, başarı garantisi veya mevcut ölçüm değildir. Dallanma testleri tek hikâyenin doğrusal devamından ayrı yürütülmeli. Model/sürüm/ayar, kaynak commit, yüklenen dosyalar, gerçek kayıt sonuçları ve gecikme kaydedilmeli. Önceki konuşmayı koruyan ajan “yeni bağlam” sayılmamalı.

**Somut dönüşüm örneği — ürün davranışı değil, önerilen tasarım**

Kampanya sorusu: “Bu şehirde güven, çıkar ilişkilerinden daha güçlü bir bağ olabilir mi?” İlk act sorusu: “Mahallenin atölyesi kendi şartlarıyla ayakta kalacak mı?” Oyuncu planlanmış siyasi teklifi reddedip ustayla çalışmayı seçiyor.

İyi devam, aynı teklifi başka bir NPC'ye yeniden söyletmez. Usta kendi işi ve yükümlülükleriyle hareket eder. Eski borç veya verilmiş söz, yalnız gerçek tetikleyicisi geldiğinde atölyenin seçeneklerini etkiler. Oyuncu yeni bir çözüm bulursa ilk act onun üzerinden kapanabilir. İkinci act, sonucun doğurduğu yeni soruyu kurar; başlangıçtaki güven teması uygun olduğu kadar taşınır. Oyuncu bu konuyu da bırakırsa eski soru zorla geri çağrılmaz. Bilinen dünya sonuçları korunur; henüz gerçekleşmemiş hazırlık yeniden tasarlanabilir.

**Araştırmadan alınabilecek, sınırları belli dersler**

- Uzun bağlamın varlığı, içindeki her bilginin eşit biçimde kullanılacağını göstermiyor. Bu, kısa ve ilgili kaynak bağlantılarını sınamak için gerekçe; RePoG'un kullandığı güncel modelin hata oranı hakkında ölçüm değil. [Lost in the Middle — TACL 2024](https://aclanthology.org/2024.tacl-1.9/)
- Uzun süreli hafıza değerlendirmesinde bilgi çıkarma, oturumlar arası akıl yürütme, zaman, bilgi güncelleme ve bilmediğini belirtme ayrı yetenekler. RePoG testlerinde yalnız “adı hatırlıyor mu?” sorusunu aşmak için yararlı. [LongMemEval — ICLR 2025](https://arxiv.org/abs/2410.10813)
- Gözlem, ilgili anıyı geri çağırma ve deneyimden daha üst düzey çıkarım yapma, çalışmanın kendi simülasyonunda inanılırlığa katkıda bulundu. RePoG'a uyarlanabilecek çıkarım: karakter değişimini olay kaynağına bağlamak. Tüm konuşmayı saklayan arka plan ajan simülasyonunu kopyalamak gerekmiyor. [Generative Agents](https://arxiv.org/abs/2304.03442)
- Katmanlı planlama ve mevcut hikâye durumunu yeniden kullanma, araştırmalardaki uzun öykülerde bütünlüğü iyileştirdi. RePoG için çıkarım, kampanya sorusu–act–sahne ilişkisidir; oyuncunun gelecekteki kararlarını sabitlemek değildir. [Re3](https://aclanthology.org/2022.emnlp-main.296/), [DOC](https://aclanthology.org/2023.acl-long.190/)
- Dinamik plan ile zamanlı hafızayı birleştiren çalışmalar da var. Bu, gerçekleşmemiş hazırlığın gelişmelere göre güncellenmesini araştırmaya değer kılıyor; RePoG'a grafik veritabanı veya otomatik anlatı hakemi eklenmesi gerektiğini kanıtlamıyor. [DOME — NAACL 2025](https://aclanthology.org/2025.naacl-long.63/)

Bu çalışmalar farklı görevler, modeller ve değerlendirmeler kullanıyor. Buradaki uygulama önerileri kaynaklardan yapılan tasarım çıkarımlarıdır; RePoG üzerinde doğrulanmış kalite artışı olarak sunulmuyor.
