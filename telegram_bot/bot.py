import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_NAME = os.getenv("CARD_NAME", "")
CARD_BANK = os.getenv("CARD_BANK", "")
PAYMENT_NOTE = os.getenv("PAYMENT_NOTE", "")

# Majburiy a'zo bo'lish kanallari (username @ ixtiyoriy, vergul bilan ajrating)
# Masalan: "my_channel, second_channel"
REQUIRED_CHANNELS = [
    c.strip().lstrip("@")
    for c in os.getenv("REQUIRED_CHANNELS", "").split(",")
    if c.strip()
]

# Chek/buyurtma yuboriladigan kanal yoki guruh (username yoki raqamli ID)
ORDERS_CHANNEL = os.getenv("ORDERS_CHANNEL", "").strip()

# Stars narxlari: telegram stars -> so'm (1 stars = 190 so'm)
STAR_RATES = {1: 190, 2: 380, 5: 950, 10: 1900, 25: 4750, 50: 9500}

# Premium oylik narxlari
PREMIUM_RATES = {1: 42000, 3: 160000, 6: 210000, 12: 370000}

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)
