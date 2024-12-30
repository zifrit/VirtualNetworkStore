from aiogram.fsm.state import StatesGroup, State


class BuyVPN(StatesGroup):
    country = State()
    price = State()
