from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext


async def clear_last_results_keyboard(bot: Bot, state: FSMContext, chat_id: int):
    data = await state.get_data()
    message_id = data.get("results_message_id")
    if not message_id:
        return

    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=None
        )
    except TelegramBadRequest:
        pass


async def clear_after_card_message(bot: Bot, state: FSMContext, chat_id: int):
    data = await state.get_data()
    message_id = data.get("after_card_message_id")
    if not message_id:
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass
