/*
  Designed for itsy bitsy 32u4
  "AVR109 compatible (same as Flora, Feather 32u4, Leonardo, etc)"

  sleep till: switch or watchdog
  while switch is on:
    send a pulse sequence out (to driver transistor)
  Because a second xmitter is blocked if it overlaps,
    we need 2 patterns that can't always overlap:
  The SL-jumper (ao->gnd) designates short-gap (open), long-gap (closed).
  Correspondance to "A" or "B" is not required at all:
    that is encoded in the hard-wired keyfob.

  std programmer: AVRISP mkii
  If the BUILTIN is throbbing, then you are in bootloader mode:
  (press reset to get into bootloader mode)
  You have about 2 seconds to hit upload,
  so hit reset again if you miss it.

  todo: sleep, power reduction
  test w/better power supply
*/

// lib: Streaming Mikal Hart <mikal@arduiniana.org>
#include <Streaming.h>
#include "every.h"

#define StandAlone 1 // "installation mode": no serial, power down everything

// Pins
// LED_BUILTIN is 13 on itsybitsy 32u4
const int Switch = 12; // we'll want a pcint pin...
const int Pulse = 7; // just digital-out
const int SLJumper = A0; // open is A, closed is B

// Pulse Pattern
const int TotalPatternLength = 4 * 1000; // 4 seconds
const int OnTime = 200; // minimum reliable
// leave an OnTime gap for the other to fit in
// ----____----___...
const int SShortTime = OnTime + 20;
// The second on has to miss A's:
// ----________----___...
const int LShortTime = SShortTime + OnTime + 20;

char Which = '?'; // to be filled in
int ShortGap = 0; // to be filled in based on jumper
int EndGap = 0; // to be filled in based on jumper

void setup() {

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  pinMode(Switch, INPUT_PULLUP);
  pinMode(SLJumper, INPUT_PULLUP);

  pinMode(Pulse, OUTPUT);
  digitalWrite(Pulse, LOW);

  // disables serial output when standalone
  if (! StandAlone) {
    // NB: (Serial) will always be false if USB-data is not connected
    // on 32u4's like itsy-bitsy
    Timer serial_timeout(4 * 1000);
    Serial.begin(115200); while (!Serial && !serial_timeout()) {}
  }
  Serial << "Start\n";

  if (OnTime * 2 + LShortTime > TotalPatternLength) {
    Serial << "Fail: pattern with LShortTime ("
           << (OnTime * 2 + LShortTime)
           << ") is longer than TotalPatternLength("
           << TotalPatternLength
           << ")\n";
  }

  // Short|Long gap
  // FIXME: signal which A|B somehow?
  if (digitalRead(SLJumper)) {
    // high is open, so A
    Which = 'S';
    ShortGap = SShortTime;
    Serial << "Short Gap\n";

  }
  else {
    Which = 'L';
    ShortGap = LShortTime;
    Serial << "Long Gap\n";
  }

  EndGap = TotalPatternLength - (OnTime * 2 + LShortTime);

  Serial << "Pattern: " << Which << "\n"
         << "-" << OnTime << "- "
         << "_" << ShortGap << "_ "
         << "-" << OnTime << "- "
         << "_" << EndGap << "_"
         << "\n";

  // give a clue that we are powered-on: blink a bit
  digitalWrite(LED_BUILTIN, HIGH);
  for (int i = 0; i < 10; i++) {
    delay(200);
    digitalWrite(LED_BUILTIN, ! digitalRead(LED_BUILTIN));
    // in stand-alone, I usually have an LED instead of the transmitter
    // so I like to see it flash:
    if (! StandAlone) digitalWrite( Pulse, ! digitalRead(Pulse) );
  }
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite( Pulse, LOW );
}

void loop() {
  // on power-up, will turn on Pulse for 1 "persistance":
  // initial persistance is short, reset to longer for real event below
  static Timer switch_persistance(100); // pretend to be on for at least a while
  static boolean switch_was_reset = 1;
  
  if ( ! digitalRead(Switch) ) {
    // high is open (pullup)
    if (! StandAlone) digitalWrite(LED_BUILTIN, HIGH);
    // but pretend to be on for 1 second more, which is not enough for a full pattern
    switch_persistance.reset(1 * 1000);
    //Serial << "ON\n";
  }
  else {
    // let the timer expire == off
    digitalWrite(LED_BUILTIN, LOW);
  }

  // if we are pretending switch is (still) on
  // i.e. timer hasn't expired

  if (switch_persistance.until()) {
    // signal if this is a new duration of the switch being down
    pulse_sequence(switch_was_reset);
    switch_was_reset = 0;
    // Serial << "Running " << (millis() - switch_persistance.last) << "\n";
  }
  else {
    //Serial << "OFF\n";
    switch_was_reset = 1;
    digitalWrite( Pulse, LOW );
  }

  delay(10); // FIXME: sleep
}

void pulse_sequence(boolean restart) {
  // on short-delay on long-delay
  enum State {S_On1, S_On1Hold, S_Short, S_On2, S_End};
  static State state = S_On1;

  static Timer On(OnTime);
  // we don't know the durations at compile time:
  static Timer short_off(0);
  static Timer long_off(0); // till end of PatternLength

  if (restart) {
    // so we can send out a pulse immediately
    state = S_On1;
  }

  switch (state) {
    case S_On1:
      // (re)Start
      On.reset();
      digitalWrite( Pulse, HIGH);
      state = S_On1Hold;
      Serial << state << " ";
    // fall through

    case S_On1Hold:
      // in the "ON" state for the 1st pulse
      if (On()) {
        state = S_Short;
        digitalWrite( Pulse, LOW );
        short_off.reset(ShortGap);
        Serial << state << " ";
      }
      break;

    case S_Short:
      if (short_off()) {
        state = S_On2;
        digitalWrite( Pulse, HIGH );
        On.reset();
        Serial << state << " ";
      }
      break;

    case S_On2:
      if (On()) {
        state = S_End;
        digitalWrite( Pulse, LOW );
        long_off.reset(EndGap);
        Serial << state << " ";
      }
      break;

    case S_End:
      if (long_off()) {
        state = S_On1;
        // that special state takes care of HIGH/reset
        Serial << state << "\n";
      }
      break;
  }
}
