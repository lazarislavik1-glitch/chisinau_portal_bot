from telegram.ext import Application
application = Application.builder().token("ТВОЙ_ТОКЕН").build()
# bot.py
import logging
from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID
from core.categories import CATEGORIES
from core.company_manager import (
    load_companies,
    save_companies,
    get_companies_by_subcategory,
    add_company,
)

# Логирование (можно потом отправлять в файл)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Шаги диалога добавления компании
(
    ADD_NAME,
    ADD_ACTIVITY,
    ADD_ADVANTAGES,
    ADD_ADDRESS,
    ADD_CONTACTS,
    ADD_CATEGORY,
) = range(6)

# В памяти держим компании (кэш)
companies_cache: Dict[str, list[Dict[str, Any]]] = load_companies()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def sync_companies():
    """Перезаписать companies.json из кэша."""
    save_companies(companies_cache)


def ensure_sub_list(sub_code: str) -> list[Dict[str, Any]]:
    """Гарантирует, что для подкатегории есть список компаний."""
    if sub_code not in companies_cache:
        companies_cache[sub_code] = []
    return companies_cache[sub_code]


# ========== ГЛАВНОЕ МЕНЮ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — показывает главное меню."""
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("🔍 Найти услуги", callback_data="services")],
        [InlineKeyboardButton("📋 Политика использования", callback_data="policy")],
        [InlineKeyboardButton("👤 Менеджер / контакты", callback_data="contacts")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("⚙️ Администратор", callback_data="admin_panel")]
        )

    await update.message.reply_text(
        "🏠 Главное меню\n\nДобро пожаловать в Chisinau-PORTAL!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_main_menu(query, user_id: int):
    keyboard = [
        [InlineKeyboardButton("🔍 Найти услуги", callback_data="services")],
        [InlineKeyboardButton("📋 Политика использования", callback_data="policy")],
        [InlineKeyboardButton("👤 Менеджер / контакты", callback_data="contacts")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("⚙️ Администратор", callback_data="admin_panel")]
        )

    await query.edit_message_text(
        "🏠 Главное меню\n\nВыберите нужный раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ========== ОБРАБОТКА КНОПОК ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    # Возврат в главное меню
    if data == "main":
        return await show_main_menu(query, user_id)

    # Политика
    if data == "policy":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="main")]]
        return await query.edit_message_text(
            "📋 Политика использования\n\n"
            "1. Все услуги предоставляются компаниями-партнёрами.\n"
            "2. Администрация бота не несёт ответственности за качество услуг.\n"
            "3. Уточняйте все детали у исполнителей перед заказом.\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Контакты
    if data == "contacts":
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="main")]]
        return await query.edit_message_text(
            "👤 Менеджер / контакты\n\n"
            "Телефон: +373 XX XXX XXX\n"
            "Email: example@mail.com\n"
            "Telegram: @your_manager\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Админ-панель
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            return await query.answer("⛔ Нет доступа", show_alert=True)

        keyboard = [
            [InlineKeyboardButton("➕ Добавить компанию", callback_data="admin_add_company")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main")],
        ]
        return await query.edit_message_text(
            "⚙️ Панель администратора\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    if data == "admin_stats":
        total = sum(len(lst) for lst in companies_cache.values())
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]
        return await query.edit_message_text(
            f"📊 Статистика\n\nВсего компаний: {total}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Меню категорий
    if data == "services":
        keyboard = []
        for cat_code, cat_data in CATEGORIES.items():
            keyboard.append(
                [
                    InlineKeyboardButton(
                        cat_data["title"],
                        callback_data=f"cat:{cat_code}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main")]
        )
        return await query.edit_message_text(
            "🔍 Найти услуги\n\nВыберите категорию:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Категория -> подкатегории
    if data.startswith("cat:"):
        cat_code = data.split(":", 1)[1]
        cat = CATEGORIES.get(cat_code)
        if not cat:
            return await query.answer("Категория не найдена", show_alert=True)

        keyboard = []
        for sub_code, sub_name in cat["subcategories"].items():
            keyboard.append(
                [
                    InlineKeyboardButton(
                        sub_name,
                        callback_data=f"sub:{sub_code}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("◀️ Назад", callback_data="services")]
        )
        keyboard.append(
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main")]
        )
        return await query.edit_message_text(
            f"{cat['title']}\n\nВыберите подкатегорию:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Подкатегория -> список компаний
    if data.startswith("sub:"):
        sub_code = data.split(":", 1)[1]
        return await show_companies_list(query, sub_code)

    # Открыть компанию
    if data.startswith("company:"):
        _, sub_code, idx_str = data.split(":", 2)
        index = int(idx_str)
        return await show_company_card(query, sub_code, index)


# ========== ПОКАЗ КОМПАНИЙ ==========

async def show_companies_list(query, sub_code: str):
    companies = companies_cache.get(sub_code, [])
    # ищем имя подкатегории
    sub_name = None
    for cat in CATEGORIES.values():
        if sub_code in cat["subcategories"]:
            sub_name = cat["subcategories"][sub_code]
            break

    if not sub_name:
        sub_name = "Неизвестная подкатегория"

    if not companies:
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="services")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main")],
        ]
        return await query.edit_message_text(
            f"{sub_name}\n\nПока нет компаний в этой подкатегории.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    keyboard = []
    for i, comp in enumerate(companies):
        title = comp.get("name", f"Компания #{i+1}")
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🏢 {title}",
                    callback_data=f"company:{sub_code}:{i}",
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton("◀️ Назад", callback_data="services")]
    )
    keyboard.append(
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main")]
    )

    await query.edit_message_text(
        f"{sub_name}\n\nВыберите компанию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_company_card(query, sub_code: str, index: int):
    companies = companies_cache.get(sub_code, [])
    if not (0 <= index < len(companies)):
        return await query.answer("Компания не найдена", show_alert=True)

    comp = companies[index]
    text = (
        f"🏢 {comp.get('name', 'Без названия')}\n\n"
        f"📌 Деятельность: {comp.get('activity', 'Не указана')}\n"
        f"⭐ Преимущества: {comp.get('advantages', 'Не указаны')}\n"
        f"📍 Адрес: {comp.get('address', 'Не указан')}\n"
        f"📞 Контакты: {comp.get('contacts', 'Не указаны')}"
    )

    keyboard = [
        [InlineKeyboardButton("◀️ Назад к списку", callback_data=f"sub:{sub_code}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main")],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ========== ДОБАВЛЕНИЕ КОМПАНИИ (АДМИН) ==========

async def admin_add_company_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск диалога добавления компании (только для админа)."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ Нет доступа", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(
        "➕ Добавление компании\n\nШаг 1/6\nВведите название компании:"
    )
    return ADD_NAME


async def add_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Шаг 2/6\nОпишите деятельность компании:")
    return ADD_ACTIVITY


async def add_company_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["activity"] = update.message.text.strip()
    await update.message.reply_text("Шаг 3/6\nНапишите преимущества компании:")
    return ADD_ADVANTAGES


async def add_company_advantages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["advantages"] = update.message.text.strip()
    await update.message.reply_text("Шаг 4/6\nУкажите адрес компании:")
    return ADD_ADDRESS


async def add_company_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("Шаг 5/6\nУкажите контакты (телефон, сайт, соцсети):")
    return ADD_CONTACTS


async def add_company_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contacts"] = update.message.text.strip()

    # выбор подкатегории
    keyboard = []
    for cat_code, cat_data in CATEGORIES.items():
        keyboard.append(
            [InlineKeyboardButton(f"📂 {cat_data['title']}", callback_data=f"dummy_cat:{cat_code}")]
        )
        for sub_code, sub_name in cat_data["subcategories"].items():
            keyboard.append(
                [InlineKeyboardButton(f" └ {sub_name}", callback_data=f"add_sub:{sub_code}")]
            )
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="add_cancel")])

    await update.message.reply_text(
        "Шаг 6/6\nВыберите подкатегорию, к которой относится компания:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADD_CATEGORY


async def add_company_choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "add_cancel":
        await query.edit_message_text("Добавление компании отменено.")
        return ConversationHandler.END

    if not data.startswith("add_sub:"):
        # нажатие на заголовок категории (dummy)
        return ADD_CATEGORY

    sub_code = data.split(":", 1)[1]

    comp = {
        "name": context.user_data.get("name", ""),
        "activity": context.user_data.get("activity", ""),
        "advantages": context.user_data.get("advantages", ""),
        "address": context.user_data.get("address", ""),
        "contacts": context.user_data.get("contacts", ""),
        "photos": [],
    }

    ensure_sub_list(sub_code).append(comp)
    sync_companies()

    await query.edit_message_text("✅ Компания успешно добавлена.")
    return ConversationHandler.END


async def add_company_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление компании отменено.")
    return ConversationHandler.END


# ========== СОЗДАНИЕ APPLICATION ДЛЯ WEBHOOK ==========

def create_application() -> Application:
    """Создаём и настраиваем telegram Application (используется и локально, и на сервере)."""
    app = Application.builder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # Обработчик всех кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    # Диалог добавления компании
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_company_start, pattern="^admin_add_company$")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company_name)],
            ADD_ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company_activity)],
            ADD_ADVANTAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company_advantages)],
            ADD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company_address)],
            ADD_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_company_contacts)],
            ADD_CATEGORY: [CallbackQueryHandler(add_company_choose_category, pattern="^(add_sub:|add_cancel)")],
        },
        fallbacks=[MessageHandler(filters.Regex("^/cancel$"), add_company_cancel)],
    )
    app.add_handler(conv_handler)

    return app


# Возможность локального запуска через polling
if __name__ == "__main__":
    application = create_application()
    print("Бот запущен локально (polling)...")
    application.run_polling()
