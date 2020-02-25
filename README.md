# DeleteMoveAfterPrint

[![Version](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=version&url=https://api.github.com/repos/OllisGit/OctoPrint-DeleteAfterPrint/releases&query=$[0].name)]()
[![Released](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=released&url=https://api.github.com/repos/OllisGit/OctoPrint-DeleteAfterPrint/releases&query=$[0].published_at)]()
![GitHub Releases (by Release)](https://img.shields.io/github/downloads/OllisGit/OctoPrint-DeleteAfterPrint/latest/total.svg)

Delete or **move** (*since V1.5.0+*) automatically the Print-Model:
* after successful print or if you want, also on canceled and failed prints
* after predefined days

#### Support my Efforts

This plugin, as well as my [other plugins](https://github.com/OllisGit/) were developed in my spare time.
If you like it, I would be thankful about a cup of coffee :)

[![More coffee, more code](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=6SW5R6ZUKLB5E&source=url)

## Details
The user can enable automatic deletion/movement after each print by using a checkbox in the sidebar.

If you want to delete/move files after a couple of days, use the Plugin-Settings. Deletion/Movement in done while opening OctoPrint.

**ATTENTION: There is no inquiry pop-up!!!**


![Sidebar](screenshots/sidebar.jpg)
![PluginSettings](screenshots/plugin-settings.jpg)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/OllisGit/OctoPrint-DeleteAfterPrint/releases/latest/download/master.zip

## Configuration

Settings can be edited in OctoPrint Plugin-Settings section.
