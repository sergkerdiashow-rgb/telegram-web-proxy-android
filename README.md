# Telegram Android WEB Proxy POC

Экспериментальная реконструкция Android-клиента для нового Telegram WEB proxy по публичным материалам `telegramdesktop/tproxy-server` (`ANDROID.md`, `PROTOCOL.md`) поверх официального `DrKLO/Telegram`.

**Это не официальный APK Telegram.** Исходная база зафиксирована на commit `45ab8f4308496e1f01026a97fcdb0d58a5274474`, чтобы патч не применялся молча к изменившемуся коду.

GitHub Actions автоматически:

- восстанавливает исходники POC из `chunks/`;
- проверяет официальные capability test vectors;
- скачивает зафиксированный Telegram Android;
- ставит Android SDK 35, Build-tools 35.0.0, NDK 27.2.12479018 и CMake 3.10.2;
- делает dry-run патча;
- добавляет тип `WEB Proxy` и Android WebView transport;
- собирает `:TMessagesProj_App:assembleAfatDebug`;
- публикует `app.apk` как artifact.

В POC WEB proxy использует hostname + MTProxy secret, внешний carrier идёт через приватный WebView к HTTPS/WSS relay, а tgnet подключается только к loopback sidecar. При отказе WebView транспорт сделан fail-closed, чтобы не было тихого прямого обхода WEB proxy.

Первоисточники:
- https://github.com/telegramdesktop/tproxy-server/blob/master/ANDROID.md
- https://github.com/telegramdesktop/tproxy-server/blob/master/PROTOCOL.md
- https://github.com/telegramdesktop/tproxy-server
- https://github.com/DrKLO/Telegram

После успешной сборки: **Actions → Build Telegram WEB Proxy Android POC → Artifacts → telegram-web-proxy-android-poc**.
