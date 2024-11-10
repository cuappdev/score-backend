import requests
from PIL import Image
from io import BytesIO
from collections import Counter


def get_dominant_color(image_url, white_threshold=200, black_threshold=50):
    """
    Get the hex code of the dominant color of an image.

    Args:
        image_url (str): The URL of the image.
        white_threshold (int): The threshold for white pixels. (optional)
        black_threshold (int): The threshold for black pixels. (optional)

    Returns:
        color: The hex code of the dominant color.
    """
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGBA")

    image = image.resize((50, 50))
    image = image.quantize(colors=5).convert("RGBA")
    pixels = image.getdata()

    filtered_pixels = [
        pixel
        for pixel in pixels
        if not (
            pixel[0] > white_threshold
            and pixel[1] > white_threshold
            and pixel[2] > white_threshold
        )
        and not (
            pixel[0] < black_threshold
            and pixel[1] < black_threshold
            and pixel[2] < black_threshold
        )
    ]

    if filtered_pixels:
        pixel_count = Counter(filtered_pixels)
        dominant_color = pixel_count.most_common(1)[0][0]
    else:
        dominant_color = (0, 0, 0)

    hex_color = "#{:02x}{:02x}{:02x}".format(
        dominant_color[0], dominant_color[1], dominant_color[2]
    )
    return hex_color
