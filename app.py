import os
import psycopg2
from psycopg2.extras import RealDictCursor
import secrets
import unicodedata
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
REGOLAMENTO_PATH = os.path.join(BASE_DIR, "regolamento.txt")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

COPPIE_PER_SQUADRA = 5      # rosa: quante coppie sceglie ogni utente
TITOLARI_PER_PUNTATA = 3    # quante coppie si schierano ad ogni puntata

DEADLINE_FMT = "%Y-%m-%d %H:%M"
LOCK_START_DEFAULT = 20     # ora di inizio blocco formazione (diretta)
LOCK_END_DEFAULT = 12       # ora del giorno dopo in cui si sblocca

st.set_page_config(page_title="Fanta Temptation Island", page_icon="🔥")


# =========================
# IMMAGINI
# =========================
def slugify(nome):
    """'Marco & Sara' -> 'marco_sara' (nome del file foto)."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii").lower()
    s = "".join(c if c.isalnum() else "_" for c in s)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def nome_file_atteso(nome):
    return slugify(nome)


def find_image(nome):
    base = os.path.join(IMAGES_DIR, slugify(nome))
    for ext in IMAGE_EXTS:
        path = base + ext
        if os.path.exists(path):
            return path
    return None


def mostra_foto(nome, width=90):
    img = find_image(nome)
    if img:
        st.image(img, width=width)
    else:
        st.markdown("### 💑")


# =========================
# DB HELPERS
# =========================
def get_connection():
    return psycopg2.connect(st.secrets["SUPABASE_DB_URL"])


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


def execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# =========================
# IMPOSTAZIONI / DEADLINE / BLOCCHI
# =========================
def init_schema():
    """Crea/aggiorna le strutture aggiunte dopo il primo rilascio (su DB già esistenti)."""
    execute("CREATE TABLE IF NOT EXISTS impostazioni (chiave TEXT PRIMARY KEY, valore TEXT)")
    execute("ALTER TABLE eventi ADD COLUMN IF NOT EXISTS ripetibile INTEGER DEFAULT 0")
    execute("ALTER TABLE eventi_coppie ADD COLUMN IF NOT EXISTS quantita INTEGER DEFAULT 1")


@st.cache_resource
def _init_schema_once():
    try:
        init_schema()
    except Exception:
        pass

_init_schema_once()


def get_impostazione(chiave, default=None):
    row = query("SELECT valore FROM impostazioni WHERE chiave = %s", (chiave,), one=True)
    return row["valore"] if row else default


def set_impostazione(chiave, valore):
    execute(
        "INSERT INTO impostazioni (chiave, valore) VALUES (%s, %s) "
        "ON CONFLICT (chiave) DO UPDATE SET valore = EXCLUDED.valore",
        (chiave, str(valore)),
    )


def get_deadline_rosa():
    s = get_impostazione("deadline_rosa")
    if not s:
        return None
    try:
        return datetime.strptime(s, DEADLINE_FMT)
    except ValueError:
        return None


def rosa_bloccata():
    """Ritorna (bloccata, deadline|None). Bloccata = deadline impostata e già passata."""
    dl = get_deadline_rosa()
    if dl is None:
        return False, None
    return datetime.now() >= dl, dl


def get_lock_hours():
    start = int(get_impostazione("lock_start", LOCK_START_DEFAULT))
    end = int(get_impostazione("lock_end", LOCK_END_DEFAULT))
    return start, end


def formazione_bloccata():
    """True se ora siamo nella fascia 'diretta' in cui la formazione è congelata."""
    start, end = get_lock_hours()
    if start == end:
        return False
    ora = datetime.now().hour
    if start > end:          # finestra che attraversa la mezzanotte, es. 20 -> 12
        return ora >= start or ora < end
    return start <= ora < end  # finestra nello stesso giorno


def prossimo_sblocco():
    """Prossimo momento in cui la formazione si sblocca (ora = end)."""
    _, end = get_lock_hours()
    now = datetime.now()
    unlock = now.replace(hour=end % 24, minute=0, second=0, microsecond=0)
    if now >= unlock:
        unlock += timedelta(days=1)
    return unlock


def countdown_html(target_dt, label="⏳ Tempo rimasto:", bg="#1f2937"):
    """Countdown live lato browser; allo scadere ricarica la pagina una sola volta."""
    target = target_dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"""
    <div id="cd" style="font-family:sans-serif;font-size:1.05rem;font-weight:600;
         padding:10px;border-radius:8px;background:{bg};color:#fff;text-align:center;"></div>
    <script>
    const target = new Date("{target}").getTime();
    let reloaded = false;
    function tick() {{
        const el = document.getElementById("cd");
        const diff = target - new Date().getTime();
        if (diff <= 0) {{
            el.innerHTML = "⏰ Aggiorno...";
            if (!reloaded) {{
                reloaded = true;
                setTimeout(function() {{ try {{ window.parent.location.reload(); }} catch (e) {{}} }}, 1500);
            }}
            return;
        }}
        const g = Math.floor(diff / 86400000);
        const h = Math.floor((diff % 86400000) / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        let txt = "{label} ";
        if (g > 0) txt += g + "g ";
        el.innerHTML = txt + h + "h " + m + "m " + s + "s";
    }}
    tick();
    setInterval(tick, 1000);
    </script>
    """


# =========================
# AUTENTICAZIONE
# =========================
def register_user(username, password):
    execute("INSERT INTO utenti (username, password) VALUES (%s, %s)", (username, password))


def login_user(username, password):
    return query(
        "SELECT * FROM utenti WHERE username = %s AND password = %s",
        (username, password),
        one=True,
    )


# =========================
# COPPIE
# =========================
def get_coppie(solo_attive=True, solo_non_eliminate=False):
    sql = "SELECT * FROM coppie WHERE 1=1"
    if solo_attive:
        sql += " AND attiva = 1"
    if solo_non_eliminate:
        sql += " AND eliminata = 0"
    sql += " ORDER BY nome"
    return query(sql)


def punti_coppia_totali(coppia_id):
    """Punti totali della coppia (tutti gli eventi, a prescindere da chi l'ha schierata)."""
    row = query(
        """
        SELECT COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
        FROM eventi_coppie ec
        JOIN eventi e ON e.id = ec.evento_id
        WHERE ec.coppia_id = %s
        """,
        (coppia_id,),
        one=True,
    )
    return row["punti"]


# =========================
# SQUADRE / ROSA
# =========================
def get_squadra_by_user(user_id):
    return query("SELECT * FROM squadre WHERE user_id = %s", (user_id,), one=True)


def create_squadra(user_id, nome):
    execute("INSERT INTO squadre (user_id, nome_squadra) VALUES (%s, %s)", (user_id, nome))


def get_rosa(squadra_id):
    return query(
        """
        SELECT c.* FROM squadra_coppie sc
        JOIN coppie c ON c.id = sc.coppia_id
        WHERE sc.squadra_id = %s
        ORDER BY c.nome
        """,
        (squadra_id,),
    )


def set_rosa(squadra_id, coppia_ids):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM squadra_coppie WHERE squadra_id = %s", (squadra_id,))
        cur.executemany(
            "INSERT INTO squadra_coppie (squadra_id, coppia_id) VALUES (%s, %s)",
            [(squadra_id, cid) for cid in coppia_ids],
        )
        conn.commit()
    finally:
        conn.close()


# =========================
# PUNTATE / SCHIERAMENTI
# =========================
def get_puntate():
    return query("SELECT * FROM puntate ORDER BY numero DESC")


def get_puntata_aperta():
    return query("SELECT * FROM puntate WHERE aperta = 1 ORDER BY numero DESC", one=True)


def get_schieramento(squadra_id, puntata_id):
    return query(
        """
        SELECT c.* FROM schieramenti s
        JOIN coppie c ON c.id = s.coppia_id
        WHERE s.squadra_id = %s AND s.puntata_id = %s
        ORDER BY c.nome
        """,
        (squadra_id, puntata_id),
    )


def set_schieramento(squadra_id, puntata_id, coppia_ids):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM schieramenti WHERE squadra_id = %s AND puntata_id = %s",
            (squadra_id, puntata_id),
        )
        cur.executemany(
            "INSERT INTO schieramenti (squadra_id, puntata_id, coppia_id) VALUES (%s, %s, %s)",
            [(squadra_id, puntata_id, cid) for cid in coppia_ids],
        )
        conn.commit()
    finally:
        conn.close()


# =========================
# EVENTI / PUNTEGGI
# =========================
def get_eventi():
    return query("SELECT * FROM eventi ORDER BY punti DESC")


def punteggio_squadra(squadra_id):
    """Somma i punti delle coppie SOLO nelle puntate in cui sono state schierate."""
    row = query(
        """
        SELECT COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
        FROM schieramenti s
        JOIN eventi_coppie ec ON ec.coppia_id = s.coppia_id AND ec.puntata_id = s.puntata_id
        JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = %s
        """,
        (squadra_id,),
        one=True,
    )
    return row["punti"]


def dettaglio_punteggio(squadra_id):
    """Per ogni puntata, i punti di ciascuna coppia schierata (0 se non ha eventi)."""
    return query(
        """
        SELECT p.numero AS puntata, c.nome AS coppia,
               COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
        FROM schieramenti s
        JOIN puntate p ON p.id = s.puntata_id
        JOIN coppie c ON c.id = s.coppia_id
        LEFT JOIN eventi_coppie ec ON ec.coppia_id = s.coppia_id AND ec.puntata_id = s.puntata_id
        LEFT JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = %s
        GROUP BY s.puntata_id, s.coppia_id, p.numero, c.nome
        ORDER BY p.numero, c.nome
        """,
        (squadra_id,),
    )


PUNTI_SUBQUERY = """
    COALESCE((
        SELECT SUM(e.punti * COALESCE(ec.quantita, 1))
        FROM schieramenti s
        JOIN eventi_coppie ec ON ec.coppia_id = s.coppia_id AND ec.puntata_id = s.puntata_id
        JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = sq.id
    ), 0) AS punti
"""


def classifica_generale():
    return query(
        f"""
        SELECT u.username, sq.id AS squadra_id, sq.nome_squadra, {PUNTI_SUBQUERY}
        FROM squadre sq
        JOIN utenti u ON u.id = sq.user_id
        ORDER BY punti DESC, sq.nome_squadra
        """
    )


def classifica_lega(lega_id):
    return query(
        f"""
        SELECT u.username, sq.id AS squadra_id, sq.nome_squadra, {PUNTI_SUBQUERY}
        FROM lega_membri lm
        JOIN utenti u ON u.id = lm.user_id
        JOIN squadre sq ON sq.user_id = u.id
        WHERE lm.lega_id = %s
        ORDER BY punti DESC, sq.nome_squadra
        """,
        (lega_id,),
    )


# =========================
# LEGHE
# =========================
def genera_codice():
    return secrets.token_hex(3).upper()  # es. "9F2A7C"


def crea_lega(nome, creatore_id):
    codice = genera_codice()
    execute(
        "INSERT INTO leghe (nome, codice, creatore_id) VALUES (%s, %s, %s)",
        (nome, codice, creatore_id),
    )
    lega = query("SELECT id FROM leghe WHERE codice = %s", (codice,), one=True)
    execute("INSERT INTO lega_membri (lega_id, user_id) VALUES (%s, %s)", (lega["id"], creatore_id))
    return codice


def entra_in_lega(codice, user_id):
    lega = query("SELECT * FROM leghe WHERE codice = %s", (codice.strip().upper(),), one=True)
    if not lega:
        return None
    execute(
        "INSERT INTO lega_membri (lega_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (lega["id"], user_id),
    )
    return lega


def get_leghe_utente(user_id):
    return query(
        """
        SELECT l.* FROM lega_membri lm
        JOIN leghe l ON l.id = lm.lega_id
        WHERE lm.user_id = %s
        ORDER BY l.nome
        """,
        (user_id,),
    )


# =========================
# CANCELLAZIONI (admin)
# =========================
def elimina_coppia(coppia_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM eventi_coppie WHERE coppia_id = %s", (coppia_id,))
        cur.execute("DELETE FROM schieramenti WHERE coppia_id = %s", (coppia_id,))
        cur.execute("DELETE FROM squadra_coppie WHERE coppia_id = %s", (coppia_id,))
        cur.execute("DELETE FROM coppie WHERE id = %s", (coppia_id,))
        conn.commit()
    finally:
        conn.close()


def elimina_evento(evento_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM eventi_coppie WHERE evento_id = %s", (evento_id,))
        cur.execute("DELETE FROM eventi WHERE id = %s", (evento_id,))
        conn.commit()
    finally:
        conn.close()


def elimina_lega(lega_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM lega_membri WHERE lega_id = %s", (lega_id,))
        cur.execute("DELETE FROM leghe WHERE id = %s", (lega_id,))
        conn.commit()
    finally:
        conn.close()


def elimina_squadra(squadra_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM schieramenti WHERE squadra_id = %s", (squadra_id,))
        cur.execute("DELETE FROM squadra_coppie WHERE squadra_id = %s", (squadra_id,))
        cur.execute("DELETE FROM squadre WHERE id = %s", (squadra_id,))
        conn.commit()
    finally:
        conn.close()


def elimina_puntata(puntata_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM eventi_coppie WHERE puntata_id = %s", (puntata_id,))
        cur.execute("DELETE FROM schieramenti WHERE puntata_id = %s", (puntata_id,))
        cur.execute("DELETE FROM puntate WHERE id = %s", (puntata_id,))
        conn.commit()
    finally:
        conn.close()


# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "home"


def logout():
    st.session_state.user = None
    st.session_state.page = "home"


# =========================
# SIDEBAR
# =========================
st.sidebar.title("🔥 MENU")
user = st.session_state.user

if user:
    st.sidebar.success(f"Ciao, {user['username']}!")
    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "home"
    if st.sidebar.button("📜 Regolamento"):
        st.session_state.page = "rules"
    if st.sidebar.button("⚽ La mia squadra"):
        st.session_state.page = "my_team"
    if st.sidebar.button("🏆 Classifica"):
        st.session_state.page = "ranking"
    if st.sidebar.button("🏅 Leghe"):
        st.session_state.page = "leghe"
    if st.sidebar.button("💑 Coppie"):
        st.session_state.page = "coppie"
    if st.sidebar.button("⚡ Eventi"):
        st.session_state.page = "events"
    if user["is_admin"]:
        st.sidebar.divider()
        if st.sidebar.button("🔒 Area Admin"):
            st.session_state.page = "admin"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout"):
        logout()
        st.rerun()
else:
    st.sidebar.info("Effettua il login per giocare.")
    if st.sidebar.button("📜 Regolamento"):
        st.session_state.page = "rules"


# =========================
# PAGINA: HOME / LOGIN / REGISTRAZIONE
# =========================
if st.session_state.page == "home":
    st.title("🔥 Fanta Temptation Island")

    if user:
        st.write(f"Sei loggato come **{user['username']}**.")
        squadra = get_squadra_by_user(user["id"])
        if squadra:
            st.metric(f"🏆 {squadra['nome_squadra']}", f"{punteggio_squadra(squadra['id'])} punti")
        else:
            st.info("Non hai ancora una squadra. Vai su **⚽ La mia squadra** per crearla!")

        puntata = get_puntata_aperta()
        if puntata:
            st.success(f"📺 Puntata aperta: **Puntata {puntata['numero']}** — ricordati di schierare i titolari!")
        else:
            st.warning("Nessuna puntata aperta al momento.")
    else:
        choice = st.radio("Scegli azione:", ["Login", "Nuovo utente"], horizontal=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if choice == "Login":
            if st.button("Entra"):
                row = login_user(username.strip(), password)
                if row:
                    st.session_state.user = {"id": row["id"], "username": row["username"], "is_admin": row["is_admin"]}
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        else:
            if st.button("Registrati"):
                if not username.strip() or not password:
                    st.error("Username e password sono obbligatori.")
                else:
                    try:
                        register_user(username.strip(), password)
                        st.success("Utente creato! Ora effettua il login.")
                    except Exception:
                        st.error("Username già esistente, scegline un altro.")

        st.info("""
⚠️ Ti consigliamo di usare una password diversa da quelle che utilizzi altrove.

💡 Salvala da qualche parte: non è possibile recuperarla automaticamente.
Per assistenza, contatta Filippo Bisciglia o l'admin ma salva la password.
""")

# =========================
# PAGINA: REGOLAMENTO
# =========================
elif st.session_state.page == "rules":
    if os.path.exists(REGOLAMENTO_PATH):
        with open(REGOLAMENTO_PATH, encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.error("File regolamento.txt non trovato.")


# =========================
# PAGINA: LA MIA SQUADRA
# =========================
elif st.session_state.page == "my_team":
    if not user:
        st.warning("Devi effettuare il login.")
        st.stop()
    try:
        st.title("⚽ La mia squadra")
        squadra = get_squadra_by_user(user["id"])

        # --- Crea squadra ---
        if not squadra:
            st.info("Non hai ancora una squadra. Creala qui sotto.")
            nome = st.text_input("Nome della squadra")
            if st.button("Crea squadra"):
                if nome.strip():
                    create_squadra(user["id"], nome.strip())
                    st.success("Squadra creata!")
                    st.rerun()
                else:
                    st.error("Inserisci un nome.")
            st.stop()

        st.subheader(f"🏆 {squadra['nome_squadra']}")
        st.metric("Punteggio totale", f"{punteggio_squadra(squadra['id'])} punti")

        dett = dettaglio_punteggio(squadra["id"])
        if dett:
            with st.expander("📊 Come ho fatto i punti (dettaglio per puntata)"):
                st.caption("Contano solo i punti delle coppie nella puntata in cui le hai schierate.")
                puntata_corr = None
                for r in dett:
                    if r["puntata"] != puntata_corr:
                        puntata_corr = r["puntata"]
                        st.markdown(f"**📺 Puntata {puntata_corr}**")
                    st.write(f"• {r['coppia']}: **{r['punti']}** punti")
        else:
            st.caption("Non hai ancora schierato nessuna coppia: schiera i titolari per fare punti.")
        st.divider()

        # --- ROSA: scelta delle coppie ---
        st.subheader(f"💑 La tua rosa ({COPPIE_PER_SQUADRA} coppie)")
        tutte = get_coppie(solo_attive=True)
        nome_to_id = {c["nome"]: c["id"] for c in tutte}
        rosa_attuale = [c["nome"] for c in get_rosa(squadra["id"])]

        rosa_lock, deadline_rosa = rosa_bloccata()
        if deadline_rosa and not rosa_lock:
            components.html(countdown_html(deadline_rosa, "⏳ Chiusura mercato tra"), height=56)

        if rosa_lock:
            st.error(f"⛔ Mercato chiuso il {deadline_rosa.strftime('%d/%m/%Y %H:%M')}: la rosa non è più modificabile.")
        else:
            scelte = st.multiselect(
                f"Scegli {COPPIE_PER_SQUADRA} coppie",
                options=list(nome_to_id.keys()),
                default=[n for n in rosa_attuale if n in nome_to_id],
                max_selections=COPPIE_PER_SQUADRA,
            )
            if st.button("💾 Salva rosa"):
                if rosa_bloccata()[0]:
                    st.error("⛔ Mercato appena chiuso: rosa non più modificabile.")
                elif len(scelte) != COPPIE_PER_SQUADRA:
                    st.error(f"Devi scegliere esattamente {COPPIE_PER_SQUADRA} coppie.")
                else:
                    set_rosa(squadra["id"], [nome_to_id[n] for n in scelte])
                    st.success("Rosa salvata!")
                    st.rerun()

        # mostra rosa con foto
        rosa = get_rosa(squadra["id"])
        if rosa:
            cols = st.columns(len(rosa))
            for col, c in zip(cols, rosa):
                with col:
                    mostra_foto(c["nome"], width=90)
                    etichetta = "❌ eliminata" if c["eliminata"] else f"{punti_coppia_totali(c['id'])} pt"
                    st.caption(f"**{c['nome']}**\n\n{etichetta}")

        st.divider()

        # --- SCHIERAMENTO per la puntata aperta ---
        st.subheader("🎯 Schiera i titolari")
        puntata = get_puntata_aperta()

        if not puntata:
            st.warning("Nessuna puntata aperta: non puoi ancora schierare.")
        elif not rosa:
            st.info("Prima scegli la tua rosa di coppie qui sopra.")
        else:
            st.write(f"📺 **Puntata {puntata['numero']}** — schiera {TITOLARI_PER_PUNTATA} coppie (non eliminate).")
            schierabili = {c["nome"]: c["id"] for c in rosa if not c["eliminata"]}
            gia_schierati = [c["nome"] for c in get_schieramento(squadra["id"], puntata["id"]) if c["nome"] in schierabili]

            if formazione_bloccata():
                st.error("🔴 Formazione bloccata (fascia diretta): non puoi cambiare i titolari ora.")
                components.html(
                    countdown_html(prossimo_sblocco(), "🔓 Formazione modificabile di nuovo tra", "#7f1d1d"),
                    height=56,
                )
                if gia_schierati:
                    st.write("I tuoi titolari per questa puntata:")
                    for n in gia_schierati:
                        st.write(f"• {n}")
                else:
                    st.caption("Non avevi schierato titolari per questa puntata.")
            else:
                titolari = st.multiselect(
                    "Titolari di questa puntata",
                    options=list(schierabili.keys()),
                    default=gia_schierati,
                    max_selections=TITOLARI_PER_PUNTATA,
                )
                if st.button("✅ Conferma schieramento"):
                    if formazione_bloccata():
                        st.error("🔴 Formazione appena bloccata (fascia diretta): riprova più tardi.")
                    elif len(titolari) != TITOLARI_PER_PUNTATA:
                        st.error(f"Devi schierare esattamente {TITOLARI_PER_PUNTATA} coppie.")
                    else:
                        set_schieramento(squadra["id"], puntata["id"], [schierabili[n] for n in titolari])
                        st.success("Schieramento confermato!")
                        st.rerun()
    except Exception as e:
        st.error("⚠️ Errore di connessione al database. Riprova tra qualche secondo.")
        st.caption(f"Dettaglio: {e}")


# =========================
# PAGINA: CLASSIFICA GENERALE
# =========================
elif st.session_state.page == "ranking":
    st.title("🏆 Classifica generale")
    righe = classifica_generale()
    if not righe:
        st.info("Nessuna squadra ancora creata.")
    else:
        for i, r in enumerate(righe, start=1):
            medaglia = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            st.write(f"{medaglia} **{r['nome_squadra']}** (di {r['username']}) — **{r['punti']} punti**")


# =========================
# PAGINA: LEGHE
# =========================
elif st.session_state.page == "leghe":
    if not user:
        st.warning("Devi effettuare il login.")
        st.stop()

    st.title("🏅 Leghe")

    col_crea, col_entra = st.columns(2)
    with col_crea:
        st.subheader("➕ Crea una lega")
        nome_lega = st.text_input("Nome lega", key="nome_lega")
        if st.button("Crea lega"):
            if nome_lega.strip():
                codice = crea_lega(nome_lega.strip(), user["id"])
                st.success(f"Lega creata! Codice invito: **{codice}**")
            else:
                st.error("Inserisci un nome.")
    with col_entra:
        st.subheader("🔑 Entra con codice")
        codice_in = st.text_input("Codice invito", key="codice_in")
        if st.button("Entra nella lega"):
            lega = entra_in_lega(codice_in, user["id"])
            if lega:
                st.success(f"Sei entrato nella lega **{lega['nome']}**!")
                st.rerun()
            else:
                st.error("Codice non valido.")

    st.divider()
    st.subheader("📋 Le mie leghe")
    leghe = get_leghe_utente(user["id"])
    if not leghe:
        st.info("Non fai ancora parte di nessuna lega.")
    for l in leghe:
        st.markdown(f"### 🏅 {l['nome']}")
        st.caption(f"Codice invito: `{l['codice']}`")
        righe = classifica_lega(l["id"])
        def _render_riga_lega(i, r):
            medaglia = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            rosa_r = get_rosa(r["squadra_id"])
            st.write(f"{medaglia} **{r['nome_squadra']}** (di {r['username']}) — **{r['punti']} pt**")
            if rosa_r:
                foto_cols = st.columns(len(rosa_r))
                for j, c_rosa in enumerate(rosa_r):
                    img = find_image(c_rosa["nome"])
                    if img:
                        foto_cols[j].image(img, width=55)
                    foto_cols[j].caption(c_rosa["nome"].split(" & ")[0])

        for i, r in enumerate(righe[:3], start=1):
            _render_riga_lega(i, r)

        if len(righe) > 3:
            with st.expander(f"Vedi tutta la classifica ({len(righe)} partecipanti)"):
                for i, r in enumerate(righe[3:], start=4):
                    _render_riga_lega(i, r)
        st.divider()


# =========================
# PAGINA: COPPIE
# =========================
elif st.session_state.page == "coppie":
    st.title("💑 Coppie")
    for c in get_coppie(solo_attive=True):
        col_img, col_txt = st.columns([1, 4])
        with col_img:
            mostra_foto(c["nome"], width=110)
        with col_txt:
            stato = " — ❌ **ELIMINATA**" if c["eliminata"] else ""
            st.subheader(f"{c['nome']}{stato}")
            st.write(f"⭐ {punti_coppia_totali(c['id'])} punti totali")
        st.divider()


# =========================
# PAGINA: EVENTI
# =========================
elif st.session_state.page == "events":
    st.title("⚡ Eventi")
    for e in get_eventi():
        st.write(f"⚡ **{e['nome']}** | {e['punti']} punti")
        if e["descrizione"]:
            st.caption(e["descrizione"])


# =========================
# PAGINA: AREA ADMIN
# =========================
elif st.session_state.page == "admin":
    if not user or not user["is_admin"]:
        st.error("Accesso riservato agli amministratori.")
        st.stop()

    st.title("🔒 Area Admin")
    tab_coppie, tab_eventi, tab_puntate, tab_mercato, tab_punti, tab_squadre, tab_leghe, tab_pw = st.tabs(
        ["💑 Coppie", "⚡ Eventi", "📺 Puntate", "⏳ Mercato", "🎯 Assegna punti", "⚽ Squadre", "🏅 Leghe", "🔑 Password"]
    )

    # --- COPPIE ---
    with tab_coppie:
        st.subheader("Aggiungi coppia")
        nome = st.text_input("Nome coppia (es. 'Marco & Sara')", key="nc_nome")
        if nome.strip():
            st.caption(f"Foto da salvare in `images/` come: **{nome_file_atteso(nome.strip())}.jpg**")
        if st.button("Aggiungi coppia"):
            if nome.strip():
                execute("INSERT INTO coppie (nome) VALUES (%s)", (nome.strip(),))
                st.success("Coppia aggiunta!")
                st.rerun()
            else:
                st.error("Inserisci un nome.")

        st.divider()
        st.subheader("Coppie esistenti")
        for c in get_coppie(solo_attive=False):
            stato = "✅ **Attiva** (schierabile)" if not c["eliminata"] else "❌ **Eliminata** (non schierabile)"
            foto = "🖼️" if find_image(c["nome"]) else f"⛔ ({nome_file_atteso(c['nome'])}.jpg)"
            st.markdown(f"💑 **{c['nome']}** — {stato} — foto: {foto}")
            col1, col2 = st.columns(2)
            # Elimina dal gioco / Ripristina (contestuale)
            if not c["eliminata"]:
                if col1.button("❌ Elimina dal gioco", key=f"elim_{c['id']}"):
                    execute("UPDATE coppie SET eliminata = 1 WHERE id = %s", (c["id"],))
                    st.rerun()
            else:
                if col1.button("♻️ Ripristina", key=f"rip_{c['id']}"):
                    execute("UPDATE coppie SET eliminata = 0 WHERE id = %s", (c["id"],))
                    st.rerun()
            # Cancella dal DB (protetta da conferma per evitare click accidentali)
            with col2.expander("⚠️ Cancella dal database"):
                st.caption("Rimuove la coppia e tutti i suoi punti/storici. **Irreversibile.**")
                if st.button("Sì, cancella definitivamente", key=f"del_{c['id']}"):
                    elimina_coppia(c["id"])
                    st.rerun()
            st.divider()

    # --- EVENTI ---
    with tab_eventi:
        st.subheader("Aggiungi evento")
        e_nome = st.text_input("Nome evento", key="ne_nome")
        e_punti = st.number_input("Punti", value=5, step=1, key="ne_punti")
        e_desc = st.text_area("Descrizione", key="ne_desc")
        e_rip = st.checkbox("🔁 Ripetibile (può capitare più volte nella stessa puntata)", key="ne_rip")
        if st.button("Aggiungi evento"):
            if e_nome.strip():
                execute(
                    "INSERT INTO eventi (nome, punti, descrizione, ripetibile) VALUES (%s, %s, %s, %s)",
                    (e_nome.strip(), e_punti, e_desc.strip(), 1 if e_rip else 0),
                )
                st.success("Evento aggiunto!")
                st.rerun()
            else:
                st.error("Inserisci un nome.")

        st.divider()
        st.subheader("Eventi esistenti")
        for e in get_eventi():
            rip = " — 🔁 ripetibile" if e["ripetibile"] else ""
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.write(f"⚡ **{e['nome']}** — {e['punti']} punti{rip}")
            if e["descrizione"]:
                col1.caption(e["descrizione"])
            if col2.button("🔁 On/Off", key=f"riptog_{e['id']}"):
                execute("UPDATE eventi SET ripetibile = %s WHERE id = %s", (0 if e["ripetibile"] else 1, e["id"]))
                st.rerun()
            if col3.button("🗑️ Cancella", key=f"delev_{e['id']}"):
                elimina_evento(e["id"])
                st.rerun()

    # --- PUNTATE ---
    with tab_puntate:
        st.subheader("Crea nuova puntata")
        prossimo = (get_puntate()[0]["numero"] + 1) if get_puntate() else 1
        num = st.number_input("Numero puntata", min_value=1, value=prossimo, step=1, key="np_num")
        if st.button("Crea puntata"):
            try:
                execute("INSERT INTO puntate (numero, aperta) VALUES (%s, 1)", (num,))
                st.success(f"Puntata {num} creata e aperta!")
                st.rerun()
            except Exception:
                st.error("Esiste già una puntata con quel numero.")

        st.divider()
        st.subheader("Puntate")
        for p in get_puntate():
            stato = "🟢 aperta" if p["aperta"] else "🔴 chiusa"
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📺 **Puntata {p['numero']}** — {stato}")
            label = "Chiudi" if p["aperta"] else "Riapri"
            if col2.button(label, key=f"pun_{p['id']}"):
                execute("UPDATE puntate SET aperta = %s WHERE id = %s", (0 if p["aperta"] else 1, p["id"]))
                st.rerun()
            with col3.expander("🗑️ Cancella"):
                st.caption("Cancella la puntata e **tutti i punti assegnati**. Irreversibile.")
                if st.button("Sì, cancella", key=f"delpun_{p['id']}"):
                    elimina_puntata(p["id"])
                    st.rerun()

    # --- MERCATO: deadline rosa + fascia blocco formazione ---
    with tab_mercato:
        st.subheader("⏳ Chiusura mercato (scelta rosa)")
        dl = get_deadline_rosa()
        if dl:
            st.info(f"Deadline rosa attuale: **{dl.strftime('%d/%m/%Y %H:%M')}**")
        else:
            st.warning("Nessuna deadline impostata: la rosa è sempre modificabile.")

        c1, c2 = st.columns(2)
        d_def = dl.date() if dl else datetime.now().date()
        t_def = dl.time() if dl else datetime.now().replace(hour=20, minute=0).time()
        d_in = c1.date_input("Data chiusura rosa", value=d_def, key="dl_data")
        t_in = c2.time_input("Ora chiusura rosa", value=t_def, key="dl_ora")

        b1, b2 = st.columns(2)
        if b1.button("💾 Imposta deadline rosa"):
            nuova = datetime.combine(d_in, t_in)
            set_impostazione("deadline_rosa", nuova.strftime(DEADLINE_FMT))
            st.success(f"Deadline impostata: {nuova.strftime('%d/%m/%Y %H:%M')}")
            st.rerun()
        if dl and b2.button("🗑️ Rimuovi deadline"):
            execute("DELETE FROM impostazioni WHERE chiave = 'deadline_rosa'")
            st.rerun()

        st.divider()
        st.subheader("🔴 Blocco formazione (fascia diretta)")
        st.caption("In questa fascia oraria gli utenti NON possono cambiare i titolari (diretta + assegnazione punti).")
        start, end = get_lock_hours()
        cc1, cc2 = st.columns(2)
        s_in = cc1.number_input("Blocca dalle ore", min_value=0, max_value=23, value=start, step=1, key="ls")
        e_in = cc2.number_input("Sblocca alle ore (giorno dopo)", min_value=0, max_value=23, value=end, step=1, key="le")
        if st.button("💾 Salva fascia di blocco"):
            set_impostazione("lock_start", int(s_in))
            set_impostazione("lock_end", int(e_in))
            st.success(f"Formazione bloccata dalle {int(s_in)}:00 alle {int(e_in)}:00.")
            st.rerun()
        stato = "🔴 BLOCCATA adesso" if formazione_bloccata() else "🟢 modificabile adesso"
        st.write(f"Stato formazione in questo momento: **{stato}**")

    # --- ASSEGNA PUNTI (griglia coppie x eventi) ---
    with tab_punti:
        st.subheader("Assegna gli eventi della puntata")
        coppie = get_coppie(solo_attive=False)
        eventi = get_eventi()
        puntate = get_puntate()

        if not coppie or not eventi or not puntate:
            st.info("Servono almeno una coppia, un evento e una puntata.")
        else:
            p_map = {f"Puntata {p['numero']}": p["id"] for p in puntate}
            sel_p = st.selectbox("Puntata", list(p_map.keys()))
            pid = p_map[sel_p]

            st.caption(
                "Spunta gli eventi successi a ciascuna coppia in questa puntata, poi premi Inserisci. "
                "Togliendo la spunta rimuovi l'evento già inserito."
            )

            correnti = {
                (r["coppia_id"], r["evento_id"]): r["q"]
                for r in query(
                    "SELECT coppia_id, evento_id, SUM(quantita) AS q FROM eventi_coppie "
                    "WHERE puntata_id = %s GROUP BY coppia_id, evento_id",
                    (pid,),
                )
            }

            with st.form(f"griglia_{pid}"):
                for c in coppie:
                    nota = " — ❌ eliminata" if c["eliminata"] else ""
                    st.markdown(f"**💑 {c['nome']}**{nota}")
                    cols = st.columns(2)
                    for i, e in enumerate(eventi):
                        chk_key = f"chk_{pid}_{c['id']}_{e['id']}"
                        qty_key = f"qty_{pid}_{c['id']}_{e['id']}"
                        attuale = correnti.get((c["id"], e["id"]), 0)
                        col = cols[i % 2]
                        label = f"🔁 {e['nome']} ({e['punti']:+d} pt cad.)" if e["ripetibile"] else f"{e['nome']} ({e['punti']:+d} pt)"
                        col.checkbox(label, value=attuale > 0, key=chk_key)
                        if e["ripetibile"]:
                            col.number_input(
                                "Quantità",
                                min_value=1, value=max(1, int(attuale)), step=1, key=qty_key,
                                label_visibility="collapsed",
                            )
                    st.divider()
                submitted = st.form_submit_button(f"💾 Inserisci punti — {sel_p}")

            if submitted:
                conn = get_connection()
                try:
                    cur = conn.cursor()
                    for c in coppie:
                        for e in eventi:
                            chk = st.session_state.get(f"chk_{pid}_{c['id']}_{e['id']}", False)
                            if e["ripetibile"]:
                                qty = st.session_state.get(f"qty_{pid}_{c['id']}_{e['id']}", 1)
                                desired = max(1, int(qty)) if chk else 0
                            else:
                                desired = 1 if chk else 0
                            cur.execute(
                                "DELETE FROM eventi_coppie WHERE coppia_id=%s AND evento_id=%s AND puntata_id=%s",
                                (c["id"], e["id"], pid),
                            )
                            if desired > 0:
                                cur.execute(
                                    "INSERT INTO eventi_coppie (coppia_id, evento_id, puntata_id, quantita) "
                                    "VALUES (%s, %s, %s, %s)",
                                    (c["id"], e["id"], pid, desired),
                                )
                    conn.commit()
                finally:
                    conn.close()
                st.success(f"Punti salvati per {sel_p}.")
                st.rerun()

        st.divider()
        st.subheader("Ultimi eventi assegnati")
        storico = query(
            """
            SELECT c.nome AS coppia, e.nome AS evento, e.punti, ec.quantita AS q,
                   p.numero AS puntata, ec.id
            FROM eventi_coppie ec
            JOIN coppie c ON c.id = ec.coppia_id
            JOIN eventi e ON e.id = ec.evento_id
            JOIN puntate p ON p.id = ec.puntata_id
            ORDER BY ec.id DESC
            LIMIT 30
            """
        )
        if not storico:
            st.caption("Nessun evento ancora assegnato.")
        for s in storico:
            q = s["q"] or 1
            extra = f" x{q}" if q > 1 else ""
            tot = s["punti"] * q
            col1, col2 = st.columns([4, 1])
            col1.write(f"📺 P{s['puntata']} — 💑 {s['coppia']} → ⚡ {s['evento']}{extra} ({tot} pt)")
            if col2.button("🗑️", key=f"delassign_{s['id']}"):
                execute("DELETE FROM eventi_coppie WHERE id = %s", (s["id"],))
                st.rerun()

    # --- SQUADRE (admin) ---
    with tab_squadre:
        st.subheader("Tutte le squadre iscritte")
        squadre_tutte = query(
            f"""
            SELECT sq.id, sq.nome_squadra, u.username,
                   {PUNTI_SUBQUERY}
            FROM squadre sq
            JOIN utenti u ON u.id = sq.user_id
            ORDER BY sq.nome_squadra
            """
        )
        filtro_sq = st.text_input("🔍 Filtra per nome squadra o giocatore", key="filtro_sq")
        squadre_vis = [
            s for s in squadre_tutte
            if filtro_sq.lower() in s["nome_squadra"].lower() or filtro_sq.lower() in s["username"].lower()
        ] if filtro_sq else squadre_tutte

        if not squadre_vis:
            st.info("Nessuna squadra trovata.")
        for s in squadre_vis:
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"**⚽ {s['nome_squadra']}** (di {s['username']}) — {s['punti']} pt")
            rosa_sq = get_rosa(s["id"])
            if rosa_sq:
                foto_cols = col1.columns(len(rosa_sq))
                for fc, c in zip(foto_cols, rosa_sq):
                    img = find_image(c["nome"])
                    if img:
                        fc.image(img, width=55)
                    fc.caption(c["nome"].split(" & ")[0])
            with col2.expander("⚠️ Cancella"):
                st.caption("Rimuove la squadra e i suoi schieramenti. **Irreversibile.**")
                if st.button("Sì, cancella", key=f"delsq_{s['id']}"):
                    elimina_squadra(s["id"])
                    st.rerun()
            st.divider()

    # --- LEGHE (admin) ---
    with tab_leghe:
        st.subheader("Tutte le leghe")
        leghe = query(
            """
            SELECT l.*, u.username AS creatore,
                   (SELECT COUNT(*) FROM lega_membri lm WHERE lm.lega_id = l.id) AS membri
            FROM leghe l JOIN utenti u ON u.id = l.creatore_id
            ORDER BY l.nome
            """
        )
        if not leghe:
            st.info("Nessuna lega creata.")
        for l in leghe:
            col1, col2 = st.columns([4, 1])
            col1.write(f"🏅 **{l['nome']}** — codice `{l['codice']}` — creata da {l['creatore']} — {l['membri']} membri")
            if col2.button("🗑️ Cancella", key=f"dellega_{l['id']}"):
                elimina_lega(l["id"])
                st.rerun()

    # --- PASSWORD ---
    with tab_pw:
        st.subheader("🔑 Credenziali utenti (solo admin)")
        st.caption("Visibile solo a te. Le password sono in chiaro.")
        utenti = query("SELECT id, username, password, is_admin FROM utenti ORDER BY is_admin DESC, username")
        for u in utenti:
            ruolo = " 👑 (admin)" if u["is_admin"] else ""
            st.write(f"👤 **{u['username']}**{ruolo} → `{u['password']}`")

        st.divider()
        st.subheader("✏️ Cambia password")
        u_map = {u["username"]: u["id"] for u in utenti}
        sel_user = st.selectbox("Utente", list(u_map.keys()))
        nuova_pw = st.text_input("Nuova password", type="password", key="cambia_pw")
        if st.button("Aggiorna password"):
            if nuova_pw:
                execute("UPDATE utenti SET password = %s WHERE id = %s", (nuova_pw, u_map[sel_user]))
                st.success(f"Password di {sel_user} aggiornata!")
                st.rerun()
            else:
                st.error("Inserisci una password.")
