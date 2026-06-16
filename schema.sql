-- ================================================================
-- SCHEMA  Fanta Temptation Island  --  PostgreSQL / Supabase
-- Incolla TUTTO questo testo nel SQL Editor di Supabase e premi RUN
-- ================================================================

CREATE TABLE IF NOT EXISTS utenti (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coppie (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    eliminata INTEGER DEFAULT 0,
    attiva INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS squadre (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES utenti(id),
    nome_squadra TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS squadra_coppie (
    id SERIAL PRIMARY KEY,
    squadra_id INTEGER NOT NULL REFERENCES squadre(id),
    coppia_id INTEGER NOT NULL REFERENCES coppie(id),
    UNIQUE (squadra_id, coppia_id)
);

CREATE TABLE IF NOT EXISTS puntate (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL UNIQUE,
    aperta INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schieramenti (
    id SERIAL PRIMARY KEY,
    squadra_id INTEGER NOT NULL REFERENCES squadre(id),
    puntata_id INTEGER NOT NULL REFERENCES puntate(id),
    coppia_id INTEGER NOT NULL REFERENCES coppie(id),
    UNIQUE (squadra_id, puntata_id, coppia_id)
);

CREATE TABLE IF NOT EXISTS eventi (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    punti INTEGER NOT NULL,
    descrizione TEXT,
    ripetibile INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS eventi_coppie (
    id SERIAL PRIMARY KEY,
    coppia_id INTEGER NOT NULL REFERENCES coppie(id),
    evento_id INTEGER NOT NULL REFERENCES eventi(id),
    puntata_id INTEGER NOT NULL REFERENCES puntate(id),
    quantita INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leghe (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    codice TEXT NOT NULL UNIQUE,
    creatore_id INTEGER NOT NULL REFERENCES utenti(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lega_membri (
    id SERIAL PRIMARY KEY,
    lega_id INTEGER NOT NULL REFERENCES leghe(id),
    user_id INTEGER NOT NULL REFERENCES utenti(id),
    UNIQUE (lega_id, user_id)
);

CREATE TABLE IF NOT EXISTS impostazioni (
    chiave TEXT PRIMARY KEY,
    valore TEXT
);

-- ================================================================
-- SEED: admin + 6 coppie + 6 eventi + puntata 1
-- (eseguito solo se le tabelle sono vuote)
-- ================================================================

INSERT INTO utenti (username, password, is_admin)
SELECT 'admin', 'admin123', 1
WHERE NOT EXISTS (SELECT 1 FROM utenti WHERE is_admin = 1);

INSERT INTO coppie (nome)
SELECT unnest(ARRAY[
    'Marco & Sara',
    'Luca & Giulia',
    'Alessandro & Federica',
    'Davide & Martina',
    'Simone & Chiara',
    'Andrea & Valentina'
])
WHERE NOT EXISTS (SELECT 1 FROM coppie);

INSERT INTO eventi (nome, punti, descrizione, ripetibile)
SELECT * FROM (VALUES
    ('Bacio con un tentatore',      10, 'Bacio con un single/tentatore', 1),
    ('Pianto',                       5, 'Scoppia in lacrime',             1),
    ('Falo'' di confronto anticipato', 15, 'Chiede il falo'' in anticipo', 0),
    ('Lite furiosa',                  8, 'Litiga pesantemente',           1),
    ('Tradimento',                   12, 'Tradimento conclamato',         0),
    ('Abbandona il programma',      -10, 'Lascia Temptation Island',      0)
) AS v(nome, punti, descrizione, ripetibile)
WHERE NOT EXISTS (SELECT 1 FROM eventi);

INSERT INTO puntate (numero, aperta)
SELECT 1, 1
WHERE NOT EXISTS (SELECT 1 FROM puntate);
