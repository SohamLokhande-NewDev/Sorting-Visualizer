import cv2
import os
from .models import ImageSlice

def slice_and_store(image_instance):
    img_path = image_instance.image.path
    img = cv2.imread(img_path)

    height, width, _ = img.shape
    num_slices = image_instance.num_slices
    slice_width = width // num_slices

    slices = []

    for i in range(num_slices):
        x_start = i * slice_width
        x_end = (i + 1) * slice_width

        slice_img = img[:, x_start:x_end]

        filename = f"slice_{image_instance.id}_{i}.jpg"
        filepath = os.path.join("media/slices", filename)

        # Ensure folder exists
        os.makedirs("media/slices", exist_ok=True)

        cv2.imwrite(filepath, slice_img)

        # Save in DB
        slice_obj = ImageSlice.objects.create(
            image=image_instance,
            slice_index=i,
            image_part=f"slices/{filename}"
        )

        slices.append(slice_obj)

    return slices