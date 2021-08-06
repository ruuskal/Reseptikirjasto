CREATE TABLE users (
    id SERIAL PRIMARY KEY, 
    username TEXT UNIQUE, 
    password TEXT
);

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY, 
    name INTEGER NOT NULL, 
    added_by INTEGER REFERENCES users
);

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY, 
    ingredient TEXT, 
    amount NUMERIC, 
    unit TEXT, 
    recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE
);

CREATE TABLE instructions (
    id SERIAL PRIMARY KEY,
    step TEXT,
    recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
    sequence INTEGER
); 

CREATE TABLE library (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
);