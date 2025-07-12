import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import get_logger

logger = get_logger(__name__)

class TelegramBot:
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not configured.")
            self.application = None
            return
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        if not self.application:
            return
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_html(rf"Hi {user.mention_html()}! I am your trading assistant.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("System Status: OPERATIONAL")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Available commands: /start /status /help")

    async def send_alert(self, message: str):
        if not self.application or not TELEGRAM_CHAT_ID:
            return
        try:
            await self.application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    async def start(self):
        if self.application:
            self.application.run_polling()

