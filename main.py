import time
from datetime import datetime
from whatsapp_sender import WhatsAppSender
from db import insert_message, get_due_pending_messages, mark_as_sent, mark_as_failed

# ===== SIMPLE LOG FUNCTION =====
def log(msg):
    with open("logs.txt", "a") as f:
        f.write(f"{datetime.now()} - {msg}\n")


# ===== ASK MESSAGE ONLY ONCE =====
common_message = input("💬 Enter message to send to ALL contacts: ").strip()
log("Program started")


# ===== COLLECT MULTIPLE MESSAGES =====
tasks = []
print("📝 Enter messages one by one. Type 'done' as phone to finish.\n")

while True:
    phone = input("📱 Phone (+91...) or 'done': ").strip()
    if phone.lower() == "done":
        log("Input collection finished")
        break

    _ = input("💬 Message (ignored): ").strip()
    image_path = input("🖼️ Image path: ").strip()
    target_time = input("⏰ Time (HH:MM): ").strip()

    try:
        hour, minute = map(int, target_time.split(":"))
    except:
        print("❌ Bad time format, skipped\n")
        log("Bad time format entered")
        continue

    insert_message(phone, common_message, image_path, hour, minute)
    tasks.append((phone, target_time, hour, minute))
    print("✅ Stored\n")
    log(f"Stored message for {phone} at {target_time}")

if not tasks:
    print("⚠️ Nothing to send. Exit.")
    log("No tasks found - exiting")
    exit()

# ===== PREPARE SCHEDULER =====
all_minutes = sorted({(h, m) for _, _, h, m in tasks})
print(f"\n⏳ {len(tasks)} message(s) queued. Waiting...")
log(f"{len(tasks)} messages queued")

processed_slots = set()
sender = None  # lazy ini

try:
    while True:
        now = datetime.now()
        print(f"🕒 Now: {now.strftime('%H:%M:%S')}")

        due_slots = [
            (h, m) for (h, m) in all_minutes
            if (now.hour > h or (now.hour == h and now.minute >= m))
            and (h, m) not in processed_slots
        ]

        for (h, m) in due_slots:
            messages = get_due_pending_messages(h, m)
            print(f"📋 Slot {h:02d}:{m:02d} → {len(messages)} message(s)")
            log(f"Processing slot {h}:{m}")

            if messages and sender is None:
                sender = WhatsAppSender()
                sender.start()
                log("WhatsApp started")

            for msg in messages:
                msg_id, phone, message, image_path = msg
                try:
                    print(f"📤 Sending to {phone}...")
                    log(f"Sending to {phone}")

                    # ===== STEP 1: SEND TEXT =====
                    sender.send_text(phone, message)

                    # ===== STEP 2: WAIT =====
                    time.sleep(2)

                    # ===== STEP 3: SEND IMAGE =====
                    sender.send_image(phone, image_path)

                    mark_as_sent(msg_id)
                    print("✅ Sent")
                    log(f"Sent successfully to {phone}")

                except Exception as e:
                    mark_as_failed(msg_id, str(e))
                    print(f"❌ Failed: {e}")
                    log(f"Failed for {phone}: {e}")

            processed_slots.add((h, m))

        if len(processed_slots) == len(all_minutes):
            print("🏁 All scheduled messages processed. Exiting...")
            log("All tasks completed")
            break

        time.sleep(15)

finally:
    if sender:
        sender.quit()
        log("WhatsApp closed")