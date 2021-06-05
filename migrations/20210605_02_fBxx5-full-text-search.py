"""
full text search
"""

from yoyo import step

__depends__ = {'20210605_01_YbdtM-message-id-and-channel-id'}

steps = [
    step(
        "ALTER TABLE meme ADD COLUMN tsv tsvector",
        "ALTER TABLE meme DROP COLUMN tsv",
    ),
    step(
        "CREATE INDEX tsv_idx ON meme USING gin(tsv);",
        "DROP INDEX tsv_idx",
    ),
    step(
        '''
        CREATE FUNCTION meme_search_trigger() RETURNS trigger AS $$
        begin
          new.tsv :=
            to_tsvector('english', coalesce(new.text,'')) || to_tsvector('spanish', coalesce(new.text,''));
          return new;
        end
        $$ LANGUAGE plpgsql;
        ''',
        'DROP FUNCTION meme_search_trigger'
    ),
    step(
        '''
        CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
        ON meme FOR EACH ROW EXECUTE PROCEDURE meme_search_trigger();
        '''
    )
]
