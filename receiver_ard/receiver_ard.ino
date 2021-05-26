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
    pinMode(i, INPUT_PULLUP);
    // twice, baseline & actual
    Serial << "d" << (i - data_0) << " "; // baseline
    Serial << "d" << (i - data_0) << " "; // actual
  }
  Serial << "\n";
}

const int threshold = 1;
void loop() {
  loop_reliability();
}

// stats on detection
const int bins_ct_ct = 2 * 5 + 1; // 0..5..10
struct bins {
  unsigned long last_millis = 0;
  boolean low = 1; // to track rising edge
  unsigned long ct[bins_ct_ct];
};
bins detection[data_ct]; // should all be zero

void loop_reliability() {
  // 0:  0 146 9 138 64 0 0 0 1 0 0
  // 1: 146 6 1 153 60
  // + 69 in about 5 minutes
  
  boolean any = 0;
  static Every count_elapsed(30 * 1000, true);
  static float minutes = 0.0;


  for (int rf_pin = data_0; rf_pin < data_0 + data_ct; rf_pin++) {
    int rf_i = rf_pin - data_0; // 0...n
    int v = digitalRead(rf_pin);
    boolean hit = v >= threshold;

    if (hit) {
      if (count_elapsed()) {
        minutes = minutes + 0.5;
        int hours = int(minutes / 60.0);
        int minutes_part = int(minutes) % 60;
        Serial << "<< runtime " << hours << ":" << minutes_part << "\n";
      }

      if (detection[rf_i].low) {
        detection[rf_i].low = 0;

        int bin_number = int( (millis() - detection[rf_i].last_millis) / 1000) ;
        if (bin_number > bins_ct_ct - 1) bin_number = bins_ct_ct - 1;
        detection[rf_i].ct[ bin_number ] += 1;
        detection[rf_i].last_millis = millis();

        Serial << rf_i << ": ";
        for (int i = 0; i < bins_ct_ct; i++) {
          Serial << detection[rf_i].ct[i] << " ";
        }
        Serial << "\n";
      }
    }
    else {
      detection[rf_i].low = 1; // for next leading edge
    }
  }
  digitalWrite(LED_BUILTIN, any);
}

void loop_plot() {

  // print on/off indication for each channel
  boolean any = 0;
  static boolean already[data_ct] = {0, 0, 0, 0};
  static unsigned long last[data_ct] = {0, 0, 0, 0};

  any = 0;
  for (int i = data_0; i < data_0 + data_ct; i++) {
    int v = digitalRead(i);
    boolean hit = v >= threshold;

    Serial << v << "x ";

    Serial <<  ((i - data_0) * 5) << " "; // baseline
    Serial << (((i - data_0) * 5) + (hit ? -2 : 0)) << " "; // signal
    Serial << ((i - data_0) * 5) + (hit ? int((millis() - last[i]) / 1000) : 0) << " "; // delta since last

    if ( hit ) {
      any = 1;
      if ( ! already[i]) {
        already[i] = 1;
        last[i] = millis();
      }
      else {
        already[i] = 0;
      }
    }

  }

  // light up if any

  digitalWrite(LED_BUILTIN, any);
  Serial << "\n";
  delay(10);
}
