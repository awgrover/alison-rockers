/*
  need pull-downs, pin floats, then high for signal
  for pi
  GPIO.setup(port_or_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

  ffs: simultaneous inhibits both! w/in about 100ms
  rcvr d3 is A, d2 is B
    vt does go high on rcv
*/
#include "tired_of_serial.h"
const int data_0 = A0;
const int data_ct = 4;


void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  // header
  for (int i = data_0; i < data_0 + data_ct; i++) {
    // pinMode(i, INPUT);
    // twice, baseline & actual
    print("d"); print(i - data_0); print(" ");
    print("d"); print(i - data_0); print(" ");
  }
  println();
}

void loop() {
  // put your main code here, to run repeatedly:
  for (int i = data_0; i < data_0 + data_ct; i++) {
    // print(digitalRead(i));print(" ");
    int v = analogRead(i);

    // light up if any
    digitalWrite(LED_BUILTIN, v > 100);

    print(  ((i - data_0) * 5)); print(" "); // baseline
    print(  ((i - data_0) * 5) + (v > 100 ? 2 : 0)); print(" "); // signal

  }
  println();
  delay(10);
}
