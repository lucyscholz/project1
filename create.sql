CREATE TABLE books (
    isbn VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year VARCHAR NOT NULL
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY
    isbn VARCHAR NOT NULL,
    rating INTEGER NOT NULL,
    review VARCHAR,
    user_id VARCHAR NOT NULL
);

CREATE TABLE users (
    user_id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    date_created TIMESTAMP NOT NULL
);
