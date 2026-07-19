-- ASENA SQLite şeması (sürüm 1)
-- Kalıcı bellek: kelimeler, kavramlar, bilgiler, ilişkiler, kurallar,
-- kanıtlar, konuşmalar ve öğrenme günlüğü.

CREATE TABLE IF NOT EXISTS meta (
    anahtar TEXT PRIMARY KEY,
    deger   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kelimeler (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    yazim         TEXT NOT NULL UNIQUE,      -- kelimenin göründüğü biçim
    kok           TEXT,                      -- kök analizi sonucu
    tur           TEXT,                      -- isim | fiil | sıfat | zarf | ...
    anlam         TEXT,                      -- birincil anlam
    onem          REAL NOT NULL DEFAULT 1.0, -- önem puanı (★ karşılığı)
    anlam_x       REAL DEFAULT 0.0,          -- anlam uzayı koordinatları
    anlam_y       REAL DEFAULT 0.0,
    anlam_z       REAL DEFAULT 0.0,
    erisim_sayisi INTEGER NOT NULL DEFAULT 0,
    olusturma     TEXT NOT NULL DEFAULT (datetime('now')),
    son_erisim    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kavramlar (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ad            TEXT NOT NULL UNIQUE,
    tanim         TEXT,
    ust_kavram_id INTEGER REFERENCES kavramlar(id) ON DELETE SET NULL,
    yogunluk      REAL NOT NULL DEFAULT 1.0, -- knowledge density gücü
    olusturma     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bilgiler (
    id          TEXT PRIMARY KEY,          -- KB-00000001 biçiminde evrensel kimlik
    ozne        TEXT NOT NULL,
    yuklem      TEXT NOT NULL,
    nesne       TEXT,
    onerme      TEXT NOT NULL,             -- doğal dil karşılığı
    guven       REAL NOT NULL DEFAULT 1.0,
    onem        REAL NOT NULL DEFAULT 1.0,
    surum       INTEGER NOT NULL DEFAULT 1,
    durum       TEXT NOT NULL DEFAULT 'aktif',  -- aktif | arsiv
    kaynak      TEXT,                      -- kullanici | egitim | cikarim
    olusturma   TEXT NOT NULL DEFAULT (datetime('now')),
    guncelleme  TEXT NOT NULL DEFAULT (datetime('now')),
    gecerlilik  TEXT                       -- zamanla değişen bilgi için dönem
);

CREATE INDEX IF NOT EXISTS ix_bilgiler_ozne ON bilgiler(ozne);
CREATE INDEX IF NOT EXISTS ix_bilgiler_yuklem ON bilgiler(yuklem);

CREATE TABLE IF NOT EXISTS iliskiler (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kaynak     TEXT NOT NULL,              -- düğüm adı (kelime/kavram/bilgi)
    hedef      TEXT NOT NULL,
    tur        TEXT NOT NULL,              -- es | ust_tur | alt_tur | sebep | sonuc | zit | ...
    agirlik    REAL NOT NULL DEFAULT 1.0,
    olusturma  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(kaynak, hedef, tur)
);

CREATE INDEX IF NOT EXISTS ix_iliskiler_kaynak ON iliskiler(kaynak);
CREATE INDEX IF NOT EXISTS ix_iliskiler_hedef ON iliskiler(hedef);

CREATE TABLE IF NOT EXISTS kurallar (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kosul      TEXT NOT NULL,              -- öncül önerme kalıbı
    sonuc      TEXT NOT NULL,              -- sonuç önerme kalıbı
    guven      REAL NOT NULL DEFAULT 1.0,
    olusturma  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kanitlar (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bilgi_id      TEXT NOT NULL REFERENCES bilgiler(id) ON DELETE CASCADE,
    kanit_metni   TEXT NOT NULL,
    kaynak        TEXT,
    zincir_sirasi INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS bilgi_surumleri (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    bilgi_id       TEXT NOT NULL,
    surum_no       INTEGER NOT NULL,
    icerik         TEXT NOT NULL,
    degisim_nedeni TEXT,
    zaman          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(bilgi_id, surum_no)
);

CREATE TABLE IF NOT EXISTS konusmalar (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mod        TEXT NOT NULL DEFAULT 'sohbet',
    baslangic  TEXT NOT NULL DEFAULT (datetime('now')),
    bitis      TEXT
);

CREATE TABLE IF NOT EXISTS mesajlar (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    konusma_id  INTEGER NOT NULL REFERENCES konusmalar(id) ON DELETE CASCADE,
    rol         TEXT NOT NULL,             -- kullanici | asena | sistem
    icerik      TEXT NOT NULL,
    zaman       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ogrenme_gunlugu (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih        TEXT NOT NULL,
    yeni_kelime  INTEGER NOT NULL DEFAULT 0,
    yeni_iliski  INTEGER NOT NULL DEFAULT 0,
    yeni_kural   INTEGER NOT NULL DEFAULT 0,
    yeni_kavram  INTEGER NOT NULL DEFAULT 0,
    notlar       TEXT,
    UNIQUE(tarih)
);
