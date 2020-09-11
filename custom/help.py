import asyncio
from typing import List

from discord import Reaction, User
from discord.ext.commands import Context

import custom
from utils import literals, get_check, get_constant, get_cog, get_emoji
from .bot import CustomBot
from .cog import CustomCog
from .core import CustomGroup, CustomCommand
from .embed import ChainedEmbed

PREVIOUS_EMOJI = get_emoji(':arrow_left:')
NEXT_EMOJI = get_emoji(':arrow_right:')
DONE_EMOJI = get_emoji(':white_check_mark:')

COMMANDS_TIMEOUT = 60


def brief_cog(cog: CustomCog):
    brief = '-'
    if cog.description is not None:
        brief = cog.description
    elif cog.get_commands():
        brief = ''
    if not cog.get_commands():
        return brief
    commands = ''
    for command in cog.get_commands():
        if not command.enabled:
            continue
        commands += brief_command(command) + '\n'
    if commands:
        brief += '\n' + commands
    return brief


def brief_group(group: CustomGroup):
    brief = '* `' + group.qualified_name + '`'
    if group.brief is not None:
        brief += ': ' + group.brief
    for command in group.commands:
        if not command.enabled:
            continue
        if isinstance(command, CustomGroup):
            brief += '\n' + brief_group(command)
        else:
            brief += '\n' + brief_command(command)
    return brief


def brief_command(command: CustomCommand):
    if isinstance(command, CustomGroup):
        return brief_group(command)
    brief = '* `' + command.qualified_name + '`'
    if command.brief is not None:
        brief += ': ' + command.brief
    return brief


def get_command_signature(command: CustomCommand):
    parent = command.full_parent_name
    if len(command.aliases) > 0:
        aliases = '|'.join(command.aliases)
        fmt = '[%s|%s]' % (command.name, aliases)
        if parent:
            fmt = parent + ' ' + fmt
        alias = fmt
    else:
        alias = command.name if not parent else parent + ' ' + command.name
    return ('%s%s %s' % (get_constant('default_prefix'), alias, command.signature)).rstrip()


def get_command_info(command: CustomCommand):
    signature = '`' + get_command_signature(command) + '`\n'
    info = ''
    if command.brief is not None:
        info = command.brief
    if command.help is not None:
        info = '- ' + info + '\n- ' + command.help
    return signature + info


def check_correlation(command: CustomCommand, keywords: List[str], embed: ChainedEmbed):
    found = 0
    command_info = get_command_info(command)
    for keyword in keywords:
        if keyword in command_info:
            embed.add_field(name=command.qualified_name, value=command_info)
            found += 1
        break
    if isinstance(command, CustomGroup):
        for subcommand in command.commands:
            found += check_correlation(subcommand, keywords, embed)
    return found


class CustomHelpCog(CustomCog, name=get_cog('CustomHelpCog')['name']):
    """
    필요한 명령어를 찾거나 사용볍을 확인하기 위한 기능을 포함합니다.
    """
    def __init__(self, client: CustomBot):
        super().__init__(client)
        self.client: CustomBot = client

    @custom.core.command(name='검색', aliases=('찾기', 'search'))
    async def search(self, ctx: Context, keyword: str, *keywords: str):
        literal = literals('search')
        keywords = list(keywords)
        keywords.append(keyword)
        description = literal['found']
        embeds = ChainedEmbed(title=literal['title'], description=description)
        embeds.set_thumbnail(url=self.client.user.avatar_url)
        found = 0
        for command in self.client.commands:
            found += check_correlation(command, keywords, embeds)
        embeds.description = description % (found, ', '.join(keywords)) if found \
            else literal['not_found'] % ', '.join(keywords)
        for embed in embeds.to_list():
            await ctx.send(embed=embed)

    @custom.core.command(name='명령어', aliases=('commands', 'cmd', 'cmds'))
    async def commands(self, ctx: Context, *, category: str = ''):
        cog: CustomCog = self.client.get_cog(category)
        if cog is not None:
            await self.send_cog_info(ctx, cog)
        else:
            await self.send_cog_list(ctx)

    @custom.core.command(name='도움말', aliases=('help', 'h'))
    async def help(self, ctx: Context, *, command_name: str = ''):
        if not command_name:
            command_name = '도움말'
        command: CustomCommand = self.client.get_command(command_name)
        cog: CustomCog = self.client.get_cog(command_name)
        if command is not None:
            await self.send_command_help(ctx, command)
        elif cog is not None:
            await self.send_cog_info(ctx, cog)

    async def send_cog_info(self, ctx: Context, cog: CustomCog):
        cog_name = cog.qualified_name
        if isinstance(cog, CustomCog):
            cog_name = cog.emoji + ' ' + cog_name
        brief = brief_cog(cog)
        embeds = ChainedEmbed(title=cog_name, description=brief)
        embeds.set_thumbnail(url=self.client.user.avatar_url)
        for embed in embeds.to_list():
            await ctx.send(embed=embed)

    async def send_cog_list(self, ctx: Context):
        literal = literals('send_cog_list')
        embed = ChainedEmbed(title=literal['title'],
                             description=literal['description'])
        embed.set_thumbnail(url=self.client.user.avatar_url)
        pages = dict()
        page = 0
        for cog_name, cog in self.client.cogs.items():
            name = cog_name
            if cog.literal is not None:
                name = cog.literal['emoji'] + ' ' + name
            pages[get_cog(type(cog).__name__)['priority']] = (name, brief_cog(cog))
        embed.add_field(name=pages[page][0], value=pages[page][1])
        embed.set_footer(text=literal['footer'] % (page + 1, len(pages)))
        message = await ctx.send(embed=embed)
        emojis = (PREVIOUS_EMOJI, NEXT_EMOJI, DONE_EMOJI)
        await message.add_reaction(PREVIOUS_EMOJI)
        await message.add_reaction(DONE_EMOJI)
        await message.add_reaction(NEXT_EMOJI)

        print(pages)

        def is_reaction(reaction_: Reaction, user_: User):
            return reaction_.message.id == message.id and user_.id == ctx.author.id and reaction_.emoji in emojis

        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=is_reaction, timeout=COMMANDS_TIMEOUT)
                if reaction.emoji == DONE_EMOJI:
                    break
                else:
                    embed.clear_fields()
                    if reaction.emoji == PREVIOUS_EMOJI:
                        page = (page - 1) % len(pages)
                    elif reaction.emoji == NEXT_EMOJI:
                        page = (page + 1) % len(pages)
                    embed.add_field(name=pages[page][0], value=pages[page][1])
                    embed.set_footer(text=literal['footer'] % (page + 1, len(pages)))
                    await message.edit(embed=embed)
            except asyncio.TimeoutError:
                break
            finally:
                await asyncio.wait([message.remove_reaction(PREVIOUS_EMOJI, ctx.author),
                                    message.remove_reaction(NEXT_EMOJI, ctx.author)])
        await asyncio.wait([message.clear_reaction(PREVIOUS_EMOJI),
                            message.clear_reaction(NEXT_EMOJI)])

    async def send_command_help(self, ctx: Context, command: CustomCommand):
        command_name = command.qualified_name
        signature = get_command_signature(command)
        description = ''
        if command.help is not None:
            description = command.help + '\n'
        elif command.brief is not None:
            description = command.brief + '\n'
        description += f'`{signature}`'
        embeds = ChainedEmbed(title=get_constant('default_prefix') + command_name, description=description)
        embeds.set_thumbnail(url=self.client.user.avatar_url)
        if isinstance(command, CustomGroup):
            embeds.add_field(name=literals('send_command_help')['subcommand'],
                             value=f'\n{brief_group(command)}\n')
        for check in command.checks:
            data = get_check(check.name)
            if data is None:
                continue
            embeds.add_field(name=f'{data["emoji"]} {data["name"]}', value=data["description"])
        if command.cog is not None:
            text = command.cog.qualified_name
            if command.cog.literal is not None:
                text = command.cog.literal['emoji'] + ' ' + text
            embeds.set_footer(text=text)
        for embed in embeds.to_list():
            await ctx.send(embed=embed)
