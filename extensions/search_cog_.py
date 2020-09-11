from discord.ext import commands
from discord.ext.commands import Context

from custom import CustomBot
from custom.cog import CustomCog
from modules.google_search import search
from utils import get_cog


class SearchCog(CustomCog, name=get_cog('SearchCog')['name']):
    def __init__(self, bot: CustomBot):
        super().__init__(bot)
        self.bot = bot

    @commands.command(name='구글')
    async def google(self, ctx: Context, *, keyword: str):
        search()


def setup(bot: CustomBot):
    bot.add_cog(SearchCog(bot))
