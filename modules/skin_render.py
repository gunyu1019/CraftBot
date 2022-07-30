import asyncio
import aiohttp
import io
from enum import Enum
from PIL import Image

from .minecraft.client import Client
from .request import Requests


class Direction:
    front = 1
    back = 2


class SkinRender:
    PIXEL1: int = 4  # Leg Width, Arm Width
    PIXEL2: int = 8  # Head, Body Width
    PIXEL3: int = 12  # Lef Height, Arm Height, Body Height
    PIXEL4: int = 16  # Section

    def __init__(
            self,
            resource: Image.Image,
            scale: int = 15,
            variant: str = "CLASSIC",
            minimal: bool = None
    ):
        self.resource = resource
        self.variant = variant
        self.minimal = minimal
        self.scale = scale

        self.arm_size = self.PIXEL1
        if self.variant == "SLIM":
            self.arm_size = 3

        self.resource_size_x, self.resource_size_y = self.resource.size
        if self.minimal is None:
            self.minimal = self.resource_size_y <= 32

    @classmethod
    async def from_uuid(
            cls,
            uuid: str,
            scale: int = 15,
            loop: asyncio.AbstractEventLoop = None,
            session: aiohttp.ClientSession = None
    ):
        client = Client(loop=loop, session=session)
        data = await client.profile_uuid(uuid)
        return await cls.from_url(data.skin.url, data.skin.variant, scale=scale)

    @classmethod
    async def from_url(
            cls,
            url: str,
            variant: str = "CLASSIC",
            scale: int = 15,
            loop: asyncio.AbstractEventLoop = None,
            session: aiohttp.ClientSession = None
    ):
        request = Requests(loop=loop, session=session)
        resource_byte = await request.get(url=url, raise_on=False)
        resource = Image.open(io.BytesIO(resource_byte.data))
        return cls(resource=resource, variant=variant, scale=scale)

    def cropped_and_resize_image(
            self,
            position_x_start: int, position_y_start: int,
            position_x_end: int, position_y_end: int,
            resized_width: int, resized_height: int
    ) -> Image.Image:
        cropped_head_data = self.resource.crop((position_x_start, position_y_start, position_x_end, position_y_end))
        resized_head_data = cropped_head_data.resize((resized_width, resized_height), Image.Resampling.BOX)
        return resized_head_data

    def head_image(self, direction: Direction = Direction.front):
        expend_canvas = Image.new(
            "RGBA",
            (int(self.scale * (self.PIXEL2 + 0.4)), int(self.scale * (self.PIXEL2 + 0.4)))
        )

        if direction == Direction.back:
            head_pos_x_start, head_pos_x_end = 24, 32
            hat_pos_x_start, hat_pos_x_end = 56, 64
        else:
            head_pos_x_start, head_pos_x_end = 8, 16
            hat_pos_x_start, hat_pos_x_end = 40, 48

        head = self.cropped_and_resize_image(
            head_pos_x_start, 8, head_pos_x_end, 16,
            self.scale * self.PIXEL2, self.scale * self.PIXEL2
        )
        hat = self.cropped_and_resize_image(
            hat_pos_x_start, 8, hat_pos_x_end, 16,
            int(self.scale * (self.PIXEL2 + 0.4)), int(self.scale * (self.PIXEL2 + 0.4))
        )
        expend_canvas.paste(head, (int(self.scale * 0.2), int(self.scale * 0.2)))
        expend_canvas.alpha_composite(hat, (0, 0))
        return expend_canvas

    def body_image(self, direction: Direction = Direction.front, minimal: bool = None):
        if minimal is None:
            minimal = self.minimal

        if direction == Direction.back:
            body_pos_x_start, body_pos_x_end = 32, 40
        else:
            body_pos_x_start, body_pos_x_end = 20, 28

        body = self.cropped_and_resize_image(
            body_pos_x_start, 20, body_pos_x_end, 32,
            self.scale * self.PIXEL2, self.scale * self.PIXEL3
        )
        if not minimal:

            expend_canvas = Image.new(
                "RGBA",
                (int(self.scale * (self.PIXEL2 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4)))
            )
            jacket = self.cropped_and_resize_image(
                body_pos_x_start, 36, body_pos_x_start, 48,
                int(self.scale * (self.PIXEL2 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4))
            )
            expend_canvas.paste(body, (int(self.scale * 0.2), int(self.scale * 0.2)))
            expend_canvas.alpha_composite(jacket, (0, 0))
            return expend_canvas
        return body

    def right_arm_image(self, direction: Direction = Direction.front, minimal: bool = None):
        if minimal is None:
            minimal = self.minimal

        if direction == Direction.back:
            right_arm_pos_x_start, right_arm_pos_x_end = 48 + self.arm_size, 48 + self.arm_size * 2
        else:
            right_arm_pos_x_start, right_arm_pos_x_end = 44, 44 + self.arm_size

        right_arm = self.cropped_and_resize_image(
            right_arm_pos_x_start, 20, right_arm_pos_x_end, 32, self.scale * self.arm_size, self.scale * self.PIXEL3
        )
        if not minimal:
            expend_canvas = Image.new(
                "RGBA", (int(self.scale * (self.arm_size + 0.4)), int(self.scale * (self.PIXEL3 + 0.4)))
            )
            expend_canvas.paste(right_arm, (int(self.scale * 0.2), int(self.scale * 0.2)))
            right_arm2 = self.cropped_and_resize_image(
                right_arm_pos_x_start, 36, right_arm_pos_x_end, 48,
                int(self.scale * (self.arm_size + 0.4)), int(self.scale * (self.PIXEL3 + 0.4))
            )
            expend_canvas.alpha_composite(right_arm2, (0, 0))
            return expend_canvas
        return right_arm

    def left_arm_image(self, direction: Direction = Direction.front, minimal: bool = None):
        if minimal is None:
            minimal = self.minimal

        if not minimal:
            if direction == Direction.back:
                left_arm1_pos_x_start, left_arm1_pos_x_end = 40 + self.arm_size, 40 + self.arm_size * 2
                left_arm2_pos_x_start, left_arm2_pos_x_end = 56 + self.arm_size, 56 + self.arm_size * 2
            else:
                left_arm1_pos_x_start, left_arm1_pos_x_end = 36, 36 + self.arm_size
                left_arm2_pos_x_start, left_arm2_pos_x_end = 52, 52 + self.arm_size

            expend_canvas = Image.new(
                "RGBA", (int(self.scale * (self.arm_size + 0.4)), int(self.scale * (self.PIXEL3 + 0.4)))
            )
            left_arm = self.cropped_and_resize_image(
                left_arm1_pos_x_start, 52, left_arm1_pos_x_end, 64, self.scale * self.arm_size, self.scale * self.PIXEL3
            )
            left_arm2 = self.cropped_and_resize_image(
                left_arm2_pos_x_start, 52, left_arm2_pos_x_end, 64,
                int(self.scale * (self.arm_size + 0.4)), int(self.scale * (self.PIXEL3 + 0.4))
            )
            expend_canvas.paste(left_arm, (int(self.scale * 0.2), int(self.scale * 0.2)))
            expend_canvas.alpha_composite(left_arm2, (0, 0))
            return expend_canvas
        else:
            left_arm = self.right_arm_image(direction=direction, minimal=minimal)
        return left_arm

    def right_leg_image(self, direction: Direction = Direction.front, minimal: bool = None):
        if minimal is None:
            minimal = self.minimal

        if direction == Direction.back:
            right_leg_pos_x_start, right_leg_pos_x_end = 12, 16
        else:
            right_leg_pos_x_start, right_leg_pos_x_end = 4, 8

        right_leg = self.cropped_and_resize_image(
            right_leg_pos_x_start, 20, right_leg_pos_x_end, 32,
            self.scale * self.PIXEL1, self.scale * self.PIXEL3
        )
        if not minimal:
            expend_canvas = Image.new(
                "RGBA", (int(self.scale * (self.PIXEL1 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4)))
            )
            expend_canvas.paste(right_leg, (int(self.scale * 0.2), int(self.scale * 0.2)))
            right_leg2 = self.cropped_and_resize_image(
                right_leg_pos_x_start, 36, right_leg_pos_x_end, 48,
                int(self.scale * (self.PIXEL1 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4))
            )
            expend_canvas.alpha_composite(right_leg2, (0, 0))
            return expend_canvas
        return right_leg

    def left_leg_image(self, direction: Direction = Direction.front, minimal: bool = None):
        if minimal is None:
            minimal = self.minimal

        if not minimal:
            if direction == Direction.back:
                left_leg1_pos_x_start, left_leg1_pos_x_end = 28, 32
                left_leg2_pos_x_start, left_leg2_pos_x_end = 12, 16
            else:
                left_leg1_pos_x_start, left_leg1_pos_x_end = 20, 24
                left_leg2_pos_x_start, left_leg2_pos_x_end = 4, 8

            expend_canvas = Image.new(
                "RGBA", (int(self.scale * (self.PIXEL1 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4)))
            )
            left_leg = self.cropped_and_resize_image(
                left_leg1_pos_x_start, 52, left_leg1_pos_x_end, 64,
                self.scale * self.PIXEL1, self.scale * self.PIXEL3
            )

            left_leg2 = self.cropped_and_resize_image(
                left_leg2_pos_x_start, 52, left_leg2_pos_x_end, 64,
                int(self.scale * (self.PIXEL1 + 0.4)), int(self.scale * (self.PIXEL3 + 0.4))
            )
            expend_canvas.paste(left_leg, (int(self.scale * 0.2), int(self.scale * 0.2)))
            expend_canvas.alpha_composite(left_leg2, (0, 0))
            return expend_canvas
        else:
            left_leg = self.right_leg_image(direction=direction, minimal=minimal)
        return left_leg

    def portrait(self, direction: Direction = Direction.front):
        original_canvas_size = canvas_size = (int(self.scale * self.PIXEL4), int(self.scale * self.PIXEL4 * 2))
        if self.minimal:
            canvas_size = (int(self.scale * (self.PIXEL4 + 0.4)), int(self.scale * (self.PIXEL4 * 2 + 0.4)))
        portrait_canvas = Image.new(
            "RGBA", canvas_size
        )
        if not self.minimal:
            if self.variant == "CLASSIC":
                portrait_canvas.alpha_composite(
                    self.left_arm_image(direction=direction),
                    (int(0.2 * self.scale), int((self.PIXEL2 + 0.2) * self.scale))
                )
            else:
                portrait_canvas.alpha_composite(
                    self.left_arm_image(direction=direction),
                    (int(1.2 * self.scale), int((self.PIXEL2 + 0.2) * self.scale))
                )
            portrait_canvas.alpha_composite(
                self.right_arm_image(direction=direction),
                (int((self.PIXEL3 + 0.2) * self.scale), int((self.PIXEL2 + 0.2) * self.scale))
            )
            portrait_canvas.alpha_composite(
                self.left_leg_image(direction=direction),
                (int((self.PIXEL1 + 0.2) * self.scale), int(20.2 * self.scale))
            )
            portrait_canvas.alpha_composite(
                self.right_leg_image(direction=direction),
                (int((self.PIXEL2 + 0.2) * self.scale), int(20.2 * self.scale))
            )

            portrait_canvas.alpha_composite(
                self.body_image(direction=direction),
                (int((self.PIXEL1 + 0.2) * self.scale), int(8.2 * self.scale))
            )
            portrait_canvas.alpha_composite(
                self.head_image(direction=direction),
                (int((self.PIXEL1 + 0.2) * self.scale), int(0.2 * self.scale))
            )
            portrait_canvas = portrait_canvas.resize(original_canvas_size, resample=Image.Resampling.BOX)
        else:
            if self.variant == "CLASSIC":
                portrait_canvas.alpha_composite(
                    self.left_arm_image(direction=direction), (0, self.PIXEL2 * self.scale)
                )
            else:
                portrait_canvas.alpha_composite(
                    self.left_arm_image(direction=direction), (1, self.PIXEL2 * self.scale)
                )
            portrait_canvas.alpha_composite(
                self.right_arm_image(direction=direction), (0, self.PIXEL3)
            )
            portrait_canvas.alpha_composite(
                self.left_leg_image(direction=direction), (self.PIXEL1 * self.scale, 20 * self.scale)
            )
            portrait_canvas.alpha_composite(
                self.right_leg_image(direction=direction), (self.PIXEL2 * self.scale, 20 * self.scale)
            )

            portrait_canvas.alpha_composite(
                self.body_image(direction=direction), (self.PIXEL1 * self.scale, self.PIXEL2 * self.scale)
            )
            portrait_canvas.alpha_composite(
                self.head_image(direction=direction), (self.PIXEL1 * self.scale, 0)
            )
        return portrait_canvas
