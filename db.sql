CREATE TABLE IF NOT EXISTS quote (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    url VARCHAR(255),
    likes INTEGER,
    date DATETIME
);