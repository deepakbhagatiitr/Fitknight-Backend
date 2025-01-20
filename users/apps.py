from django.apps import AppConfig
import os


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Creating media directories if they don't exist
        media_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media')
        profile_images_dir = os.path.join(media_root, 'profile_images')
        
        if not os.path.exists(media_root):
            os.makedirs(media_root)
        if not os.path.exists(profile_images_dir):
            os.makedirs(profile_images_dir)
