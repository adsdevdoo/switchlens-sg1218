[English](SYSTEM-INFO.md) | **Русский**

# Источники полей System Info

**Актуальный статус:** рабочая v0.1.1 загружается, отвечает на UART help и
возвращает динамический JSON; [доказательства](../docs/evidence/2026-10-17-switchlens/README.ru.md). Ниже — исторический
отчёт 16–17 октября до первого успешного запуска. Его прежние планы и запреты
не являются новыми условиями продолжения; восстановление и нагрузочные
проверки остаются открытыми. [Исходный TXT](SYSTEM-INFO.txt) сохранён без изменений.

```text
Полная информация с первого System Info скриншота — 2026-10-16
Проверено: прочитано содержимое исходного скриншота84c6b5bc-2698-42e0-85ed-8316311f0cb3.png,
сверено с JS страницы в BIN@0x99cce и обработчиком@0x37388..0x376f8.
Значения MAC/IP пользователя не перенесены в примеры или отчёт.

Поле экрана          Поле JSON               Источник info_ds
Device Description   system.description      descriStr
MAC Address          system.mac              macStr
IP Address           system.ip_address       ipStr
Subnet Mask          system.subnet_mask      netmaskStr
Default Gateway      system.default_gateway  gatewayStr
Firmware Version     system.firmware_version firmwareStr
Hardware Version     system.hardware_version hardwareStr

Все семь полей включены в проект схемы. Значения в примере null, а не реальные
данные или HTML-заглушки. Текст прошивки и аппаратной версии сохраняется целиком,
как в панели. Строку hardware_version не урезать до одного номера ревизии.
system.name оставлен как совместимый alias description, значения должны совпадать.
system.model — отдельное идентификационное поле; не извлекать модель из редактируемого
description. Источник модели требует отдельной нормализации hardware string.

Проверено статически:
- descriStr:page@374a8 вызывает BFC51370->BFC51E18; последняя копирует33байта
  из BF0015FC либо B41FE008 по флагуBF0015F0 и ставит NUL в offset32.
  Сохранить содержимое максимум32байта до NUL, экранировать для JSON.
- macStr:page@37490 вызывает BFC51378, далее BFC280B0 с unit0; форматирование
  BFC314B8. Это getter, не MAC-заглушка из HTML.
- ipStr/netmaskStr/gatewayStr:page@374b8 вызывает BFC50FBC;
  getter file48fbc..4902c копирует по4байта из BF016D3A/BF016D3E/BF016D42.
  Преобразование для страницы через BFC3147C. При реализации учитывать порядок байт.
- firmwareStr:page@374e4 вызывает BFC51030, копирует64байта из BF014348.
  Ограничивать чтение64байтами; не предполагать NUL за пределами буфера.
- hardwareStr:page@374ec вызывает BFC512C0, строка BFCE02F4/file0xd82f4.

Проверено:ресурс HTML содержит демонстрационные TL-SG105E/MAC/старую версию,
а loadValue заменяет их данными info_ds. Никогда не использовать эти заглушки
как информацию о работающем коммутаторе. Значения получать через найденные getters.

Это проект JSON и результаты анализа. Штатная прошивка endpoint stats.json пока
не содержит. Никаких запросов/изменений на устройстве не выполнялось.
```
