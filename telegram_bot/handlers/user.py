from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot import bot, ADMIN_IDS, ORDERS_CHANNEL
from database import add_user, get_user, get_balance, user_purchases, update_balance, add_purchase, update_purchase, pending_purchases
from handlers.states import StarsOrder, PremiumOrder, PaymentConfirm, BalanceTopUp
from subscription import ensure_subscription, check_subscriptions, subscription_buttons

router = Router()

MAIN_MENU = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="menu:stars")],
        [InlineKeyboardButton(text="👑 Telegram Premium", callback_data="menu:premium")],
        [InlineKeyboardButton(text="👤 Mening profilim", callback_data="menu:profile")],
        [InlineKeyboardButton(text="💰 Balans to'ldirish", callback_data="menu:card")],
        [InlineKeyboardButton(text="ℹ️ Yordam", callback_data="menu:help")],
    ]
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await add_user(user.id, user.username or "", user.first_name or "")
    ok = await ensure_subscription(user.id, message)
    if not ok:
        return
    share = f"\n\n<b>👤 Sizning ID:</b> <code>{user.id}</code>" if user.id in ADMIN_IDS else ""
    await message.answer(
        "👋 <b>Xush kelibsiz!</b>\n\n"
        "Bu bot orqali <b>Telegram Stars</b> va <b>Telegram Premium</b> sotib olishingiz mumkin.\n"
        f"To'lov karta orqali amalga oshiriladi.{share}",
        reply_markup=MAIN_MENU,
    )


async def require_sub(call: CallbackQuery) -> bool:
    """A'zolik tekshiradi. A'zo bo'lsa True, a'zo emas bo'lsa xabar ko'rsatib False."""
    ok = await ensure_subscription(call.from_user.id, call)
    if not ok:
        await call.answer("Avval kanallarga a'zo bo'ling!", show_alert=True)
    return ok


@router.callback_query(F.data == "sub:check")
async def sub_check(call: CallbackQuery, state: FSMContext):
    missing = await check_subscriptions(call.from_user.id)
    if not missing:
        await call.message.edit_text(
            "✅ <b>A'zo bo'ldingiz!</b> Endi botdan foydalanishingiz mumkin.",
            reply_markup=MAIN_MENU,
        )
        await call.answer()
        return
    msg = "❌ Siz hali ham quyidagi kanallarga a'zo emassiz:\n\n"
    for ch in missing:
        msg += f"👉 <a href='https://t.me/{ch}'>@{ch}</a>\n"
    msg += "\nA'zo bo'lgandan so'ng <b>\"A'zo bo'ldim\"</b> tugmasini bosing."
    try:
        await call.message.answer(msg, reply_markup=await subscription_buttons(call.from_user.id, missing))
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data == "menu:stars")
async def menu_stars(call: CallbackQuery, state: FSMContext):
    if not await require_sub(call):
        return
    await state.set_state(StarsOrder.amount)
    await call.message.edit_text(
        "⭐ <b>Telegram Stars</b>\n\n"
        "Miqdorni tanlang yoki o'zingiz kiritib qo'ying:\n"
        "Narx: <b>190 so'm = 1 Stars</b>\n\n"
        "Minimal: <b>50 Stars</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="50 ⭐", callback_data="stars:quick:50")],
                [InlineKeyboardButton(text="100 ⭐", callback_data="stars:quick:100")],
                [InlineKeyboardButton(text="200 ⭐", callback_data="stars:quick:200")],
                [InlineKeyboardButton(text="500 ⭐", callback_data="stars:quick:500")],
                [InlineKeyboardButton(text="1000 ⭐", callback_data="stars:quick:1000")],
                [InlineKeyboardButton(text="5000 ⭐", callback_data="stars:quick:5000")],
                [InlineKeyboardButton(text="✍️ O'zim kiritaman", callback_data="stars:manual")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("stars:quick:"))
async def stars_quick(call: CallbackQuery, state: FSMContext):
    amount = int(call.data.split(":")[2])
    price = amount * 190
    await state.update_data(amount=amount, price=price)
    await state.set_state(StarsOrder.recipient)
    await call.message.edit_text(
        f"⭐ Stars: <b>{amount}</b> | 💵 <b>{price:,} so'm</b>\n\n"
        "👤 <b>Kimga sotib olmoqchisiz?</b>\n"
        "Telegram username'ni kiriting (masalan <code>@username</code>) yoki pastdagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 O'zim uchun", callback_data="recipient:self")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data == "stars:manual")
async def stars_manual(call: CallbackQuery, state: FSMContext):
    await state.set_state(StarsOrder.amount)
    await call.message.answer(
        "🔢 <b>Nechta Stars kerak?</b>\n"
        "Raqamni yozing (minimal <b>50</b>). Masalan: <code>350</code>"
    )
    await call.answer()


@router.message(StarsOrder.amount)
async def stars_amount(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or int(text) < 50:
        await message.answer("❌ Minimal buyurtma <b>50 Stars</b>. Yana bir marta yozing:")
        return
    amount = int(text)
    price = amount * 190
    await state.update_data(amount=amount, price=price)
    await state.set_state(StarsOrder.recipient)
    await message.answer(
        f"⭐ Stars: <b>{amount}</b> | 💵 <b>{price:,} so'm</b>\n\n"
        "👤 <b>Kimga sotib olmoqchisiz?</b>\n"
        "Telegram username'ni kiriting (masalan <code>@username</code>) yoki pastdagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 O'zim uchun", callback_data="recipient:self")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )


@router.callback_query(StarsOrder.recipient, F.data == "recipient:self")
async def stars_recipient_self(call: CallbackQuery, state: FSMContext):
    await state.update_data(recipient=f"@{call.from_user.username or call.from_user.id}")
    await state.set_state(StarsOrder.confirm)
    await show_stars_confirm(call.message, state)
    await call.answer()


@router.message(StarsOrder.recipient)
async def stars_recipient_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.startswith("@") and not text.replace("@", "").replace("_", "").isalnum():
        await message.answer("❌ Noto'g'ri username. Masalan: <code>@username</code> kabi yozing.")
        return
    await state.update_data(recipient=text if text.startswith("@") else f"@{text}")
    await state.set_state(StarsOrder.confirm)
    await show_stars_confirm(message, state)


async def show_stars_confirm(msg_or_call, state: FSMContext):
    data = await state.get_data()
    recipient = data.get("recipient", "—")
    balance = await get_balance(msg_or_call.from_user.id if hasattr(msg_or_call, "from_user") else msg_or_call.chat.id)
    diff = data["price"] - balance
    if diff > 0:
        bal_line = f"💰 Balans: <b>{balance:,} so'm</b> · ❌ <b>{diff:,} so'm kam</b>"
    else:
        bal_line = f"💰 Balans: <b>{balance:,} so'm</b> · ✅ <b>To'lov balansdan</b>"
    text = (
        f"✅ <b>Buyurtma tasdiqlash</b>\n\n"
        f"⭐ Stars: <b>{data['amount']}</b>\n"
        f"💵 Narx: <b>{data['price']:,} so'm</b>\n"
        f"👤 Kimga: <b>{recipient}</b>\n"
        f"{bal_line}\n\n"
        f"Ijobiy bo'lsa, <b>buyurtma berish</b> tugmasini bosing."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="stars:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
            ],
            [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="menu:card")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
        ]
    )
    try:
        await msg_or_call.edit_text(text, reply_markup=kb)
    except Exception:
        await msg_or_call.answer(text, reply_markup=kb)




@router.callback_query(StarsOrder.confirm, F.data == "stars:confirm")
async def stars_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    balance = await get_balance(call.from_user.id)
    user = call.from_user

    if balance >= data["price"]:
        await update_balance(call.from_user.id, -data["price"])
        purchase_id = await add_purchase(
            user_id=user.id,
            username=user.username or "",
            item_type=data.get("item_type", "stars"),
            amount=str(data["amount"]),
            price=data["price"],
            txn_id=f"STAR{user.id}{data['amount']}",
        )
        await update_purchase(purchase_id, "approved")
        uname = f"@{user.username}" if user.username else f"{user.first_name or user.id} (username yo'q)"
        caption = (
            f"🆕 <b>Balansdan buyurtma!</b>  (#{purchase_id})\n"
            f"────────────────\n"
            f"👤 Foydalanuvchi: <b>{uname}</b>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📦 Turi: <b>⭐ {data['amount']} Stars</b>\n"
            f"💵 Narx: <b>{data['price']:,} so'm</b>\n"
            f"👤 Kimga: <b>{data.get('recipient', '—')}</b>\n\n"
            f"To'lov balansdan ayirildi ✅"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📦 Bajarildi", callback_data=f"deliver:{purchase_id}")]]
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, caption, reply_markup=kb)
            except Exception:
                pass
        if ORDERS_CHANNEL:
            try:
                await bot.send_message(ORDERS_CHANNEL, caption, reply_markup=kb)
            except Exception:
                pass
        await call.message.edit_text(
            "✅ <b>Buyurtmangiz balansdan to'landi!</b>\n\n"
            f"⭐ {data['amount']} Stars\n"
            f"💵 {data['price']:,} so'm\n\n"
            f"💰 Qolgan balans: {await get_balance(user.id):,} so'm\n\n"
            "Tez orada sizga topshiriladi. Rahmat! 🙌",
        )
        await state.clear()
        await call.answer()
        return

    await state.set_state(PaymentConfirm.waiting_proof)
    await state.update_data(item_type="stars", txn_id=f"STAR{call.from_user.id}{data['amount']}")
    from bot import CARD_NUMBER, CARD_NAME, CARD_BANK, PAYMENT_NOTE
    diff = data["price"] - balance
    await call.message.edit_text(
        "💳 <b>To'lov uchun:</b>\n\n"
        f"🏦 Bank: <b>{CARD_BANK}</b>\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Ism: <b>{CARD_NAME}</b>\n\n"
        f"📝 {PAYMENT_NOTE}\n\n"
        f"⭐ Stars: <b>{data['amount']}</b> | 💵 <b>{data['price']:,} so'm</b>\n"
        f"👤 Kimga: <b>{data.get('recipient', '—')}</b>\n"
        f"💰 Balans: <b>{balance:,} so'm</b> · ❌ <b>{diff:,} so'm kam</b>\n\n"
        f"To'lovni amalga oshirib, chek/bank apps skrinshotini yuboring👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="menu:card")],
                [InlineKeyboardButton(text="✅ To'ladim, chek yuboraman", callback_data="pay:start")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
            ]
        ),
    )
    await call.message.answer("📎 <b>Chek/skrinshot rasmini yuboring.</b>")
    await call.answer()


@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=MAIN_MENU)
    await call.answer()


@router.callback_query(F.data == "menu:back")
async def menu_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🏠 <b>Bosh menu</b>", reply_markup=MAIN_MENU)
    await call.answer()


@router.callback_query(F.data == "menu:premium")
async def menu_premium(call: CallbackQuery):
    if not await require_sub(call):
        return
    await call.message.edit_text(
        "👑 <b>Telegram Premium</b>\n\n"
        "Muddatni tanlang:\n"
        "🗓 <b>1 oy</b> – 42 000 so'm\n"
        "🗓 <b>3 oy</b> – 160 000 so'm\n"
        "🗓 <b>6 oy</b> – 210 000 so'm\n"
        "🗓 <b>12 oy</b> – 370 000 so'm\n\n"
        "Tanlang, keyin nechta oy kerakligini yozasiz👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="1 oy – 42 000 so'm", callback_data="premium:1")],
                [InlineKeyboardButton(text="3 oy – 160 000 so'm", callback_data="premium:3")],
                [InlineKeyboardButton(text="6 oy – 210 000 so'm", callback_data="premium:6")],
                [InlineKeyboardButton(text="12 oy – 370 000 so'm", callback_data="premium:12")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data.startswith("premium:"))
async def premium_select(call: CallbackQuery, state: FSMContext):
    months = int(call.data.split(":")[1])
    from bot import PREMIUM_RATES
    price = PREMIUM_RATES[months]
    await state.update_data(item_type="premium", months=months, price=price, txn_id=f"PRM{call.from_user.id}{months}")
    await state.set_state(PremiumOrder.recipient)
    await call.message.edit_text(
        f"👑 Premium: <b>{months} oy</b> | 💵 <b>{price:,} so'm</b>\n\n"
        "👤 <b>Kimga sotib olmoqchisiz?</b>\n"
        "Telegram username'ni kiriting (masalan <code>@username</code>) yoki pastdagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 O'zim uchun", callback_data="prem_rec:self")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(PremiumOrder.recipient, F.data == "prem_rec:self")
async def prem_recipient_self(call: CallbackQuery, state: FSMContext):
    await state.update_data(recipient=f"@{call.from_user.username or call.from_user.id}")
    await state.set_state(PremiumOrder.confirm)
    await show_premium_confirm(call.message, state)
    await call.answer()


@router.message(PremiumOrder.recipient)
async def prem_recipient_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.startswith("@") and not text.replace("@", "").replace("_", "").isalnum():
        await message.answer("❌ Noto'g'ri username. Masalan: <code>@username</code> kabi yozing.")
        return
    await state.update_data(recipient=text if text.startswith("@") else f"@{text}")
    await state.set_state(PremiumOrder.confirm)
    await show_premium_confirm(message, state)


async def show_premium_confirm(msg_or_call, state: FSMContext):
    data = await state.get_data()
    recipient = data.get("recipient", "—")
    balance = await get_balance(msg_or_call.from_user.id if hasattr(msg_or_call, "from_user") else msg_or_call.chat.id)
    diff = data["price"] - balance
    if diff > 0:
        bal_line = f"💰 Balans: <b>{balance:,} so'm</b> · ❌ <b>{diff:,} so'm kam</b>"
    else:
        bal_line = f"💰 Balans: <b>{balance:,} so'm</b> · ✅ <b>To'lov balansdan</b>"
    text = (
        f"✅ <b>Premium buyurtma</b>\n\n"
        f"👑 Muddat: <b>{data['months']} oy</b>\n"
        f"💵 Narx: <b>{data['price']:,} so'm</b>\n"
        f"👤 Kimga: <b>{recipient}</b>\n"
        f"{bal_line}\n\n"
        f"Ijobiy bo'lsa tasdiqlang👇"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="premium:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
            ],
            [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="menu:card")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
        ]
    )
    try:
        await msg_or_call.edit_text(text, reply_markup=kb)
    except Exception:
        await msg_or_call.answer(text, reply_markup=kb)


@router.callback_query(F.data == "premium:confirm")
async def premium_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = call.from_user
    balance = await get_balance(user.id)

    if balance >= data["price"]:
        await update_balance(user.id, -data["price"])
        purchase_id = await add_purchase(
            user_id=user.id,
            username=user.username or "",
            item_type=data.get("item_type", "premium"),
            amount=str(data.get("months", "")),
            price=data["price"],
            txn_id=f"PRM{user.id}{data.get('months', '')}",
        )
        await update_purchase(purchase_id, "approved")
        uname = f"@{user.username}" if user.username else f"{user.first_name or user.id} (username yo'q)"
        caption = (
            f"🆕 <b>Balansdan buyurtma!</b>  (#{purchase_id})\n"
            f"────────────────\n"
            f"👤 Foydalanuvchi: <b>{uname}</b>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📦 Turi: <b>👑 {data.get('months', '')} oy Premium</b>\n"
            f"💵 Narx: <b>{data['price']:,} so'm</b>\n"
            f"👤 Kimga: <b>{data.get('recipient', '—')}</b>\n\n"
            f"To'lov balansdan ayirildi ✅"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📦 Bajarildi", callback_data=f"deliver:{purchase_id}")]]
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, caption, reply_markup=kb)
            except Exception:
                pass
        if ORDERS_CHANNEL:
            try:
                await bot.send_message(ORDERS_CHANNEL, caption, reply_markup=kb)
            except Exception:
                pass
        await call.message.edit_text(
            "✅ <b>Buyurtmangiz balansdan to'landi!</b>\n\n"
            f"👑 {data.get('months', '')} oy Premium\n"
            f"💵 {data['price']:,} so'm\n\n"
            f"💰 Qolgan balans: {await get_balance(user.id):,} so'm\n\n"
            "Tez orada sizga topshiriladi. Rahmat! 🙌",
        )
        await state.clear()
        await call.answer()
        return

    from bot import CARD_NUMBER, CARD_NAME, CARD_BANK, PAYMENT_NOTE
    await state.set_state(PaymentConfirm.waiting_proof)
    await call.message.edit_text(
        "💳 <b>To'lov uchun:</b>\n\n"
        f"🏦 Bank: <b>{CARD_BANK}</b>\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Ism: <b>{CARD_NAME}</b>\n\n"
        f"📝 {PAYMENT_NOTE}\n\n"
        f"👑 <b>{data['months']} oy Premium</b> | 💵 <b>{data['price']:,} so'm</b>\n"
        f"👤 Kimga: <b>{data.get('recipient', '—')}</b>\n"
        f"💰 Balans: <b>{balance:,} so'm</b> · ❌ <b>{data['price'] - balance:,} so'm kam</b>\n\n"
        f"To'lovni qilib, chek yuboring👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="menu:card")],
                [InlineKeyboardButton(text="✅ To'ladim, chek yuboraman", callback_data="pay:start")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data == "pay:start")
async def pay_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentConfirm.waiting_proof)
    await call.message.answer("📎 <b>Chek/skrinshot rasmini yuboring.</b>")
    await call.answer()


@router.callback_query(F.data == "menu:card")
async def menu_card(call: CallbackQuery, state: FSMContext):
    if not await require_sub(call):
        return
    await state.set_state(BalanceTopUp.amount)
    await call.message.edit_text(
        "💰 <b>Balans to'ldirish</b>\n\n"
        "Qancha summa kiritmoqchisiz?\n"
        "Minimal: <b>1 000 so'm</b>\n\n"
        "Summani raqam bilan yozing. Masalan: <code>10000</code>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")]]
        ),
    )
    await call.answer()


@router.message(BalanceTopUp.amount)
async def balance_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "")
    if not text.isdigit() or int(text) < 1000:
        await message.answer("❌ Minimal summa <b>1 000 so'm</b>. Yana bir marta yozing:")
        return
    amount = int(text)
    await state.update_data(amount=amount)
    await state.set_state(BalanceTopUp.confirm)
    await message.answer(
        f"✅ <b>Balans to'ldirish</b>\n\n"
        f"💰 Summa: <b>{amount:,} so'm</b>\n\n"
        f"Ijobiy bo'lsa, <b>to'lovga o'tish</b> tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 To'lovga o'tish", callback_data="balance:pay")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )


@router.callback_query(BalanceTopUp.confirm, F.data == "balance:pay")
async def balance_pay(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    await state.set_state(PaymentConfirm.waiting_proof)
    await state.update_data(item_type="balance", txn_id=f"BAL{call.from_user.id}{amount}")
    from bot import CARD_NUMBER, CARD_NAME, CARD_BANK, PAYMENT_NOTE
    await call.message.edit_text(
        "💳 <b>To'lov uchun:</b>\n\n"
        f"🏦 Bank: <b>{CARD_BANK}</b>\n"
        f"💳 Karta: <code>{CARD_NUMBER}</code>\n"
        f"👤 Ism: <b>{CARD_NAME}</b>\n\n"
        f"📝 {PAYMENT_NOTE}\n\n"
        f"💰 <b>{amount:,} so'm</b> — balans to'ldirish\n\n"
        f"To'lovni amalga oshirib, chek/bank apps skrinshotini yuboring👇",
    )
    await call.message.answer("📎 <b>Chek/skrinshot rasmini yuboring.</b>")
    await call.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(call: CallbackQuery):
    if not await require_sub(call):
        return
    await call.message.edit_text(
        "ℹ️ <b>Yordam</b>\n\n"
        "⭐ Stars sotib olish:\n"
        "  1. 'Telegram Stars' bo'limini tanlang\n"
        "  2. Miqdorni yozing\n"
        "  3. Karta orqali to'lang\n"
        "  4. Chekni yuboring\n\n"
        "👑 Premium sotib olish:\n"
        "  1. 'Telegram Premium' ni tanlang\n"
        "  2. Muddatni tanlang\n"
        "  3. To'lab chek yuboring\n\n"
        "Admin tekshirgach, buyurtmangiz bajariladi.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")]]
        ),
    )
    await call.answer()


@router.callback_query(F.data == "menu:profile")
async def menu_profile(call: CallbackQuery, state: FSMContext):
    if not await require_sub(call):
        return
    await state.clear()
    user = call.from_user
    db_user = await get_user(user.id)
    if not db_user:
        await add_user(user.id, user.username or "", user.first_name or "")
        db_user = await get_user(user.id)
    balance = db_user["balance"] if db_user else 0
    text = (
        "👤 <b>Mening profilim</b>\n"
        "──────────────\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Username: @{user.username or '—'}\n"
        f"✏️ Ism: <b>{user.first_name or '—'}</b>\n"
        f"💰 Balans: <b>{balance:,} so'm</b>\n"
        f"🗓 Ro'yxatdan o'tgan: {db_user['created_at'][:10] if db_user else '—'}\n"
        "──────────────"
    )
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📜 Buyurtma tarixim", callback_data="profile:orders")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:back")],
            ]
        ),
    )
    await call.answer()


@router.callback_query(F.data == "profile:orders")
async def profile_orders(call: CallbackQuery, state: FSMContext):
    orders = await user_purchases(call.from_user.id, 10)
    if not orders:
        text = "📜 <b>Buyurtma tarixi</b>\n\nHozircha buyurtmalar yo'q."
    else:
        text = "📜 <b>Buyurtma tarixi</b>\n──────────────\n"
        for o in orders:
            status_map = {
                "pending": "⏳ Kutilmoqda",
                "approved": "✅ Tasdiqlandi",
                "completed": "📦 Bajarildi",
                "rejected": "❌ Rad etildi",
            }
            status = status_map.get(o["status"], o["status"])
            item = f"{o['amount']} Stars" if o["item_type"] == "stars" else f"{o['amount']} oy Premium"
            text += (
                f"#{o['id']} · {item}\n"
                f"   💵 {o['price']:,} so'm · {status}\n"
                f"   🗓 {o['created_at'][:16]}\n"
                "──────────────\n"
            )
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:profile")],
            ]
        ),
    )
    await call.answer()
