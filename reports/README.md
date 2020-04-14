# Report PDF creation

In this module reports are created on the website and can be downloaded as PDF's.

## Prerequisites

- wkhtmltopdf

## Installing wkhtmltopdf on Linux

Installing wkhtmltopdf on a linux server has shown to be combersome for several reasons.
Initially it can not find a display server, however the online solution to this answer
reults in the page being exported on the wrong size, no matter the settings of zoom and dpi.
It turns out this can be solved by calling --disable-smart-shrinking. But this throws a new problem.

The key give-away is as follows: DO NOT USE APT-GET! Instead download from the source:

- `sudo apt -y install wget`
- `wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb`
- `sudo dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb`
- `sudo apt -f install` 

