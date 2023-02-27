import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class Error:
    def __init__(self, bot):
        self.bot = bot

    def _traceback_msg(self, tb):
        if tb.tb_next is None:
            return f"{tb.tb_frame.f_code.co_filename} {tb.tb_frame.f_code.co_name} {tb.tb_lineno}줄 "
        return f"{tb.tb_frame.f_code.co_filename} ({tb.tb_frame.f_code.co_name}) {tb.tb_lineno}줄\n{self._traceback_msg(tb.tb_next)}"

    @commands.Cog.listener()
    async def on_interaction_command_error(self, ctx, error):
        if error.__class__ == discord.ext.commands.errors.CommandNotFound:
            return
        elif error.__class__ == discord.ext.commands.CheckFailure:
            embed = discord.Embed(title="\U000026A0 에러", description="권한이 부족합니다.", color=0xaa0000)
            await ctx.send(embed=embed)
            return
        exc_name = type(error)
        exc_list = [str(x) for x in error.args]

        if not exc_list:
            exc_log = exc_name.__name__
        else:
            exc_log = "{exc_name}: {exc_list}".format(
                exc_name=exc_name.__name__,
                exc_list=", ".join(exc_list)
            )

        error_location = self._traceback_msg(error.__traceback__)

        if ctx.guild is not None:
            logger.error(
                f"({ctx.guild.name}, {ctx.channel.name}, {ctx.author}, {ctx.content}): {exc_log}\n{error_location}"
            )
        else:
            logger.error(f"({ctx.channel},{ctx.author},{ctx.content}): {exc_log}\n{error_location}")
        embed = discord.Embed(title="\U000026A0 에러", color=0x070ff)
        embed.add_field(name='에러 내용(traceback)', value=f'{exc_log}', inline=False)
        embed.add_field(name='에러 위치', value=f'{error_location}', inline=False)
        if ctx.guild is not None:
            embed.add_field(name='서버명', value=f'{ctx.guild.name}', inline=True)
            embed.add_field(name='채널명', value=f'{ctx.channel.name}', inline=True)
        embed.add_field(name='유저명', value=f'{ctx.author}', inline=True)
        embed.add_field(name='메세지', value=f'{ctx.content}', inline=False)
        await self.bot.get_guild(844613188900356157).get_channel(969647903738069012).send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ctx.content = ""
        if ctx.message is not None:
            ctx.content = ctx.message.content
        await self.on_interaction_command_error(ctx, error)


def setup(client):
    client.add_interaction_cog(Error(client))
