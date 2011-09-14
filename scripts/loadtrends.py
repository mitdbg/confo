from util import *

if __name__ == '__main__':
    load_db = copy_to_table('year_paper_similarity', ['yid', 'pid', 'dist'], './trends.txt')
    load_db()

    load_db = copy_to_table('conf_idf', ['cid', 'word', 'idf'], './idf.txt')
    load_db()
