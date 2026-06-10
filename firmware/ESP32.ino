/*

* ESP32 Communication Gateway
* ---
* Course:
* Diseño de Sistemas en Chip
* March - June 2023
*
* Description:
* This firmware acts as the communication bridge between:
*
* * PyQt desktop application
* * Firebase Realtime Database
* * Arduino Mega (MBot controller)
* * Infrared remote controller
*
* Main responsibilities:
* 1. Receive movement commands from Firebase and forward them to the Arduino Mega through UART.
* 2. Receive multimedia commands from an IR remote and publish them to Firebase.
* 3. Receive sensor events from the MBot and publish them to Firebase.
* 4. Provide visual feedback through LEDs and buzzer.
*
*/



// ----------------------------------------------------------
// Infrared Remote Control
// ----------------------------------------------------------

#include <IRremote.h>

// IR receiver connected to GPIO 15
IRrecv irrecv(15);
decode_results results;

// Auxiliary variables used to build numeric commands
// entered through the IR remote.
int number = 0;

// Current and previous robot command states
String stateA = "";
String stateP = "";

// ----------------------------------------------------------
// Firebase and WiFi Libraries
// ----------------------------------------------------------

#include <Arduino.h>

#if defined(ESP32)
#include <WiFi.h>
#elif defined(ESP8266)
#include <ESP8266WiFi.h>
#endif

#include <Firebase_ESP_Client.h>

// Firebase helper utilities
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

// ----------------------------------------------------------
// Network Configuration
// ----------------------------------------------------------

#define WIFI_SSID "Vico"
#define WIFI_PASSWORD "facil#34"

// Firebase project configuration
#define API_KEY "AIzaSyBMHJxkLAUbJneLDtkdPXEZMq45TpXAdBE"//AIzaSyAjjTHMIV0y394tayvijhU-aVVcKdkIZxU
#define DATABASE_URL "https://sp32-5f852-default-rtdb.firebaseio.com"

// ----------------------------------------------------------
// Firebase Objects
// ----------------------------------------------------------

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long sendDataPrevMillis = 0;
bool signupOK = false;

// ----------------------------------------------------------
// System Initialization
// ----------------------------------------------------------


void setup() {

  // Enable infrared receiver
  irrecv.enableIRIn();

  // Serial monitor
  Serial.begin(9600);

  // UART channel used to communicate with the Arduino Mega
  Serial2.begin(9600); 
  
  // Status indicators   
  pinMode(4, OUTPUT);  // Buzzer 
  pinMode(19, OUTPUT); // Error LED
  pinMode(21, OUTPUT); // Success LED
  pinMode(22, OUTPUT); // WiFi LED
  pinMode(23, OUTPUT); // Firebase LED

  // --------------------------------------------------------
  // WiFi Connection
  // --------------------------------------------------------

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(22, HIGH);
    delay(250);
    digitalWrite(22, LOW);
    delay(250);
  }

  digitalWrite(22, HIGH);

  // --------------------------------------------------------
  // Firebase Configuration
  // --------------------------------------------------------

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  if (Firebase.signUp(&config, &auth, "", "")) {
    digitalWrite(23, HIGH);
    signupOK = true;
  }
  else {
    digitalWrite(19, HIGH);
  }

  config.token_status_callback = tokenStatusCallback; //see addons/TokenHelper.h

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}


// ----------------------------------------------------------
// Publish MP3 Control Commands
// ----------------------------------------------------------
// Commands are written to: test/mp3
// Typical values: Prev | Next | PP | Stop | <song_number>
//
// These commands are later consumed by the desktop application.
//

void sendDataBase(String instruction) {
  if (Firebase.ready() && signupOK && (millis() - sendDataPrevMillis > 1000 || sendDataPrevMillis == 0)) {
    sendDataPrevMillis = millis();
    if (Firebase.RTDB.setString(&fbdo, "test/mp3", instruction)) {
      // Use the buzzer to indicate the data has been sent to firebase
      digitalWrite(4, HIGH);
      delay(250);
      digitalWrite(4, LOW);
    }
    else {
      digitalWrite(4, HIGH);
      delay(1000);
      digitalWrite(4, LOW);

    }
  }
}

// ----------------------------------------------------------
// Visual Feedback Utilities
// ----------------------------------------------------------

void invalidData() {
  digitalWrite(19, HIGH);
  delay(500);
  digitalWrite(19, LOW);
}

void validData() {
  digitalWrite(21, HIGH);
  delay(500);
  digitalWrite(21, LOW);
}

// ----------------------------------------------------------
// Main Loop
// ----------------------------------------------------------

void loop() {

  // --------------------------------------------------------
  // Infrared Remote Processing
  // --------------------------------------------------------


  if (irrecv.decode(&results)) {

    irrecv.resume();
    
    // Previous song
    if ( results.value == 0xFEA25D) {
      validData();
      sendDataBase("Prev");
    }
    
    // Next song
    else if ( results.value == 0xFE22DD ) {
      validData();
      sendDataBase("Next");
    }
    
    // Play / Pause
    else if ( results.value == 0xFE52AD ) {
      validData();
      sendDataBase("PP");
    }

    // Stop playback 
    else if ( results.value == 0xFED22D ) {
      validData();
      sendDataBase("Stop");
    }

    // Numeric song selection 
    else if ( results.value == 0xFE00FF ) {
      number = number * 10 + 0;
      validData();
    } else if ( results.value == 0xFE807F ) {
      number = number * 10 + 1;
      validData();
    } else if ( results.value == 0xFE40BF ) {
      number = number * 10 + 2;
      validData();
    } else if ( results.value == 0xFEC03F ) {
      number = number * 10 + 3;
      validData();
    } else if ( results.value == 0xFE20DF ) {
      number = number * 10 + 4;
      validData();
    } else if ( results.value == 0xFEA05F ) {
      number = number * 10 + 5;
      validData();
    } else if ( results.value == 0xFE609F ) {
      number = number * 10 + 6;
      validData();
    } else if ( results.value == 0xFEE01F ) {
      number = number * 10 + 7;
      validData();
    } else if ( results.value == 0xFE10EF ) {
      number = number * 10 + 8;
      validData();
    } else if ( results.value == 0xFE906F ) {
      number = number * 10 + 9;
      validData();
    } 
    // Confirm numeric selection
    else if ( results.value == 0xFE08F7) {
      if (number > 0 and number <= 100) {
        String numberS = String(number);
        validData();
        sendDataBase(numberS);
        number = 0;
      }
      else {
        number = 0;
        invalidData();
      }
    } else if (results.value = 0xFFFFFFFF) {
      number = number;
    } else {
      invalidData();
    }
  }

  // --------------------------------------------------------
  // Firebase -> Arduino Mega Command Forwarding
  // --------------------------------------------------------
  //
  // Reads movement commands from test/dir and forwards them through UART.
  //

  if (Firebase.RTDB.getString(&fbdo, "test/dir")) {
    if (fbdo.dataType() == "string") {
      String stateA = fbdo.stringData();
      if (stateA != stateP) {
        Serial.print(stateA);
      }
      stateP = stateA;
    }
  }

  // --------------------------------------------------------
  // Arduino Mega -> Firebase Sensor Reporting
  // --------------------------------------------------------
  //
  // Receives sensor events through UART and publishes
  // them to: test/sensor
  //

  if (Serial2.available()) {
    int sensor = Serial2.read();
    if (Firebase.ready() && signupOK && (millis() - sendDataPrevMillis > 1000 || sendDataPrevMillis == 0)) {
      sendDataPrevMillis = millis();
      // Write an Int number on the database path test/int
      if (Firebase.RTDB.setInt(&fbdo, "test/sensor", sensor)) {
      // Use the buzzer to indicate the data was sent. 
      }
    }
  }
}
