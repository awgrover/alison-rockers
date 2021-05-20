/*
  For debugging the receiver module:
  Use Serial Plotter: 4 traces: 
  Simply monitors 4 pins for a positive signal,
  nb: receiver sends high-active.

  Hook module D0..D3 to arduino A0..A3
  
  need pull-downs, pin floats, then high for signal
  for pi
  GPIO.setup(port_or_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

  ffs: simultaneous inhibits both! w/in about 100ms
  rcvr d3 is A, d2 is B
    vt does go high on rcv
*/
// lib: Streaming Mikal Hart <mikal@arduiniana.org>
#include <Streaming.h>
const int data_0 = A0;
const int data_ct = 4;

#include "every.h"
Every blink(200);

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);

  // give a clue that we are powered-on: blink a bit
  digitalWrite(LED_BUILTIN, HIGH);
  for (int i = 0; i < 10; i++) {
    delay(200);
    digitalWrite(LED_BUILTIN, ! digitalRead(LED_BUILTIN));
  }
  // save power
  digitalWrite(LED_BUILTIN, LOW);
  
  // header
  for (int i = data_0; i < data_0 + data_ct; i++) {
    // pinMode(i, INPUT);
    // twice, baseline & actual
    Serial << "d" << (i - data_0) << " "; // baseline
    Serial << "d" << (i - data_0) << " "; // actual
  }
  Serial << "\n";
}

void loop() {
  // print on/off indication for each channel
  for (int i = data_0; i < data_0 + data_ct; i++) {
     int v = analogRead(i);
    Serial << v << "x ";

    // light up if any
    digitalWrite(LED_BUILTIN, v > 100);

    Serial <<  ((i - data_0) * 5) << " "; // baseline
    Serial << (((i - data_0) * 5) + (v > 100 ? 2 : 0)) << " "; // signal

  }
  Serial << "\n";
  delay(10);
}
