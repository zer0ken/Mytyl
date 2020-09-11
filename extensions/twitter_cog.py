import asyncio
from tempfile import NamedTemporaryFile

import tweepy
from decouple import config
from discord import Profile, Reaction, User, Attachment
from discord.ext.commands import Bot

from custom.cog import CustomCog
from utils import get_cog, get_emoji

TWEET_MAX_LENGTH = 140


def get_status_url(id_: str):
    return 'https://twitter.com/mytyl_thrainn/status/' + id_


def get_attachment_path(name):
    return f'./mytyl/data/{name}.temp'


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

    @CustomCog.listener(name='on_reaction_add')
    async def tweet_from_message(self, reaction: Reaction, uploader: User):
        if reaction.emoji != get_emoji(':blue_heart:'):
            return
        media_ids = list()
        if reaction.message.attachments:
            async def save(attachment: Attachment):
                file_ = NamedTemporaryFile('wb')
                await attachment.save(file_.name)
                response: tweepy.models.Media = self.twitter.media_upload(media=file_)
                media_ids.append(response.id)

            await asyncio.wait([save(attachment) for attachment in reaction.message.attachments])
        author_name = await get_twitter_mention(reaction.message.author)
        if author_name is None:
            author_name = reaction.message.author.name
        uploader_name = await get_twitter_mention(uploader)
        if uploader_name is None:
            uploader_name = uploader.name
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
        self.twitter.update_status(status=f'{uploader_name}님의 제보\n@//shtelo', in_reply_to_status_id=prev_status)
        await reaction.message.channel.send(get_status_url(first_status.id_str))


def setup(bot: Bot):
    bot.add_cog(TwitterCog(bot))
