
CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, userpass VARCHAR NOT NULL);

CREATE TABLE ingredients(
    ing_name VARCHAR(50), 
    ing_id integer PRIMARY KEY,
    unit_list VARCHAR(50),
    image VARCHAR(50));

CREATE TABLE in_frige(
    id BIGSERIAL,
    user_id integer REFERENCES users,
    ing_id integer REFERENCES ingredients,
    unit VARCHAR(50),
    quantity integer,
    PRIMARY KEY(user_id, ing_id));

CREATE TABLE buy(
    id SERIAL,
    user_id INTEGER, 
    ing_id INTEGER,    
    PRIMARY KEY(user_id, ing_id));

CREATE TABLE favorite(
    user_id INTEGER,
    recipe_id INTEGER,    
    PRIMARY KEY(user_id, recipe_id));

