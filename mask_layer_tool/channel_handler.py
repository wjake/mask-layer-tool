import OpenImageIO as oiio
import numpy as np


def detect_channels(image: oiio.ImageBuf) -> dict:
    """
    Detects all available channels in an OpenImageIO ImageBuf and checks if they contain non-zero data.
    Parameters:
        image (oiio.ImageBuf): The image object to analyze.
    Returns:
        dict: A dictionary mapping channel names to a boolean indicating if they contain any non-zero data.
    """
    if not image.initialized:
        raise ValueError("Invalid or uninitialized image.")

    spec = image.spec()
    channels = spec.channelnames

    roi = oiio.ROI(0, spec.width, 0, spec.height, 0, 1, 0, len(channels))
    pixel_data = np.array(image.get_pixels(oiio.FLOAT, roi)).reshape(
        (spec.height, spec.width, len(channels))
    )

    used_channels = {
        channel: bool(np.any(pixel_data[:, :, i])) for i, channel in enumerate(channels)
    }

    return used_channels


def extract_channel(image: oiio.ImageBuf, channel: str = "R") -> np.ndarray:
    """
    Extracts the specified channel from an OpenImageIO ImageBuf and returns it as a NumPy array.
    Parameters:
        image (oiio.ImageBuf): The image object to extract the channel from.
        channel (str): The name of the channel to extract (default is "R").
    Returns:
        np.ndarray: A NumPy array containing the pixel data for the specified channel.
    """
    spec = image.spec()
    channels = spec.channelnames

    if channel not in channels:
        raise ValueError(f"Channel '{channel}' not found in image.")

    width, height = spec.width, spec.height
    num_channels = len(channels)

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, num_channels)
    pixel_data = image.get_pixels(oiio.FLOAT, roi)

    pixel_data = np.array(pixel_data, dtype=np.float32).reshape(
        (height, width, num_channels)
    )

    channel_index = channels.index(channel)
    return pixel_data[:, :, channel_index]


def modify_channel(
    image: oiio.ImageBuf, channel_data: np.ndarray, channel: str = "R"
) -> oiio.ImageBuf:
    """
    Modifies a specific channel in an OpenImageIO ImageBuf with new pixel data.
    Parameters:
        image (oiio.ImageBuf): The image object to modify.
        channel_data (np.ndarray): A NumPy array containing new pixel data for the specified channel.
        channel (str): The name of the channel to modify (default is "R").
    Returns:
        oiio.ImageBuf: A new ImageBuf with the modified channel.
    """
    spec = image.spec()
    channels = spec.channelnames
    width, height = spec.width, spec.height

    if channel not in channels:
        raise ValueError(f"Channel '{channel}' not found in image.")

    if channel_data.shape != (height, width):
        raise ValueError(
            "The size of the channel data does not match the image dimensions."
        )

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, len(channels))

    pixel_data = image.get_pixels(oiio.FLOAT, roi)
    pixel_data = np.array(pixel_data, dtype=np.float32).reshape(
        (height, width, len(channels))
    )

    channel_index = channels.index(channel)
    pixel_data[:, :, channel_index] = channel_data

    modified_image = oiio.ImageBuf(
        oiio.ImageSpec(width, height, len(channels), oiio.FLOAT)
    )
    modified_image.set_pixels(roi, pixel_data)

    return modified_image


def append_channel(
    image: oiio.ImageBuf, channel_data: np.ndarray, channel_name: str
) -> oiio.ImageBuf:
    """
    Appends a new channel to an existing OpenImageIO ImageBuf and returns the updated image.

    Parameters:
        image (oiio.ImageBuf): The original image buffer.
        channel_data (np.ndarray): A NumPy array containing pixel data for the new channel.
        channel_name (str): Name of the new channel to append.

    Returns:
        oiio.ImageBuf: A new ImageBuf with the additional channel.
    """
    if not image.initialized:
        raise ValueError("Input image is not initialized.")

    spec = image.spec()
    width, height, existing_channels = spec.width, spec.height, spec.nchannels

    if channel_data.shape != (height, width):
        raise ValueError(
            f"Channel data shape {channel_data.shape} does not match image dimensions ({width}x{height})."
        )

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, existing_channels)
    pixel_data = np.array(image.get_pixels(oiio.FLOAT, roi)).reshape(
        (height, width, existing_channels)
    )

    updated_pixel_data = np.concatenate(
        [pixel_data, channel_data[..., np.newaxis]], axis=-1
    )

    new_spec = oiio.ImageSpec(width, height, existing_channels + 1, oiio.FLOAT)
    new_spec.channelnames = list(spec.channelnames) + [channel_name]

    new_image = oiio.ImageBuf(new_spec)
    new_roi = oiio.ROI(0, width, 0, height, 0, 1, 0, existing_channels + 1)
    new_image.set_pixels(new_roi, updated_pixel_data)

    return new_image


def check_is_greyscale(image: oiio.ImageBuf) -> bool:
    """
    Checks if the image is grayscale by verifying if all RGB channels are equal.
    Parameters:
        image (oiio.ImageBuf): The image object to check.
    Returns:
        bool: True if the image is grayscale, False otherwise.
    """
    spec = image.spec()
    channels = spec.channelnames

    if not {"R", "G", "B"}.issubset(channels):
        return False

    roi = oiio.ROI(0, spec.width, 0, spec.height, 0, 1, 0, len(channels))
    pixel_data = np.array(image.get_pixels(oiio.FLOAT, roi)).reshape(
        (spec.height, spec.width, len(channels))
    )

    return np.allclose(pixel_data[:, :, 0], pixel_data[:, :, 1]) and np.allclose(
        pixel_data[:, :, 1], pixel_data[:, :, 2]
    )


def create_greyscale_from_channel(
    channel_data: np.ndarray, width: int, height: int
) -> oiio.ImageBuf:
    """
    Converts grayscale channel data into an OIIO ImageBuf with RGB channels.

    Parameters:
        channel_data (np.ndarray): A NumPy array containing grayscale pixel values.
        width (int): Width of the output image.
        height (int): Height of the output image.

    Returns:
        oiio.ImageBuf: An ImageBuf object where the grayscale data is applied to RGB channels.
    """
    if channel_data.shape != (height, width):
        raise ValueError(
            f"Channel data shape {channel_data.shape} does not match image dimensions ({width}x{height})."
        )

    rgb_data = np.stack([channel_data] * 3, axis=-1)

    spec = oiio.ImageSpec(width, height, 3, oiio.FLOAT)
    image = oiio.ImageBuf(spec)

    roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 3)
    image.set_pixels(roi, rgb_data.astype(np.float32))

    return image
