**English** | [Русский](COOLING-WEB-EVIDENCE.ru.md)

# Fan replacement evidence and next diagnostic step

17 October 2026. This record separates published replacements, manufacturer
specifications and hypotheses about PCB 2060500612 / Ver:5.40. No firmware changes.

## What the linked replacement actually demonstrates

[Spot on Tech, 31 May 2022](https://spotontech.nl/blog/tp-link-poe-switch-geluidsoverlast-oplossen/)
reports a successful TL-SG1218MPE fan replacement. Its photograph identifies
**Sunon EF40201BX-Q18C-F99** and **Noctua NF-A4x20 FLX**. The hardware revision
is not established. The image called a connection diagram in the article is
actually a Sunon model-number decoder, not an electrical pinout. This is evidence
of a replacement on that unit, not a V5.40 circuit diagram or software speed control.

## Manufacturer facts

- [NF-A4x20 PWM specifications](https://www.noctua.at/en/products/nf-a4x20-pwm/specifications):
  rated 12 V, starting voltage 8 V; black GND, yellow Vcc, green RPM, blue PWM.
- [PWM model manual](https://cdn.noctua.at/media/noctua_nf_a4x20_pwm_manual_en_web.pdf):
  a standard three-pin connection runs the fan at full speed unless voltage control
  reduces its supply. An unconnected fourth pin alone does not explain failure to start.
- [Noctua PWM white paper](https://noctua.at/pub/media/wysiwyg/Noctua_PWM_specifications_white_paper.pdf):
  tach output is open collector, two pulses per revolution. It is not a dedicated
  binary rotor-lock signal.
- The owner's close-up marking matches **NCE9435A**. The
  [manufacturer datasheet](https://www.ncepower.com/upload/cn/propdf/NCE9435A.pdf)
  identifies a P-channel power MOSFET. Its physical connection to GPIO27 or either
  fan supply has not been established from the photograph.

## Reports that need qualification

[An author's TP-Link modification](https://www.reddit.com/r/TPLink_Omada/comments/1knakgs/switch_quite_fan_mod_guide/)
describes rotor-lock feedback and connector differences from Noctua. This cannot
establish the feedback type or pin order on this V5.40 board. Do not copy its
pin swaps or alarm-bypass wiring into this project as verified instructions.

The [V5 forum thread](https://community.tp-link.com/en/business/threads/topic/859480)
contains both the V5 owner's replacement report and another contributor's
SG3428MP modification. Support's broad statement about software noise reduction
does not prove absence of a controllable output on our board.

## Second-fan hypothesis

The owner proposed that the approximately 150 W PoE threshold enables a second
fan while the first runs continuously. This fits a binary output conceptually,
but is not a demonstrated connection. The stock controller writes GPIO27=0 at
raw PoE sum >=1501, GPIO27=1 below 1460, and retains its state in between;
see [code evidence](COOLING.md).

The earlier active `cool test 0;cool status` already confirmed GPIO27=0, but no
clear second-fan start was observed. The test's 100 raw ticks have not been
calibrated against elapsed seconds. Do not claim either a successful fan enable
or a conclusively excluded second-fan function from that observation.

The owner's later phrase “тот что не меняли” is ambiguous: it may describe an
unchanged stock fan or the fan that did not react. The exact installed pair needs
clarification; do not diagnose a defective Noctua by assuming both are Noctua.

## Next step without opening the enclosure

Use the installed v0.1.2 and take two **read-only** `cool status` outputs about
10 seconds apart. Record the actual interval. For an interval T and a positive
tick difference D, estimate the 100-tick duration as `100*T/D` seconds. This
calibrates the timer only; it does not identify the fan circuit. These readings
are planned, not completed, and need no new BIN or register writes.

If the hold is already ample, repeating the same GPIO level offers little new
evidence. If it is very short, a longer bounded test can be considered separately.
The owner declined further disassembly and voltage measurements for now.
RPM, per-fan health, actual supply voltage and output-to-fan mapping remain unknown.
