# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.
import time
import os
import octoprint.plugin
from octoprint.filemanager.destinations import FileDestinations
from octoprint.events import eventManager, Events

import octoprint.filemanager
import octoprint.filemanager.util
import octoprint.filemanager.storage

class DeleteAfterPrintPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    # my stuff
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.StartupPlugin
):

    def __init__(self):
        self.rememberCheckBox = False
        self.lastCheckBoxValue = False
        self._deleteAfterPrintEnabled = False

        self._deleteFile = False

    def initialize(self):
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self._logger.debug("rememberCheckBox: %s" % self.rememberCheckBox)

        self.lastCheckBoxValue = self._settings.get_boolean(["lastCheckBoxValue"])
        self._logger.debug("lastCheckBoxValue: %s" % self.lastCheckBoxValue)
        if self.rememberCheckBox:
            self._deleteAfterPrintEnabled = self.lastCheckBoxValue

    # start/stop event-hook
    def on_event(self, event, payload):

        if event == Events.CLIENT_OPENED:
            self._plugin_manager.send_plugin_message(self._identifier,
                                                     dict(deleteAfterPrintEnabled=self._deleteAfterPrintEnabled))
            return

        if event == Events.PRINT_STARTED:
            self._logger.info("Printing started. Detailed progress started." + str(payload))

        elif event == Events.PRINT_DONE:
            self._logger.info("Printing succesfull!")
            if self._deleteAfterPrintEnabled:
                self._logger.info("Try unselect file")
                time.sleep(2)
                #self._logger.info("Busy:::" + self._printer.isBusy() + " Streaming:::" + self._printer.isStreaming())
                self._printer.unselect_file()
                time.sleep(2)
                self._logger.info("Unselect file")

                self._destination = payload.get("origin", "")
                self._filename = payload.get("name", "")
                self._deleteFile = True

        elif event == Events.METADATA_STATISTICS_UPDATED:
            if self._deleteFile:
                self._deleteFile = False
                # see files.py deleteGcodeFile API
                if self._destination == FileDestinations.SDCARD:
                    self._printer.delete_sd_file(self._filename)
                else:
                    self._file_manager.remove_file(self._destination, self._filename)
                self._logger.info("File deleted.")

    def get_template_configs(self):
        return [dict(type="sidebar",
                     name="Automatic Deletion",
                     custom_bindings=False,
                     icon="trash"),
                dict(type="settings", custom_bindings=False)]
## fa-trash-o

    def get_api_commands(self):
        return dict(enable=[],
                    disable=[],
                    abort=[])

    def on_api_command(self, command, data):
        #if not user_permission.can():
        #    return make_response("Insufficient rights", 403)

        if command == "enable":
            self._deleteAfterPrintEnabled = True
        elif command == "disable":
            self._deleteAfterPrintEnabled = False

        if command == "enable" or command == "disable":
            self.lastCheckBoxValue = self._deleteAfterPrintEnabled
            if self.rememberCheckBox:
                self._settings.set_boolean(["lastCheckBoxValue"], self.lastCheckBoxValue)
                self._settings.save()
                eventManager().fire(Events.SETTINGS_UPDATED)

        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(deleteAfterPrintEnabled=self._deleteAfterPrintEnabled))

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            rememberCheckBox=False,
            lastCheckBoxValue=False
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self.lastCheckBoxValue = self._settings.get_boolean(["lastCheckBoxValue"])

    ##~~ AssetPlugin mixin
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/DeleteAfterPrint.js"],
            css=["css/DeleteAfterPrint.css"],
            less=["less/DeleteAfterPrint.less"]
        )

    ##~~ Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            DeleteAfterPrint=dict(
                displayName="DeleteAfterPrint Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="OllisGit",
                repo="OctoPrint-DeleteAfterPrint",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/OllisGit/OctoPrint-DeleteAfterPrint/archive/{target_version}.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "DeleteAfterPrint Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = DeleteAfterPrintPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
