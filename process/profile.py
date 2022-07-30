import io
import os.path

import discord
from discord.ext import interaction
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

from config.config import get_config
from modules.model import Profile
from modules.minecraft import Client
from modules.skin_render import SkinRender
from utils.directory import directory

parser = get_config()
font_location = os.path.join(directory, "assets", "font", "Minecraftia-Regular.ttf")


class ProfileProcess:
    profile_player_name_font = ImageFont.truetype(font_location, size=36)
    profile_content_title = ImageFont.truetype(font_location, size=20)
    profile_recent_nickname = ImageFont.truetype(font_location, size=20)
    profile_uuid = ImageFont.truetype(font_location, size=18)

    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            author: discord.User,
            profile: List[Profile]
    ):
        self.ctx = ctx
        self.author = author
        self.client = client
        self.minecraft_client = Client(loop=self.client.loop)
        self._profile = profile
        self.message: Optional[interaction.Message] = None

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    def selection(self, index: int):
        print()
        return interaction.Selection(
            custom_id="{0}_{1}".format(self._profile[index].uuid, self.ctx.id),
            options=[
                interaction.Options(label=player.nickname, description=player.uuid, value=f"{_index}_{player.uuid}")
                for _index, player in enumerate(self._profile)
            ],
            min_values=1, max_values=1, disabled=len(self._profile) < 2
        )

    async def profile(self, index: int):
        pre_data = self._profile[index]
        data = await self.minecraft_client.profile_uuid(pre_data.uuid)

        embed = discord.Embed(color=self.color)
        embed.set_image(url="attachment://{0}_profile.png".format(pre_data.nickname))
        embed.set_author(
            name=f"{self.author.name}#{self.author.discriminator}",
            icon_url=self.author.display_avatar.url
        )

        canvas = Image.new('RGBA', (784, 512), (47, 49, 54))
        canvas_draw = ImageDraw.Draw(canvas)

        canvas_draw.text((32, 32), text=data.name, fill=(255, 255, 255), font=self.profile_player_name_font)

        skin_render_client = await SkinRender.from_url(
            url=data.skin.url,
            variant=data.skin.variant,
            loop=self.client.loop
        )
        canvas.alpha_composite(skin_render_client.portrait(), (48 + 480, 16))

        content_position_y = self.profile_player_name_font.size + 32 + 25
        content_count = 0
        if not pre_data.private_nickname_history:
            nickname_history = await self.minecraft_client.profile_history(pre_data.uuid)
            if len(nickname_history) > 1:
                content_count += 1
                canvas_draw.rounded_rectangle(
                    (
                        32, content_position_y + (self.profile_content_title.size / 2),
                        32 + 480,
                        content_position_y + (self.profile_content_title.size / 2)
                        + 30 + (10 + self.profile_recent_nickname.size) * len(nickname_history)
                    ),
                    radius=20,
                    fill=(54, 57, 63)
                )
                canvas_draw.text(
                    (64, content_position_y), text="Recent Nickname",
                    fill=(165, 175, 185), font=self.profile_content_title
                )
                nickname_history.reverse()
                content_position_y += (self.profile_content_title.size / 2) + 20

                max_nickname = 6
                if len(nickname_history) > 6:
                    max_nickname = 5
                for nickname in nickname_history[0:max_nickname]:
                    canvas_draw.text(
                        (52, content_position_y), text=nickname.name,
                        fill=(165, 175, 185), font=self.profile_recent_nickname
                    )
                    content_position_y += self.profile_recent_nickname.size + 10
                if len(nickname_history) > 6:
                    canvas_draw.text(
                        (52, content_position_y), text="...",
                        fill=(165, 175, 185), font=self.profile_recent_nickname
                    )
                    content_position_y += self.profile_recent_nickname.size + 10
                content_position_y += 16

        canvas_draw.rounded_rectangle(
            (
                32, content_position_y + (self.profile_content_title.size / 2),
                32 + 480, content_position_y + self.profile_uuid.size + self.profile_content_title.size + 25
            ),
            radius=20,
            fill=(54, 57, 63)
        )
        canvas_draw.text(
            (64, content_position_y), text="UUID",
            fill=(165, 175, 185), font=self.profile_content_title
        )
        uuid_text_x, _ = canvas_draw.textsize(text=pre_data.uuid, font=self.profile_uuid)
        canvas_draw.text(
            ((480 - uuid_text_x) / 2 + 32, content_position_y + (self.profile_content_title.size / 2) + 20),
            text=pre_data.uuid,
            fill=(165, 175, 185), font=self.profile_uuid
        )
        content_position_y += self.profile_uuid.size + 15 + self.profile_content_title.size + 16

        canvas_draw.rounded_rectangle(
            (
                32, content_position_y + (self.profile_content_title.size / 2),
                32 + 480, content_position_y + int((512 - 32 - 20 - content_position_y) / 75) * 75 + 20
            ),
            radius=20,
            fill=(54, 57, 63)
        )
        canvas_draw.text(
            (64, content_position_y), text="Connected Server",
            fill=(165, 175, 185), font=self.profile_content_title
        )

        buffer = io.BytesIO()
        canvas.save(buffer, format='png')
        buffer.seek(0)

        send_file = discord.File(buffer, filename="{0}_profile.png".format(pre_data.nickname))
        if self.message is None or not self.ctx.responded:
            self.message = await self.ctx.edit(embed=embed, file=send_file, components=[
                interaction.ActionRow(components=[self.selection(index)])
            ])
        else:
            await self.ctx.edit(embed=embed, file=send_file, components=[
                interaction.ActionRow(components=[self.selection(index)])
            ])
        if len(self._profile) > 1:
            component_response: interaction.ComponentsContext = await self.client.wait_for_component(
                custom_id="{0}_{1}".format(self._profile[index].uuid, self.ctx.id),
                check=lambda _component:
                    _component.author.id == self.ctx.author.id and
                    _component.message.id == self.message.id,
                timeout=300
            )
            await component_response.defer_update()
            index = component_response.values[0].split('_')[0]
            print(component_response.values)
            await self.profile(int(index))
        return
