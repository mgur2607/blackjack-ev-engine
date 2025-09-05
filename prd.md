# Blackjack EV Karar Motoru & PyQt5 Arayüzü — PRD

**Sürüm:** v1.0  
**Sahip:** Mustafa Gür (ürün sahibi) — teknik destek: ChatGPT  
**Tarih:** 02 Eylül 2025 (TRT, Europe/Istanbul)

---

## 0) TL;DR

- **Amaç:** 8 destelik Blackjack’te **kalan kart kompozisyonu** ile **tam dallanmalı (without replacement)** EV hesaplayıp **Hit / Stand / Double / Split** için en iyi kararı veren bir motor ve bunu canlı oyunda gösterecek **PyQt5** arayüz geliştirmek.  
- **Kurallar:** S17, BJ 3:2, **double sadece ilk iki karttan sonra** (tam 1 kart ve dur), **split sadece ilk iki kart aynıysa**, Insurance/Surrender **yok**, **Peek sadece upcard=A**.  
- **Kapsam:** Masada **en fazla 6 oyuncu**; her dağıtılan/çekilen kart **shoe**’dan düşülür; her state’te tüm aksiyonların EV’si hesaplanıp öneri gösterilir.

---

## 1) Hedefler ve Başarı Kriterleri

### 1.1 Hedefler
- H1 — **Doğru EV:** Kalan kart kompozisyonu ile H/S/D/Spl için **tam dallanma** EV.  
- H2 — **Gerçek Zamanlı:** Çıkan kartlar shoe’dan düşsün; EV’ler anında yenilensin.  
- H3 — **Parametrik Kurallar:** S17, 3:2 BJ, split & double kısıtları, Peek(A) bayraklarla ayarlanabilir.  
- H4 — **Kullanıcı Arayüzü:** PyQt5 masa görünümü + EV panelleri + shoe yüzdeleri + “öneriyi uygula”.  
- H5 — **Performans:** 8 deste için tek spot EV hesabı sıcak cache ile **< 30 ms**, soğuk **< 150 ms**.

### 1.2 Kabul Kriterleri
- A1 — Krupiye dağılımı (17/18/19/20/21/bust) olasılıkları **≈1.0** toplar (±1e−9).  
- A2 — Temel spot doğrulamaları (ör. 10v5: Double EV > Stand EV).  
- A3 — Peek(A): Dealer BJ ise el anında biter; değilse oyun kaldığı yerden devam.  
- A4 — Split: **tek split** destekli; A-A splitte **tek kart** ve dur (bayrakla yönetilir).  
- A5 — UI: Kart girildiğinde shoe & EV & öneri otomatik güncellenir.  
- A6 — Aynı state → aynı EV & öneri (deterministik).

---

## 2) Kapsam & Kısıtlar

### 2.1 Oyun Kuralları (sabit)
- **Deste:** 8 deste; oyun başında karışık. 10/J/Q/K → tek sınıf “10”.  
- **Krupiye:** S17 (soft 17’de durur).  
- **Ödeme:** Blackjack 3:2; diğer sonuçlar +1 / 0 / −1.  
- **Double:** Sadece **ilk iki kart**; **tek kart çekip dur**.  
- **Split:** Sadece **ilk iki kart eşitse**; V1’de **tek split** (resplit yok).  
- **A-A Split:** Varsayılan **tek kart** ve dur (parametrik).  
- **Insurance/Surrender:** Yok.  
- **Peek:** Sadece **upcard = A** (dealer BJ kontrolü).

### 2.2 Masa & UI
- En fazla 6 oyuncu. PyQt5: masa görünümü, seat panelleri, shoe barları, EV kutuları, aksiyon butonları.

### 2.3 Kapsam Dışı (V1)
- H17 modu, insurance, surrender, çoklu resplit, yan bahisler, çoklu masa.

---

## 3) Kullanıcı Senaryoları

- **S1 — Canlı Oyun:** Dağıtılan kartlar UI’dan girilir → shoe düşer → motor EV/öneri verir → kullanıcı aksiyonu uygular (Hit/Double’da **çekilen gerçek kart** girilir) → yine shoe düşer → tüm oyuncular bitince dealer oynar (S17) → sonuçlar.  
- **S2 — Simülasyon:** Rastgele çekim modu; otomatik akış ve log.  
- **S3 — Analiz:** Belirli spotlar için EV parçalanımı, krupiye dağılımı ve shoe yüzdeleri.

---

## 4) Sistem Mimarisi

```
PyQt5 UI  <-->  Engine Facade  <-->  EV Core (DP + Cache)
     ^                |                    |
     |                v                    v
 Table/Game Loop   Shoe/Rules Model   Dealer Dist Cache
```

- **EV Core:** Rekürsif DP + `@lru_cache`, without-replacement olasılıklar.  
- **Dealer Dist:** Upcard + shoe → {17..21,bust}.  
- **Game Loop:** Sıra yönetimi, gerçek çekilen kartların shoe’dan düşmesi, skor.  
- **Facade:** UI ile sade API.

---

## 5) Veri Modelleri

### 5.1 Shoe
- Tuple[int × 10]: `(A,2,3,4,5,6,7,8,9,10)` sayıları.  
- Başlangıç (8 deste): `(32,32,32,32,32,32,32,32,32,128)`.

### 5.2 Hand
- `cards: tuple[int,...]` (ör. `(6,4)`)  
- `total: int`, `soft: bool`  
- `is_initial_two: bool` (double/split uygunluğu)  
- `is_pair: bool` (`len(cards)==2 && cards[0]==cards[1]`)

### 5.3 Table
- `players: list[Hand] (<=6)`; split sonrası aktif eller listesi olabilir  
- `dealer_upcard: int | None`  
- `shoe: tuple[int,...]`  
- `rules: Rules`  
- `turn_index: int`, `log: list`

---

## 6) EV Matematiği (Tam Dallanma)

**Kart olasılığı:** \( p(c) = \#c / N \), N=kalan kart.  

**Stand:**  
\( \mathrm{EV}_S = \sum_{d \in \{17,18,19,20,21,\mathrm{bust}\}} \Pr(d)\cdot r(	ext{player}, d) \)  
r: +1 (win), 0 (push), −1 (loss).

**Hit:**  
\( \mathrm{EV}_H = \sum_c p(c)\cdot
egin{cases}
-1, & 	ext{bust} \
\max(\mathrm{EV}_S,\mathrm{EV}_H,\mathrm{EV}_D,\mathrm{EV}_P), & 	ext{aksi halde}
\end{cases}
\)

**Double:** (yalnızca ilk iki kart)  
Tek kart çek → mecburi Stand → **2×**:  
\( \mathrm{EV}_D = 2 \cdot \sum_c p(c)\cdot \mathrm{EV}_S(	ext{player}+c) \)

**Split:** (V1 tek split)  
İki ele ayrılır; el‑1 ikinci kartı koşullu çeker (shoe’dan düşer), sonra el‑2 ikinci kartını çeker (yine düşer); A‑A ise tek kart ve dur. Toplam EV, iki elin beklenen sonuçlarının toplamıdır.

**Dealer Dağılımı (S17):**  
`dealer_play_dist(total, soft, shoe, s17)` rekürsifi; `total>21 → bust`; `total≥17` ve **(soft17 & H17)** değilse dur; aksi halde tüm kartları çek → alt dağılımlar toplanır.

**Peek(A):**  
\(p_{BJ} = \#10 / N\). Dealer BJ ise el anında biter; değilse kaldığı yerden devam. (V2’de “no‑BJ” kolunda hole ≠ 10 koşullamasını shoe’a yedireceğiz.)

---

## 7) Algoritma, State ve Cache

- **State (kanonik):**  
  `(player_total, soft(0/1), upcard, shoe_tuple, can_double(0/1), is_initial_two(0/1), sorted_cards_tuple, rules_key)`  
- **Cache:** `@lru_cache` hem `dealer_distribution` hem `EV` için.  
- **10 sınıfı:** 10/J/Q/K tek sınıf.  
- **Kesme:** Double sadece ilk iki kartta; A‑split tek kart; resplit yok.

Hedef: Sıcak cache ile tek spot < 30 ms.

---

## 8) PyQt5 UI Gereksinimleri

### 8.1 Bileşenler
- **Masa Paneli:** 6 koltuk; her koltukta kartlar, toplam/soft etiketi, H/S/D/P butonları, EV kutuları ve **öneri rozeti**.  
- **Shoe Paneli:** (A..10) adet ve % (progress bar).  
- **Krupiye Paneli:** Upcard ve dealer outcome bar grafiği (17..21,bust yüzdeleri).  
- **Log Paneli:** Dağıtım/çekiş/sonuç; geri al (opsiyon).  
- **Kontroller:** “Yeni El”, “Öneriyi Uygula”, “Kart Gir (A..10)”, “Rastgele Çek”.

### 8.2 Akış
1) Yeni el → kullanıcı dağıtım kartlarını girer (oyuncular + krupiye upcard) → shoe düşer.  
2) Motor EV’leri hesaplar; öneri gösterilir.  
3) Aksiyon uygulanır; Hit/Double’da çekilen **gerçek kart** UI’dan girilir → shoe tekrar düşer → EV’ler yenilenir.  
4) Tüm oyuncular bitince dealer oynatılır (S17) → skorlanır.

### 8.3 Performans
- Hesaplama ana thread’de; takılma olursa `QThread` ile arka iş parçacığı (opsiyon).

---

## 9) Engine ↔ UI API (öneri)

```python
class Rules: ...
class Engine:
    def __init__(self, rules: Rules, decks: int = 8): ...
    def reset_shoe(self) -> None: ...
    def shoe_counts(self) -> dict[int,int]: ...
    def shoe_percents(self) -> dict[int,float]: ...

    # State mutators
    def deal_card_to_player(self, seat: int, card: int) -> None: ...
    def deal_card_to_dealer_up(self, card: int) -> None: ...
    def commit_dealer_peek_if_needed(self) -> None: ...  # upcard=A ise kontrol
    def player_action(self, seat: int, action: str, drawn_card: int | None) -> None: ...
        # action ∈ {"H","S","D","P"}

    # Queries
    def compute_ev(self, seat: int) -> dict:
        # { 'H':ev_h, 'S':ev_s, 'D':ev_d, 'P':ev_p, 'best':'H' }
        ...

    # Round control
    def play_dealer_and_score(self) -> dict: ...  # {seat: +1/0/-1; double/split ölçeği dahil}
    def new_round(self) -> None: ...
```

---

## 10) Test Planı

### 10.1 Birim
- `hand_add` (A yumuşama / soft→hard dönüşümü).  
- `dealer_play_dist` S17 doğruluğu ve olasılık toplamı.  
- `dealer_distribution` upcard örnekleri.  
- EV kısıtları: double sadece ilk iki kartta; split tek; A‑A tek kart.

### 10.2 Entegrasyon
- Başlangıç 8 deste: 10v5 (Double>Stand), 16v10 (Hit≥Stand), 8‑8v10 (Split≥diğerleri), A‑7v9 vb.

### 10.3 Regresyon
- Belirli `shoe` + `state` → EV vektörlerini golden snapshot olarak saklayıp kıyaslama.

---

## 11) Loglama & Analitik
- Her eylem/çekiş: timestamp, state özeti, aksiyon, EV’ler, sonuç; CSV/JSON export.  
- “En çok hatalı seçilen spotlar”, “en yüksek edge noktaları” raporları (opsiyon).

---

## 12) Performans & Optimizasyon
- `@lru_cache` anahtarları küçük ve immütabl; 10 sınıfı tek.  
- Split akışı: el‑1 ikinci kart → el‑2 ikinci kart; her adımda shoe güncelle.  
- Gerekirse **V2:** derinlikte Monte Carlo kesimi; Peek(A) tam koşullu modu.

---

## 13) Kenar Durumlar
- `shoe_size == 0` → dur varsayımı.  
- A‑A split kuralı (tek kart).  
- Double sonrası mecburi stand.  
- Push=0; double’da 2×, split’te iki el ayrı skorlanır.  
- Peek(A) “basit mod” (V1) → “tam koşullu” (V2) yol haritası.

---

## 14) Yapılandırma Örneği (config.yaml)

```yaml
decks: 8
rules:
  s17: true
  bj_payout: 1.5
  allow_double_any_two: true
  allow_double_after_split: false
  allow_resplit: false
  split_aces_one_card: true
  peek_on_ace: true
ui:
  max_players: 6
```

---

## 15) Yol Haritası

- **M1:** EV çekirdeği (H/S/D), dealer dağılımı, cache, temel testler.  
- **M2:** Split (tek), A‑A tek kart; Peek(A) basit mod.  
- **M3:** PyQt5 MVP (2 koltuk), shoe paneli, EV paneli, öneriyi uygula.  
- **M4:** 6 koltuk, dealer oyunu, log/export.  
- **M5:** Peek tam koşullu, Monte Carlo kesim, çoklu masa.

---

## 16) Riskler & Azaltımlar
- **Performans:** 8 deste dallanması ağır → cache/memoization + 10 sınıfı tek.  
- **Peek duyarlılığı:** Basit mod yeterli; V2’de tam koşullu.  
- **UI donması:** Gerekirse QThread ile arka plan hesaplama.

---

## 17) Örnek Doğrulama Beklentileri
- 10 vs 5 → Double EV > Stand EV.  
- 16 vs 10 → Hit EV ≥ Stand EV.  
- A‑A vs 6 → Split EV ≥ diğerleri.  
(Referanslar, kurallar sabitken tutarlı olmalı.)

---

## 18) Lisans & Uyarı
Bu yazılım eğitim/araştırma amaçlıdır. Gerçek kumar ortamlarında kullanım ve yerel düzenlemelere uyum kullanıcı sorumluluğundadır.
