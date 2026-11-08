# Composants d'un turboréacteur

## Entrée d'air (manche)
Rôle : amener l'air au compresseur avec une pression totale maximale et une
distorsion minimale. Recouvrement de pression Pt2/Pt0 : 0,97-0,99 en
subsonique ; en supersonique on utilise la norme MIL-E-5008B :
Pt2/Pt0 = 1 - 0,075 (M0 - 1)^1,35 pour 1 < M0 < 5.
Entrées supersoniques à compression externe/mixte (rampe, cône) pour limiter
les pertes par chocs.

## Compresseur
- Axial multi-étages : taux par étage 1,15-1,4 (transsonique jusqu'à 1,6-1,8
  pour les premiers étages). Rendement polytropique 0,88-0,92.
- Centrifuge : taux 4-8 par étage, compact, utilisé sur petits moteurs et APU.
- Marge au pompage (surge margin) : typiquement 15-25 %. Le pompage est une
  inversion violente du débit ; le décrochage tournant le précède.
- Lignes de fonctionnement : le compresseur HP est le plus critique
  (température, jeux, taux par étage). Stators à calage variable (VSV) et
  vannes de décharge (VBV) pour la stabilité aux régimes partiels.
- Aubes : titane (Ti-6Al-4V) jusqu'à ~600 K ; au-delà Inconel 718 ;
  derniers étages HP : alliages de nickel (T3 jusqu'à ~950 K sur les
  moteurs modernes à OPR élevé). Disques BLISK (aubes et disque monobloc) sur
  les moteurs récents.

## Chambre de combustion
Types : annulaire (standard moderne), tubulaire, tubo-annulaire.
Paramètres :
- Richesse globale f = mdot_f / mdot_air ≈ 0,02-0,03 ; zone primaire proche
  de la stoechiométrie (f_st ≈ 0,068 pour le kérosène).
- Perte de pression totale : 3-6 %.
- Rendement de combustion > 99 % au point de conception.
- Facteur de profil / pattern factor en sortie : 0,15-0,30 (homogénéité
  thermique vers la turbine).
- Émissions : NOx (RQL, TAPS/lean-burn), CO/UHC à faible régime, suies.
  Normes OACI CAEP/8 puis CAEP/10 (nvPM).
- Refroidissement des parois : films, effusion, matériaux CMC envisagés.

## Turbine
- Détente des gaz chauds pour entraîner compresseur (et soufflante).
- Turbine HP : 1-2 étages, chargement élevé, refroidissement interne
  (convection, impact, film) consommant 15-25 % du débit cœur.
- Turbine BP : 3-7 étages, entraîne la soufflante (directement ou via
  réducteur sur les GTF type PW1000G).
- Aubes HP : superalliages de nickel monocristallins (CMSX-4, René N5),
  revêtement barrière thermique (TBC, zircone yttriée) : gain 100-150 K.
- Température métal admissible : ~1 350 K en continu ; T4 jusqu'à 1 950 K
  grâce au refroidissement + TBC.
- Jeux en bout d'aube : contrôle actif (ACC) par air de refroidissement du
  carter, gain de rendement de 0,5-1 %.

## Tuyère
- Convergente : suffisante jusqu'à NPR ≈ 3-4 (vols subsoniques).
- Convergente-divergente à géométrie variable pour le supersonique
  (NPR > 5) : gain significatif de poussée par détente complète.
- Rapport critique de pression (gamma = 1,33) : 1,85.
- Coefficient de vitesse Cv : 0,97-0,99 ; coefficient de débit Cd : 0,96-0,99.
- Mélangeur (turbosoufflantes à flux mélangés) : gain 2-3 % de TSFC, réduction du bruit.

## Post-combustion (réchauffe)
Augmente la poussée de 50-70 % en portant la température à ~2 000-2 200 K
dans le canal de réchauffe, au prix d'une TSFC doublée (0,17-0,20 kg/(N.h)).
Utilisée sur les moteurs militaires (M88, F119, EJ200).

## Systèmes auxiliaires
- Boîtier d'accessoires (AGB), générateur, pompes hydrauliques et carburant.
- Régulation numérique FADEC : lois N1/N2/EPR, protections (surchauffe,
  survitesse, pompage), gestion des VSV/VBV et des jeux.
- Lubrification : huiles synthétiques MIL-PRF-23699, température max ~ 200 °C.
- Démarrage : démarreur pneumatique ou électrique, allumeurs haute énergie.
