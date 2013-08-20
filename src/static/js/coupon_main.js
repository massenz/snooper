/** Form builder and handler. */
var formEngine;
var FormBox = function() {
    var that = this;

    /**
     Set up the submit button and core submission functionality.
     @param {string} formId - the HTML ID of the form.
     @param {string} theSubmit - the Submit button/link identifier.
     */
    this.registerSubmit = function(formId, theSubmit) {

        /**
         Enable/disable submit button based on form validation check.
         @see checkForFullFields.
         */
        var inputAndSelectCheck = function() {
            if (that.checkForFullFields($("#"+formId))) {
                $(theSubmit).removeClass("disabled");
            } else {
                $(theSubmit).addClass("disabled");
            }
        }

        /** Check form "required" elements on input/select keyup/change events. */
        $('#'+formId+' input').unbind("keyup");
        $('#'+formId+' select').unbind("change");
        $('#'+formId+' input[required="required"]').keyup(function(event) {
            inputAndSelectCheck();
        });
        $('#'+formId+' select[required="required"], #'+formId+' input[type="checkbox"]').change(function(event) {
            inputAndSelectCheck();
        });
        $('#'+formId+' input[type="radio"]').click(function(event) {
            inputAndSelectCheck();
        });

        /** Submit button setup. */
        $(theSubmit).unbind("click");
        $(theSubmit).click(function(event) {

            /** Code is only fired if the button is not "disabled." */
            if (!$(this).hasClass('disabled')) {
                alertEngine.clearAlerts();
                $('#'+formId).submit();
            }

            return false;
        });

        /** Capturing enter key for form submission. */
        $(document).keydown(function(event) {
            if ((event.keyCode === 13) && ($("body").find("form").length < 2)) {
                $('#'+formId).submit();
                return false;
            }
        });

        inputAndSelectCheck();
    };

    /**
     If an input fails validation, show the error (and an optional message) inline.
     @param {string} theInput - the Input identifier.
     @param {string} [theMessage] - The optional error message.
     @param {boolean} [showMessage] - Optionally show message.
     */
    this.showBadInput = function(theInput, theMessage, showMessage) {
        var theMessage = theMessage || false;
        var showMessage = showMessage || false;
        if (theMessage) {
            $(theInput).attr("data-error_message", theMessage);
            if (showMessage) {
                var parentControls = $(theInput).closest(".controls");
                var parentHelp = $(parentControls).find(".help-inline");
                if ($(parentHelp).length === 0) {
                    $(parentControls).append('<span class="help-inline">'+theMessage+'</span>');
                } else {
                    $(parentHelp).text(theMessage);
                }
            }
        }
    };

    /**
     If a form fails validation, alert the error message(s).
     @param {string} theForm - form identifier.
     */
    this.alertErrors = function(theForm) {
        /**
         Find any "error" inputs and add them to the errorList array.
         @see showBadInput.
         */
        var errorList = [];
        $(theForm).find(".error").each(function() {
            $(this).find("input[data-error_message], select[data-error_message], textarea[data-error_message]").each(function() {
                var errorText = $(this).attr("data-error_message");
                if ($.inArray(errorText, errorList) === -1) errorList.push(errorText);
            });
        });

        /**
         If errors are found, build an error message and a corresponding alert.
         @see AlertBox.showAlert.
         */
        if (errorList.length > 0) {
            var listString = "<br /><ul>";
            forEach(errorList, function(thisItem) {
                listString += '<li>'+thisItem+'</li>';
            });
            alertEngine.showAlert({
                alertTitle : "We're sorry.",
                alertBody : listString+"</ul>",
                alertClass : "error"
            });
        }

    };

    /**
     Make sure we are dealing with an email address.
     @param {string} theInputValue - the value to test.
     @returns {boolean} - validation result.
     */
    this.validateEmail = function(theInputValue) {
        var reg = /^([A-Za-z0-9_\-\.+])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
        return (reg.test(theInputValue));
    };

    /**
     Make sure "required" inputs are non-empty.
     @param {string} theForm - form identifier.
     @returns {boolean} fieldsAreFull - validation result.
     */
    this.checkForFullFields = function(theForm) {
        var fieldsAreFull = true;
        $(theForm).find("input, select, textarea").each(function() {
            var isEmpty = ($(this).attr("type") === "checkbox") ? !$(this).prop('checked') : (!$.trim($(this).val()) || ($.trim($(this).val()) === ""));
            if ($(this).attr("type") === "radio") {
                isEmpty = true;
                var radioName = $(this).attr("name");
                $(theForm).find('input[name="'+radioName+'"]').each(function() {
                    if ($(this).prop('checked')) isEmpty = false;
                });
            }
            if ($(this).attr("required") && isEmpty) {
                fieldsAreFull = false;
                return false;
            };
        });
        return fieldsAreFull;
    };

    /**
     Call previously-defined validation functions.
     @see showBadInput.
     @param {string} theForm - form identifier.
     @returns {boolean} formIsGood - validation result.
     */
    this.validateForm = function(theForm) {
        var formIsGood = true;
        $(theForm).find("input, select, textarea").each(function() {
            $(this).closest(".control-group").removeClass("error");
            var isEmpty = ($(this).attr("type") === "checkbox") ? !$(this).prop('checked') : (!$(this).val() || ($(this).val() === ""));
            if ($(this).attr("required") && isEmpty) {
                formIsGood = false;
                that.showBadInput($(this), 'Must not be blank');
                $(this).closest(".control-group").addClass("error");
            } else if (($(this).attr("type") && ($(this).attr("type").toLowerCase() === "email")) && (!that.validateEmail($(this).val()))) {
                formIsGood = false;
                that.showBadInput($(this), 'Must be a valid email format');
                $(this).closest(".control-group").addClass("error");
            }
            if ($(this).attr("maxlength") && ($(this).val().length > parseInt($(this).attr("maxlength")))) {
                formIsGood = false;
                that.showBadInput($(this), 'Value exceeds maximum length');
                $(this).closest(".control-group").addClass("error");
            }
        });
        var passwordFields = $(theForm).find("[type='password']");
        if ((($(passwordFields).length > 1) && ($(passwordFields).eq(1).attr("id").indexOf("confirm") !== -1)) && ($(passwordFields).eq(0).val() !== $(passwordFields).eq(1).val())) {
            formIsGood = false;
            that.showBadInput($(passwordFields).eq(0), 'Passwords must match');
            $(passwordFields).eq(0).closest(".control-group").addClass("error");
            that.showBadInput($(passwordFields).eq(1));
            $(passwordFields).eq(1).closest(".control-group").addClass("error");
        }
        that.alertErrors(theForm);
        return formIsGood;
    };

    var init = function() {

        /** When an input is focused, changed, or clicked, remove the error state and clear any alerts. */
        $("input, textarea, select").on("focus, change, click", function() {
            if ($(this).closest(".control-group") && $(this).closest(".control-group").hasClass("error")) {
                $(this).closest(".controls").find(".help-inline").remove();
                $(this).closest(".control-group").removeClass("error");
            }
            $(this).removeAttr("data-error_message");
            alertEngine.clearAlerts();
        });

        /**
         When a form is submitted, return false.
         This is typically augmented by form-specific code elsewhere.
         */
        $("form").submit(function() {
            return false;
        });

    }();
}

/** Alert display mechanism. */
var alertEngine;
var AlertBox = function() {
    var that = this;

    /**
     Takes an alert object with optional title, body, and class, and displays it.
     @param {object} messageObject - the message object.
     */
    this.showAlert = function(messageObject) {
        var messageHtml = "";
        if (messageObject.hasOwnProperty("alertTitle")) messageHtml += "<strong>"+messageObject.alertTitle+"</strong>";
        if (messageObject.hasOwnProperty("alertBody")) messageHtml += messageObject.alertBody;
        var alertClass = (messageObject.hasOwnProperty("alertClass")) ? " alert-"+messageObject.alertClass : "";

        /** If the message is greater than 120 characters or has embedded paragraph tags, use the "alert-block" class for improved appearance. */
        if ((messageHtml.length > 120) || (messageHtml.indexOf("<p>") > -1)) alertClass += " alert-block";

        /** Clear any existing alerts and show this new one. */
        that.clearAlerts();
        $(that.alertWrapper).prepend('<div class="alert_wrapper"><div class="alert_wrapper_inner"><div class="alert'+alertClass+'"><div class="alert-inner"><button type="button" class="close" data-dismiss="alert">&times;</button>'+messageHtml+'</div></div></div></div>');

        /** When an alert's "close" button is clicked, clear all page alerts. */
        $(that.alertWrapper+" .alert .close").click(function(event) {
            that.clearAlerts();
        });

    }

    /**
     Store an alert in Session Storage for retrieval on a subsequent page.
     @param {object} messageObject - the message object.
     */
    this.setAlert = function(messageObject) {
        var messageString = JSON.stringify(messageObject);
        sessionStorage.setItem("alert", messageString);
    };

    /**
     If there is an alert in Session Storage, show it and then clear it.
     @see showAlert.
     */
    this.getAlert = function() {
        var sessionAlert = (sessionStorage.getItem("alert")) || false;
        if (sessionAlert) {
            var messageObject = JSON.parse(sessionAlert);
            that.showAlert(messageObject);
            sessionStorage.removeItem("alert");
        }
    };

    /** Clear any existing alerts. */
    this.clearAlerts = function() {
        $(that.alertWrapper+" div.alert_wrapper").remove();
    };

    /**
     Establish container for alert messages and check for alerts in Session Storage.
     @see getAlert.
     */
    var init = function() {
        that.alertWrapper = "body";
        that.getAlert();
    }();

};

/** Utility functions */

/**
 Iterate through an object, performing the specified function on each property.
 @param {object} theObject - the object to iterate through.
 @param {object} theFunction - the function to execute on each property.
 */
var forEach = function(theObject, theFunction) {
    for (var theKey in theObject) {
        if (theObject.hasOwnProperty(theKey)) theFunction(theObject[theKey], theKey);
    }
};

/**
 If a given item exists in session storage, parse it into an object and return it.
 @param {string} itemName - the name of the item.
 @returns {object} itemObject - the parsed object.
 */
var memoryToObject = function(itemName) {
    var itemObject;
    try {
        itemObject = JSON.parse(sessionStorage.getItem(itemName));
    } catch (e) {
        itemObject = false;
    }
    return itemObject;
};

/**
 Takes an object and saves it to session storage.
 @param {string} objectName - name to use as a storage key.
 @param {object} theObject - the object passed in.
 @returns {string} theString - the stringified version of the object.
 */
var objectToMemory = function(objectName, theObject) {
    var theString;
    try {
        theString = JSON.stringify(theObject);
        sessionStorage.setItem(objectName, theString);
    } catch (e) {
        theString = false;
    }
    return theString;
}

/**
 Return a code-safe version of a supplied string.
 @param {string} rawName - the raw string.
 @returns {string} - the code-safe version of the string.
 */
var makeSafeName = function(rawName) {
    return $.trim(rawName).replace(/\s+/g," ").toLowerCase();
};

/**
 Make a human-friendly version of a supplied string.
 @param {string} rawName - the raw string.
 @param {boolean} [makeCaps] - test individual words against a map of words with special capitalization.
 @returns {string} - the human-friendly version of the string.
 */
var makeNiceName = function(rawName, makeCaps) {
    var makeCaps = makeCaps || false;
    var capsMap = {
        "ip" : "IP",
        "url" : "URL",
        "vdc" : "VDC",
        "os" : "OS"
    };
    var niceWords = [];
    var rawWords = $.trim(rawName.toLowerCase()).split("_");
    forEach(rawWords, function(thisWord) {
        var niceWord = (makeCaps && capsMap.hasOwnProperty(thisWord)) ? capsMap[thisWord] : thisWord.substr(0,1).toUpperCase() + thisWord.substr(1);
        niceWords.push(niceWord);
    });
    return niceWords.join(" ");
}

/**
 Wraps the given text with the given tag.
 @param {string} theText - The text to wrap.
 @param {string} theTag - The tag name to wrap around the text.
 @param {object} tagAttributes - Optional attributes (like class, id, etc.) to be added to the tag.  Multiple values should be sent as an array.
 @returns {string} theText - formatted message.
 @see forceArray.
 */
var wrapWithTag = function(theText, theTag, tagAttributes) {
    var theText = theText || '';
    var theTag = (theTag) ? $.trim(theTag).toLowerCase() : false;
    var tagAttributes = tagAttributes || false;
    var attributesString = '';
    if (tagAttributes) {
        var attributesArray = [];
        forEach(tagAttributes, function(attributeValue, attributeKey) {
            attributesArray.push(attributeKey+'="'+forceArray(attributeValue).join(" ")+'"');
        });
        attributesString = ' '+attributesArray.join(" ");
    }
    if (theTag && (theText !== '')) theText = '<'+theTag+attributesString+'>'+theText+'</'+theTag+'>';
    return theText;
}

/**
 Sets a .status_progress bar's loading indicator.
 @param {object} theBar - The .status_progress bar.
 @param {number} widthPercentage - the progress percentage.
 */
var setProgressBarWidth = function(theBar, widthPercentage) {
    var newDimensions = (100 - parseInt(widthPercentage)) + "% 100%";
    $(theBar).css("background-size", newDimensions);
}

/**
 Formats date string.
 @param {string} theDate - the Date to be formatted.
 @param {boolean} [getMs] - optional flag to get epoch milliseconds instead of a formatted date.
 @returns {string} - the formatted date.
 */
var formatDate = function(theDate, getMs) {
    var getMs = getMs || false;
    var prettyDate = theDate;
    var theDate = ((typeof theDate === 'string') || (typeof theDate === 'number')) ? new Date(theDate) : theDate;
    if (theDate instanceof Date) {
        if (getMs) {
            prettyDate = theDate.getTime();
        } else {
            prettyDate = padDigit(theDate.getMonth() + 1) +'/'+ padDigit(theDate.getDate()) +'/'+ theDate.getFullYear();
        }
    }
    return prettyDate;
}

/**
 Pads single-digit numbers with a leading zero.
 @param {number} rawNumber - the number to pad.
 @returns {int} - the padded number.
 */
var padDigit = function(rawNumber) {
    var rawNumber = parseInt(rawNumber);
    return (rawNumber < 10) ? '0'+rawNumber : rawNumber;
}

/**
 Force a unique array.
 @param {array} rawArray - the raw array.
 @returns {array} cleanArray - the unique array.
 */
var makeUniqueArray = function(rawArray) {
    var cleanArray = [];
    forEach(rawArray, function(rawValue) {
        if ($.inArray(rawValue, cleanArray) === -1) cleanArray.push(rawValue);
    });
    return cleanArray;
};

/**
 Force a supplied item to be an array, if it is not already one.
 @param {string|array|object} rawItem - the raw item.
 @returns {array} - the forced array.
 */
var forceArray = function(rawItem) {
    return ($.isArray(rawItem)) ? rawItem : [rawItem];
}

/** API call handler. */
var apiCaller;
var CallBox = function() {
    var that = this;

    /** Construct base URL for API calls based on current protocol, hostname, and port. */
    var baseUrl = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port : '')+'/';

    /**
     API caller.
     @param {object} nextCallInfo - overriding call object.
     */
    this.doCall = function(nextCallInfo) {
        /** Base call payload object; typically overridden by nextCallInfo.settings. */
        var callPayload = {
            dataType : "json",
            headers : {
                "accept" : "application/json"
            },
            success : function(data, textStatus, jqXHR) {},
            error : function(jqXHR, textStatus, errorThrown) {},
            complete : function(jqXHR, textStatus) {}
        };

        /** If nextCallInfo has a "settings" property, override callPayload data with the property value data. */
        if (nextCallInfo.hasOwnProperty("settings")) $.extend(true, callPayload, nextCallInfo.settings);

        /** Make the API ajax call. */
        $.ajax(baseUrl+nextCallInfo.url, callPayload);
    };
};


$(function() {
    formEngine = new FormBox();
    alertEngine = new AlertBox();
    apiCaller = new CallBox();
})