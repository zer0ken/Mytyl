from asyncio import get_event_loop
from os import listdir

from decouple import config
from discord import Status
from discord.ext.commands import ExtensionAlreadyLoaded, ExtensionFailed, NoEntryPointError, ExtensionError
from discord.ext.commands.bot import Bot

from utils import get_path, get_constant, singleton


@singleton
class CustomBot(Bot):
    def __init__(self, args: list):
        super().__init__(get_constant('prefixes'), status=Status.online)
        self.help_command = None
        self.load_all_extensions()
        if 'b' in args:
            get_event_loop().run_until_complete(self.start(config('DISCORD_BOT_TOKEN'), bot=True))
        else:
            get_event_loop().run_until_complete(self.start(config('DISCORD_USER_TOKEN'), bot=False, ))

    def load_all_extensions(self):
        for file_name in listdir(get_path('extensions')):
            if not file_name.endswith('_cog.py') and not file_name.endswith('_cmd.py'):
                continue
            module = file_name[:-3]
            try:
                self.load_extension(get_constant('extension_name') % module)
            except ExtensionAlreadyLoaded as e:
                self.reload_extension(e.name)
            except (ExtensionFailed, NoEntryPointError, ExtensionFailed) as e:
                raise e

    def reload_extension(self, name):
        old = super().get_cog(name)
        try:
            super().reload_extension(name)
        except ExtensionError as e:
            super().add_cog(old)
            return False
        return True

    def reload_all_extensions(self):
        done = True
        for extension in self.extensions.keys():
            done = done and self.reload_extension(extension)
        return done
