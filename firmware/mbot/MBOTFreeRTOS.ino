/*

* MBot Controller Firmware
*
* Academic Project - Diseño de Sistemas en Chip (2023)
*
* Description:
* Firmware running on the Arduino Mega responsible for:
*
* * Receiving movement commands from the ESP32 through UART.
* * Controlling the MBot motors using direct register access.
* * Monitoring obstacle and limit sensors.
* * Reporting sensor events back to the ESP32.
* * Coordinating robot actions using FreeRTOS tasks.
*
* Main Components:
* * FreeRTOS task scheduler
* * UART communication
* * Direct register-based motor control
* * Barrier sensor monitoring
* * Limit switch monitoring
*

*/


#include <Arduino_FreeRTOS.h>
#include "queue.h"


// -----------------------------------------------------------------------------
// FreeRTOS and UART Configuration
// -----------------------------------------------------------------------------
//
// Defines UART communication parameters used to exchange
// commands and sensor events with the ESP32.
//

#define F_CPU 16000000UL
#define USART_BAUDRATE 9600
#define UBRR_VALUE (((F_CPU / (USART_BAUDRATE * 16UL))) - 1)

// -----------------------------------------------------------------------------
// MBot Hardware Interfaces
// -----------------------------------------------------------------------------
//
// Barrier sensor and MegaPi hardware abstractions.
//

#include <Wire.h>
#include "src/MeBarrierSensor.h"
#include <MeMegaPi.h>
MeBarrierSensor barrier_61(61);

// -----------------------------------------------------------------------------
// Global Resources
// -----------------------------------------------------------------------------
//
// Shared resources used by FreeRTOS tasks.
//

unsigned char _buffer[35];
char sens, peeks;

QueueHandle_t FireBase;

// -----------------------------------------------------------------------------
// System Initialization
// -----------------------------------------------------------------------------
//
// Creates RTOS tasks, configures UART peripherals,
// initializes GPIO directions and motor outputs.
//

void setup()
{
  Serial.begin(19200);
  FireBase = xQueueCreate(1, sizeof(char *));
  xTaskCreate(moveBotForward, "Movimiento del MBot ", 100, NULL, 1, NULL );
  xTaskCreate(moveBotBackward, "Movimiento del MBot", 100, NULL, 1, NULL );
  xTaskCreate(moveBotRight, "Movimiento del MBot", 100, NULL, 1, NULL );
  xTaskCreate(moveBotLeft, "Movimiento del MBot", 100, NULL, 1, NULL );
  xTaskCreate(moveBotStop, "Movimiento del MBot", 100, NULL, 1, NULL );
  xTaskCreate(GateKeeperTask, "GateKeeper", 100, NULL, 0, NULL);
  xTaskCreate(vTaskSensorRead, "Sensores", 100, NULL, 1, NULL);

  // Serial Prot configuration 
  UBRR2H = (uint8_t)(UBRR_VALUE >> 8);
  UBRR2L = (uint8_t)UBRR_VALUE;
  UCSR2C = 0x06;       // Set frame format: 8data, 1stop bit
  UCSR2B |= (1 << RXEN2) | (1 << TXEN2);   // TX y RX habilitados

  UBRR3H = (uint8_t)(UBRR_VALUE >> 8);
  UBRR3L = (uint8_t)UBRR_VALUE;
  UCSR3C = 0x06;       // Set frame format: 8data, 1stop bit
  UCSR3B |= (1 << RXEN2) | (1 << TXEN2);   // TX y RX habilitados

  DDRK &= ~(1 << PK3);//crash
  
  set_pins();
}

// -----------------------------------------------------------------------------
// Motor Pin Configuration
// -----------------------------------------------------------------------------
//
// Configures motor control pins as outputs using
// direct register access.
//

void set_pins()
{
  /*La presente función no recibe ningún argumento */

  //Motor 1 -> E:11 , i1:33, i2:32
  //             B5      C4     C5
  //Motor 2 -> E:12 , i1:34, i2:35
  //             B6      C3     C2
  //Motor 3 -> E:7 ,  i1:40, i2:41
  //           H4      G1     G0
  //Motor 4 -> E:8 ,  i1:37, i2:36
  //             H5      C0     C1

  DDRB = 0x60; // PORT B -> 0110_0000

  DDRC = 0x3F; // PORT C -> 0011_1111

  DDRH = 0x30; // PORT H -> 0011_0000

  DDRG = 0x03;// PORT G -> 0000_0011
}


// -----------------------------------------------------------------------------
// Low-Level Motor Control
// -----------------------------------------------------------------------------
//
// Configures PWM timers and updates motor direction
// signals through direct port manipulation.
//

void move(int m1, int m2)
{
  OCR1A = 128;
  OCR1B = 128;
  OCR4B = 128;
  OCR4C = 128;

  TCCR1A = 0xA1; //PWM - 8bit
  TCCR1B = 0x0C; //6.25 x 256 x 256, inverso para tener 244hz

  TCCR4A = 0b00101001; //PWM - 8bit
  TCCR4B = 0x0C; //6.25 x 256 x 256, inverso para tener 244hz

  TCNT3H = 0xA4;
  TCNT3L = 0x72; //A472 hex= 42,098 ciclos para 1.5 seg

  TCCR3A = 0x00; //normal mode
  TCCR3B = 0x05; //Normal mode prescaler 1:1024. 24 millones/ 1024 = 23,437

  //while((TIFR3&(0x01<<TOV3))==0) //Esperar hasta que desborde el timer (delay)
  //{
  //C4(33):1, C0(37):1, C2(35):1, G0(41):1
  //C3(34):0, C5(32):0, C1(36):0, G1(40):1
  PORTC = m1;//PORT C -> xx010101
  PORTG = m2;//PORT G -> xxxxxx11
  //}
  TIFR3 = 0x01 << TOV1; //Baja la bandera de desborde
}

// -----------------------------------------------------------------------------
// Low-Level Motor Control
// -----------------------------------------------------------------------------
//
// Configures PWM timers and updates motor direction
// signals through direct port manipulation.
//

// Forward motion task 
void moveBotForward(void *pvParameters)
{
  char mensaje1;
  while (1)
  {
    xQueuePeek(FireBase, &mensaje1, portMAX_DELAY);
    if (mensaje1 == 'F') {
      move(0b00010101, 0b00000001);
      xQueueReceive(FireBase, &mensaje1, portMAX_DELAY);
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// Backward motion task 
void moveBotBackward(void *pvParameters)
{
  char mensaje1;
  while (1)
  {
    xQueuePeek(FireBase, &mensaje1, portMAX_DELAY);
    if (mensaje1 == 'B') {
      move(0b00101010, 0b00000010);
      xQueueReceive(FireBase, &mensaje1, portMAX_DELAY);
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// Right turn task 
void moveBotRight(void *pvParameters)
{
  char mensaje1;
  while (1)
  {
    xQueuePeek(FireBase, &mensaje1, portMAX_DELAY);
    if (mensaje1 == 'R') {
      move(0b00101001, 0b00000001);
      xQueueReceive(FireBase, &mensaje1, portMAX_DELAY);
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// Left turn task 
void moveBotLeft(void *pvParameters)
{
  char mensaje1;
  while (1)
  {
    xQueuePeek(FireBase, &mensaje1, portMAX_DELAY);
    if (mensaje1 == 'L') {
      move(0b00010110, 0b00000010);
      xQueueReceive(FireBase, &mensaje1, portMAX_DELAY);
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// Stop motion task 
void moveBotStop(void *pvParameters)
{
  char mensaje1;
  while (1)
  {
    xQueuePeek(FireBase, &mensaje1, portMAX_DELAY);
    if (mensaje1 == 'S') {
      move(0, 0);
      xQueueReceive(FireBase, &mensaje1, portMAX_DELAY);
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// -----------------------------------------------------------------------------
// Sensor Monitoring Task
// -----------------------------------------------------------------------------
//
// Periodically monitors:
//
// - Barrier sensor
// - Limit switch
//
// Sensor states are transmitted to the ESP32
// through UART.
//
// Reported codes:
//
// J -> Barrier + limit switch active
// O -> Barrier sensor active
// C -> Limit switch active
//
void vTaskSensorRead (void *pvParameters) {
  while(1){
    while (!(UCSR3A & (1 << UDRE3)));
      if (barrier_61.isBarried() and !(PINK & (1 << PK3))) {
        //sprintf(_buffer, "J");
        //USART2_Transmit_String((unsigned char *)_buffer);
        Serial.println("J");
        UDR3 = "J";
      }
      else if (barrier_61.isBarried()) {
        //sprintf(_buffer, "O");
        //USART2_Transmit_String((unsigned char *)_buffer);
        Serial.println("O");
        UDR3 = "O";
      }
      else if (!(PINK & (1 << PK3))) {
        //sprintf(_buffer, "C");
        //USART2_Transmit_String((unsigned char *)_buffer);
        Serial.println("C");
        UDR3 = "C";
      }
      vTaskDelay(pdMS_TO_TICKS(500));
    }
  }

// -----------------------------------------------------------------------------
// UART Command Dispatcher
// -----------------------------------------------------------------------------
//
// Receives movement commands from the ESP32 through
// UART and places them in the FreeRTOS queue for
// processing by the motion tasks.
//

void GateKeeperTask(void *pvParameters)
{
  char sr;
  char ch;
  while (1)
  {
    while (!(UCSR2A & (1 << RXC2)));
    ch = UDR2;
    xQueueSend(FireBase, &ch, portMAX_DELAY);
    Serial.println(ch);
  }
}

// -----------------------------------------------------------------------------
// Main Loop
// -----------------------------------------------------------------------------
//
// Not used.
// Execution is handled entirely by FreeRTOS tasks.
//

void loop() {}
