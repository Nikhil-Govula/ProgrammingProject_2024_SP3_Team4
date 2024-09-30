# src/views/__init__.py

from .index_views import index_bp
from .landing_views import landing_bp
from .user_views import user_bp
from .employer_views import employer_bp
from .admin_views import admin_bp

__all__ = ['index_bp', 'landing_bp', 'user_bp', 'employer_bp', 'admin_bp']
