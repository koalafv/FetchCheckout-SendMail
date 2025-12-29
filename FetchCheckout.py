import requests
import json
import time
import os
import concurrent.futures
import threading

# --- KONFIGURACJA PLIKÓW ---
INPUT_FILE = 'ids.txt'      # Plik z listą ID
OUTPUT_FILE = 'results.txt' # Plik wynikowy
MAX_WORKERS = 5             # Liczba jednoczesnych zapytań (dla szybkości)

# --- TWOJE DANE SESJI (Zaktualizowane z Twojego kodu) ---
cookies = {
    '_shopify_essential_': 'b88d1a9c-16a9-4936-abb2-f401e3f02199',
    '_shopify_y': '5fd897a2-4304-45da-bf85-6fe2d61efd2d',
    'privacy_signal': 'eyJjb25zZW50ZWRBbGwiOiItMSIsImNvbnNlbnRlZEFuYWx5dGljcyI6Ii0xIiwiY29uc2VudGVkRnVuY3Rpb25hbCI6Ii0xIiwiY29uc2VudGVkTWFya2V0aW5nIjoiLTEiLCJjb3VudHJ5Q29kZSI6IlBMIiwicmVnaW9uQ29kZSI6IiIsImNvbXBsaWFuY2Vab25lIjoiZ2RwciIsInJvb3REb21haW4iOiIuc2hvcGlmeS5jb20iLCJkYXRlIjoiMTc2NjIzMTI3NzU2OSIsInVybCI6Imh0dHBzOi8vYXBwcy5zaG9waWZ5LmNvbS9rbGF2aXlvLWVtYWlsLW1hcmtldGluZz9sb2NhbGU9cGwmc3RfY2FtcGFpZ249YWRtaW4tc2VhcmNoJnN0X3NvdXJjZT1hZG1pbi13ZWImdXRtX2NhbXBhaWduPWFkbWluLXNlYXJjaCZ1dG1fc291cmNlPXNob3BpZnkiLCJhcGlWZXJzaW9uIjoiMS4wLjIifQ%3D%3D',
    'cf_clearance': 'A.ZY0zrrBchBlPXuAZgUn9eodP9IjRgrQQfra_XmPx8-1767005778-1.2.1.1-1JENbB13R856EHg_9joqdXSvPYwai1zTB5NtGBqZ6GrTM75EyTIoZoYqRN.B8ll6VDJNabEEzFr77ethQgW5qmXhp606C4X2ZZQ6yPaZuWr88P.XByEeCN057e66WCRJO4sDziv8UgR95H38Gw.mIps86hq3zUhQQlfZ3E9vVTnIhUturGnv2urZF9HkJAXGuJTW08QB1_TjnWy4Hq3drwHRmI2sBwe8zjV551HNF0c',
    'koa.sid': 'abv69GoojLBhaUGjcm3jWrkzoBejM4IT',
    'koa.sid.sig': 'JTiPkV6TGCgI7EZlQKNLs8zCRKo',
    '_shopify_s': 'e7890304-a918-42f2-b3f2-d4b21869fc2e',
    '_merchant_essential': '%3AAZtqS3oQAAEAWgwr8IzuGiO-bKHHp030Sj27Q5WAFz4B62Cb7PBb72KDdrI8Ekd0U0GoCB5-GesvlD0biYDGj1pstzkXZt9B1UD9t_rjZW-RQhwRhU1x7ipjEiqUuuCSvgJiWGEKRM3cMN6Cmytrwvts6ms1pPMU7eWxtEGnMq2px_xkcBaVav02o_e1StQ1Ww4Pv-gMXaO3YyVcZCV6CcvUFU35S0A07SJy_Z_g53decfo4r5sxGDz8sfTwTRndGGwHR2pa5MhDxNUQzPN4g9uJDlvyuoaH1vas3tuCoO9-vjba7aTewXeEZuoV78CtWYRe_0o8Jr9PxPzUGaUpppwtMt7GUYBKFBiS3_scwq2nS9c7HpNn0gZBrSWhDVbMxLICvwFG2XADwH5DFCo4yh--1id534P0UV1YWlFbvygSRVbSwOq4EAlPhCE-kn5ZgS_kdPAzPbgc91qpsjEm1r0aKaMtAWzl61CWcH83bgJFYoD6rw5vjgts6onA4Nq577MjN9NMX6NE6fuXqybDDQ0djnOW8SVf5DV4X32csYFe7CAYXXH6E_a1bugE972JAzY51BgxAitiEDM6yZtgeMAR6UzeQFty7aRybTW7axo4ryWTcJvfJzegPNK0RWy65wi6w75WgK4D_9-mvg8jRzbaXEleW2iv2a72-wOyOEFtRisAUH-Q8CVGvdqp%3A',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'pl-PL,pl;q=0.8',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Brave";v="143.0.0.0", "Chromium";v="143.0.0.0", "Not A(Brand";v="24.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"19.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    # WAŻNE: Jeśli dostaniesz błąd 401, sprawdź czy nie brakuje tu nagłówka 'x-csrf-token'
}

# Blokada, żeby wątki nie pisały do pliku w tym samym czasie
file_lock = threading.Lock()

def fetch_checkout_data(checkout_id):
    """Pobiera dane dla konkretnego ID z Shopify API"""
    variables = {
        "queryAutomationResults": True,
        "componentLimit": 30,
        "id": f"gid://shopify/AbandonedCheckout/{checkout_id}",
        "checkoutId": f"gid://shopify/Checkout/{checkout_id}"
    }

    params = {
        'operationName': 'AbandonedCheckout',
        'variables': json.dumps(variables),
    }

    url = 'https://admin.shopify.com/api/operations/a3098ffb06342d22576490de1a36313938122f2d7989399c19ef79689cb18775/AbandonedCheckout/shopify/suwg0m-ia'

    try:
        response = requests.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=10
        )
        
        # Obsługa zbyt szybkich zapytań (Rate Limit)
        if response.status_code == 429:
            time.sleep(2)
            return fetch_checkout_data(checkout_id)
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Możesz odkomentować linię niżej, żeby widzieć błędy
        # print(f"❌ Błąd połączenia dla ID {checkout_id}: {e}")
        return None

def process_single_id(checkout_id):
    """Funkcja, którą wykonuje każdy wątek"""
    data = fetch_checkout_data(checkout_id)
    
    if data and 'data' in data and data['data']['abandonedCheckout']:
        ac_data = data['data']['abandonedCheckout']
        
        url = ac_data.get('abandonedCheckoutUrl', 'BRAK_URL')
        customer = ac_data.get('customer')
        email = customer.get('email', 'BRAK_EMAIL') if customer else 'BRAK_DANYCH_KLIENTA'

        result_line = f"{email}:{url}"
        print(f"✅ Znaleziono: {email}")
        
        # Bezpieczny zapis do pliku z użyciem blokady (Lock)
        with file_lock:
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as outfile:
                outfile.write(result_line + '\n')
                outfile.flush()
        return True
    else:
        print(f"⚠️  Brak danych/Błąd: {checkout_id}")
        return False

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Błąd: Nie znaleziono pliku {INPUT_FILE}. Stwórz go i wklej numery ID.")
        return

    print(f"📂 Wczytywanie pliku {INPUT_FILE} i usuwanie duplikatów...")

    # 1. Wczytanie i usunięcie duplikatów (używamy set)
    unique_ids = set()
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile:
        for line in infile:
            clean_id = line.strip().replace('#', '')
            if clean_id:
                unique_ids.add(clean_id)
    
    print(f"ℹ️  Unikalnych ID do sprawdzenia: {len(unique_ids)}")
    print(f"🚀 Uruchamiam {MAX_WORKERS} wątków...")

    # 2. Przetwarzanie wielowątkowe
    found_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # map() uruchamia funkcję process_single_id dla każdego ID z listy
        results = executor.map(process_single_id, unique_ids)
        
        # Zliczanie sukcesów
        for success in results:
            if success:
                found_count += 1

    print(f"\n🏁 Zakończono! Zapisano {found_count} wyników w pliku {OUTPUT_FILE}")

if __name__ == "__main__":
    main()