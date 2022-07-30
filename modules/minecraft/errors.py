class MinecraftException(Exception):
    pass


class TokenRequired(MinecraftException):
    def __init__(self):
        super(TokenRequired, self).__init__("Required Minecraft Authorization Token")
