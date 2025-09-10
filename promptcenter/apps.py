from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command


class PromptcenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'promptcenter'

    def ready(self) -> None:
        # Auto-load initial prompts once after migrations on a fresh database
        def _load_initial_prompts(sender, **kwargs):
            try:
                from .models import Prompt  # local import after apps are ready
                if Prompt.objects.exists():
                    return
                # Fresh DB: load bundled JSON sample data
                call_command('loaddata', 'promptcenter/fixtures/sample_prompts.json')
            except Exception:
                # Silently ignore if fixture not found or already loaded
                return

        post_migrate.connect(_load_initial_prompts, sender=self)
