import sqlite3

conn = sqlite3.connect("gioco.db")

# 🔥 ATTIVA FOREIGN KEY (IMPORTANTE)
conn.execute("PRAGMA foreign_keys = ON")

cursor = conn.cursor()

# 👤 UTENTI  (password IN CHIARO, richiesto per la dashboard admin)
cursor.execute("""
CREATE TABLE IF NOT EXISTS utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 💑 COPPIE  (6 coppie totali; possono essere eliminate dal gioco)
cursor.execute("""
CREATE TABLE IF NOT EXISTS coppie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    eliminata INTEGER DEFAULT 0,
    attiva INTEGER DEFAULT 1
)
""")

# 🏆 SQUADRE  (una squadra per utente)
cursor.execute("""
CREATE TABLE IF NOT EXISTS squadre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    nome_squadra TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utenti(id)
)
""")

# 🔗 ROSA: SQUADRA - COPPIE  (4 coppie scelte da ogni utente)
cursor.execute("""
CREATE TABLE IF NOT EXISTS squadra_coppie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squadra_id INTEGER NOT NULL,
    coppia_id INTEGER NOT NULL,
    UNIQUE (squadra_id, coppia_id),
    FOREIGN KEY (squadra_id) REFERENCES squadre(id),
    FOREIGN KEY (coppia_id) REFERENCES coppie(id)
)
""")

# 📺 PUNTATE  (gli episodi; l'admin ne tiene aperta una alla volta)
cursor.execute("""
CREATE TABLE IF NOT EXISTS puntate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL UNIQUE,
    aperta INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 🎯 SCHIERAMENTI  (le 2 coppie titolari che l'utente schiera in una puntata)
cursor.execute("""
CREATE TABLE IF NOT EXISTS schieramenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squadra_id INTEGER NOT NULL,
    puntata_id INTEGER NOT NULL,
    coppia_id INTEGER NOT NULL,
    UNIQUE (squadra_id, puntata_id, coppia_id),
    FOREIGN KEY (squadra_id) REFERENCES squadre(id),
    FOREIGN KEY (puntata_id) REFERENCES puntate(id),
    FOREIGN KEY (coppia_id) REFERENCES coppie(id)
)
""")

# ⚡ EVENTI  (ripetibile = 1 -> può capitare più volte nella stessa puntata)
cursor.execute("""
CREATE TABLE IF NOT EXISTS eventi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    punti INTEGER NOT NULL,
    descrizione TEXT,
    ripetibile INTEGER DEFAULT 0
)
""")

# 📊 EVENTI SU COPPIE  (un evento assegnato a una coppia IN una puntata)
cursor.execute("""
CREATE TABLE IF NOT EXISTS eventi_coppie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coppia_id INTEGER NOT NULL,
    evento_id INTEGER NOT NULL,
    puntata_id INTEGER NOT NULL,
    quantita INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coppia_id) REFERENCES coppie(id),
    FOREIGN KEY (evento_id) REFERENCES eventi(id),
    FOREIGN KEY (puntata_id) REFERENCES puntate(id)
)
""")

# 🏅 LEGHE  (create dagli utenti, si entra con un codice invito)
cursor.execute("""
CREATE TABLE IF NOT EXISTS leghe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    codice TEXT NOT NULL UNIQUE,
    creatore_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creatore_id) REFERENCES utenti(id)
)
""")

# 👥 MEMBRI DI UNA LEGA
cursor.execute("""
CREATE TABLE IF NOT EXISTS lega_membri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lega_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    UNIQUE (lega_id, user_id),
    FOREIGN KEY (lega_id) REFERENCES leghe(id),
    FOREIGN KEY (user_id) REFERENCES utenti(id)
)
""")

# ⚙️ IMPOSTAZIONI  (chiave/valore: deadline rosa, fascia blocco formazione, ...)
cursor.execute("""
CREATE TABLE IF NOT EXISTS impostazioni (
    chiave TEXT PRIMARY KEY,
    valore TEXT
)
""")

# =========================================================
# 🌱 SEED: admin + 6 coppie + eventi + prima puntata
# =========================================================

cursor.execute("SELECT COUNT(*) FROM utenti WHERE is_admin = 1")
if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO utenti (username, password, is_admin) VALUES (?, ?, 1)",
        ("admin", "admin123"),
    )

cursor.execute("SELECT COUNT(*) FROM coppie")
if cursor.fetchone()[0] == 0:
    coppie_demo = [
        ("Marco & Sara",),
        ("Luca & Giulia",),
        ("Alessandro & Federica",),
        ("Davide & Martina",),
        ("Simone & Chiara",),
        ("Andrea & Valentina",),
    ]
    cursor.executemany("INSERT INTO coppie (nome) VALUES (?)", coppie_demo)

cursor.execute("SELECT COUNT(*) FROM eventi")
if cursor.fetchone()[0] == 0:
    # (nome, punti, descrizione, ripetibile)
    eventi_demo = [
        ("Bacio con un tentatore", 10, "Bacio con un single/tentatore", 1),
        ("Pianto", 5, "Scoppia in lacrime", 1),
        ("Falò di confronto anticipato", 15, "Chiede il falò in anticipo", 0),
        ("Lite furiosa", 8, "Litiga pesantemente", 1),
        ("Tradimento", 12, "Tradimento conclamato", 0),
        ("Abbandona il programma", -10, "Lascia Temptation Island", 0),
    ]
    cursor.executemany(
        "INSERT INTO eventi (nome, punti, descrizione, ripetibile) VALUES (?, ?, ?, ?)", eventi_demo
    )

cursor.execute("SELECT COUNT(*) FROM puntate")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO puntate (numero, aperta) VALUES (1, 1)")

conn.commit()
conn.close()

print("Database creato con successo!")
print("Admin di default -> username: admin | password: admin123  (CAMBIALA!)")
