from discord import Status, Member
from discord.ext.commands import Context

import custom
from custom import CustomBot, CustomCog
from custom.core import owner_only, on_status
from utils import get_cog


class BaseCog(CustomCog, name=get_cog('BaseCog')['name']):
    def __init__(self, bot: CustomBot):
        super().__init__(bot)
        self.bot = bot

    @custom.core.command(name='핑')
    @owner_only()
    @on_status(Status.online)
    async def ping(self, ctx: Context):
        response = await ctx.send('pong')
        await response.edit(content=response.content + f'({response.created_at - ctx.message.created_at})')


def setup(bot: CustomBot):
    bot.add_cog(BaseCog(bot))