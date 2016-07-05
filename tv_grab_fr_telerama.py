#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright 2015, 2016 Mohamed El Morabity
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


'''
tv_grab_fr_telerama.py - Grab French television listings from Télérama in XMLTV format
'''

import argparse
import datetime
import os
import pytz
import re
import sys
import urllib.request
import xml.etree.ElementTree


DESCRIPTION = 'France (Télérama)'
VERSION = '0.1'
CAPABILITIES = ['baseline', 'manualconfig']

TELERAMA_USER_AGENT = 'Telerama/1.2 CFNetwork/459 Darwin/10.0.0d3'
TELERAMA_ENCODING = 'windows-1252'
DEFAULT_DAYS = 1
DEFAULT_OFFSET = 0
MAX_FETCH_DAYS = 11
CONFIG_FILE = os.path.join(
    os.environ['HOME'],
    '.xmltv',
    os.path.splitext(os.path.basename(__file__))[0] + '.conf'
)


def print_description():
    '''Print the description of the grabber'''

    print(DESCRIPTION)


def print_version():
    '''Print the version of the grabber'''

    print(VERSION)


def print_capabilities():
    '''Print the capabilities of the grabber'''

    for c in CAPABILITIES:
        print(c)


def telerama_to_xmltv_id(channel_id):
    '''Convert a Télérama channel ID to a valid XMLTV channel ID'''

    return channel_id + '.tv.telerama.fr'


def xmltv_to_telerama_id(channel_id):
    '''Get the Télérama channel ID from the XMLTV channel ID'''

    return channel_id.replace('.tv.telerama.fr', '')


def translate_categories(category):
    '''Translate Télérama program categories to categories from the ETSI standard EN 300 468'''

    categories = {
        "Ballet": "Music / Ballet / Dance",
        "Clips": "Music / Ballet / Dance",
        "Concert": "Music / Ballet / Dance",
        "Débat": "Talk show",
        "Dessin animé": "Cartoons / Puppets",
        "Divers": "",
        "Divertissement": "Variety show",
        "Documentaire": "Documentary",
        "Émission": "",
        "Emission du bien-être": "Fitness and health",
        "Emission du bien-êtr": "Fitness and health",
        "Feuilleton": "Soap / Melodrama / Folkloric",
        "Feuilleton sentimental": "Romance",
        "Film": "Movie / Drama",
        "Fin": "",
        "Fitness": "Fitness and health",
        "Interview": "Discussion / Interview / Debate",
        "Jeu": "Game show / Quiz / Contest",
        "Jeunesse": "Children's / Youth programmes",
        "Journal": "News / Current affairs",
        "Loterie": "Game show / Quiz / Contest",
        "Magazine": "Magazines / Reports / Documentary",
        "Météo": "News / Weather report",
        "Opéra": "Musical / Opera",
        "Politique": "Social / Political issues / Economics",
        "Religion": "Religion",
        "Série": "Movie / Drama",
        "Spectacle": "Performing arts",
        "Sport": "Sports",
        "Talk show": "Talk show",
        "Téléfilm": "Movie / Drama",
        "Téléréalité": "Variety show",
        "Théâtre": "Performing arts",
        "Tiercé": "Sports",
        "Variétés": "Variety show",
        "Voyance": "Leisure hobbies"
    }

    if category in categories:
        return categories[category]

    print("Unmanaged category: {}".format(category), file=sys.stderr)
    return ''


def split_outside_delimiters(string, separator, delimiter1, delimiter2):
    '''Split a string into a string array using the specified separator string,
    except when the separator is between the specified delimiters'''

    result = []
    n, s, d1, d2 = len(string), len(separator), len(delimiter1), len(delimiter2)
    tmp = ''
    level = 0
    i = 0
    while i < n:
        if string[i:i + s] == separator and level == 0:
            result.append(tmp)
            tmp = ''
            i += s
        else:
            if string[i:i + d1] == delimiter1:
                level += 1
            elif string[i:i + d2] == delimiter2:
                level -= 1
            tmp += string[i]
            i += 1
    result.append(tmp)

    return result


def get_telerama_programs(channel_id, date=datetime.date.today()):
    '''Get the Télérama programs for a given channel and a given day '''

    url = "http://guidetv-iphone.telerama.fr/verytv/procedures/LitProgrammes1Chaine.php?date={:%Y-%m-%d}&chaine={}".format(date, xmltv_to_telerama_id(channel_id))
    opener = urllib.request.Request(url, headers={'User-agent': TELERAMA_USER_AGENT})
    with urllib.request.urlopen(opener) as response:
        content = response.read().decode(TELERAMA_ENCODING)
        return content.split(':$$$:')[:-1]


def get_available_channels():
    '''Get all available channels in Télérama data'''

    url = 'http://guidetv-iphone.telerama.fr/verytv/procedures/ListeChaines.php'
    opener = urllib.request.Request(url, headers={'User-agent': TELERAMA_USER_AGENT})
    with urllib.request.urlopen(opener) as response:
        content = response.read().decode(TELERAMA_ENCODING)[:-5]
        channels = {}
        for i in content.split(':$$$:')[:-1]:
            c = i.split('$$$')
            if len(c) != 2 or c[1] == '':
                continue
            channels[telerama_to_xmltv_id(c[0])] = c[1]
        return channels


def write_configuration(channels, output_file=CONFIG_FILE):
    '''Write specified channels to the specified configuration file'''

    config_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(config_dir):
        os.mkdir(config_dir)

    with open(output_file, 'w') as config:
        for c in channels:
            print('channel=' + c, file=config)


def load_configuration(input_file=CONFIG_FILE):
    '''Load channels from the specified configuration file'''

    channels = []
    with open(input_file, 'r') as config:
        for l in config:
            m = re.search(r'^channel=(.*)$', l)
            if m:
                channels.append(m.group(1))
    return channels


def write_xmltv_data(channels, days=1, offset=0, output_file='/dev/stdout'):
    '''Get TV programs in XMLTV for the specified channels and for a given number of days'''

    output = xml.etree.ElementTree.ElementTree()
    root = xml.etree.ElementTree.Element(
        'tv',
        attrib={
            'generator-info-name': 'tv_grab_fr_telerama',
            'source-info-name': 'Télérama',
            'source-info-url': 'http://guidetv-iphone.telerama.fr/'
        }
    )
    output._setroot(root)

    telerama_programs = []
    for i in range(0, days):
        for channel_id in channels:
            telerama_programs.append(
                get_telerama_programs(channel_id, datetime.date.today()
                                      + datetime.timedelta(days=i + offset))
            )

    france_tz = pytz.timezone('Europe/Paris')
    for programs in telerama_programs:
        for program in programs:
            data = [i.strip() for i in program.split('$$$')]

            # Channel ID
            channel_id = telerama_to_xmltv_id(data[0])
            if root.find('channel[@id="{}"]'.format(channel_id)) is None:
                channel_xml = xml.etree.ElementTree.Element('channel', attrib={'id': channel_id})
                displayname_xml = xml.etree.ElementTree.Element('display-name')
                displayname_xml.text = data[1]
                channel_xml.append(displayname_xml)
                root.insert(0, channel_xml)

            # Start and stop time, for the current timezone
            start = france_tz.localize(
                datetime.datetime.strptime(data[12] + ' ' + data[3], '%d/%m/%Y %H:%M:%S')
            )
            stop = france_tz.localize(
                datetime.datetime.strptime(data[12] + ' ' + data[4], '%d/%m/%Y %H:%M:%S')
            )
            if start > stop:
                stop += datetime.timedelta(days=1)

            program_xml = xml.etree.ElementTree.Element(
                'programme',
                attrib={
                    'start': "{:%Y%m%d%H%M%S %z}".format(start),
                    'stop': "{:%Y%m%d%H%M%S %z}".format(stop),
                    'channel': telerama_to_xmltv_id(data[0])
                }
            )

            # Showview
            m = re.search(r'^Showview :\s*(.+)\s*$', data[7], re.MULTILINE)
            if m:
                program_xml.set('showview', m.group(1))

            # Title
            title_xml = xml.etree.ElementTree.Element('title')
            title_xml.text = data[2]
            program_xml.append(title_xml)

            # Sub-title
            m = re.search(r'^Sous-titre :\s*(.+)\s*$', data[7], re.MULTILINE)
            if m:
                subtitle_xml = xml.etree.ElementTree.Element('sub-title')
                subtitle_xml.text = m.group(1)
                program_xml.append(subtitle_xml)

            # Description
            if data[6] != '':
                desc_xml = xml.etree.ElementTree.Element('desc')
                desc_xml.text = data[6]
                program_xml.append(desc_xml)

            m_directors = re.search(r'^Réalisateur :\s*(.+)\s*$', data[7], re.MULTILINE)
            m_actors = re.search(r'^Acteurs :\s*(.+)\s*$', data[7], re.MULTILINE)
            m_composers = re.search(r'^Musique :\s*(.+)\s*$', data[7], re.MULTILINE)
            m_presenters = re.search(r'^Présentateur :\s*(.+)\s*$', data[7], re.MULTILINE)
            m_guests = re.search(r'^Invités :\s*(.+)\s*$', data[7], re.MULTILINE)

            if m_directors or m_actors or m_composers or m_presenters or m_guests:
                credits_xml = xml.etree.ElementTree.Element('credits')

                # Directors
                if m_directors:
                    for director in split_outside_delimiters(m_directors.group(1), ', ', '(', ')'):
                        director_xml = xml.etree.ElementTree.Element('director')
                        director_xml.text = director
                        credits_xml.append(director_xml)

                # Actors
                if m_actors:
                    for actor in split_outside_delimiters(m_actors.group(1), ', ', '(', ')'):
                        actor_xml = xml.etree.ElementTree.Element('actor')
                        m = re.search(r'(.*) \((.*)\)', actor)
                        if m:
                            actor_xml.text = m.group(1)
                            actor_xml.set('role', m.group(2))
                        else:
                            actor_xml.text = actor
                        credits_xml.append(actor_xml)

                # Composers
                if m_composers:
                    for composer in split_outside_delimiters(m_composers.group(1), ', ', '(', ')'):
                        composer_xml = xml.etree.ElementTree.Element('composer')
                        composer_xml.text = composer
                        credits_xml.append(composer_xml)

                # Presenters
                if m_presenters:
                    for presenter in split_outside_delimiters(m_presenters.group(1), ', ', '(', ')'):
                        presenter_xml = xml.etree.ElementTree.Element('presenter')
                        presenter_xml.text = presenter
                        credits_xml.append(presenter_xml)

                # Guests
                if m_guests:
                    for guest in split_outside_delimiters(m_guests.group(1), ', ', '(', ')'):
                        guest_xml = xml.etree.ElementTree.Element('guest')
                        guest_xml.text = guest
                        credits_xml.append(guest_xml)

                program_xml.append(credits_xml)

            # Year
            m = re.search(r'^Année :\s*(.+)\s*$', data[7], re.MULTILINE)
            if m:
                date_xml = xml.etree.ElementTree.Element('date')
                date_xml.text = m.group(1)
                program_xml.append(date_xml)

            # Categories
            category = translate_categories(data[5])
            if category != '':
                category_xml = xml.etree.ElementTree.Element('category')
                category_xml.text = category
                program_xml.append(category_xml)
            # Original French categories are added also
            if data[5] != '':
                category_xml = xml.etree.ElementTree.Element('category', attrib={'lang': 'fr'})
                category_xml.text = data[5]
                program_xml.append(category_xml)
            # Read program genres as categories
            m = re.search(r'^Genre :\s*(.+)\s*$', data[7], re.MULTILINE)
            if m and m.group(1) != data[5]:
                category_xml = xml.etree.ElementTree.Element('category', attrib={'lang': 'fr'})
                category_xml.text = m.group(1)
                program_xml.append(category_xml)

            # Thumbnail
            program_xml.append(
                xml.etree.ElementTree.Element(
                    'icon',
                    attrib={'src': "http://guidetv-iphone.telerama.fr/verytv/procedures/images/{:%Y-%m-%d}_{}_{:%H:%M}.jpg".format(start, data[0], start)}
                )
            )

            # Episode/season
            episode = 0
            m = re.search(r'^Episode :\s*([0-9]+)(?:/([0-9]+))?\s*$', data[7], re.MULTILINE)
            if m:
                season = 0
                n = re.search(r'^Saison :\s*([0-9]+)\s*$', data[7], re.MULTILINE)
                if n:
                    season = int(n.group(1)) - 1

                episode = int(m.group(1)) - 1
                episode_data = "{}.{}".format(season, episode)
                if m.group(2) is not None:
                    episode_data += '/' + m.group(2)
                episode_data += '.0/1'
                episodenum_xml = xml.etree.ElementTree.Element(
                    'episode-num',
                    attrib={'system': 'xmltv_ns'}
                )
                episodenum_xml.text = episode_data
                program_xml.append(episodenum_xml)

            # Video format
            video_xml = xml.etree.ElementTree.Element('video')
            m = re.search(r'^En (16:9|4:3)', data[7], re.MULTILINE)
            video_aspect_xml = xml.etree.ElementTree.Element('aspect')
            video_aspect_xml.text = m.group(1)
            video_xml.append(video_aspect_xml)
            m = re.search(r'^HD$', data[7], re.MULTILINE)
            if m:
                video_quality_xml = xml.etree.ElementTree.Element('quality')
                video_quality_xml.text = 'HDTV'
                video_xml.append(video_quality_xml)

            # Program audio format
            stereo = ''
            if re.search(r'^En Dolby 5\.1', data[7], re.MULTILINE):
                stereo = 'surround'
            elif re.search(r'^En Dolby', data[7], re.MULTILINE):
                stereo = 'dolby'
            elif re.search(r'^Stéréo', data[7], re.MULTILINE):
                stereo = 'stereo'
            if stereo != '':
                audio_xml = xml.etree.ElementTree.Element('audio')
                stereo_xml = xml.etree.ElementTree.Element('stereo')
                stereo_xml.text = stereo
                audio_xml.append(stereo_xml)
                program_xml.append(audio_xml)

            # Check whether the program was previously shown
            if re.search('^Rediffusion', data[7], re.MULTILINE):
                program_xml.append(xml.etree.ElementTree.Element('previously-shown'))

            # Check whether the program is a premiere
            m = re.search('^(Inédit|Première diffusion)', data[7], re.MULTILINE)
            if m:
                premiere_xml = xml.etree.ElementTree.Element('premiere', attrib={'lang': 'fr'})
                premiere_xml.text = m.group(0)
                program_xml.append(premiere_xml)

            # Subtitles availability
            subtitles = ''
            if re.search('^VOST', data[7], re.MULTILINE):
                subtitles = 'onscreen'
            elif re.search('^Sous-titré', data[7], re.MULTILINE):
                subtitles = 'teletext'
            if subtitles != '':
                subtitles_xml = xml.etree.ElementTree.Element(
                    'subtitles',
                    attrib={'type': subtitles}
                )
                program_xml.append(subtitles_xml)

            # Ratings
            if data[8] != '0':
                rating_xml = xml.etree.ElementTree.Element('rating')
                value_xml = xml.etree.ElementTree.Element('value')
                value_xml.text = data[8]
                rating_xml.append(value_xml)
                program_xml.append(rating_xml)

            if data[10] == '1' or data[10] == '2' or data[10] == '3':
                starrating_xml = xml.etree.ElementTree.Element('star-rating')
                value_xml = xml.etree.ElementTree.Element('value')
                value_xml.text = data[10] + '/3'
                starrating_xml.append(value_xml)
                program_xml.append(starrating_xml)

            # Reviews
            if data[11] != '':
                review_xml = xml.etree.ElementTree.Element(
                    'review',
                    attrib={'type': 'text', 'lang': 'fr'}
                )
                review_xml.text = data[11]
                program_xml.append(review_xml)

            root.append(program_xml)

    output.write(output_file, encoding='UTF-8', xml_declaration=True)


def configure(config_file=CONFIG_FILE):
    '''Ask for Télérama channels to configure and write them into the specified
       configuration file'''

    available_channels = get_available_channels()
    channels = []
    select_all = False
    select_none = False
    print('Select the channels that you want to receive data for.')
    for channel_id, channel_name in available_channels.items():
        if not select_all and not select_none:
            answer = ''
            while True:
                answer = input(channel_name + ' [yes,no,all,none (default=no)] ').strip()
                if answer in ['', 'yes', 'no', 'all', 'none']:
                    break
                print('invalid response, please choose one of yes,no,select_all,select_none\n')
            select_all = answer == 'all'
            select_none = answer == 'none'
        if select_all or answer == 'yes':
            channels.append(channel_id)
        if select_all:
            print(channel_name + ' yes')
        elif select_none:
            print(channel_name + ' no')

    write_configuration(channels, config_file)


parser = argparse.ArgumentParser(description='get French television listings from Télérama in XMLTV format')
parser.add_argument(
    '--description',
    action='store_true',
    help='print the description for this grabber')
parser.add_argument(
    '--version',
    action='store_true',
    help='show the version of this grabber'
)
parser.add_argument(
    '--capabilities',
    action='store_true',
    help='show the capabilities this grabber supports'
)
parser.add_argument(
    '--configure',
    action='store_true',
    help='generate the configuration file by asking the users which channels to grab'
)
parser.add_argument(
    '--days',
    type=int,
    help='grab DAYS days of TV data (default: {0})'.format(DEFAULT_DAYS)
)
parser.add_argument(
    '--offset',
    type=int,
    help='grab TV data starting at OFFSET days in the future (default: {0})'.format(DEFAULT_OFFSET)
)
parser.add_argument(
    '--output',
    help='write the XML data to OUTPUT instead of the standard output'
)
parser.add_argument(
    '--config-file',
    help='file name to write/load the configuration to/from. Default is ' + CONFIG_FILE
)
args = parser.parse_args()

config_file = args.config_file or CONFIG_FILE

if args.version:
    print_version()
    sys.exit()

if args.description:
    print_description()
    sys.exit()

if args.capabilities:
    print_capabilities()
    sys.exit()

if args.configure:
    configure(config_file)
    sys.exit()

output_file = args.output or '/dev/stdout'

offset = args.offset or DEFAULT_OFFSET

days = args.days or DEFAULT_DAYS
if offset + days > MAX_FETCH_DAYS:
    days = MAX_FETCH_DAYS - offset

if not os.path.isfile(config_file):
    print('You need to configure the grabber by running it with --configure')
    sys.exit(1)

write_xmltv_data(load_configuration(config_file), days, offset, output_file)
