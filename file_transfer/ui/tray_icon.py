"""
Tray icon image builder.

Small unit used by the tray app. Pure drawing code: it builds the little
picture shown in the system tray, so we do not need an external .ico/.png file.
"""

from PIL import Image, ImageDraw


class TrayIconBuilder:
    """
    Create tray icon image.

    This is only aesthetic/UI helper code.
    """

    @staticmethod
    def create() -> Image.Image:
        """
        Create a simple in-memory icon image.

        This avoids needing an external .ico/.png file for now.
        """
        image = Image.new("RGB", (64, 64), color=(26, 115, 232))
        draw = ImageDraw.Draw(image)

        # Simple bright upload-folder icon.
        # Big shapes work better because tray icons are very small.
        draw.rounded_rectangle((9, 20, 55, 49), radius=7, fill=(255, 213, 79))
        draw.rounded_rectangle((13, 14, 32, 25), radius=4, fill=(255, 238, 150))

        # White upload arrow.
        draw.polygon(
            (32, 25, 21, 37, 28, 37, 28, 45, 36, 45, 36, 37, 43, 37),
            fill=(255, 255, 255),
        )
        draw.polygon((32, 25, 24, 34, 40, 34), fill=(255, 255, 255))

        return image
