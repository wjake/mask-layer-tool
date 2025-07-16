import os
import OpenImageIO as oiio


def load_image(image_path: str) -> oiio.ImageBuf:
    """
    Load an image from the given path using OpenImageIO.

    Returns an ImageBuf if successful, raises an exception otherwise.
    """
    image = oiio.ImageBuf(image_path)
    if not image.initialized:
        raise ValueError(f"Error loading image: {image_path}")

    return image


def save_image(
    image: oiio.ImageBuf, destination: str, filename: str = "output.exr"
) -> None:
    """
    Save an OpenImageIO ImageBuf to the specified destination.
    If the destination directory does not exist, it will be created.

    Parameters:
        image (oiio.ImageBuf): The image object to save.
        destination (str): The directory where the image will be saved.
        filename (str): The output filename.

    Returns:
        None
    """
    if not os.path.exists(destination):
        os.makedirs(destination)

    output_path = os.path.join(destination, filename)

    if not image.write(output_path):
        raise ValueError(f"Failed to save image to {output_path}")

    print(f"Image saved to {output_path}")
