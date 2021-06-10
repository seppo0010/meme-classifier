"""
votes
"""

from yoyo import step

__depends__ = {'20210606_02_bhyLe-temporarily-store-searches'}

steps = [
    step(
        "ALTER TABLE meme ADD COLUMN upvotes INT DEFAULT 0",
        "ALTER TABLE meme DROP COLUMN upvotes",
    ),
    step(
        "ALTER TABLE meme ADD COLUMN downvotes INT DEFAULT 0",
        "ALTER TABLE meme DROP COLUMN downvotes",
    ),
]
