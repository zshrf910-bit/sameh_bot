import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# 1. إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# قائمة المشرفين
ADMINS = {8811946164}

# ملف حفظ البيانات الدائم
DB_FILE = "bot_database.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["users"] = set(data.get("users", []))
                return data
        except Exception as e:
            logging.error(f"خطأ في قراءة ملف البيانات: {e}")

    return {
        "data": {"khutbahs": [], "fiqh": [], "hadith": [], "qiyam": [], "athar": []},
        "users": set()
    }

def save_data():
    save_dict = {
        "data": DB_DATA["data"],
        "users": list(DB_DATA["users"])
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(save_dict, f, ensure_ascii=False, indent=4)

DB_DATA = load_data()
DATA = DB_DATA["data"]
USERS = DB_DATA["users"]

# مراحل المحادثات
GET_MEDIA, GET_TITLE, GET_CATEGORY, GET_SUMMARY = range(4)
GET_NEW_ADMIN, GET_REMOVE_ADMIN, GET_CONTACT_MSG = range(4, 7)
GET_EDIT_SUMMARY_TEXT = 7

# ----------------- الواجهة العامة -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS.add(user_id)
    save_data()

    welcome_text = (
        "🌸 **فضلاً وليس أمراً** 🌸\n"
        "🌹 **نرجو منكم صالح الدعاء** 🌹\n\n"
        "«اللهم اغفر له وارحمه، ونوّر قبره، وآنس وحشته، واجعل قبره روضةً من رياض الجنة، واجمعنا به في جنات النعيم يارب العالمين، واغفر لأبي ولموتى المسلمين أجمعين.. آمين» 🤲🏻\n\n"
        "✨ **أهلاً بك في بوت خطب ودروس الشيخ سامح** ✨\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "🤍 **شاركونا الأجر والأثر:**\n"
        "إذا كان لديك أي تسجيل صوتي أو مقطع فيديو للشيخ سامح، يسعدني كثيراً تواصلك لإرساله عبر زر *(💌 تواصل مع الإدارة)* لنشره؛ فكل من ينتفع بكلمة سيكون في ميزان حسناتك وميزان حسناته إلى يوم القيامة 🌿.\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "💻 **تطوير وتصميم:**  زياد شرف\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "👇 **اختر القسم المطلوب للتصفح والاستماع، أو اكتب كلمة البحث مباشرة:**"
    )

    keyboard = [
        [InlineKeyboardButton("🎤 خطب الجمعة", callback_data="cat_khutbahs")],
        [InlineKeyboardButton("📚 دروس الفقه", callback_data="cat_fiqh"), InlineKeyboardButton("📖 دروس الحديث", callback_data="cat_hadith")],
        [InlineKeyboardButton("🌙 من قيام الليل", callback_data="cat_qiyam")],
        [InlineKeyboardButton("🖼️ أثر وذكرى (فيديو وصور)", callback_data="cat_athar")],
        [InlineKeyboardButton("💌 تواصل مع الإدارة / إرسال مقطع", callback_data="contact_us")],
        [InlineKeyboardButton("🔍 كيفية البحث", callback_data="help_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "main_menu":
        await start(update, context)
        return

    if data == "help_search":
        help_text = (
            "🔍 **كيفية البحث:**\n\n"
            "أولاً: اكتب أي كلمة بحث في المحادثة مباشرة (مثلاً: الصلاة، الأب، الصبر) وسيظهر لك المحتوى الذي يحتوي على هذه الكلمات فوراً.\n\n"
            "👨‍💻 **تطوير وتصميم:** زياد شرف"
        )
        keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]]
        await query.message.edit_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        items = DATA.get(cat_key, [])
        cat_names = {
            "khutbahs": "خطب الجمعة",
            "fiqh": "دروس الفقه",
            "hadith": "دروس الحديث",
            "qiyam": "من قيام الليل",
            "athar": "أثر وذكرى"
        }
        cat_title = cat_names.get(cat_key, "المحتوى")

        if not items:
            keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]]
            await query.message.edit_text(
                f"📁 **{cat_title}**\n\n⏳ **جاري تجهيز هذا القسم ورفعه قريباً بإذن الله.**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for item in items:
            icon = "🎬" if item["type"] == "video" else ("📸" if item["type"] == "photo" else "🔊")
            keyboard.append([InlineKeyboardButton(f"{icon} {item['title']}", callback_data=f"show_{item['id']}")])

        keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
        await query.message.edit_text(f"📁 **{cat_title}**\nاختر المحتوى للعرض:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    if data.startswith("show_"):
        item_id = data.replace("show_", "")
        selected_item = None
        selected_cat_key = None
        for cat_key, cat_list in DATA.items():
            for item in cat_list:
                if item["id"] == item_id:
                    selected_item = item
                    selected_cat_key = cat_key
                    break

        if selected_item:
            selected_item["views"] = selected_item.get("views", 0) + 1
            save_data()

            caption = f"📌 **{selected_item['title']}**\n📂 القسم: {selected_item['category']}\n"

            if user_id in ADMINS:
                caption += f"👁️ **عدد المشاهدات والتحميلات:** `{selected_item['views']}` (خاص بالإدارة)\n"

            caption += f"\n📝 **الملخص:**\n{selected_item['summary']}"

            keyboard = []
            if user_id in ADMINS:
                keyboard.append([InlineKeyboardButton("✏️ تعديل الملخص (للإدارة)", callback_data=f"editsummary_{selected_item['id']}")])

            keyboard.append([InlineKeyboardButton("🔙 رجوع للقسم", callback_data=f"cat_{selected_cat_key}"), InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
            markup = InlineKeyboardMarkup(keyboard)

            if selected_item["type"] == "audio":
                await query.message.reply_audio(audio=selected_item["file_id"], caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif selected_item["type"] == "video":
                await query.message.reply_video(video=selected_item["file_id"], caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif selected_item["type"] == "photo":
                await query.message.reply_photo(photo=selected_item["file_id"], caption=caption, parse_mode="Markdown", reply_markup=markup)

    if data.startswith("delcat_"):
        cat_key = data.replace("delcat_", "")
        items = DATA.get(cat_key, [])
        if not items:
            await query.message.edit_text("⚠️ هذا القسم فارغ تماماً.")
            return

        keyboard = []
        for item in items:
            keyboard.append([InlineKeyboardButton(f"❌ حذف: {item['title']}", callback_data=f"confirmdel_{item['id']}")])

        await query.message.edit_text("اختر المقطع المراد حذفه نهائياً:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("confirmdel_"):
        item_id = data.replace("confirmdel_", "")
        deleted_title = ""
        for cat_key, cat_list in DATA.items():
            for item in cat_list:
                if item["id"] == item_id:
                    deleted_title = item["title"]
                    cat_list.remove(item)
                    break

        save_data()
        await query.message.edit_text(f"✅ تم حذف المقطع **({deleted_title})** بنجاح من البوت وقاعدة البيانات.")
        return

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip().lower()
    results = []
    for cat_list in DATA.values():
        for item in cat_list:
            if query_text in item["title"].lower() or query_text in item["summary"].lower():
                results.append(item)

    if not results:
        await update.message.reply_text(f"🔍 لم نجد نتائج تطابق: `{query_text}`", parse_mode="Markdown")
        return

    keyboard = []
    for item in results:
        icon = "🎬" if item["type"] == "video" else ("📸" if item["type"] == "photo" else "🔊")
        keyboard.append([InlineKeyboardButton(f"{icon} {item['title']}", callback_data=f"show_{item['id']}")])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])

    await update.message.reply_text(f"🔍 **نتائج البحث عن ({query_text}):**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ----------------- التواصــل مع الإدارة -----------------

async def contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("💌 **تواصل مع الإدارة**\n\nأرسل رسالتك، اقتراحك، أو المقطع الخاص بالشيخ سامح الآن في محادثة واحدة:")
    return GET_CONTACT_MSG

async def contact_get_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    for admin_id in ADMINS:
        try:
            await context.bot.send_message(admin_id, f"📥 **رسالة جديدة من زائر:**\nالاسم: {user.first_name} (@{user.username})\nالـ ID: `{user.id}`", parse_mode="Markdown")
            await msg.forward(admin_id)
        except Exception:
            pass

    await update.message.reply_text("✅ تم إرسال رسالتك للإدارة بنجاح، جزاك الله خيراً!")
    return ConversationHandler.END

# ----------------- تعديل الملخص للمشرفين -----------------

async def edit_summary_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id not in ADMINS:
        return ConversationHandler.END

    item_id = query.data.replace("editsummary_", "")
    context.user_data['edit_item_id'] = item_id

    await query.message.reply_text("📝 **أرسل النص الجديد للملخص الآن:**")
    return GET_EDIT_SUMMARY_TEXT

async def edit_summary_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_summary = update.message.text.strip()
    item_id = context.user_data.get('edit_item_id')

    target_item = None
    for cat_list in DATA.values():
        for item in cat_list:
            if item["id"] == item_id:
                item["summary"] = new_summary
                target_item = item
                break

    if target_item:
        save_data()
        await update.message.reply_text(f"✅ **تم تحديث الملخص بنجاح للمقطع:**\n📌 {target_item['title']}")
    else:
        await update.message.reply_text("❌ حدث خطأ، لم نتمكن من العثور على المقطع.")

    return ConversationHandler.END

# ----------------- لوحة المشرفين والإدارة -----------------

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    keyboard = [
        [InlineKeyboardButton("🎤 خطب الجمعة", callback_data="delcat_khutbahs")],
        [InlineKeyboardButton("📚 دروس الفقه", callback_data="delcat_fiqh"), InlineKeyboardButton("📖 دروس الحديث", callback_data="delcat_hadith")],
        [InlineKeyboardButton("🌙 من قيام الليل", callback_data="delcat_qiyam")],
        [InlineKeyboardButton("🖼️ أثر وذكرى", callback_data="delcat_athar")]
    ]
    await update.message.reply_text("🗑️ **اختر القسم الذي تريد حذف مقطع منه:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END

    await update.message.reply_text("🎙️ **إضافة محتوى جديد**\n\nيرجى إرسال الصوت، الفيديو، أو الصورة الآن:")
    return GET_MEDIA

async def get_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.audio or msg.voice:
        context.user_data['file_id'] = (msg.audio or msg.voice).file_id
        context.user_data['type'] = "audio"
    elif msg.video:
        context.user_data['file_id'] = msg.video.file_id
        context.user_data['type'] = "video"
    elif msg.photo:
        context.user_data['file_id'] = msg.photo[-1].file_id
        context.user_data['type'] = "photo"
    else:
        await update.message.reply_text("❌ يرجى إرسال ملف صوتي، فيديو، أو صورة فقط.")
        return GET_MEDIA

    await update.message.reply_text("✅ تم الاستقبال بنجاح!\n\nاكتب الآن **عنوان المقطع/الدرس**:")
    return GET_TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("🎤 خطب الجمعة", callback_data="addcat_khutbahs")],
        [InlineKeyboardButton("📚 دروس الفقه", callback_data="addcat_fiqh")],
        [InlineKeyboardButton("📖 دروس الحديث", callback_data="addcat_hadith")],
        [InlineKeyboardButton("🌙 من قيام الليل", callback_data="addcat_qiyam")],
        [InlineKeyboardButton("🖼️ أثر وذكرى", callback_data="addcat_athar")]
    ]
    await update.message.reply_text("اختر **القسم** الذي ينتمي إليه المحتوى:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GET_CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat_key = query.data.replace("addcat_", "")
    context.user_data['cat_key'] = cat_key
    cat_names = {
        "khutbahs": "خطب الجمعة",
        "fiqh": "دروس الفقه",
        "hadith": "دروس الحديث",
        "qiyam": "من قيام الليل",
        "athar": "أثر وذكرى"
    }
    context.user_data['category_name'] = cat_names[cat_key]

    await query.message.edit_text("اكتب الآن **ملخصاً قصيراً** أو الكلمات المفتاحية للدرس:")
    return GET_SUMMARY

async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = update.message.text.strip()
    file_id = context.user_data['file_id']
    media_type = context.user_data['type']
    title = context.user_data['title']
    cat_key = context.user_data['cat_key']
    cat_name = context.user_data['category_name']

    item_id = f"item_{len(DATA[cat_key]) + 1}_{cat_key}"
    DATA[cat_key].append({
        "id": item_id,
        "title": title,
        "category": cat_name,
        "type": media_type,
        "file_id": file_id,
        "summary": summary,
        "views": 0
    })
    save_data()

    await update.message.reply_text(f"🎉 **تمت الإضافة بنجاح وحفظ الملف دائمياً!**\n\n📌 **العنوان:** {title}\n📂 **القسم:** {cat_name}\n\n📢 جاري إرسال إشعار للمشتركين...")

    notify_text = f"🔔 **تم إضافة محتوى جديد!**\n\n📌 **العنوان:** {title}\n📂 **القسم:** {cat_name}\n\nيمكنك الاستماع للتسجيل الآن عبر البوت 🌿."
    for uid in USERS:
        try:
            await context.bot.send_message(uid, notify_text, parse_mode="Markdown")
        except Exception:
            pass

    return ConversationHandler.END

# ---- إدارة المشرفين ----

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END
    await update.message.reply_text("➕ أرسل رقم الـ ID الخاص بـ **الأدمن الجديد**:")
    return GET_NEW_ADMIN

async def add_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_id = int(update.message.text.strip())
        ADMINS.add(new_id)
        await update.message.reply_text(f"✅ تم إضافة الأدمن الجديد بنجاح! (`{new_id}`)", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ يرجى كتابة أرقام فقط.")
    return ConversationHandler.END

async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return ConversationHandler.END
    await update.message.reply_text("➖ أرسل رقم الـ ID الخاص بـ **الأدمن المراد حذفه**:")
    return GET_REMOVE_ADMIN

async def remove_admin_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rem_id = int(update.message.text.strip())
        if rem_id in ADMINS:
            ADMINS.remove(rem_id)
            await update.message.reply_text(f"✅ تم حذف الأدمن (`{rem_id}`) بنجاح.")
        else:
            await update.message.reply_text("⚠️ هذا الرقم ليس أدمن من الأساس.")
    except ValueError:
        await update.message.reply_text("❌ يرجى كتابة أرقام فقط.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

# ----------------- التشغيل الرئيسي -----------------

def main():
    TOKEN = "8992618163:AAFW21TExhj7Gj41CT1baX9S9NbujLIZ1Kg"
    PROXY_URL = "http://proxy.server:3128"

    application = (
        Application.builder()
        .token(TOKEN)
        .proxy(PROXY_URL)
        .get_updates_proxy(PROXY_URL)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            GET_MEDIA: [MessageHandler(filters.AUDIO | filters.VOICE | filters.VIDEO | filters.PHOTO, get_media)],
            GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            GET_CATEGORY: [CallbackQueryHandler(get_category, pattern="^addcat_")],
            GET_SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    edit_summary_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_summary_start, pattern="^editsummary_")],
        states={
            GET_EDIT_SUMMARY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_summary_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    add_admin_conv = ConversationHandler(
        entry_points=[CommandHandler("add_admin", add_admin_start)],
        states={GET_NEW_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    remove_admin_conv = ConversationHandler(
        entry_points=[CommandHandler("remove_admin", remove_admin_start)],
        states={GET_REMOVE_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    contact_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(contact_start, pattern="^contact_us$")],
        states={GET_CONTACT_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, contact_get_msg)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(add_conv)
    application.add_handler(edit_summary_conv)
    application.add_handler(add_admin_conv)
    application.add_handler(remove_admin_conv)
    application.add_handler(contact_conv)

    application.add_handler(CommandHandler("delete", delete_start))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    print("✅ تم تشغيل البوت بنجاح...")
    application.run_polling()

if __name__ == "__main__":
    main()
