# bayern_blockade
Simple determination of the region within a specific radius of the borders of a town in Bavaria

Based on the name of a "Landkreis" in Bavaria, retrieve its borders, apply a maximum range from the borders, and export the resulting boundary into a GPX file.

## Motivation
Due to Corona, the government in Bavaria imposes a range you are allowed to visit, if you're living in a hotspot.
The allowed region is based on the outer borders of the city (or "Landkreis") you live in and applying a (15-km) range from there.

## Notes
1. This program is only intended to be informative and the results have no legal value whatsoever.
2. If the original city area has disjoint parts (like in Nuremberg), providing a too small radius may lead into strange and invalid results.

## Usage
Download the geographical definitions from https://opendata.bayern.de/detailansicht/datensatz/verwaltungsgebiete, unpack it under `./data/`, and run the script:

`python bayern_blockade.py`

`--target_lkr <Landkreis>` : target "Landkreis" in Bavaria using the local names. default="Nürnberg"

`--max_range_km <val>` : distance from the border of the Landkreis. default=15

`--do_map` : create an interactive map. default=False

`--open_map` : attempt to open the created interactive map in a browser. default=False

## License
Copyright &copy; 2021, Jouni Paulus

Released under BSD-3-Clause license.


