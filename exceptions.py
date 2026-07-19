# ASENA varsayılan yapılandırması
# Kullanıcı dosyası bu değerlerin üzerine birleştirilir (deep merge).

[sistem]
ad = "asena"
dil = "tr"
mod = "sohbet"            # sohbet | egitim

[bellek]
kisa_sureli_kapasite = 25      # çalışma belleğine alınan en çok öğe
dikkat_kapasitesi = 25         # attention system sınırı
cache_boyutu = 1024            # bellek önbelleği (öğe)
unutma_esigi = 0.05            # bu gücün altındaki anılar silinir
guclenme_miktari = 0.1         # her erişimde anı gücü artışı

[veritabani]
yol = "veri/asena.db"

[performans]
is_parcacigi = 4
cok_cekirdek = true
asenkron = true
gpu_etkin = false              # opsiyonel CUDA; varsa algılanır
predictive_etkin = true        # kullanıcı yazarken düşünme

[cikarim]
en_cok_hipotez = 5
en_cok_adim = 8                # reason engine çok adımlı akıl yürütme sınırı
guven_esigi = 0.4              # altındaki yanıtlar "emin değilim" ile işaretlenir

[ogrenme]
onem_esigi = 2                 # knowledge economy: altındaki bilgi ezberlenmez
gunluk_dizini = "veri/gunluk"

[egitim]
corpus_dizini = "veri/corpus"
parca_boyutu = 65536           # corpus okuma parçası (bayt)

[guvenlik]
onay_gerekli = ["internet", "dosya_yazma", "dosya_okuma_disi", "kod_calistirma", "sistem_cagrisi", "egitim_verisi"]
