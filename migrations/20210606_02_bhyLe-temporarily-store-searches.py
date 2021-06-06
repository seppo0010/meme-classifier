"""
temporarily store searches
"""

from yoyo import step

__depends__ = {'20210606_01_4oXII-add-template-correction'}

steps = [
    step(
        '''
        CREATE TABLE search_results ( id SERIAL PRIMARY KEY, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, results TEXT )
        ''',
        '''
        DROP TABLE search_results
        ''',
    ),
]
