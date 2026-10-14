from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup
import sqlite3

# التوكن النظيف الخاص بك
BOT_TOKEN = "8805697936:AAHQ0NM8GXv09-8_Me4BaTdMYpR72QqsIvk"

# إعداد قاعدة البيانات التلقائية لحفظ الأسماء مجاناً
conn = sqlite3.connect("names_database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        user_id INTEGER,
        full_name TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# تشغيل البوت عبر مكتبة بايثون
app = Client("name_history_bot", bot_token=BOT_TOKEN, api_id=2040, api_hash="b18441a1d107e11e3100d1858c14b74a")

# دالة فحص وحفظ الاسم إذا تغير
def save_user_name(user_id, current_name):
    cursor.execute("SELECT full_name FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    last_saved = cursor.fetchone()
    if not last_saved or last_saved[0] != current_name:
        cursor.execute("INSERT INTO history (user_id, full_name) VALUES (?, ?)", (user_id, current_name))
        conn.commit()

# رصد تلقائي لأسماء الأعضاء في المجموعات والخاص لتخزينها
@app.on_message(filters.group | filters.private, group=-1)
async def auto_track(client, message: Message):
    # حماية صارمة: إذا كانت الرسالة من بوت أو من البوت نفسه، يتم تجاهلها فوراً لمنع التكرار
    if not message.from_user or message.from_user.is_bot:
        return
        
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    full_name = f"{first} {last}".strip()
    if full_name:
        save_user_name(message.from_user.id, full_name)

# تفعيل أزرار المنيو الشبيهة بالبوت الروسي عند إرسال /start أو /menu
@app.on_message(filters.command(["start", "menu"]))
async def send_welcome_menu(client, message: Message):
    if not message.from_user or message.from_user.is_bot: 
        return
        
    await message.reply(
        "👋 أهلاً بك أبو هارف في بوت استعراض الأسماء المجاني 100% بدون كرستالات!\n\n"
        "اضغط على الأزرار أدناه للاستخدام:",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["🔍 فحص الأسماء بالرد", "ℹ️ مساعدة"],
                ["📊 إحصائيات البوت"]
            ],
            resize_keyboard=True
        )
    )

# استقبال أمر فحص الأسماء أو الضغط على زر الفحص
@app.on_message(filters.command("history") | filters.regex("🔍 فحص الأسماء بالرد"))
async def check_history(client, message: Message):
    if not message.from_user or message.from_user.is_bot: 
        return
        
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user

    cursor.execute("SELECT full_name, timestamp FROM history WHERE user_id = ? ORDER BY timestamp ASC", (target.id,))
    records = cursor.fetchall()
    
    if not records:
        await message.reply("❌ هذا المستخدم لم أقم بحفظ أي أسماء له في قاعدتي بعد.")
        return
        
    reply_text = f"👤 **تاريخ أسماء المستخدم ({target.id}):**\n\n"
    for i, row in enumerate(records, 1):
        reply_text += f"{i}. `{row[0]}`\n"
        
    await message.reply(reply_text)

# زر المساعدة
@app.on_message(filters.regex("ℹ️ مساعدة") | filters.command("help"))
async def help_command(client, message: Message):
    if not message.from_user or message.from_user.is_bot: 
        return
        
    await message.reply("💡 **طريقة عمل البوت:**\n\nقم بإضافة البوت كمشرف في مجموعتك، وسيبدأ تلقائياً برصد وحفظ أسماء الأعضاء كلما تفاعلوا أو قاموا بتغيير أسمائهم. لرؤية أسماء أي شخص، فقط قم بالرد على رسالته واضغط زر (🔍 فحص الأسماء بالرد) أو أرسل أمر /history.")

# زر الإحصائيات
@app.on_message(filters.regex("📊 إحصائيات البوت"))
async def stats_command(client, message: Message):
    if not message.from_user or message.from_user.is_bot: 
        return
        
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM history")
    total_users = cursor.fetchone()
    await message.reply(f"📊 **إحصائيات البوت الحالية:**\n\n👤 عدد المستخدمين المسجلين في القاعدة: {total_users[0]}")

app.run()
