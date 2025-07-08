
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import telegram
import time
from keepalive import keep_alive
keep_alive()
TOKEN = "7539077469:AAGsx1yah5ggTa6aCo1niApca3uiPvq0AdU"

VIDEO_TIMER = 100
UPDATE_INTERVAL = 2
CALLBACK_TIMEOUT = 5

CHANNEL_1_ID = "-1002869672048"
CHANNEL_2_ID = "-1002377596183"
PREVIEW_CHANNEL_ID = "-1002328379313"
PRIVATE_CHANNEL_ID = "-1002621336219"

CHANNEL_1 = "https://t.me/+k1LqFyo1IkViMDA1"
CHANNEL_2 = "https://t.me/CYBOTOOLS"
PREVIEW_CHANNEL = "https://t.me/+k1LqFyo1IkViMDA1"
PRIVATE_CHANNEL = "https://t.me/+IA8F0X3Klt8xNzM1"

CHANNEL_ID = PRIVATE_CHANNEL_ID.replace("-100", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Join Channel 1", url=CHANNEL_1)],
        [InlineKeyboardButton("Join Channel 2", url=CHANNEL_2)],
        [InlineKeyboardButton("✅ Check Membership", callback_data='check_membership')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "👋 Welcome! Please join our channels:\n\n"
        "1️⃣ First Channel\n"
        "2️⃣ Second Channel\n\n"
        "After joining both channels, click the Check button below!"
    )

    await update.message.reply_text(text, reply_markup=reply_markup)
    context.user_data['membership_checked'] = False

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if not member.is_bot:
            await update.message.reply_text(
                f"Welcome {member.mention_html()}! 👋\n"
                "Thank you for joining our channel!",
                parse_mode='HTML'
            )

async def check_member(user_id: int, channel_id: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except telegram.error.BadRequest:
        return False

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer(cache_time=CALLBACK_TIMEOUT)

        user_id = query.from_user.id
        is_member_1 = await check_member(user_id, CHANNEL_1_ID, context)
        is_member_2 = await check_member(user_id, CHANNEL_2_ID, context)

        if not is_member_1 or not is_member_2:
            keyboard = [
                [InlineKeyboardButton("Join Channel 1", url=CHANNEL_1)],
                [InlineKeyboardButton("Join Channel 2", url=CHANNEL_2)],
                [InlineKeyboardButton("✅ Check Again", callback_data='check_membership')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = "❌ You must join both channels:\n\n"
            if not is_member_1:
                text += "• Not joined Channel 1\n"
            if not is_member_2:
                text += "• Not joined Channel 2\n"

            await query.edit_message_text(text, reply_markup=reply_markup)
            context.user_data['membership_checked'] = False
            return

        keyboard = [[InlineKeyboardButton("🎥 Browse Videos", callback_data='show_videos')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "✅ Successfully verified! You've joined both channels.\nClick below to browse videos:",
            reply_markup=reply_markup
        )
        context.user_data['membership_checked'] = True
    except telegram.error.BadRequest:
        keyboard = [
            [InlineKeyboardButton("🔄 Start Again", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "⚠️ Session expired. Please try again.",
            reply_markup=reply_markup
        )

async def show_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer(cache_time=CALLBACK_TIMEOUT)

        user_id = query.from_user.id
        is_member_1 = await check_member(user_id, CHANNEL_1_ID, context)
        is_member_2 = await check_member(user_id, CHANNEL_2_ID, context)

        if not is_member_1 or not is_member_2:
            await check_membership(update, context)
            return

        keyboard = [
            [InlineKeyboardButton("🎥 Preview Channel", url=PREVIEW_CHANNEL)],
            [InlineKeyboardButton("⬅️ Back", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            "📝 Instructions:\n\n"
            "1️⃣ Click 'Preview Channel' button to see videos\n"
            "2️⃣ Copy the video number from preview channel\n"
            "3️⃣ Come back here and send the number\n\n"
            "The video will be sent to you!"
        )

        await query.edit_message_text(text, reply_markup=reply_markup)
        context.user_data['waiting_for_number'] = True
    except telegram.error.BadRequest:
        keyboard = [
            [InlineKeyboardButton("🔄 Start Again", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "⚠️ Session expired. Please try again.",
            reply_markup=reply_markup
        )

async def handle_video_timer(context, chat_id, sent_msg, user_msg):
    try:
        remaining_time = VIDEO_TIMER
        last_caption = ""
        while remaining_time >= 0:
            try:
                caption = f"⚠️ Video will disappear in {remaining_time} seconds!\nPlease save this video or forward to save"
                if caption != last_caption:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=sent_msg.message_id,
                        caption=caption
                    )
                    last_caption = caption
                await asyncio.sleep(1)
                remaining_time -= 1
            except telegram.error.BadRequest as e:
                if "not modified" not in str(e).lower():
                    print(f"Caption edit error: {e}")
                await asyncio.sleep(1)
                remaining_time -= 1
                continue

        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
            if isinstance(user_msg, telegram.Message):
                await user_msg.delete()
        except telegram.error.BadRequest as e:
            print(f"Delete error: {e}")

        keyboard = [
            [InlineKeyboardButton("🎥 Preview Channel", url=PREVIEW_CHANNEL)],
            [InlineKeyboardButton("⬅️ Back", callback_data='check_membership')]
        ]
        text = (
            "📝 Want to watch another video?\n\n"
            "1️⃣ Click 'Preview Channel' button\n"
            "2️⃣ Copy the video number\n"
            "3️⃣ Send the number here"
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Timer error: {e}")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_number'):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    is_member_1 = await check_member(user_id, CHANNEL_1_ID, context)
    is_member_2 = await check_member(user_id, CHANNEL_2_ID, context)

    if not is_member_1 or not is_member_2:
        keyboard = [
            [InlineKeyboardButton("Join Channel 1", url=CHANNEL_1)],
            [InlineKeyboardButton("Join Channel 2", url=CHANNEL_2)],
            [InlineKeyboardButton("✅ Check Membership", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("❌ Please rejoin the channels first!", reply_markup=reply_markup)
        context.user_data['waiting_for_number'] = False
        return

    try:
        text = update.message.text
        if "https://t.me/c/" in text:
            msg_id = int(text.split("/")[-1])
        elif "/" in text:
            msg_id = int(text.split("/")[-1])
        else:
            msg_id = int(text)

        try:
            sent_msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=PRIVATE_CHANNEL_ID,
                message_id=msg_id,
                protect_content=False,
                caption=f"⚠️ Video will disappear in {VIDEO_TIMER} seconds!\nPlease save this video or forward to save"
            )

            if sent_msg:
                asyncio.create_task(
                    handle_video_timer(context, chat_id, sent_msg, update.message)
                )

        except telegram.error.BadRequest as e:
            print(f"Error sending video: {e}")
            keyboard = [
                [InlineKeyboardButton("🎥 Preview Channel", url=PREVIEW_CHANNEL)],
                [InlineKeyboardButton("⬅️ Back", callback_data='check_membership')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Video not found. Please check the number and try again:",
                reply_markup=reply_markup
            )

    except ValueError:
        keyboard = [
            [InlineKeyboardButton("🎥 Preview Channel", url=PREVIEW_CHANNEL)],
            [InlineKeyboardButton("⬅️ Back", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Please enter a valid video number:",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error handling number: {e}")
        await update.message.reply_text("Error processing video. Please try again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error occurred: {context.error}")
    if isinstance(context.error, telegram.error.BadRequest):
        if "Query is too old" in str(context.error):
            try:
                if update.callback_query:
                    await update.callback_query.answer()
                    keyboard = [
                        [InlineKeyboardButton("🔄 Start Again", callback_data='check_membership')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.callback_query.message.reply_text(
                        "⚠️ Session expired. Please try again.",
                        reply_markup=reply_markup
                    )
            except:
                pass

def main():
    application = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(100)
        .pool_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .get_updates_read_timeout(60)
        .get_updates_pool_timeout(60)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_membership, pattern="^check_membership$"))
    application.add_handler(CallbackQueryHandler(show_videos, pattern="^show_videos$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    application.add_error_handler(error_handler)

    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
