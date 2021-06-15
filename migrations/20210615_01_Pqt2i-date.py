"""
date
"""

from yoyo import step

__depends__ = {'20210610_01_6lOkJ-votes'}

steps = [
    step(
        "ALTER TABLE meme ADD COLUMN date TIMESTAMP",
        "ALTER TABLE meme DROP COLUMN date",
    )
]
