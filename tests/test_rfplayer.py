import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "edisio"))
import rfplayer as r

ID = "63ED3D7A"            # = 1676492154 en decimal (le RFPlayer veut du decimal)
DEC = int(ID, 16)

# --- Lumiere / interrupteur : boutons par paire (ON impair, OFF pair) ---
assert r.build_command("on", ID, 1) == f"ON EDISIO ID {DEC} QUALIFIER 1"
assert r.build_command("off", ID, 1) == f"OFF EDISIO ID {DEC} QUALIFIER 2"
assert r.build_command("on", ID, 2) == f"ON EDISIO ID {DEC} QUALIFIER 3"
assert r.build_command("off", ID, 2) == f"OFF EDISIO ID {DEC} QUALIFIER 4"
print("lumiere ch1 ->", r.build_command("on", ID, 1), "/", r.build_command("off", ID, 1))

# --- Volet : montee = ON, descente = OFF, MEME bouton (confirme sur materiel) ---
up, down = r.build_command("open", ID, 2), r.build_command("close", ID, 2)
print("volet ch2   ->", up, "/", down)
assert up == f"ON EDISIO ID {DEC} QUALIFIER 3"
assert down == f"OFF EDISIO ID {DEC} QUALIFIER 3"
assert r.build_command("open", ID, 1) == f"ON EDISIO ID {DEC} QUALIFIER 1"
assert r.build_command("close", ID, 1) == f"OFF EDISIO ID {DEC} QUALIFIER 1"

# --- Stop : aucun verbe ZIA ne le code -> non traduit (no-op) ---
assert r.build_command("stop", ID, 1) is None

# --- Appairage d'un volet : chaque sortie apprend SA trame de pilotage ---
# La trame apprise doit etre STRICTEMENT celle que l'entite emettra ensuite.
for ch in (1, 2, 3, 4):
    assert r.build_cover_learn_command("up", ID, ch) == r.build_command("open", ID, ch)
    assert r.build_cover_learn_command("down", ID, ch) == r.build_command("close", ID, ch)
# Les deux sorties recoivent bien deux trames differentes (≠ ASSOC, unique).
assert r.build_cover_learn_command("up", ID, 1) != r.build_cover_learn_command("down", ID, 1)
assert set(r.COVER_LEARN_OUTPUTS) == {"up", "down"}
print("appairage   ->", r.build_cover_learn_command("up", ID, 1), "/",
      r.build_cover_learn_command("down", ID, 1))

# --- Entrees invalides : jamais d'exception, None ---
assert r.build_cover_learn_command("stop", ID, 1) is None
assert r.build_cover_learn_command("up", "PAS-HEXA", 1) is None
assert r.build_command("open", None, 1) is None

# --- ASSOC (appairage generique des autres recepteurs) : inchange ---
assert r.build_assoc_command(ID, 1) == f"ASSOC EDISIO ID {DEC} QUALIFIER 1"

print("OK rfplayer")
