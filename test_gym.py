"""Self-check di Sales Gym: python test_gym.py (con il python della .venv di video-editor)."""
import json
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path

import numpy as np

tmp = Path(tempfile.mkdtemp())
os.environ.update(GYM_ROOT=str(tmp / "root"), GYM_VAULT=str(tmp / "vault"), GYM_INBOX=str(tmp / "inbox"), GYM_WIDGET=str(tmp / "no"))
import gym  # noqa: E402


def w(text, start, end, seg=0):
    return {"w": text, "start": start, "end": end, "seg": seg}


# intercalari
c = gym.count_fillers([gym.norm(x) for x in "Insomma, e niente, ecco ehm tipo insomma".split()])
assert c["insomma"] == 2 and c["e niente"] == 1 and c["ecco"] == 1 and c["ehm"] == 1, c

# curva del suono: 0-1 s voce, 1-2 s rumore di fondo, 2-3 s "ehm" senza parole, 3-4 s voce, 4-7 s silenzio, 7-8 s voce
db = np.full(160, 30.0)
db[:20] = db[40:60] = db[60:80] = db[140:] = 70.0
words = [w("buongiorno", 0.2, 0.9), w("come", 3.0, 3.4), w("va?", 3.5, 3.9), w("bene", 7.1, 7.5)]
m = gym.compute_metrics(words, db, 8.0)
assert [h["tipo"] for h in m["hesitations"]] == ["suono senza parole"], m["hesitations"]
assert m["pauses_long"] == 1, "il silenzio pieno è una pausa, non un'esitazione"

# parola allungata
m = gym.compute_metrics([w("e", 0, 2.0), w("poi", 2.0, 2.3)] + [w("ok", 2.4, 2.6)], np.full(60, 70.0), 3.0)
assert m["hesitations"][0]["tipo"] == "parola allungata", m

# turni del cliente esclusi, anche il suono mentre parla lui
words = [w("insomma", 0, 0.5, 0), w("insomma", 1, 1.5, 1), w("ecco", 5, 5.4, 2)]
m = gym.compute_metrics(words, np.full(120, 70.0), 6.0, client_segments=[1])
assert m["fillers"] == {"insomma": 1, "ecco": 1} and m["own_words"] == 2 and not m["hesitations"], m

# livelli: le call non contano e il focus deve riuscire
good = {"kind": "simulazione", "voto": 7, "focus_riuscito": True}
assert gym.level_for([good, good]) == 1 and gym.level_for([good] * 3) == 2
assert gym.level_for([good, good, {"kind": "simulazione", "voto": 7, "focus_riuscito": False}, good]) == 1
assert gym.level_for([good, good, {"kind": "call", "voto": 2}, good]) == 2

# data dai metadati, non dal file
media = tmp / "video.mov"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=200:duration=2", "-metadata",
                "creation_time=2026-03-04T10:20:30Z", media], check=True)
assert gym.media_datetime(media).date() == date(2026, 3, 4)

REVIEW = {"voto": 7, "sottovoti": {k: 7 for k in gym.SUBSCORES}, "punti_forti": ["a"], "punti_deboli": ["b"], "consigli": ["c"],
          "focus_riuscito": True, "focus_prossimo": "Pausa dopo le domande", "script_successivo": "**Focus:** nuovo\n1. **Chi**"}
assert not gym.validate_review(REVIEW)
assert gym.validate_review({**REVIEW, "voto": 11}) and gym.validate_review({**REVIEW, "script_successivo": "x\n" * 30})
assert gym.validate_review(REVIEW, ["**focus:** NUOVO 1. chi"]), "script identico a uno recente va rifiutato"


def fixture(sid, source, kind="simulazione", review=REVIEW):
    d = gym.WORK / sid
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"id": sid, "source": str(source), "date": sid[:10], "kind": kind, "baseline": False,
                                             "has_video": False, "duration": 2.0}))
    (d / "words.json").write_text(json.dumps([w("ciao", 0, 0.5)]))
    (d / "transcript.txt").write_text("#0 [00:00] ciao")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=200:duration=2", "-ac", "1", "-ar", "16000",
                    d / "audio.wav"], check=True)
    (d / "review.json").write_text(json.dumps(review))
    return d


gym.DATA.mkdir(parents=True)
gym.SCRIPT.write_text("**Focus:** vecchio\n")
day = "2026-03-04"
src = tmp / "a.mov"
src.write_bytes(b"x")

# review non valida: niente viene cancellato
d = fixture(f"{day}_101010", src, review={**REVIEW, "voto": 0})
try:
    gym.commit(f"{day}_101010")
    raise AssertionError("doveva fallire")
except SystemExit:
    pass
assert src.exists() and d.exists() and gym.SCRIPT.read_text().startswith("**Focus:** vecchio"), "dati toccati da una review invalida"

# se salti un giorno lo script resta quello
assert "vecchio" in gym.ensure_daily("2026-03-02").read_text() and "vecchio" in gym.ensure_daily("2026-03-03").read_text()

# review valida: spunta il giorno del video, cambia script, cancella alla fine
(d / "review.json").write_text(json.dumps(REVIEW))
gym.commit(f"{day}_101010")
assert not src.exists() and not d.exists()
note = gym.daily_path(day).read_text()
assert "- [x] Video di oggi" in note and "fatto: true" in note and "Review" in note
assert "- [ ] Video di oggi" in gym.daily_path("2026-03-03").read_text()
assert "nuovo" in gym.SCRIPT.read_text()
assert "nuovo" in gym.ensure_daily("2026-03-05").read_text()
assert gym.load_sessions()[0]["script_provato"].startswith("**Focus:** vecchio")
assert (gym.VAULT / "Grafici/calendario.svg").exists()

# stesso script di nuovo: rifiutato e video salvo
src2 = tmp / "b.mov"
src2.write_bytes(b"x")
fixture("2026-03-06_101010", src2)
try:
    gym.commit("2026-03-06_101010")
    raise AssertionError("doveva rifiutare lo script ripetuto")
except SystemExit:
    pass
assert src2.exists()

# una review rifiutata conta come tentativo e non ferma il giro; al terzo il file va in Errori, intatto
gym.INBOX.mkdir(parents=True)
stuck = gym.INBOX / "c.mov"
stuck.write_bytes(b"x")
gym.send_reminder = lambda today: None
gym.process = lambda path, call: exit("review non valida")
for _ in range(gym.MAX_ATTEMPTS):
    gym.auto()
assert not stuck.exists() and (gym.INBOX / "Errori/c.mov").read_bytes() == b"x"
assert "Errori" in gym.daily_path(date.today().isoformat()).read_text()
print("ok")
