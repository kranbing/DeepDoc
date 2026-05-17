import base64
from pathlib import Path
import os
from typing import List
from PIL import Image


def encode_image(image_path: str) -> str:
    """将图像文件编码为base64字符串。

    Args:
        image_path: 图像文件路径

    Returns:
        Base64编码的图像字符串

    Raises:
        ImageEncodingError: 如果图像编码失败
    """
    try:
        path = Path(image_path)
        if not path.exists():
            raise Exception(f"Image file not found: {image_path}")

        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"<|base64|>{encoded_string}"
    except Exception as e:
        raise Exception(f"Failed to encode image {image_path}: {str(e)}")


def crop_image_by_bbox_to_path(
    source_image_path: str,
    bbox: List[int],
    output_path: str,
) -> str:
    """
    根据bbox裁剪图片到指定路径

    Args:
        source_image_path: 源图片路径
        bbox: 边界框 [x1, y1, x2, y2]
        output_path: 输出文件完整路径

    Returns:
        裁剪后的图片路径（与输入output_path相同）
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 打开源图片
    with Image.open(source_image_path) as img:
        # bbox格式: [x1, y1, x2, y2]
        # PIL的crop使用: (left, upper, right, lower)
        x1, y1, x2, y2 = bbox

        # 裁剪图片
        cropped_img = img.crop((x1, y1, x2, y2))

        # 保存裁剪后的图片
        cropped_img.save(output_path)

        return output_path

def vlm_bbox_convert(layout_box: List, page_width: int, page_height: int):
    normalized_box = [
        round(int(layout_box[0] * page_width / 1000)),  # x1
        round(int(layout_box[1] * page_height / 1000)),  # y1
        round(int(layout_box[2] * page_width / 1000)),  # x2
        round(int(layout_box[3] * page_height / 1000)),  # y2
    ]
    return normalized_box