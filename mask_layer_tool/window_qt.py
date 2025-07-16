import sys
import os
import OpenImageIO as oiio
import numpy as np

from mask_layer_tool.image_loader import load_image, save_image
from mask_layer_tool.channel_handler import (
    detect_channels,
    extract_channel,
    create_greyscale_from_channel,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QFrame,
)
from PySide6.QtGui import QPixmap, QImage


class ImageChannelSelector(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Texture Channel Tool")
        self.setGeometry(200, 200, 600, 200)

        # UI Elements
        self.open_button = QPushButton("Open Texture Files...", self)
        self.open_button.clicked.connect(self.open_images)

        self.clear_button = QPushButton("Clear Selection", self)
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_selection)

        self.unpack_button = QPushButton("Unpack Channels As Greyscale", self)
        self.unpack_button.setEnabled(False)
        self.unpack_button.clicked.connect(self.unpack_channels)

        self.save_button = QPushButton("Save All Channels As Texture", self)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_packed_image)

        self.channel_label = QLabel("Color Channel Preview:", self)
        self.channel_dropdown = QComboBox(self)
        self.channel_dropdown.setEnabled(False)
        self.channel_dropdown.currentIndexChanged.connect(self.update_preview)

        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(100, 100)

        self.save_greyscale_button = QPushButton("Save Greyscale Channel", self)
        self.save_greyscale_button.setEnabled(False)
        self.save_greyscale_button.clicked.connect(self.save_as_greyscale)

        # Divider line
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.VLine)

        # Layout setup
        layout_left = QVBoxLayout()
        layout_left.addWidget(self.open_button)
        layout_left.addWidget(self.clear_button)
        layout_left.addWidget(self.unpack_button)
        layout_left.addWidget(self.save_button)

        layout_right = QVBoxLayout()
        layout_right.addWidget(self.channel_label)
        layout_right.addWidget(self.channel_dropdown)
        layout_right.addWidget(self.preview_label)
        layout_right.addWidget(self.save_greyscale_button)

        main_layout = QHBoxLayout()
        main_layout.addLayout(layout_left)
        main_layout.addWidget(self.divider)
        main_layout.addLayout(layout_right)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.image_files = []
        self.image_buffers = []

    def open_images(self):
        """
        Opens a file dialog to select image files and loads them into the application.
        The selected images are stored in self.image_files and their corresponding
        image buffers are stored in self.image_buffers.
        The channel dropdown is populated with prefixed channel names based on the
        selected images.
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Image Files (*.exr *.png *.jpg *.tif, *.tiff)"
        )
        if file_paths:
            self.image_files = file_paths
            self.image_buffers = []
            self.channel_dropdown.clear()
            all_channels = []

            for image_path in file_paths:
                image = load_image(image_path)
                if image.initialized:
                    filename = os.path.basename(image_path).split(".")[0]
                    prefixed_channels = [
                        f"{filename}_{channel}" for channel in image.spec().channelnames
                    ]
                    all_channels.extend(prefixed_channels)
                    self.image_buffers.append(image)

            self.channel_dropdown.addItems(all_channels)
            self.channel_dropdown.setEnabled(True)

            self.unpack_button.setEnabled(bool(self.image_buffers))
            self.save_button.setEnabled(bool(self.image_buffers))
            self.clear_button.setEnabled(True)
        else:
            self.unpack_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.clear_button.setEnabled(False)

    def unpack_channels(self):
        """
        Unpacks channels from the loaded images and processes them.
        This function detects channels in the images and processes them for further use.
        It also updates the UI to reflect the unpacked channels.
        """
        if not self.image_buffers:
            return

        print("Unpacking channels...")

        for image, image_path in zip(self.image_buffers, self.image_files):
            filename = os.path.basename(image_path).split(".")[0]

            detected_channels = detect_channels(image)
            for channel, is_used in detected_channels.items():
                if is_used:
                    print(f"Processing channel: {filename}_{channel}")

    def save_packed_image(self):
        """Saves the packed image to a file using OpenImageIO."""
        if not self.image_buffers:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Packed Image",
            "",
            "Image Files (*.exr *.png *.jpg *.tif, *.tiff)",
        )
        if save_path:
            print(f"Saving packed image to: {save_path}")
            self.image_buffers[0].write(save_path)

    def save_as_greyscale(self):
        """Saves the displayed grayscale image to a file."""
        if self.channel_dropdown.count() == 0:
            return

        selected_channel = self.channel_dropdown.currentText()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Greyscale Image",
            "",
            "Image Files (*.exr *.png *.jpg *.tif, *.tiff)",
        )

        if not save_path:
            return

        for image_path, image in zip(self.image_files, self.image_buffers):
            filename = os.path.basename(image_path).split(".")[0]
            if selected_channel.startswith(filename):
                channel_name = selected_channel[len(filename) + 1 :]
                channel_data = extract_channel(image, channel_name)

                width, height = image.spec().width, image.spec().height
                rgb_greyscale_image = create_greyscale_from_channel(
                    channel_data, width, height
                )

                save_image(
                    rgb_greyscale_image,
                    os.path.dirname(save_path),
                    filename=os.path.basename(save_path),
                )

                print(f"Saved greyscale image to: {save_path}")
                break

    def clear_selection(self):
        """Clears all selections and resets the UI."""
        self.image_files = []
        self.image_buffers = []
        self.channel_dropdown.clear()
        self.channel_dropdown.setEnabled(False)
        self.preview_label.clear()
        self.unpack_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.save_greyscale_button.setEnabled(False)
        self.clear_button.setEnabled(False)

    def update_preview(self):
        """Updates preview based on selected channel."""
        if not self.image_buffers or self.channel_dropdown.count() == 0:
            return

        selected_channel = self.channel_dropdown.currentText()

        for image_path, image in zip(self.image_files, self.image_buffers):
            filename = os.path.basename(image_path).split(".")[0]
            if selected_channel.startswith(filename):
                channel_name = selected_channel[len(filename) + 1 :]

                if channel_name not in image.spec().channelnames:
                    return

                channel_data = extract_channel(image, channel_name)

                width, height = image.spec().width, image.spec().height
                rgb_greyscale_image = create_greyscale_from_channel(
                    channel_data, width, height
                )

                roi = oiio.ROI(0, width, 0, height, 0, 1, 0, 3)
                pixel_data = np.array(
                    rgb_greyscale_image.get_pixels(oiio.FLOAT, roi)
                ).reshape((height, width, 3))

                grayscale_preview = (pixel_data[:, :, 0] * 255).astype(np.uint8)

                self.display_grayscale_image(grayscale_preview)
                self.save_greyscale_button.setEnabled(True)
                break

    def display_grayscale_image(self, grayscale_data):
        """Converts NumPy array to QPixmap and displays it in QLabel."""
        height, width = grayscale_data.shape
        image = QImage(grayscale_data, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(image)
        self.preview_label.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageChannelSelector()
    window.show()
    sys.exit(app.exec())
