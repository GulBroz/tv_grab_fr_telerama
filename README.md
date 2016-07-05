# tv_grab_fr_telerama

Grab French television listings from Télérama in XMLTV format.

## Authors

Mohamed El Morabity

## Usage

    tv_grab_fr_telerama.py --help
    tv_grab_fr_telerama.py [--config-file FILE] --configure
    tv_grab_fr_telerama.py [--config-file FILE] [--output FILE] [--days N] [--offset N]
    tv_grab_fr_telerama.py --description
    tv_grab_fr_telerama.py --capabilities
    tv_grab_fr_telerama.py --version

## Description

Output TV listings for several channels available in France and (partly) Europe. The data comes from guidetv-iphone.telerama.fr.

First run `tv_grab_fr_telerama.py --configure` to choose, which channels you want to download. Then running `tv_grab_fr_telerama.py` with no arguments will output listings in XML format to standard output.

    --configure

Ask for each available channel whether to download and write the configuration file.

    --config-file FILE

Set the name of the configuration file, the default is `~/.xmltv/tv_grab_fr_telerama.conf`. This is the file written by `--configure` and read when grabbing.

    --output FILE

Write to `FILE` rather than standard output.


    --days N

Grab `N` days. The default is 1.

    --offset N

Start `N` days in the future. The default is to start from now on (= 0).

    --capabilities

Show which capabilities the grabber supports. For more information, see http://wiki.xmltv.org/index.php/XmltvCapabilities.

    --description

Show the description of the grabber.

    --version

Show the version of the grabber.

    --help

Print a help message and exit.
