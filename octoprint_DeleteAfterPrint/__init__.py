# coding=utf-8
from __future__ import absolute_import

import re

import flask
import time
from datetime import datetime, timedelta
import octoprint.plugin
from operator import itemgetter

from flask import jsonify
from octoprint.filemanager.destinations import FileDestinations

from octoprint.events import eventManager, Events

SETTINGS_KEY_NOTIFICATION_AFTER_PRINT = "nofificationAfterPrintCheckbox"
SETTINGS_KEY_NOTIFICATION_HIDE_AFTER_TIME = "nofificationHideAfterTimeCheckbox"

SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE = "deleteAfterPrintLastValue"
SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE= "deleteInSubFoldersLastValue"

SETTINGS_KEY_DELETE_WHEN_FAILED_LASTVALUE= "deleteWhenFailedLastValue"
SETTINGS_KEY_DELETE_WHEN_CANCELED_LASTVALUE= "deleteWhenCanceledLastValue"

SETTINGS_KEY_DAYS_LIMIT = "daysLimit"

SETTINGS_KEY_DELETE_MOVE_METHODE = "deleteMoveMethode"
SETTINGS_KEY_MOVE_FOLDER = "moveFolder"

METHODE_DELETE = "delete"
METHODE_MOVE = "move"

DEFAULT_DELETEAFTERPRINT_VALUE = False
DEFAULT_INSUBFOLDER_VALUE = False
DEFAULT_WHENPRINT_FAILED_VALUE = False
DEFAULT_WHENPRINT_CANCELED_VALUE = False
DEFAULT_DELETE_MOVE_METHODE = METHODE_DELETE
DEFAULT_MOVE_FOLDER = "_archive"


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

        self._deleteWhenPrintFailed = DEFAULT_WHENPRINT_FAILED_VALUE
        self._deleteWhenPrintCanceled = DEFAULT_WHENPRINT_CANCELED_VALUE

        self._deleteFile = False
        self.daysLimit = 0

    def initialize(self):
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self._logger.debug("rememberCheckBox: %s" % self.rememberCheckBox)

        if self.rememberCheckBox:
            deleteAfterPrintLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE])
            deleteInSubFoldersLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE])
            deleteWhenPrintFailedLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_WHEN_FAILED_LASTVALUE])
            deleteWhenPrintCanceledLastValue  = self._settings.get_boolean([SETTINGS_KEY_DELETE_WHEN_CANCELED_LASTVALUE])

            if deleteAfterPrintLastValue is not None:
                self._deleteAfterPrintEnabled = deleteAfterPrintLastValue
            if deleteInSubFoldersLastValue is not None:
                self._deleteInSubFoldersEnabled = deleteInSubFoldersLastValue
            if deleteWhenPrintFailedLastValue is not None:
                self._deleteWhenPrintFailed = deleteWhenPrintFailedLastValue
            if deleteWhenPrintCanceledLastValue is not None:
                self._deleteWhenPrintCanceled = deleteWhenPrintCanceledLastValue

        daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])
        if daysLimit is not None:
            self.daysLimit = daysLimit

    # start/stop event-hook
    def on_event(self, event, payload):

        if event == Events.CLIENT_OPENED:
            # Send initial values to the frontend
            self._sendViewModelToClient()

            # is deletion after days activated
            daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])
            if (daysLimit > 0):
                from octoprint import __display_version__
                allFiles = {}
                # filter methode signature is changed in OP 1.5+
                if (__display_version__.startswith("1.4") or __display_version__.startswith("1.3")):
                    allFiles = self._file_manager.list_files(filter=self._historyFilterFunction)
                else:
                    allFiles = self._file_manager.list_files(filter=self._historyFilterFunction15)

                notificationMessage = ""

## @nur für local ein move durchführen sonst nicht vorher testen
                deleteMoveMethode = self._settings.get([SETTINGS_KEY_DELETE_MOVE_METHODE])

                for destination in allFiles:

                    if (deleteMoveMethode and (deleteMoveMethode == METHODE_MOVE) and destination == FileDestinations.SDCARD):
                        #no move for SD-Card
                        continue
                    allFileEntries = allFiles.get(destination)
                    for fileEntries in allFileEntries:
                        if len(fileEntries) > 0:
                            filename = fileEntries

                            self._deleteOrMoveFile(destination, filename)

                            #if destination == FileDestinations.SDCARD:
                            #    self._printer.delete_sd_file(filename)
                            #else:
                            #    self._file_manager.remove_file(destination, filename)

                            ## popup notifier
                            notificationMessage += "<li>" + filename + "</li>"


                if notificationMessage:
                    notificationMessage = "<ul>" + notificationMessage + "</ul>"

                    ## MOVE
                    if (deleteMoveMethode and (deleteMoveMethode == METHODE_MOVE)):
                        self._sendPopupMessageToClient('info', "File(s) moved to '"+self._settings.get(
                            [SETTINGS_KEY_MOVE_FOLDER])+"'!", notificationMessage)
                    ## DELETE
                    if (deleteMoveMethode and (deleteMoveMethode == METHODE_DELETE)):
                        self._sendPopupMessageToClient('info', "File(s) deleted!", notificationMessage)

        elif event == Events.PRINT_STARTED:
            self._logger.info("Printing started. Detailed progress started." + str(payload))

        elif event == Events.FILE_SELECTED:
            self._logger.info("File selected")


        elif self._deleteAfterPrintEnabled and ( \
             event == Events.PRINT_DONE or \
             (event == Events.PRINT_FAILED  and self._deleteWhenPrintFailed)or \
             (event == Events.PRINT_CANCELLED and self._deleteWhenPrintCanceled) \
            ):
            self._logger.info("Printing finished!")

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
                #reset
                self._deleteFile = False

                if (self._settings.get([SETTINGS_KEY_NOTIFICATION_AFTER_PRINT]) == True):
                    deleteMoveMethode = self._deleteOrMoveFile(self._destination, self._filename)
                    # move or delete
                    if (deleteMoveMethode and (deleteMoveMethode == METHODE_MOVE)):
                        msg = "File '" + self._filename + "' moved to folder '" + self._settings.get([SETTINGS_KEY_MOVE_FOLDER]) + "'"
                        self._sendPopupMessageToClient('info', "File is moved!", msg)
                    if (deleteMoveMethode and (deleteMoveMethode == METHODE_DELETE)):
                        ## DELETE - FILE
                        msg = self._filename
                        self._sendPopupMessageToClient('info', "File is deleted!", msg)

    def _deleteOrMoveFile(self, destination, filename):
        # should this file excluded
        if (self._settings.get_boolean(["excludeFilenameCheckbox"])):
            excludePatterns = self._settings.get(["excludeFilenamePattern"])
            if (self._isFileNameExcluded(filename, excludePatterns) == True):
                self._logger.info("File '" + filename + "' is excluded and not deleted/moved.")
                self._sendPopupMessageToClient('info', "File was excluded from delete/move!", self._filename)
                return ""

        # move or delete
        deleteMoveMethode = self._settings.get([SETTINGS_KEY_DELETE_MOVE_METHODE])
        if (deleteMoveMethode and (deleteMoveMethode == METHODE_MOVE)):
            ## MOVE - FILE
            if destination == FileDestinations.SDCARD:
                # move for sd-card not supported
                self._sendPopupMessageToClient('error', "Not supported!",
                                               "Move files on SD-Card is not supported. Please create an issue if you need this feature!")
                deleteMoveMethode = None
            else:
                moveToFolder = self._getMoveFolder()
                self._file_manager.move_file(FileDestinations.LOCAL, filename, moveToFolder + "/" + filename)
                self._logger.info("File '" + filename + "' is moved to folder '" + moveToFolder + "'!")
        else:
            ## DELETE - FILE
            # see files.py deleteGcodeFile API
            if (destination == FileDestinations.SDCARD):
                self._printer.delete_sd_file(filename)
            else:
                self._file_manager.remove_file(destination, filename)
            self._logger.info("File '" + filename + "' deleted.")
        return deleteMoveMethode

    #type: 'notice', 'info', 'success', or 'error'
    def _sendPopupMessageToClient(self, type, title, popUpMessage):

        # should the message disappear after some time
        shouldPopupHide = self._settings.get_boolean([SETTINGS_KEY_NOTIFICATION_HIDE_AFTER_TIME])
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(
                                                     hide_type=shouldPopupHide,
                                                     message_type=type,
                                                      message_title=title,
                                                      message_text=popUpMessage))

    def _sendViewModelToClient(self):

        selectedDeleteMoveOption = ""
        if (self._deleteAfterPrintEnabled == False):
            selectedDeleteMoveOption = "[DO NOTHING]"
        else:
            if (self._settings.get([SETTINGS_KEY_DELETE_MOVE_METHODE]) == METHODE_DELETE):
                selectedDeleteMoveOption = "[DELETE FILE]"
            else:
                selectedDeleteMoveOption = self._getMoveFolder()

        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(
                                                     deleteAfterPrintEnabled=self._deleteAfterPrintEnabled,
                                                     deleteInSubFoldersEnabled=self._deleteInSubFoldersEnabled,
                                                     deleteWhenFailedEnabled=self._deleteWhenPrintFailed,
                                                     deleteWhenCanceledEnabled=self._deleteWhenPrintCanceled,
                                                     selectedDeleteMoveOption=selectedDeleteMoveOption
                                                    )
                                                 )

    def _getMoveFolder(self):
        movedFolder = self._settings.get([SETTINGS_KEY_MOVE_FOLDER])
        if (movedFolder[0] != "/"):
            movedFolder = "/" + movedFolder
        return movedFolder

    # Methode signature was changed since OP 1.5
    def _historyFilterFunction15(self, node):
        entry_name = node["name"]
        entry_data = node
        filteredEntry = self._historyFilterFunction(entry_name, entry_data)
        return filteredEntry

    def _historyFilterFunction(self, entry_name, entry_data):
        history = entry_data.get("history")
        entryType = entry_data["type"]
        # START: WORKAROUND
        if (entryType == "folder"):
            entry_data["type"] = "myfolderfix"
        # STOP: WORKAROUND
        if (history is not None and entryType == "machinecode"):
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
                    return entry_name

    def _isFileNameExcluded(self, filenameToTest, excludePatterns):

        result = False
        if (len(excludePatterns) != 0 and len(filenameToTest) != 0):
            allExcludePatterns = excludePatterns.split("\n")
            for exPattern in allExcludePatterns:
                if (len(exPattern.strip()) == 0):
                    continue


                exPattern = re.compile(exPattern)
                if (exPattern.fullmatch(filenameToTest)):
                    # should be excluded
                    result = True
                    break

        return result

    def get_api_commands(self):
        #return dict(checkboxStates=["deleteAfterPrint", "deleteInSubFolders"])
        return dict(checkboxStates=[],
                    testExcludePatterns=[])

    def on_api_command(self, command, data):
        #if not user_permission.can():
        #    return make_response("Insufficient rights", 403)

        if command == "checkboxStates":
            if "deleteAfterPrint" in data:
                self._deleteAfterPrintEnabled = bool(data["deleteAfterPrint"])
            if  "deleteInSubFolders" in data:
                self._deleteInSubFoldersEnabled = bool(data["deleteInSubFolders"])
            if  "deleteWhenPrintFailed" in data:
                self._deleteWhenPrintFailed = bool(data["deleteWhenPrintFailed"])
            if  "deleteWhenPrintCanceled" in data:
                self._deleteWhenPrintCanceled = bool(data["deleteWhenPrintCanceled"])

            if self.rememberCheckBox:
                if ("selectedDeleteMoveOption" in data):
                    selectedDeleteMoveOption = data["selectedDeleteMoveOption"]

                    if (selectedDeleteMoveOption == "[DO NOTHING]"):
                        self._deleteAfterPrintEnabled = False
                    if (selectedDeleteMoveOption == "[DELETE FILE]"):
                        self._deleteAfterPrintEnabled = True
                        self._settings.set([SETTINGS_KEY_DELETE_MOVE_METHODE], METHODE_DELETE)

                    if (selectedDeleteMoveOption != "[DO NOTHING]" and selectedDeleteMoveOption != "[DELETE FILE]"):
                        self._deleteAfterPrintEnabled = True
                        self._settings.set([SETTINGS_KEY_DELETE_MOVE_METHODE], METHODE_MOVE)
                        self._settings.set([SETTINGS_KEY_MOVE_FOLDER], selectedDeleteMoveOption)


                self._settings.set_boolean([SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE], self._deleteAfterPrintEnabled)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE], self._deleteInSubFoldersEnabled)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_WHEN_FAILED_LASTVALUE], self._deleteWhenPrintFailed)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_WHEN_CANCELED_LASTVALUE], self._deleteWhenPrintCanceled)
            else:
                # set default values again
                self._settings.set_boolean([SETTINGS_KEY_DELETE_AFTER_PRINT_LASTVALUE], DEFAULT_DELETEAFTERPRINT_VALUE)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_IN_SUBFOLDERS_LASTVALUE], DEFAULT_INSUBFOLDER_VALUE)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_WHEN_FAILED_LASTVALUE], DEFAULT_WHENPRINT_FAILED_VALUE)
                self._settings.set_boolean([SETTINGS_KEY_DELETE_WHEN_CANCELED_LASTVALUE], DEFAULT_WHENPRINT_CANCELED_VALUE)
                self._settings.set([SETTINGS_KEY_DELETE_MOVE_METHODE], DEFAULT_DELETE_MOVE_METHODE)
                self._settings.set([SETTINGS_KEY_MOVE_FOLDER], DEFAULT_MOVE_FOLDER)

            self._settings.save()
            eventManager().fire(Events.SETTINGS_UPDATED)

        if (command == "testExcludePatterns"):
            filenameToTest = data["filenameToTest"]
            excludePatterns = data["excludePatterns"]
            matchResult = self._isFileNameExcluded(filenameToTest, excludePatterns)
            resultText = ""
            if (matchResult == True):
                resultText = "Filename '"+filenameToTest+"' will be excluded"
            else:
                resultText = "Filename '"+filenameToTest+"' will NOT be exclude -> deleted/moved"

            result = {
                "result": resultText
            }
            return jsonify(result)

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
        return [dict(type="sidebar",
                     name="Delete/Move after print finishes",
                     custom_bindings=True,
                     icon="trash"),
                dict(type="settings",
                     custom_bindings=True,
                     name="Delete/Move after print")]

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            installed_version=self._plugin_version,
            rememberCheckBox=True,
            nofificationAfterPrintCheckbox=True,
            nofificationHideAfterTimeCheckbox=False,
            daysLimit=0,
            deleteAfterPrintLastValue=DEFAULT_DELETEAFTERPRINT_VALUE,
            deleteInSubFoldersLastValue=DEFAULT_INSUBFOLDER_VALUE,
            deleteWhenFailedLastValue=DEFAULT_WHENPRINT_FAILED_VALUE,
            deleteWhenCanceledLastValue=DEFAULT_WHENPRINT_CANCELED_VALUE,
            deleteMoveMethode=DEFAULT_DELETE_MOVE_METHODE,
            moveFolder=DEFAULT_MOVE_FOLDER,
            excludeFilenameCheckbox=False,
            excludeFilenamePattern=""
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
        self.daysLimit = self._settings.get_int([SETTINGS_KEY_DAYS_LIMIT])

        self._sendViewModelToClient()
        deleteMoveMethode = self._settings.get([SETTINGS_KEY_DELETE_MOVE_METHODE])
        if (deleteMoveMethode):
            if (deleteMoveMethode == METHODE_MOVE):
                # check if archive folder alr4eady exitst, if not create it
                moveFolder = self._getMoveFolder()
                if (moveFolder):
                    target = FileDestinations.LOCAL
                    # from octoprint.server.api.files import _verifyFolderExists
                    # verifyResult = _verifyFolderExists(target, moveFolder)
                    verifyResult = self._file_manager.folder_exists(target, moveFolder)
                    if (verifyResult == False):
                        resultType = 'info'
                        resultTitle = "Successful"
                        resultMessage = "Folder '"+moveFolder+"' created"
                        try:
                            self._logger.debug("try to create moveFolder '"+moveFolder+"'")
                            self._file_manager.add_folder(target, moveFolder)
                        except (ValueError, RuntimeError):
                            resultType = 'error'
                            resultTitle = "ERROR"
                            resultMessage = "Error during creation of folder '"+moveFolder+"'"
                            self._logger.error("BOOM something goes wrong during creation of '"+moveFolder+"'")
                            self._logger.error(RuntimeError)
                            self._logger.error(ValueError)
                        self._sendPopupMessageToClient(resultType, resultTitle, resultMessage)

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
                displayName="DeleteMoveAfterPrint Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="OllisGit",
                repo="OctoPrint-DeleteAfterPrint",
                current=self._plugin_version,

                # update method: pip
                # pip="https://github.com/OllisGit/OctoPrint-DeleteAfterPrint/archive/{target_version}.zip"
                pip = "https://github.com/OllisGit/OctoPrint-DeleteAfterPrint/releases/latest/download/master.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "DeleteAfterPrint Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = DeleteAfterPrintPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }


# excludePattern = "benchy.+\nhallo.gcode"
# testFilename = "hallo.gcode"
# res = DeleteAfterPrintPlugin()._isFileNameExcluded(testFilename, excludePattern)
# print(res)
