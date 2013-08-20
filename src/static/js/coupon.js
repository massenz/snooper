jQuery.download = function(url, data, method){
    //url and data options required
    if( url && data ){
        //data can be string of parameters or array/object
        data = typeof data == 'string' ? data : jQuery.param(data);
        //split params into form inputs
        var inputs = '';
        jQuery.each(data.split('&'), function(){
            var pair = this.split('=');
            inputs+='<input type="hidden" name="'+ pair[0] +'" value="'+ pair[1] +'" />';
        });
        //send request
        jQuery('<form action="'+ url +'" method="'+ (method||'post') +'">'+inputs+'</form>')
            .appendTo('body').submit().remove();
    };
};



$(function() {
    formEngine.registerSubmit("coupon_form", $("#btnSubmit"));

    $("#coupon_form").submit(function(event) {
        /**
         Form must pass validation before code is fired.
         @see FormBox.validateForm in main.js.
         */
        if (formEngine.validateForm($(this))) {

            var formData = form2js("coupon_form",".",false,null,true);
            var count = formData["count"];
            var form = $('<form method="POST" action="/codes/' + count + '">');
            $.each(formData, function(k, v) {
                form.append($('<input type="hidden" name="' + k + '" value="' + v + '">'));
            });
            $('body').append(form);
            form.submit();

/*
            delete formData["count"];

            $.download("/codes/" + count, formData, "POST");
*/

/*
            var params = $.param(formData);
            console.log(params);
            location.href = "/codes/" + count + "?" + params;
*/

/*            apiCaller.doCall({
                url : "codes/" + count,
                settings : {
                    type: "POST",
                    contentType : "application/json",
                    data : JSON.stringify(formData),
                    success : function(response, textStatus, jqXHR) {
                        var disp = jqXHR.getResponseHeader('Content-Disposition');
                        if (disp && disp.search('attachment') != -1) {
                            var form = $('<form method="POST" action="' + url + '">');
                            $.each(formData, function(k, v) {
                                form.append($('<input type="hidden" name="' + k + '" value="' + v + '">'));
                            });
                            $('body').append(form);
                            form.submit();
                        }

                        alertEngine.showAlert({
                            alertClass : "success",
                            alertBody : "Your promotion code has been redeemed!"
                        });
                    },
                    complete : function(jqXHR, textStatus, errorThrown) {
                        var disp = jqXHR.getResponseHeader('Content-Disposition');
                        if (disp && disp.search('attachment') != -1) {
                            var form = $('<form method="POST" action="/codes/' + count + '">');
                            $.each(formData, function(k, v) {
                                form.append($('<input type="hidden" name="' + k + '" value="' + v + '">'));
                            });
                            $('body').append(form);
                            form.submit();
                        }
                    }
                }
            });*/
        }
    });

});