import subprocess
import sys
import threading
import time

# دالة لتثبيت المكتبات إذا لم تكن مثبتة
def install_missing_packages():
    try:
        # تثبيت المكتبات الضرورية
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.7"])
    except Exception as e:
        print(f"Error installing packages: {e}")

# استدعاء دالة تثبيت المكتبات
install_missing_packages()

# استيراد المكتبات بعد تثبيتها
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# متغير لتخزين الإيميل الحالي لكل مستخدم
user_email = {}

# دالة لإنشاء إيميل وهمي باستخدام API لموقع مهمل أو موقع آخر
def create_fake_email():
    try:
        response = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        email = response.json()[0]
        return email
    except Exception as e:
        print(f"Error creating email: {e}")
        return None

# دالة لعرض صندوق الرسائل
def check_inbox(email):
    try:
        domain = email.split('@')[1]
        username = email.split('@')[0]
        url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
        response = requests.get(url)
        messages = response.json()

        if not messages:
            return "لا توجد رسائل جديدة."

        inbox_content = ""
        for message in messages:
            # زخرفة الموضوع والمحتوى
            inbox_content += (
                f"✉️ من: {message['from']}\n"
                f"📩 الموضوع: {message['subject']}\n"
                f"📃 المحتوى: {message['textBody'] if 'textBody' in message else 'لا يوجد محتوى.'}\n\n"
            )
        return inbox_content

    except Exception as e:
        print(f"Error checking inbox: {e}")
        return "حدث خطأ أثناء التحقق من الرسائل."

# دالة لبدء البوت
def start(update: Update, context):
    user_id = update.message.chat_id

    # إذا كان المستخدم قد أنشأ إيميلًا بالفعل
    if user_id in user_email:
        email = user_email[user_id]
        update.message.reply_text(f"إيميلك الحالي: {email}")
    else:
        # إنشاء إيميل جديد
        email = create_fake_email()
        if email:
            user_email[user_id] = email
            update.message.reply_text(f"تم إنشاء إيميلك الجديد: {email}")
        else:
            update.message.reply_text("حدث خطأ أثناء إنشاء الإيميل.")
            return

    # عرض الأزرار سواء كان لديه إيميل مسبق أو جديد
    keyboard = [
        [InlineKeyboardButton("📥 صندوق الرسائل", callback_data='inbox')],
        [InlineKeyboardButton("🔄 تغيير الإيميل", callback_data='change_email')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر خيارًا:", reply_markup=reply_markup)

# دالة لاستقبال أوامر الأزرار
def button(update: Update, context):
    query = update.callback_query
    query.answer()
    user_id = query.message.chat_id
    email = user_email.get(user_id)

    if query.data == 'inbox':
        inbox_content = check_inbox(email)
        query.edit_message_text(f"صندوق الرسائل:\n{inbox_content}")
    elif query.data == 'change_email':
        # تغيير الإيميل
        new_email = create_fake_email()
        if new_email:
            user_email[user_id] = new_email
            query.edit_message_text(f"تم تغيير إيميلك إلى: {new_email}")
        else:
            query.edit_message_text("حدث خطأ أثناء تغيير الإيميل.")

# دالة للتحقق من الرسائل الجديدة
def check_for_new_messages():
    while True:
        for user_id, email in user_email.items():
            inbox_content = check_inbox(email)
            if inbox_content != "لا توجد رسائل جديدة.":
                updater.bot.send_message(chat_id=user_id, text=f"لديك رسائل جديدة:\n{inbox_content}")
        time.sleep(60)  # تحقق كل دقيقة

# إعدادات البوت
def main():
    global updater
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN", use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    # تشغيل التحري عن الرسائل الجديدة في الخلفية
    message_check_thread = threading.Thread(target=check_for_new_messages)
    message_check_thread.start()

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()