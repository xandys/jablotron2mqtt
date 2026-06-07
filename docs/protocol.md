This is an attempt to reverse engineer the protocol that is used by the Jablotron 6x alarm to communicate over the JA-80T serial cable with the ComLink software.

Source: https://github.com/pezinek/py-jablotron6x/wiki/Protocol

# Serial connection details

| baud rate    | 9600 |
|--------------|------|
| data bits    | 8    |
| stop bits    | 1    |
| parity       | None |
| flow control | None |


# Common format for all packets

| offset | size     | description                     |
|--------|----------|---------------------------------|
| 00     | 1 byte   | [record type](#record-types)    |
| ..     | variable | payload                         |
| -2     | 1 byte   | checksum                        |
| -1     | 1 byte   | 0xFF - indicates end of message |


# Record types

| Record type       | Description                            |
|-------------------|----------------------------------------|
| [80](#80) - 8f    | key pressed                            |
| [a0](#a0) - af    | Audio/Beeps                            |
| [b0](#b0) - bf    | Internal commands                      |
| [c0](#c0) - c1    | ???                                    |
| [de](#de)         | ???                                    |
| [e0](#e0) - e2    | General status (send periodically)     |
| [e3](#e3)         | Service event                          |
| [e4](#e4)         | User event                             |
| [e5](#e5)         | Alarm clock time (periodic)            |
| [e6](#e6)         | Switchboard configuration              |
| [e7](#e7)         | Some other event (send periodically)   |
| [e8](#e8)         | Some different event                   |
| [e9](#e9)         | Sensor seen motion in service mode     |
| [ea](#ea)         | ???                                    |
| [eb](#eb)         | ???                                    |
| [ec](#ec)         | Settings from GSM communicator         |
| [fe](#fe)         | ???                                    |


# 80

Record types 80 are being sent by the switchboard to echo the pressed keys; these codes can also be sent
over serial to the switchboard to emulate key presses (in input mode the 0xFF terminator is omitted).

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | [key being pressed](#key)       |
| 01     | 1 byte | 0xFF - indicates end of message |

#### Key

Mapping of keypad keys to their serial codes. Special keys with pictograms are emulated as F1, F2, etc. (see the manual).
Serial codes 0x8A - 0x8D are accepted by the switchboard and confirmed by beeps but do not do anything.

| Code | Key |
|------|-----|
| 0x80 |  0  |
| 0x81 |  1  |
| 0x82 |  2  |
| 0x83 |  3  |
| 0x84 |  4  |
| 0x85 |  5  |
| 0x86 |  6  |
| 0x87 |  7  |
| 0x88 |  8  |
| 0x89 |  9  |
| 0x8E |  N  |
| 0x8F |  F  |


# a0

Record types a0 - af are likely requests for peripherals to emit various kinds of beeps.

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | [beep type](#beep)              |
| 01     | 1 byte | 0xFF - indicates end of message |

#### Beep

| Code | Description                                          |
|------|------------------------------------------------------|
| 0xa0 | single short beep (e.g. when key gets pressed)       |
| 0xa1 | single long beep (e.g. when entering service mode)   |
| 0xa2 | two long beeps (e.g. when disarmed)                  |
| 0xa4 | 4 short beeps (e.g. when N gets pressed)             |
| 0xa8 | infinite beeping (e.g. after being armed)            |
| 0xaa | seen when arming/disarming                           |


# b0

b0 - bf are internal commands that peripherals use to request data from other peripherals. You may send these
codes without the trailing 0xFF to dispatch the request yourself and the command will be echoed back (with trailing 0xFF).

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | [command](#command)             |
| 01     | 1 byte | 0xFF - indicates end of message |

#### Command

| Code  | Description                                                        |
|-------|--------------------------------------------------------------------|
| 0xb1  | responds with [e3](#e3)/[e7](#e7) events [4d 1b]                                 |
| 0xb2  | responds with [e3](#e3)/[e7](#e7) [05 b1] and fires tamper alarm                 |
| 0xb3  | responds with [e3](#e3)/[e7](#e7) [16 b1]                                        |
| 0xb4  | end of response / confirmation                                                    |
| 0xb5  | list of [e4](#e4) events from switchboard                                        |
| 0xb6  | does nothing when sent                                                            |
| 0xb7  | seen when switching to service mode, silent alarm fired or disarmed; does nothing when sent |
| 0xb8  | seen when switching to user mode; does nothing when sent                          |
| 0xb9  | responds with [e8](#e8) 10                                                       |
| 0xba  | responds with [e7](#e7) [48 1b] (last message in the log?)                       |
| 0xbb  | responds with [e3](#e3)/[e7](#e7) [53 1b]                                        |
| 0xbc  | responds with [e3](#e3)/[e7](#e7) [54 1b]                                        |
| 0xbd  | does nothing when sent                                                            |
| 0xbe  | does nothing when sent                                                            |
| 0xbf  | responds with [e4](#e4) 17 04 19 56 46 1b 5f ff                                 |


# c0
# c1

There is a routine for handling c0 and c1 in the ComLink software however the meaning of these codes is still unknown.


# de

The 0xde events have a special case in the ComLink software to be ignored. Not sure what they are supposed to do.


# e0

Record type e0 is general status, sent periodically every second or so by the alarm.
When arming is delayed the e0 events get replaced by e1 events, and when the delay is about to expire with e2 events. Once fully armed they go back to e0.
e2 is also used all the time during entry delay or when a silent alarm is fired.

| offset | size   | description                      |
|--------|--------|----------------------------------|
| 00     | 1 byte | e0/e1/e2 - general status        |
| 01     | 1 byte | mode                             |
| 02     | 1 byte | binary status of LEDs            |
| 03     | 1 byte | content of display               |
| 04     | 1 byte | strength of GSM signal/battery   |
| 05     | 1 byte | zero, one, or two                |
| 06     | 1 byte | checksum                         |
| 07     | 1 byte | 0xFF - indicates end of message  |

#### Mode

| Value | Value (binary) | Mode                        |
|-------|----------------|-----------------------------|
| 0x00  | 0000 0000      | service mode                |
| 0x03  | 0000 0011      | service mode (keypress active) |
| 0x04  | 0000 0100      | service mode (entering code/value) |
| 0x06  | 0000 0110      | service mode (entering code, keypress active) |
| 0x20  | 0010 0000      | user mode                   |
| 0x23  | 0010 0011      | user mode (keypress active) |
| 0x40  | 0100 0000      | disarmed                    |
| 0x41  | 0100 0001      | armed                       |
| 0x44  | 0100 0100      | tamper/silent alarm         |
| 0x45  | 0100 0101      | alarm triggered             |
| 0x49  | 0100 1001      | entry delay                 |
| 0x51  | 0101 0001      | arming                      |
| 0x61  | 0110 0001      | zone A armed                |
| 0x63  | 0110 0011      | zone B armed                |
| 0x69  | 0110 1001      | entry delay B               |
| 0x71  | 0111 0001      | zone A arming               |
| 0x73  | 0111 0011      | zone B arming               |

#### LED status

| Bit mask | LED indicator                               |
|----------|---------------------------------------------|
| 0x01     | Power                                       |
| 0x02     | Alarm                                       |
| 0x04     | Tamper                                      |
| 0x07     | Malfunction (power + alarm + tamper all set)|
| 0x10     | Lock LED ON                                 |
| 0x20     | Lock LED blinking                           |
| 0x40     | Wireless communication                      |
| 0x80     | ???                                         |

#### Display

| Value     | Content of display             |
|-----------|--------------------------------|
| 0x00      | (blank — during code entry)    |
| 0x01      | 1                              |
| 0x02      | 2                              |
| 0x03      | 3                              |
| 0x04      | 4                              |
| 0x05      | 5                              |
| 0x06      | 6                              |
| 0x07      | 7                              |
| 0x08      | 8                              |
| 0x09      | 9                              |
| 0x0A      | 10                             |
| 0x0B      | 11                             |
| 0x0C      | 12                             |
| 0x0D      | 13                             |
| 0x0E      | 14                             |
| 0x0F      | 15                             |
| 0x10      | 16                             |
| 0x11      | A                              |
| 0x12      | b ?                            |
| 0x13      | C                              |
| 0x14      | d                              |
| 0x17      | U                              |
| 0x1a      | P                              |
| 0x1c      | L                              |
| 0x1d      | J                              |
| 0x21      | c1                             |
| 0x22      | c2                             |
| 0x23      | c3                             |
| 0x24      | c4                             |
| 0x25      | c5                             |
| 0x26      | c6                             |
| 0x27      | c7                             |
| 0x28      | c8                             |
| 0x41      | number 1 (alarm LED blinking)  |
| 0x53      | ' C' (alarm LED blinking)      |
| 0x59      | empty display or ',,'          |
| 0x5b      | symbol "-"                     |
| 0x5e      | ', '                           |
| 0x5f      | ' ,'                           |
| 0x??      | H                              |
| 0x??      | F                              |
| 0x??      | E                              |

#### Zero, one, or two

This field is most of the time zero; it is nonzero in these cases:

| Value | When seen                                                   |
|-------|-------------------------------------------------------------|
| 0x01  | when armed and a delayed PIR sensor was triggered           |
| 0x02  | when time for delayed entry expired and alarm was triggered |

#### Examples

| Message                    | Description                                                       |
|----------------------------|-------------------------------------------------------------------|
| e0 40 01 59 75 00 3d ff    | normal mode, nothing on display                                   |
| e0 40 01 5b 75 00 06 ff    | after pressing F on keypad                                        |
| e0 40 01 5b 75 00 06 ff    | after pressing 5 on keypad, display shows symbol '-'              |
| e0 20 01 09 75 00 38 ff    | user mode                                                         |
| e0 20 01 17 75 00 07 ff    | user mode                                                         |
| e0 20 03 02 75 00 34 ff    | user mode, sensor 1 seen motion                                   |
| e0 20 03 01 75 00 43 ff    | user mode, sensor 2 seen motion                                   |
| e0 00 01 1a 75 00 57 ff    | service mode                                                      |
| e0 00 03 02 75 00 11 ff    | service mode, sensor 2 seen motion                                |
| e0 00 01 1a 7f 00 15 ff    | service mode, happens sometimes                                   |
| e0 73 21 5f 75 00 2d ff    | arming B mode                                                     |
| e0 41 11 59 75 00 76 ff    | fully armed A + B                                                 |
| e1 51 21 59 75 00 37 ff    | delayed leave                                                     |
| e2 51 21 59 75 00 26 ff    | delay is about to expire                                          |
| e2 44 05 14 75 02 1f ff    | tamper alarm, digital bus                                         |
| e0 71 21 5e 76 00 03 ff    | arming sector A (lock LED is blinking)                            |
| e0 61 21 5e 75 00 3e ff    | armed sector A (lock LED is continuously on?)                     |
| e0 61 11 5e 7f 00 10 ff    | armed sector A (lock LED is continuously on)                      |
| e0 73 21 5f 75 00 2d ff    | arming sector B (lock LED is blinking)                            |
| e0 63 21 5f 75 00 6e ff    | sector B armed (lock LED is continuously on?)                     |
| e0 63 11 5f 75 00 02 ff    | sector B armed (lock LED is continuously on)                      |
| e0 51 21 59 76 00 27 ff    | sector A armed + arming sector B (lock blinking + slow beeps)     |
| e1 51 21 59 74 00 1d ff    | sector A armed + arming sector B (lock blinking + slow beeps)     |
| e2 51 21 59 75 00 26 ff    | sector A armed + arming sector B (lock blinking + fast beeps)     |
| e0 41 21 59 75 00 1a ff    | both sectors armed (lock LED continuously on, no beeps?)          |
| e0 41 11 59 75 00 76 ff    | both sectors armed (lock LED continuously on, no beeps)           |
| e2 49 11 59 75 01 3f ff    | armed, delayed PIR sensor triggered, entry delay started          |
| e2 45 31 59 75 02 37 ff    | armed, entry delay expired, alarm triggered                       |
| e0 45 13 01 75 02 70 ff    | alarm triggered, siren on, key pressed on keypad                  |
| e0 40 03 41 76 00 05 ff    | alarm disabled, alarm LED blinking, display: "1"                  |
| e2 44 03 13 76 00 13 ff    | silent alarm on                                                   |
| e0 40 03 53 75 00 7d ff    | silent alarm deactivated, alarm LED blinking, display: " C"       |


# e3

Record type e3 is a time-stamped service event from the alarm.
It often happens that the same event is sent as e3 and as e7 right away.

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e3 - service event              |
| 01     | 1 byte | day (BCD encoded)               |
| 02     | 1 byte | month (BCD encoded)             |
| 03     | 1 byte | hour (BCD encoded)              |
| 04     | 1 byte | minute (BCD encoded)            |
| 05     | 1 byte | [event type](#event-type)       |
| 06     | 1 byte | [event source](#event-source)   |
| 07     | 1 byte | checksum                        |
| 08     | 1 byte | 0xFF - indicates end of message |

#### Event type

Derived by cross-referencing e4 hex records with ComLink event log (timestamps matched).

| Code | Description                              |
|------|------------------------------------------|
| 0x04 | silent alarm                             |
| 0x05 | tamper alarm (cover breach)              |
| 0x07 | error / malfunction                      |
| 0x08 | system armed                             |
| 0x09 | system disarmed                          |
| 0x0e | exited programming mode                  |
| 0x11 | battery low in peripheral                |
| 0x12 | phone line fault                         |
| 0x13 | phone line OK                            |
| 0x16 | ???                                      |
| 0x1a | ???                                      |
| 0x41 | service mode started                     |
| 0x42 | service mode ended                       |
| 0x44 | message delivered to number 1            |
| 0x45 | message not delivered to number 1        |
| 0x46 | message delivered to number 2            |
| 0x47 | message not delivered to number 2        |
| 0x48 | message delivered to number 3            |
| 0x49 | message not delivered to number 3        |
| 0x4a | message delivered to number 4            |
| 0x4b | message not delivered to number 4        |
| 0x4c | message delivered (any number)           |
| 0x4d | message not delivered (all numbers failed)|
| 0x4e | alarm cancelled by user                  |
| 0x50 | all tamper sensors OK                    |
| 0x51 | all faults cleared                       |
| 0x52 | power OK (AC restored)                   |
| 0x53 | ???                                      |
| 0x54 | cannot pass info to PCO                  |
| 0x58 | remote PgX/PgY disabled                  |
| 0x59 | power outage >30 min                     |

#### Event source

| Code | Source                         |
|------|--------------------------------|
| 0x00 | switchboard / control panel    |
| 0x01 | detector 1                     |
| 0x02 | detector 2                     |
| 0x03 | detector 3                     |
| 0x11 | keypad / remote control 1      |
| 0x1b | phone line                     |
| 0x1c | digital bus / serial port      |
| 0x21 | wired sensor 1                 |
| 0x22 | wired sensor 2                 |
| 0x7c | serial port (silent alarm)     |


# e4

User event stored in memory. Same format as e3.
The full list of stored user events can be requested via the [b5](#b0) command; the alarm responds with all e4 records followed by `b4 ff` (end of response).
Published to `alarm/event/history` (vs `alarm/event` for live e3/e7).


# e5

Alarm clock time, sent periodically; carries the alarm panel's current date and time.

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e5                              |
| 01     | 1 byte | month (binary)                  |
| 02     | 1 byte | day (binary)                    |
| 03     | 1 byte | hour (binary)                   |
| 04     | 1 byte | minute (binary)                 |
| 05     | 1 byte | checksum                        |
| 06     | 1 byte | 0xFF - indicates end of message |

Example: `e5 04 11 17 07 71 ff` → 11.04 17:07


# e6

Configuration of the switchboard, sent in bulk after `0x8A` ('*') is pressed in service mode.
The subtype byte (offset 01) determines the record structure.

Example records from a real device:
```
e6 03 01 01 4d ff  - boolean setting 1 = on
e6 03 02 01 33 ff  - boolean setting 2 = on
e6 03 03 01 19 ff  - boolean setting 3 = on
e6 03 04 00 2a ff  - boolean setting 4 = off
e6 03 05 01 46 ff  - boolean setting 5 = on
e6 03 09 00 1d ff  - boolean setting 9 = off
e6 02 05 00 4c ff  - multi-value setting 5 = 0
e6 02 06 00 32 ff  - multi-value setting 6 = 0
e6 02 07 00 18 ff  - multi-value setting 7 = 0
e6 02 08 01 3d ff  - multi-value setting 8 = 1
```

#### Subtype 0x02 — multi-value setting

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e6                              |
| 01     | 1 byte | 0x02                            |
| 02     | 1 byte | setting ID                      |
| 03     | 1 byte | value                           |
| 04     | 1 byte | checksum                        |
| 05     | 1 byte | 0xFF                            |

#### Subtype 0x03 — boolean setting

Same structure as 0x02; value is 0x00 (off) or 0x01 (on).

#### Subtype 0x04 — raw record

| offset | size     | description                     |
|--------|----------|---------------------------------|
| 00     | 1 byte   | e6                              |
| 01     | 1 byte   | 0x04                            |
| 02+    | variable | raw data bytes                  |
| -2     | 1 byte   | checksum                        |
| -1     | 1 byte   | 0xFF                            |

#### Subtype 0x06 — grouped setting (3-byte form)

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e6                              |
| 01     | 1 byte | 0x06                            |
| 02     | 1 byte | group                           |
| 03     | 1 byte | index                           |
| 04     | 1 byte | value                           |
| 05     | 1 byte | checksum                        |
| 06     | 1 byte | 0xFF                            |

#### Subtype 0x06 — grouped setting (4+ byte form)

| offset | size     | description                     |
|--------|----------|---------------------------------|
| 00     | 1 byte   | e6                              |
| 01     | 1 byte   | 0x06                            |
| 02     | 1 byte   | group                           |
| 03     | 1 byte   | block                           |
| 04     | 1 byte   | index                           |
| 05+    | variable | value bytes                     |
| -2     | 1 byte   | checksum                        |
| -1     | 1 byte   | 0xFF                            |

#### Known e6 02 setting IDs

Keypad code: `2[id][value]`.

| ID | Czech                                                   | English                                          | Value encoding |
|----|---------------------------------------------------------|--------------------------------------------------|----------------|
| 0  | Odchodové zpoždění                                      | Exit delay                                       | step index: 0=10s, 1=15s, 2=20s, 3=30s, 4=45s, 5=60s, 6=90s, 7=120s |
| 1  | Příchodové zpoždění                                     | Entry delay                                      | same step table |
| 2  | Doba poplachu                                           | Alarm duration                                   | minutes (direct integer) |
| 3  | Funkce výstupu PgX                                      | PgX output function                              | 0=Chime, 1=Fire, 2=Arm, 3=Panic, 4=Alarm, 5=Door, 6=Home, 7=NoAC, 8=Phone |
| 4  | Funkce výstupu PgY                                      | PgY output function                              | same as PgX |
| 5  | Změna tlf. čísel a zpráv v uživatelském režimu          | Change phone numbers/messages in user mode       | 0=disabled, 1=enabled |
| 6  | Hlídání rádiového rušení ústředny                       | Panel radio jamming monitoring                   | 0=disabled, 1=enabled |
| 7  | Pravidelná kontrola spojení s bezdr. detektory          | Regular wireless detector connection check       | 0=disabled, 1=enabled |
| 8  | Povolení RESETU ústředny                                | Allow panel RESET                                | 0=disabled, 1=enabled |

#### Known e6 03 boolean setting IDs

Value encoding: 0=No, 1=Yes. Keypad code: `3[id][value]`.

| ID | Setting (Czech)                                          | English                                              | Default |
|----|----------------------------------------------------------|------------------------------------------------------|---------|
| 0  | Ovládání bez kódu                                        | Control without code (affects F1/F2/F3/F4/F9)        | 1       |
| 1  | Částečné zajištění povoleno (F2)                         | Partial arming allowed (F2)                          | 1       |
| 2  | Povolení poplachu připojenou sirénou                     | Siren connected during alarm                         | 1       |
| 3  | Akustická signalizace odchodového zpoždění               | Acoustic signaling of exit delay                     | 1       |
| 4  | Ak. signal. odchod. zp. při částečném zajištění          | Acoustic exit delay signaling (partial arm)          | 0       |
| 5  | Akustická signalizace příchodového zpoždění              | Acoustic signaling of entry delay                    | 1       |
| 6  | Hlasité potvrzení zajištění a odjištění sirénou          | Loud confirmation of arming/disarming                | 0       |
| 7  | Siréna při částečném zajištění nebo odjištění            | Siren alarm during partial arming                    | 1       |
| 8  | Poplach bezdrátovou vnější sirénou JA-60A/UC-260         | Wireless siren alarm                                 | 1       |
| 9  | Upozornění na závadu periferie při zajištění             | Peripheral fault warning during arming               | 0       |

#### E6 06 groups observed

Fields listed are those after the group byte (buf[2]).

| Group | Extra fields              | Notes                                                    |
|-------|---------------------------|----------------------------------------------------------|
| 0     | block, idx, 3 value bytes | per-peripheral multi-byte settings                       |
| 1     | block, idx, 1 value byte  | sensor enable flags                                      |
| 2     | block, idx, 1 value byte  | zone settings                                            |
| 3     | block, idx, 1 value byte  | zone options                                             |
| 4     | block, idx, 4 value bytes | zone/sensor config; block=zone id (0–9); all-zero = disabled |
| 9     | idx, 1 value byte         | system options (3-byte form); keypad code `69[idx]x`     |

Zone 01–10 maps to e6 06 group 4, block 0–9.

#### Known e6 06 group 9 setting indices

Value encoding: 0=No, 1=Yes. Keypad code: `69[idx]x`.

| idx | Setting (Czech)                                              | English                                         | Default |
|-----|--------------------------------------------------------------|-------------------------------------------------|---------|
| 0   | Rozdělení ústředny do sekcí                                  | Division into sections (A/B)                    | 0       |
| 1   | Zaznamenání pouze 1. příčiny poplachu                        | Record only 1st cause of alarm                  | 0       |
| 2   | Poplach při zajištění s otevřenou zónou                      | Alarm when arming with open zone                | 0       |
| 3   | Hlasitý tísňový poplach                                      | Loud panic alarm                                | 0       |
| 4   | Přepnutí bezdrátových detektorů do následně zpožděné smyčky  | Wireless detectors in delayed loop              | 0       |
| 5   | (unknown)                                                    | —                                               | 0       |
| 6   | Poplach při ztrátě periferie                                 | Alarm on peripheral loss                        | 1       |
| 7   | Vstup do programování SC+MC/UC                               | Enter programming via SC+MC/UC                  | 0       |


# e7

Some other time-stamped event; typically repeats the content of the previous [e3](#e3) event.
e7 can be requested by the [ba](#b0) command.


# e8

Some simple timeless status event. Appears during service mode transitions and in response to the b9 command.

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e8                              |
| 01     | 1 byte | ID                              |
| 02     | 1 byte | value                           |
| 03     | 1 byte | 0xFF - indicates end of message |

Examples:

```
e8 0c 64 ff
e8 0b 53 ff - when switched to user mode
e8 0d 22 ff - when setting time
e8 0e 4b ff - when disarming section B
e8 0e 4b ff - when armed + delay
e8 0e 4b ff - when switched to service mode
e8 0e 4b ff - when alarm was deactivated by entering master code
e8 01 63 ff - when silent alarm fired via serial line while system was disarmed (F7 + CODE)
```


# e9

These events are seen when in service mode and testing sensors.

(Event type codes are the codes sent to PCO, so they likely match the internal event types.)

| offset | size   | description                     |
|--------|--------|---------------------------------|
| 00     | 1 byte | e9 - service event              |
| 01     | 1 byte | event type                      |
| 02     | 1 byte | event source                    |
| 03     | 1 byte | RF signal                       |
| 04     | 1 byte | checksum                        |
| 05     | 1 byte | 0xFF - indicates end of message |

#### Event type

| Code | Event                               |
|------|-------------------------------------|
| 0x01 | alarm in immediate zone             |
| 0x02 | alarm in delayed zone               |
| 0x03 | fire alarm                          |
| 0x04 | silent alarm                        |
| 0x05 | alarm - num attempts exceeded       |
| 0x06 | alarm after power on                |
| 0x07 | tamper alarm                        |
| 0x08 | tamper recovered                    |
| 0x09 | alarm timed out                     |
| 0x0A | alarm canceled by user              |
| 0x0B | armed                               |
| 0x0C | disarmed                            |
| 0x0D | armed partially (home)              |
| 0x0E | armed without code                  |
| 0x0F | external communication failure      |
| 0x10 | external communication recovered    |
| 0x11 | malfunction                         |
| 0x12 | malfunction recovered               |
| 0x13 | AC disconnected for longer than 30 min |
| 0x14 | AC disconnected                     |
| 0x15 | AC recovered                        |
| 0x16 | battery depleted                    |
| 0x17 | battery OK                          |
| 0x18 | service mode started                |
| 0x19 | service mode ended                  |
| 0x1A | remote access started               |
| 0x1B | remote access ended                 |
| 0x1C | VF receiver jamming                 |
| 0x1D | internal communication failure      |
| 0x1E | internal communication recovery     |
| 0x1F | test transmission                   |


# ea
# eb

0xea and 0xeb messages have never been observed, but the ComLink software loads them similarly to [e8](#e8) and [ec](#ec).
The handling routine for 0xea and 0xeb is the same, so likely these have the same structure.


# ec

These events are used by the GSM communicator to dump/set its configuration.
If you are in service mode you may send these messages (must contain valid checksum and trailing 0xFF)
to talk to the GSM communicator.

| offset | size     | description                     |
|--------|----------|---------------------------------|
| 00     | 1 byte   | ec - GSM configuration/text     |
| 01     | 1 byte   | GSM message type                |
| 02     | 1 byte   | settings/message ID             |
| 03+    | variable | payload                         |
| -2     | 1 byte   | checksum                        |
| -1     | 1 byte   | 0xFF - indicates end of message |

#### GSM message type

| Code | Description                                                          |
|------|----------------------------------------------------------------------|
| 0x00 | terminates the list of GSM configuration (ec 00 00 12 ff)           |
| 0x01 | configuration containing zero-terminated strings (e.g. phone numbers)|
| 0x02 | seen when dumping GSM config (single value)                          |
| 0x03 | binary configuration for 40 checkboxes                              |
| 0x2X | configurable texts starting from ID X×100                           |
| 0x40 | used to request configuration dumps                                  |

#### Format of the 0x2X text message type

| offset    | size    | description                       |
|-----------|---------|-----------------------------------|
| 00        | 1 byte  | ec - GSM message                  |
| 01 (high) | 4 bits  | 0x2 - GSM text identifier         |
| 01 (low)  | 4 bits  | base ID                           |
| 02        | 1 byte  | message ID (+ base ID × 100)      |
| 03        | 3 bytes | string length                     |
| X         | 3 bytes | character (e.g. 20 00 00 = space) |
| -5        | 1 byte  | 0x00                              |
| -4        | 1 byte  | 0x00                              |
| -2        | 1 byte  | checksum                          |
| -1        | 1 byte  | 0xFF - indicates end of message   |

#### Known commands to send to GSM communicator

(must be in service mode)

| Command          | Description                                   |
|------------------|-----------------------------------------------|
| ec 40 05 19 ff   | dump customizable texts from GSM communicator |
| ec 40 07 36 ff   | dump configuration of the GSM communicator   |


# fe

Unknown, seen when exiting user mode in format `fe ff`.
