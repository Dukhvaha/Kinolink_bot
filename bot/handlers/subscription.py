from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.reply import main_keyboard
from bot.services.subscription import is_subscribed

router = Router()


@router.callback_query(F.data == "check_subscription")
async def handle_subscription_check(callback: CallbackQuery, bot: Bot):
    if not await is_subscribed(bot, callback.from_user.id):
        await callback.answer("Подписка пока не найдена.", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        "✅ Отлично, подписка подтверждена!\n\n"
        "Теперь можно искать фильмы и сериалы.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    await callback.answer()
