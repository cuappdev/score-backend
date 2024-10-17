import requests
from PIL import Image
from io import BytesIO
from collections import Counter

BASE_URL = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/cornellbigred.com"

def get_dominant_color(relative_path, white_threshold=200, black_threshold=50):
    image_url = f"{BASE_URL}{relative_path}"
    
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGBA")
    
    image = image.resize((50, 50))
    image = image.quantize(colors=5).convert("RGBA")
    pixels = image.getdata()

    filtered_pixels = [
        pixel for pixel in pixels 
        if not (pixel[0] > white_threshold and pixel[1] > white_threshold and pixel[2] > white_threshold) and
           not (pixel[0] < black_threshold and pixel[1] < black_threshold and pixel[2] < black_threshold)
    ]

    if filtered_pixels:
        pixel_count = Counter(filtered_pixels)
        dominant_color = pixel_count.most_common(1)[0][0]
    else:
        dominant_color = (0, 0, 0)

    return dominant_color

dominant_color = get_dominant_color('/images/logos/Princeton_Tigers.png?width=80&height=80&mode=max')
print(f"Dominant color: {dominant_color}")