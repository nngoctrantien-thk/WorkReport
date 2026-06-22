class TelegramActivity:

    @staticmethod
    def execute(token, callback):
        """
        Start Telegram bot.

        Args:
            token (str): Telegram Bot Token.
            callback (callable): Function receives message text and returns reply.

        Example:
            TelegramActivity.execute(
                BOT_TOKEN,
                handle_message
            )
        """

        telegram = TelegramService(token)

        telegram.register_message_handler(callback)

        telegram.run()