from aiogram.fsm.state import StatesGroup, State


class ExtendVirtualNetwork(StatesGroup):
    virtual_network_key = State()
