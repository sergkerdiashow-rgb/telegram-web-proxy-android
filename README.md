# Telegram Android WEB Proxy POC

Экспериментальная реконструкция Android-клиента для нового Telegram WEB proxy по публичным материалам `telegramdesktop/tproxy-server` (`ANDROID.md`, `PROTOCOL.md`) поверх официального `DrKLO/Telegram`.

**Это не официальный APK Telegram.** Исходная база зафиксирована на commit `4e1a61eca6c9b6ee3aa9c35cf8c70554750f2439` (Telegram Android 12.10.0), чтобы патч не применялся молча к изменившемуся коду.

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

## Лицензия и происхождение кода

Патч в `chunks/` — производная работа от `DrKLO/Telegram`, который распространяется под GNU General Public License версии 2. Поэтому этот репозиторий тоже под **GPL-2.0**, полный текст в [LICENSE](LICENSE).

Исходники Telegram сюда не скопированы: CI забирает их с зафиксированного коммита `4e1a61eca6c9b6ee3aa9c35cf8c70554750f2439` официального репозитория. Соответствующий исходный код собранного APK — это данный репозиторий плюс тот коммит.

Практическое следствие: если вы раздаёте собранный APK кому-то ещё, получатели по GPL-2.0 имеют право на соответствующие исходники. Публичный репозиторий закрывает это требование.

Отдельно от лицензии: имя, логотип и оформление Telegram остаются товарными знаками их владельца. GPL разрешает изменять и распространять код, но не даёт прав на бренд — для распространения сборки нужны собственное название и иконка.

**Что нельзя класть в этот репозиторий:** файл keystore и его пароли (только секреты репозитория `SIGNING_KEYSTORE_BASE64`, `SIGNING_KEYSTORE_PASSWORD`, `SIGNING_KEY_ALIAS`, `SIGNING_KEY_PASSWORD`) и собственные `api_id` / `api_hash` с my.telegram.org.

## Первоисточники

- https://github.com/telegramdesktop/tproxy-server/blob/master/ANDROID.md
- https://github.com/telegramdesktop/tproxy-server/blob/master/PROTOCOL.md
- https://github.com/telegramdesktop/tproxy-server
- https://github.com/DrKLO/Telegram

После успешной сборки: **Actions → Build Telegram WEB Proxy Android POC → Artifacts → telegram-web-proxy-android-poc-arm64**.
