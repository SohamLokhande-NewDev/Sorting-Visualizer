import cv2
import numpy as np
import random

# Load image
img = cv2.imread("horse.png")   # change path if needed

# Get dimensions
h, w = img.shape[:2]

# Define grid (4 x 5 = 20 slices)
rows, cols = 4, 5
slice_h = h // rows
slice_w = w // cols

# Step 1: Slice image
slices = []
for i in range(rows):
    for j in range(cols):
        y1 = i * slice_h
        y2 = (i + 1) * slice_h if i != rows - 1 else h
        x1 = j * slice_w
        x2 = (j + 1) * slice_w if j != cols - 1 else w

        piece = img[y1:y2, x1:x2]
        slices.append(piece)

# Step 2: Shuffle slices randomly
random.shuffle(slices)

# Step 3: Reconstruct shuffled image
shuffled_img = np.zeros_like(img)

index = 0
for i in range(rows):
    for j in range(cols):
        y1 = i * slice_h
        y2 = (i + 1) * slice_h if i != rows - 1 else h
        x1 = j * slice_w
        x2 = (j + 1) * slice_w if j != cols - 1 else w

        shuffled_img[y1:y2, x1:x2] = slices[index]
        index += 1

# Step 4: Save result
cv2.imwrite("shuffled_image.jpg", shuffled_img)

# Optional: Display
cv2.imshow("Shuffled Image", shuffled_img)
cv2.waitKey(0)
cv2.destroyAllWindows()