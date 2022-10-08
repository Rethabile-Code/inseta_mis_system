odoo.define('theme_inseta.HeiRepRegistration', function (require) {
    "use strict";

    require('web.dom_ready');
    var utils = require('web.utils');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;


    ajax.loadXML('/theme_inseta/static/xml/partials.xml', qweb);

    function showAlertDialog(title, msg) {
        var wizard = $(qweb.render('alert.dialog', {
            'msg': msg || _t('Message Body'),
            'title': title || _t('Title')
        }));
        wizard.appendTo($('body')).modal({
            'keyboard': true
        });
    }
    //multi step vars
    var current_fs, next_fs, previous_fs; //fieldsets
    var opacity;

    publicWidget.registry.HEIRepRegistration = publicWidget.Widget.extend({
        selector: '.hei-rep-registration',
        willStart: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var inputTel = document.querySelector("#inputTel");
                var itiTel = window.intlTelInput(inputTel,{
                  initialCountry: "auto",
                  hiddenInput:"inputItiTel",
                  placeholderNumberType:"MOBILE",
                  preferredCountries: ["za"],
                  geoIpLookup: function(callback) {
                    $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                        console.log("IP DATA "+ JSON.stringify(resp))
                        var countryCode = (resp && resp.country) ? resp.country : "za";
                        callback(countryCode);
                    });
                  },
                  utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                });
                window.itiTel = itiTel

                var inputCellPhone = document.querySelector("#inputSignatoryTel");
                var itiCell = window.intlTelInput(inputCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCell",
                  placeholderNumberType:"MOBILE",
                  preferredCountries: ["za"],
                  geoIpLookup: function(callback) {
                    $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                        console.log("IP DATA "+ JSON.stringify(resp))
                        var countryCode = (resp && resp.country) ? resp.country : "za";
                        callback(countryCode);
                    });
                  },
                  utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                });
                window.itiSignatoryTel = itiCell
            });
        },
        events: {
            'click .next': function (ev) {

                current_fs = $(ev.target).parent();
                next_fs = $(ev.target).parent().next();

                var next_step = true;
                let validEmail = false
                let validCell = false
                let validSignatoryCell = false
                let validSignatoryEmail = false

                current_fs.find('input:required, select:required').each(function (ev) {
                    if ($(this).val() == "") {
                        $(this).addClass('is-invalid');
                        next_step = false;
                    } else {
                        $(this).removeClass('is-invalid').addClass('is-valid')
                    }
                });

                let inputTel = $("#inputTel");
                if(!validatePhone(inputTel.val())){
                    inputTel.addClass("is-invalid")
                }else{
                    inputTel.removeClass('is-invalid').addClass("is-valid")
                    validCell = true
                }

                let inputSignatoryTel = $("#inputSignatoryTel");
                if(!validatePhone(inputSignatoryTel.val())){
                    inputSignatoryTel.addClass("is-invalid")
                }else{
                    inputSignatoryTel.removeClass('is-invalid').addClass("is-valid")
                    validSignatoryCell = true
                }

                //validate email and cell phone
                let inputEmail = $("#inputEmail");
                if(!validateEmail(inputEmail.val())){
                    inputEmail.addClass("is-invalid")
                }else{
                    inputEmail.removeClass('is-invalid').addClass("is-valid")
                    validEmail= true
                }
                let inputSignatoryEmail = $("#inputEmail");
                if(!validateEmail(inputSignatoryEmail.val())){
                    inputSignatoryEmail.addClass("is-invalid")
                }else{
                    inputSignatoryEmail.removeClass('is-invalid').addClass("is-valid")
                    validSignatoryEmail= true
                }

                if(validEmail && validCell && validSignatoryCell && validSignatoryEmail && next_step){
                    next_step = true
                }else{
                    next_step = false
                }

                if (next_step) {
                    //if the next button is submit, then submit the form before showing next fieldset
                    if ($(ev.target).val() == "Confirm") {

                        // Get form
                        var form = $('#msform')[0];
                        // FormData object 
                        var formData = new FormData(form);
                        //append extra data to form
                        if($("#inputTel").val() !== "") formData.append('inputTelDialCode', itiTel.getSelectedCountryData().dialCode);
                        if($("#inputSignatoryTel").val() !== "") formData.append('inputSignatoryTelDialCode', itiSignatoryTel.getSelectedCountryData().dialCode);

                        let inputSubmit = $(ev.target)
                        let btnPreloader = $("#btn-preloader");
                        console.log('Sending request to server => '+ formData)
                        var xmlRequest = $.ajax({
                            type: "POST",
                            url: "hei-rep-registration-ajax",
                            data: formData,
                            processData: false,
                            contentType: false,
                            cache: false,
                            timeout: 800000,
                            beforeSend: function () {
                                inputSubmit.addClass("d-none")
                                btnPreloader.removeClass("d-none")
                            }
                        });
                        xmlRequest.done(function (data) {
                            console.log('Recieving response from server => '+ JSON.stringify(data))
                            const response = JSON.parse(data)
                            if(response.status){
                                //Show success tab
                                $("#progressbar li").eq($("fieldset").index(next_fs)).addClass("active");
                                next_fs.show();
                                current_fs.animate({
                                    opacity: 0
                                }, {
                                    step: function (now) {
                                        opacity = 1 - now;
                                        current_fs.css({
                                            'display': 'none',
                                            'position': 'relative'
                                        });
                                        next_fs.css({
                                            'opacity': opacity
                                        });
                                    },
                                    duration: 600
                                });
                            }else{
                                showAlertDialog("Validation Error:", `Message: ${response.message}`)
                            }
                        });
                        xmlRequest.fail(function (jqXHR, textStatus) {
                            console.log(`SDF Registration. TextStatus: ${textStatus}. Statuscode:  ${jqXHR.status}`);
                            showAlertDialog("Server Error", `TextStatus: ${textStatus} <br/> StatusCode: ${jqXHR.status}`)
                        });
                        xmlRequest.always(function () {
                            inputSubmit.removeClass("d-none")
                            btnPreloader.addClass("d-none")
                        })

                    } else {

                        //Show next field set Add Class Active
                        $("#progressbar li").eq($("fieldset").index(next_fs)).addClass("active");

                        //show the next fieldset
                        next_fs.show();
                        //hide the current fieldset with style
                        current_fs.animate({
                            opacity: 0
                        }, {
                            step: function (now) {
                                // for making fielset appear animation
                                opacity = 1 - now;

                                current_fs.css({
                                    'display': 'none',
                                    'position': 'relative'
                                });
                                next_fs.css({
                                    'opacity': opacity
                                });
                            },
                            duration: 600
                        });
                    }
                }
            },
            'click .previous': function (ev) {
                current_fs = $(ev.target).parent();
                previous_fs = $(ev.target).parent().prev();

                //Remove class active
                $("#progressbar li").eq($("fieldset").index(current_fs)).removeClass("active");

                //show the previous fieldset
                previous_fs.show();

                //hide the current fieldset with style
                current_fs.animate({
                    opacity: 0
                }, {
                    step: function (now) {
                        // for making fielset appear animation
                        opacity = 1 - now;

                        current_fs.css({
                            'display': 'none',
                            'position': 'relative'
                        });
                        previous_fs.css({
                            'opacity': opacity
                        });
                    },
                    duration: 600
                });
            },
            'blur input[name=inputEmail]': function (ev) {
                ev.preventDefault()
                let inputEmail = $(ev.target)
                let email = inputEmail.val()
                if (email !== '') {
                    this._rpc({
                        route: `/users/${email}`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            inputEmail.val('')
                            inputEmail.addClass('is-invalid')
                            showAlertDialog("User Exists!", `User with same email ${email} already exists!`)
                        } else {
                            inputEmail.removeClass('is-invalid').addClass('is-valid')
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

        },
    })

})