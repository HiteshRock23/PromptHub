from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:  # pragma: no cover
        return self.name


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
    # New fields for structured imports
    tags = models.JSONField(default=list, blank=True)
    prompt = models.TextField(blank=True, help_text='Primary prompt body; supersedes content when present.')
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


class PromptVoteCounter(models.Model):
    """Stores aggregate up/down counts per prompt id.

    We use the integer prompt id from the aggregated feed (XML/JSON ordering).
    User-specific vote state is tracked in the session; counts live here.
    """

    prompt_id = models.IntegerField(unique=True)
    up_count = models.IntegerField(default=0)
    down_count = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["prompt_id"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"Votes(pid={self.prompt_id}, up={self.up_count}, down={self.down_count})"


class ImagePrompt(models.Model):
    """Stores an image preview and its associated generation prompt.

    Images are stored on disk (MEDIA_ROOT) and we persist only the relative path
    so that storage backends can be swapped later (e.g., S3/Cloudinary).
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Optional labels used for filtering and display chips
    tags = models.JSONField(default=list, blank=True)
    prompt_text = models.TextField()
    image = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class ImageVoteCounter(models.Model):
    """Stores aggregate up/down counts per image prompt id.

    Similar to `PromptVoteCounter`, but keyed by `image_id` which is the
    primary key of `ImagePrompt`. User vote state is session-scoped.
    """

    image_id = models.IntegerField(unique=True)
    up_count = models.IntegerField(default=0)
    down_count = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["image_id"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"ImageVotes(iid={self.image_id}, up={self.up_count}, down={self.down_count})"


class Feedback(models.Model):
    class Category(models.TextChoices):
        EXPERIENCE = 'experience', 'Experience'
        BUG = 'bug', 'Bug'
        FEATURE = 'feature', 'Feature Request'
        PROMPT_QUALITY = 'prompt_quality', 'Prompt Quality'

    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    rating = models.IntegerField(null=True, blank=True)
    comments = models.TextField(blank=True)
    prompt = models.ForeignKey(Prompt, null=True, blank=True, on_delete=models.SET_NULL)
    reaction = models.CharField(max_length=8, blank=True)  # e.g., ":love:", ":meh:", ":angry:"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=["category", "created_at"])]

    def __str__(self) -> str:  # pragma: no cover
        who = self.name or 'Anonymous'
        return f"Feedback({who}, {self.category}, rating={self.rating})"