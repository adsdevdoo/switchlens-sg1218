[English](JSON-CONTRACT.md) | **Русский**

# Решения контракта JSON

**Актуальный статус:** рабочая v0.1.1 загружается, отвечает на UART help и
возвращает динамический JSON; [доказательства](../docs/evidence/2026-10-17-switchlens/README.ru.md). Ниже — исторический
отчёт 16–17 октября до первого успешного запуска. Его прежние планы и запреты
не являются новыми условиями продолжения; восстановление и нагрузочные
проверки остаются открытыми. [Исходный TXT](JSON-CONTRACT.txt) сохранён без изменений.

```text
Проект контракта stats.json v1 — не существующий endpoint и не реальные показания
Обновлён: полный набор согласован 2026-10-16.
Точная структура и обязательные поля: stats.schema.json (JSON Schema2020-12).
Шаблон без показаний: stats.empty-example.json. Карта доказательств: metric-sources.json.
Ниже исходные принципы; при отличии структуры приоритет имеет схема.

Цель: GET /stats.json -> application/json, Cache-Control: no-store.
Динамический ответ из RAM/ASIC; не создавать и не обновлять файл во флеше.
Один общий запрос на все порты и PoE. Первоначальный интервал exporter:15секунд (проектное значение, испытать под нагрузкой).
Не включать операции записи, reset counters, изменение портов или PoE.

Корень:
 schema_version:1
 uptime_seconds:null до доказательства единицы времени
 uptime_ticks_raw: uint32 из BF002E90; оборачивается, не называть секундами
 poe: budget_w, consumption_w, remaining_w (числа/null); источник штатный RAM-кэш
 ports: массив18 физических логических портов, внешние номера1..18

Порт:
 port:1..18 (mapping на панель подтвердить стендом)
 link_up:boolean|null, speed_mbps:number|null (источники статуса отдельно привязать)
 rx_bytes, tx_bytes: decimal strings|null, чтобы контракт сохранял точность uint64
 tx_drop_packets: decimal string|null, исходный32-битный счётчик
 rx_discards:null до нахождения подтверждённого источника
 rx_good_packets,tx_good_packets,rx_bad_packets,tx_bad_packets: decimal strings|null;
   имена соответствуют web, не обещают эквивалентности IF-MIB
 poe:null для порта без PoE, иначе объект:
   enabled:boolean|null
   status_code:integer|null, status:string|null
   power_w:number|null, current_ma:number|null, voltage_v:number|null
   pd_class:integer|null, pd_class_raw:integer|null
   priority_code:integer|null
   power_limit_mode:"auto"|"fixed"|null, power_limit_w:number|null
   measurements_valid:boolean|null

Правила реализации (проектные, а не доказанное поведение прошивки):
- Ошибка чтения метрики -> null, никогда не маскировать нулём.
- Для PoE сохранять сырой код класса и статуса; неизвестный код не переименовывать в OFF.
- При недоказанной валидности измерений measurements_valid:null; не обещать свежесть кэша.
- Budget/remaining брать с явным описанием семантики: web ограничивает consumption бюджетом; для диагностики желательно сохранить также raw consumption. Не трактовать UI-clamp как измерение.
- Десятичные строки uint64 конвертировать собственным коротким кодом, не полагаться на поддержку %llu штатным форматтером.
- Снимок не считать атомарным: порты читаются последовательно. Не удерживать прерывания выключенными на время JSON/сети.
- Не аллоцировать весь JSON на стеке или heap. Короткие фрагменты, фиксированный буфер, контроль ошибок отправки.
- Клиент принимает только целый JSON и ожидаемую schema_version; HTML login page — ошибка сбора.
- Частота опроса, максимальное время ответа, влияние на PoE, сетевые таймауты и расход стека — обязательные стендовые проверки.

Этот контракт — заготовка для реализации после восстановления стенда. Поля с неизвестным источником не объявляются готовыми.


РАСШИРЕНИЯ СОГЛАСОВАННОГО НАБОРА
system: model, hardware_version, firmware_version, name, mac, uptime_seconds, uptime_ticks_raw.
ports[]: admin_enabled, link_up, speed_config_code, speed_actual_code, speed_mbps,
duplex, flow_control_configured, flow_control_active, lag_id.
ports[].counters: все счётчики из предыдущей версии, плюс отдельные RX/TX unicast,
multicast, broadcast. Счётчики перемещены в объект counters.
ports[].poe: предыдущие поля, плюс extend_enabled и объект recovery.
recovery: enabled, ping_address, startup_delay_seconds, interval_seconds,
failure_threshold, break_seconds, failures_current, reboots_raw, pings_raw.
poe в корне: budget_w, consumption_w, remaining_w, consumption_raw, recovery_enabled.
Поле status — строка с расшифровкой status_code; неизвестный код сохраняется,
строковая расшифровка остаётся null. Пустая строка и null не взаимозаменяемы.

Все поля обязательны в структуре, но значения могут быть null, если неизвестны.
poe:null у порта означает неприменимость PoE; объект с null-измерениями — поддержку
PoE с недоступными показаниями. Пример использует предполагаемую карту16+2;
проверить на стенде. Остальные примеры не содержат реальных показаний.
Узлы system и recovery могут содержать строки: сериализатор обязан экранировать
кавычки, обратные слеши и управляющие символы. Не вставлять sysName напрямую.
Предел строки128символов в схеме — проектный лимит, не найденный размер RAM-поля.
lag_id:null означает неизвестно; смысл нулевого кода подтвердить перед нормализацией.

ОСОБЕННОСТИ AUTO RECOVERY
Проверено по справке образа: Failures сбрасывается на успешном ping/перезапуске PD
(file0xba452); Reboots и Total Pings сбрасываются при достижении9999/перезапуске
коммутатора (file0xba5af,0xba6be). Точные границы и код сброса ещё не проверены.
Поэтому отдаём failures_current, reboots_raw, pings_raw как gauge; не называем
их монотонными Prometheus counter и не применяем rate к failures_current.
Показания относятся к механизму свитча, не ко всем ping и перезагрузкам Raspberry Pi.
Не включать Auto Recovery для заполнения этих полей.

ВЫЧИСЛЕНИЯ EXPORTER (проект)
Скорость трафика:8*delta(bytes)/delta(time); загрузка отдельно RX/TX относительно
фактической скорости линка. Не складывать RX+TX для процента full-duplex линка.
Проверять сброс/переполнение/смену скорости; не превращать неизвестный разрыв
в гигантский всплеск. Не обещать точную64битную нормализацию до стендового теста.
Доля broadcast/multicast — по дельтам соответствующих счётчиков; при нулевом
знаменателе значение недоступно. Знаменатель — сумма unicast+multicast+broadcast.
PoE budget utilization: consumption/budget при budget>0.
Энергия — приблизительное интегрирование валидных power_w по времени; интервалы
с пропусками не заполнять нулём, выдавать покрытие наблюдений отдельно.
События линка/PoE — наблюдаемые переходы между опросами, не аппаратный журнал.
Сбор начально каждые15секунд; фактическую нагрузку и пропуски измерить на стенде.

НЕ ВКЛЮЧАТЬ КАК ГОТОВЫЕ МЕТРИКИ
Температура в градусах, fan RPM, CPU, RAM, SFP DOM и причина перезагрузки:
подтверждённых источников нет. RX discards зарезервирован как null.
Cable Test не запускать из endpoint: наличие результата теста не доказывает,
что его получение пассивно и не влияет на линк.

ДОПОЛНЕНИЕ MIB И ПЕТЛИ
Добавлены35полей counters:21счётчик диагностики и14интервалов RX/TX размеров.
Семантика новых полей — гипотеза по внешней карте RTL838x; источник и чтение
проверены статически. Уточнение для experimental-1: адаптер выдаёт эти значения
экспериментально, с ограничениями из docs/FIRMWARE.md; стенд должен проверить
семантику, разрядность и side effects. Селектор58 строго
исключён: tx_packets_256_511 допускает только null в текущем проекте схемы.
loop_prevention хранит enabled и сырые RLDP/RLPP/selfLoop маски; активный режим
ещё не установлен. Это не поле blocked и не обещание детектировать петли при
выключенной защите. Подробности в MIB-LOOPS-FOLLOWUP.txt.

SYSTEM INFO
Все7полей первого скриншота включены в system; см.SYSTEM-INFO.txt.
Добавлены description, ip_address, subnet_mask, default_gateway.
name=description (alias); model не брать из редактируемого description.
Сохранять firmware_version/hardware_version целиком.
```
