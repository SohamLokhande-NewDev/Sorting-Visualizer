from django.contrib import admin
from .models import ImageUpload, ImageSlice, SortResult

admin.site.register(ImageUpload)
admin.site.register(ImageSlice)
admin.site.register(SortResult)