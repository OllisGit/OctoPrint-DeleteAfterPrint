# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.
import flask
import time
from datetime import datetime, timedelta
import octoprint.plugin
from operator import itemgetter
from octoprint.filemanager.destinations import FileDestinations
from octoprint.events import eventManager, Events

import octoprint.filemanager
import octoprint.filemanager.util
import octoprint.filemanager.storage


SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE = "deleteAfterPrintLastValue"
SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE= "deleteInSubFoldersLastValue"
SETTINGS_KEY_DAYS_LIMIT = "daysLimit"

DEFAULT_DELETEAFTERPRINT_VALUE = False
DEFAULT_INSUBFOLDER_VALUE = False


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
        self._deleteAfterPrintEnabled = DEFAULT_DELETEAFTERPRINT_VALUE
        self._deleteInSubFoldersEnabled = DEFAULT_INSUBFOLDER_VALUE

        self._deleteFile = False
        self.daysLimit = 0

    def initialize(self):
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self._logger.debug("rememberCheckBox: %s" % self.rememberCheckBox)

        if self.rememberCheckBox:
            deleteAfterPrintLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE])
            deleteInSubFoldersLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE])

            if deleteAfterPrintLastValue is not None:
                self._deleteAfterPrintEnabled = deleteAfterPrintLastValue
            if deleteInSubFoldersLastValue is not None:
                self._deleteInSubFoldersEnabled = deleteInSubFoldersLastValue


        daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])
        if daysLimit is not None:
            self.daysLimit = daysLimit



    # start/stop event-hook
    def on_event(self, event, payload):

        if event == Events.CLIENT_OPENED:
            # Send initial values to the frontend
            self._plugin_manager.send_plugin_message(self._identifier,
                                                     dict(deleteAfterPrintEnabled=self._deleteAfterPrintEnabled,
                                                          deleteInSubFoldersEnabled=self._deleteInSubFoldersEnabled))

            # is deletion after days activated
            daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])
            if daysLimit > 0:
                allFiles = self._file_manager.list_files(filter=self._historyFilterFunction)
                notificationMessage = ""

                for destination in allFiles:
                    allFileEntries = allFiles.get(destination)
                    for fileEntries in allFileEntries:
                        if len(fileEntries) > 0:
                            filename = fileEntries
                                #fileEntries.keys()[0]
                            if destination == FileDestinations.SDCARD:
                                self._printer.delete_sd_file(filename)
                            else:
                                self._file_manager.remove_file(destination, filename)
                            ## popup notifier
                            notificationMessage += "<li>" + filename + "</li>"
                            self._logger.info("File deleted '%s'." % filename)

                if notificationMessage:
                    notificationMessage = "<ul>" + notificationMessage + "</ul>"
                    self._plugin_manager.send_plugin_message(self._identifier,
                                                             dict(type="popup", message=notificationMessage))

        elif event == Events.PRINT_STARTED:
            self._logger.info("Printing started. Detailed progress started." + str(payload))

        elif event == Events.FILE_SELECTED:
            self._logger.info("File selected")

        elif event == Events.PRINT_DONE:
            self._logger.info("Printing succesfull!")
            if self._deleteAfterPrintEnabled:
                self._destination = payload.get("origin", "")
                #self._filename = payload.get("name", "")
                self._filename = payload.get("path", "")

                if self._deleteInSubFoldersEnabled == False and self._filename.find('/') != -1:
                    self._deleteFile = False
                else:
                    self._deleteFile = True

                    self._logger.info("Try unselect file")
                    for attempt in range(1, 5):
                        if self._printer.is_ready() == True:
                            break;
                        self._logger.info("...wait for printer being ready...attempt:"+str(attempt))
                        time.sleep(1)
                    self._logger.info("Ready:::" + str(self._printer.is_ready()))
                    self._printer.unselect_file()
                    self._logger.info("Unselect file")

        elif event == Events.METADATA_STATISTICS_UPDATED:
            if self._deleteFile:
                self._deleteFile = False
                # see files.py deleteGcodeFile API
                if self._destination == FileDestinations.SDCARD:
                    self._printer.delete_sd_file(self._filename)
                else:
                    self._file_manager.remove_file(self._destination, self._filename)
                self._logger.info("File deleted.")

    def _historyFilterFunction(self, entry, entry_data):
        history = entry_data.get("history")
        if history is not None:
            orderedList = sorted(history, key=itemgetter('timestamp'), reverse=True)
            if orderedList:
                lastEntry = orderedList[0]
                lastPrintTimestamp = lastEntry.get("timestamp")
                currentTime = time.time()
                currentDate = datetime.now()
                daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])
                limitDate = currentDate - timedelta(days=daysLimit)
                lastPrintDate = datetime.fromtimestamp(lastPrintTimestamp)

                if lastPrintDate < limitDate:
                    # to be delete
                    return entry

    def get_template_configs(self):
        return [dict(type="sidebar",
                     name="Automatic Deletion",
                     custom_bindings=False,
                     icon="trash"),
                dict(type="settings", custom_bindings=False)]

    def get_api_commands(self):
        #return dict(checkboxStates=["deleteAfterPrint", "deleteInSubFolders"])
        return dict(checkboxStates=[])

    def on_api_command(self, command, data):
        #if not user_permission.can():
        #    return make_response("Insufficient rights", 403)

        if command == "checkboxStates":
            if data.has_key("deleteAfterPrint"):
                self._deleteAfterPrintEnabled = bool(data["deleteAfterPrint"])
            if  data.has_key("deleteInSubFolders"):
                self._deleteInSubFoldersEnabled = bool(data["deleteInSubFolders"])

            if self.rememberCheckBox:
                self._settings.set_boolean([SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE],self._deleteAfterPrintEnabled)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE],self._deleteInSubFoldersEnabled)
                self._settings.save()
                eventManager().fire(Events.SETTINGS_UPDATED)

#        self._plugin_manager.send_plugin_message(self._identifier,
#                                                 dict(deleteAfterPrintEnabled=self._deleteAfterPrintEnabled,
#                                                      deleteInSubFoldersEnabled=self._deleteInSubFoldersEnabled))


    def on_api_get(self, request):
        action = request.values["action"]

        if "isResetSettingsEnabled" == action:
            return flask.jsonify(enabled="true")

        if "resetSettings" == action:
            self._settings.set([], self.get_settings_defaults())
            self._settings.save()
            return flask.jsonify(self.get_settings_defaults())

    # ~~ TemplatePlugin mixin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True)
        ]

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            rememberCheckBox=True,
            daysLimit=0,
            deleteAfterPrintLastValue = DEFAULT_DELETEAFTERPRINT_VALUE,
            deleteInSubFoldersLastValue = DEFAULT_INSUBFOLDER_VALUE
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self.daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])

    ##~~ AssetPlugin mixin
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/DeleteAfterPrint.js",
                "js/ResetSettingsUtil.js"],
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
