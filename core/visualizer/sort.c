#include <stdlib.h>

typedef struct {
    int id;
    int index;
} Slice;

typedef struct {
    int* frames;
    int frames_count;
} SortResult;

void record_frame(Slice* arr, int n, int** frames, int* capacity, int* count) {
    if (*count >= *capacity) {
        *capacity = (*capacity == 0) ? 16 : (*capacity) * 2;
        *frames = (int*)realloc(*frames, (*capacity) * n * sizeof(int));
    }
    for (int i = 0; i < n; i++) {
        (*frames)[(*count) * n + i] = arr[i].id;
    }
    (*count)++;
}

SortResult bubble_sort(Slice* arr, int n) {
    int* frames = NULL;
    int capacity = 0;
    int count = 0;
    record_frame(arr, n, &frames, &capacity, &count);

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j].index > arr[j+1].index) {
                Slice temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
            record_frame(arr, n, &frames, &capacity, &count);
        }
    }

    SortResult result = {frames, count};
    return result;
}

SortResult insertion_sort(Slice* arr, int n) {
    int* frames = NULL;
    int capacity = 0;
    int count = 0;
    record_frame(arr, n, &frames, &capacity, &count);

    for (int i = 1; i < n; i++) {
        Slice key = arr[i];
        int j = i - 1;

        while (j >= 0 && arr[j].index > key.index) {
            arr[j+1] = arr[j];
            j--;
            record_frame(arr, n, &frames, &capacity, &count);
        }
        arr[j+1] = key;
        record_frame(arr, n, &frames, &capacity, &count);
    }

    SortResult result = {frames, count};
    return result;
}

void _quick_sort(Slice* arr, int low, int high, int n, int** frames, int* capacity, int* count) {
    if (low < high) {
        int pivot = arr[high].index;
        int i = low - 1;

        for (int j = low; j < high; j++) {
            if (arr[j].index < pivot) {
                i++;
                Slice temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
                record_frame(arr, n, frames, capacity, count);
            }
        }

        Slice temp = arr[i+1];
        arr[i+1] = arr[high];
        arr[high] = temp;
        record_frame(arr, n, frames, capacity, count);

        int pi = i + 1;
        _quick_sort(arr, low, pi - 1, n, frames, capacity, count);
        _quick_sort(arr, pi + 1, high, n, frames, capacity, count);
    }
}

SortResult quick_sort(Slice* arr, int n) {
    int* frames = NULL;
    int capacity = 0;
    int count = 0;
    record_frame(arr, n, &frames, &capacity, &count);

    _quick_sort(arr, 0, n - 1, n, &frames, &capacity, &count);

    SortResult result = {frames, count};
    return result;
}

void _merge(Slice* arr, int start, int mid, int end, int n, int** frames, int* capacity, int* count) {
    int n1 = mid - start;
    int n2 = end - mid;

    Slice* L = (Slice*)malloc(n1 * sizeof(Slice));
    Slice* R = (Slice*)malloc(n2 * sizeof(Slice));

    for (int i = 0; i < n1; i++) L[i] = arr[start + i];
    for (int j = 0; j < n2; j++) R[j] = arr[mid + j];

    int i = 0, j = 0, k = start;

    while (i < n1 && j < n2) {
        if (L[i].index < R[j].index) {
            arr[k] = L[i];
            i++;
        } else {
            arr[k] = R[j];
            j++;
        }
        record_frame(arr, n, frames, capacity, count);
        k++;
    }

    while (i < n1) {
        arr[k] = L[i];
        i++;
        k++;
        record_frame(arr, n, frames, capacity, count);
    }

    while (j < n2) {
        arr[k] = R[j];
        j++;
        k++;
        record_frame(arr, n, frames, capacity, count);
    }

    free(L);
    free(R);
}

void _merge_sort(Slice* arr, int start, int end, int n, int** frames, int* capacity, int* count) {
    if (end - start > 1) {
        int mid = start + (end - start) / 2;
        _merge_sort(arr, start, mid, n, frames, capacity, count);
        _merge_sort(arr, mid, end, n, frames, capacity, count);
        _merge(arr, start, mid, end, n, frames, capacity, count);
    }
}

SortResult merge_sort(Slice* arr, int n) {
    int* frames = NULL;
    int capacity = 0;
    int count = 0;
    record_frame(arr, n, &frames, &capacity, &count);

    _merge_sort(arr, 0, n, n, &frames, &capacity, &count);

    SortResult result = {frames, count};
    return result;
}

__declspec(dllexport) SortResult c_bubble_sort(Slice* arr, int n) { return bubble_sort(arr, n); }
__declspec(dllexport) SortResult c_insertion_sort(Slice* arr, int n) { return insertion_sort(arr, n); }
__declspec(dllexport) SortResult c_quick_sort(Slice* arr, int n) { return quick_sort(arr, n); }
__declspec(dllexport) SortResult c_merge_sort(Slice* arr, int n) { return merge_sort(arr, n); }
__declspec(dllexport) void free_result(SortResult res) { if(res.frames) free(res.frames); }
