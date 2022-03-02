#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# bayern_blockade.py
#
# Based on the name of a Landkreis in Bavaria, retrieve its borders,
# apply a maximum range from the borders, and export the resulting
# boundary into a GPX file.
#
# Motivation: Due to Corona, the government in Bavaria imposes a
# range you are allowed to visit, if you're living in a hotspot.
# The allowed region is based on the outer borders of the city
# (or Landkreis) you live in and applying a (15-km) range from there.
#
# Please note, that this program is only intended to be informative
# and the results have no legal value whatsoever.
#
# Note: If the original city area has disjoint parts (like in Nuremberg),
# providing a too small radius may lead into strange and invalid results.
#
# Download the geographical definitions from
# <https://opendata.bayern.de/detailansicht/datensatz/verwaltungsgebiete>,
# unpack it under ./data/, and run the script.
#
# Usage:
#  python bayern_blockade.py
#    --target_lkr <Landkreis> : target "Landkreis" in Bavaria. default="Nürnberg"
#    --max_range_km <val> : distance from the border of the Landkreis. default=15
#    --do_map : create an interactive map. default=False
#    --open_map : attempt to open the created interactive map in a browser. default=False
#
#
#
# (c) Jouni Paulus, 09.01.2021
#
##
# License: BSD-3-Clause
#
# Copyright 2021 Jouni Paulus
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import sys
import os
import argparse  # command line handling
import geopandas as gpd  # geographic data handling

import folium  # interactive slippy map
import webbrowser  # for launching browser


__version__ = 0.3

# data downloaded from <https://opendata.bayern.de/detailansicht/datensatz/verwaltungsgebiete>
border_file = 'data/Verwaltungsgebiete_shp_epsg4258/lkr_ex.shp'  #  Landkreise
field_name = 'BEZ_KRS'
# it's possible that the same BEZ_KRS exists for a "Kreisfreie Stadt" and "Landkreis", e.g., Fürth
adm_map = {'4002': 'Landkreis', '4003': 'Kreisfreie Stadt'}
adm_shorts = {'4002': '(Lkr)', '4003': '(kfSt)'}

credit_text = 'Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de'

char_coding = 'iso8859_15'

##
def main(argv):
    """
    Top level input argument parsing.

    Parameters
    ----------
    argv : list of string

    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--target_lkr',
                           action='store',
                           type=str,
                           default='Nürnberg',
                           help='target "Landkreis" or "Kreisfreie Stadt" in Bavaria')

    argparser.add_argument('--max_range_km',
                           action='store',
                           type=float,
                           default=15,
                           help='range from the border of the Landkreis')

    argparser.add_argument('--do_map',
                           action='store_true',
                           help='create an interactive map')

    argparser.add_argument('--open_map',
                           action='store_true',
                           help='attempt to open the created interactive map in a browser')

    args = argparser.parse_args(argv)

    # load border data
    lkr_data = gpd.read_file(border_file)
    print('INFO: Geographical data credits:\n{}\nLicense: CC BY'.format(credit_text))

    # encode targe name in binary
    target_lkr_b = str.encode(args.target_lkr, encoding=char_coding)

    # modify all 'BEZ_KRS' to be bytes (some are str, some bytes)
    for r_idx, one_row in lkr_data.iterrows():
        if type(one_row[field_name]) != bytes:
            lkr_data.at[r_idx, field_name] = str.encode(one_row[field_name], encoding=char_coding)

    # retrieve row of target
    target_data = lkr_data[lkr_data[field_name] == target_lkr_b]

    # couldn't find requested target => show a list of supported alternatives
    if target_data.shape[0] == 0:
        print('ERROR: Could not find "{}" in the data.'.format(args.target_lkr))
        print('INFO: Available alternatives are:')

        lkr_list = [lkr.decode(char_coding) for lkr in lkr_data[field_name]]
        lkr_list.sort()
        alt_str = None
        for one_lkr in lkr_list:
            if alt_str is None:
                alt_str = one_lkr
            else:
                alt_str += ', ' + one_lkr

        print(alt_str)

        sys.exit()

    elif target_data.shape[0] > 1:
        print('INFO: Found multiple hits:')
        adm_list = []
        for alt_idx, alt_data in enumerate(target_data.iterrows()):
            row_idx, one_row = alt_data

            print('#{}: {} ({})'.format(alt_idx+1,
                                        one_row[field_name].decode(char_coding),
                                        adm_map[one_row['ADM']]))
            adm_list.append(one_row['ADM'])

        while True:
            try:
                user_in = int(input('Select one of the listed alternatives (number of the selection): '))
            except ValueError:
                print('ERROR: Input was not a valid number.')
            else:
                if 0 < user_in <= target_data.shape[0]:
                    target_data = lkr_data[(lkr_data[field_name] == target_lkr_b) & (lkr_data['ADM'] == adm_list[user_in-1])]
                    args.target_lkr += adm_shorts[adm_list[user_in-1]]
                    break

    # retrieve the border polygon
    border_poly = target_data['geometry']

    print('INFO: Border polygon uses CRS: "{}""'.format(lkr_data.crs))

    # project data to UTM North (in which the units are in meters)
    target_data = target_data.to_crs('EPSG:32633')
    b_poly = target_data['geometry']

    # use dilation with the given radius. result is a MultiPolygon
    allowed_area = b_poly.buffer(args.max_range_km * 1000.0)

    # retrieve MultiLine representation of the area boundary
    aa_bound = allowed_area.boundary

    # convert the coordinate system to WGS84
    aa_bound = aa_bound.to_crs('EPSG:4258')

    # export to a file
    out_name_base = '{}_{}km'.format(args.target_lkr, args.max_range_km)
    out_name = '{}.gpx'.format(out_name_base)
    aa_bound.to_file(out_name, 'GPX')

    print('INFO: Exported boundary into "{}"'.format(out_name))

    if args.do_map or args.open_map:
        folium_map_file = os.path.join(os.getcwd(), '{}.html'.format(out_name_base))

        # convert allowed area to WSG84 for visualization with folium
        aa_wsg84 = allowed_area.to_crs('EPSG:4258')

        # compute center of the area (for centering the map) and convert to WGS84
        lkr_center = allowed_area.centroid.to_crs('EPSG:4258')

        # basemap
        m = folium.Map(location=(lkr_center.y, lkr_center.x),
                       control_scale=True,  # add reference scale (distance) information
                       tiles=None)

        # add various background types
        folium.TileLayer(tiles='OpenStreetMap', name='OpenStreetMap').add_to(m)
        #folium.TileLayer(tiles='Stamen Terrain', name='Stamen Terrain').add_to(m)
        #folium.TileLayer(tiles='Stamen Watercolor', name='Stamen Watercolor').add_to(m)
        #folium.TileLayer(tiles='CartoDB Positron', name='CartoDB Positron').add_to(m)
        #folium.TileLayer(tiles='CartoDB Dark_Matter', name='CartoDB Dark_Matter').add_to(m)

        # target city borders
        folium.GeoJson(data=border_poly,
                       name=args.target_lkr,
                       control=True).add_to(m)

        # plot the MultiPolygon as a map layer
        folium.GeoJson(data=aa_wsg84,
                       name='{}km radius'.format(args.max_range_km),
                       control=True).add_to(m)

        # add layer control
        folium.LayerControl().add_to(m)

        # save to a file
        m.save(folium_map_file)
        print('INFO: Folium map written into "{}"'.format(folium_map_file))

        if args.open_map:
            # attempt to launch file file
            webbrowser.open('file:///' + folium_map_file)


## entry point
if __name__ == '__main__':
    main(sys.argv[1:])
