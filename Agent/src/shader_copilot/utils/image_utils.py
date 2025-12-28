"""
Image encoding/decoding utilities for handling reference images.
"""

import base64
import io
import mimetypes
from pathlib import Path
from typing import Optional, Tuple


def encode_image_to_base64(image_path: str | Path) -> Tuple[str, str]:
    """
    Encode an image file to base64.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_string, mime_type)

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If file type is not supported
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None or not mime_type.startswith("image/"):
        raise ValueError(f"Unsupported file type: {path.suffix}")

    # Read and encode
    with open(path, "rb") as f:
        data = f.read()

    base64_str = base64.b64encode(data).decode("utf-8")
    return base64_str, mime_type


def decode_base64_to_bytes(base64_str: str) -> bytes:
    """
    Decode a base64 string to bytes.

    Args:
        base64_str: Base64 encoded string (with or without data URL prefix)

    Returns:
        Decoded bytes
    """
    # Remove data URL prefix if present
    if base64_str.startswith("data:"):
        # Format: data:image/png;base64,xxxxx
        _, data = base64_str.split(",", 1)
        return base64.b64decode(data)

    return base64.b64decode(base64_str)


def extract_mime_type(base64_str: str, default: str = "image/png") -> str:
    """
    Extract MIME type from a data URL.

    Args:
        base64_str: Base64 string, possibly with data URL prefix
        default: Default MIME type if not found

    Returns:
        MIME type string
    """
    if base64_str.startswith("data:"):
        # Format: data:image/png;base64,xxxxx
        prefix = base64_str.split(",", 1)[0]
        if ";" in prefix:
            mime_part = prefix.split(";")[0]
            return mime_part.replace("data:", "")

    return default


def create_data_url(base64_str: str, mime_type: str = "image/png") -> str:
    """
    Create a data URL from base64 string.

    Args:
        base64_str: Base64 encoded image data
        mime_type: MIME type of the image

    Returns:
        Data URL string
    """
    # Remove existing data URL prefix if present
    if base64_str.startswith("data:"):
        return base64_str

    return f"data:{mime_type};base64,{base64_str}"


def validate_image_data(base64_str: str) -> bool:
    """
    Validate that a base64 string contains valid image data.

    Args:
        base64_str: Base64 encoded string

    Returns:
        True if valid, False otherwise
    """
    try:
        data = decode_base64_to_bytes(base64_str)

        # Check for common image file signatures
        if len(data) < 8:
            return False

        # PNG signature
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return True

        # JPEG signature (SOI marker)
        if data[:2] == b"\xff\xd8":
            return True

        # GIF signature
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return True

        # WebP signature
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return True

        return False

    except Exception:
        return False


def resize_image_if_needed(
    image_bytes: bytes,
    max_size: int = 1024,
    quality: int = 85,
) -> Tuple[bytes, bool]:
    """
    Resize an image if it exceeds the maximum dimension.

    Requires PIL/Pillow. Returns original bytes if PIL is not available.

    Args:
        image_bytes: Original image bytes
        max_size: Maximum width or height in pixels
        quality: JPEG quality for output

    Returns:
        Tuple of (image_bytes, was_resized)
    """
    try:
        from PIL import Image
    except ImportError:
        return image_bytes, False

    # Load image
    img = Image.open(io.BytesIO(image_bytes))

    # Check if resize is needed
    width, height = img.size
    if width <= max_size and height <= max_size:
        return image_bytes, False

    # Calculate new size maintaining aspect ratio
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    # Resize
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()

    # Preserve format if possible, otherwise use JPEG
    fmt = img.format or "JPEG"
    if fmt == "JPEG":
        img.save(output, format=fmt, quality=quality)
    else:
        img.save(output, format=fmt)

    return output.getvalue(), True


def get_image_dimensions(image_bytes: bytes) -> Optional[Tuple[int, int]]:
    """
    Get dimensions of an image from its bytes.

    Args:
        image_bytes: Image data as bytes

    Returns:
        Tuple of (width, height) or None if cannot determine
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        return img.size
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: try to parse PNG/JPEG headers manually
    try:
        # PNG
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            # Width and height are at bytes 16-23 in IHDR chunk
            width = int.from_bytes(image_bytes[16:20], "big")
            height = int.from_bytes(image_bytes[20:24], "big")
            return (width, height)

        # JPEG - more complex, skip for now
        return None

    except Exception:
        return None
