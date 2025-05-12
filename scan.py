import requests
import cv2
from pyzbar.pyzbar import decode
import time
from flask import redirect, url_for
import os

# دالة للحصول على معلومات المنتج باستخدام Open Food Facts
def get_product_info(barcode):
    url = f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json'
    response = requests.get(url)
    if response.status_code == 200:
        product_data = response.json()
        if product_data.get('status') == 1:
            return product_data['product']
        else:
            print("❌ المنتج غير موجود في Open Food Facts. يحاول من الملف المحلي...")
    
    local_info = read_local_barcode(barcode)
    if local_info:
        print("✅ تم العثور على المنتج في الملف المحلي.")
        return local_info
    else:
        print("❌ لا يوجد في الملف المحلي أيضًا.")
        return None

def read_local_barcode(barcode):
    filename = "local_barcodes.txt"
    if not os.path.exists(filename):
        return None

    with open(filename, "r", encoding="utf-8") as f:
        blocks = f.read().split("==================================================")
        for block in blocks:
            lines = block.strip().splitlines()
            data = {}
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == "barcode" and val != barcode:
                        break
                    if key == "barcode":
                        data["code"] = val
                    elif key == "product name":
                        data["product_name"] = val
                    elif key == "brand":
                        data["brands"] = val
                    elif key == "ingredients":
                        data["ingredients_text"] = val
                    elif key == "energy":
                        data["nutriments"] = {"energy-kcal": val.replace("kcal", "").strip()}
            if data.get("code") == barcode:
                return data
    return None

# دالة لحفظ الصورة عند اكتشاف الباركود
def save_image(frame):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"barcode_image_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"Image saved as {filename}")

# دالة لبدء المسح باستخدام كاميرا IP Webcam عبر URL
def start_scan():
    # URL كاميرا IP Webcam
    url = "http://192.168.43.95:8080/video"  # تأكد من أن هذا هو عنوان IP الصحيح

    # الاتصال بكاميرا IP Webcam عبر URL
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        return "❌ لا يمكن الوصول إلى كاميرا الويب."

    # بدء المسح من الكاميرا عبر URL
    while True:
        ret, frame = cap.read()
        if not ret:
            return "❌ فشل في التقاط الإطار"

        # استخراج الباركود من الصورة
        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            print(f"Barcode detected: {barcode_data}")
            save_image(frame)  # حفظ الصورة عند اكتشاف الباركود
            cap.release()
            cv2.destroyAllWindows()

            # توجيه المستخدم إلى صفحة إدخال تاريخ الانتهاء مع الباركود
            return redirect(url_for('enter_expiration_date', barcode=barcode_data))

    cap.release()
    cv2.destroyAllWindows()
    return "Scan complete."
