import os
import logging
import sqlite3
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = os.getenv("FLIPRADAR_DB", "flipradar.db")
MIN_BUY = 0
MAX_BUY = 500
MIN_PROFIT = 200

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("flipradar")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            buy REAL NOT NULL,
            resale REAL NOT NULL,
            shipping REAL NOT NULL DEFAULT 0,
            other_costs REAL NOT NULL DEFAULT 0,
            profit REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, url)
        )
    """)
    conn.commit()
    return conn


def valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def parse_money(s: str) -> float:
    return float(s.replace(",", ".").replace("zł", "").strip())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Cześć! Jestem FlipRadar PL — asystent do oceny okazji.\n\n"
        "Na razie mogę policzyć potencjalny zysk z linku, który mi wyślesz. "
        "Automatyczne pobieranie nowych ofert wymaga osobnego, dozwolonego źródła danych.\n\n"
        "Komenda:\n"
        "/add CENA_ZAKUPU CENA_SPRZEDAŻY DOSTAWA INNE_KOSZTY LINK\n\n"
        "Przykład:\n"
        "/add 150 400 15 15 https://www.vinted.pl/\n\n"
        "Domyślne filtry: zakup 0–500 zł, prognozowany zysk co najmniej 200 zł."
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 5:
        await update.message.reply_text(
            "Format:\n/add CENA_ZAKUPU CENA_SPRZEDAŻY DOSTAWA INNE_KOSZTY LINK\n"
            "Przykład:\n/add 150 400 15 15 https://www.vinted.pl/"
        )
        return

    try:
        buy = parse_money(context.args[0])
        resale = parse_money(context.args[1])
        shipping = parse_money(context.args[2])
        other = parse_money(context.args[3])
        url = context.args[4]
        if not valid_url(url):
            raise ValueError("Nieprawidłowy URL")
        if min(buy, resale, shipping, other) < 0:
            raise ValueError("Kwoty nie mogą być ujemne")
    except Exception:
        await update.message.reply_text("Nie udało się odczytać danych. Sprawdź kwoty i link.")
        return

    if not (MIN_BUY <= buy <= MAX_BUY):
        await update.message.reply_text(
            f"⚠️ Zakup {buy:.0f} zł jest poza ustawionym zakresem {MIN_BUY}–{MAX_BUY} zł, ale policzę wynik."
        )

    profit = resale - buy - shipping - other
    conn = db()
    try:
        conn.execute(
            "INSERT INTO leads (user_id,url,buy,resale,shipping,other_costs,profit) VALUES (?,?,?,?,?,?,?)",
            (update.effective_user.id, url, buy, resale, shipping, other, profit)
        )
        conn.commit()
        saved = True
    except sqlite3.IntegrityError:
        saved = False
    finally:
        conn.close()

    status = "✅ Przechodzi próg 200 zł" if profit >= MIN_PROFIT else "❌ Nie przechodzi progu 200 zł"
    if profit >= MIN_PROFIT:
        status += "\nPamiętaj: to szacunek, a nie gwarancja sprzedaży."
    msg = (
        f"📊 <b>Wynik FlipRadar PL</b>\n\n"
        f"Zakup: {buy:.2f} zł\n"
        f"Sprzedaż (szacunek): {resale:.2f} zł\n"
        f"Dostawa: {shipping:.2f} zł\n"
        f"Inne koszty/rezerwa: {other:.2f} zł\n"
        f"━━━━━━━━━━━━\n"
        f"<b>Szacowany zysk: {profit:.2f} zł</b>\n"
        f"{status}\n\n"
        f"Link: {url}\n"
        f"{'Zapisano do historii.' if saved else 'Ten link jest już w historii.'}"
    )
    await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    row = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(CASE WHEN profit >= ? THEN 1 ELSE 0 END),0), "
        "COALESCE(MAX(profit),0) FROM leads WHERE user_id=?",
        (MIN_PROFIT, update.effective_user.id)
    ).fetchone()
    conn.close()
    await update.message.reply_text(
        f"📈 Twoja historia\n"
        f"Sprawdzone linki: {row[0]}\n"
        f"Z progiem 200 zł+: {row[1]}\n"
        f"Najwyższy wyliczony zysk: {row[2]:.2f} zł"
    )


def main():
    if not TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable first.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("stats", stats))
    log.info("FlipRadar PL started. This starter does not scrape Vinted.")
    app.run_polling()


if __name__ == "__main__":
    main()
