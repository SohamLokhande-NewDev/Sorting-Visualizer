import random

def get_shuffled_slices(slices):
    shuffled = slices.copy()
    random.shuffle(shuffled)
    return shuffled

def bubble_sort_frames(slices):
    arr = slices.copy()
    frames = []

    frames.append([s.id for s in arr])

    n = len(arr)

    for i in range(n):
        for j in range(0, n - i - 1):

            # compare based on correct position
            if arr[j].slice_index > arr[j+1].slice_index:
                arr[j], arr[j+1] = arr[j+1], arr[j]

            # store frame (IDs order)
            frames.append([s.id for s in arr])

    return frames

def insertion_sort_frames(slices):
    arr = slices.copy()
    frames = []

    frames.append([s.id for s in arr])

    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1

        while j >= 0 and arr[j].slice_index > key.slice_index:
            arr[j+1] = arr[j]
            j -= 1
            frames.append([s.id for s in arr])

        arr[j+1] = key
        frames.append([s.id for s in arr])

    return frames

def quick_sort_frames(slices):
    arr = slices.copy()
    frames = []

    frames.append([s.id for s in arr])

    def partition(low, high):
        pivot = arr[high].slice_index
        i = low - 1

        for j in range(low, high):
            if arr[j].slice_index < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                frames.append([s.id for s in arr])

        arr[i+1], arr[high] = arr[high], arr[i+1]
        frames.append([s.id for s in arr])

        return i + 1

    def quick_sort(low, high):
        if low < high:
            pi = partition(low, high)
            quick_sort(low, pi - 1)
            quick_sort(pi + 1, high)

    quick_sort(0, len(arr) - 1)

    return frames

def merge_sort_frames(slices):
    arr = slices.copy()
    frames = []

    frames.append([s.id for s in arr])

    def merge_sort(start, end):
        if end - start > 1:
            mid = (start + end) // 2
            merge_sort(start, mid)
            merge_sort(mid, end)

            merge(start, mid, end)

    def merge(start, mid, end):
        left = arr[start:mid]
        right = arr[mid:end]

        i = j = 0
        k = start

        while i < len(left) and j < len(right):
            if left[i].slice_index < right[j].slice_index:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1

            frames.append([s.id for s in arr])
            k += 1

        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1
            frames.append([s.id for s in arr])

        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
            frames.append([s.id for s in arr])

    merge_sort(0, len(arr))

    return frames