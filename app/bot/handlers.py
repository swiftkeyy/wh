from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from app.bot.keyboards import main_menu_keyboard, pricing_keyboard, quick_modes_keyboard
from app.core.config import settings
from app.services.admin import AdminService
from app.services.billing import BillingService
from app.services.job_service import JobService
from app.services.ledger import LedgerService
from app.services.pricing_policy import PricingPolicyService
from app.services.user_context import UserContextService

router = Router()
user_context = UserContextService()
job_service = JobService()
ledger_service = LedgerService()
pricing_policy = PricingPolicyService()
billing_service = BillingService()
admin_service = AdminService()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await user_context.ensure_user(
        telegram_user_id=message.from_user.id,
        username=message.from_user.username,
        language_code=message.from_user.language_code,
    )
    text = (
        f"Добро пожаловать в {settings.app_name}.\n\n"
        "Это Telegram-first AI studio для генерации и редактирования изображений.\n"
        "Начни с готового режима, открой тарифы или сразу загрузи фото."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:create")
async def menu_create_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Выбери стартовый режим. Для launch лучше вести пользователя через mode-first UX.",
        reply_markup=quick_modes_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:pricing")
async def menu_pricing_handler(callback: CallbackQuery) -> None:
    await callback.message.answer(pricing_policy.pricing_screen_text(), reply_markup=pricing_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:balance")
async def menu_balance_handler(callback: CallbackQuery) -> None:
    balance = await ledger_service.get_user_balance_by_telegram_id(callback.from_user.id)
    subscription_summary = await billing_service.get_active_subscription_summary(callback.from_user.id)
    await callback.message.answer(
        "Баланс WHYNOT Photoshop\n\n"
        f"Доступно кредитов: {balance}\n"
        f"Удалить фон сейчас стоит: {pricing_policy.get_job_price('transparent_bg')} кредита\n"
        f"{subscription_summary}"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:history")
async def menu_history_handler(callback: CallbackQuery) -> None:
    history = await ledger_service.get_recent_user_history_by_telegram_id(callback.from_user.id)
    if not history:
        text = "История операций пока пустая."
    else:
        lines = [
            f"- {entry.direction} {entry.amount} | {entry.reason} | balance={entry.balance_after} | {entry.entry_status}"
            for entry in history
        ]
        text = "Последние операции по кредитам\n\n" + "\n".join(lines)
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "menu:purchases")
async def menu_purchases_handler(callback: CallbackQuery) -> None:
    purchases = await billing_service.get_recent_purchase_history(callback.from_user.id)
    if not purchases:
        text = "Покупок пока нет."
    else:
        lines = [
            f"- {purchase.purchase_type} {purchase.sku} | {purchase.status} | {purchase.amount_minor} {purchase.currency}"
            for purchase in purchases
        ]
        text = "Последние покупки\n\n" + "\n".join(lines)
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def mode_select_handler(callback: CallbackQuery) -> None:
    mode_code = callback.data.split(":", 1)[1]
    await user_context.set_pending_mode(callback.from_user.id, mode_code)
    await callback.message.answer(
        f"Режим `{mode_code}` выбран.\n"
        "Следующий шаг: загрузи фото или пришли текстовый запрос, в зависимости от режима.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(F.photo)
async def photo_handler(message: Message) -> None:
    pending_mode = await user_context.get_pending_mode(message.from_user.id)
    if pending_mode != "transparent_bg":
        await message.answer(
            "Фото получено. Для первого рабочего сценария выбери режим `Удалить фон`, и я запущу обработку.",
            parse_mode="Markdown",
        )
        return

    largest_photo = message.photo[-1]
    file_info = await message.bot.get_file(largest_photo.file_id)
    file_buffer = await message.bot.download(file_info.file_path)
    image_bytes = file_buffer.read()

    job_id = await job_service.create_remove_bg_job(
        telegram_user_id=message.from_user.id,
        image_bytes=image_bytes,
        mime_type="image/jpeg",
    )
    await user_context.set_pending_mode(message.from_user.id, None)
    await message.answer(
        f"Задача создана.\nJob ID: `{job_id}`\nИзображение поставлено в очередь на удаление фона.",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("buy_pack:"))
async def buy_pack_handler(callback: CallbackQuery) -> None:
    sku = callback.data.split(":", 1)[1]
    pack = pricing_policy.get_purchase_pack(sku)
    if not pack:
        await callback.message.answer("Пакет не найден.")
        await callback.answer()
        return
    intent = await billing_service.create_pack_purchase(telegram_user_id=callback.from_user.id, pack=pack)
    await billing_service.send_stars_invoice(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        title=pack["title"],
        description=f"{pack['credits']} кредитов для WHYNOT Photoshop",
        intent=intent,
    )
    await callback.answer("Инвойс отправлен")


@router.callback_query(F.data.startswith("buy_sub:"))
async def buy_subscription_handler(callback: CallbackQuery) -> None:
    code = callback.data.split(":", 1)[1]
    plan = pricing_policy.get_subscription_plan(code)
    if not plan:
        await callback.message.answer("Тариф не найден.")
        await callback.answer()
        return
    intent = await billing_service.create_subscription_purchase(telegram_user_id=callback.from_user.id, plan=plan)
    await billing_service.send_stars_invoice(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        title=plan["title"],
        description=f"{plan['credits_monthly']} кредитов в месяц для WHYNOT Photoshop",
        intent=intent,
    )
    await callback.answer("Инвойс отправлен")


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    await billing_service.answer_pre_checkout(
        bot=pre_checkout_query.bot,
        pre_checkout_query_id=pre_checkout_query.id,
        ok=True,
    )


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    successful_payment = message.successful_payment
    result_text = await billing_service.confirm_successful_payment(
        telegram_user_id=message.from_user.id,
        payload=successful_payment.invoice_payload,
        telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        provider_payment_charge_id=successful_payment.provider_payment_charge_id,
        total_amount=successful_payment.total_amount,
    )
    await message.answer(result_text)


@router.message(Command("balance"))
async def balance_command_handler(message: Message) -> None:
    balance = await ledger_service.get_user_balance_by_telegram_id(message.from_user.id)
    await message.answer(
        "Баланс WHYNOT Photoshop\n\n"
        f"Доступно кредитов: {balance}\n"
        f"Welcome bonus: {pricing_policy.get_welcome_credits()}"
    )


@router.message(Command("pricing"))
async def pricing_command_handler(message: Message) -> None:
    await message.answer(pricing_policy.pricing_screen_text(), reply_markup=pricing_keyboard())


@router.message(Command("history"))
async def history_command_handler(message: Message) -> None:
    history = await ledger_service.get_recent_user_history_by_telegram_id(message.from_user.id)
    if not history:
        await message.answer("История операций пока пустая.")
        return
    lines = [
        f"- {entry.direction} {entry.amount} | {entry.reason} | balance={entry.balance_after} | {entry.entry_status}"
        for entry in history
    ]
    await message.answer("Последние операции по кредитам\n\n" + "\n".join(lines))


@router.message(Command("purchases"))
async def purchases_command_handler(message: Message) -> None:
    purchases = await billing_service.get_recent_purchase_history(message.from_user.id)
    if not purchases:
        await message.answer("Покупок пока нет.")
        return
    lines = [
        f"- {purchase.purchase_type} {purchase.sku} | {purchase.status} | {purchase.amount_minor} {purchase.currency}"
        for purchase in purchases
    ]
    await message.answer("Последние покупки\n\n" + "\n".join(lines))


@router.message(Command("account"))
async def account_command_handler(message: Message) -> None:
    balance = await ledger_service.get_user_balance_by_telegram_id(message.from_user.id)
    subscription_summary = await billing_service.get_active_subscription_summary(message.from_user.id)
    purchases = await billing_service.get_recent_purchase_history(message.from_user.id, limit=3)
    purchase_lines = (
        "\n".join([f"- {purchase.sku} | {purchase.status} | {purchase.amount_minor} {purchase.currency}" for purchase in purchases])
        if purchases
        else "- покупок пока нет"
    )
    text = (
        "Аккаунт WHYNOT Photoshop\n\n"
        f"Баланс: {balance} кредитов\n"
        f"{subscription_summary}\n\n"
        "Последние покупки:\n"
        f"{purchase_lines}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("admin_credits"))
async def admin_credits_command_handler(message: Message) -> None:
    if not admin_service.is_admin(message.from_user.id):
        await message.answer("Команда недоступна.")
        return

    parts = (message.text or "").split(maxsplit=4)
    if len(parts) < 5:
        await message.answer("Формат: /admin_credits <telegram_user_id> <credit|debit> <amount> <reason>")
        return

    target_telegram_user_id = int(parts[1])
    direction = parts[2]
    amount = int(parts[3])
    reason = parts[4]
    new_balance = await admin_service.adjust_credits(
        admin_telegram_user_id=message.from_user.id,
        target_telegram_user_id=target_telegram_user_id,
        direction=direction,
        amount=amount,
        reason=reason,
    )
    await message.answer(
        f"Операция выполнена.\nUser: {target_telegram_user_id}\nDirection: {direction}\nAmount: {amount}\nNew balance: {new_balance}"
    )


@router.message(Command("admin_audit"))
async def admin_audit_command_handler(message: Message) -> None:
    if not admin_service.is_admin(message.from_user.id):
        await message.answer("Команда недоступна.")
        return
    text = await admin_service.get_audit_report_text(limit=5)
    await message.answer(text, parse_mode="Markdown")
