/** Code to be invoked when page assets have finished loading. */
var pageReady = function() {
    /** Instantiate Objects */
    urlEngine = new UrlBox();
    apiCaller = new CallBox();
    tableEngine = new TableBox();

    apiCaller.doCall({
        url : urlEngine.getUrlDirective(),
        settings : {
            success : function(data, textStatus, jqXHR) {
                showData(data);
            }
        }
    });
};

var showData = function(rawData, dataUrl) {
    console.log('data:');
    console.log(rawData);

    var directiveElements = urlEngine.getUrlDirective().substring(1).split("/");

    var processedData = rawData.results;

    var makePrettyStatus = function(theString) {
        return makePrettyName(theString.toLowerCase().replace("completed_",""));
    }

    if (directiveElements.length > 0) {
        var statusKey = makePrettyName(directiveElements[0]);
        $("ul.nav").html('<li><a href="#">'+statusKey+'</a></li>');
        $("title").html('Snooper - '+statusKey);
    }

/*
    var processedData = [];
    if (urlDirective.length === 2) {
        var statusKey = makePrettyName(urlDirective[0]);
        var statusVal = (urlDirective[0] === 'status') ? makePrettyStatus(urlDirective[1]) : makePrettyName(urlDirective[1]);
        $("ul.nav").html('<li><a href="#">'+statusKey+' / '+statusVal+'</a></li>');
        forEach(rawData, function(thisMigration) {
            if (thisMigration.hasOwnProperty(urlDirective[0]) && (thisMigration[urlDirective[0]].toString() === urlDirective[1].toString())) processedData.push(thisMigration);
        });
    } else {
        $("ul.nav").html('<li><a href="#">All Migrations</a></li>');
        processedData = rawData;
    }
*/

    $("ul.nav").append('<li><a href="mailto:?subject=reporting&body='+document.location.href+'"><i class="icon-cloud-upload"></i> '+processedData.length+' Total</a></li>');

    var headersWritten = false;

    forEach(processedData, function(thisRow) {
        var rowKeys = [];
        var newRow = '<tr>';
        var colIterator = 0;
        forEach(thisRow, function(thisData, thisKey) {
            rowKeys.push(makePrettyName(thisKey));
            var cookedData = (thisKey === "status") ? makePrettyStatus(thisData) : thisData;
            if ($.isArray(thisData)) {
                cookedData = '<dl>';
                forEach(thisData, function(thisStep) {
                    cookedData += '<dt>'+makePrettyName(thisStep.name)+':</dt><dd>'+makePrettyStatus(thisStep.status)+'</dd>';
                });
                cookedData += '</dl>';
            } else {
                //cookedData = '<a href="http://10.10.121.60/migrations/'+urlEngine.smartEncode(thisKey)+'/'+urlEngine.smartEncode(thisData)+'">'+cookedData+'</a>';
            }
            newRow += '<td data-colId="'+colIterator+'" class="js_colId-'+colIterator+'">'+cookedData+'</td>';
            colIterator++;
        });
        $("#reporting_display tbody").append(newRow+'</tr>');
        if (!headersWritten) {
            $("#reporting_display").addClass("js_sorTable");
            $("#reporting_display thead").append('<tr><th>'+rowKeys.join(' <i class="icon-sort-down"></i></th><th>')+' <i class="icon-sort-down"></i></th></tr>');
            headersWritten = true;
        }
    });
    tableEngine.setUpTableSort($("#reporting_display"));
}

/** URL handler. */
var urlEngine;
var UrlBox = function() {
    var that = this;

    this.smartEncode = function(theString) {
        return encodeURI(theString.toString().split(" ").join("__"));
    }

    this.smartDecode = function(theString) {
        return decodeURI(theString.toString().split("__").join("%20"));
    }

    this.getUrlDirective = function(theUrl) {
        var theUrl = theUrl || that.workingUrl;
        var defaultDirective = "/get_all_migrations";
        var theDirective = theUrl.substring(that.rootUrl.length);
        if (theDirective.length <= 1) theDirective = defaultDirective;
        return theDirective;
    }

    /**
        Set the working URL.
        @param {string} theUrl - the URL to work with.
    */
    this.setUrl = function(theUrl) {
        that.workingUrl = theUrl;
        that.rootUrl = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');
    };

    /**
        Get all parameters from a URL, and return them as an object.
        If a URL is not supplied, use the UrlBox instance's working URL.
        @param {string} [theUrl=workingUrl] - the URL to work with.
        @returns {object} paramObject - the URL parameters.
    */
    this.getParams = function(theUrl) {
        var theUrl = theUrl || that.workingUrl;
        var paramObject = {};
        var urlArray = theUrl.split("?");
        var urlPath = urlArray.shift();
        var urlParams = (urlArray.length > 0) ? urlArray.join("?").split("&") : [];
        forEach(urlParams, function(thisPair) {
            var pairArray = thisPair.split("=");
            var pairKey = pairArray.shift();
            var pairVal = (pairArray.length > 0) ? pairArray.join("=") : null;
            paramObject[pairKey] = pairVal;
        });
        return paramObject;
    };

    /**
        Add params to a URL and return it.
        @param {object} newParams - the parameters/values to add.
        @param {string} theUrl - the URL to work with.
        @returns {string} - the URL with new params.
    */
    this.setParams = function(newParams, theUrl) {
        var theUrl = theUrl || that.workingUrl;
        theUrl = theUrl.split("?")[0] + "?";
        var paramArray = [];
        forEach(newParams, function(paramValue, paramKey) {
            paramArray.push(paramKey+"="+paramValue);
        });
        return theUrl + paramArray.join("&");
    };

    /**
        Return the value of a given URL param.
        @param {string} paramKey - the parameter key.
        @param {string} theUrl - the URL to work with.
        @returns {string} paramVal - the value of the URL parameter.
    */
    this.getParam = function(paramKey, theUrl) {
        var allParams = that.getParams(theUrl);
        var paramVal = (allParams.hasOwnProperty(paramKey)) ? allParams[paramKey] : false;
        return paramVal;
    };

    /**
        Create/Set the value of a given URL param.
        @param {string} paramKey - the parameter key.
        @param {string} paramValue - the parameter value.
        @param {string} theUrl - the URL to work with.
        @returns {string} - the URL with the new parameter set.
    */
    this.setParam = function(paramKey, paramValue, theUrl) {
        var allParams = that.getParams(theUrl);
        allParams[paramKey] = paramValue;
        return that.setParams(allParams, theUrl);
    }

    /**
        Try to add a new param to the current URL.
        If the attempt fails, refresh the page with the modified URL.
    */
    this.setCurrentParam = function(paramKey, paramValue) {
        var newUrl = that.setParam(paramKey, paramValue, that.workingUrl);
        try {
            history.pushState({}, "", newUrl);
        } catch (e) {
            document.location.href = newUrl;
        }
    }

    /**
        Clear a given URL param.
        @param {string} paramKey - the parameter key.
        @param {string} theUrl - the URL to work with.
        @returns {string} - the URL with the parameter removed.
    */
    this.clearParam = function(paramKey, theUrl) {
        var allParams = that.getParams(theUrl);
        if (allParams.hasOwnProperty(paramKey)) delete allParams[paramKey];
        return that.setParams(allParams, theUrl);
    }

    var init = function() {
        /** Set this instance's working URL to be the document location. */
        that.setUrl(document.location.href);
    }();
}

/** Table handler. */
var tableEngine;
var TableBox = function() {
    var that = this;

    /**
        Set up click sorting behavior for each table header.
        @see doTableSort.
    */
    this.setUpTableSort = function(theTable) {
        $(theTable).find("th").each(function() {
            $(this).click(function(event) {
                that.doTableSort($(this));
                return false;
            });
        });
    };

    /**
        Sort a table's rows.
        @param {object} theTH - the table header to sort by.
    */
    this.doTableSort = function(theTH) {
        var parentTable = $(theTH).closest("table");
        var rowParent = $(parentTable).find("tbody")[0] || false;
        if (rowParent) {

            /** Style hooks and resets. */
            $(theTH).addClass("sorting_by");
            $(theTH).toggleClass("js_ascendingSort");
            $(theTH).siblings("th").removeClass("sorting_by");
            var ascendingSort = $(theTH).hasClass("js_ascendingSort");

            var sortIndex = ($(theTH).index());
            var compareRows = function(row_0, row_1) {
                var matchResult = 0;
                var rowVals = [];

                /**
                    Find the cell based on table header index.
                    If the cell has a "data-sortBy" attribute, use that as the sorting value,
                    Otherwise use a sanitized version of the cell's textual content.
                */
                forEach([row_0, row_1], function(thisRow) {
                    var targetCell = $(thisRow).find("td").eq(sortIndex);
                    var sortValue = $(targetCell).attr("data-sortBy") || makeSafeName($(targetCell).text().split(" ").join("_"));
                    rowVals.push(sortValue);
                });

                /** Sorting logic. */
                if (rowVals[0] < rowVals[1]) {
                    matchResult = 1;
                } else if (rowVals[0] > rowVals[1]) {
                    matchResult = -1;
                }

                /** If we are doing an ascending sort, reverse the match results. */
                if (ascendingSort) matchResult *= -1;

                return matchResult;
            };
            $(rowParent).html($(rowParent).find("tr").sort(compareRows));

            /** If the TH has directional icons, reverse them. */
            if (ascendingSort) {
                $(theTH).find("i.icon-sort-down").removeClass("icon-sort-down").addClass("icon-sort-up");
            } else {
                $(theTH).find("i.icon-sort-up").removeClass("icon-sort-up").addClass("icon-sort-down");
            }

            /** Store the last sort in the session. */
            var bodyId = $("body").attr("id") || false;
            var tableId = $(parentTable).attr("id") || false;
            if (bodyId && tableId) sessionStorage.setItem("tableSort_"+bodyId+"_"+tableId, sortIndex+","+ascendingSort);

        }
    };

    this.init = function() {
        $("table").each(function() {
           if ($(this).hasClass("js_sorTable")) that.setUpTableSort($(this));
        });
    }();
}

/** API call handler. */
var apiCaller;
var CallBox = function() {
    var that = this;
    this.baseUrl = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '')+'/api/1/query';

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
            error : function(jqXHR, textStatus, errorThrown) {
                var errorText = [];
                forEach([textStatus, errorThrown], function(thisText) {
                    if (thisText.length > 0) errorText.push(thisText);
                });
                console.log("Error Status: "+errorText+" (details below)");
                console.log(jqXHR);
                alert('Could not complete query.\n\nPlease check your browser console for details.');
            },
            complete : function(jqXHR, textStatus) {}
        };

        /** If nextCallInfo has a "settings" property, override callPayload data with the property value data. */
        if (nextCallInfo.hasOwnProperty("settings")) $.extend(true, callPayload, nextCallInfo.settings);

        /** Make the API ajax call. */
        $.ajax(that.baseUrl+nextCallInfo.url, callPayload);
    };
};

/** Utility Functions. */
/**
    Base64 encrypt a username and password, and return the value.
    @param {string} username - user name.
    @param {string} password - password.
    @returns {string} - the Base64 encrypted value.
*/
var generateAuth = function(username, password) {
    return $().crypt({method:"b64enc",source:username+':'+password});
};

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
    Given two numbers, gives back the percentage.
    @param {int} percentNumber - The current number.
    @param {int} totalNumber - The total.
*/
var getPercentOfTotal = function(percentNumber, totalNumber) {
    return ((100 / totalNumber) * percentNumber);
}

/**
    Converts a supplied storage amount and unit to another amount and unit,
    optionally rounding up to a given number of decimal places.
    @param {number} inputAmount - The initial storage amount.
    @param {string} inputUnit - The initial storage unit.
    @param {string} outputUnit - The desired storage unit.
    @param {int} [roundToPlaces] - Optional number of decimal places to round to.
    @returns {number} outputAmount - The storage amount, converted to the new unit.
*/
var convertStorageToUnit = function(inputAmount, inputUnit, outputUnit, roundToPlaces) {
    var inputAmount = ((typeof inputAmount) !== 'number') ? parseFloat(inputAmount) : inputAmount;
    var inputUnit = $.trim(inputUnit+''.toUpperCase());
    var outputUnit = $.trim(outputUnit+''.toUpperCase());
    var roundToPlaces = roundToPlaces || false;
    var outputAmount = inputAmount;
    var conversionMap = {
        "B" : 1,
        "KB" : 1024,
        "MB" : 1048576,
        "GB" : 1073741824,
        "TB" : 1099511627776
    }
    if (conversionMap.hasOwnProperty(inputUnit) && conversionMap.hasOwnProperty(outputUnit)) {
        var amountInBytes = (inputAmount * conversionMap[inputUnit]);
        forEach(conversionMap, function(unitConversion, unitName) {
            conversionMap[unitName] = (1 / unitConversion);
        });
        outputAmount = (amountInBytes * conversionMap[outputUnit]);
    }
    if (roundToPlaces && (typeof roundToPlaces === 'number')) {
        var keyFactor = Math.pow(10, parseInt(roundToPlaces));
        outputAmount = (Math.ceil(outputAmount * keyFactor) / keyFactor);
    }
    return outputAmount;
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
            prettyDate += '&nbsp;&nbsp;&nbsp;'+ padDigit(theDate.getHours()) +':'+ padDigit(theDate.getMinutes()) +':'+ padDigit(theDate.getSeconds());
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
    If a given item exists in sessionStorage, parse it into an object and return it.
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
    Return a code-safe version of a supplied string.
    @param {string} rawName - the raw string.
    @returns {string} - the code-safe version of the string.
*/
var makeSafeName = function(rawName) {
    return $.trim(rawName).replace(/\s+/g," ").toLowerCase();
};

/**
    Return a more readable version of a supplied string.
    @param {string} rawName - the raw string.
    @returns {string} - the friendly version of the string.
*/
var makePrettyName = function(rawName) {
    var rawWords = $.trim(rawName).split("_");
    var cookedWords = [];
    forEach(rawWords, function(thisWord) {
        cookedWords.push(thisWord.charAt(0).toUpperCase() + thisWord.slice(1));
    });
    return cookedWords.join(" ");
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