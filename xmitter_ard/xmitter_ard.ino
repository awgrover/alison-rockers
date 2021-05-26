/*
  Designed for itsy bitsy 32u4
  "AVR109 compatible (same as Flora, Feather 32u4, Leonardo, etc)"

  ### To load new program
  If we are power-down, probably won't work, so:
  Press reset button (once) on itsy-bitsy,
  wait for built-in LED
  then 
  
  
  
  
  upload immediately
  (startup takes significant time before we get to power-down).

  startup:
  ** fast flashing while waiting for serial
  ** slow flashing for about 1 second
  ** start with a short pulse
  ** run:

  On swtich close: if it has been > 1 sec since last switch close: restart pattern of pulses
  While switch close, run pulse-pattern
  continue the pulse-pattern for 1 second after the switch opens

  We deep-sleep:
    When the switch off (interrupt wakes us)
      (and we do a quick led pulse as heartbeat)
    When the Pulse pattern has an interval > 1second

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
*/

// lib: Streaming Mikal Hart <mikal@arduiniana.org>
#include "Streaming.h"
// lib:  LowPower by PowerLab
#include "LowPower.h"
#include "every.h"

#define StandAlone 1 // "installation mode": no serial

// Pins
// LED_BUILTIN is 13 on itsybitsy 32u4
const int Switch = 7; // we want a interrupt pin (0,1,2,3,7)
const int SwitchInterrupt = digitalPinToInterrupt(Switch);
volatile  boolean SwitchHit = 0;
const int Pulse = 5; // just digital-out
const int SLJumper = 10; // open is A, closed is B
const int SLJumper_GND = 9; // we set it to low as gnd for jumper, so a jumper can just go between adjacent pins

// Pulse Pattern
const int TotalPatternLength = 4 * 1000; // 4 seconds
const int OnTime = 400; // minimum reliable
// leave an OnTime gap for the other to fit in
// ----____----___...
const int SleepTimeMinQuanta = 16; // watchdog timer min duration
const int ShortOffTime = OnTime + 20;
// The second on has to miss A's:
// ----________----___...
const int LongOffTime = ShortOffTime + OnTime + 20;

char Which = '?'; // serial/debug: to be filled in with S or L for the off time
// The pulse pattern, 0's filled in at setup():
unsigned long BlinkPattern[] = {OnTime, 0, OnTime, 0};
template <typename T, unsigned S> inline unsigned arraysize(const T (&v)[S]) {
  return S;
};

Every::Pattern Pulsing(arraysize(BlinkPattern), BlinkPattern);
int ShortOff_I = 1; // to be filled in based on jumper
int EndOff_I = arraysize(BlinkPattern) - 1; // to be filled in based on jumper

void serial_wait() {
  // have to wait on usb-serial (or timeout if not connected)
  // Blink while waiting

  Timer serial_begin_timeout(2000);
  unsigned long BlinkPattern[] = {10, 100};
  Every::Pattern blink(2, BlinkPattern, true);

  digitalWrite(LED_BUILTIN, LOW);
  while ( ! Serial && ! serial_begin_timeout() ) {
    if (blink()) digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN) );
  }
}

void setup() {

  // Setup for minimum power use:
  // worth 1-3ma
  // do first, so other uses will "override" later
  for (int i = 0; i < NUM_DIGITAL_PINS; i++) {
    // the pins_arduino.h for itsybitsy32u4/ doesn't define LED_BUILTIN_TX
    if (i != 30 /* LED_BUILTIN_TX */ ) { // might not be necessary to skip
      pinMode(i, OUTPUT);
      digitalWrite(i, LOW);
    }
  }

  // Minimum signal that we started:
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // using pullup is slightly more power hungry ~micro-amps
  // will attach interrupt below
  pinMode(Switch, INPUT_PULLUP);

  pinMode(SLJumper, INPUT_PULLUP);
  // a "ground" for the above so a jumper can just go between adjacent pins
  pinMode(SLJumper_GND, OUTPUT);
  digitalWrite(SLJumper_GND, LOW);

  pinMode(Pulse, OUTPUT);
  digitalWrite(Pulse, LOW);

  serial_wait(); // flashes rapidly for 2 seconds, also startup signal

  Serial << "Start\n";

  // Short|Long gap
  // FIXME: signal which A|B somehow?
  if (digitalRead(SLJumper)) {
    // high is open, so S
    Which = 'S';
    BlinkPattern[ShortOff_I] = ShortOffTime;
  }
  else {
    Which = 'L';
    BlinkPattern[ShortOff_I] = LongOffTime;
  }

  int end_off = TotalPatternLength;
  for (int i = 0; i < EndOff_I; i++) {
    end_off -= BlinkPattern[i];
  }
  BlinkPattern[EndOff_I] = end_off;

  Serial << "Pattern: " << Which << "\n";
  int pattern_sum = 0;
  for (unsigned int i = 0; i < arraysize(BlinkPattern); i++) {
    pattern_sum += BlinkPattern[i];
    Serial << ( i % 2 ? "_" : "-") << BlinkPattern[i] << " ";
  }
  Serial << "\n";

  if (pattern_sum > TotalPatternLength) {
    Serial << "Fail: pattern ("
           << pattern_sum
           << ") is longer than TotalPatternLength("
           << TotalPatternLength
           << ")\n";
  }

  // give a clue that we are powered-on: blink a bit
  // NB: also gives time to upload w/o being in power down, so allow at least 2 seconds here!
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

void wakeUp()
{
  // Just a handler for the pin interrupt.
  detachInterrupt(SwitchInterrupt);
  SwitchHit = 1;
}

void loop() {
  // on power-up, will turn on Pulse for 1 "persistance":
  // covers debounce, and person moving around on the seat
  // initial persistance is short, reset to longer for real event below
  static Timer switch_persistance(100); // pretend to be on for at least a while
  static boolean switch_was_reset = 1;
  static Every say_on(500);

  if ( ! digitalRead(Switch) ) {
    // high is open (pullup)
    if (StandAlone) digitalWrite(LED_BUILTIN, HIGH);
    // but pretend to be on for 1 second more, which is not enough for a full pattern
    switch_persistance.reset(1 * 1000);
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
    if (switch_was_reset) Serial << millis() << " ON\n";
    switch_was_reset = 0;
    // if (StandAlone && say_on()) Serial << millis() << " Running " << (millis() - switch_persistance.last) << "\n";
  }
  else {
    if (! switch_was_reset) Serial << millis() << " OFF\n";
    switch_was_reset = 1;
    digitalWrite( Pulse, LOW );

    // we can powerdown if the switch is off, and let interrupt wake us up
    while (! SwitchHit) {
      attachInterrupt(SwitchInterrupt, wakeUp, LOW);

      if (StandAlone) Serial << "SLEEP-OFF @" << millis() << "\n";
      LowPower.powerDown(StandAlone ? SLEEP_2S : SLEEP_4S, ADC_OFF, BOD_OFF);
      // a Serial operation, here, seems to cause a 200ms delay: waiting for usb-serial?
      // Without active serial, we get immediate Pulse pattern restart
      if (StandAlone) Serial << "SLEEP-ON @" << millis() << "\n";

      digitalWrite(LED_BUILTIN, HIGH);
      delay(10);
      digitalWrite(LED_BUILTIN, LOW);
    }
    SwitchHit = 0;

  }

  // delay(10);
}

void pulse_sequence(boolean restart) {
  static unsigned long last_change = millis();

  if (restart) {
    // so we can send out a pulse immediately
    Pulsing.reset();
    if (StandAlone) Serial << millis() - last_change << " RF reset sequence, start []" << Pulsing.sequence() << " 1" << "\n";
    digitalWrite( Pulse, HIGH); // start high
    last_change = millis();
  }

  if (Pulsing()) {
    digitalWrite( Pulse, ! digitalRead(Pulse) );
    if (StandAlone) Serial << millis() - last_change << " RF []" << Pulsing.sequence() << " " << digitalRead(Pulse) << "\n";
    last_change = millis();

    // we can idle/sleep while waiting:
    unsigned long next_period = BlinkPattern[Pulsing.sequence()];

    // assume long periods aren't accuracy important,
    // so let's deep-sleep for long periods
    if (next_period > 1000ul) {
      if (StandAlone) Serial << "SLEEP for " << next_period << " @" << millis() << "\n";
      LowPower.longPowerDown(next_period);
      // USBDevice.attach(); appears to be harmful! I mostly get serial port reconnect w/o!
      if (StandAlone) Serial << "Wake @" << millis() << "\n";
      Pulsing.last = millis() - next_period; // force expire, clock doesn't run during powerdown
    }
  }

}
