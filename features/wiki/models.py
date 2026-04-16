from django.db import models


class WikiPage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Markdown content")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "wiki page"
        verbose_name_plural = "wiki pages"

    def __str__(self):
        return self.title
