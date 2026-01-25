//stream.h
#include "esp_http_server.h"
#include <WiFi.h>
#include "globals.h"

#define PART_BOUNDARY "123456789000000000000987654321"

static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t stream_httpd = NULL;


// ===================
// DANE SIECI WIFI
// ===================
const char* ssid = "PIGS IN SPACE";
const char* password = "krokodyl.2006";


// === KONFIGURACJA FPS ===
#define LIMIT_FPS 2 // Celujemy w 2 klatki na sekundę
// ========================

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) {
    return res;
  }

  int64_t last_frame = 0;
  if(!last_frame) {
    last_frame = esp_timer_get_time();
  }

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
    } else {
      if (fb->format != PIXFORMAT_JPEG) {
        bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
        esp_camera_fb_return(fb);
        fb = NULL;
        if (!jpeg_converted) {
          Serial.println("JPEG compression failed");
          res = ESP_FAIL;
        }
      } else {
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
      }
    }
    if (res == ESP_OK) {
      size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
    }
    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }
    if (res != ESP_OK) {
      break;
    }

    // === PRECYZYJNE OGRANICZENIE FPS (2 FPS) ===
    int64_t fr_end = esp_timer_get_time();
    int64_t frame_duration = fr_end - last_frame;
    last_frame = fr_end;
    
    // Dla 2 FPS interwał to 500ms = 500000us
    int64_t target_interval_us = 1000000 / LIMIT_FPS; 

    if(frame_duration < target_interval_us) {
        int64_t sleep_time_ms = (target_interval_us - frame_duration) / 1000;
        // Jeśli mamy zapas czasu, usypiamy wątek kamery.
        // Dzięki temu inne wątki (WiFi, loop) mają mnóstwo czasu dla siebie.
        if(sleep_time_ms > 0) {
            vTaskDelay(sleep_time_ms / portTICK_PERIOD_MS); 
        }
    }
  }
  return res;
}

static esp_err_t control_handler(httpd_req_t *req) {
    char buf[32];
    if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {
        char param[16];
        if (httpd_query_key_value(buf, "power", param, sizeof(param)) == ESP_OK) {
            if (strcmp(param, "on") == 0) {
                ledMode = 1; // Tryb Ręczny ON
                //digitalWrite(PIN_LED, HIGH);
            } else if (strcmp(param, "off") == 0) {
                ledMode = 2; // Tryb Ręczny OFF
                //digitalWrite(PIN_LED, LOW);
            } else if (strcmp(param, "auto") == 0) {
                ledMode = 0; // Powrót do automatu
            }
            return httpd_resp_send(req, "OK", 2);
        }
    }

    // Dodajemy trzeci przycisk "AUTO" w HTML
    const char* resp_str = 
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "  body { font-family: sans-serif; text-align: center; background: #1a1a1a; color: white; }"
        "  .btn { padding: 15px; width: 120px; font-size: 16px; margin: 5px; cursor: pointer; border: none; border-radius: 5px; }"
        "  .on { background: #2ecc71; color: white; }"
        "  .off { background: #e74c3c; color: white; }"
        "  .auto { background: #3498db; color: white; }"
        "</style>"
        "<script>function toggle(s) { fetch('/control?power=' + s); }</script>"
        "</head><body>"
        "<h1>Sterowanie LED</h1>"
        "<button class='btn on' onclick=\"toggle('on')\">ON</button>"
        "<button class='btn off' onclick=\"toggle('off')\">OFF</button>"
        "<button class='btn auto' onclick=\"toggle('auto')\">AUTO</button>"
        "<p><a href='/' style='color:#aaa'>Podgląd Kamery</a></p>"
        "</body></html>";

    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, resp_str, strlen(resp_str));
}

static esp_err_t dzikcount_handler(httpd_req_t *req) {
    char resp_str[1024];
    
    // Budujemy dynamiczny kod HTML z aktualną wartością dzikCounter
    // Dodajemy <meta http-equiv='refresh' content='2'>, aby strona sama odświeżała się co 2 sekundy
    snprintf(resp_str, sizeof(resp_str), 
        "<html><head><meta charset='utf-8'>"
        "<meta http-equiv='refresh' content='2'>" 
        "<style>body{font-family:sans-serif; text-align:center; background:#1a1a1a; color:#f1c40f; padding-top:50px;}"
        "h1{font-size:50px;} .count{font-size:100px; color:white;}</style></head>"
        "<body><h1>Liczba wykrytych dzików:</h1>"
        "<div class='count'>%d</div>"
        "<p><a href='/control' style='color:#aaa'>Panel sterowania</a></p>"
        "</body></html>", 
        dzikCount);

    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, resp_str, strlen(resp_str));
}

void startServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  config.max_open_sockets = 7; 
  config.lru_purge_enable = true;

  httpd_uri_t stream_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t control_uri = {
    .uri       = "/control",
    .method    = HTTP_GET,
    .handler   = control_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t dzikcount_uri = { 
    .uri = "/dzikcount", 
    .method = HTTP_GET, 
    .handler = dzikcount_handler, 
    .user_ctx = NULL 
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    httpd_register_uri_handler(stream_httpd, &control_uri);
    httpd_register_uri_handler(stream_httpd, &dzikcount_uri);
  }
}
