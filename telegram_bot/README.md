# Telegram Stars & Premium Bot

Telegram Stars va Premium sotuv boti. Karta orqali to'lov, admin panel bilan.

## Xususiyatlar

- ⭐ **Stars** — istalgan miqdorda, 1 Stars = 100 so'm
- 👑 **Premium** — 1, 3, 6, 12 oy
- 💳 Karta orqali to'lov (chek rasmini yuborish)
- 🛡 Admin panel: foydalanuvchilar, buyurtmalar, kutilayotganlar, statistika
- 🗄 SQLite ma'lumotlar bazasi

## 1. Bot yaratish (BotFather)

1. Telegram'da **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username yozing
4. Sizga **token** beriladi — uni saqlang

## 2. O'rnatish (local test)

```bash
cd telegram_bot
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

copy .env.example .env   # keyin .env ni to'ldiring
python main.py
```

**.env** faylini to'ldiring:
```
BOT_TOKEN=BotFather dan olingan token
ADMIN_IDS=sizning telegram ID (vergul bilan bir nechta)
CARD_NUMBER=karta raqamingiz
CARD_NAME=karta egasi ismi
CARD_BANK=bank nomi
PAYMENT_NOTE=komment uchun eslatma
```

> **Admin ID ni topish:** `/start` bosganingizda admin bo'lsangiz bot "Sizning ID: ..." deb yozadi. Avval shu ID'ni `.env` ga qo'ying.

## 3. Koyeb.com ga deploy (bepul)

1. **GitHub** ga `telegram_bot` papkasini yuklang (repo yarating, `git push`)
2. [app.koyeb.com](https://app.koyeb.com) ga kiring (GitHub orqali sign up)
3. **Create Service** → **GitHub** ni tanlang → repongizni tanlang
4. Sozlamalar:
   - **Builder:** `Dockerfile`
   - **Instance type:** `nano` (bepul)
5. **Environment variables** (muhit o'zgaruvchilari) qo'shing:
   - `BOT_TOKEN`, `ADMIN_IDS`, `CARD_NUMBER`, `CARD_NAME`, `CARD_BANK`, `PAYMENT_NOTE`
6. **Deploy** bosing

> ⚠️ SQLite ma'lumotlar bepul tier'da qayta ishga tushganda o'chib ketishi mumkin. Ma'lumotlar doimiy saqlanishi uchun render'da Python boshqarilsin yoki jiddiy loyiha uchun PostgreSQL (Railway) ishlating.

## Foydalanish

- Foydalanuvchilar `/start` bosib buyurtma beradi
- Admin `/admin` buyrug'i bilan panelni ochadi
- Chek rasm Yuborilganda adminlarga tasdiqlash/rad etish tugmasi keladi

## Muammolar

Agar bot ishlamasa:
1. `.env` da token to'g'riligini tekshiring
2. `ADMIN_IDS` da o'z ID'ingiz borligini tekshiring
3. Google Koyeb loglaridan xatoni ko'ring
