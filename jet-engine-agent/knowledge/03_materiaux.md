# Matériaux et limites thermomécaniques

| Zone | Matériau typique | Température métal max (K) | Remarques |
|---|---|---|---|
| Soufflante | Ti-6Al-4V, composite carbone (LEAP, GE90) | ~ 600 | Résistance à l'ingestion d'oiseaux, flutter |
| Compresseur BP | Ti-6Al-4V, Ti-6242 | 600-800 | BLISK fréquents |
| Compresseur HP (étages arrière) | Inconel 718, Waspaloy, Udimet 720 | 900-1 000 | T3 limitant l'OPR |
| Chambre | Hastelloy X, Haynes 230, CMC (SiC/SiC) | 1 150-1 450 (CMC) | Refroidissement film/effusion |
| Turbine HP (aubes) | CMSX-4, René N5/N6 (monocristal) + TBC | ~ 1 350 (métal) | T4 jusqu'à 1 950 K avec refroidissement |
| Disques turbine HP | René 88DT, Udimet 720Li (poudre) | 900-1 000 | Fluage et fatigue en pied d'aube |
| Turbine BP | IN738, IN713, TiAl (gamma, GEnx/LEAP) | 1 000-1 100 | TiAl : -50 % de masse |
| Tuyère / canal réchauffe | Inconel 625, Haynes 188, CMC | 1 100-1 400 | |

## Mécanismes de dégradation
- Fluage : limitant pour les aubes HP ; loi de Larson-Miller pour l'extrapolation.
- Fatigue thermomécanique (TMF) et fatigue oligocyclique (LCF) : cycles décollage/atterrissage.
- Fatigue vibratoire (HCF) : excitations aérodynamiques (sillages), flutter.
- Oxydation et corrosion à chaud (sulfuration type I/II) : revêtements aluminisés, MCrAlY.
- Érosion / FOD : sable, grêle, oiseaux ; certification ingestion (CS-E 800).
- Spallation des TBC et CMAS (dépôts fondus de silicates).

## Règles de dimensionnement courantes
- Contrainte centrifuge en pied d'aube ≈ rho * omega^2 * A_annulaire / (2*pi) -> paramètre AN² (A en in², N en tr/min) :
  limite ~ 4,5-5 x 10^10 pour les turbines HP refroidies en nickel.
- Vitesse périphérique soufflante : 400-480 m/s (Ti), limitée par le flutter et le bruit.
- Durée de vie des pièces critiques (disques) : déclarée en cycles (LLP), 15 000-30 000 cycles typiques.
