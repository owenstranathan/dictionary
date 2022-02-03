import os
from urllib import request
import math
import sqlite3
from collections import namedtuple
import argparse


Entry = namedtuple("Entry", ["id", "word", "pos", "definition"])


URLFORMAT = "https://www.mso.anu.edu.au/~ralph/OPTED/v003/wb1913_{}.html"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
DICTIONARY = f"{os.path.abspath(os.path.dirname(__file__))}{os.path.sep}dictionary.db"

def get_words_for_letter(letter, con):
    from bs4 import BeautifulSoup
    print(f"Fetching words for {letter.upper()}")
    req = request.urlopen(URLFORMAT.format(letter))
    print("Soupifying")
    soup = BeautifulSoup(req.read(), "html.parser")
    p_s = soup.find_all("p")
    count = len(p_s)
    for i, p in enumerate(soup.find_all("p")):
        percent = math.ceil(i/count * 10)
        word = p.b.get_text().replace("'", "''").lower()
        pos = p.i.get_text().replace("'", "''")
        definition = (p.i.nextSibling[2:]).replace("'", "''")
        print(f"{percent}", end="\r")
        try:
            con.execute("INSERT INTO words (word, pos, def) VALUES (?, ?, ?);", (word, pos, definition))
        except Exception as e:
            breakpoint()
            print(e)
    print()


def rebuild_dictionary():
    conn = sqlite3.connect(DICTIONARY)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS words(\
        id INT PRIMARY KEY,\
        word TEXT NOT NULL,\
        pos TEXT,\
        def TEXT NOT NULL);")
    for a in ALPHABET:
        get_words_for_letter(a, conn)
    conn.commit()
    conn.close()

def lookup(word, fuzzy=False):
    conn = sqlite3.connect(DICTIONARY)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM words WHERE word{'=' if not fuzzy else ' LIKE '}:word;", {"word":word})
    results = [Entry(*e) for e in cur.fetchall()]
    print(f"Found {len(results)} definition{'s' if len(results)!=1 else ''}.")
    for result in results:
        print(f"{result.word} ({result.pos}) - {result.definition}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Looks up words from an sqlite dictionary.")
    parser.add_argument("word", help="The word to lookup")
    parser.add_argument("-f", "--fuzzy", action="store_true", default=False)
    args = parser.parse_args()
    lookup(args.word, args.fuzzy)
