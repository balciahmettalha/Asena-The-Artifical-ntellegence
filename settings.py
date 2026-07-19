{
  "openapi": "3.0.3",
  "info": {
    "title": "ASENA Yerel API",
    "version": "1.0.0",
    "description": "ASENA Bilişsel İşletim Sistemi yerel JSON API'si. Sunucu yalnızca kullanıcı başlattığında açılır; sistem kendiliğinden ağ dinlemez (onay ilkesi).",
    "license": { "name": "MIT" }
  },
  "servers": [
    { "url": "http://127.0.0.1:8765", "description": "Yerel sunucu" }
  ],
  "paths": {
    "/sohbet": {
      "post": {
        "summary": "Sohbet döngüsünü çalıştır",
        "operationId": "sohbet",
        "tags": ["sohbet"],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/SohbetIstek" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Bilişsel döngünün ürettiği yanıt",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SohbetYanit" }
              }
            }
          }
        }
      }
    },
    "/kismi": {
      "post": {
        "summary": "Kısmi girdiyi ön-işleme gönder",
        "operationId": "kismi",
        "description": "Öngörülü düşünme: kullanıcı yazarken kısmi metni ön-işleme kuyruğuna alır.",
        "tags": ["sohbet"],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/SohbetIstek" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Ön-işlem durumu",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/DurumMesaj" }
              }
            }
          }
        }
      }
    },
    "/egitim": {
      "post": {
        "summary": "Eğitim modunu çalıştır",
        "operationId": "egitim",
        "description": "Verilen dosya veya dizindeki Türkçe metinlerden kelime ve ilişki öğrenir.",
        "tags": ["egitim"],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/EgitimIstek" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Eğitim raporu",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/EgitimYanit" }
              }
            }
          }
        }
      }
    },
    "/durum": {
      "get": {
        "summary": "Sistem durumunu bildir",
        "operationId": "durum",
        "tags": ["sistem"],
        "responses": {
          "200": {
            "description": "Sürüm, motor ve bellek durumu",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SistemDurum" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "SohbetIstek": {
        "type": "object",
        "required": ["metin"],
        "properties": {
          "metin": { "type": "string", "example": "Su nedir?" }
        }
      },
      "SohbetYanit": {
        "type": "object",
        "properties": {
          "yanit": { "type": "string" },
          "guven": { "type": "number", "format": "float", "minimum": 0, "maximum": 1 },
          "niyet": { "type": "string", "example": "tanim_sorusu" },
          "iz": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Bilişsel döngünün adım adım izi"
          }
        }
      },
      "DurumMesaj": {
        "type": "object",
        "properties": {
          "durum": { "type": "string", "example": "ön-işlem başlatıldı" }
        }
      },
      "EgitimIstek": {
        "type": "object",
        "required": ["kaynak"],
        "properties": {
          "kaynak": {
            "type": "string",
            "description": "Metin dosyası veya dizin yolu",
            "example": "veri/korpus"
          }
        }
      },
      "EgitimYanit": {
        "type": "object",
        "properties": {
          "dosya": { "type": "integer" },
          "cumle": { "type": "integer" },
          "yeni_kelime": { "type": "integer" },
          "yeni_iliski": { "type": "integer" },
          "hatalar": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      },
      "SistemDurum": {
        "type": "object",
        "properties": {
          "surum": { "type": "string" },
          "motor_sayisi": { "type": "integer" },
          "motorlar": {
            "type": "array",
            "items": { "type": "string" }
          },
          "bilgi_sayisi": { "type": "integer" },
          "yetkiler": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
