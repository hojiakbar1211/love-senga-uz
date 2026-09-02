from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot import bot, ADMIN_IDS, ORDERS_CHANNEL
from database import add_purchase, add_user, update_purchase, get_purchase, update_balance, get_balance
from handlers.states import PaymentConfirm

router = Router()


@router.message(PaymentConfirm.waiting_proof, F.photo)
async def receive_proof(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()

    purchase_id = await add_purchase(
        user_id=user.id,
        username=user.username or "",
        item_type=data.get("item_type", "unknown"),
        amount=str(data.get("price", data.get("amount", data.get("months", "")))),
        price=data.get("price", data.get("amount", 0)),
        txn_id=data.get("txn_id", ""),
    )

    uname = f"@{user.username}" if user.username else f"{user.first_name or user.id} (username yo'q)"
    recipient = data.get("recipient", "—")

    item_type = data.get("item_type", "unknown")
    item_label = {
        "stars": f"⭐ {data.get('amount', '')} Stars",
        "premium": f"👑 {data.get('months', '')} oy Premium",
        "balance": f"💰 Balans to'ldirish",
    }.get(item_type, item_type)

    # Kartaga tushadigan summa: buyurtma narxi (stars/premium) yoki kiritilgan summa (balance)
    paid_sum = data.get("price", data.get("amount", 0))

    caption = (
        f"🆕 <b>Yangi buyurtma!</b>  (#{purchase_id})\n"
        f"────────────────\n"
        f"👤 Foydalanuvchi: <b>{uname}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📦 Turi: <b>{item_label}</b>\n"
        f"{'👤 Kimga: <b>' + recipient + '</b>\n' if recipient and recipient != '—' else ''}"
        f"💳 <b>Kartaga tushadigan summa: {paid_sum:,} so'm</b>\n\n"
        f"⚠️ Foydalanuvchi tarafidan quyidagi chek yuborildi — "
        f"buning kartaga tushgan summasini tekshiring👇"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.copy_to(
                admin_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{purchase_id}"),
                            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{purchase_id}"),
                        ]
                    ]
                ),
            )
        except Exception:
            pass

    # Belgilangan kanalga ham yuboramiz (accept/reject tugmalari bilan)
    if ORDERS_CHANNEL:
        try:
            await message.copy_to(
                ORDERS_CHANNEL,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{purchase_id}"),
                            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{purchase_id}"),
                        ]
                    ]
                ),
            )
        except Exception:
            pass

    await message.answer(
        "✅ <b>Chek qabul qilindi!</b>\n\n"
        "Buyurtmangiz admin tomonidan ko'rib chiqilmoqda.\n"
        "Tasdiqlangach siz bilan bog'lanamiz. Rahmat! 🙌"
    )
    await state.clear()


@router.message(PaymentConfirm.waiting_proof)
async def no_photo(message: Message):
    await message.answer("❌ Iltimos, to'lov chekining <b>rasmini</b> yuboring.")


@router.callback_query(F.data.startswith("approve:"))
async def approve_purchase(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Siz admin emassiz", show_alert=True)
        return
    purchase_id = int(call.data.split(":")[1])
    row = await get_purchase(purchase_id)
    if not row:
        await call.answer("❌ Topilmadi", show_alert=True)
        return
    await update_purchase(purchase_id, "approved")
    # Faqat "balance" (balans to'ldirish) tipida balansga qo'shiladi.
    # Stars/Premium chek orqali tasdiqlanganda balans o'zgarmaydi.
    if row["item_type"] == "balance":
        await update_balance(row["user_id"], row["price"])

    await call.message.edit_caption(
        caption=call.message.caption.replace("🆕", "✅") + "\n\n<b>Status: TASDIQLANDI ✅</b>"
    )
    await call.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📦 Bajarildi", callback_data=f"deliver:{purchase_id}")],
            ]
        )
    )
    try:
        if row["item_type"] == "balance":
            msg = (
                "🎉 <b>To'lov tasdiqlandi!</b>\n\n"
                f"📦 <b>Balans to'ldirish</b> – {row['amount']:,} so'm\n"
                f"💰 Jami balans: {await get_balance(row['user_id']):,} so'm\n\n"
                "Rahmat! 🙌"
            )
        else:
            msg = (
                "🎉 <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
                f"📦 <b>{row['item_type']}</b> – {row['amount']}\n"
                f"💵 {row['price']:,} so'm\n\n"
                "Tez orada sizga topshiriladi. Rahmat! 🙌"
            )
        await bot.send_message(row["user_id"], msg)
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("deliver:"))
async def deliver_purchase(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Siz admin emassiz", show_alert=True)
        return
    purchase_id = int(call.data.split(":")[1])
    row = await get_purchase(purchase_id)
    if not row:
        await call.answer("❌ Topilmadi", show_alert=True)
        return
    await update_purchase(purchase_id, "completed")

    await call.message.edit_caption(
        caption=call.message.caption.replace("TASDIQLANDI ✅", "BAJARILDI 📦") + "\n\n<b>Status: BAJARILDI 📦</b>"
    )
    try:
        await bot.send_message(
            row["user_id"],
            "✅ <b>Buyurtmangiz bajarildi!</b>\n\n"
            f"📦 <b>{row['item_type']}</b> – {row['amount']}\n"
            f"💵 {row['price']:,} so'm\n\n"
            "Xizmatni olganingiz uchun rahmat! 🙌",
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("reject:"))
async def reject_purchase(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Siz admin emassiz", show_alert=True)
        return
    purchase_id = int(call.data.split(":")[1])
    row = await get_purchase(purchase_id)
    if not row:
        await call.answer("❌ Topilmadi", show_alert=True)
        return
    await update_purchase(purchase_id, "rejected")

    await call.message.edit_caption(
        caption=call.message.caption.replace("🆕", "❌") + "\n\n<b>Status: RAD ETILDI ❌</b>"
    )
    try:
        await bot.send_message(
            row["user_id"],
            "❌ <b>Buyurtmangiz rad etildi.</b>\n\n"
            "Savol bo'lsa admin bilan bog'laning.",
        )
    except Exception:
        pass
    await call.answer()
