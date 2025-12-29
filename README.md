# 🛒 FetchCheckout-SendMail: Automatyzacja Porzuconych Koszyków

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Shopify](https://img.shields.io/badge/Shopify-Admin-green?style=for-the-badge&logo=shopify)

**FetchCheckout-SendMail** to zestaw narzędzi automatyzujących proces odzyskiwania utraconej sprzedaży w sklepie Shopify. System pobiera szczegółowe dane o porzuconych koszykach (linki do płatności, e-maile klientów), a następnie automatycznie wysyła spersonalizowane wiadomości przypominające.

---

## 📂 Struktura Projektu

Zrozumienie plików w repozytorium:

| Plik | Opis |
| :--- | :--- |
| `fetchchecout.py` | 🕵️ **Skraper:** Pobiera linki do checkoutu i adresy email na podstawie ID zamówień. |
| `SendMailsv2.py` | 📧 **Mailer:** Główny skrypt wysyłkowy (wersja v2). |
| `ids.txt` | 📥 **Input:** Plik wejściowy, w którym umieszczamy numery ID zamówień. |
| `results.txt` | 📤 **Output:** Plik generowany automatycznie, zawiera przetworzone dane gotowe do wysyłki. |
| `main.py` | ⚙️ **Alternatywa:** Alternatywny skrypt startowy dla procesu wysyłki. |

---

## 🚀 Instrukcja Obsługi (Krok po Kroku)

### 1. Eksport Danych z Shopify
Zaloguj się do panelu administratora i pobierz listę porzuconych koszyków. Użyj opcji **Eksportuj** (Export) do pliku Excel/CSV.

👉 **[Kliknij tutaj, aby przejść do sekcji Checkouts](https://admin.shopify.com/store/suwg0m-ia/checkouts?link_source=search&selectedView=all)**

### 2. Selekcja i Przygotowanie ID
Otwórz pobrany plik arkusza kalkulacyjnego.
1. Skopiuj kolumnę z **ID zamówienia**.
2. Wklej numery do pliku `ids.txt`.
3. **Ważne:** Upewnij się, że numery są czyste (usuń znak `#`, jeśli został skopiowany).

> **Przykład zawartości ids.txt:**
> ```text
> 66414504411461
> 66414504411462
> 66414504411463
> ```

### 3. Pobieranie Danych (Fetch)
Uruchom skrypt zbierający dane. Program połączy się ze sklepem i dla każdego ID pobierze unikalny link do dokończenia płatności oraz e-mail klienta.

✅ **Rezultat:** Dane zostaną dopisane do pliku `results.txt`.

### 4. Wysyłka Maili
Teraz uruchamiamy wysyłkę. Możesz użyć jednej z dwóch wersji skryptu (działają tak samo, wybierz preferowany):


python SendMailsv2.py

python main.py


Jasne, oto dokładnie ta brakująca część w formacie Markdown.

Skopiuj poniższy kod i wklej go na samym dole swojego pliku (zaraz pod linijką python main.py). Dodałem na początku znaczniki zamykające blok kodu (```), żeby całość się nie "rozjechała".


## 🍪 Rozwiązywanie problemów: Błąd 401 (Unauthorized)

Jeśli w konsoli zobaczysz błąd **401**, oznacza to, że Twoja sesja wygasła. Musisz ręcznie pobrać nowe `HEADERS` (nagłówki) oraz `COOKIES` (ciasteczka) i podmienić je w kodzie.

### 🛠️ Jak pobrać nowe dane logowania?

1. **Wejdź w przykładowe zamówienie**
   Otwórz w przeglądarce dowolny link do checkoutu w panelu admina, np.:
   🔗 `https://admin.shopify.com/store/NAZWA-SKLEPU/checkouts/66414504411461`

2. **Otwórz narzędzia deweloperskie**
   Kliknij prawym przyciskiem myszy na stronie i wybierz **Zbadaj** (Inspect) lub wciśnij klawisz `F12`.

3. **Skopiuj zapytanie jako cURL**
   * Przejdź do zakładki **Network** (Sieć).
   * Odśwież stronę (`F5`), aby załadowały się zapytania.
   * Znajdź główny request (zazwyczaj na samej górze listy, często ma nazwę taką jak ID zamówienia).
   * Kliknij na niego **Prawym Przyciskiem Myszy** → **Copy** → **Copy as cURL**.

   👇 **Zobacz na screenie jak to zrobić:**
   <img width="100%" alt="Poradnik cookies and headers" src="[https://github.com/user-attachments/assets/05c30417-9b49-43e9-951d-59cad8ed9e5a](https://github.com/user-attachments/assets/05c30417-9b49-43e9-951d-59cad8ed9e5a)" />

4. **Przekonwertuj cURL na Python**
   * Wejdź na stronę: 👉 [curlconverter.com](https://curlconverter.com)
   * Wklej skopiowany kod w pole tekstowe.
   * Wybierz język **Python**.

5. **Zaktualizuj skrypty**
   Strona wygeneruje kod. Skopiuj z niego **tylko** fragmenty:
   * `cookies = { ... }`
   * `headers = { ... }`

   Następnie otwórz plik `SendMailsv2.py` (lub `main.py`) i podmień stare wartości na nowe.

---

> ### ⚠️ Ważne informacje
> * Skrypt korzysta z **aktywnej sesji Shopify Admin**.
> * **Cookies wygasają** – okresowo trzeba je odnawiać (powtarzając powyższe kroki).
> * Projekt nie używa oficjalnego API Shopify, lecz symuluje działanie przeglądarki.
