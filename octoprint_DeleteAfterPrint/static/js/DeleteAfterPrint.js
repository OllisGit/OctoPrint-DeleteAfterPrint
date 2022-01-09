/*
 * View model for OctoPrint-DeleteAfterPrint
 *
 * Author: OllisGit
 * License: AGPLv3
 */
$(function() {
    function DeleteAfterPrintViewModel(parameters) {

        var PLUGIN_ID = "DeleteAfterPrint";
        // enable support of resetSettings
        new ResetSettingsUtil().assignResetSettingsFeature(PLUGIN_ID, function(data){
                                // assign new settings-values // TODO find a more generic way
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.daysLimit(data.daysLimit);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.nofificationAfterPrintCheckbox(data.nofificationAfterPrintCheckbox);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.nofificationHideAfterTimeCheckbox(data.nofificationHideAfterTimeCheckbox);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.rememberCheckBox(data.rememberCheckBox);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.deleteMoveMethode(data.deleteMoveMethode);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.moveFolder(data.moveFolder);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.excludeFilenameCheckbox(data.excludeFilenameCheckbox);
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.excludeFilenamePattern(data.excludeFilenamePattern);
        });


        var self = this;

        // assign the injected parameters, e.g.:
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.filesViewModel = parameters[2];

        self.deleteAfterPrintEnabled = ko.observable();
        self.deleteInSubFoldersEnabled = ko.observable();
        self.deleteWhenFailedEnabled = ko.observable();
        self.deleteWhenCanceledEnabled = ko.observable();

        // self.deleteMoveText = ko.observable();

        const OPTION_DO_NOTHING = "[DO NOTHING]";
        const OPTION_DELETE = "[DELETE FILE]";

        self.allDeleteMoveOptions = ko.observableArray([]);
        self.selectedDeleteMoveOption = ko.observable();

        self.filesViewModel.folderList.subscribe(function(changed){
            let allOptions = [
                OPTION_DO_NOTHING,
                OPTION_DELETE
            ];
            for (let i=0; i<changed.length; i++){
                let folder = changed[i];
                if (folder != "/"){
                    allOptions.push(folder);
                }
            }
            self.allDeleteMoveOptions(allOptions);
            let currentSelection = self.selectedDeleteMoveOption();
            if (currentSelection != undefined && allOptions.includes(currentSelection) == false){
                self.selectedDeleteMoveOption(OPTION_DO_NOTHING);
                alert("Folder '"+currentSelection+"' for move after print is not available. Check target action!");
            }
        }, self);



        self.deleteMoveOptionChanged = function(){
            let currentvVal = self.selectedDeleteMoveOption();
            if (currentvVal == OPTION_DO_NOTHING){
                self.deleteAfterPrintEnabled(false);
            } else {
                self.deleteAfterPrintEnabled(true);
            }
            console.error("Current selection: " + currentvVal);
        }

        self.settingsViewModel.isDaysLimitVisible = function(daysLimit) {
            var result = daysLimit != "0";
            return result;
        };

        self.onDeleteAfterPrintEvent = function() {
            var selectedDeleteMoveOption = self.selectedDeleteMoveOption();

            var checkedDeleteAfterPrint = self.deleteAfterPrintEnabled();
            var checkedDeleteOnylRoot = self.deleteInSubFoldersEnabled();
            var checkedDeleteFailed = self.deleteWhenFailedEnabled();
            var checkedDeleteCanceled = self.deleteWhenCanceledEnabled();
            $.ajax({
                url: API_BASEURL + "plugin/"+PLUGIN_ID,
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "checkboxStates",
                    selectedDeleteMoveOption: selectedDeleteMoveOption,
                    deleteAfterPrint: checkedDeleteAfterPrint,
                    deleteInSubFolders: checkedDeleteOnylRoot,
                    deleteWhenPrintFailed: checkedDeleteFailed,
                    deleteWhenPrintCanceled: checkedDeleteCanceled
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }
        // assign event-listener
        self.selectedDeleteMoveOption.subscribe(self.onDeleteAfterPrintEvent, self);
        self.deleteAfterPrintEnabled.subscribe(self.onDeleteAfterPrintEvent, self);
        self.deleteInSubFoldersEnabled.subscribe(self.onDeleteAfterPrintEvent, self);
        self.deleteWhenFailedEnabled.subscribe(self.onDeleteAfterPrintEvent, self);
        self.deleteWhenCanceledEnabled.subscribe(self.onDeleteAfterPrintEvent, self);

        self.filenameToTest = ko.observable();
        self.testResultMessage = ko.observable("");

        self.testFilenamePattern = function () {
            let filenameToTest = self.filenameToTest();
            let excludePatterns = self.settingsViewModel.settings.plugins.DeleteAfterPrint.excludeFilenamePattern();
            if (filenameToTest != undefined && filenameToTest.trim().length != 0 &&
                excludePatterns != undefined && excludePatterns.trim().length != 0){
                self.testResultMessage("")
                $.ajax({
                    url: API_BASEURL + "plugin/"+PLUGIN_ID,
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "testExcludePatterns",
                        filenameToTest: filenameToTest,
                        excludePatterns: excludePatterns
                    }),
                    contentType: "application/json; charset=UTF-8"
                })
                .done(function( data ){
                    self.testResultMessage(data["result"])
                });
            }
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != PLUGIN_ID) {
                return;
            }
            if (data.deleteAfterPrintEnabled != undefined){
                self.deleteAfterPrintEnabled(data.deleteAfterPrintEnabled);
            }
            if (data.deleteInSubFoldersEnabled != undefined){
                self.deleteInSubFoldersEnabled(data.deleteInSubFoldersEnabled);
            }
            if (data.deleteWhenFailedEnabled != undefined){
                self.deleteWhenFailedEnabled(data.deleteWhenFailedEnabled);
            }
            if (data.deleteWhenCanceledEnabled != undefined){
                self.deleteWhenCanceledEnabled(data.deleteWhenCanceledEnabled);
            }

            // if (data.deleteMoveMethode == "move"){
            //     self.deleteMoveText("Move");
            // } else {
            //     self.deleteMoveText("Delete");
            //     self.selectedDeleteMoveOption(OPTION_DELETE);
            // }
            if (data.selectedDeleteMoveOption != undefined){
                self.selectedDeleteMoveOption(data.selectedDeleteMoveOption);
            }



            if (data.message_text){
					new PNotify({
						title: data.message_title,
						text: data.message_text,
						type: data.message_type,  // 'notice', 'info', 'success', or 'error'.
						hide: data.hide_type
						});
/*
					new PNotify({
						title: 'File(s) were deleted:',
						text: data.message,
						type: "popup",
						hide: false
						});
*/

            }
        }
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: DeleteAfterPrintViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel", "filesViewModel"  ],
        // Elements to bind to, e.g. #settings_plugin_DeleteAfterPrint, #tab_plugin_DeleteAfterPrint, ...
        elements: [
            document.getElementById("sidebar_plugin_deleteAfterPrint"),
            document.getElementById("deleteafterprint_plugin_navbar"),
            document.getElementById("deleteafterprint_plugin_settings")
        ]
    });
});
