import os
import json
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Конфигурация
CACHE_FILE = 'news_cache.json'
CACHE_EXPIRE_SEC = 3600  # 1 час
MAX_NEWS_TO_SHOW = 15

# Инициализация
try:
    from dotenv import load_dotenv

    load_dotenv()
    BOT_TOKEN = os.getenv("token")
except:
    BOT_TOKEN = os.environ.get("token")


def init_cache():
    """Инициализация пустого кеша"""
    return {
        'last_update': 0,
        'news': {
            'data': [],
            'total_count': 0,
            'timestamp': 0
        }
    }


def load_cache():
    """Загрузка кеша из файла с созданием, если не существует"""
    if not os.path.exists(CACHE_FILE):
        return init_cache()

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            # Проверка структуры
            if 'last_update' not in cache or 'news' not in cache:
                return init_cache()
            return cache
    except:
        return init_cache()


def save_cache(cache):
    """Сохранение кеша в файл"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# Инициализация кеша
cache = load_cache()
current_news = cache['news']  # Теперь точно существует

# Клавиатура
keyboard = [["/start", "/help"], ["/parserbot", "/novosty"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡Привествую вас! Бот для парсинга новостей науки\nВыберите действие:",
        reply_markup=reply_markup
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ <b>Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Справка\n"
        "/parserbot - Обновить новости\n"
        "/novosty - Показать новости"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def parser_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cache, current_news

    try:
        # Проверка времени последнего обновления
        if time.time() - cache['last_update'] < CACHE_EXPIRE_SEC:
            await update.message.reply_text("🔄 Используются ранее загруженные новости")
            return

        await update.message.reply_text("⏳ Загружаю свежие новости...")

        from main import parse_news
        success, count = parse_news()

        if success:
            # Загружаем свежие данные
            with open('news_february.json', 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            # Обновляем кеш
            cache['last_update'] = time.time()
            cache['news'] = new_data
            current_news = new_data
            save_cache(cache)

            await update.message.reply_text(
                f"✅ <b>Обновлено!</b>\n"
                f"📊 Всего новостей: {count}\n"
                f"⏰ Время: {time.strftime('%H:%M', time.localtime())}",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("⚠️ Не удалось обновить новости")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        print(f"[Ошибка бота] {str(e)}")


async def show_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_news

    if not current_news['data']:
        await update.message.reply_text("📭 Новостей нет. Используйте /parserbot")
        return

    total = current_news['total_count']
    to_show = min(total, MAX_NEWS_TO_SHOW)
    last_update = time.strftime('%d.%m.%Y %H:%M', time.localtime(cache['last_update']))

    response = (
        f"📅 <b>Обновление:</b> {last_update}\n"
        f"📊 <b>Найдено:</b> {total}\n"
        f"🔍 <b>Показано:</b> {to_show}\n\n"
    )

    for idx, item in enumerate(current_news['data'][:to_show], 1):
        title = item.get('title', 'Без названия').replace('<', '&lt;').replace('>', '&gt;')
        link = item.get('link', '')
        text = item.get('text', '')[:100].replace('<', '&lt;').replace('>', '&gt;')

        link_part = f"<a href=\"{link}\">🔗 Подробнее</a>\n" if link.startswith('http') else ""
        response += f"<b>{idx}. {title}</b>\n{link_part}{text}...\n\n"

    try:
        await update.message.reply_text(
            response,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка при выводе новостей")
        print(f"[Ошибка отправки] {str(e)}")


def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("parserbot", parser_bot))
    app.add_handler(CommandHandler("novosty", show_news))

    # Обработчик ошибок
    app.add_error_handler(lambda u, c: print(f"⚠️ Ошибка: {c.error}"))

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()