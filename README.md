🏨 Otel Rezervasyon ve Yönetim Sistemi (Hibrit Mimari)
Bu proje, masaüstü ve web platformlarının eş zamanlı (real-time) çalıştığı, bulut tabanlı dağıtık bir otel yönetim sistemidir.

Resepsiyon tarafı güçlü ve hızlı bir JavaFX masaüstü uygulaması ile yönetilirken, Müşteriler Python/Flask ile yazılmış Web Arayüzü üzerinden odaları görüntüleyip rezervasyon durumlarını takip edebilirler. Her iki sistem de Ortak Bulut Veritabanı üzerinden haberleşir.

🔗 Canlı Demo (Web): https://otelweb.onrender.com

🚀 Proje Mimarisi ve Çalışma Mantığı
Bu proje, tek bir veritabanına bağlı iki farklı uçtan oluşur:

Masaüstü (Admin/Personel): Java ve JavaFX ile geliştirilmiştir. Resepsiyon görevlileri oda satışı, check-in/check-out ve müşteri takibi işlemlerini buradan yapar.

Web (Müşteri): Python ve Flask ile geliştirilmiştir. Müşteriler internet üzerinden otelin doluluk durumunu anlık olarak görür.

Veritabanı (Ortak Beyin): Bulut sunucuda barınan MySQL veritabanı, iki uygulamanın saniyesi saniyesine senkronize olmasını sağlar.


📸 Ekran Görüntüleri
Masaüstü Uygulaması (JavaFX)
<img width="1917" height="1033" alt="image" src="https://github.com/user-attachments/assets/3164250a-b15f-4064-b443-6008b230762d" />

Web Arayüzü (Python/Flask)
<img width="1919" height="1029" alt="image" src="https://github.com/user-attachments/assets/d5618f11-b58b-4156-845b-b86969626247" />

🛠️ Kullanılan Teknolojiler
Masaüstü Tarafı (Back-Office)
Dil: Java 17+

Arayüz: JavaFX

Veritabanı Bağlantısı: JDBC / MySQL Connector

Özellikler: Dinamik grafikler, oda yönetimi, müşteri veritabanı.

Web Tarafı (Front-Office)
Dil: Python 3.10+

Framework: Flask

ORM: SQLAlchemy

Sunucu: Gunicorn

Hosting: Render.com

Veritabanı
Tip: MySQL (Cloud Hosting)

Yapı: İlişkisel Veritabanı (Relational DB)



👨‍💻 Geliştirici
[Murat Aydoğan] Java & Python Developer

[https://www.linkedin.com/in/murat-aydo%C4%9Fan-51587b298/]
