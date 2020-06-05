import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# For managing connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# To create different sessions
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)

    authors = {}
    count = 0
    number = 0

    for isbn, title, author, year in reader:
        break

    for isbn, title, author, year in reader:
        author_id = authors.get(author)
        
        if author_id is None:
            count += 1
            authors[author] = count
            author_id = count
            db.execute("INSERT INTO authors (name) VALUES (:name)", {"name": author})
        
        db.execute("INSERT INTO books (isbn, title, author_id, year) VALUES (:isbn, :title, :author_id, :year)", 
                    {"isbn": isbn, "title": title, "author_id": author_id, "year": year})
        number += 1
        print(number)
        
    db.commit()

if __name__ == "__main__":
    main()