"""
app/services/generator/__init__.py
------------------------------------
Public API for the generator package.

Import from here to keep feature services decoupled from file layout:

    from app.services.generator import facebook_comment_generator
    from app.services.generator import BaseReplyGenerator   # for type hints
"""
from .base_generator import BaseReplyGenerator
from .generators.facebook_comment_generator import (
    FacebookCommentGenerator,
    facebook_comment_generator,
)

__all__ = [
    "BaseReplyGenerator",
    "FacebookCommentGenerator",
    "facebook_comment_generator",
]
