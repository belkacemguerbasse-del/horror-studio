# Principes fondamentaux des moteurs à réaction

## Cycle de Brayton
Un turboréacteur fonctionne selon un cycle de Brayton ouvert : compression
(adiabatique), apport de chaleur à pression ~constante (combustion), détente
(adiabatique) dans la turbine puis la tuyère. Le travail de la turbine
entraîne le compresseur ; l'énergie restante accélère les gaz d'échappement.

Rendement thermique idéal : eta_th = 1 - 1 / OPR^((gamma-1)/gamma).
Il croît avec le taux de compression global (OPR), mais le rendement réel
est borné par la température entrée turbine (T4 ou TIT) que supportent les
matériaux, et par les rendements des composants.

## Numérotation des stations (SAE ARP 755A)
- 0 : écoulement libre (ambiant)
- 1 : entrée de la nacelle
- 2 : entrée du compresseur (ou de la soufflante)
- 2.5 : entre compresseur BP et HP
- 3 : sortie compresseur / entrée chambre
- 4 : sortie chambre / entrée turbine HP (T4 = TIT)
- 4.5 : entre turbine HP et BP
- 5 : sortie turbine
- 7 : entrée tuyère
- 8 : col de la tuyère
- 9 : section de sortie

## Poussée
F = mdot_9 * V9 - mdot_0 * V0 + (P9 - P0) * A9
Poussée spécifique Fsp = F / mdot_0 (N par kg/s d'air). Les turboréacteurs
simple flux se situent typiquement entre 600 et 1 000 N/(kg/s) au point fixe.
Les turbosoufflantes à fort taux de dilution (BPR 8-12) descendent à
250-350 N/(kg/s), avec une consommation spécifique bien meilleure.

## Consommation spécifique (TSFC)
TSFC = mdot_fuel / F. Unités usuelles : kg/(N.h) ou lb/(lbf.h).
Conversion : 1 lb/(lbf.h) = 0,1020 kg/(N.h).
Ordres de grandeur en croisière (M0,8 / 11 km) :
- turboréacteur simple flux : 0,10-0,12 kg/(N.h)
- turbosoufflante BPR 5 (CFM56) : ~0,065 kg/(N.h)
- turbosoufflante BPR 10-12 (LEAP, GTF) : ~0,053-0,055 kg/(N.h)

## Rendements
- Rendement thermique : eta_th = puissance cinétique du jet / puissance combustible.
- Rendement propulsif : eta_p = F * V0 / puissance cinétique ≈ 2 V0 / (V9 + V0).
  Il augmente quand V9 se rapproche de V0 : c'est la motivation du taux de
  dilution élevé.
- Rendement global : eta_o = eta_th * eta_p. État de l'art en croisière : ~0,40.

## Paramètres clés de conception
| Paramètre | Turboréacteur militaire | Turbosoufflante civile moderne |
|---|---|---|
| OPR | 8-25 | 40-60 |
| T4 (TIT) | 1 600-1 900 K | 1 750-1 950 K |
| BPR | 0-1 | 9-12 |
| FPR (soufflante) | - | 1,3-1,5 |
| Rendement compresseur polytropique | 0,88-0,90 | 0,90-0,92 |
| Rendement turbine | 0,88-0,91 | 0,90-0,93 |
