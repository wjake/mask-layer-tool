import os
import pytest
import OpenImageIO as oiio
import numpy as np

from mask_layer_tool.image_loader import (
    load_image,
    save_image,
)


@pytest.fixture
def sample_image() -> oiio.ImageBuf:
    """Creates a synthetic OIIO ImageBuf for testing."""
    width, height = 4, 4
    spec = oiio.ImageSpec(width, height, 4, oiio.FLOAT)  # RGBA format
    image = oiio.ImageBuf(spec)

    pixel_data = np.zeros((height, width, 4), dtype=np.float32)
    pixel_data[:, :, 0] = 1.0  # Red channel
    pixel_data[:, :, 1] = 0.5  # Green channel
    pixel_data[:, :, 2] = 0.25  # Blue channel
    pixel_data[:, :, 3] = 0.75  # Alpha channel

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 4)
    image.set_pixels(roi, pixel_data)

    return image


@pytest.fixture
def sample_image_file(tmpdir: str, sample_image: oiio.ImageBuf) -> str:
    """Creates and saves a synthetic image for testing."""
    temp_file = os.path.join(tmpdir, "test_image.exr")
    sample_image.write(temp_file)

    return temp_file


def test_load_image(sample_image_file: str) -> None:
    """Tests loading an image."""
    image = load_image(sample_image_file)
    assert isinstance(image, oiio.ImageBuf)
    assert image.initialized


def test_save_image(sample_image: oiio.ImageBuf, tmpdir: str) -> None:
    """Tests saving an image."""
    output_path = tmpdir.mkdir("test_output")
    save_image(sample_image, str(output_path), "test.exr")
    saved_image = load_image(str(output_path) + "/test.exr")
    assert saved_image.initialized
