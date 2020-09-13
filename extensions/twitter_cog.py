import asyncio
from tempfile import NamedTemporaryFile

import tweepy
from decouple import config
from discord import Profile, Reaction, User, Attachment, Message, Status
from discord.ext.commands import Bot

from custom.cog import CustomCog
from utils import get_cog, get_emoji

CACHE_SIZE = 100
TWEET_MAX_LENGTH = 140
TWEET_TIMEOUT = 60
TWEET_DELAY = 5

UPLOAD_EMOJI = get_emoji(':blue_heart:')
CONFIRM_EMOJI = get_emoji(':o:')
CANCEL_EMOJI = get_emoji(':x:')


def get_status_url(id_: str):
    return 'https://twitter.com/mytyl_thrainn/status/' + id_


def chunkstring(string, length):
    return [string[i:i + length] for i in range(0, len(string), length)]


async def get_twitter_mention(user: User):
    profile: Profile = await user.profile()
    for account in profile.connected_accounts:
        if account['type'] == 'twitter':
            return '@' + account['name']


class TwitterCog(CustomCog, name=get_cog('TwitterCog')['name']):
    """
    트위터와 연동하여 동작하는 기능들을 포함합니다.
    """
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot
        auth = tweepy.OAuthHandler(config('TWITTER_API_KEY'), config('TWITTER_API_KEY_SECRET'))
        auth.set_access_token(config('TWITTER_ACCESS_TOKEN'), config('TWITTER_ACCESS_TOKEN_SECRET'))
        self.twitter = tweepy.API(auth)
        self.cached_message = list()

    def cache(self, message_id: int):
        self.cached_message.append(message_id)
        if len(self.cached_message) > CACHE_SIZE:
            self.cached_message = self.cached_message[1:]

    @CustomCog.listener(name='on_reaction_add')
    async def tweet_from_message(self, reaction: Reaction, uploader: User):
        if self.bot.guilds[0].get_member(self.bot.user.id).status != Status.online:
            return
        if reaction.emoji != UPLOAD_EMOJI:
            return
        if reaction.message.id in self.cached_message:
            return

        confirm_message: Message = await reaction.message.channel.send('이 메시지를 트위터에 올릴까요?')
        await confirm_message.add_reaction(CONFIRM_EMOJI)
        await confirm_message.add_reaction(CANCEL_EMOJI)

        def is_reaction(reaction_: Reaction, user_: User):
            return uploader == user_ and reaction_.emoji in (CONFIRM_EMOJI, CANCEL_EMOJI)

        try:
            confirm_reaction, _ = await self.bot.wait_for('reaction_add', check=is_reaction, timeout=TWEET_TIMEOUT)
        except asyncio.TimeoutError:
            return
        else:
            if confirm_reaction.emoji == CANCEL_EMOJI:
                self.cache(reaction.message.id)
                return
        finally:
            await confirm_message.delete()
        media_ids = list()
        for attachment in reaction.message.attachments:
            file_ = NamedTemporaryFile('wb')
            await attachment.save(file_.name)
            media_: tweepy.models.Media = self.twitter.media_upload(file_.name)
            media_ids.append(media_.media_id)
            file_.close()
        author_name = await get_twitter_mention(reaction.message.author)
        if author_name is None:
            author_name = reaction.message.author.name
        first_status = None
        prev_status = None
        for status in chunkstring(f'{author_name}: {reaction.message.content}', TWEET_MAX_LENGTH):
            media = None
            if media_ids:
                media = media_ids[:4]
                media_ids = media_ids[4:]
            prev_status = self.twitter.update_status(status=status, media_ids=media,
                                                     in_reply_to_status_id=prev_status)
            if first_status is None:
                first_status = prev_status
            prev_status = prev_status.id
            await asyncio.sleep(TWEET_DELAY)
        mentions = f'{uploader.name}님의 제보\n@shtelo'
        uploader_mention = await get_twitter_mention(uploader)
        if uploader_mention is not None:
            mentions = uploader_mention + ' ' + mentions
        self.twitter.update_status(status=mentions, in_reply_to_status_id=prev_status)
        await reaction.message.channel.send(get_status_url(first_status.id_str))
        self.cache(reaction.message.id)


def setup(bot: Bot):
    bot.add_cog(TwitterCog(bot))
