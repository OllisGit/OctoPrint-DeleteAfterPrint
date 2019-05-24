# DeleteAfterPrint

[![Version](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=version&url=https://api.github.com/repos/OllisGit/OctoPrint-DeleteAfterPrint/releases&query=$[0].name)]()
[![Released](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=released&url=https://api.github.com/repos/OllisGit/OctoPrint-DeleteAfterPrint/releases&query=$[0].published_at)]()
![GitHub Releases (by Release)](https://img.shields.io/github/downloads/OllisGit/OctoPrint-DeleteAfterPrint/latest/total.svg)

Delete automatically the Print-Model: 
* after successful print. If the print fails, the deletion is not executed!
* after predefined days

The user can enable automatic deletion after each print by using a checkbox in the sidebar.

If you want to delete files after a couple of days, use the Plugin-Settings. Deletion in done while opening OctoPrint.

**ATTENTION: There is no confirmation pop-up!!!** 



![Sidebar](screenshots/sidebar.jpg)
![PluginSettings](screenshots/plugin-settings.jpg)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/OllisGit/OctoPrint-DeleteAfterPrint/archive/master.zip


## Configuration

Settings can be edited in OctoPrint Plugin-Settings section.
