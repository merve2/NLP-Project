from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import re

yorumlar_csv = "yorumlar.csv"

# Ürün linkleri bir dosyada. Satır satır okuyup boşları atıyoruz
with open("urun_linkleri.txt", "r", encoding="utf-8") as f:
    urun_linkleri = [line.strip() for line in f if line.strip()]

# Linkin içinden ürün ID'sini çekiyoruz
def urun_id_bul(link):
    # pm- ile başlayan ID varsa onu döndür
    match = re.search(r'pm-([A-Z0-9]+)', link)
    if match:
        return match.group(1)
    # -p- ile başlayan ID varsa onu döndür
    match = re.search(r'-p-([A-Z0-9]+)', link)
    if match:
        return match.group(1)
    # HBC ile başlayanlar için
    match = re.search(r'(HBC[A-Z0-9]{5,})', link)
    if match:
        return match.group(1)
    return "urunid-bulunamadi"

# Her ürün linkinin yorumlar sayfası linkini oluşturuyoruz
def yorum_linki_olustur(link):
    # Eğer linkte "-pm-" geçiyorsa parçala ve ekle
    if "-pm-" in link:
        return link.split("?")[0] + "-yorumlari?sayfa="
    else:
        # Diğer tüm durumlarda sonuna ekle
        return link + "-yorumlari?sayfa="

# Tarayıcı ayarlarını yapıyoruz (bildirimler vs. kapanıyor)
ayarlar = Options()
ayarlar.add_argument("--start-maximized")
ayarlar.add_argument("--disable-notifications")
ayarlar.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=ayarlar)

with open(yorumlar_csv, mode="w", newline='', encoding="utf-8") as dosya_yorum:
    yazici_yorum = csv.writer(dosya_yorum)
    yazici_yorum.writerow(["urun_id", "yorum", "star"])  # başlıklar

    for urun_linki in urun_linkleri:
        urun_id = urun_id_bul(urun_linki)  # ID bul
        yorum_sayfasi_taban_link = yorum_linki_olustur(urun_linki) 

        print(f"\n Ürün işleniyor: {urun_id}")

        yorumlar = []     # Aynı yorumu tekrar eklememek için liste tutuyoruz
        sayfa_no = 1      # Her ürün için sayfa numarasını başlat

        # Sonsuz döngü - yorumlar bitene kadar dönüyor
        while True:
            yorum_sayfa_linki = yorum_sayfasi_taban_link + str(sayfa_no) 
            print(f"  Sayfa {sayfa_no}: {yorum_sayfa_linki}")
            driver.get(yorum_sayfa_linki)        
            time.sleep(3)                       

            #  yorumlar CSS selector ile geliyor
            yorum_kartlari = driver.find_elements(By.CSS_SELECTOR, "div.hermes-ReviewCard-module-KaU17BbDowCWcTZ9zzxw")
            if not yorum_kartlari:
                print(" ---Yorum sayfaları bitti---")
                break  # kart yoksa bitmiş demektir

            yeni_yorum_sayisi = 0  

           
            for kart in yorum_kartlari:
                try:
                    # Yorum metnini span etiketiyle alıyoruz
                    yorum_span = kart.find_element(By.TAG_NAME, "span")
                    yorum = yorum_span.text.strip()
                except:
                    yorum = "" 

                star = ""  
                try:
                    # Yıldızlar bazen kartın bir üstünde, bazen iki üstünde olabiliyor
                    parent = kart.find_element(By.XPATH, "..")
                    rating_div = None
                    try:
                        rating_div = parent.find_element(By.CSS_SELECTOR, "div.hermes-RatingPointer-module-UefD0t2XvgGWsKdLkNoX")
                    except:
                        grandparent = parent.find_element(By.XPATH, "..")
                        try:
                            rating_div = grandparent.find_element(By.CSS_SELECTOR, "div.hermes-RatingPointer-module-UefD0t2XvgGWsKdLkNoX")
                        except:
                            rating_div = None

                    # Yıldız kutusunun içindeki yıldız (div.star) sayısını alıyoruz
                    if rating_div:
                        star = len(rating_div.find_elements(By.CSS_SELECTOR, "div.star"))
                except:
                    star = ""  

              
                if yorum and (yorum, star) not in yorumlar:
                    yorumlar.append((yorum, star))
                    yazici_yorum.writerow([urun_id, yorum, star])
                    yeni_yorum_sayisi += 1

            print(f"  {yeni_yorum_sayisi} yorum eklendi. Toplam: {len(yorumlar)}")

            
            if yeni_yorum_sayisi == 0:
                break
            sayfa_no += 1   


driver.quit()
print("\n Tüm yorumlar başarıyla 'yorumlar.csv' dosyasına kaydedildi.")