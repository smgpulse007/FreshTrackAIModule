from PIL import Image
import numpy as np

def preprocess_image(image: Image.Image) -> Image.Image:
    # Convert the image to grayscale
    gray_image = image.convert("L")
    
    # Resize the image to a standard size (e.g., 800x800)
    resized_image = gray_image.resize((800, 800), Image.ANTIALIAS)
    
    # Convert the image to a numpy array for further processing if needed
    image_array = np.array(resized_image)
    
    return resized_image, image_array

def enhance_image(image: Image.Image) -> Image.Image:
    # Apply additional enhancements if necessary (e.g., contrast adjustment)
    # This is a placeholder for any enhancement techniques
    return image  # Return the enhanced image (currently no enhancement applied)