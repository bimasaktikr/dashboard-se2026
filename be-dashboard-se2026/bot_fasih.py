import requests
import pandas as pd
import time
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT = rf"SE2026_report_progress_{timestamp}.xlsx"

URL_PAGES = "https://fasih-sm.bps.go.id/oauth_login.html"
USERNAME_BPS = "saras.wati"  #TULISKAN TANPA @bps.go.id
PASSWORD = "saras2017!"


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto(URL_PAGES, wait_until="domcontentloaded")
    with page.expect_navigation():
        page.get_by_text("Login SSO BPS").click()

    page.wait_for_url("https://sso.bps.go.id/**", timeout=15000)
    page.wait_for_selector("#kc-login")
    page.fill("input[name='username']", USERNAME_BPS)
    page.fill("input[name='password']", PASSWORD)
    page.click("#kc-login")
    page.wait_for_url("https://**fasih-sm.bps.go.id/**")

    # Kalau ada OTP, masukkan OTP secara manual, lalu tekan ENTER
    if "https://sso.bps.go.id/auth/realms/pegawai-bps/login-actions/authenticate?execution**" in page.url:
        try:
            # Menunggu kode OTP dimasukkan
            time.sleep(10)
        except Exception as e:
            browser.close()
            
    page.wait_for_url("https://**fasih-sm.bps.go.id/**", wait_until="domcontentloaded")
    page.goto("https://fasih-sm.bps.go.id/app/surveys/a0429e96-51a5-477b-a415-485f9c153004/fd68e454-ba45-4b85-8205-f3bf777ded24", wait_until="networkidle", timeout=120000)
    print("HALAMAN FASIH SELESAI LOAD")

    cookies = {}
    for c in context.cookies():
        cookies[c["name"]] = c["value"]

    # =====================================================
    # SESSION
    # =====================================================
    session = requests.Session()
    session.headers.update({
        "Accept": "*/*",
        "Content-Type": "application/json",
        "X-XSRF-TOKEN": cookies.get("XSRF-TOKEN", ""),
        "Origin": "https://fasih-sm.bps.go.id",
        "Referer": "https://fasih-sm.bps.go.id/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/146 Safari/537.36"
    })
    session.cookies.update(cookies)

    # =====================================================
    # PAYLOAD
    # =====================================================
    payload = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "surveyRoleId": "6d7d919a-45e5-4779-bb87-2905b49fd31a",
        "size": 10,
        "page": 0,
        "search": "",
        "target": "TARGET_ONLY",
        "region": {
            "region1Id": '08761d89-218c-48f2-9c28-9903d9356164',
            "region2Id": 'dfd53bf4-6e74-4037-8926-b8435cea416d',
            "region3Id": None,
            "region4Id": None,
            "region5Id": None,
            "region6Id": None,
            "region7Id": None,
            "region8Id": None,
            "region9Id": None,
            "region10Id": None
        },
        "regionSummaryLevel": 6
    }

    # =====================================================
    # AMBIL DATA
    # =====================================================
    all_result = []
    raw_response = []
    page_num = 0

    while True:
        print("\n==============================")
        print("AMBIL PAGE:", page_num)
        print("==============================")
        payload["page"] = page_num

        try:
            r = session.post(URL, json=payload, timeout=180)
        except Exception as e:
            print("REQUEST ERROR")
            print(e)
            break

        print("STATUS:", r.status_code)
        raw_response.append({
            "page": page_num,
            "status_code": r.status_code,
            "response": r.text
        })

        if r.status_code != 200:
            print(r.text[:1000])
            break
            
        try:
            response_json = r.json()
        except Exception as e:
            print("GAGAL PARSE JSON")
            print(e)
            break

        api_data = response_json.get("data", {})
        content = api_data.get("content", [])

        if not content:
            print("CONTENT KOSONG")
            break

        all_result.extend(content)

        if api_data.get("last", False):
            print("HALAMAN TERAKHIR")
            break

        page_num += 1
        time.sleep(1)

    print("\n===================================")
    print("TOTAL USER:", len(all_result))
    print("===================================\n")

    # =====================================================
    # FLATTEN
    # =====================================================
    region_rows = []
    for item in all_result:
        regions = item.get("regionSummary") or []
        for region in regions:
            row = {
                "userId": item.get("userId"),
                "username": item.get("username"),
                "email": item.get("email"),
                "roleName": item.get("roleName"),
                "isPencacah": item.get("isPencacah"),
                "userTotal": item.get("total"),
                "regionCode": region.get("regionCode"),
                "regionTotal": region.get("total"),
                "OPEN": 0,
                "DRAFT": 0,
                "SUBMITTED BY Pencacah": 0,
                "APPROVED BY Pengawas": 0,
                "REJECTED BY Pengawas": 0
            }

            for status in region.get("statusBreakdown", []):
                status_name = status.get("status")
                count = status.get("count", 0)
                row[status_name] = count

            region_rows.append(row)

    print("\nTOTAL REGION:", len(region_rows))

   # =====================================================
    # TAHAP BARU: INJEKSI KE BACKEND API COMMAND CENTER
    # =====================================================
    API_URL = "http://127.0.0.1:8000/api/v1/sync"
    
    print("\n===================================")
    print("[INFO] MENGIRIM DATA KE DATABASE MYSQL/POSTGRES...")
    print("===================================")
    
    try:
        api_req = requests.post(API_URL, json=region_rows, timeout=30)
        
        if api_req.status_code == 200:
            resp_data = api_req.json()
            print(f"[SUCCESS] STATUS: BERHASIL!")
            print(f"[SUCCESS] PESAN : {resp_data.get('message')}")
        else:
            print(f"[WARNING] GAGAL INJEKSI. HTTP Status: {api_req.status_code}")
            print(f"[WARNING] DETAIL: {api_req.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] KONEKSI KE API GAGAL: Server mungkin mati.")
        print(f"[ERROR] ERROR DETAIL: {e}")
        print("[INFO] Mengaktifkan Mode Fallback: Menyimpan log ke Excel saja.")

    # =====================================================
    # EXPORT EXCEL (FALLBACK / BACKUP)
    # =====================================================
    df_region = pd.DataFrame(region_rows)
    df_response = pd.DataFrame(raw_response)
    
    print("\n[INFO] MENYIMPAN BACKUP EXCEL...")
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        df_region.to_excel(writer, sheet_name="Region_Status", index=False)
        df_response.to_excel(writer, sheet_name="Raw_Response", index=False)

    print("\nSELESAI")
    print("FILE BACKUP:", OUTPUT)

    # =====================================================
    # EXPORT EXCEL (FALLBACK / BACKUP)
    # =====================================================
    df_region = pd.DataFrame(region_rows)
    df_response = pd.DataFrame(raw_response)
    
    print("\n[💾] MENYIMPAN BACKUP EXCEL...")
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        df_region.to_excel(writer, sheet_name="Region_Status", index=False)
        df_response.to_excel(writer, sheet_name="Raw_Response", index=False)

    print("\nSELESAI")
    print("FILE BACKUP:", OUTPUT)