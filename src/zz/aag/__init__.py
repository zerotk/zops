from fileinput import filename
from pathlib import Path

from zerotk import deps
from zz.services.console import Console
from zz.services.filesystem import FileSystem
from zz.services.template_engine import TemplateEngine


# @deps.define
# class AagEngine:
#
#   filesystem = deps.Singleton(FileSystem)
#   template_engine = deps.Singleton(TemplateEngine)
#   console = deps.Singleton(Console)
#
#   def run(self, playbook_filename: Path):
#     """
#     Apply AAG configuration from the specified playbook.
#     """
#     print(f"Applying AAG configuration in {playbook_filename}")


# BASE_DIR = Path(__file__).resolve().parent.parent
#
# class DjangoSlice:
#   pass
#
# class AppDjangoSlice(DjangoSlice):
#
#   settings = dict(
#     BASE_DIR = BASE_DIR,
#     SECRET_KEY = "9999",
#     DEBUG = True,
#     ALLOWED_HOSTS = [],
#     INSTALLED_APPS = [
#       "django.contrib.admin",
#       "django.contrib.auth",
#       "django.contrib.contenttypes",
#       "django.contrib.sessions",
#       "django.contrib.messages",
#       "django.contrib.staticfiles",
#     ],
#     MIDDLEWARE = [
#       "django.middleware.security.SecurityMiddleware",
#       "django.contrib.sessions.middleware.SessionMiddleware",
#       "django.middleware.common.CommonMiddleware",
#       "django.middleware.csrf.CsrfViewMiddleware",
#       "django.contrib.auth.middleware.AuthenticationMiddleware",
#       "django.contrib.messages.middleware.MessageMiddleware",
#       "django.middleware.clickjacking.XFrameOptionsMiddleware",
#     ],
#     ROOT_URLCONF = f"{APP_NAME}.urls",
#     TEMPLATES = [
#       {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [],
#         "APP_DIRS": True,
#         "OPTIONS": {
#           "context_processors": [
#             "django.template.context_processors.request",
#             "django.contrib.auth.context_processors.auth",
#             "django.contrib.messages.context_processors.messages",
#           ],
#         },
#       },
#     ],
#     WSGI_APPLICATION = f"{APP_NAME}.wsgi.application",
#     # Database
#     # https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#     DATABASES = {
#       "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#       }
#     },
#     # Password validation
#     # https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
#     AUTH_PASSWORD_VALIDATORS = [
#       {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#       },
#       {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#       },
#       {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#       },
#       {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#       },
#     ],
#     # Internationalization
#     # https://docs.djangoproject.com/en/5.2/topics/i18n/
#     LANGUAGE_CODE = "en-us",
#     TIME_ZONE = "UTC",
#     USE_I18N = True,
#     USE_TZ = True,
#     # Static files (CSS, JavaScript, Images)
#     # https://docs.djangoproject.com/en/5.2/howto/static-files/
#     STATIC_URL = "static/",
#     # Default primary key field type
#     # https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
#     DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField",
#   )
#
#   def urlpatterns(self):
#     from django.contrib import admin
#     from django.urls import path
#
#     return [
#       path("admin/", admin.site.urls),
#     ]


class DjangoAppBuilder:

  def __init__(self, app_name, admin_username, admin_email, admin_password):
    self.app_name = app_name
    self.admin_username = admin_username
    self.admin_email = admin_email
    self.admin_password = admin_password

    self.slices = []

    self.__settings = {}
    self.__urlpatterns = []
    self.generate_file(
      f"manage.py",
      f'''
        """Django's command-line utility for administrative tasks."""
        import os
        import sys


        def main():
            """Run administrative tasks."""
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ self.app_name }}.settings")
            try:
                from django.core.management import execute_from_command_line
            except ImportError as exc:
                raise ImportError(
                    "Couldn't import Django. Are you sure it's installed and "
                    "available on your PYTHONPATH environment variable? Did you "
                    "forget to activate a virtual environment?"
                ) from exc
            execute_from_command_line(sys.argv)


        if __name__ == "__main__":
            main()
      '''
    )
    self.generate_file(
      f"{self.app_name}/settings.py",
      f"""
      """
    )
    self.generate_file(
      f"{self.app_name}/urls.py",
      f"""
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parent.parent
      """
    )
    self.generate_file(
      f"bin/bootstrap.sh",
      """
        #!/usr/bin/env bash
        set -eou pipefail

        SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
        cd "$SCRIPTDIR/.."

        # Create virtual environment
        rm -rf venv
        python3 -m venv venv
        source venv/bin/activate

        # Install slices
        for slice in slices:
          echo "Installing slice: $slice.name"
          pip install --upgrade {" ".join(slice.python_packages)}
      """
    )

  def settings_module(self):
    # Merge settings from all slices.
    self.__settings = {}
    for slice in self.slices:
      self.__settings.update(slice.settings)
    return self.__settings.get_item, lambda: self.__settings.keys()

  def urlpatterns(self):
    # Merge url patterns from all slices.
    self.__urlpatterns = []
    for slice in self.slices:
      self.__urlpatterns.extend(slice.urlpatterns())
    return self.__urlpatterns

  def AddAdminTheme(self):
    pass

  def generate(self):
    result = """
    python3 -m venv venv
    source venv/bin/activate
    """
    for i_slice in self.slices:
      result += f"""
        # {i_slice.name}
        pip install --update {" ".join(i_slice.python_packages)}
      """
    create_file("bin/bootstrap.sh", result)


# class AdminThemeSlice(DjangoSlice):
#   name = "jet-reboot"
#   python_packages = ["django-jet-reboot"]
#   settings_INSTALLED_APPS = [
#     "jet",
#   ]
#
#   def urlpatterns(self):
#     from django.urls import path, include
#
#     return [
#       path("jet/", include("jet.urls", "jet")),
#     ]
#
#   def run_manage(self):
#     return [
#       "migrate",
#       "collectstatic",
#   ]
