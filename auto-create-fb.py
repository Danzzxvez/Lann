import os, sys, re, time, random, string, requests
from bs4 import BeautifulSoup
from pystyle import Colors, Colorate, Write
from faker import Faker

# [CONFIG]
fake = Faker()
oks = []
cps = []
loop = 0
G = "\033[1;32m"
Y = "\033[1;33m"
C = "\033[1;36m"
W = "\033[1;37m"
R = "\033[0m"

# --- MASUKKAN API KEY ANDA DI SINI ---
SMS_ACTIVATE_KEY = "MASUKKAN_API_KEY_DISINI" 

class SMSGateway:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.sms-activate.org/stubs/handler_api.php"

    def get_number(self, service='fb', country=6): # 6 = Indonesia
        params = {'api_key': self.api_key, 'action': 'getNumber', 'service': service, 'country': country}
        try:
            res = requests.get(self.url, params=params).text
            if "ACCESS_NUMBER" in res:
                _, order_id, phone = res.split(':')
                return order_id, phone
            return None, res
        except Exception:
            return None, "Error Koneksi API"

    def get_status(self, order_id):
        params = {'api_key': self.api_key, 'action': 'getStatus', 'id': order_id}
        return requests.get(self.url, params=params).text

    def set_status(self, order_id, status):
        """Status 6 = Selesai, Status 8 = Batalkan"""
        params = {'api_key': self.api_key, 'action': 'setStatus', 'status': status, 'id': order_id}
        return requests.get(self.url, params=params).text

def get_user_agent():
    rr = random.randint
    rc = random.choice
    devices = ["CPH2461","CPH2451","X669C","SM-G975F","SM-A515F","X6823","V2202","RMX3511"]
    android_ver = rr(9, 14)
    chrome_ver = f"{rr(110, 126)}.0.{rr(5000, 7000)}.{rr(80, 200)}"
    build_id = rc(["TP1A", "TKQ1", "RKQ1", "SP1A", "SKQ1", "RP1A"])
    fbav = f"{rr(350, 460)}.0.0.{rr(10, 99)}.{rr(100, 999)}"
    fbbv = rr(100000000, 999999999)
    return (f"Mozilla/5.0 (Linux; Android {android_ver}; {rc(devices)} Build/{build_id}; wv) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{chrome_ver} "
            f"Mobile Safari/537.36 [FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};]")

def extractor(data):
    soup = BeautifulSoup(data, "html.parser")
    return {i.get("name"): i.get("value") for i in soup.find_all("input") if i.get("name")}

def linex():
    print("\033[1;37m" + "━" * 60)

# --- SISTEM UTAMA ---
sms_api = SMSGateway(SMS_ACTIVATE_KEY)

def create_account(num, mode):
    global loop
    for _ in range(num):
        loop += 1
        ua = get_user_agent()
        ses = requests.Session()
        order_id, target, otp = None, None, "N/A"
        
        # Progress UI
        sys.stdout.write(f"\r\033[1;37m{C}[RUNNING]{R} {loop}/{num} {G}OK:{len(oks)} {Y}CP:{len(cps)} ")
        sys.stdout.flush()

        try:
            # Step 1: Ambil Data Identitas
            if mode == "phone":
                order_id, target = sms_api.get_number()
                if not order_id: 
                    print(f"\n[!] Gagal ambil nomor: {target}")
                    break
            else:
                target = f"{fake.user_name()}{random.randint(10,999)}@gmail.com"

            # Step 2: Akses Halaman Registrasi
            res = ses.get('https://m.facebook.com/reg', timeout=20)
            reg_data = extractor(res.text)
            
            password = f"VARKCOZERY{random.randint(1000,9999)}123"
            
            payload = {
                'lsd': reg_data.get('lsd'),
                'jazoest': reg_data.get('jazoest'),
                'firstname': fake.first_name(),
                'lastname': fake.last_name(),
                'birthday_day': str(random.randint(1, 28)),
                'birthday_month': str(random.randint(1, 12)),
                'birthday_year': str(random.randint(1995, 2005)),
                'reg_passwd__': password,
                'sex': str(random.randint(1, 2)),
                'submit': "Sign Up",
            }
            
            if mode == "phone":
                payload['reg_phone_1__'] = target
            else:
                payload['reg_email__'] = target

            headers = {
                "Host": "m.facebook.com", 
                "User-Agent": ua, 
                "Referer": "https://m.facebook.com/reg",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            response = ses.post("https://m.facebook.com/reg/submit/", data=payload, headers=headers, timeout=25)

            # Step 3: Verifikasi Keberhasilan
            cookies_dict = ses.cookies.get_dict()
            
            if "c_user" in cookies_dict:
                uid = cookies_dict['c_user']
                cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                
                # Tunggu OTP jika pakai nomor telepon
                if mode == "phone" and order_id:
                    print(f"\n[!] Menunggu SMS untuk {target}...")
                    for _ in range(15): # Cek selama ~2.5 menit
                        status = sms_api.get_status(order_id)
                        if "STATUS_OK" in status:
                            otp = status.split(':')[1]
                            sms_api.set_status(order_id, 6) # Konfirmasi sukses ke API
                            break
                        time.sleep(10)
                
                print(f"""
{G}╭─[ SUCCESS ]
{G}├─ UID      : {uid}
{G}╰─ PASSWORD : {password}{R}
""")
                print(f"""
{G}╭─[ SESSION COOKIES ]
{G}╰─➤ {cookies_str}{R}
""")
                oks.append(uid)
                with open("/sdcard/varkcozery-ok.txt", "a") as f:
                    f.write(f"{uid}|{password}|{target}|{otp}|{cookies_str}\n")
                linex()
            
            elif "checkpoint" in response.url:
                print(f"\n\033[1;33m[CP] {target} (Akun terkena checkpoint)")
                cps.append(target)
                if order_id: sms_api.set_status(order_id, 8)

            else:
                if order_id: sms_api.set_status(order_id, 8)

        except Exception as e:
            if order_id: sms_api.set_status(order_id, 8)
            continue

def main():
    if os.name == 'nt': os.system("cls")
    else: os.system("clear")
    
    banner = "AUTO CREATE FB - NOMOR TELEPON 082121348660 - BY VARKCOZERY"
    print(Colorate.Horizontal(Colors.green_to_white, banner))
    linex()
    print(" [1] CREATE WITH PHONE (DALAM PERCOBAAN)")
    print(" [2] CREATE WITH EMAIL (TEMPORARY)")
    linex()
    
    m_choice = input(" [?] CHOOSE : ")
    try:
        num = int(input(" [?] JUMLAH AKUN : "))
    except ValueError:
        num = 1
    
    if m_choice == '1':
        create_account(num, "phone")
    else:
        create_account(num, "email")

    print(f"\n\n[!] SELESAI. TOTAL OK: {len(oks)} - CP: {len(cps)}")

if __name__ == "__main__":
    main()