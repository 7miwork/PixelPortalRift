# Loesungen - PixelPortalRift Hausaufgaben (5 Stufen)

| Stufe | Fehlende Zeile | Typischer Fehler |
|---|---|---|
| 1 | `holz["count"] = holz["count"] + 3` | `holz = holz + 3` (Dictionary statt Wert) |
| 2 | `return inventory.get(name, 0) >= count` | `return` vergessen, nur `>` statt `>=` |
| 3 | `ok = False` | `ok == False` (Vergleich statt Zuweisung) |
| 4 | `self.count -= count` | `self.` vergessen, oder `+=` statt `-=` |
| 5 | `inventory[zutat] -= anzahl` | `inventory.zutat` statt `inventory[zutat]` |

Ablauf: Schueler-Ordner mitgeben. Jede Datei hat Beispiel, Aufgabe, Selbst-Check und Eltern-Karte.
Beim naechsten Termin: Eltern-Karte der letzten Stufe muendlich wiederholen lassen (2 Minuten).
