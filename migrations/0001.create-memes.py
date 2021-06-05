from yoyo import step
import os

template_path = 'template'
templates = [(1+i, f) for i, f in enumerate(os.listdir(template_path)) if os.path.isfile(os.path.join(template_path, f))]

steps = [
   step(
       "CREATE TABLE meme_template (id SERIAL PRIMARY KEY, name VARCHAR(40))",
       "DROP TABLE meme_template"
   ),
   step(
       "INSERT INTO meme_template (id, name) VALUES " + ','.join(map(lambda m: f"({m[0]}, '{m[1]}')", templates)),
   ),
   step(
       "CREATE TABLE meme (id SERIAL PRIMARY KEY, update_id BIGINT, template INT, text TEXT)",
       "DROP TABLE meme"
   ),
]
