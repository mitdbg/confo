from util import *

if __name__ == '__main__':
    load_db = copy_to_table('words', ['pid', 'word'], './allwords.txt')
    load_db()
