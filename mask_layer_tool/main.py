#!/usr/bin/env python

import sys
import argparse
import os

from mask_layer_tool.image_loader import load_image, save_image
from mask_layer_tool.channel_handler import (
    detect_channels,
    extract_channel,
    append_channel,
    create_greyscale_from_channel,
)

from PySide6.QtWidgets import QApplication
from window_qt import ImageChannelSelector


def check(source_image_path: str) -> None:
    """
    Check if the image is grayscale and print the detected channels.

    Parameters:
        source_image_path (str): Path to the source image file.

    Returns:
        None
    """
    image = load_image(source_image_path)
    detected_channels = detect_channels(image)
    print(f"Detected channels: {detected_channels}")


def pack(files: list, destination: str) -> None:
    """
    Packs multiple EXR images into a single EXR file containing all color channels.

    Parameters:
        files (list): A list of image file paths to combine.
        destination (str): Path to save the final packed EXR image.

    Returns:
        None
    """
    if not files:
        print("Error: No files provided for packing.")
        return

    print(f"Packing images: {files} into {destination}")

    # Using base image to create a new image with the same dimensions,
    # would prefer to use a new image specification but OIIO does not
    # support creating an empty image with no channels properly.
    # TODO: Figure out how to get working this way, or figure out how
    # to rename first file channels to include filename.
    #
    # spec = oiio.ImageSpec(base_image.spec().width, base_image.spec().height, 0, oiio.FLOAT)
    # packed_image = oiio.ImageBuf(spec)

    base_image = load_image(files[0])
    packed_image = base_image

    for image_path in files[1:]:  # Skip first image cause loaded with base_image
        image = load_image(image_path)
        filename = os.path.basename(image_path).split(".")[0]

        # Extract and append each channel from the image
        for channel in image.spec().channelnames:  # might reverse
            unique_name = f"{filename}_{channel}"
            channel_data = extract_channel(image, channel)
            packed_image = append_channel(packed_image, channel_data, unique_name)

    packed_dir = os.path.join(destination, "packed")
    os.makedirs(packed_dir, exist_ok=True)
    save_image(packed_image, packed_dir, "packed_image.exr")


def unpack(source_image_path: str, destination: str) -> None:
    """
    Unpacks all detected channels from an image, converts each to an RGB grayscale image,
    and saves them using OpenImageIO.

    Parameters:
        source_image_path (str): Path to the source image file.
        destination (str): Directory to save the extracted grayscale channel images.

    Returns:
        None
    """
    print(f"Unpacking channels from {source_image_path} into {destination}")

    image_filename = os.path.splitext(os.path.basename(source_image_path))[0]
    image_output_dir = os.path.join(destination, image_filename)
    os.makedirs(image_output_dir, exist_ok=True)

    image = load_image(source_image_path)
    spec = image.spec()
    width, height = spec.width, spec.height
    channels = spec.channelnames

    print(f"Detected channels: {channels}")

    for ch in channels:
        try:
            channel_data = extract_channel(image, ch)
            rgb_greyscale_image = create_greyscale_from_channel(
                channel_data, width, height
            )
            save_image(rgb_greyscale_image, image_output_dir, f"{ch}.exr")
        except Exception as e:
            print(f"Skipping channel {ch} due to error: {e}")


def main():
    print("Hello from pipeline-project-wjake!")
    parser = argparse.ArgumentParser(description="Pack and Unpack texture-maps")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create parser for the "pack" command
    pack_parser = subparsers.add_parser("pack", help="Pack files into a package")
    pack_parser.add_argument(
        "files", nargs="+", type=str, help="File paths to pack (unlimited files)"
    )
    pack_parser.add_argument(
        "destination",
        type=str,
        nargs="?",
        default="out/",
        help="Destination directory (default: out/)",
    )

    # Create parser for the "unpack" command
    unpack_parser = subparsers.add_parser(
        "unpack", help="Unpack a package into a directory"
    )
    unpack_parser.add_argument("source", type=str, help="Source package file to unpack")
    unpack_parser.add_argument(
        "destination",
        type=str,
        nargs="?",
        default="out/unpacked/",
        help="Destination directory (default: out/unpacked/)",
    )

    # Create parser for the "check" command
    check_parser = subparsers.add_parser("check", help="Check if an image is greyscale")
    check_parser.add_argument("source", type=str, help="Image file to check")

    args = parser.parse_args()

    if len(sys.argv) > 1:
        if args.command == "pack":
            pack(args.files, args.destination)
        elif args.command == "unpack":
            unpack(args.source, args.destination)
        elif args.command == "check":
            check(args.source)
        else:
            parser.print_help()
    else:
        app = QApplication(sys.argv)
        window = ImageChannelSelector()
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
