-- ================================================================
-- QUERY DI RIFERIMENTO — Fanta Temptation Island
-- PostgreSQL / Supabase
--
-- Raccolta delle query più importanti del progetto,
-- tutte con JOIN e aggregazioni. Utili per capire come
-- funziona il calcolo dei punti, le classifiche e le leghe.
-- ================================================================


-- ----------------------------------------------------------------
-- 1. PUNTI TOTALI DI UNA COPPIA
--    Somma tutti i punti che una coppia ha accumulato nel gioco,
--    indipendentemente da chi l'ha schierata o in quale puntata.
--    Usata nella pagina "Coppie" per mostrare i punti complessivi.
-- ----------------------------------------------------------------
SELECT
    COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
FROM eventi_coppie ec
JOIN eventi e ON e.id = ec.evento_id
WHERE ec.coppia_id = 1;  -- sostituisci con l'id della coppia


-- ----------------------------------------------------------------
-- 2. ROSA DI UNA SQUADRA (le 5 coppie scelte)
--    Mostra le coppie che un utente ha scelto per la sua rosa.
--    La tabella ponte "squadra_coppie" collega squadre e coppie.
-- ----------------------------------------------------------------
SELECT c.*
FROM squadra_coppie sc
JOIN coppie c ON c.id = sc.coppia_id
WHERE sc.squadra_id = 1  -- sostituisci con l'id della squadra
ORDER BY c.nome;


-- ----------------------------------------------------------------
-- 3. TITOLARI SCHIERATI IN UNA PUNTATA
--    Le coppie che una squadra ha schierato in una specifica puntata.
--    La tabella ponte "schieramenti" collega squadre, coppie e puntate.
-- ----------------------------------------------------------------
SELECT c.*
FROM schieramenti s
JOIN coppie c ON c.id = s.coppia_id
WHERE s.squadra_id = 1     -- id squadra
  AND s.puntata_id = 1     -- id puntata
ORDER BY c.nome;


-- ----------------------------------------------------------------
-- 4. PUNTI DI UNA SQUADRA (solo coppie schierate)
--    La regola del gioco: una coppia porta punti alla squadra
--    SOLO nelle puntate in cui è stata schierata come titolare.
--    Tre JOIN: schieramenti → eventi_coppie → eventi.
-- ----------------------------------------------------------------
SELECT
    COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
FROM schieramenti s
JOIN eventi_coppie ec
    ON ec.coppia_id = s.coppia_id
    AND ec.puntata_id = s.puntata_id   -- stessa puntata: la condizione chiave
JOIN eventi e ON e.id = ec.evento_id
WHERE s.squadra_id = 1;  -- id squadra


-- ----------------------------------------------------------------
-- 5. DETTAGLIO PUNTI PUNTATA PER PUNTATA (storico squadra)
--    Per ogni puntata e ogni coppia schierata: quanti punti ha fatto.
--    LEFT JOIN perché una coppia può essere schierata senza che
--    le vengano assegnati eventi in quella puntata (0 punti).
-- ----------------------------------------------------------------
SELECT
    p.numero      AS puntata,
    c.nome        AS coppia,
    COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti
FROM schieramenti s
JOIN  puntate p  ON p.id = s.puntata_id
JOIN  coppie  c  ON c.id = s.coppia_id
LEFT JOIN eventi_coppie ec
    ON ec.coppia_id = s.coppia_id
    AND ec.puntata_id = s.puntata_id
LEFT JOIN eventi e ON e.id = ec.evento_id
WHERE s.squadra_id = 1   -- id squadra
GROUP BY s.puntata_id, s.coppia_id, p.numero, c.nome
ORDER BY p.numero, c.nome;


-- ----------------------------------------------------------------
-- 6. CLASSIFICA GENERALE
--    Tutte le squadre con il loro punteggio totale, ordinate.
--    La subquery PUNTI_SUBQUERY (punto 4) è inline qui.
--    JOIN: squadre → utenti (per mostrare il nome del giocatore).
-- ----------------------------------------------------------------
SELECT
    u.username,
    sq.id           AS squadra_id,
    sq.nome_squadra,
    COALESCE((
        SELECT SUM(e.punti * COALESCE(ec.quantita, 1))
        FROM schieramenti s
        JOIN eventi_coppie ec
            ON ec.coppia_id = s.coppia_id
            AND ec.puntata_id = s.puntata_id
        JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = sq.id
    ), 0) AS punti
FROM squadre sq
JOIN utenti u ON u.id = sq.user_id
ORDER BY punti DESC, sq.nome_squadra;


-- ----------------------------------------------------------------
-- 7. CLASSIFICA DI UNA LEGA
--    Come la classifica generale, ma filtrata per i soli iscritti
--    a una specifica lega.
--    JOIN: lega_membri → utenti → squadre.
-- ----------------------------------------------------------------
SELECT
    u.username,
    sq.id           AS squadra_id,
    sq.nome_squadra,
    COALESCE((
        SELECT SUM(e.punti * COALESCE(ec.quantita, 1))
        FROM schieramenti s
        JOIN eventi_coppie ec
            ON ec.coppia_id = s.coppia_id
            AND ec.puntata_id = s.puntata_id
        JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = sq.id
    ), 0) AS punti
FROM lega_membri lm
JOIN utenti  u  ON u.id = lm.user_id
JOIN squadre sq ON sq.user_id = u.id
WHERE lm.lega_id = 1   -- id della lega
ORDER BY punti DESC, sq.nome_squadra;


-- ----------------------------------------------------------------
-- 8. LEGHE A CUI È ISCRITTO UN UTENTE
--    Recupera tutte le leghe di un utente passando per la
--    tabella ponte lega_membri.
-- ----------------------------------------------------------------
SELECT l.*
FROM lega_membri lm
JOIN leghe l ON l.id = lm.lega_id
WHERE lm.user_id = 1   -- id utente
ORDER BY l.nome;


-- ----------------------------------------------------------------
-- 9. STORICO ULTIMI EVENTI ASSEGNATI (vista admin)
--    Gli ultimi 30 eventi assegnati, con nome coppia, evento,
--    puntata, punti e quantità.
--    Quattro tabelle collegate: eventi_coppie → coppie, eventi, puntate.
-- ----------------------------------------------------------------
SELECT
    c.nome      AS coppia,
    e.nome      AS evento,
    e.punti,
    ec.quantita AS quantita,
    p.numero    AS puntata,
    ec.id
FROM eventi_coppie ec
JOIN coppie  c ON c.id = ec.coppia_id
JOIN eventi  e ON e.id = ec.evento_id
JOIN puntate p ON p.id = ec.puntata_id
ORDER BY ec.id DESC
LIMIT 30;


-- ----------------------------------------------------------------
-- 10. TUTTE LE SQUADRE CON PUNTEGGIO (vista admin Squadre)
--     Come la classifica generale ma ordinata per nome squadra,
--     usata nella tab admin "Squadre" con filtro e bottone cancella.
-- ----------------------------------------------------------------
SELECT
    sq.id,
    sq.nome_squadra,
    u.username,
    COALESCE((
        SELECT SUM(e.punti * COALESCE(ec.quantita, 1))
        FROM schieramenti s
        JOIN eventi_coppie ec
            ON ec.coppia_id = s.coppia_id
            AND ec.puntata_id = s.puntata_id
        JOIN eventi e ON e.id = ec.evento_id
        WHERE s.squadra_id = sq.id
    ), 0) AS punti
FROM squadre sq
JOIN utenti u ON u.id = sq.user_id
ORDER BY sq.nome_squadra;


-- ----------------------------------------------------------------
-- 11. LEGHE CON NUMERO DI MEMBRI (vista admin Leghe)
--     Per ogni lega: nome, codice, creatore e quanti iscritti ha.
--     Usa una subquery scalare per il conteggio membri.
-- ----------------------------------------------------------------
SELECT
    l.*,
    u.username AS creatore,
    (SELECT COUNT(*) FROM lega_membri lm WHERE lm.lega_id = l.id) AS membri
FROM leghe l
JOIN utenti u ON u.id = l.creatore_id
ORDER BY l.nome;


-- ----------------------------------------------------------------
-- 12. EVENTI ASSEGNATI A UNA COPPIA IN UNA PUNTATA SPECIFICA
--     Utile per verificare cosa è successo a una coppia in un episodio.
-- ----------------------------------------------------------------
SELECT
    e.nome      AS evento,
    e.punti,
    ec.quantita,
    (e.punti * ec.quantita) AS punti_totali
FROM eventi_coppie ec
JOIN eventi e ON e.id = ec.evento_id
WHERE ec.coppia_id = 1    -- id coppia
  AND ec.puntata_id = 1;  -- id puntata


-- ----------------------------------------------------------------
-- 13. RIEPILOGO PUNTI PER PUNTATA (tutte le squadre)
--     Utile per vedere chi ha fatto meglio in ogni singola puntata.
--     Aggrega per squadra e per puntata.
-- ----------------------------------------------------------------
SELECT
    p.numero        AS puntata,
    u.username,
    sq.nome_squadra,
    COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti_puntata
FROM schieramenti s
JOIN puntate p  ON p.id = s.puntata_id
JOIN squadre sq ON sq.id = s.squadra_id
JOIN utenti  u  ON u.id = sq.user_id
JOIN coppie  c  ON c.id = s.coppia_id
LEFT JOIN eventi_coppie ec
    ON ec.coppia_id = s.coppia_id
    AND ec.puntata_id = s.puntata_id
LEFT JOIN eventi e ON e.id = ec.evento_id
GROUP BY p.numero, s.squadra_id, u.username, sq.nome_squadra
ORDER BY p.numero, punti_puntata DESC;


-- ----------------------------------------------------------------
-- 14. COPPIE PIÙ "PROFITTEVOLI" IN ASSOLUTO
--     Classifica le coppie per punti totali guadagnati nel gioco,
--     indipendentemente da chi le ha schierate.
-- ----------------------------------------------------------------
SELECT
    c.nome,
    COALESCE(SUM(e.punti * COALESCE(ec.quantita, 1)), 0) AS punti_totali,
    COUNT(ec.id) AS eventi_subiti
FROM coppie c
LEFT JOIN eventi_coppie ec ON ec.coppia_id = c.id
LEFT JOIN eventi e ON e.id = ec.evento_id
GROUP BY c.id, c.nome
ORDER BY punti_totali DESC;


-- ----------------------------------------------------------------
-- 15. QUANTE VOLTE UNA COPPIA È STATA SCHIERATA DA OGNI SQUADRA
--     Utile per capire quali coppie sono più "popolari" tra i giocatori.
-- ----------------------------------------------------------------
SELECT
    c.nome          AS coppia,
    u.username,
    sq.nome_squadra,
    COUNT(s.id)     AS volte_schierata
FROM schieramenti s
JOIN coppie  c  ON c.id = s.coppia_id
JOIN squadre sq ON sq.id = s.squadra_id
JOIN utenti  u  ON u.id = sq.user_id
GROUP BY c.id, c.nome, sq.id, u.username, sq.nome_squadra
ORDER BY c.nome, volte_schierata DESC;



#	Query	Cosa fa
1	Punti totali coppia	SUM con JOIN eventi
2	Rosa squadra	JOIN squadra_coppie → coppie
3	Titolari in una puntata	JOIN schieramenti → coppie
4	Punti squadra (solo titolari)	Doppio JOIN con condizione di puntata
5	Storico puntata per puntata	LEFT JOIN per includere puntate a 0
6	Classifica generale	Subquery annidata + JOIN utenti
7	Classifica di una lega	JOIN lega_membri → utenti → squadre
8	Leghe di un utente	JOIN lega_membri → leghe
9	Ultimi eventi assegnati	4 tabelle collegate
10	Tutte le squadre con punti	Vista admin Squadre
11	Leghe con conteggio membri	Subquery scalare + JOIN
12	Eventi coppia in una puntata	Filtro specifico coppia+puntata
13	Punti per puntata (tutte squadre)	GROUP BY puntata + squadra
14	Coppie più profittevoli	Classifica coppie per punti totali
15	Popolarità coppie	Conteggio schieramenti per coppia
