//slopek.ino
#include "esp_timer.h"
#include "soc/soc.h" 
#include "soc/rtc_cntl_reg.h"


#include "oled.h"
#include "camera.h"
#include "stream.h"
#include "globals.h"

// 0 = Auto (czujnik), 1 = Zawsze ON, 2 = Zawsze OFF
int ledMode = 0;
int dzikCount = 0;

//#define BUTTON_SUB D1
//#define BUTTON_ADD D2

#define LASER D1
#define RESET D0

int treshold = 1800;
int treshold_high;
int treshold_low;

void setup() {
 // WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Wyłącz detektor Brownout
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_FOTO, INPUT);
  pinMode(LASER,OUTPUT);
  pinMode(RESET,INPUT_PULLUP);
  digitalWrite(LASER,HIGH);
  delay(500);
  treshold_high = analogRead(PIN_FOTO);
  delay(500);
  digitalWrite(LASER,LOW);
  delay(500);
  treshold_low = analogRead(PIN_FOTO);
  delay(500);
  digitalWrite(LASER,HIGH);
  
  treshold = treshold_high+(treshold_low-treshold_high)/2;

  Serial.begin(115200);
  
  // Małe zabezpieczenie na start monitora (opcjonalne)
  unsigned long startWait = millis();
  while(!Serial && (millis() - startWait < 3000)) { 
    delay(10); 
  }
  Wire.begin(D4, D5);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println("inicjalizacja \n kamery...");
    display.setCursor(0,40);
    display.println(treshold);
    display.display();


  //Serial.setDebugOutput(true);

  // Konfiguracja kamery - WYSOKA JAKOŚĆ
  esp_err_t err = initCamera();
  if (err != ESP_OK) {
    Serial.printf("Inicjalizacja kamery nieudana, błąd 0x%x", err);
    display.println("Inicjalizacja kamery nieudana");
    display.display();
    return ;
  }

  // --- Konfiguracja dodatków ---
  
  //pinMode(BUTTON_ADD,INPUT);
 // pinMode(BUTTON_SUB,INPUT);



  // Połączenie z WiFi
  display.setCursor(0,16);
  unsigned long connect_try = millis();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED && (millis()<(connect_try+10000))) {
    delay(1000);
    Serial.print(".");
    display.print(".");
    display.display();
  }

  if(WiFi.status() != WL_CONNECTED){
    Serial.println("brak połączenia WiFi");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("brak polaczenia WiFi");
    display.setCursor(0,40);
    display.println(treshold);
    display.display();
    return;
  }


  Serial.println("");
  Serial.println("WiFi połączone");

  display.println("WiFi połączone");
  display.display();

  // Start serwera
  startServer();

  // Start wyświetlacza
  
  display.clearDisplay();
  display.println("IP obrazu w sieci");
  display.println(ssid);
  display.println(WiFi.localIP()); 
  display.println(treshold); 
  display.display();


  Serial.print("Kamera gotowa! Użyj adresu: http://");
  Serial.print(WiFi.localIP());
}

bool ok=true;

void loop() {
  static unsigned long ledTimer = 0;
  unsigned long currentMillis = millis();

  //if (ledMode == 0) {
    //Serial.println(ledMode)

    // === TRYB AUTOMATYCZNY (Czujnik) ===
    int irStatus = analogRead(PIN_FOTO);

    if (irStatus < treshold || ledMode == 1) {
      digitalWrite(PIN_LED, HIGH); 
      ledTimer = currentMillis;
      ledMode = 2;
    } else {
      if (currentMillis - ledTimer >= 2000) {
        digitalWrite(PIN_LED, LOW); 
        //ledMode = 0;
      }
    }

  /*} else if (ledMode == 1) {
    // === TRYB RĘCZNY ON ===
    digitalWrite(PIN_LED, HIGH);
  } else if (ledMode == 2) {
    // === TRYB RĘCZNY OFF ===
    digitalWrite(PIN_LED, LOW);
  }*/

  if(digitalRead(PIN_LED)==1 && ok){dzikCount++; ok = false;}
  if(digitalRead(PIN_LED)==0) ok = true;

  if(digitalRead(RESET)==0)esp_restart();
  
 
  delay(10); 
}