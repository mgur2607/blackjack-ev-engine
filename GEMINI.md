# Blackjack EV Karar Motoru (HIT/STAND/SPLIT) — PRD v1.2

**Sahip:** Mustafa Gür (Ürün Sahibi) — teknik destek: ChatGPT
**Dil/Stack:** Python 3.11+, PyQt5 (UI), saf Python (EV çekirdeği)
**Tarih:** 06 Eylül 2025 (TRT / Europe/Istanbul)

---

## 0) TL;DR

* Amaç (V1): Kalan kart kompozisyonunu (without replacement) kullanarak tam dallanmalı beklenen değer (EV) hesabıyla HIT / STAND / SPLIT kararını veren olasılık tabanlı karar motoru ve bunu gerçek oyun akışında gösterecek PyQt5 arayüzü geliştirmek.
* Kapsam (V1): Double yok, Split var (ilk iki kart aynı değerdeyse). Insurance, Surrender, Peek yok. 10/J/Q/K tek sınıf “10” olarak modellenir.
* Kart Girişi: Oyuncuların ve krupiyenin tüm kartlarını kullanıcı manuel girer.
* Eli Sonlandır: Geçerli eli kapatır (skorlar), ayakkabı (shoe) aynı kalır, kalan kartlarla bir sonraki ele geçilir (yeni elde kartlar yine manuel girilir).
* Oyunu Sonlandır: Yeni oyuna başlanır; deste sayısı bu aşamada seçilir ve yeni shoe oluşturulur.
* Çoklu Oyuncu: Oturak ekle/sil; her oyuncu bağımsız akışta yönetilir. Kartlar UI’da görselleri veya etiketleriyle görünür.
* Loglama (V1): CSV/JSON çıktı yok; print() ile konsola debug/log akışı yazdırılır.

---

## 1) Hedefler ve Başarı Kriterleri

### 1.1 Hedefler

* H1 — Doğru EV: Kalan kart kompozisyonuyla tam dallanmalı {H, S, SP} için EV hesaplanır, önerilen aksiyon deterministik biçimde üretilir.
* H2 — Gerçek Zamanlı: Her kart girişiyle shoe düşer, EV’ler anında yenilenir.
* H3 — Çoklu Oyuncu: En az 6 oyuncu desteklenir; ekle/sil dinamik.
* H4 — İzlenebilirlik: Tüm eylemler print() ile net ve okunur biçimde loglanır.
* H5 — Performans: Tek spot hesaplama sıcak cache ile < 20 ms, soğuk < 150 ms hedeflenir.

### 1.2 Kabul Kriterleri

* A1: Krupiye sonuç dağılımlarının (17/18/19/20/21/bust) olasılık toplamı ≈ 1.0 (±1e−9).
* A2: Bilinen temel spotlarda (tam ayakkabı): 16v10 için EV(H) ≥ EV(S), 20v10 için EV(S) ≥ EV(H) tutarlı çıkar.
* A3: Aynı state → aynı EV & öneri (deterministik).
* A4: UI: Kart girildiğinde shoe & EV & öneri otomatik güncellenir; oyuncu panelinde net görünür.
* A5: Split kullanılabilirliği (ilk iki kart aynı değer) doğru tespit edilir; EV(SP) görüntülenir.

---

## 2) Kapsam, Kurallar ve Varsayımlar (V1)

### 2.1 Masa Kuralları (parametrik; varsayılanlar)

* Deste/ayakkabı: Varsayılan 8 deste; başlangıçta karışık.
* Krupiye: S17 (soft 17’de durur).
* Ödeme: Blackjack 3:2 (yalnızca dağıtım aşamasındaki ilk iki kart ile 21).
* Aksiyonlar: Hit, Stand, Split. Double yok.
* Kapsam Dışı: Insurance, Surrender, Peek yok.
* Kart sınıflaması: 10/J/Q/K tek sınıf 10. As 1 veya 11 (soft/hard) olarak değerlendirilir.
* Kart çekimi: Without replacement (kalan sayımlardan olasılık).

### 2.2 Split Kuralları (net)

* Uygunluk: İlk iki kart aynı değer (ör. (8,8), (10,10), (A,A)). 10-J-Q-K kombinasyonları aynı değer (10) sayılır → split mümkündür.
* Split sayısı: Tek split (yeniden split yok).
* A’lar özel kural: A split’inde her ele yalnızca 1 kart dağıtılır, hit yapılamaz (stand zorunlu).
* BJ sonrası split: Split sonrası 21 blackjack sayılmaz; 1:1 olarak değerlendirilir.
* Double: Yok (split sonrası da yok).
* Karar kıstası: Öneri seçiminde mutlak beklenen getiri maksimize edilir. Split, ikinci eşit bahsi gerektirir; motor bunu toplam getirisi üzerinden kıyaslar (bkz. 6.3).

### 2.3 Çoklu Oyuncu & Akış

* Her oyuncu sırasıyla oynar; her aksiyon sonrası gerçek çekilen kart UI’dan girilir → shoe güncellenir.
* Krupiye kartları (upcard, downcard, ve gerektiğinde çekilen tüm kartlar) kullanıcı tarafından girilir.
* Eli Sonlandır: Tüm oyuncular tamamlandıktan sonra, krupiye kartları kuralı sağlayacak (S17) şekilde kullanıcı tarafından girilir; el sonuçları hesaplanır ve yalnızca print() ile loglanır; shoe korunur; bir sonraki el için bekleme durumuna geçilir.
* Oyunu Sonlandır: Yeni oyuna başlanır; açılır diyalogda deste sayısı seçilir → yeni shoe oluşturulur.

---

## 3) Kullanıcı Senaryoları

* S1 — Canlı Oyun Takibi: Dağıtılan kartlar (oyuncular + krupiye up/down) UI’dan girilir → shoe düşer → motor koltuk için EV(H/S/SP) ve öneriyi gösterir → kullanıcı aksiyonu uygular (Hit/Stand/Split). Hit’te çekilen gerçek kart UI’dan girilir → EV yenilenir. Tüm oyuncular bitince krupiye kartları kullanıcı tarafından tamamlanır; Eli Sonlandır ile sonuçlar kapatılır; aynı shoe ile yeni ele geçilir.
* S2 — Spot Analizi: Belirli upcard ve eldeki toplam/soft ve shoe kompozisyonuyla EV(H/S/SP) ve krupiye dağılımı incelenir.

---

## 4) Sistem Mimarisi

```
PyQt5 UI  <-->  Engine Facade  <-->  EV Core (DP + LRU Cache)
     ^                |                     |
     |                v                     v
 Table/Game Loop   Shoe/Rules Model   Dealer Distribution Cache
```

* EV Core: Rekürsif dinamik programlama; without replacement olasılıklar; @lru\_cache ile hızlandırma.
* Dealer Distribution: Upcard + shoe → {17,18,19,20,21,bust} olasılık vektörü.
* Game Loop: Sıralı oyuncu akışı; manuel krupiye kart girişi; skor kapanışı.
* Facade: UI’nın kullandığı sade API yüzeyi.

---

## 5) Veri Modelleri

### 5.1 Shoe

* Tuple\[int × 10]: (A,2,3,4,5,6,7,8,9,10) sayıları.
* Başlangıç (8 deste): (32,32,32,32,32,32,32,32,32,128).

### 5.2 Hand

* cards: tuple\[int,...] (ör. (7,4))
* Türetilen: total: int, soft: bool (As=11 aktif mi), is\_initial\_two: bool

### 5.3 Player

* hands: list\[Hand]
* active\_hand\_idx: int (sıradaki el)
* has\_split: bool (tek split limiti için)

### 5.4 Table

* players: list\[Player] (≤6)
* dealer\_cards: list\[int] (downcard dahil, UI’da işaretlenir)
* dealer\_upcard: int | None (kolay erişim)
* shoe: tuple\[int,...]
* rules: Rules
* turn\_index: int (aktif oyuncu)
* log\_level: str ("info" | "debug")

---

## 6) EV Matematiği (H/S/SP, Tam Dallanma)

### 6.1 Kart Olasılıkları (without replacement)

Kalan kart sayısı N ve kart sınıfı c’nin kalan adedi #c iken:
p(c) = #c / N

### 6.2 STAND EV’si

Oyuncu durursa krupiye S17 kuralıyla oynar (kullanıcı krupiye kartlarını gerçekten girecek olsa da hesaplamada olasılıksal dağılım kullanılır). Sonuç ödeme: win=+1, push=0, loss=−1 (doğal blackjack yalnızca ilk iki kart).
EV\_Stand = toplam\_{d ∈ {17,18,19,20,21,bust}} Pr(d) × r(player, d)

### 6.3 HIT EV’si

EV\_Hit = toplam\_{c} p(c) ×
-1  (bust ise)
aksi halde max( EV\_Stand(h + c), EV\_Hit(h + c), EV\_Split(h + c) \[\*] )

(\*) EV\_Split yalnızca ilk iki kart seviyesinde ve aynı değer şartı sağlanıyorsa dikkate alınır; aksi halde seçenek kümesinden çıkar. (Hit sonrası oluşan iki kartta da aynı değer şartı sağlanırsa split uygun olur.)

### 6.4 SPLIT EV’si (tek split, A kısıtı)

İlk iki kart (x, x) iken split edersek iki ayrı el doğar: h1=(x, ?), h2=(x, ?). Bu ellere sırayla birer kart gelir (without replacement).

Genel durum (x ≠ A):
EV\_Split = toplam\_{c1} p(c1)  toplam\_{c2} p'(c2 | c1)  \[ EV\_Best(x,c1) + EV\_Best(x,c2) ]
Burada EV\_Best o el için {H,S} arasında maksimumu verir (split sonrası yeniden split yok, double yok). p' birinci kart çekildikten sonra güncellenmiş shoe olasılığıdır.

A split (x = A): Her ele 1 kart dağıtılır ve stand zorunlu:
EV\_Split(A) = toplam\_{c1} p(c1)  toplam\_{c2} p'(c2 | c1)  \[ EV\_Stand(A,c1) + EV\_Stand(A,c2) ]

Not (karşılaştırma temeli): Split ikinci bir eşit bahis gerektirdiği için karşılaştırma mutlak beklenen getiri üzerinden yapılır. Yani EV\_Split iki elin toplam beklenen getirisi olup, EV\_Hit/Stand (tek bahiste) ile doğrudan kıyaslanır.

### 6.5 Krupiye Dağılımı (S17)

dealer\_play\_dist(total, soft, shoe, s17=True) rekürsiftir. total>21 → bust; total≥17 ve soft17 ise S17’de dur, H17’de devam (parametrik). Aksi halde olası tüm kartlar için dallan ve alt dağılımları topla.

---

## 7) State & Cache Tasarımı

### 7.1 Kanonik State Anahtarı

(player\_total, soft(0/1), dealer\_upcard, shoe\_tuple, rules\_key, split\_used(0/1))

* Aksiyon seti: State bağlamına göre {H,S,SP?}.
* 10 sınıfı tek: (10/J/Q/K) birleşimi state alanını küçültür.
* LRU Cache: dealer\_distribution ve ev\_best fonksiyonlarında kullanılır.

### 7.2 Doğruluk Koruması

* Olasılık toplam kontrolü (≈1.0).
* Aynı state için idempotent EV çıktısı.
* “Shoe − çekilen kart” işlemlerinde negatif adet guard.

---

## 8) PyQt5 UI Gereksinimleri (V1)

### 8.1 Ana Bileşenler

* Masa Paneli: En çok 6 koltuk; her koltukta kart görselleri/etiketleri, toplam/soft etiketi, HIT / STAND butonları, SPLIT (uygunsa) butonu, EV kutuları ve öneri rozeti. Split sonrası oyuncu panelinde iki el yan yana gösterilir; aktif el highlight edilir.
* Shoe Paneli: (A..10) kalan adet ve % (progress bar + sayısal).
* Krupiye Paneli: Upcard, downcard ve çekilen tüm kartlar (kullanıcı girişi); ayrıca dealer outcome çubuğu (17..21,bust yüzdeleri).
* Kontroller: “Yeni El için Kart Gir”, “Eli Sonlandır”, “Oyunu Sonlandır (Yeni Shoe)”, “Oyuncu Ekle/Sil”, “Öneriyi Uygula”.
* Log: Sadece print() (UI’da küçük bir console overlay opsiyonel).

### 8.2 Akış

1. Yeni El (aynı shoe): Oyuncu ve krupiye kartları manuel girilir → shoe düşer.
2. Motor EV’leri hesaplar; öneri gösterilir.
3. Aksiyon uygulanır; Hit’te çekilen gerçek kart girilir; Split’te iki el oluşturulur, her birine kartlar yine manuel girilir → EV’ler yenilenir.
4. Tüm oyuncular bitince kullanıcı krupiye kartlarını kuralı sağlayacak şekilde tamamlar → Eli Sonlandır: skorlar kapanır, shoe korunur.
5. Oyunu Sonlandır seçilirse: deste sayısı seçilir, yeni shoe ile tam sıfırdan başlanır.

### 8.3 UX & Performans

* Gecikmede QThread ile arka iş parçacığı.
* Aktif koltuk/aktif el highlight.
* Split uygun olduğunda buton ve rozet açık şekilde görünür.

---

## 9) Engine ↔ UI API (Öneri)

```python
class Rules:
    s17: bool = True
    bj_payout: float = 1.5
    allow_split: bool = True
    allow_double: bool = False
    split_aces_one_card_stand: bool = True
    allow_resplit: bool = False

class Engine:
    def __init__(self, rules: Rules, decks: int = 8): ...

    # Shoe
    def reset_shoe(self, decks: int | None = None) -> None: ...
    def shoe_counts(self) -> dict[int, int]: ...
    def shoe_percents(self) -> dict[int, float]: ...

    # Kart Girişi (Oyuncu & Krupiye)
    def deal_card_to_player(self, seat: int, card: int, hand_idx: int | None = None) -> None: ...
    def deal_card_to_dealer_up(self, card: int) -> None: ...
    def deal_card_to_dealer_down(self, card: int) -> None: ...
    def dealer_draw(self, card: int) -> None: ...  # manuel çekiş

    # Sorgular
    def compute_ev(self, seat: int, hand_idx: int | None = None) -> dict:
        """Return: { 'H': ev_hit, 'S': ev_stand, 'SP': ev_split_or_None, 'best': 'H'|'S'|'SP' }"""

    def can_split(self, seat: int, hand_idx: int | None = None) -> bool: ...

    # Aksiyon Uygulama
    def apply_player_action(self, seat: int, action: str, *, hand_idx: int | None = None, drawn_card: int | None = None) -> None: ...
        # action in {"H", "S", "SP"}

    # El & Oyun Yönetimi
    def end_hand(self) -> dict: ...   # {seat_index: total_win_units} — print() ile loglanır
    def end_game(self, decks: int) -> None: ...  # yeni shoe
    def new_round(self) -> None: ...

    # Log seviye
    def set_log_level(self, level: str) -> None: ...  # "info"|"debug"
```

Not: compute\_ev krupiye kartlarını olasılıksal oynatırken (hesaplamada), kullanıcı gerçek krupiye kartlarını manuel girmeye devam eder; bu ikisi birbirinden bağımsızdır. Skor kapanışı kullanıcının girdiği krupiye eline göre yapılır.

---

## 10) Test Planı (V1)

### 10.1 Birim Testleri

* Toplam/Soft Mantığı: As sayısı, soft→hard dönüşümü, bust kontrolü.
* Dealer Dağılımı (S17): Olasılık toplamı ve örnek state’lerde beklenen paternler.
* Shoe Operasyonları: Kart düşümü/geri alma, negatif sayım guard’ları.
* EV(H/S): Bilinen spotlarda tutarlılık (tam ayakkabı).
* EV(SP): (8,8)v6, (A,A)v5 gibi klasik çiftlerde EV\_SP’nin pozitif davranışı; A split kısıtının uygulanması.

### 10.2 Entegrasyon Testleri

* Çoklu oyuncu akışı: 3–6 koltukta dağıtım→karar→split→dealer→skor; print log akışı.
* Deterministiklik: Aynı state snapshot’larında aynı sonuçlar.

---

## 11) Loglama

* Yalnızca print(): her karar/çekiş/sonuç için: timestamp, seat/hand, upcard, eldeki toplam/soft, EV(H/S/SP), öneri, uygulanan aksiyon, çekilen kart(lar), el sonucu. (CSV/JSON V1’de yok.)

---

## 12) Performans & Optimizasyon

* @lru\_cache: dealer\_distribution ve ev\_best fonksiyonlarında.
* State küçültme: 10 sınıfı birleşimi; shoe\_tuple immutability.
* Erken kesme: Bust durumlarında dalı kapat.
* Hedefler: Sıcak cache tek spot < 20 ms; soğuk < 150 ms (8 deste, upcard biliniyor).

---

## 13) Kenar Durumlar

* Blackjack (oyuncu 2 kart 21): Skorlamada 3:2; split sonrası 21 blackjack sayılmaz.
* A split: Her ele 1 kart, hit yok, stand zorunlu.
* Shoe tükenmesi: N == 0 → kullanıcıya yeni ayakkabı uyarısı.
* UI veri bütünlüğü: Aynı kart iki kez girilemez; undo ile tutarlı geri dönüş (opsiyonel).
* Manual dealer: Eli Sonlandır öncesi dealer toplamı S17 kuralını sağlamıyorsa UI yönlendirici uyarı çıkarır.

---

## 14) Yapılandırma Örneği (config.yaml)

```yaml
decks: 8
rules:
  s17: true
  bj_payout: 1.5
  allow_split: true
  allow_double: false
  split_aces_one_card_stand: true
  allow_resplit: false
ui:
  max_players: 6
  manual_dealer: true
  console_overlay: true  # print akışını UI’da göstermek için opsiyonel
```

---

## 15) Mühendislik Notları

* Kısa İngilizce docstring + Türkçe yorumlar.
* typing/mypy ile tip ipuçları.
* Çekirdek saf Python; UI PyQt5; test pytest.
* Deterministiklik: RNG yalnızca test senaryolarında kullanılabilir (çekirdek hesaplamada yok).

# Blackjack EV Karar Motoru (HIT/STAND/SPLIT) — PRD v1.2

**Sahip:** Mustafa Gür (Ürün Sahibi) — teknik destek: ChatGPT
**Dil/Stack:** Python 3.11+, PyQt5 (UI), saf Python (EV çekirdeği)
**Tarih:** 06 Eylül 2025 (TRT / Europe/Istanbul)

---

## 0) TL;DR

* Amaç (V1): Kalan kart kompozisyonunu (without replacement) kullanarak tam dallanmalı beklenen değer (EV) hesabıyla HIT / STAND / SPLIT kararını veren olasılık tabanlı karar motoru ve bunu gerçek oyun akışında gösterecek PyQt5 arayüzü geliştirmek.
* Kapsam (V1): Double yok, Split var (ilk iki kart aynı değerdeyse). Insurance, Surrender, Peek yok. 10/J/Q/K tek sınıf “10” olarak modellenir.
* Kart Girişi: Oyuncuların ve krupiyenin tüm kartlarını kullanıcı manuel girer.
* Eli Sonlandır: Geçerli eli kapatır (skorlar), ayakkabı (shoe) aynı kalır, kalan kartlarla bir sonraki ele geçilir (yeni elde kartlar yine manuel girilir).
* Oyunu Sonlandır: Yeni oyuna başlanır; deste sayısı bu aşamada seçilir ve yeni shoe oluşturulur.
* Çoklu Oyuncu: Oturak ekle/sil; her oyuncu bağımsız akışta yönetilir. Kartlar UI’da görselleri veya etiketleriyle görünür.
* Loglama (V1): CSV/JSON çıktı yok; print() ile konsola debug/log akışı yazdırılır.

---

## 1) Hedefler ve Başarı Kriterleri

### 1.1 Hedefler

* H1 — Doğru EV: Kalan kart kompozisyonuyla tam dallanmalı {H, S, SP} için EV hesaplanır, önerilen aksiyon deterministik biçimde üretilir.
* H2 — Gerçek Zamanlı: Her kart girişiyle shoe düşer, EV’ler anında yenilenir.
* H3 — Çoklu Oyuncu: En az 6 oyuncu desteklenir; ekle/sil dinamik.
* H4 — İzlenebilirlik: Tüm eylemler print() ile net ve okunur biçimde loglanır.
* H5 — Performans: Tek spot hesaplama sıcak cache ile < 20 ms, soğuk < 150 ms hedeflenir.

### 1.2 Kabul Kriterleri

* A1: Krupiye sonuç dağılımlarının (17/18/19/20/21/bust) olasılık toplamı ≈ 1.0 (±1e−9).
* A2: Bilinen temel spotlarda (tam ayakkabı): 16v10 için EV(H) ≥ EV(S), 20v10 için EV(S) ≥ EV(H) tutarlı çıkar.
* A3: Aynı state → aynı EV & öneri (deterministik).
* A4: UI: Kart girildiğinde shoe & EV & öneri otomatik güncellenir; oyuncu panelinde net görünür.
* A5: Split kullanılabilirliği (ilk iki kart aynı değer) doğru tespit edilir; EV(SP) görüntülenir.

---

## 2) Kapsam, Kurallar ve Varsayımlar (V1)

### 2.1 Masa Kuralları (parametrik; varsayılanlar)

* Deste/ayakkabı: Varsayılan 8 deste; başlangıçta karışık.
* Krupiye: S17 (soft 17’de durur).
* Ödeme: Blackjack 3:2 (yalnızca dağıtım aşamasındaki ilk iki kart ile 21).
* Aksiyonlar: Hit, Stand, Split. Double yok.
* Kapsam Dışı: Insurance, Surrender, Peek yok.
* Kart sınıflaması: 10/J/Q/K tek sınıf 10. As 1 veya 11 (soft/hard) olarak değerlendirilir.
* Kart çekimi: Without replacement (kalan sayımlardan olasılık).

### 2.2 Split Kuralları (net)

* Uygunluk: İlk iki kart aynı değer (ör. (8,8), (10,10), (A,A)). 10-J-Q-K kombinasyonları aynı değer (10) sayılır → split mümkündür.
* Split sayısı: Tek split (yeniden split yok).
* A’lar özel kural: A split’inde her ele yalnızca 1 kart dağıtılır, hit yapılamaz (stand zorunlu).
* BJ sonrası split: Split sonrası 21 blackjack sayılmaz; 1:1 olarak değerlendirilir.
* Double: Yok (split sonrası da yok).
* Karar kıstası: Öneri seçiminde mutlak beklenen getiri maksimize edilir. Split, ikinci eşit bahsi gerektirir; motor bunu toplam getirisi üzerinden kıyaslar (bkz. 6.3).

### 2.3 Çoklu Oyuncu & Akış

* Her oyuncu sırasıyla oynar; her aksiyon sonrası gerçek çekilen kart UI’dan girilir → shoe güncellenir.
* Krupiye kartları (upcard, downcard, ve gerektiğinde çekilen tüm kartlar) kullanıcı tarafından girilir.
* Eli Sonlandır: Tüm oyuncular tamamlandıktan sonra, krupiye kartları kuralı sağlayacak (S17) şekilde kullanıcı tarafından girilir; el sonuçları hesaplanır ve yalnızca print() ile loglanır; shoe korunur; bir sonraki el için bekleme durumuna geçilir.
* Oyunu Sonlandır: Yeni oyuna başlanır; açılır diyalogda deste sayısı seçilir → yeni shoe oluşturulur.

---

## 3) Kullanıcı Senaryoları

* S1 — Canlı Oyun Takibi: Dağıtılan kartlar (oyuncular + krupiye up/down) UI’dan girilir → shoe düşer → motor koltuk için EV(H/S/SP) ve öneriyi gösterir → kullanıcı aksiyonu uygular (Hit/Stand/Split). Hit’te çekilen gerçek kart UI’dan girilir → EV yenilenir. Tüm oyuncular bitince krupiye kartları kullanıcı tarafından tamamlanır; Eli Sonlandır ile sonuçlar kapatılır; aynı shoe ile yeni ele geçilir.
* S2 — Spot Analizi: Belirli upcard ve eldeki toplam/soft ve shoe kompozisyonuyla EV(H/S/SP) ve krupiye dağılımı incelenir.

---

## 4) Sistem Mimarisi

```
PyQt5 UI  <-->  Engine Facade  <-->  EV Core (DP + LRU Cache)
     ^                |                     |
     |                v                     v
 Table/Game Loop   Shoe/Rules Model   Dealer Distribution Cache
```

* EV Core: Rekürsif dinamik programlama; without replacement olasılıklar; @lru\_cache ile hızlandırma.
* Dealer Distribution: Upcard + shoe → {17,18,19,20,21,bust} olasılık vektörü.
* Game Loop: Sıralı oyuncu akışı; manuel krupiye kart girişi; skor kapanışı.
* Facade: UI’nın kullandığı sade API yüzeyi.

---

## 5) Veri Modelleri

### 5.1 Shoe

* Tuple\[int × 10]: (A,2,3,4,5,6,7,8,9,10) sayıları.
* Başlangıç (8 deste): (32,32,32,32,32,32,32,32,32,128).

### 5.2 Hand

* cards: tuple\[int,...] (ör. (7,4))
* Türetilen: total: int, soft: bool (As=11 aktif mi), is\_initial\_two: bool

### 5.3 Player

* hands: list\[Hand]
* active\_hand\_idx: int (sıradaki el)
* has\_split: bool (tek split limiti için)

### 5.4 Table

* players: list\[Player] (≤6)
* dealer\_cards: list\[int] (downcard dahil, UI’da işaretlenir)
* dealer\_upcard: int | None (kolay erişim)
* shoe: tuple\[int,...]
* rules: Rules
* turn\_index: int (aktif oyuncu)
* log\_level: str ("info" | "debug")

---

## 6) EV Matematiği (H/S/SP, Tam Dallanma)

### 6.1 Kart Olasılıkları (without replacement)

Kalan kart sayısı N ve kart sınıfı c’nin kalan adedi #c iken:
p(c) = #c / N

### 6.2 STAND EV’si

Oyuncu durursa krupiye S17 kuralıyla oynar (kullanıcı krupiye kartlarını gerçekten girecek olsa da hesaplamada olasılıksal dağılım kullanılır). Sonuç ödeme: win=+1, push=0, loss=−1 (doğal blackjack yalnızca ilk iki kart).
EV\_Stand = toplam\_{d ∈ {17,18,19,20,21,bust}} Pr(d) × r(player, d)

### 6.3 HIT EV’si

EV\_Hit = toplam\_{c} p(c) ×
-1  (bust ise)
aksi halde max( EV\_Stand(h + c), EV\_Hit(h + c), EV\_Split(h + c) \[\*] )

(\*) EV\_Split yalnızca ilk iki kart seviyesinde ve aynı değer şartı sağlanıyorsa dikkate alınır; aksi halde seçenek kümesinden çıkar. (Hit sonrası oluşan iki kartta da aynı değer şartı sağlanırsa split uygun olur.)

### 6.4 SPLIT EV’si (tek split, A kısıtı)

İlk iki kart (x, x) iken split edersek iki ayrı el doğar: h1=(x, ?), h2=(x, ?). Bu ellere sırayla birer kart gelir (without replacement).

Genel durum (x ≠ A):
EV\_Split = toplam\_{c1} p(c1)  toplam\_{c2} p'(c2 | c1)  \[ EV\_Best(x,c1) + EV\_Best(x,c2) ]
Burada EV\_Best o el için {H,S} arasında maksimumu verir (split sonrası yeniden split yok, double yok). p' birinci kart çekildikten sonra güncellenmiş shoe olasılığıdır.

A split (x = A): Her ele 1 kart dağıtılır ve stand zorunlu:
EV\_Split(A) = toplam\_{c1} p(c1)  toplam\_{c2} p'(c2 | c1)  \[ EV\_Stand(A,c1) + EV\_Stand(A,c2) ]

Not (karşılaştırma temeli): Split ikinci bir eşit bahis gerektirdiği için karşılaştırma mutlak beklenen getiri üzerinden yapılır. Yani EV\_Split iki elin toplam beklenen getirisi olup, EV\_Hit/Stand (tek bahiste) ile doğrudan kıyaslanır.

### 6.5 Krupiye Dağılımı (S17)

dealer\_play\_dist(total, soft, shoe, s17=True) rekürsiftir. total>21 → bust; total≥17 ve soft17 ise S17’de dur, H17’de devam (parametrik). Aksi halde olası tüm kartlar için dallan ve alt dağılımları topla.

---

## 7) State & Cache Tasarımı

### 7.1 Kanonik State Anahtarı

(player\_total, soft(0/1), dealer\_upcard, shoe\_tuple, rules\_key, split\_used(0/1))

* Aksiyon seti: State bağlamına göre {H,S,SP?}.
* 10 sınıfı tek: (10/J/Q/K) birleşimi state alanını küçültür.
* LRU Cache: dealer\_distribution ve ev\_best fonksiyonlarında kullanılır.

### 7.2 Doğruluk Koruması

* Olasılık toplam kontrolü (≈1.0).
* Aynı state için idempotent EV çıktısı.
* “Shoe − çekilen kart” işlemlerinde negatif adet guard.

---

## 8) PyQt5 UI Gereksinimleri (V1)

### 8.1 Ana Bileşenler

* Masa Paneli: En çok 6 koltuk; her koltukta kart görselleri/etiketleri, toplam/soft etiketi, HIT / STAND butonları, SPLIT (uygunsa) butonu, EV kutuları ve öneri rozeti. Split sonrası oyuncu panelinde iki el yan yana gösterilir; aktif el highlight edilir.
* Shoe Paneli: (A..10) kalan adet ve % (progress bar + sayısal).
* Krupiye Paneli: Upcard, downcard ve çekilen tüm kartlar (kullanıcı girişi); ayrıca dealer outcome çubuğu (17..21,bust yüzdeleri).
* Kontroller: “Yeni El için Kart Gir”, “Eli Sonlandır”, “Oyunu Sonlandır (Yeni Shoe)”, “Oyuncu Ekle/Sil”, “Öneriyi Uygula”.
* Log: Sadece print() (UI’da küçük bir console overlay opsiyonel).

### 8.2 Akış

1. Yeni El (aynı shoe): Oyuncu ve krupiye kartları manuel girilir → shoe düşer.
2. Motor EV’leri hesaplar; öneri gösterilir.
3. Aksiyon uygulanır; Hit’te çekilen gerçek kart girilir; Split’te iki el oluşturulur, her birine kartlar yine manuel girilir → EV’ler yenilenir.
4. Tüm oyuncular bitince kullanıcı krupiye kartlarını kuralı sağlayacak şekilde tamamlar → Eli Sonlandır: skorlar kapanır, shoe korunur.
5. Oyunu Sonlandır seçilirse: deste sayısı seçilir, yeni shoe ile tam sıfırdan başlanır.

### 8.3 UX & Performans

* Gecikmede QThread ile arka iş parçacığı.
* Aktif koltuk/aktif el highlight.
* Split uygun olduğunda buton ve rozet açık şekilde görünür.

---

## 9) Engine ↔ UI API (Öneri)

```python
class Rules:
    s17: bool = True
    bj_payout: float = 1.5
    allow_split: bool = True
    allow_double: bool = False
    split_aces_one_card_stand: bool = True
    allow_resplit: bool = False

class Engine:
    def __init__(self, rules: Rules, decks: int = 8): ...

    # Shoe
    def reset_shoe(self, decks: int | None = None) -> None: ...
    def shoe_counts(self) -> dict[int, int]: ...
    def shoe_percents(self) -> dict[int, float]: ...

    # Kart Girişi (Oyuncu & Krupiye)
    def deal_card_to_player(self, seat: int, card: int, hand_idx: int | None = None) -> None: ...
    def deal_card_to_dealer_up(self, card: int) -> None: ...
    def deal_card_to_dealer_down(self, card: int) -> None: ...
    def dealer_draw(self, card: int) -> None: ...  # manuel çekiş

    # Sorgular
    def compute_ev(self, seat: int, hand_idx: int | None = None) -> dict:
        """Return: { 'H': ev_hit, 'S': ev_stand, 'SP': ev_split_or_None, 'best': 'H'|'S'|'SP' }"""

    def can_split(self, seat: int, hand_idx: int | None = None) -> bool: ...

    # Aksiyon Uygulama
    def apply_player_action(self, seat: int, action: str, *, hand_idx: int | None = None, drawn_card: int | None = None) -> None: ...
        # action in {"H", "S", "SP"}

    # El & Oyun Yönetimi
    def end_hand(self) -> dict: ...   # {seat_index: total_win_units} — print() ile loglanır
    def end_game(self, decks: int) -> None: ...  # yeni shoe
    def new_round(self) -> None: ...

    # Log seviye
    def set_log_level(self, level: str) -> None: ...  # "info"|"debug"
```

Not: compute\_ev krupiye kartlarını olasılıksal oynatırken (hesaplamada), kullanıcı gerçek krupiye kartlarını manuel girmeye devam eder; bu ikisi birbirinden bağımsızdır. Skor kapanışı kullanıcının girdiği krupiye eline göre yapılır.

---

## 10) Test Planı (V1)

### 10.1 Birim Testleri

* Toplam/Soft Mantığı: As sayısı, soft→hard dönüşümü, bust kontrolü.
* Dealer Dağılımı (S17): Olasılık toplamı ve örnek state’lerde beklenen paternler.
* Shoe Operasyonları: Kart düşümü/geri alma, negatif sayım guard’ları.
* EV(H/S): Bilinen spotlarda tutarlılık (tam ayakkabı).
* EV(SP): (8,8)v6, (A,A)v5 gibi klasik çiftlerde EV\_SP’nin pozitif davranışı; A split kısıtının uygulanması.

### 10.2 Entegrasyon Testleri

* Çoklu oyuncu akışı: 3–6 koltukta dağıtım→karar→split→dealer→skor; print log akışı.
* Deterministiklik: Aynı state snapshot’larında aynı sonuçlar.

---

## 11) Loglama

* Yalnızca print(): her karar/çekiş/sonuç için: timestamp, seat/hand, upcard, eldeki toplam/soft, EV(H/S/SP), öneri, uygulanan aksiyon, çekilen kart(lar), el sonucu. (CSV/JSON V1’de yok.)

---

## 12) Performans & Optimizasyon

* @lru\_cache: dealer\_distribution ve ev\_best fonksiyonlarında.
* State küçültme: 10 sınıfı birleşimi; shoe\_tuple immutability.
* Erken kesme: Bust durumlarında dalı kapat.
* Hedefler: Sıcak cache tek spot < 20 ms; soğuk < 150 ms (8 deste, upcard biliniyor).

---

## 13) Kenar Durumlar

* Blackjack (oyuncu 2 kart 21): Skorlamada 3:2; split sonrası 21 blackjack sayılmaz.
* A split: Her ele 1 kart, hit yok, stand zorunlu.
* Shoe tükenmesi: N == 0 → kullanıcıya yeni ayakkabı uyarısı.
* UI veri bütünlüğü: Aynı kart iki kez girilemez; undo ile tutarlı geri dönüş (opsiyonel).
* Manual dealer: Eli Sonlandır öncesi dealer toplamı S17 kuralını sağlamıyorsa UI yönlendirici uyarı çıkarır.

---

## 14) Yapılandırma Örneği (config.yaml)

```yaml
decks: 8
rules:
  s17: true
  bj_payout: 1.5
  allow_split: true
  allow_double: false
  split_aces_one_card_stand: true
  allow_resplit: false
ui:
  max_players: 6
  manual_dealer: true
  console_overlay: true  # print akışını UI’da göstermek için opsiyonel
```

---

## 15) Mühendislik Notları

* Kısa İngilizce docstring + Türkçe yorumlar.
* typing/mypy ile tip ipuçları.
* Çekirdek saf Python; UI PyQt5; test pytest.
* Deterministiklik: RNG yalnızca test senaryolarında kullanılabilir (çekirdek hesaplamada yok).
