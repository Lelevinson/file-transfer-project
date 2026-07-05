import time
from pystray import Icon
from PIL import Image

# 1) an image, so the tray icon is actually visible
image = Image.new("RGB", (64, 64), (0, 120, 220))

notify = Icon(name="test_notif", icon=image)
notify.run_detached()
time.sleep(5)
notify.notify(message="Test", title="Notification")
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    notify.remove_notification()
    notify.stop()
