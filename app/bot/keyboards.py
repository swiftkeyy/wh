from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.config import settings


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Создать", callback_data="menu:create"),
                InlineKeyboardButton(text="Редактировать", callback_data="menu:edit"),
            ],
            [
                InlineKeyboardButton(text="Шаблоны", callback_data="menu:templates"),
                InlineKeyboardButton(text="Тарифы", callback_data="menu:pricing"),
            ],
            [
                InlineKeyboardButton(text="Баланс", callback_data="menu:balance"),
                InlineKeyboardButton(text="История", callback_data="menu:history"),
            ],
            [
                InlineKeyboardButton(text="Покупки", callback_data="menu:purchases"),
            ],
        ]
    )


def quick_modes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Улучшить фото", callback_data="mode:photo_enhance")],
            [InlineKeyboardButton(text="Удалить фон", callback_data="mode:transparent_bg")],
            [InlineKeyboardButton(text="Кинопостер", callback_data="mode:movie_poster")],
            [InlineKeyboardButton(text="Экшн-фигурка", callback_data="mode:action_figure")],
        ]
    )


def pricing_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for pack in settings.purchase_packs:
        rows.append([InlineKeyboardButton(text=f"Купить {pack['title']}", callback_data=f"buy_pack:{pack['sku']}")])
    for plan in settings.subscription_plans:
        rows.append([InlineKeyboardButton(text=f"Подписка {plan['title']}", callback_data=f"buy_sub:{plan['code']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
