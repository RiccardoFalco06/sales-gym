---
name: sales-gym
description: Analizza subito un video di allenamento o la registrazione di una sales call di Riccardo dentro Sales Gym (trascrizione, frame, voto, consigli, script del giorno dopo, tracking in Obsidian). Usare quando Riccardo manda in chat un video o audio di allenamento/simulazione o una call da valutare, quando chiede lo script di oggi o com'è andata la sessione, o quando nomina Sales Gym.
---

# Sales Gym in chat

Progetto: `~/Projects/sales-gym`. Python: `~/Projects/video-editor/.venv/bin/python`.

**Script di oggi:** leggi `data/current_script.md`. Se Riccardo chiede solo quello, fermati qui.

## Analizzare un file
1. `python gym.py ingest "<file>"`, con `--call` se è una call vera. Stampa l'id.
   - Se stampa `POCO_PARLATO`, avvisalo: la casella non va spuntata e il file resta dov'è.
2. Leggi `prompt.md` e seguilo con `{{DIR}}` = `work/<id>`, `{{CODE}}` = il progetto, `{{PY}}` = il python sopra, `{{TIPO}}` = simulazione o call vera, `{{LUNEDI}}` = se oggi è lunedì.
3. `python gym.py check <id>` finché stampa `ok`, poi `python gym.py commit <id>`: salva, spunta il giorno, aggiorna grafici e script.
   **Cancella il file indicato all'ingest**, quindi indica solo video di Sales Gym, mai originali da conservare. Se Riccardo vuole tenerlo, fai prima una copia e passa quella.
4. Riporta in chat: voto, punti forti e deboli, focus e nuovo script. Di' che il video è stato cancellato.

Non modificare `data/sessions.jsonl` a mano.
