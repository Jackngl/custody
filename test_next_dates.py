#!/usr/bin/env python3
"""Script de test pour vérifier les prochaines dates calculées"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Simulation de la date actuelle (15 janvier 2026, 17:55)
now = datetime(2026, 1, 15, 17, 55, 0, tzinfo=ZoneInfo("Europe/Paris"))

print("=" * 80)
print("TEST DES PROCHAINES DATES")
print("=" * 80)
print(f"\nDate actuelle simulée: {now.strftime('%d %B %Y à %H:%M:%S')}")
print(f"Jour de la semaine: {now.strftime('%A')} (ISO week: {now.isocalendar()[1]})")
print()

# Configuration simulée pour Sarah-Léa
custody_type = "alternate_weekend"
reference_year = "even"  # ou "odd" selon la config
arrival_time = "16:15"
departure_time = "19:00"

print(f"Configuration:")
print(f"  - Type de garde: {custody_type}")
print(f"  - Année de référence: {reference_year}")
print(f"  - Heure d'arrivée: {arrival_time}")
print(f"  - Heure de départ: {departure_time}")
print()

# Pour alternate_weekend, on utilise la parité ISO de la semaine
# reference_year="even" signifie qu'on a les weekends des semaines paires
# reference_year="odd" signifie qu'on a les weekends des semaines impaires

def get_week_parity(date):
    """Retourne la parité ISO de la semaine (0=paire, 1=impaire)"""
    iso_week = date.isocalendar()[1]
    return iso_week % 2

def get_next_weekend_start(date, target_parity):
    """Trouve le prochain weekend qui correspond à la parité cible"""
    current = date
    # Chercher le prochain vendredi
    days_until_friday = (4 - current.weekday()) % 7
    if days_until_friday == 0 and current.hour < 16:
        # On est vendredi avant 16h, ce weekend pourrait être le bon
        friday = current.replace(hour=16, minute=15, second=0, microsecond=0)
    else:
        if days_until_friday == 0:
            days_until_friday = 7  # Passer au vendredi suivant
        friday = (current + timedelta(days=days_until_friday)).replace(hour=16, minute=15, second=0, microsecond=0)
    
    # Vérifier la parité de la semaine du vendredi
    friday_parity = get_week_parity(friday)
    
    # Si la parité ne correspond pas, passer au weekend suivant
    if friday_parity != target_parity:
        friday += timedelta(days=7)
    
    return friday

def get_weekend_end(start):
    """Retourne la fin du weekend (dimanche 19h)"""
    # Vendredi 16:15 -> Dimanche 19:00
    sunday = start + timedelta(days=2)
    return sunday.replace(hour=19, minute=0, second=0, microsecond=0)

# Calculer la parité cible
target_parity = 0 if reference_year == "even" else 1

print(f"Parité cible: {'Paire' if target_parity == 0 else 'Impaire'}")
print(f"Parité semaine actuelle: {'Paire' if get_week_parity(now) == 0 else 'Impaire'}")
print()

# Vérifier si on est actuellement dans un weekend de garde
current_friday = now - timedelta(days=(now.weekday() - 4) % 7)
if now.weekday() >= 4:  # Vendredi ou après
    current_friday = (now - timedelta(days=(now.weekday() - 4))).replace(hour=16, minute=15, second=0, microsecond=0)
else:
    current_friday = (now - timedelta(days=(now.weekday() + 3))).replace(hour=16, minute=15, second=0, microsecond=0)

current_weekend_start = current_friday
current_weekend_end = get_weekend_end(current_weekend_start)
is_current_weekend = get_week_parity(current_weekend_start) == target_parity

print(f"Weekend actuel:")
print(f"  - Début: {current_weekend_start.strftime('%d %B %Y à %H:%M:%S')}")
print(f"  - Fin: {current_weekend_end.strftime('%d %B %Y à %H:%M:%S')}")
print(f"  - Parité: {'Paire' if get_week_parity(current_weekend_start) == 0 else 'Impaire'}")
print(f"  - En garde ce weekend: {'OUI' if is_current_weekend else 'NON'}")
print()

# Vérifier si on est actuellement en garde
is_present = False
if is_current_weekend and current_weekend_start <= now < current_weekend_end:
    is_present = True

print(f"Statut actuel: {'EN GARDE' if is_present else 'PAS EN GARDE'}")
print()

# Calculer les prochaines dates
if is_present:
    # En garde actuellement
    next_departure = current_weekend_end
    # Prochain weekend de garde
    next_weekend_start = get_next_weekend_start(now + timedelta(days=7), target_parity)
    next_arrival = next_weekend_start
else:
    # Pas en garde
    next_weekend_start = get_next_weekend_start(now, target_parity)
    next_arrival = next_weekend_start
    next_weekend_end = get_weekend_end(next_weekend_start)
    next_departure = next_weekend_end

print("=" * 80)
print("RÉSULTATS CALCULÉS")
print("=" * 80)
print()
print(f"Next arrival:  {next_arrival.strftime('%d %B %Y à %H:%M:%S') if next_arrival else 'Aucune'}")
print(f"Next departure: {next_departure.strftime('%d %B %Y à %H:%M:%S') if next_departure else 'Aucune'}")
print()

# Vérifier la cohérence
if next_arrival and next_departure:
    if next_departure < next_arrival:
        print("❌ ERREUR: next_departure est AVANT next_arrival !")
    elif next_departure == next_arrival:
        print("⚠️  ATTENTION: next_departure est ÉGAL à next_arrival")
    else:
        delta = next_departure - next_arrival
        print(f"✅ OK: next_departure est {delta.total_seconds() / 3600:.1f} heures après next_arrival")
    
    if next_arrival < now:
        print(f"⚠️  ATTENTION: next_arrival est dans le passé ({now - next_arrival})")
    if next_departure < now:
        print(f"⚠️  ATTENTION: next_departure est dans le passé ({now - next_departure})")

print()
print("=" * 80)
