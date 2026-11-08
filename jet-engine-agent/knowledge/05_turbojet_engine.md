# Turbojet Engine (turboréacteur simple flux)

Terminologie : turbojet (EN) = turboréacteur simple flux ou « pur » (FR).
Tout l'air admis traverse le cœur (compresseur, chambre, turbine) et sort par
une seule tuyère. Pas de soufflante, taux de dilution (BPR) nul.

## Architecture
- Simple corps (single-spool) : un seul arbre, compresseur axial 7-9 étages
  (Atar 9K-50, J79 avec stators variables, Olympus 593 est double corps).
- Double corps (twin-spool) : compresseur BP + HP sur deux arbres
  concentriques (Olympus 593, J57, Pratt & Whitney J58 à cycle variable).
- Compresseur centrifuge : premiers turbojets (Whittle W.1, Rolls-Royce Derwent,
  Nene) et petits moteurs de missiles/drones (Williams F107, Microturbo TRI 60).
- Chambre : tubo-annulaire (J79, Avon) ou annulaire (moderne).
- Turbine : 1 à 3 étages, non refroidie sur les anciens (T4 ≈ 1 100-1 200 K),
  refroidie par convection/film sur les modernes (T4 1 500-1 700 K).
- Tuyère : convergente simple en subsonique ; convergente-divergente à section
  variable (volets, « paupières ») dès que NPR > 4, indispensable avec réchauffe.

## Paramètres typiques
| Moteur | Année | OPR | T4 (K) | Poussée sec / PC (kN) | TSFC sec / PC (kg/N/h) | Application |
|---|---|---|---|---|---|---|
| Junkers Jumo 004B | 1944 | 3,1 | ~1 050 | 8,8 / - | 0,142 / - | Me 262 |
| Rolls-Royce Avon 301 | 1958 | 8,4 | ~1 150 | 50 / 56 | 0,090 / - | Lightning, Hunter |
| GE J79-17 | 1960 | 13,5 | ~1 250 | 53 / 80 | 0,086 / 0,200 | F-104, F-4, B-58 |
| Snecma Atar 9K-50 | 1970 | 6,2 | ~1 200 | 50 / 71 | 0,098 / 0,200 | Mirage F1, Mirage 50 |
| RR/Snecma Olympus 593 | 1976 | 15,5 | ~1 450 | 140 / 170 | 0,120 (croisière M2) | Concorde |
| P&W J58 | 1966 | 8,8 | ~1 400 | 110 / 150 | ~0,19 (M3, PC) | SR-71 |
| Microturbo TRI 60 | 1980 | 3,8 | ~1 150 | 3,5-5,5 | ~0,13 | Missiles (Exocet, Storm Shadow) |

Ordres de grandeur : poussée spécifique 600-1 000 N/(kg/s) sec, 1 000-1 300 N/(kg/s)
avec réchauffe ; TSFC 0,085-0,12 kg/(N/h) sec, 0,17-0,21 kg/(N/h) avec réchauffe.

## Pourquoi (et quand) un turbojet plutôt qu'une turbosoufflante
Avantages :
- Vitesse d'éjection élevée : rendement propulsif bon à haut Mach (> 1,8-2) où
  V0 se rapproche de V9 ; la soufflante perd son intérêt au-delà de M ≈ 2,2.
- Section frontale minimale, faible traînée nacelle, simplicité mécanique.
- Peu sensible à l'altitude et au Mach en termes de pompage de soufflante.
Inconvénients :
- TSFC subsonique médiocre (eta_p ≈ 0,3-0,5 à M0,8) : 1,5 à 2 fois la
  consommation d'une turbosoufflante BPR 5-10.
- Bruit de jet très élevé (V9 500-700 m/s) : incompatible OACI Ch. 14 pour
  le civil (le Concorde ne respectait pas le Ch. 3).
- Température d'échappement élevée : signature infrarouge.
Domaines d'emploi actuels : missiles de croisière et drones cibles (coût, compacité),
vols supersoniques soutenus (M2-M3), moteurs d'appoint ; les chasseurs modernes
utilisent des turbosoufflantes à faible BPR (0,2-0,4) avec réchauffe.

## Dimensionnement d'un turbojet : choix principaux
1. Point de conception : croisière supersonique ou décollage selon la mission.
   À Mach élevé, la compression dynamique (tau_r) est forte : OPR optimal plus
   faible (6-10 à M2, 3-5 à M3) pour contenir T3.
2. T4 : fixée par les matériaux et le refroidissement disponible ; chaque
   +100 K ≈ +8-10 % de poussée spécifique au prix de la durée de vie.
3. Réchauffe : Tt7 1 900-2 100 K, perte de pression 4-8 %, rendement 0,9-0,95 ;
   gain de poussée 40-70 %, TSFC multipliée par ~1,8-2,2.
4. Tuyère : C-D à géométrie variable au-delà de NPR ≈ 4 ; gain 5-12 % de
   poussée à M2 par rapport à une convergente sous-détendue.
5. Entrée d'air supersonique : recouvrement MIL-E-5008B, rampes/cônes mobiles,
   pièges à couche limite, dérivation (bypass doors) pour l'adaptation débit.
6. Hors-design : lignes de fonctionnement compresseur, stators variables ou
   vannes de décharge pour la marge au pompage à bas régime ; régulation
   de la section de col A8 pour maintenir le point turbine.

## Historique court
1930 brevet Whittle ; 1937 premier essai au banc (Whittle Unit) ; 1939 premier
vol Heinkel He 178 (HeS 3B de von Ohain) ; 1944 Jumo 004 et Welland en service ;
années 1950 compresseurs axiaux haute performance (Avon, J57, J79) ; années 1960
turbojets à réchauffe supersoniques (J58, Olympus) ; à partir des années 1970 la
turbosoufflante supplante le turbojet partout sauf missiles et niches supersoniques.
