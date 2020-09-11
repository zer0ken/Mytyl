from discord.ext.commands import Cog, Bot

from utils import get_cog


class CustomCog(Cog):
    def __init__(self, bot: Bot):
        self.literal = get_cog(self.__class__.__name__)

        async def after_ready_():
            await bot.wait_until_ready()
            await self.after_ready()

        bot.loop.create_task(after_ready_())

    async def after_ready(self):
        pass

    async def is_completed(self):
        return True
