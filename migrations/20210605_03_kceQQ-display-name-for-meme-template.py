"""
display name for meme template
"""

from yoyo import step

__depends__ = {'20210605_02_fBxx5-full-text-search'}

steps = [
    step(
        "alter table meme_template add column display_name VARCHAR(40)",
        "alter table meme_template drop column display_name",
    )
]
