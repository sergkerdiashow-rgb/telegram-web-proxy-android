#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'Telegram')


def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one match, got {count}')
    path.write_text(text.replace(old, new, 1))

# Keep the reliability transport aligned with the Android 12.10.1 compile SDK APIs.
transport = root / 'TMessagesProj/src/main/java/org/telegram/messenger/WebProxyTransport.java'
replace_once(
    transport,
    'view.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_IMPORTANT, false, -1);',
    'view.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_IMPORTANT, false);',
    'WebView renderer priority signature',
)
replace_once(
    transport,
    'if (callback != null) callback.invoke(origin, false, false, -1);',
    'if (callback != null) callback.invoke(origin, false, false);',
    'WebView callback signature',
)

# Make WEB keep-alive mandatory while WEB proxy is selected and start it via
# startForegroundService on Android 8+, so the promotion is not merely deferred
# until the next app restart.
app = root / 'TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java'
text = app.read_text()
needle = '''        if (enabled) {\n            try {\n                applicationContext.startService(new Intent(applicationContext, NotificationsService.class));\n            } catch (Throwable ignore) {\n\n            }\n        } else {\n            applicationContext.stopService(new Intent(applicationContext, NotificationsService.class));\n        }\n'''
replacement = '''        if (isWebProxySelected()) {\n            // WEB has no network path when this process dies, so keep-alive is not\n            // optional for the WEB transport even if the legacy preference was off.\n            enabled = true;\n        }\n        if (enabled) {\n            try {\n                Intent serviceIntent = new Intent(applicationContext, NotificationsService.class);\n                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && isWebProxySelected()) {\n                    applicationContext.startForegroundService(serviceIntent);\n                } else {\n                    applicationContext.startService(serviceIntent);\n                }\n            } catch (Throwable error) {\n                FileLog.e(error);\n            }\n        } else {\n            applicationContext.stopService(new Intent(applicationContext, NotificationsService.class));\n        }\n'''
if text.count(needle) != 1:
    raise SystemExit(f'ApplicationLoader start service: expected one match, got {text.count(needle)}')
app.write_text(text.replace(needle, replacement, 1))

# Re-evaluate the foreground service immediately whenever the selected proxy changes.
cm = root / 'TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java'
text = cm.read_text()
start = text.find('    public static void setProxySettings(boolean enabled, String address, int port, String username, String password, String secret) {')
if start < 0:
    raise SystemExit('ConnectionsManager.setProxySettings not found')
brace = text.find('{', start)
depth = 0
end = None
for i in range(brace, len(text)):
    ch = text[i]
    if ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end = i
            break
if end is None:
    raise SystemExit('ConnectionsManager.setProxySettings closing brace not found')
method = text[start:end+1]
if 'ApplicationLoader.startPushService();' not in method:
    method = method[:-1] + '''\n        // Apply WEB process residency immediately on proxy selection/change instead of\n        // waiting for a later app restart. Disabling WEB also drops the WEB-only FGS.\n        ApplicationLoader.startPushService();\n    }'''
    text = text[:start] + method + text[end+1:]
cm.write_text(text)

# Promote before the potentially expensive Telegram application init. Android requires
# a service started with startForegroundService() to call startForeground quickly.
svc = root / 'TMessagesProj/src/main/java/org/telegram/messenger/NotificationsService.java'
text = svc.read_text()
old_oncreate = '''    @Override\n    public void onCreate() {\n        super.onCreate();\n        ApplicationLoader.postInitApplication();\n    }\n'''
new_oncreate = '''    @Override\n    public void onCreate() {\n        super.onCreate();\n    }\n'''
if text.count(old_oncreate) != 1:
    raise SystemExit(f'NotificationsService onCreate: expected one match, got {text.count(old_oncreate)}')
text = text.replace(old_oncreate, new_oncreate, 1)
needle = '''    @Override\n    public int onStartCommand(Intent intent, int flags, int startId) {\n        // Upstream never called startForeground here. A WEB proxy is different:\n'''
if text.count(needle) != 1:
    raise SystemExit(f'NotificationsService onStartCommand: expected one match, got {text.count(needle)}')
text = text.replace(needle, '''    @Override\n    public int onStartCommand(Intent intent, int flags, int startId) {\n        // Promote first; postInitApplication can be much heavier on a cold process and\n        // must not consume Android's startForegroundService deadline.\n        // Upstream never called startForeground here. A WEB proxy is different:\n''', 1)
# Insert application init after the promotion/stopForeground branch, immediately before return.
needle = '''        return START_STICKY;\n    }\n'''
if text.count(needle) != 1:
    raise SystemExit(f'NotificationsService return: expected one match, got {text.count(needle)}')
text = text.replace(needle, '''        ApplicationLoader.postInitApplication();\n        return START_STICKY;\n    }\n''', 1)
svc.write_text(text)

print('WEB reliability integration patch applied')
