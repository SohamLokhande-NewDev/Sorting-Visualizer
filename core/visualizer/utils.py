import cv2
import os

def slice_and_store(image_instance):
    from .models import ImageSlice
    img_path = image_instance.image.path
    img = cv2.imread(img_path)

    # Safety check
    if img is None:
        print("Error: Image not loaded properly")
        return

    height, width, _ = img.shape
    num_slices = image_instance.num_slices
    slice_width = width // num_slices

    os.makedirs("media/slices", exist_ok=True)

    for i in range(num_slices):
        x_start = i * slice_width

        # ✅ Fix for last slice
        if i == num_slices - 1:
            x_end = width
        else:
            x_end = (i + 1) * slice_width

        slice_img = img[:, x_start:x_end]

        filename = f"slice_{image_instance.id}_{i}.jpg"
        filepath = os.path.join("media/slices", filename)

        cv2.imwrite(filepath, slice_img)

        ImageSlice.objects.create(
            image=image_instance,
            slice_index=i,
            image_part=f"slices/{filename}"
        )