#!/usr/bin/env python3
"""Test de debug pour comprendre pourquoi next_departure = 15 janvier"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Date actuelle simulée (jeudi 15 janvier 2026, 17:55)
now = datetime(2026, 1, 15, 17, 55, 0, tzinfo=ZoneInfo("Europe/Paris"))

print("=" * 80)
print("DEBUG - Pourquoi next_departure = 15 janvier ?")
print("=" * 80)
print(f"\nDate actuelle: {now.strftime('%A %d %B %Y à %H:%M:%S')}")
print(f"Jour de la semaine: {now.strftime('%A')} (ISO semaine {now.isocalendar()[1]})")
print()

# Simuler le calcul
print("Simulation du calcul:")
print("-" * 80)

# Pour alternate_weekend avec reference_year="even" (semaines paires)
# Le jeudi 15 janvier est semaine 3 (impaire), donc PAS en garde
iso_week = now.isocalendar()[1]
week_parity = iso_week % 2
reference_year = "even"  # Semaines paires
target_parity = 0  # Paire

print(f"Semaine ISO: {iso_week}")
print(f"Parité semaine: {'Paire' if week_parity == 0 else 'Impaire'}")
print(f"Reference year: {reference_year} (semaines {'paires' if target_parity == 0 else 'impaires'})")
print(f"En garde ce weekend: {'NON' if week_parity != target_parity else 'OUI'}")
print()

# Calculer les prochaines fenêtres
print("Prochaines fenêtres de garde (semaines paires):")
print("-" * 80)

# Semaine 4 (paire) - 23-25 janvier
week4_friday = datetime(2026, 1, 23, 16, 15, 0, tzinfo=ZoneInfo("Europe/Paris"))
week4_sunday = datetime(2026, 1, 25, 19, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

print(f"1. {week4_friday.strftime('%A %d %B %Y à %H:%M')} → {week4_sunday.strftime('%A %d %B %Y à %H:%M')}")

# Simuler is_present
is_present = False  # Pas en garde le jeudi (semaine impaire)
current_window = None
next_window_start = week4_friday
next_window_end = week4_sunday

print(f"\nCalcul:")
print(f"  is_present: {is_present}")
print(f"  current_window: {current_window}")
print(f"  next_window: {next_window_start.strftime('%d %B %H:%M')} → {next_window_end.strftime('%d %B %H:%M')}")
print()

if is_present:
    print("  ❌ PROBLÈME: is_present=True mais current_window=None")
    print("     Cela peut arriver avec un override")
    print("     Dans l'ancien code: next_departure = now_local (15 janvier)")
    print("     Dans le nouveau code: next_departure = next_window.end")
else:
    print("  ✅ is_present=False")
    print(f"     next_arrival = {next_window_start.strftime('%d %B %Y à %H:%M')}")
    print(f"     next_departure = {next_window_end.strftime('%d %B %Y à %H:%M')}")

print()
print("=" * 80)
print("VÉRIFICATION: Si next_departure = 15 janvier, c'est probablement:")
print("  1. Un override actif qui force is_present=True")
print("  2. current_window=None mais is_present=True")
print("  3. L'ancien code qui mettait next_departure = now_local")
print("=" * 80)
