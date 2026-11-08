# Certification, normes et méthodes

## Réglementation
- EASA CS-E (Certification Specifications for Engines) : CS-E 50 (systèmes),
  CS-E 510 (analyse de sécurité, taux de panne catastrophique < 1e-8/h),
  CS-E 520 (résistance), CS-E 740 (essai d'endurance 150 h), CS-E 800
  (ingestion d'oiseaux), CS-E 810 (rupture d'aube de compresseur/turbine,
  containment), CS-E 840 (survitesse rotor), CS-E 850 (arrêt moteur).
- FAA 14 CFR Part 33 : équivalent américain (33.75 safety analysis, 33.76 bird
  ingestion, 33.87 endurance, 33.94 blade containment).
- OACI Annexe 16 : Vol. I bruit (Chapitre 14), Vol. II émissions (NOx CAEP/8,
  nvPM CAEP/10-11), Vol. III CO2.
- ETOPS : fiabilité IFSD (in-flight shutdown) < 0,02 / 1 000 h pour 180 min.

## Normes industrielles
- SAE ARP 755A : nomenclature des stations et symboles.
- SAE AS 681 : spécification des programmes de performance (decks).
- SAE ARP 4754A / ARP 4761 : développement systèmes et analyse de sécurité.
- DO-178C : logiciel (FADEC, DAL A) ; DO-254 : hardware électronique.
- AMS (Aerospace Material Specifications) : spécifications matériaux SAE.

## Méthodes de conception
1. Analyse de cycle paramétrique (on-design) : choix OPR, T4, BPR, FPR.
2. Analyse hors-design (off-design) : lignes de fonctionnement, cartographies
   compresseur/turbine, adaptation des composants (matching).
3. Dimensionnement aéro 1D/2D (ligne moyenne), puis 3D CFD (RANS, puis URANS/LES
   pour la combustion).
4. Analyse thermique et mécanique (FEM) : fluage, LCF/HCF, Campbell/Goodman.
5. Essais : banc partiel (rig), moteur complet au point fixe, essais en
   altitude (cellule), essais en vol (banc volant).
Outils logiciels : NPSS, GasTurb, GSP, PROOSIS, pyCycle (NASA, open source).

## Carburants
- Jet A-1 (ASTM D1655 / DEF STAN 91-091) : PCI 43,0-43,2 MJ/kg, densité
  0,80 kg/L, point de congélation -47 °C.
- SAF (ASTM D7566) : HEFA, FT-SPK, ATJ ; mélange jusqu'à 50 % certifié, 100 %
  en cours.
- Hydrogène : PCI 120 MJ/kg mais densité énergétique volumique faible ;
  problèmes de NOx (température de flamme) et de stockage cryogénique.
