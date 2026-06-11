# Firmware

This directory contains the embedded software used by the MBot control system.

## Files

### ESP32.ino

Firmware intended to run on the ESP32 communication module.

Responsibilities:

- Connect to the local WiFi network.
- Communicate with Firebase Realtime Database.
- Receive movement commands from Firebase.
- Forward commands to the Arduino Mega through UART.
- Receive commands from an infrared remote controller.
- Publish multimedia control events to Firebase.
- Receive sensor events from the robot and publish them to Firebase.

This file should be uploaded to the ESP32 board.

---

### MBOTFreeRTOS.ino

Firmware intended to run on the Arduino Mega installed on the MBot platform.

Responsibilities:

- Receive movement commands from the ESP32.
- Control robot motion.
- Monitor onboard sensors.
- Report sensor events back to the ESP32.
- Execute concurrent tasks using FreeRTOS.

This file should be uploaded to the Arduino Mega.# Firmware

This directory contains the embedded software used by the MBot control system.
