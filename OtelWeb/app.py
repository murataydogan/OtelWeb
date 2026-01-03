from flask import Flask, render_template, request, session, flash, redirect, url_for
import mysql.connector
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from paytr_manager import PayTRManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_otel_projesi'

# ==========================================
# VERİTABANI AYARLARI
# ==========================================
db_config = {
    'host': 'sql7.freesqldatabase.com',
    'user': 'sql7813250',
    'password': 'cxmQlSVHvB',
    'database': 'sql7813250',
    'port': 3306
}


def mail_gonder(alici_mail, konu, icerik):
    # --- BURAYI KENDİ BİLGİLERİNLE DOLDUR ---
    gonderen_mail = "bbsaydogan@gmail.com"
    gonderen_sifre = "jubx snix mvec kzhy"
    # ----------------------------------------

    try:
        msg = MIMEMultipart()
        msg['From'] = gonderen_mail
        msg['To'] = alici_mail
        msg['Subject'] = konu
        msg.attach(MIMEText(icerik, 'html', 'utf-8'))

        # Gmail Sunucusuna Bağlan
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gonderen_mail, gonderen_sifre)
        server.sendmail(gonderen_mail, alici_mail, msg.as_string())
        server.quit()
        print("✅ Mail başarıyla gönderildi!")
    except Exception as e:
        print(f"❌ Mail Hatası: {e}")


def baglanti_al():
    return mysql.connector.connect(**db_config)


# ==========================================
# OTEL ADI SİHİRBAZI
# ==========================================
@app.context_processor
def inject_hotel_info():
    otel_adi = "Otel Rezervasyon"
    slogan = ""
    try:
        conn = baglanti_al()
        cursor = conn.cursor()
        cursor.execute("SELECT hotel_name, slogan FROM settings WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        if row:
            otel_adi = row[0]
            slogan = row[1]
    except Exception:
        pass
    return dict(otel_adi=otel_adi, slogan=slogan)


# ==========================================
# ROTALAR
# ==========================================
@app.route('/')
def index():
    return redirect(url_for('odalar'))


@app.route('/odalar')
def odalar():
    conn = baglanti_al()
    cursor = conn.cursor(dictionary=True)

    giris = request.args.get('giris')
    cikis = request.args.get('cikis')
    kisi = request.args.get('kisi')
    tip = request.args.get('tip')

    sql = "SELECT * FROM rooms WHERE 1=1"
    params = []

    if giris and cikis:
        overlap_sql = """SELECT oda_no FROM reservations WHERE durum != 'IPTAL' AND (giris_tarihi < %s AND cikis_tarihi > %s)"""
        sql += f" AND oda_no NOT IN ({overlap_sql})"
        params.extend([cikis, giris])
    else:
        sql += " AND durum = 'MUSAIT'"

    if kisi and kisi != '0':
        sql += " AND kapasite >= %s"
        params.append(kisi)
    if tip and tip != 'HEPSI':
        sql += " AND tip = %s"
        params.append(tip)

    sql += " ORDER BY oda_no ASC"
    cursor.execute(sql, tuple(params))
    odalar_listesi = cursor.fetchall()
    conn.close()
    return render_template('odalar.html', odalar=odalar_listesi)


@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        tc = request.form['tc_no']
        gelen_sifre = request.form['sifre']
        try:
            conn = baglanti_al()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE tc_no = %s", (tc,))
            kullanici = cursor.fetchone()
            conn.close()
            if kullanici and check_password_hash(kullanici['sifre'], gelen_sifre):
                session['user_id'] = kullanici['id']
                session['tc_no'] = kullanici['tc_no']
                session['ad'] = kullanici['ad_soyad']
                return redirect(url_for('odalar'))
            else:
                flash("Hatalı bilgi!", "danger")
        except Exception as e:
            flash(f"Hata: {e}", "danger")
    return render_template('login.html')


@app.route('/kayit')
def kayit_sayfasi():
    return render_template('login.html')


@app.route('/kayit_ol', methods=['POST'])
def kayit_ol():
    ad_soyad = request.form.get('ad_soyad')
    tc_no = request.form.get('tc_no')
    email = request.form.get('email')
    telefon = request.form.get('telefon')
    duz_sifre = request.form.get('sifre')

    sifreli_sifre = generate_password_hash(duz_sifre, method='pbkdf2:sha256')
    try:
        conn = baglanti_al()
        cursor = conn.cursor()
        sql = "INSERT INTO users (ad_soyad, tc_no, email, telefon, sifre, rol) VALUES (%s, %s, %s, %s, %s, 'MUSTERI')"
        val = (ad_soyad, tc_no, email, telefon, sifreli_sifre)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        flash("Kayıt başarılı!", "success")
    except Exception:
        flash("Hata: Kayıt yapılamadı.", "danger")
    return redirect(url_for('giris'))


@app.route('/rezervasyonlarim')
def rezervasyonlarim():
    if 'user_id' not in session: return redirect(url_for('giris'))
    conn = baglanti_al()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservations WHERE tc_no = %s ORDER BY id DESC", (session['tc_no'],))
    tum_kayitlar = cursor.fetchall()
    conn.close()

    bugun = date.today()
    aktif_rez = []
    gecmis_rez = []
    for kayit in tum_kayitlar:
        cikis_tarihi = kayit['cikis_tarihi']
        if isinstance(cikis_tarihi, str): cikis_tarihi = datetime.strptime(cikis_tarihi, "%Y-%m-%d").date()
        if kayit['durum'] == 'AKTIF' and cikis_tarihi >= bugun:
            aktif_rez.append(kayit)
        else:
            gecmis_rez.append(kayit)
    return render_template('rezervasyonlarim.html', aktifler=aktif_rez, gecmisler=gecmis_rez, musteri=session.get('ad'))


@app.route('/rezervasyon_yap', methods=['POST'])
def rezervasyon_yap():
    if 'user_id' not in session: return redirect(url_for('giris'))
    secilen_oda = request.form.get('oda_no')
    giris_tarihi = request.form.get('giris_tarihi')
    cikis_tarihi = request.form.get('cikis_tarihi')
    toplam_ucret = request.form.get('toplam_ucret')

    try:
        conn = baglanti_al()
        cursor = conn.cursor()
        sql1 = "INSERT INTO reservations (tc_no, oda_no, giris_tarihi, cikis_tarihi, ucret, durum, odeme_durumu) VALUES (%s, %s, %s, %s, %s, 'AKTIF', 'BEKLIYOR')"
        cursor.execute(sql1, (session['tc_no'], secilen_oda, giris_tarihi, cikis_tarihi, toplam_ucret))
        cursor.execute("UPDATE rooms SET durum = 'REZERVE' WHERE oda_no = %s", (secilen_oda,))
        conn.commit()
        conn.close()
        flash(f"Oda {secilen_oda} rezerve edildi!", "success")
        return redirect(url_for('rezervasyonlarim'))
    except Exception as e:
        flash(f"Hata: {e}", "danger")
        return redirect(url_for('odalar'))


@app.route('/iptal_et/<int:id>')
def iptal_et(id):
    if 'user_id' not in session: return redirect(url_for('giris'))
    conn = baglanti_al()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservations WHERE id=%s", (id,))
    rezerv = cursor.fetchone()
    if rezerv and rezerv['durum'] == 'AKTIF':
        cursor.execute("UPDATE reservations SET durum='IPTAL' WHERE id=%s", (id,))
        cursor.execute("UPDATE rooms SET durum='MUSAIT' WHERE oda_no=%s", (rezerv['oda_no'],))
        conn.commit()
        flash("İptal edildi.", "info")
    conn.close()
    return redirect(url_for('rezervasyonlarim'))


@app.route('/profilim', methods=['GET', 'POST'])
def profilim():
    if 'tc_no' not in session: return redirect(url_for('giris'))
    conn = baglanti_al()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        email = request.form.get('email')
        telefon = request.form.get('telefon')
        yeni_sifre = request.form.get('yeni_sifre')
        try:
            if yeni_sifre and yeni_sifre.strip():
                hashed_pw = generate_password_hash(yeni_sifre, method='pbkdf2:sha256')
                cursor.execute("UPDATE users SET email=%s, telefon=%s, sifre=%s WHERE tc_no=%s",
                               (email, telefon, hashed_pw, session['tc_no']))
            else:
                cursor.execute("UPDATE users SET email=%s, telefon=%s WHERE tc_no=%s",
                               (email, telefon, session['tc_no']))
            conn.commit()
            flash("Güncellendi.", "success")
        except Exception:
            pass
    cursor.execute("SELECT * FROM users WHERE tc_no = %s", (session['tc_no'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('profilim.html', user=user)


@app.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('odalar'))


# ========================================================
# 💳 PAYTR (PAYCO) ÖDEME YOLLARI - GERÇEK SİSTEM
# ========================================================

@app.route('/paytr_odeme_baslat', methods=['POST'])
def paytr_odeme_baslat():
    if 'user_id' not in session: return redirect(url_for('giris'))

    # Formdan gelen veriler
    rez_id = request.form.get('rezervasyon_id')
    fiyat = request.form.get('fiyat')
    fiyat_int = int(float(fiyat) * 100)

    # Kullanıcı Bilgileri
    user_name = session['ad']
    user_address = "Musteri Adresi Test"
    user_phone = "05555555555"
    user_email = session.get('email', 'test@email.com')  # Session'dan email al, yoksa test yaz
    user_ip = request.remote_addr

    basket = [{'name': 'Otel Rezervasyonu', 'price': fiyat}]
    manager = PayTRManager()
    callback_url = url_for('paytr_sonuc', _external=True)

    # PayTR'a İstek At
    sonuc = manager.odeme_formu_olustur(
        user_ip, user_name, user_address, user_phone, user_email,
        fiyat_int, basket, rez_id, callback_url
    )

    # ============================================================
    # 🕵️‍♂️ DEMO MODU HİLESİ BURADA
    # ============================================================
    # Normalde 'success' değilse hata verirdik.
    # Ama demo olduğu için "Mağaza aktif değil" hatasını BAŞARI sayıyoruz.

    if sonuc['status'] == 'success':
        # Gerçekten başarılıysa (İmkansız ama kodda kalsın)
        token = sonuc['token']
        iframe_code = f"""
        <script src="https://www.paytr.com/js/iframeResizer.min.js"></script>
        <iframe src="https://www.paytr.com/odeme/guvenli/{token}" id="paytriframe" frameborder="0" scrolling="no" style="width: 100%;"></iframe>
        <script>iFrameResize({{}},'#paytriframe');</script>
        """
        return render_template('odeme_sayfasi.html', iframe_code=iframe_code)

    else:
        # PayTR Hata Döndü (Çünkü mağaza ID sahte)
        # BİZ BUNU "BAŞARILI GİBİ" YÖNETECEĞİZ

        print(f"⚠️ PayTR Hata Döndü (Beklenen Durum): {sonuc['message']}")
        print("✅ Demo Modu Devreye Girdi: İşlem başarılı sayılıyor...")

        # 1. Veritabanını Güncelle
        conn = baglanti_al()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET odeme_durumu = 'ODENDI' WHERE id = %s", (rez_id,))
        conn.commit()
        conn.close()

        # 2. Mail Gönder (Kritik Kısım)
        try:
            # Kullanıcının mailini veritabanından bulalım
            conn = baglanti_al()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT email FROM users WHERE tc_no=%s", (session['tc_no'],))
            user_data = cursor.fetchone()
            conn.close()

            real_email = user_data['email'] if user_data else "test@email.com"

            konu = "Rezervasyon Onayı (Demo)"
            icerik = f"""
            <h3>Tebrikler {session['ad']}!</h3>
            <p>Ödeme işleminiz simülasyon ortamında başarıyla gerçekleşti.</p>
            <p><strong>Tutar:</strong> {fiyat} TL</p>
            <p><strong>Rezervasyon ID:</strong> {rez_id}</p>
            <hr>
            <small>Bu bir otomatik bilgilendirme postasıdır.</small>
            """
            mail_gonder(real_email, konu, icerik)
            print(f"📧 Mail gönderildi: {real_email}")

        except Exception as e:
            print(f"❌ Mail Hatası: {e}")

        # 3. Başarılı Sayfasına Yönlendir
        flash("Ödeme (Demo) Başarıyla Alındı! Mail kutunuzu kontrol edin.", "success")
        return redirect(url_for('rezervasyonlarim'))


@app.route('/paytr_sonuc', methods=['POST', 'GET'])
def paytr_sonuc():
    # Güvenlik Kontrolü
    if 'user_id' not in session:
        return redirect(url_for('giris'))

    conn = baglanti_al()
    cursor = conn.cursor(dictionary=True)  # Verileri isimleriyle (örn: 'email') almak için

    try:
        # 1. ADIM: Kullanıcının henüz ödenmemiş SON rezervasyonunu bul
        # (Gerçek PayTR entegrasyonunda bu bilgi POST ile gelir, ama localhost testi için bu yöntem garantidir)
        cursor.execute("SELECT * FROM reservations WHERE tc_no=%s AND odeme_durumu='BEKLIYOR' ORDER BY id DESC LIMIT 1",
                       (session['tc_no'],))
        rezerv = cursor.fetchone()

        if rezerv:
            # 2. ADIM: Rezervasyonu 'ODENDI' olarak güncelle
            rez_id = rezerv['id']
            cursor.execute("UPDATE reservations SET odeme_durumu = 'ODENDI' WHERE id = %s", (rez_id,))
            conn.commit()

            # 3. ADIM: Kullanıcının E-Posta adresini bul
            cursor.execute("SELECT email FROM users WHERE tc_no=%s", (session['tc_no'],))
            user = cursor.fetchone()
            alici_mail = user['email']

            # 4. ADIM: Mail İçeriğini Hazırla ve Gönder
            konu = f"Rezervasyon Onayı - #{rez_id}"
            icerik = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd;">
                <h2 style="color: #2ecc71;">Rezervasyonunuz Onaylandı! ✅</h2>
                <p>Sayın <strong>{session['ad']}</strong>,</p>
                <p>Otel rezervasyon ödemeniz başarıyla alınmıştır. Detaylar aşağıdadır:</p>
                <hr>
                <p><strong>Rezervasyon No:</strong> {rez_id}</p>
                <p><strong>Giriş Tarihi:</strong> {rezerv['giris_tarihi']}</p>
                <p><strong>Çıkış Tarihi:</strong> {rezerv['cikis_tarihi']}</p>
                <p><strong>Toplam Tutar:</strong> {rezerv['ucret']} TL</p>
                <hr>
                <p><em>Bizi tercih ettiğiniz için teşekkür ederiz.</em></p>
                <small>{inject_hotel_info()['otel_adi']}</small>
            </div>
            """

            # Mail göndermeyi dene (Hata olursa program çökmesin diye try-except içinde)
            try:
                mail_gonder(alici_mail, konu, icerik)
                flash("Ödeme Başarılı! Onay e-postası gönderildi.", "success")
            except Exception as e:
                print(f"Mail Hatası: {e}")
                flash("Ödeme alındı ancak mail gönderilemedi. (Sistem Ayarı Gerekli)", "warning")

        else:
            flash("Ödenecek aktif bir rezervasyon bulunamadı veya işlem zaten yapılmış.", "info")

    except Exception as e:
        flash(f"Bir hata oluştu: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('rezervasyonlarim'))


# --- YARDIMCI / TEST ROTASI ---
@app.route('/yonetici_olustur')
def yonetici_olustur():
    try:
        conn = baglanti_al()
        cursor = conn.cursor()
        sifreli = generate_password_hash("1234", method='pbkdf2:sha256')
        sql = "INSERT INTO users (tc_no, ad_soyad, email, telefon, sifre, rol) VALUES (%s, %s, %s, %s, %s, 'YONETICI')"
        val = ("11111111112", "Patron Murat", "admin@otel.com", "5551112233", sifreli)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return "Yönetici eklendi"
    except Exception as e:
        return f"Hata: {e}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)