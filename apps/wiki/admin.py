from django.contrib import admin

from .models import WikiPage


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
