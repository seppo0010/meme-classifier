"""
message id and channel id
"""

from yoyo import step

__depends__ = {'0001.create-memes'}

steps = [
   step(
       "ALTER TABLE meme DROP COLUMN update_id",
       "ALTER TABLE meme ADD COLUMN update_id BIGINT",
   ),
   step(
       "ALTER TABLE meme ADD COLUMN chat_id BIGINT",
       "ALTER TABLE meme DROP COLUMN chat_id",
   ),
   step(
       "ALTER TABLE meme ADD COLUMN message_id BIGINT",
       "ALTER TABLE meme DROP COLUMN message_id",
   ),
]
