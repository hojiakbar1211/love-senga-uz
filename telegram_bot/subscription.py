from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, REQUIRED_CHANNELS

SUB_MSG = "🔒 <b>Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:</b>\n\n"

# Yaratilgan havolalarni har bir foydalanuvchi uchun eslab qolamiz (ramda)
_USER_LINKS = {}


async def is_subscribed(user_id: int, channel: str) -> bool:
    """Foydalanuvchi kanalga a'zo ekanini tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def get_invite_link(user_id: int, channel: str) -> str:
    """Har bir foydalanuvchi uchun alohida taklif havolasi yaratadi.
    Bot kanalda admin bo'lishi shart! Yo'qsa oddiy https://t.me/channel qaytaradi."""
    key = f"{user_id}:{channel}"
    if key in _USER_LINKS:
        return _USER_LINKS[key]
    try:
        link = await bot.create_chat_invite_link(
            chat_id=f"@{channel}",
            name=f"user{user_id}",
            member_limit=1,
        )
        invite = link.invite_link
    except Exception:
        invite = f"https://t.me/{channel}"
    _USER_LINKS[key] = invite
    return invite


async def check_subscriptions(user_id: int) -> list:
    """A'zo emas kanallar ro'yxatini qaytaradi."""
    if not REQUIRED_CHANNELS:
        return []
    missing = []
    for channel in REQUIRED_CHANNELS:
        if not await is_subscribed(user_id, channel):
            missing.append(channel)
    return missing


async def subscription_buttons(user_id: int, missing: list) -> InlineKeyboardMarkup:
    """A'zo bo'lmagan kanallar uchun shaxsiy havolalar + tekshirish tugmasi."""
    rows = []
    for channel in missing:
        link = await get_invite_link(user_id, channel)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📢 A'zo bo'lish: @{channel}",
                    url=link,
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="sub:check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def ensure_subscription(user_id: int, event) -> bool:
    """A'zo bo'lmasa, shaxsiy havolali xabar ko'rsatadi.
    True - a'zo bo'lgan, False - hali a'zo emas."""
    missing = await check_subscriptions(user_id)
    if not missing:
        return True
    msg = SUB_MSG
    for channel in missing:
        msg += f"👉 <a href='https://t.me/{channel}'>@{channel}</a>\n"
    msg += "\nA'zo bo'lgandan so'ng <b>\"A'zo bo'ldim\"</b> tugmasini bosing."
    try:
        await event.answer(
            msg,
            reply_markup=await subscription_buttons(user_id, missing),
        )
    except Exception:
        pass
    return False