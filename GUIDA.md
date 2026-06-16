# 📖 GUIDA COMPLETA — Fanta Temptation Island

Questa guida spiega **tutto** il progetto partendo da zero: a cosa serve ogni file e
cosa fa il codice, riga per riga. È scritta per chi **non ha mai programmato**.
Leggila con calma, dall'alto verso il basso.

---

## PARTE 1 — I concetti di base (leggi prima questa parte)

### Cos'è questo progetto?
È un gioco tipo "Fantacalcio" ma su *Temptation Island*: gli utenti creano una squadra
di **coppie**, le schierano puntata per puntata, e guadagnano punti in base a quello che
succede in TV (baci, liti, falò...). C'è una classifica e si possono creare leghe tra amici.

### I 4 "mattoni" che compongono il progetto

1. **Python** — il linguaggio di programmazione in cui è scritto il codice. Un file `.py`
   è un file di testo con dentro istruzioni che il computer esegue **dall'alto verso il basso**.

2. **Streamlit** — una libreria (un "pacchetto già pronto") che trasforma il codice Python
   in un **sito web** senza dover sapere HTML. Ogni volta che scrivi `st.qualcosa(...)`
   stai dicendo a Streamlit "metti questa cosa sulla pagina" (un titolo, un bottone, una scritta...).

3. **Supabase** — il **database cloud**, cioè il magazzino dove vengono salvati i dati
   (utenti, squadre, punti...). Funziona su internet: i dati non stanno più in un file
   sul tuo PC, ma su un server di Supabase accessibile da qualsiasi computer.
   Usa **PostgreSQL**, un database professionale e gratuito (nella versione base).

4. **SQL** — il "linguaggio" con cui si parla al database. Sono frasi in inglese tipo
   `SELECT ... FROM ...` (= "prendimi questi dati") o `INSERT INTO ...` (= "aggiungi questo dato").

### Come "gira" l'app (il ciclo di Streamlit) — concetto FONDAMENTALE
Streamlit funziona in modo particolare: **ogni volta che fai qualcosa** (clicchi un bottone,
scrivi in un campo, cambi pagina) Streamlit **riesegue tutto il file `app.py` dall'inizio alla fine**.
Non "ricorda" cosa c'era prima, se non per le cose salvate apposta (vedi `session_state` più sotto).
Quindi non spaventarti se vedi che il codice sembra "rifarsi tutto ogni volta": è normale, è così che funziona.

### Glossario lampo
| Parola | Cosa significa, in parole semplici |
|---|---|
| **variabile** | un contenitore con un nome, es. `nome = "Marco"` mette il testo "Marco" nel contenitore `nome` |
| **funzione** | un blocco di istruzioni con un nome, che esegui quando ti serve. Si definisce con `def nome():` e si usa scrivendo `nome()` |
| **parametro** | un valore che "passi" a una funzione perché lo usi, es. `saluta("Marco")` |
| **lista** | un elenco di cose tra parentesi quadre, es. `["a", "b", "c"]` |
| **dizionario** | coppie "chiave: valore" tra parentesi graffe, es. `{"nome": "Marco", "eta": 30}` |
| **`if` / `else`** | "se... allora... altrimenti..." — esegue cose diverse a seconda di una condizione |
| **`for`** | "per ogni elemento di una lista, ripeti..." — un ciclo che si ripete |
| **`True` / `False`** | vero / falso |
| **`None`** | "niente / vuoto" |
| **tabella** (database) | come un foglio Excel: righe (i dati) e colonne (i campi) |
| **riga / record** | una voce nella tabella (es. un utente) |

---

## PARTE 2 — Mappa dei file

Nella cartella del progetto ci sono questi file e cartelle:

| File / Cartella | A cosa serve |
|---|---|
| **`app.py`** | È **l'app vera e propria**: il sito che vedi nel browser. È il file più importante. |
| **`schema.sql`** | Lo script SQL da incollare su Supabase **una volta sola** per creare le tabelle. |
| **`.streamlit/secrets.toml`** | Contiene la **password** per connettersi a Supabase. Non condividerlo mai. |
| **`database.py`** | ~~Vecchio file che creava il database SQLite locale.~~ **Non si usa più.** |
| **`view_users.py`** | ~~Vecchio script di debug per vedere gli utenti nel terminale.~~ **Non si usa più** — usa Supabase → Table Editor → utenti. |
| **`gioco.db`** | ~~Vecchio database SQLite locale.~~ **Non esiste più / puoi cancellarlo.** I dati sono ora su Supabase. |
| **`regolamento.txt`** | Il testo del regolamento, mostrato nella pagina "Regolamento". Puoi modificarlo liberamente. |
| **`images/`** | La cartella dove metti le **foto delle coppie**. |
| **`images/LEGGIMI.txt`** | Istruzioni su come nominare le foto. |
| **`venv/`** | La "cassetta degli attrezzi" di Python per questo progetto. Non toccarla. |
| **`GUIDA.md`** | Questo documento. |

> ⚠️ Il vecchio file `gioco.db` non esiste più. Tutti i dati sono ora su Supabase.

### In che ordine succede tutto
1. **Una volta sola**: incolli `schema.sql` nel SQL Editor di Supabase → nascono le tabelle con i dati di esempio.
2. **Una volta sola**: metti la tua password Supabase in `.streamlit/secrets.toml`.
3. **Ogni volta che vuoi giocare**: lanci `app.py` con Streamlit → si apre il sito nel browser.
4. L'app legge e scrive dentro **Supabase** (via internet).

---

## PARTE 3 — `schema.sql` e Supabase

Questo file **costruisce il magazzino** (il database) su Supabase e gli scaffali (le tabelle).
Lo incolli una volta nel **SQL Editor** di Supabase e premi **RUN**.

### Come aprire il SQL Editor
1. Vai su [supabase.com](https://supabase.com) e accedi al tuo progetto.
2. Nel menu a sinistra clicca **SQL Editor**.
3. Incolla tutto il contenuto di `schema.sql` e premi il tasto **RUN** (o `Ctrl+Enter`).

### Le tabelle create

| Tabella | A cosa serve | Colonne principali |
|---|---|---|
| **utenti** | chi gioca | username, password, is_admin |
| **coppie** | le coppie del programma | nome, `eliminata` (0/1), `attiva` (0/1) |
| **squadre** | la squadra di ogni utente | user_id (di chi è), nome_squadra |
| **squadra_coppie** | la **rosa**: quali coppie ha scelto una squadra | squadra_id, coppia_id |
| **puntate** | gli episodi | numero, `aperta` (0/1) |
| **schieramenti** | quali coppie un utente schiera **in una puntata** | squadra_id, puntata_id, coppia_id |
| **eventi** | le cose che fanno punti | nome, punti, `ripetibile` (0/1) |
| **eventi_coppie** | un evento capitato a una coppia in una puntata | coppia_id, evento_id, puntata_id, `quantita` |
| **leghe** | le leghe tra amici | nome, codice invito, creatore_id |
| **lega_membri** | chi fa parte di quale lega | lega_id, user_id |
| **impostazioni** | regolazioni (deadline mercato, orari di blocco) | chiave, valore |

### La differenza da SQLite (per curiosità)
Il vecchio database usava SQLite (un file locale `gioco.db`). Supabase usa **PostgreSQL**.
Le differenze principali che trovi nel codice:
- I parametri nelle query si scrivono `%s` invece di `?`
- `AUTOINCREMENT` diventa `SERIAL` (PostgreSQL genera i numeri automatici in modo diverso)
- `INSERT OR IGNORE` diventa `INSERT ... ON CONFLICT DO NOTHING`

### Come modificare i dati direttamente su Supabase
Se hai bisogno di rinominare una coppia, correggere un dato, o fare operazioni che
l'app non prevede, puoi usare il **Table Editor** di Supabase:
1. Nel menu a sinistra clicca **Table Editor**.
2. Scegli la tabella (es. `coppie`).
3. Clicca su una riga per modificarla, come un foglio Excel.

> 💡 Qualsiasi modifica fatta da Supabase è **immediata**: la vedi subito nell'app.
> Qualsiasi modifica fatta dall'app (aggiungere coppie, assegnare punti, cancellare...)
> va direttamente su Supabase. **C'è un solo database condiviso**.

---

## PARTE 4 — `app.py` spiegato a blocchi

Questo è il file dell'app. Ricorda il concetto chiave: **Streamlit riesegue tutto questo
file da capo ad ogni clic**. Lo dividiamo nei suoi blocchi.

### 4.1 — Import e configurazione (righe 1–27)
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import secrets
import unicodedata
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
```
Porta dentro gli strumenti che servono:
- `os` = per lavorare con file e cartelle del computer.
- `psycopg2` = il "cavo" che connette Python a PostgreSQL/Supabase. Sostituisce il vecchio `sqlite3`.
- `RealDictCursor` = un "cursore speciale" che ti permette di leggere i dati per nome di colonna
  (es. `riga["username"]`) invece che per numero.
- `secrets` = per generare codici casuali sicuri (i codici invito delle leghe).
- `unicodedata` = per "ripulire" i nomi (togliere accenti) quando si cercano le foto.
- `from datetime import datetime, timedelta` = per lavorare con date e orari.
- `import streamlit as st` = porta Streamlit e lo chiama `st`.
- `import streamlit.components.v1 as components` = per il countdown che scorre ogni secondo.

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
REGOLAMENTO_PATH = os.path.join(BASE_DIR, "regolamento.txt")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
```
- `BASE_DIR` = calcola **la cartella dove si trova `app.py`**, qualunque sia il PC.
- `IMAGES_DIR`, `REGOLAMENTO_PATH` = i percorsi della cartella foto e del regolamento.
- Nota: non c'è più `DB_PATH` — il database non è un file locale, è su Supabase.

```python
COPPIE_PER_SQUADRA = 5
TITOLARI_PER_PUNTATA = 3
DEADLINE_FMT = "%Y-%m-%d %H:%M"
LOCK_START_DEFAULT = 20
LOCK_END_DEFAULT = 12
```
Impostazioni del gioco (modificabili qui):
- ogni squadra ha **5** coppie, se ne schierano **3** a puntata;
- la formazione si blocca di default dalle **20** alle **12** del giorno dopo.

### 4.2 — Funzioni per le immagini (righe 29–57)
Identiche alla versione precedente. Vedi spiegazione originale: `slugify`, `find_image`, `mostra_foto`.

### 4.3 — Funzioni per parlare col database (righe 60–82) — IMPORTANTISSIME
Queste 3 funzioni vengono usate **in tutto il resto del file**. Sono cambiate rispetto
alla versione SQLite.

```python
def get_connection():
    conn = psycopg2.connect(st.secrets["SUPABASE_DB_URL"])
    return conn
```
`get_connection` apre la "cornetta" verso Supabase. `st.secrets["SUPABASE_DB_URL"]` legge
la stringa di connessione dal file `.streamlit/secrets.toml` — così la password non è
scritta nel codice ma in un file separato che non condividi.

```python
def query(sql, params=(), one=False):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()
    if one:
        return rows[0] if rows else None
    return rows
```
`query` serve a **leggere** dati (le frasi `SELECT`). Usa `RealDictCursor` per poter
accedere ai dati per nome di colonna. Funziona uguale alla versione SQLite.

```python
def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
```
`execute` serve a **modificare** dati (`INSERT`, `UPDATE`, `DELETE`). Esegue la frase
e **salva** (`commit`). `try ... finally` garantisce che la connessione venga sempre chiusa.

> 💡 Come prima: `query(...)` = **leggo** dal database, `execute(...)` = **scrivo** nel database.

### 4.4 — Impostazioni, deadline e blocchi orari (righe 85–197)

```python
def init_schema():
    execute("CREATE TABLE IF NOT EXISTS impostazioni (chiave TEXT PRIMARY KEY, valore TEXT)")
    execute("ALTER TABLE eventi ADD COLUMN IF NOT EXISTS ripetibile INTEGER DEFAULT 0")
    execute("ALTER TABLE eventi_coppie ADD COLUMN IF NOT EXISTS quantita INTEGER DEFAULT 1")

init_schema()
```
`init_schema` si esegue ad ogni avvio e aggiorna il database se mancano colonne aggiunte
in versioni successive. In PostgreSQL, `ADD COLUMN IF NOT EXISTS` non fa nulla se la
colonna esiste già — è sicuro eseguirlo sempre.

Il resto delle funzioni (`get_impostazione`, `set_impostazione`, `get_deadline_rosa`,
`rosa_bloccata`, `formazione_bloccata`, `prossimo_sblocco`, `countdown_html`) funzionano
**esattamente come prima** — la logica non è cambiata, solo i parametri SQL usano `%s`
invece di `?`.

### 4.5 — Funzioni del gioco (righe 200–430)
Sono le stesse funzioni di prima. Le uniche differenze sono tecniche:

| Cosa è cambiato | Prima (SQLite) | Ora (Supabase) |
|---|---|---|
| Parametri nelle query | `?` | `%s` |
| Funzioni che fanno più operazioni in una transazione | `conn.execute(...)` direttamente | `cur = conn.cursor()` poi `cur.execute(...)` |
| Errore username duplicato | `sqlite3.IntegrityError` | `Exception` (generico) |
| Entra in lega senza duplicati | `INSERT OR IGNORE` | `INSERT ... ON CONFLICT DO NOTHING` |
| `crea_lega` (recupero id lega appena creata) | `cur.lastrowid` | `query("SELECT id FROM leghe WHERE codice = %s", ...)` |

### 4.6 — La "memoria" tra un clic e l'altro (session_state)
Uguale a prima. `st.session_state.user` e `st.session_state.page` tengono traccia di
chi è loggato e su quale pagina si trova.

### 4.7 — Il menù laterale (sidebar)
Uguale a prima.

### 4.8 — Le pagine

**Pagine utente** (Home, Regolamento, La mia squadra, Classifica, Coppie, Eventi): logica invariata.

**Pagina Leghe** — miglioramenti recenti:
- Ogni lega mostra solo i **primi 3 classificati** (🥇🥈🥉) con le **foto delle coppie** della loro rosa.
- Se ci sono più di 3 partecipanti, appare il tasto **"Vedi tutta la classifica (N partecipanti)"**
  che espande un pannello con tutti gli altri (dal 4° in giù).

**Area Admin** — contiene ora 8 tab:

| Tab | Funzione |
|---|---|
| 💑 Coppie | Aggiungi, elimina, ripristina coppie |
| ⚡ Eventi | Aggiungi, modifica, cancella eventi |
| 📺 Puntate | Crea puntate, apri/chiudi, **cancella** (con tutti i punti assegnati) |
| ⏳ Mercato | Imposta deadline rosa e orari di blocco formazione |
| 🎯 Assegna punti | Per ogni coppia, **tutti gli eventi** mostrano un checkbox; gli eventi ripetibili mostrano anche un campo **quantità** (minimo 1 se spuntato) |
| ⚽ Squadre | Vedi **tutte le squadre** iscritte con filtro per nome/giocatore, foto delle coppie in rosa, punteggio e bottone **Cancella** |
| 🏅 Leghe | Gestisci le leghe (crea, cancella) |
| 🔑 Password | Cambia la password admin |

---

## PARTE 5 — Gli altri file

### `.streamlit/secrets.toml`
Contiene la stringa di connessione a Supabase:
```toml
SUPABASE_DB_URL = "postgresql://postgres.ydheyledhaoizngnukge:LA_TUA_PASSWORD@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"
```
- **Non condividere mai questo file** — contiene la password del database.
- Se pubblichi il progetto su GitHub, aggiungi `.streamlit/secrets.toml` al file `.gitignore`.
- La password la trovi su: **Supabase → Settings → Database → Database password**.

### `schema.sql`
Lo SQL da incollare nel SQL Editor di Supabase per creare le tabelle.
Va eseguito **una sola volta**. Se lo riesegui su un database già popolato, non fa danni
(tutte le istruzioni usano `IF NOT EXISTS` o controlli "inserisci solo se vuoto").

### `database.py`
Questo file non viene più usato. Creava il vecchio database SQLite locale (`gioco.db`).
Puoi ignorarlo.

### `regolamento.txt`
Testo libero del regolamento. Modificalo con un editor di testo.

### `images/`
La cartella delle foto delle coppie. Il nome del file deve essere il nome della coppia in
minuscolo, con `_` al posto di spazi e `&` (es. `marco_sara.jpg`). Le istruzioni dettagliate
sono in `images/LEGGIMI.txt`.

---

## PARTE 6 — Come si usa (riepilogo dei comandi)

Apri il terminale **nella cartella del progetto** e usa questi comandi:

**1. Prima configurazione (solo la prima volta):**
- Incolla `schema.sql` nel SQL Editor di Supabase e premi RUN.
- Apri `.streamlit/secrets.toml` e sostituisci `YOUR_PASSWORD_HERE` con la tua password Supabase.

**2. Avviare il sito:**
```powershell
.\venv\Scripts\streamlit run app.py
```
Si apre il browser. Per **fermarlo**: premi `Ctrl+C` nel terminale.

**Accesso amministratore:** username `admin`, password `admin123` (cambiala dall'Area Admin → Password).

### Come azzerare tutto e ripartire
Se vuoi cancellare tutti i dati e ripartire da zero:
1. Vai su **Supabase → SQL Editor**.
2. Esegui questo SQL (cancella tutto):
```sql
TRUNCATE TABLE eventi_coppie, schieramenti, squadra_coppie, lega_membri,
               leghe, squadre, puntate, eventi, coppie, utenti, impostazioni
RESTART IDENTITY CASCADE;
```
3. Poi riesegui il seed da `schema.sql` (solo la parte dal commento `-- SEED` in poi).

---

## PARTE 6b — Deploy su Streamlit Community Cloud (app online per tutti)

Questa sezione spiega come mettere l'app **su internet** in modo che i tuoi amici
possano giocare da qualsiasi browser, senza che tu debba tenere il PC acceso.
Il servizio si chiama **Streamlit Community Cloud** ed è **gratuito**.

### Prerequisiti
- Il codice è su **GitHub** (repo pubblico o privato). ✅
- Il database è su **Supabase**. ✅
- Il file `.streamlit/secrets.toml` **NON** è su GitHub (contiene la password).
  Se non l'hai già fatto, aggiungilo al file `.gitignore` nella cartella del progetto.

### Controllare che secrets.toml non sia su GitHub
Apri (o crea) il file `.gitignore` nella cartella del progetto e assicurati che contenga:
```
.streamlit/secrets.toml
gioco.db
```
Così Git non caricherà mai questi file su GitHub.

### Passi per il deploy

**1. Vai su Streamlit Cloud**
Apri [share.streamlit.io](https://share.streamlit.io) e accedi con il tuo account GitHub.

**2. Crea una nuova app**
Clicca **New app** (o **Create app**).

**3. Collega il repository**
- **Repository**: scegli il tuo repo GitHub del progetto.
- **Branch**: `main` (o il nome del tuo branch principale).
- **Main file path**: `app.py`

**4. Aggiungi il secret PRIMA di fare deploy**
Clicca su **Advanced settings** (o **Edit secrets**) e nella casella di testo incolla:
```toml
SUPABASE_DB_URL = "postgresql://postgres.ydheyledhaoizngnukge:FantaDatabase12!@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"
```
> ⚠️ Ignora i campi `DB_username` e `DB_token` che Streamlit potrebbe mostrare — sono
> opzionali e non ti servono. Incolla solo la riga qui sopra nella casella di testo libera.

**5. Fai il deploy**
Clicca **Deploy**. Streamlit installerà le dipendenze da `requirements.txt` e avvierà l'app.
Dopo qualche minuto ricevi un link tipo:
```
https://fanta-temptation-island.streamlit.app
```
Condividilo con i tuoi amici e possono giocare da subito.

### Aggiornare l'app dopo una modifica al codice
Ogni volta che fai un `git push` sul repo GitHub, Streamlit Cloud si aggiorna
**automaticamente** — non devi fare nulla.

### Se devi cambiare la password Supabase
1. Vai su **share.streamlit.io** → la tua app → **⋮ (menu)** → **Settings → Secrets**.
2. Aggiorna la riga `SUPABASE_DB_URL` con la nuova password.
3. L'app si riavvia da sola.

---

## PARTE 7 — Domande frequenti

- **Perché ad ogni clic "succede tutto da capo"?** È il funzionamento normale di Streamlit:
  riesegue `app.py` ogni volta. Le cose da ricordare stanno in `st.session_state`.
- **Dove sono salvati i dati?** Su **Supabase** (nel cloud). Non c'è più il file `gioco.db`.
  Se vuoi vedere o modificare i dati a mano, usa il **Table Editor** di Supabase.
- **Se cancello una coppia dall'app, sparisce anche su Supabase?** Sì. L'app e Supabase
  sono la stessa cosa: l'app scrive su Supabase, Supabase è il database dell'app.
- **Cosa sono i `%s` nelle frasi SQL?** Segnaposto riempiti dai valori che passi: si usano
  per sicurezza, non scrivere mai i valori direttamente dentro la frase SQL.
  (Nel vecchio codice SQLite erano `?`, in PostgreSQL si usano `%s`.)
- **Le coppie/eventi dove si gestiscono?** Tutto dall'**Area Admin**, senza toccare Supabase
  a mano. Ma se hai bisogno di rinominare una coppia, per ora devi farlo dal Table Editor
  di Supabase (l'app non ha ancora il tasto "Rinomina").
- **Sono admin perché è il mio PC?** No: sei admin perché conosci le credenziali dell'account
  `admin`, che è dentro il database Supabase. Da qualsiasi PC, chi entra come `admin` è amministratore.
- **Il file `.streamlit/secrets.toml` va su GitHub?** **No.** Contiene la password del database.
  Aggiungilo a `.gitignore` se usi Git.

---

## PARTE 8 — 🔗 Diagramma: come si collegano le tabelle

Le tabelle non sono isolate: sono **collegate** tra loro tramite gli `id`. Per esempio, una
squadra "sa" di chi è perché tiene il `user_id` del suo proprietario. Capire questi collegamenti
è la chiave per capire tutto il gioco.

### Due concetti da sapere prima
- **Collegamento "uno a molti"**: un utente ha **una** squadra, ma una lega ha **molti** membri.
  Nel disegno lo indico con `──<` (il lato con la "forchetta" `<` è il "molti").
- **Tabella ponte** (o "tabella di mezzo"): quando due cose stanno in relazione "molti a molti"
  — es. una squadra ha molte coppie **e** una coppia può stare in molte squadre — serve una
  tabella in mezzo che tiene le coppie di id. Qui le tabelle ponte sono **4**:
  `squadra_coppie`, `schieramenti`, `eventi_coppie`, `lega_membri`.

### Legenda
```
[TABELLA]        = una tabella (un "foglio Excel")
A ──1:1── B      = a ogni A corrisponde esattamente un B (e viceversa)
A ──< B          = un A è collegato a TANTI B  (B contiene l'id di A)
( ponte )        = tabella di mezzo che collega due tabelle "molti a molti"
```

### Schema in testo semplice (si legge ovunque)
```
[utenti]   (chi gioca: username, password, is_admin)
   |
   |--1:1--> [squadre]   (la squadra dell'utente)
   |             |
   |             |--<  (ponte) [squadra_coppie]  >--  [coppie]      ◄ ROSA: le 5 coppie scelte
   |             |
   |             '--<  (ponte) [schieramenti]    >--  [puntate]     ◄ TITOLARI: 3 per puntata
   |                                             '--  [coppie]
   |
   |--<  [leghe]   (le leghe che l'utente ha creato)
   |
   '--<  (ponte) [lega_membri]  >--  [leghe]                        ◄ a quali leghe è iscritto


[coppie]  --<  (ponte) [eventi_coppie]  >--  [eventi]               ◄ PUNTI: quale evento...
                              '----------     [puntate]               ...a quale coppia, in quale
                                                                       puntata, e quante volte (quantita)


[impostazioni]   = tabella a sé, non collegata (deadline mercato, orari di blocco)
```

### Lo stesso diagramma in versione grafica (Mermaid)
> Questo si vede come disegno se apri il file su GitHub o con l'estensione VS Code
> "Markdown Preview Mermaid Support". Altrimenti leggi lo schema in testo qui sopra.

```mermaid
erDiagram
    utenti       ||--o| squadre        : "ha (1 sola)"
    utenti       ||--o{ leghe          : "crea"
    utenti       ||--o{ lega_membri    : "iscritto"
    leghe        ||--o{ lega_membri    : "ha membri"
    squadre      ||--o{ squadra_coppie : "rosa (5 coppie)"
    coppie       ||--o{ squadra_coppie : ""
    squadre      ||--o{ schieramenti   : "schiera (3 a puntata)"
    puntate      ||--o{ schieramenti   : ""
    coppie       ||--o{ schieramenti   : ""
    coppie       ||--o{ eventi_coppie  : ""
    eventi       ||--o{ eventi_coppie  : ""
    puntate      ||--o{ eventi_coppie  : ""
```

### I collegamenti spiegati a parole
1. **utenti → squadre** (uno a uno): ogni utente ha **una** squadra. La tabella `squadre`
   contiene `user_id`, cioè l'id del proprietario.
2. **squadre + coppie → squadra_coppie** (la ROSA): la tabella ponte `squadra_coppie` dice
   "questa squadra ha scelto queste 5 coppie". Tiene `squadra_id` + `coppia_id`.
3. **squadre + puntate + coppie → schieramenti** (i TITOLARI): per ogni puntata, la tabella
   ponte `schieramenti` dice "questa squadra, in questa puntata, schiera queste 3 coppie".
4. **coppie + eventi + puntate → eventi_coppie** (i PUNTI): quando l'admin assegna un evento,
   nasce una riga qui che dice "a questa coppia, in questa puntata, è successo questo evento,
   `quantita` volte". È da qui che arrivano i punti.
5. **utenti + leghe → lega_membri**: chi fa parte di quale lega. `leghe` contiene anche
   `creatore_id` (chi l'ha creata).
6. **impostazioni**: sta per conto suo, non è collegata a nessuna. Contiene solo regolazioni
   (deadline del mercato, orari di blocco).

### Come il diagramma diventa il punteggio
Mettendo insieme i collegamenti 3 e 4 si ottiene la regola dei punti:
> prendo le coppie che la squadra ha **schierato** in una puntata (`schieramenti`), guardo
> quali **eventi** hanno fatto **in quella stessa puntata** (`eventi_coppie`), sommo i punti
> (× quantità). Una coppia non schierata in quella puntata semplicemente non compare nel
> collegamento, quindi non porta punti.

---

## PARTE 9 — Come tornare a SQLite (database locale)

Se un giorno vuoi abbandonare Supabase e tornare al database locale `gioco.db`,
devi modificare **5 punti** in `app.py` e ricreare il file `gioco.db` con `database.py`.

---

### 9.1 — Import: sostituisci psycopg2 con sqlite3

**Rimuovi** queste due righe in cima al file:
```python
import psycopg2
from psycopg2.extras import RealDictCursor
```
**Aggiungi** al loro posto:
```python
import sqlite3
```

---

### 9.2 — CONFIG: ripristina il percorso del database

**Aggiungi** questa riga subito dopo `BASE_DIR = ...`:
```python
DB_PATH = os.path.join(BASE_DIR, "gioco.db")
```

---

### 9.3 — Le 3 funzioni DB: ripristina la versione SQLite

Sostituisci le funzioni `get_connection`, `query`, `execute` con queste:

```python
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def query(sql, params=(), one=False):
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows

def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
```

---

### 9.4 — init_schema: ripristina i controlli con PRAGMA

Sostituisci `init_schema` con questa versione:

```python
def init_schema():
    execute("CREATE TABLE IF NOT EXISTS impostazioni (chiave TEXT PRIMARY KEY, valore TEXT)")
    cols_eventi = [r["name"] for r in query("PRAGMA table_info(eventi)")]
    if cols_eventi and "ripetibile" not in cols_eventi:
        execute("ALTER TABLE eventi ADD COLUMN ripetibile INTEGER DEFAULT 0")
    cols_ec = [r["name"] for r in query("PRAGMA table_info(eventi_coppie)")]
    if cols_ec and "quantita" not in cols_ec:
        execute("ALTER TABLE eventi_coppie ADD COLUMN quantita INTEGER DEFAULT 1")
```

---

### 9.5 — Sostituisci tutti i `%s` con `?` nelle query SQL

In SQLite i parametri si scrivono `?`, in PostgreSQL `%s`.
Fai un **trova e sostituisci** su tutto `app.py`:
- Cerca: `%s`
- Sostituisci con: `?`

Attenzione: sostituisci solo dentro le stringhe SQL, non altrove
(ma in pratica `%s` appare solo lì, quindi puoi farlo su tutto il file).

---

### 9.6 — Altre differenze da ripristinare

| Punto nel codice | Versione PostgreSQL (attuale) | Versione SQLite (da ripristinare) |
|---|---|---|
| `set_impostazione` | `ON CONFLICT (chiave) DO UPDATE SET valore = EXCLUDED.valore` | `ON CONFLICT(chiave) DO UPDATE SET valore = excluded.valore` |
| `entra_in_lega` | `INSERT INTO lega_membri ... ON CONFLICT DO NOTHING` | `INSERT OR IGNORE INTO lega_membri ...` |
| `set_rosa`, `set_schieramento`, `elimina_*`, form assegna punti | `cur = conn.cursor()` poi `cur.execute(...)` | `conn.execute(...)` direttamente (senza cursor) |
| `crea_lega` | recupera l'id con `query("SELECT id FROM leghe WHERE codice = %s", ...)` | usa il valore restituito da `execute(...)` direttamente (`lega_id = execute(...)`) |
| Errore registrazione utente duplicato | `except Exception:` | `except sqlite3.IntegrityError:` |
| Errore puntata duplicata | `except Exception:` | `except sqlite3.IntegrityError:` |

---

### 9.7 — Ricrea il database locale

Una volta modificato `app.py`, lancia `database.py` per creare il file `gioco.db`:
```powershell
.\venv\Scripts\python.exe database.py
```
Poi avvia l'app normalmente:
```powershell
.\venv\Scripts\streamlit run app.py
```

---

---

## PARTE 10 — Registro modifiche (changelog)

Qui trovi le modifiche fatte al progetto nel tempo, dalla più recente alla più vecchia.

### Giugno 2026 — Aggiornamento funzionalità

| # | Cosa è cambiato | Dove si vede |
|---|---|---|
| 1 | **Titolari da 2 a 3** — ogni squadra ora schiera 3 coppie per puntata (era 2) | Pagina "La mia squadra" → Schiera i titolari |
| 2 | **Tab Admin "⚽ Squadre"** — nuova sezione che mostra tutte le squadre iscritte con foto delle coppie, punteggio e bottone Cancella; include filtro per nome squadra o giocatore | Area Admin → tab Squadre |
| 3 | **Cancella puntata** — bottone per eliminare una puntata e **tutti i punti assegnati** a quella puntata (irreversibile, protetto da conferma) | Area Admin → tab Puntate |
| 4 | **Assegna punti migliorato** — tutti gli eventi mostrano un checkbox (prima i ripetibili mostravano solo un numero); i ripetibili mostrano anche il campo quantità (min 1 se spuntato) | Area Admin → tab Assegna punti |
| 5 | **Leghe: top 3 + foto** — la classifica mostra solo i primi 3 con medaglie e foto delle coppie; tasto "Vedi tutta la classifica" espande il resto | Pagina Leghe |

### Giugno 2026 — Migrazione a Supabase + deploy online

| # | Cosa è cambiato | Note |
|---|---|---|
| 1 | Database migrato da SQLite locale a **Supabase (PostgreSQL)** | Dati sul cloud, accessibili da ovunque |
| 2 | `app.py` riscritto con `psycopg2` al posto di `sqlite3` | Parametri SQL: `%s` invece di `?` |
| 3 | Aggiunto `schema.sql` — script per creare le tabelle su Supabase | Va eseguito una sola volta nel SQL Editor |
| 4 | Aggiunto `.streamlit/secrets.toml` — contiene la stringa di connessione | Non va su GitHub |
| 5 | Deploy su **Streamlit Community Cloud** — app accessibile via link pubblico | Vedi Parte 6b |
| 6 | `database.py` e `view_users.py` diventati **obsoleti** | Non servono più con Supabase |

---

Buona lettura! Se qualcosa non è chiaro, indicami il punto e te lo rispiego ancora più semplice.
