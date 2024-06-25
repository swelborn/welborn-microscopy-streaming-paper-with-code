from PIL import Image


def slice_image(image_path, output_folder):
    """
    Slices an image into 4 equal parts vertically and saves them.

    Parameters:
        image_path (str): The path to the image to be sliced.
        output_folder (str): The folder where the sliced images will be saved.

    Returns:
        None
    """
    # Open the image using PIL
    img = Image.open(image_path)

    # Get the dimensions of the image
    width, height = img.size

    # Calculate the height of each slice
    slice_height = height // 4

    # Loop to create each slice
    for i in range(4):
        left = 0
        right = width
        upper = i * slice_height
        lower = (
            (i + 1) * slice_height if i != 3 else height
        )  # Use the image's lower edge for the last slice

        # Crop the image to create the slice
        img_slice = img.crop((left, upper, right, lower))

        # Save the slice
        img_slice.save(f"{output_folder}/slice_{i + 1}.png")


if __name__ == "__main__":
    image_path = "./fake_cbed.png"
    output_folder = "./"

    # Call the function to slice the image
    slice_image(image_path, output_folder)
