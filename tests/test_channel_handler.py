import pytest
import OpenImageIO as oiio
import numpy as np

from mask_layer_tool.channel_handler import (
    detect_channels,
    extract_channel,
    modify_channel,
    append_channel,
    check_is_greyscale,
    create_greyscale_from_channel,
)


@pytest.fixture
def sample_image() -> oiio.ImageBuf:
    """Creates a synthetic image with R, G, B, A channels for testing."""
    width, height = 4, 4
    spec = oiio.ImageSpec(width, height, 4, oiio.FLOAT)  # RGBA format
    image = oiio.ImageBuf(spec)

    pixel_data = np.zeros((height, width, 4), dtype=np.float32)
    pixel_data[:, :, 0] = 1.0  # Set Red channel values to 1.0
    pixel_data[:, :, 1] = 0.5  # Set Green channel values to 0.5
    pixel_data[:, :, 2] = 0.25  # Set Blue channel values to 0.25
    pixel_data[:, :, 3] = 0.75  # Set Alpha channel values to 0.75

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 4)
    image.set_pixels(roi, pixel_data)

    return image


@pytest.fixture
def image_buf_fixture() -> oiio.ImageBuf:
    """Creates a synthetic OIIO ImageBuf with multiple channels for testing."""
    width, height = 4, 4
    spec = oiio.ImageSpec(width, height, 5, oiio.FLOAT)
    spec.channelnames = ["R", "G", "B", "A", "depth.Z"]

    image = oiio.ImageBuf(spec)

    pixel_data = np.zeros((height, width, 5), dtype=np.float32)
    pixel_data[:, :, 0] = 1.0  # Red channel
    pixel_data[:, :, 1] = 0.5  # Green channel
    pixel_data[:, :, 2] = 0.25  # Blue channel
    pixel_data[:, :, 3] = 0.75  # Alpha channel (unused)
    pixel_data[:, :, 4] = 0.8  # Depth.Z channel

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 5)
    image.set_pixels(roi, pixel_data)

    return image


def test_detect_used_channels(image_buf_fixture: oiio.ImageBuf) -> None:
    """Tests detecting used color channels in an OIIO ImageBuf."""
    channel_status = detect_channels(image_buf_fixture)

    assert channel_status["R"] is True
    assert channel_status["G"] is True
    assert channel_status["B"] is True
    assert channel_status["A"] is True
    assert channel_status["depth.Z"] is True


def test_extract_channel(image_buf_fixture: oiio.ImageBuf) -> None:
    """Tests whether extract_channel_oiio correctly extracts channels."""
    red_channel = extract_channel(image_buf_fixture, "R")
    assert red_channel.shape == (4, 4)
    assert np.allclose(red_channel, 1.0)  # Ensure Red channel has expected values

    alpha_channel = extract_channel(image_buf_fixture, "A")
    assert alpha_channel.shape == (4, 4)
    assert np.allclose(alpha_channel, 0.75)  # Ensure Alpha channel has expected values


def test_modify_channel(image_buf_fixture: oiio.ImageBuf) -> None:
    """Tests modifying a channel and verifying the update."""
    new_alpha_data = np.full((4, 4), 0.9, dtype=np.float32)  # Set new Alpha values
    modified_image = modify_channel(image_buf_fixture, new_alpha_data, "A")

    modified_alpha = extract_channel(modified_image, "A")
    assert modified_alpha.shape == (4, 4)
    assert np.allclose(modified_alpha, 0.9)  # Ensure Alpha channel is updated correctly


def test_invalid_channel(image_buf_fixture: oiio.ImageBuf) -> None:
    """Tests error handling for invalid channels."""
    with pytest.raises(ValueError):
        modify_channel(image_buf_fixture, np.zeros((4, 4)), "X")  # Invalid channel

    with pytest.raises(ValueError):
        modify_channel(image_buf_fixture, np.zeros((4, 4, 3)), "A")  # Incorrect shape


@pytest.fixture
def sample_image_buf() -> oiio.ImageBuf:
    """Creates a sample OIIO ImageBuf with RGB channels for testing."""
    width, height = 4, 4
    spec = oiio.ImageSpec(width, height, 3, oiio.FLOAT)
    spec.channelnames = ["R", "G", "B"]

    image = oiio.ImageBuf(spec)

    pixel_data = np.zeros((height, width, 3), dtype=np.float32)
    pixel_data[:, :, 0] = 1.0
    pixel_data[:, :, 1] = 0.5
    pixel_data[:, :, 2] = 0.25

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 3)
    image.set_pixels(roi, pixel_data)

    return image


def test_check_is_greyscale(
    sample_image: oiio.ImageBuf, sample_channel_data: oiio.ImageBuf
) -> None:
    """Tests whether an image is grayscale."""
    assert check_is_greyscale(sample_image) is False

    grayscale_data = np.full((4, 4, 3), 0.5, dtype=np.float32)
    grayscale_spec = oiio.ImageSpec(4, 4, 3, oiio.FLOAT)
    grayscale_image = oiio.ImageBuf(grayscale_spec)
    roi = oiio.ROI(0, 4, 0, 4, 0, 1, 0, 3)
    grayscale_image.set_pixels(roi, grayscale_data)

    assert check_is_greyscale(grayscale_image) is True


@pytest.fixture
def sample_channel_data() -> np.ndarray:
    """Creates sample grayscale channel data for testing."""
    width, height = 4, 4
    return np.full((height, width), 0.5, dtype=np.float32)


def test_create_greyscale_from_channel(sample_channel_data: oiio.ImageBuf) -> None:
    """Tests converting grayscale channel data to an RGB ImageBuf."""
    width, height = sample_channel_data.shape
    image_buf = create_greyscale_from_channel(sample_channel_data, width, height)

    assert image_buf.spec().width == width
    assert image_buf.spec().height == height
    assert image_buf.spec().nchannels == 3

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 3)
    pixel_data = np.array(image_buf.get_pixels(oiio.FLOAT, roi)).reshape(
        (height, width, 3)
    )

    # Check all RGB channels match the grayscale input
    assert np.allclose(pixel_data[:, :, 0], 0.5)
    assert np.allclose(pixel_data[:, :, 1], 0.5)
    assert np.allclose(pixel_data[:, :, 2], 0.5)


def test_append_channel(
    sample_image_buf: oiio.ImageBuf, sample_channel_data: oiio.ImageBuf
) -> None:
    """Tests appending a new channel to an existing ImageBuf."""
    updated_image_buf = append_channel(sample_image_buf, sample_channel_data, "Alpha")

    assert updated_image_buf.spec().width == sample_image_buf.spec().width
    assert updated_image_buf.spec().height == sample_image_buf.spec().height
    assert updated_image_buf.spec().nchannels == 4  # Check new channel is added
    assert list(updated_image_buf.spec().channelnames) == ["R", "G", "B", "Alpha"]

    roi = oiio.ROI(
        0,
        updated_image_buf.spec().width,
        0,
        updated_image_buf.spec().height,
        0,
        1,
        0,
        4,
    )
    pixel_data = np.array(updated_image_buf.get_pixels(oiio.FLOAT, roi)).reshape(
        (roi.yend, roi.xend, 4)
    )

    assert np.allclose(pixel_data[:, :, 3], 0.5)
