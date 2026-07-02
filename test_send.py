from whatsapp_sender import WhatsAppSender
from datetime import datetime

def log(msg):
    with open("logs.txt", "a") as f:
        f.write(f"{datetime.now()} - {msg}\n")

s = WhatsAppSender()

try:
    s.start()
    log("WhatsApp started in test_send")

    s.send_text("919391187938", "Test Message")
    log("Test text sent")

    s.send_image("919391187938", "img.jpeg", "Hi Ra")
    log("Test image sent")

except Exception as e:
    log(f"Test failed: {e}")

finally:
    s.quit()
    log("WhatsApp closed in test_send")