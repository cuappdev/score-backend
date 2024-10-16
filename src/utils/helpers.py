import requests
from PIL import Image
from io import BytesIO
from collections import Counter

def get_dominant_color(image_url, threshold=200):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGB")

    image = image.resize((50, 50))
    pixels = image.getdata()

    non_white_pixels = [
        pixel for pixel in pixels 
        if not (pixel[0] > threshold and pixel[1] > threshold and pixel[2] > threshold)
    ]

    if non_white_pixels:
        pixel_count = Counter(non_white_pixels)
        dominant_color = pixel_count.most_common(1)[0][0]

    return dominant_color

dominant_color = get_dominant_color("https://cornellbigred.com/images/logos/harvardlogo.png?width=50")
print("Dominant color:", dominant_color)