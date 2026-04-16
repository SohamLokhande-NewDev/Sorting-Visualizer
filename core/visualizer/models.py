from django.db import models

class ImageUpload(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='uploads/')
    num_slices = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ImageSlice(models.Model):
    image = models.ForeignKey(ImageUpload, on_delete=models.CASCADE)
    slice_index = models.IntegerField()
    image_part = models.ImageField(upload_to='slices/')

    def __str__(self):
        return f"Slice {self.slice_index} of {self.image.name}"
    
class SortResult(models.Model):
    image = models.ForeignKey(ImageUpload, on_delete=models.CASCADE)
    
    algorithm = models.CharField(max_length=50)
    
    comparisons = models.IntegerField()
    swaps = models.IntegerField()
    execution_time = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.algorithm} - {self.image.name}"
