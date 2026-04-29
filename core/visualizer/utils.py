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
    
    if hasattr(image_instance, 'is_scrambled') and image_instance.is_scrambled:
        solve_scrambled_image(image_instance)


def solve_scrambled_image(image_instance):
    from .models import ImageSlice
    import numpy as np

    slices = list(ImageSlice.objects.filter(image=image_instance).order_by('id'))
    n = len(slices)
    if n <= 1: return

    # Load all slice images
    slice_images = []
    for s in slices:
        img_path = s.image_part.path
        img = cv2.imread(img_path)
        slice_images.append(img)

    # Compute cost matrix: cost[i][j] = difference between right edge of i and left edge of j
    # We'll use Mean Squared Error of the edge pixels
    cost = np.zeros((n, n))
    for i in range(n):
        right_edge = slice_images[i][:, -1, :]
        for j in range(n):
            if i == j:
                cost[i][j] = float('inf')
            else:
                left_edge = slice_images[j][:, 0, :]
                cost[i][j] = np.mean((right_edge.astype(np.float32) - left_edge.astype(np.float32)) ** 2)

    # Greedy TSP to find the sequence
    # Find the best starting slice (the one whose left edge matches the least with any other slice's right edge)
    best_start = 0
    max_min_left_cost = -1
    for j in range(n):
        # min cost for any slice i to be to the left of j
        min_cost = min([cost[i][j] for i in range(n) if i != j])
        if min_cost > max_min_left_cost:
            max_min_left_cost = min_cost
            best_start = j

    # Build sequence
    seq = [best_start]
    used = set([best_start])
    curr = best_start

    while len(seq) < n:
        best_next = -1
        best_cost = float('inf')
        for j in range(n):
            if j not in used and cost[curr][j] < best_cost:
                best_cost = cost[curr][j]
                best_next = j
        
        seq.append(best_next)
        used.add(best_next)
        curr = best_next

    # Assign target index
    target_indices = {orig_idx: target_idx for target_idx, orig_idx in enumerate(seq)}

    for i, s in enumerate(slices):
        s.slice_index = target_indices[i]
        s.save()
