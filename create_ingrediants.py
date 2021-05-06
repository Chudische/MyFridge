from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import get_data_from_csv

# Connect to databse
engine = create_engine("postgres://kiommsutykfchx:e539f088927d094a7bc4c542fb7c0f7b9a1598046145ee8755dcafd523be97d1@ec2-54-217-234-157.eu-west-1.compute.amazonaws.com:5432/dfpkb416sr6slt")
db = scoped_session(sessionmaker(bind=engine))


#Insert isngrediants in table from csv
data = get_data_from_csv("top-1k-ingredients.csv")
for row in data:
    db.execute("INSERT INTO ingredients( ing_name, ing_id) VALUES (:ing_name, :ing_id)",
        {"ing_name" : row[0], "ing_id" : row[1]})
    print(row, "--- is addet")
db.commit()
print("All done")



