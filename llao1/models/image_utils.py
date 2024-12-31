# LLao1/llao1/models/image_utils.py
import base64
from io import BytesIO
from PIL import Image

def encode_image_base64(image_path):
    """
    Encode an image to a base64 string for multimodal calls.

    Args:
        image_path: The file path to the image.

    Returns:
        A base64 encoded string of the image.
    """
    try:
        pil_image = Image.open(image_path)
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        raise Exception(f"Error encoding image: {str(e)}") from e
