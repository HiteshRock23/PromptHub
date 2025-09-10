from django.db import models


class Prompt(models.Model):
    """Represents a single prompt in the library."""

    class ContentFormat(models.TextChoices):
        PLAIN = 'plain', 'Plain Text'
        JSON = 'json', 'JSON'
        XML = 'xml', 'XML'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    content = models.TextField(help_text='The actual prompt text or blob.')
    format = models.CharField(
        max_length=10,
        choices=ContentFormat.choices,
        default=ContentFormat.PLAIN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title
