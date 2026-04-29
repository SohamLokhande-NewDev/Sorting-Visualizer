import random
import ctypes
import os

class SliceStruct(ctypes.Structure):
    _fields_ = [("id", ctypes.c_int), ("index", ctypes.c_int)]

class SortResult(ctypes.Structure):
    _fields_ = [("frames", ctypes.POINTER(ctypes.c_int)), ("frames_count", ctypes.c_int)]

lib_path = os.path.join(os.path.dirname(__file__), "sort_lib.dll")
_lib = ctypes.CDLL(lib_path)

_lib.c_bubble_sort.argtypes = [ctypes.POINTER(SliceStruct), ctypes.c_int]
_lib.c_bubble_sort.restype = SortResult

_lib.c_insertion_sort.argtypes = [ctypes.POINTER(SliceStruct), ctypes.c_int]
_lib.c_insertion_sort.restype = SortResult

_lib.c_quick_sort.argtypes = [ctypes.POINTER(SliceStruct), ctypes.c_int]
_lib.c_quick_sort.restype = SortResult

_lib.c_merge_sort.argtypes = [ctypes.POINTER(SliceStruct), ctypes.c_int]
_lib.c_merge_sort.restype = SortResult

_lib.free_result.argtypes = [SortResult]

def get_shuffled_slices(slices):
    shuffled = slices.copy()
    random.shuffle(shuffled)
    return shuffled

def _run_c_sort(func, slices):
    n = len(slices)
    arr = (SliceStruct * n)()
    for i, s in enumerate(slices):
        arr[i].id = s.id
        arr[i].index = s.slice_index

    res = func(arr, n)
    
    frames = []
    ptr = res.frames
    for i in range(res.frames_count):
        frame = [ptr[i * n + j] for j in range(n)]
        frames.append(frame)

    _lib.free_result(res)
    return frames

def bubble_sort_frames(slices):
    return _run_c_sort(_lib.c_bubble_sort, slices)

def insertion_sort_frames(slices):
    return _run_c_sort(_lib.c_insertion_sort, slices)

def quick_sort_frames(slices):
    return _run_c_sort(_lib.c_quick_sort, slices)

def merge_sort_frames(slices):
    return _run_c_sort(_lib.c_merge_sort, slices)