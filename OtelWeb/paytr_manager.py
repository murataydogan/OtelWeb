import base64
import hmac
import hashlib
import requests
import json


class PayTRManager:
    def __init__(self):
        # ============================================================
        # BURASI OTEL SAHİBİNİN PAYTR BİLGİLERİYLE DOLDURULACAK
        # ============================================================
        self.merchant_id = 'XXXXXX'  # PayTR Mağaza No
        self.merchant_key = 'YYYYYY'  # PayTR Mağaza Parolası
        self.merchant_salt = 'ZZZZZZ'  # PayTR Mağaza Gizli Anahtarı
        self.test_mode = "1"  # 1 = Test Modu (Satıştan önce test için), 0 = Gerçek Mod
        # ============================================================

    def odeme_formu_olustur(self, user_ip, user_name, user_address, user_phone, user_email, payment_amount,
                            basket_items, rez_id, callback_url):
        try:
            # PayTR API Ayarları
            url = "https://www.paytr.com/odeme/api/get-token"

            # Sepeti PayTR formatına çevir (Örn: [['Oda Rezervasyonu', '1500.00', 1]])
            user_basket_arr = []
            for item in basket_items:
                user_basket_arr.append([item['name'], str(item['price']), 1])
            user_basket = base64.b64encode(json.dumps(user_basket_arr).encode()).decode()

            # Zorunlu Alanlar
            merchant_oid = "REZ" + str(rez_id) + "R" + str(int(payment_amount))  # Her işlem için benzersiz ID
            currency = "TL"
            no_installment = "0"  # Taksit yok
            max_installment = "0"
            debug_on = "1"
            timeout_limit = "30"

            # Token Oluşturma (Güvenlik imzası)
            hash_str = str(self.merchant_id) + user_ip + merchant_oid + user_email + str(
                payment_amount) + user_basket + no_installment + max_installment + currency + self.test_mode
            paytr_token = hmac.new(self.merchant_key.encode(), hash_str.encode() + self.merchant_salt.encode(),
                                   hashlib.sha256).digest()
            paytr_token = base64.b64encode(paytr_token).decode()

            # API'ye İstek Gönder
            params = {
                'merchant_id': self.merchant_id,
                'user_ip': user_ip,
                'merchant_oid': merchant_oid,
                'email': user_email,
                'payment_amount': str(payment_amount),
                'paytr_token': paytr_token,
                'user_basket': user_basket,
                'debug_on': debug_on,
                'no_installment': no_installment,
                'max_installment': max_installment,
                'user_name': user_name,
                'user_address': user_address,
                'user_phone': user_phone,
                'merchant_ok_url': callback_url,  # Başarılı olunca döneceği yer
                'merchant_fail_url': callback_url,  # Hata alınca döneceği yer
                'timeout_limit': timeout_limit,
                'currency': currency,
                'test_mode': self.test_mode
            }

            result = requests.post(url, data=params)
            res = result.json()

            if res['status'] == 'success':
                # Başarılıysa bize bir IFRAME (Ödeme Ekranı Linki) verir
                return {'status': 'success', 'token': res['token']}
            else:
                return {'status': 'error', 'message': res['reason']}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}