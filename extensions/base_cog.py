from discord.ext.commands import Context

import custom
from custom import CustomBot
from custom.cog import CustomCog
from utils import get_cog


class BaseCog(CustomCog, name=get_cog('BaseCog')['name']):
    def __init__(self, bot: CustomBot):
        super().__init__(bot)
        self.bot = bot

    @custom.core.command(name='핑')
    async def ping(self, ctx: Context):
        response = await ctx.send('pong')
        await response.edit(content=response.content + f'({response.created_at - ctx.message.created_at})')


def setup(bot: CustomBot):
    bot.add_cog(BaseCog(bot))
