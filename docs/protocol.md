# Protocol - py-jablotron6x Wiki

Source: https://github.com/pezinek/py-jablotron6x/wiki/Protocol

## Serial Connection Details

| Parameter | Value |
|-----------|-------|
| Baud rate | 9600 |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Flow control | None |

## Common Format for All Packets

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | Record type |
| ... | variable | Payload |
| -2 | 1 byte | Checksum |
| -1 | 1 byte | 0xFF - end of message |

## Record Types

| Record Type | Description |
|-------------|-------------|
| 80-8f | Key pressed |
| a0-af | Audio/Beeps |
| b0-bf | Internal commands |
| c0-c1 | Unknown |
| de | Unknown |
| e0-e2 | General status (periodic) |
| e3 | Service event |
| e4 | User event |
| e5 | Alarm clock time (periodic) |
| e6 | Switchboard configuration |
| e7 | Other event (periodic) |
| e8 | Different event |
| e9 | Sensor motion in service mode |
| ea-eb | Unknown |
| ec | GSM communicator settings |
| fe | Unknown |

## Record Type 80 - Key Pressed

Switchboard echoes pressed keys; codes can emulate key presses over serial.

| Code | Key |
|------|-----|
| 0x80-0x89 | 0-9 |
| 0x8A | * |
| 0x8E | N |
| 0x8F | F |

## Record Type a0 - Beeps

Audio requests from peripherals.

| Code | Description |
|------|-------------|
| 0xa0 | Single short beep |
| 0xa1 | Single long beep |
| 0xa2 | Two long beeps |
| 0xa4 | Four short beeps |
| 0xa8 | Infinite beeping |
| 0xaa | Arm/disarm beep |

## Record Type b0 - Internal Commands

Peripherals request data; can dispatch without trailing 0xFF.

| Code | Description |
|------|-------------|
| 0xb1 | Responds with e3/e7 events [4d 1b] |
| 0xb2 | Responds with e3/e7, triggers tamper alarm [05 b1] |
| 0xb3 | Responds with e3/e7 [16 b1] |
| 0xb4 | Confirmation/end of response |
| 0xb5 | List of e4 events from switchboard |
| 0xb6 | No effect |
| 0xb7 | Service mode/silent alarm/disarm indicator |
| 0xb8 | User mode indicator |
| 0xb9 | Responds with e8 10 |
| 0xba | Responds with e7 [48 1b] |
| 0xbb | Responds with e3/e7 [53 1b] |
| 0xbc | Responds with e3/e7 [54 1b] |
| 0xbd-0xbe | No effect |
| 0xbf | Responds with e4 17 04 19 56 46 1b 5f ff |

## Record Type c0 & c1

Unknown meaning; handled in ComLink software.

## Record Type de

Special case in ComLink software to ignore these events.

## Record Type e0 - General Status

Periodic status transmission. Replaced by e1 during arming delay, e2 near expiration or during entry delay.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e0/e1/e2 |
| 01 | 1 byte | Mode |
| 02 | 1 byte | LED binary status |
| 03 | 1 byte | Display content |
| 04 | 1 byte | GSM signal/battery |
| 05 | 1 byte | Zero, one, or two |
| 06 | 1 byte | Checksum |
| 07 | 1 byte | 0xFF |

### Mode Values

| Code | Mode |
|------|------|
| 0x00 | Service mode |
| 0x20 | User mode |
| 0x23 | User mode (keypress active) |
| 0x40 | Disarmed |
| 0x41 | Armed |
| 0x44 | Tamper/silent alarm |
| 0x45 | Alarm triggered |
| 0x49 | Entry delay |
| 0x51 | Arming |
| 0x61 | Zone A armed |
| 0x63 | Zone B armed |
| 0x69 | Entry delay B |
| 0x71 | Zone A arming |
| 0x73 | Zone B arming |

### LED Status

| Bit mask | LED Indicator |
|----------|---------------|
| 0x01 | Power |
| 0x02 | Alarm |
| 0x04 | Tamper |
| 0x07 | Malfunction (power + alarm + tamper all set) |
| 0x10 | Lock LED ON |
| 0x20 | Lock LED blinking |
| 0x40 | Wireless communication |
| 0x80 | Unknown |

### Display Values

Characters mapped to hex codes (0x01-0x0F for 1-15, 0x11 for A, etc.)

### Zero One or Two Field

| Value | Condition |
|-------|-----------|
| 0x01 | Delayed PIR triggered while armed |
| 0x02 | Entry delay expired, alarm triggered |

## Record Type e3 - Service Event

Time-stamped service event; often sent simultaneously with e7.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e3 |
| 01 | 1 byte | Day (BCD) |
| 02 | 1 byte | Month (BCD) |
| 03 | 1 byte | Hour (BCD) |
| 04 | 1 byte | Minute (BCD) |
| 05 | 1 byte | Event type |
| 06 | 1 byte | Event source |
| 07 | 1 byte | Checksum |
| 08 | 1 byte | 0xFF |

### Event Types

Derived by cross-referencing E4 hex records with ComLink event log (timestamps matched).

| Code | Description |
|------|-------------|
| 0x04 | Silent alarm |
| 0x05 | Tamper (cover breach) |
| 0x07 | Error / malfunction |
| 0x08 | System armed |
| 0x09 | System disarmed |
| 0x0e | Exit programming mode |
| 0x11 | Battery low in peripheral |
| 0x12 | Phone line fault |
| 0x13 | Phone line OK |
| 0x41 | Service mode started |
| 0x42 | Service mode ended |
| 0x44 | Message delivered to number 1 |
| 0x45 | Message not delivered to number 1 |
| 0x46 | Message delivered to number 2 |
| 0x47 | Message not delivered to number 2 |
| 0x48 | Message delivered to number 3 |
| 0x49 | Message not delivered to number 3 |
| 0x4a | Message delivered to number 4 |
| 0x4b | Message not delivered to number 4 |
| 0x4c | Message delivered (any number) |
| 0x4d | Message not delivered (all numbers failed) |
| 0x4e | Alarm cancelled by user |
| 0x50 | All tamper sensors OK |
| 0x51 | All faults cleared |
| 0x52 | Power OK (AC restored) |
| 0x54 | Cannot pass info to PCO |
| 0x58 | Remote PgX/PgY disabled |
| 0x59 | Power outage >30 min |

### Event Sources

| Code | Source |
|------|--------|
| 0x00 | Switchboard/control panel |
| 0x01 | Detector 1 |
| 0x02 | Detector 2 |
| 0x03 | Detector 3 |
| 0x11 | Keypad/remote control 1 |
| 0x1b | Phone line |
| 0x1c | Digital bus/serial port |
| 0x21 | Wired sensor 1 |
| 0x22 | Wired sensor 2 |
| 0x7c | Serial port (silent alarm) |

## Record Type e4 - User Event

Memory-stored user event; same byte format as e3 (day/month/hour/min BCD, event type, source).
Request the full log via b5 command; the alarm responds with all stored e4 records followed by `b4 ff` (end of response).
Published to `alarm/event/history` (vs `alarm/event` for live e3/e7).

## Record Type e5 - Alarm Clock Time

Sent periodically; carries the alarm panel's current date and time.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e5 |
| 01 | 1 byte | Month (binary) |
| 02 | 1 byte | Day (binary) |
| 03 | 1 byte | Hour (binary) |
| 04 | 1 byte | Minute (binary) |
| 05 | 1 byte | Checksum |
| 06 | 1 byte | 0xFF |

Example: `e5 04 11 17 07 71 ff` → 11.04 17:07

## Record Type e6 - Switchboard Configuration

Configuration records from the switchboard, sent in bulk after `0x8A` ('*') is pressed in service mode.
The subtype byte (offset 01) determines the record structure.

### Subtype 0x02 — Multi-value setting

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e6 |
| 01 | 1 byte | 0x02 |
| 02 | 1 byte | Setting ID |
| 03 | 1 byte | Value |
| 04 | 1 byte | Checksum |
| 05 | 1 byte | 0xFF |

### Subtype 0x03 — Boolean setting

Same structure as 0x02; value is 0x00 (off) or 0x01 (on).

### Subtype 0x04 — Raw record

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e6 |
| 01 | 1 byte | 0x04 |
| 02+ | variable | Raw data bytes |
| -2 | 1 byte | Checksum |
| -1 | 1 byte | 0xFF |

### Subtype 0x06 — Grouped setting (3-byte form)

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e6 |
| 01 | 1 byte | 0x06 |
| 02 | 1 byte | Group |
| 03 | 1 byte | Index |
| 04 | 1 byte | Value |
| 05 | 1 byte | Checksum |
| 06 | 1 byte | 0xFF |

### Subtype 0x06 — Grouped setting (4+ byte form)

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e6 |
| 01 | 1 byte | 0x06 |
| 02 | 1 byte | Group |
| 03 | 1 byte | Block |
| 04 | 1 byte | Index |
| 05+ | variable | Value bytes (hex) |
| -2 | 1 byte | Checksum |
| -1 | 1 byte | 0xFF |

### Known E6 02 Setting IDs

| ID | Setting | Value encoding |
|----|---------|----------------|
| 0 | Exit delay | Step index: 0=10s, 1=15s, 2=20s, 3=30s, 4=45s, 5=60s, 6=90s, 7=120s |
| 1 | Entry delay | Same step table |
| 2 | Alarm duration | Minutes (direct integer) |
| 3 | PgX output function | 0=Chime, 2=Arm (other values unknown) |
| 4 | PgY output function | 0=Chime, 2=Arm (other values unknown) |

### Known E6 03 Boolean Setting IDs

Value encoding: 0=No, 1=Yes.

| ID | Setting |
|----|---------|
| 0  | ? |
| 1  | ? |
| 2  | ? |
| 3  | ? |
| 4  | ? |
| 5  | ? |
| 6  | ? |
| 7  | ? |
| 8  | ? |
| 9  | ? |

Exact ID→setting mapping requires testing with multiple configurations (toggle one setting, compare changed E6 03 record).

### E6 06 Groups Observed

Fields listed are those after the group byte (which is always buf[2]).

| Group | Extra fields | Notes |
|-------|-------------|-------|
| 0 | block, idx, 3 value bytes | Per-peripheral multi-byte settings |
| 1 | block, idx, 1 value byte | Sensor enable flags (all 1=enabled in this install) |
| 2 | block, idx, 1 value byte | Zone settings |
| 3 | block, idx, 1 value byte | Zone options |
| 4 | block, idx, 4 value bytes | Zone/sensor config; block=zone id (0–9); all-zero = disabled |
| 9 | idx, 1 value byte | System options (3-byte form; idx 3 and 6 = 1, rest = 0) |

Zone 01–10 maps to E6 06 group 4, block 0–9.

### Known Switchboard Settings

`E6 ID` = `0xSubtype / setting_id`.

| Czech | English | Value type | E6 ID |
|-------|---------|------------|-------|
| Příchodové zpoždění | Entry delay | Step index | 0x02 / 1 |
| Odchodové zpoždění | Exit delay | Step index | 0x02 / 0 |
| Doba poplachu | Alarm duration | Minutes | 0x02 / 2 |
| Funkce výstupu PgX | PgX output function | Enum | 0x02 / 3 |
| Funkce výstupu PgY | PgY output function | Enum | 0x02 / 4 |
| Změna tlf. čísel a zprávy v uživ. režimu | Change phone numbers/messages in user mode | Boolean | 0x03 / ? |
| Hlídání rádiového rušení ústředny | Panel radio jamming monitoring | Boolean | 0x03 / ? |
| Pravidelná kontrola spojení s detektory | Regular detector connection check | Boolean | 0x03 / ? |
| Povolení RESETU ústředny | Allow panel RESET | Boolean | 0x03 / ? |
| Ovládání bez kódu povoleno | Control without code allowed | Boolean | 0x03 / ? |
| Částečné zajištění povoleno (F2) | Partial arming allowed (F2) | Boolean | 0x03 / ? |
| Připojená siréna při poplachu | Siren connected during alarm | Boolean | 0x03 / ? |
| Zaznamenání pouze 1. příčiny poplachu | Record only 1st cause of alarm | Boolean | 0x03 / ? |
| Hlasitý tísňový poplach | Loud panic alarm | Boolean | 0x03 / ? |
| Poplach při ztrátě periferie | Alarm on peripheral loss | Boolean | 0x03 / ? |
| Akust. signalizace odchodového zpoždění | Acoustic signaling of exit delay | Boolean | 0x03 / ? |
| Ak. signal. odchod. zp. při částečném zaj. | Acoustic exit delay signaling (partial arm) | Boolean | 0x03 / ? |
| Akustická signalizace příchodového zp. | Acoustic signaling of entry delay | Boolean | 0x03 / ? |
| Hlasité potvrzení zajištění a odjištění | Loud confirmation of arming/disarming | Boolean | 0x03 / ? |
| Poplach sirénou při částečném zajištění | Siren alarm during partial arming | Boolean | 0x03 / ? |
| Poplach bezdrátovou sirénou | Wireless siren alarm | Boolean | 0x03 / ? |
| Upozornění na závadu periferie při zajištění | Peripheral fault warning during arming | Boolean | 0x03 / ? |
| Poplach při zajištění s otevřenou zónou | Alarm when arming with open zone | Boolean | 0x03 / ? |
| Vstup do programování SC+MC/UC | Enter programming via SC+MC/UC | Boolean | 0x03 / ? |
| Bezdrát. detektory do následně zp. smyčky | Wireless detectors in delayed loop | Boolean | 0x03 / ? |
| Zóny 01–10 | Zones 01–10 | Per-zone config | 0x06 / 4 |

## Record Type e7 - Other Event

Time-stamped event; typically repeats e3 content. Request via ba command.

## Record Type e8 - Status Event

Short status event; no timestamp. Appears during service mode transitions and in response to the `b9` command.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e8 |
| 01 | 1 byte | ID |
| 02 | 1 byte | Value |
| 03 | 1 byte | 0xFF |

Examples observed:

| ID | Value | Context |
|----|-------|---------|
| 0x0b | 0x53 | Service mode / user mode |
| 0x0c | 0x64 | User mode |
| 0x0d | 0x22 | Setting time |
| 0x0e | 0x4b | Service mode |
| 0x10 | ? | Response to b9 command |

## Record Type e9 - Service Mode Sensor Event

Observed during service mode sensor testing.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | e9 |
| 01 | 1 byte | Event type |
| 02 | 1 byte | Event source |
| 03 | 1 byte | RF signal |
| 04 | 1 byte | Checksum |
| 05 | 1 byte | 0xFF |

### e9 Event Types

| Code | Event |
|------|-------|
| 0x01 | Immediate zone alarm |
| 0x02 | Delayed zone alarm |
| 0x03 | Fire alarm |
| 0x04 | Silent alarm |
| 0x05 | Attempts exceeded |
| 0x06 | Post-power alarm |
| 0x07 | Tamper alarm |
| 0x08 | Tamper recovered |
| 0x09 | Alarm timeout |
| 0x0a | User canceled |
| 0x0b | Armed |
| 0x0c | Disarmed |
| 0x0d | Partially armed |
| 0x0e | Armed without code |
| 0x0f | Comm failure |
| 0x10 | Comm recovered |
| 0x11 | Malfunction |
| 0x12 | Malfunction recovered |
| 0x13 | AC off 30+ min |
| 0x14 | AC disconnected |
| 0x15 | AC recovered |
| 0x16 | Battery depleted |
| 0x17 | Battery OK |
| 0x18 | Service mode started |
| 0x19 | Service mode ended |
| 0x1a | Remote access started |
| 0x1b | Remote access ended |
| 0x1c | VF receiver jamming |
| 0x1d | Internal comm failure |
| 0x1e | Internal comm recovery |
| 0x1f | Test transmission |

## Record Types ea & eb

Handled similarly to e8 and ec; structure presumed identical though never observed.

## Record Type ec - GSM Configuration

GSM communicator configuration/text in service mode.

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | ec |
| 01 | 1 byte | GSM message type |
| 02 | 1 byte | Settings/message ID |
| 03+ | variable | Payload |
| -2 | 1 byte | Checksum |
| -1 | 1 byte | 0xFF |

### GSM Message Types

| Code | Description |
|------|-------------|
| 0x00 | List terminator |
| 0x01 | Configuration with zero-terminated strings |
| 0x02 | Single value (dump context) |
| 0x03 | Binary configuration (40 checkboxes) |
| 0x2X | Configurable text (ID = X×100) |

### 0x2X Text Message Format

| Offset | Size | Description |
|--------|------|-------------|
| 00 | 1 byte | ec |
| 01 (high) | 4 bits | 0x2 identifier |
| 01 (low) | 4 bits | Base ID |
| 02 | 1 byte | Message ID |
| 03+ | 3 bytes | String length |
| X | 3 bytes | Character data |
| -5 | 1 byte | 0x00 |
| -4 | 1 byte | 0x00 |
| -2 | 1 byte | Checksum |
| -1 | 1 byte | 0xFF |

### GSM Commands (Service Mode)

| Command | Function |
|---------|----------|
| `ec 40 05 19 ff` | Dump customizable texts |
| `ec 40 07 36 ff` | Dump GSM configuration |

## Record Type fe - Unknown

Observed on user mode exit in format `fe ff`.
