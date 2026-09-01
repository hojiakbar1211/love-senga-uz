from aiogram.fsm.state import State, StatesGroup


class StarsOrder(StatesGroup):
    amount = State()
    recipient = State()
    confirm = State()


class PremiumOrder(StatesGroup):
    months = State()
    recipient = State()
    confirm = State()


class PaymentConfirm(StatesGroup):
    waiting_proof = State()


class BalanceTopUp(StatesGroup):
    amount = State()
    confirm = State()


class SupportForm(StatesGroup):
    message = State()