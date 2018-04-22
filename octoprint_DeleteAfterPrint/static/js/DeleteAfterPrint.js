/*
 * View model for OctoPrint-DeleteAfterPrint
 *
 * Author: OllisGit
 * License: AGPLv3
 */
$(function() {
    function DeleteAfterPrintViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.deleteAfterPrintEnabled = ko.observable();

        self.settingsViewModel.isDaysLimitVisible = function(daysLimit) {
            var result = daysLimit !== "0";
            return result;
        };

        self.onDeleteAfterPrintEvent = function() {
            if (self.deleteAfterPrintEnabled()) {
                $.ajax({
                    url: API_BASEURL + "plugin/DeleteAfterPrint",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "enable"
                    }),
                    contentType: "application/json; charset=UTF-8"
                })
            } else {
                $.ajax({
                    url: API_BASEURL + "plugin/DeleteAfterPrint",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "disable"
                    }),
                    contentType: "application/json; charset=UTF-8"
                })
            }
        }
        // assign event-listener
        self.deleteAfterPrintEnabled.subscribe(self.onDeleteAfterPrintEvent, self);

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "DeleteAfterPrint") {
                return;
            }
            if (data.deleteAfterPrintEnabled){
                self.deleteAfterPrintEnabled(data.deleteAfterPrintEnabled);
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
            document.getElementById("deleteafterprint_plugin_navbar")
        ]
    });
});
