**English** | [Русский](messages.ru.md)

# Owner messages and test materials

Session date: 17 October 2026. Russian quotations below are the owner's original
words; English translations are provided for readers. Connecting explanations
are editorial, not messages attributed to the owner. Exact request times were
not recorded. This is a selected record, not the full conversation.

## Before enabling the CLI

> я выставил 3.3 на адаптере

Translation: “I set 3.3 on the adapter.”

> нажимаю - ничего может я плохо резистор припаял, а должно быть что-то?

Translation: “I press it and nothing happens; maybe I soldered the resistor badly?
Should something happen?”

> и что делаем тогда дальше?

Translation: “So what do we do next?”

The final question included [stock PuTTY boot output](01-stock-uart.png).
Output was readable, but no CLI prompt appeared. Static analysis later found
the stock dispatcher disabled. The silence did not prove a bad RX connection.

> а мы можем включить это в нашей прошивке? или что нужно ?

Translation: “Can we enable it in our firmware, or what is needed?”

## Package preparation and review

> ты все запушил? bin у тебя новый с stats + uart?

Translation: “Did you push everything? Is your new BIN stats + UART?”

> осталось его прошить?

Translation: “Is flashing it all that remains?”

> мы ничего не напортачили, сделай финальную проверку

Translation: “Make a final check that we haven't messed anything up.”

The v0.1.1 package with two CLI instructions and the original JSON payload was
prepared and published. The [offline review](../../FINAL-CHECK.md) preserves that
stage's findings; this explanatory sentence is not an additional owner quotation.

## Upgrade and boot

The owner supplied [System Info](02-system-info.png),
[upgrade form](03-upgrade-form.png), [5% progress](04-upgrade-progress.png),
[reboot](05-reboot-start.png), [completed boot with RTK#](06-boot-rtk.png),
and [full pasted boot text](boot-after-upgrade.txt).

```text
check runtime img
Image erase all!
Image recover done!
check runtime img
go to runtime addr 0xb4008010
```

The subsequent text includes SignCheck Pass, RTK# and code init completion.

## Input test

The owner typed help and supplied the response and [screenshot](07-uart-help.png).
The complete original command list is in [uart-help.txt](uart-help.txt).

```text
RTK# help
?       - alias for 'help'
acl     - acl configuration
help    - print online help
mib     - to get switch mib counter
```

Listing a command in help does not mean it was executed during the test.

## JSON test

The owner opened `/stats.json`, supplied the [browser screenshot](08-stats-json.png)
and [first complete attachment](stats-01-submitted.md), then supplied the
[second attachment](stats-02-submitted.md) after a repeat-request suggestion.
There is no separate confirmation of an exactly 30-second interval. Changes were
established by JSON comparison without calculating per-second rates.

## Publication request

> сделай подробное описание для json и выложи наши успешные результаты в github с сообщениями и скринами что я делал

Translation: “Make a detailed description for the JSON and publish our successful
results on GitHub, with messages and screenshots of what I did.”

The owner subsequently requested English-first documentation with a Russian
switch and working-firmware status, then asked for everything to be pushed.
These requests are fulfilled by the paired guides and evidence in this repository.
