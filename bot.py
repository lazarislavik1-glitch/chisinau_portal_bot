import json
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, ADMIN_ID, COMPANIES_FILE
from core.categories import CATEGORIES
from core.company_manager import (
    load_companies,
    save_companies
)


# ---------------- Загрузка компаний ---------------- #

companies = load_companies()


def ensure_sub_list(sub_code):
    """Гарантирует, что подкатегория существует."""
    if sub_code not in companies:
        companies[sub_code] = []
    return companies[sub_code]


def sync():
    save_companies(companies)


# ---------------- Главное меню ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Найти услуги", callback_data="services")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙ Админ", callback_data="admin")])

    await update.message.reply_text(
        "🏠 *Главное меню*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ---------------- КНОПКИ ---------------- #

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    await query.answer()

    # --- Назад в главное меню ---

    if data == "main":
        return await query.edit_message_text(
            "🏠 *Главное меню*",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Найти услуги", callback_data="services")],
                [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
                [InlineKeyboardButton("⚙ Админ", callback_data="admin")] if user_id == ADMIN_ID else []
            ]),
            parse_mode="Markdown"
        )

    # --- Контакты ---

    if data == "contacts":
        return await query.edit_message_text(
            "📞 Контакты менеджера:\n\n"
            "Телефон: +373 XX XXX XXX\n"
            "Telegram: @your_manager\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Назад", callback_data="main")]
            ])
        )

    # --- Админ панель ---

    if data == "admin":
        if user_id != ADMIN_ID:
            return await query.answer("Нет доступа", show_alert=True)

        return await query.edit_message_text(
            "⚙ *Админ панель*",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить компанию", callback_data="add_company")],
                [InlineKeyboardButton("⬅ Назад", callback_data="main")],
            ]),
            parse_mode="Markdown"
        )

    # --- Категории ---

    if data == "services":
        buttons = []
        for code, cat in CATEGORIES.items():
            buttons.append([InlineKeyboardButton(cat["title"], callback_data=f"cat:{code}")])

        buttons.append([InlineKeyboardButton("⬅ Назад", callback_data="main")])

        return await query.edit_message_text(
            "🔍 *Категории услуг*",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

    # --- Подкатегории ---

    if data.startswith("cat:"):
        code = data.split(":")[1]
        cat = CATEGORIES[code]

        btns = []
        for sub_code, sub_name in cat["subcategories"].items():
            btns.append([InlineKeyboardButton(sub_name, callback_data=f"sub:{sub_code}")])

        btns.append([InlineKeyboardButton("⬅ Назад", callback_data="services")])

        return await query.edit_message_text(
            f"{cat['title']}\nВыберите подкатегорию:",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    # --- Компании в подкатегории ---

    if data.startswith("sub:"):
        sub_code = data.split(":")[1]
        comps = companies.get(sub_code, [])

        if not comps:
            return await query.edit_message_text(
                "Пока нет компаний",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅ Назад", callback_data="services")]
                ])
            )

        btns = []
        for i, comp in enumerate(comps):
            btns.append([InlineKeyboardButton(comp["name"], callback_data=f"comp:{sub_code}:{i}")])

        btns.append([InlineKeyboardButton("⬅ Назад", callback_data="services")])

        return await query.edit_message_text(
            "Выберите компанию:",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    # --- Одна компания ---

    if data.startswith("comp:"):
        _, sub, idx = data.split(":")
        comp = companies[sub][int(idx)]

        text = (
            f"🏢 *{comp['name']}*\n\n"
            f"📌 Деятельность: {comp['activity']}\n"
            f"⭐ Преимущества: {comp['advantages']}\n"
            f"📍 Адрес: {comp['address']}\n"
            f"☎ Контакты: {comp['contacts']}"
        )

        return await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Назад", callback_data=f"sub:{sub}")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main")]
            ]),
            parse_mode="Markdown"
        )


# ---------------- Создание приложения ---------------- #

def create_app():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    return app


# Для локального теста — polling
if __name__ == "__main__":
    application = create_app()
    application.run_polling()
