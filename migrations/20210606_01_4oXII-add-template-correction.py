"""
add template correction
"""

from yoyo import step

__depends__ = {'20210605_03_kceQQ-display-name-for-meme-template'}

steps = [
    step(
        "ALTER TABLE meme ADD COLUMN bad_template INTEGER",
        "ALTER TABLE meme DROP COLUMN bad_template",
    )
]
