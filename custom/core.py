from typing import Iterable

import discord
from discord import Status, Guild, Member
from discord.ext.commands import GroupMixin, BucketType, Command, Group, Context, check

from utils import get_brief, get_help, get_constant
from .cooldowns import SharedCooldown, SharedCooldownMapping


class CustomGroupMixin(GroupMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def command(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


class CustomCommand(Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        name = self.full_parent_name + ' ' + self.name if self.full_parent_name else self.name
        self.brief = get_brief(name)
        self.help = get_help(name)


class CustomGroup(CustomGroupMixin, CustomCommand, Group):
    pass


def command(name=None, cls=None, **attrs):
    if cls is None:
        cls = CustomCommand

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


def group(name=None, **attrs):
    attrs.setdefault('cls', CustomGroup)
    attrs.setdefault('invoke_without_command', True)
    return command(name=name, **attrs)


def shared_cooldown(rate, per, type=BucketType.default):
    cooldown = SharedCooldown(rate, per, type)
    cooldown_mapping = SharedCooldownMapping(cooldown)

    def decorator(func):
        if isinstance(func, Command):
            func._buckets = cooldown_mapping
        else:
            func.__commands_cooldown__ = cooldown
        return func

    return decorator


def owner_only():
    def predicate(ctx: Context) -> bool:
        return ctx.author.id == ctx.bot.owner_id

    predicate.name = 'owner_only'
    return check(predicate)


def guild_only():
    def predicate(ctx: Context) -> bool:
        return ctx.guild is not None

    predicate.name = 'guild_only'
    return check(predicate)


def member_only(guild_id):
    async def predicate(ctx: Context):
        guild = await ctx.bot.fetch_guild(guild_id)
        return guild.fetch_member(ctx.author.id) is not None

    predicate.name = 'member_only'
    return check(member_only)


def dm_only():
    def predicate(ctx: Context) -> bool:
        return ctx.guild is None

    predicate.name = 'dm_only'
    return check(predicate)


def for_guilds(guild_id: tuple or int):
    if type(guild_id) != tuple:
        guild_id = (guild_id,)

    def predicate(ctx: Context) -> bool:
        if ctx.message.guild is not None:
            return ctx.message.guild.id in guild_id
        return False

    predicate.name = 'for_guilds'
    return check(predicate)


def for_channels(channel_id: tuple or int):
    if type(channel_id) != tuple:
        channel_id = (channel_id,)

    def predicate(ctx: Context) -> bool:
        return ctx.message.channel.id in channel_id

    predicate.name = 'for_channels'
    return check(predicate)


def avoid_guilds(guild_id: tuple or int):
    if type(guild_id) != tuple:
        guild_id = (guild_id,)

    def predicate(ctx: Context) -> bool:
        if ctx.message.guild:
            return ctx.message.guild.id not in guild_id
        return True

    predicate.name = 'avoid_guilds'
    return check(predicate)


def avoid_channels(channel_id: tuple or int):
    if type(channel_id) != tuple:
        channel_id = (channel_id,)

    def predicate(ctx: Context) -> bool:
        return ctx.message.channel.id not in channel_id

    predicate.name = 'avoid_channels'
    return check(predicate)


def bot_need_permissions(**permissions):
    def predicate(ctx: Context) -> bool:
        client_permissions: dict = dict(ctx.guild.get_member(get_constant('kenken_id')).guild_permissions)
        for perm, value in permissions.items():
            if client_permissions[perm] != value:
                return False
        return True

    predicate.name = 'bot_need_permissions'
    return check(predicate)


def has_role(guild_id: int, role_id: int):
    async def predicate(ctx: Context):
        guild = await ctx.bot.fetch_guild(guild_id)
        member = None
        if guild is not None:
            member = await guild.fetch_member(ctx.author.id)
        if member is None:
            return False
        role = discord.utils.get(member.roles, id=role_id)
        if role is None:
            return False
        return True

    predicate.name = 'has_role'
    return check(predicate)


def tokens_len(count: tuple or int):
    if type(count) != tuple:
        count = (count,)

    def predicate(ctx: Context) -> bool:
        return len(ctx.message.content.split()) in count

    predicate.name = 'tokens_len'
    return check(predicate)


def tokens_len_range(minimum: int = 0, maximum: int = 0):
    def predicate(ctx: Context) -> bool:
        len_ = len(ctx.message.content.split())
        return (not minimum or len_ >= minimum) and (not maximum or len_ <= maximum)

    predicate.name = 'tokens_len_range'
    return check(predicate)


def on_status(status: Status or Iterable[Status]):
    if not isinstance(status, Iterable):
        status = (status,)

    async def predicate(ctx: Context) -> bool:
        guild: Guild = ctx.bot.guilds[0]
        bot_member: Member = await guild.fetch_member(ctx.bot.user.id)
        print(bot_member.status)
        return bot_member.status in status

    predicate.name = 'status'
    return check(predicate)
