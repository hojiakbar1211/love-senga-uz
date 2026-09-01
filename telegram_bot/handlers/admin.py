from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot import ADMIN_IDS
from database import all_users, all_purchases, pending_purchases

router = Router()

ADMIN_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin:users")],
        [InlineKeyboardButton(text="🛒 Buyurtmalar", callback_data="admin:orders")],
        [InlineKeyboardButton(text="⏳ Kutilayotgan", callback_data="admin:pending")],
        [InlineKeyboardButton(text="🧹 Statistika", callback_data="admin:stats")],
    ]
)


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda ruxsat yo'q")
        return
    await message.answer("🛡 <b>Admin panel</b>", reply_markup=ADMIN_KEYBOARD)


@router.callback_query(F.data == "admin:users")
async def admin_users(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    users = await all_users()
    text = "👤 <b>Foydalanuvchilar</b>\n" + "─" * 20 + "\n"
    for u in users:
        text += f"• <code>{u['id']}</code> @{u['username'] or '—'} | {u['first_name'] or ''}\n"
    text += f"\n👥 Jami: <b>{len(users)}</b>"
    await call.message.answer(text, reply_markup=back_btn())
    await call.answer()


@router.callback_query(F.data == "admin:orders")
async def admin_orders(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    orders = await all_purchases(50)
    text = "🛒 <b>So'nggi buyurtmalar</b>\n" + "─" * 20 + "\n"
    if not orders:
        text += "Hozircha buyurtma yo'q."
    for o in orders:
        status_icon = "📦" if o["status"] in ("approved", "completed") else ("❌" if o["status"] == "rejected" else "⏳")
        text += (
            f"{status_icon} #{o['id']} [{o['item_type']}] "
            f"{o['amount']} – {o['price']:,} so'm × @{o['username'] or '—'}\n"
        )
    await call.message.answer(text, reply_markup=back_btn())
    await call.answer()


@router.callback_query(F.data == "admin:pending")
async def admin_pending(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    rows = await pending_purchases()
    text = "⏳ <b>Kutilayotgan buyurtmalar</b>\n" + "─" * 20 + "\n"
    if not rows:
        text += "Barcha buyurtmalar ko'rib chiqilgan. ✅"
    for o in rows:
        text += f"#{o['id']} [{o['item_type']}] {o['amount']} – {o['price']:,} so'm × @{o['username'] or '—'}\n"
    await call.message.answer(text, reply_markup=back_btn())
    await call.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    orders = await all_purchases(100000)
    approved = [o for o in orders if o["status"] in ("approved", "completed")]
    total = sum(o["price"] for o in approved)
    users = await all_users()
    text = (
        "🧹 <b>Statistika</b>\n" + "─" * 20 + "\n"
        f"👥 Foydalanuvchilar: <b>{len(users)}</b>\n"
        f"🛒 Jami buyurtmalar: <b>{len(orders)}</b>\n"
        f"✅ Tasdiqlangan: <b>{len(approved)}</b>\n"
        f"💰 Foyda: <b>{total:,} so'm</b>"
    )
    await call.message.answer(text, reply_markup=back_btn())
    await call.answer()


@router.callback_query(F.data == "admin:back")
async def admin_back(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    await call.message.edit_text("🛡 <b>Admin panel</b>", reply_markup=ADMIN_KEYBOARD)
    await call.answer()


def back_btn():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")]]
    )
