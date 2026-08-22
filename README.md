# Telegram Android WEB Proxy POC

Экспериментальная реконструкция Android-клиента для нового Telegram WEB proxy по публичным материалам `telegramdesktop/tproxy-server` (`ANDROID.md`, `PROTOCOL.md`) поверх официального `DrKLO/Telegram`.

**Это не официальный APK Telegram.** Исходная база зафиксирована на commit `45ab8f4308496e1f01026a97fcdb0d58a5274474`, чтобы патч не применялся молча к изменившемуся коду.

## Что собирает CI

GitHub Actions автоматически:

- восстанавливает исходники POC из `chunks/`;
- проверяет официальные capability test vectors;
- скачивает зафиксированный Telegram Android;
- ставит Android SDK 35, Build-tools 35.0.0, NDK 27.2.12479018 и CMake 3.10.2;
- делает dry-run патча;
- добавляет тип `WEB Proxy` и Android WebView transport;
- компилирует патченную Java отдельным шагом, чтобы ошибки в патче всплывали до часовой нативной сборки;
- собирает `:TMessagesProj_App:assembleAfatDebug` **только для arm64-v8a**;
- публикует `app.apk` как artifact.

Сборка ограничена одной ABI намеренно: `TMessagesProj_App` управляет только упаковкой, а нативные CMake-таски живут в `TMessagesProj`. Без `abiFilters` в библиотечном модуле AGP собирает все четыре ABI, и раннер GitHub падает с `No space left on device` при линковке x86.

## Что означает «работает»

APK ставится на устройство arm64 (почти все современные телефоны). Внутри появляется третий тип прокси — `WEB Proxy` — в Settings → Data and Storage → Proxy → Add Proxy: hostname + MTProxy secret, без порта.

WEB proxy использует hostname + MTProxy secret, внешний carrier идёт через приватный WebView к HTTPS/WSS relay, а tgnet подключается только к loopback sidecar. При отказе WebView транспорт сделан fail-closed: tgnet получает неиспользуемый loopback-порт и **не** уходит напрямую в Telegram.

Из этого следует главное ограничение: чтобы WEB proxy реально соединялся, нужен работающий relay `tproxy-server` на этом hostname, отдающий bridge-страницу по `https://<host>/?bridge=<capability>`. Без такого сервера тип прокси настраивается и сохраняется, но соединение не поднимется — это ожидаемое поведение fail-closed, а не дефект сборки.

Требования к устройству: Android System WebView должен поддерживать `WEB_MESSAGE_LISTENER`, `WEB_MESSAGE_ARRAY_BUFFER` и `DOCUMENT_START_SCRIPT`. Транспорт работает только пока приложение на переднем плане.

## Первоисточники

- https://github.com/telegramdesktop/tproxy-server/blob/master/ANDROID.md
- https://github.com/telegramdesktop/tproxy-server/blob/master/PROTOCOL.md
- https://github.com/telegramdesktop/tproxy-server
- https://github.com/DrKLO/Telegram

После успешной сборки: **Actions → Build Telegram WEB Proxy Android POC → Artifacts → telegram-web-proxy-android-poc-arm64**.
