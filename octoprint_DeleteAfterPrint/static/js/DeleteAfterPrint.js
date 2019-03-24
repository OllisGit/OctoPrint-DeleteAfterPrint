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
                                self.settingsViewModel.settings.plugins.DeleteAfterPrint.rememberCheckBox(data.rememberCheckBox);
        });


        var self = this;

        // assign the injected parameters, e.g.:
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];

        self.deleteAfterPrintEnabled = ko.observable();
        self.deleteInSubFoldersEnabled = ko.observable();

        self.settingsViewModel.isDaysLimitVisible = function(daysLimit) {
            var result = daysLimit != "0";
            return result;
        };

        self.onDeleteAfterPrintEvent = function() {
            var checkedDeleteAfterPrint = self.deleteAfterPrintEnabled();
            var checkedDeleteOnylRoot = self.deleteInSubFoldersEnabled();
            $.ajax({
                url: API_BASEURL + "plugin/"+PLUGIN_ID,
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "checkboxStates",
                    deleteAfterPrint: checkedDeleteAfterPrint,
                    deleteInSubFolders: checkedDeleteOnylRoot
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }
        // assign event-listener
        self.deleteAfterPrintEnabled.subscribe(self.onDeleteAfterPrintEvent, self);
        self.deleteInSubFoldersEnabled.subscribe(self.onDeleteAfterPrintEvent, self);


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
            if (data.message){
					new PNotify({
						title: 'Old files were deleted:',
						text: data.message,
						type: "popup",
						hide: false
						});
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
        dependencies: [ "loginStateViewModel", "settingsViewModel"  ],
        // Elements to bind to, e.g. #settings_plugin_DeleteAfterPrint, #tab_plugin_DeleteAfterPrint, ...
        elements: [
            document.getElementById("sidebar_plugin_deleteAfterPrint"),
            document.getElementById("deleteafterprint_plugin_navbar"),
            document.getElementById("deleteafterprint_plugin_settings")
        ]
    });
});
