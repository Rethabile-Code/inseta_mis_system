odoo.define('theme_inseta.NonlevyEmployerRegistration', function (require) {
    "use strict";

    require('web.dom_ready');
    var utils = require('web.utils');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var membership_data = false;
    var _t = core._t;

    //multi step vars
    var current_fs, next_fs, previous_fs; //fieldsets
    var opacity;

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

    function formatToDatePicker(date_str){
        //split 1988-01-23 00:00:00 and return datepicker format 01/31/2021
        if(date_str !== ''){
            let date = date_str.split(" ")[0]
            let data = date.split("-")
            if(data.length > 0) return `${data[2]}/${data[1]}/${data[0]}`;
        }
    }
    function getMembers() {
        return JSON.parse(localStorage.getItem('members'));
    }

    function setMember(data) {
        localStorage.setItem('members', JSON.stringify(data));
    }

    function getNextSn() {
        var data = JSON.parse(localStorage.getItem("members"));
        return (data != null) ? data.length + 1 : 0
    };

    publicWidget.registry.NonlevyEmployerRegistrationPage = publicWidget.Widget.extend({
        selector: '.nonlevy-registration',
        xmlDependencies: [
            '/theme_inseta/static/xml/add_training_committee.xml'
        ],
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                //initialize datepicker
                $('.datepicker').datepicker('destroy').datepicker({
                    onSelect: function(ev) {
                        $('.datepicker').trigger('blur')
                      },
                    dateFormat: 'mm/dd/yy',
                    changeMonth: true,
                    changeYear: true,
                    yearRange: '1920:2050',
                    maxDate: "+0d"
                });

            });
        },
        willStart: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                //garbage collect training committee list
                setMember(null)
                //initialize intl phone format
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

                var inputCellPhone = document.querySelector("#inputCellPhone");
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
                window.itiCell = itiCell

                var inputFax = document.querySelector("#inputFax");
                var itiFax = window.intlTelInput(inputFax, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiFax",
                  placeholderNumberType:"MOBILE",
                  preferredCountries: ["za"],
                  geoIpLookup: function(callback) {
                    $.blockUI({
                        'message': '<h2 class="text-white">Please wait ...</h2>'
                    });
                    $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                        $.unblockUI()
                        console.log("IP DATA "+ JSON.stringify(resp))
                        var countryCode = (resp && resp.country) ? resp.country : "za";
                        callback(countryCode);
                    });
                  },
                  utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                });
                window.itiFax = itiFax
                
                //cfo and contacts
                var inputCfoCellPhone = document.querySelector("#inputCfoCellPhone");
                var itiCfoCell = window.intlTelInput(inputCfoCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCfoCell",
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
                window.itiCfoCell = itiCfoCell

                var inputCfoTel = document.querySelector("#inputCfoTel");
                var itiCfoTel = window.intlTelInput(inputCfoTel, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCfoTel",
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
                window.itiCfoTel = itiCfoTel
                //ceo
                var inputCeoCellPhone = document.querySelector("#inputCeoCellPhone");
                var itiCeoCell = window.intlTelInput(inputCeoCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCeoCell",
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
                window.itiCeoCell = itiCeoCell

                var inputCeoTel = document.querySelector("#inputCeoTel");
                var itiCeoTel = window.intlTelInput(inputCeoTel, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCeoTel",
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
                window.itiCeoTel = itiCeoTel
                //contact
                var inputContactCellPhone = document.querySelector("#inputContactCellPhone");
                var itiContactCell = window.intlTelInput(inputContactCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiContactCell",
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
                window.itiContactCell = itiContactCell

                var inputContactTel = document.querySelector("#inputContactTel");
                var itiContactTel = window.intlTelInput(inputContactTel, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiContactTel",
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
                window.itiContactTel = itiContactTel
                //training committee contact phone
                var inputMemberCellPhone = document.querySelector("#inputMemberCellPhone");
                var itiMemberCell = window.intlTelInput(inputMemberCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiMemberCell",
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
                window.itiMemberCell = itiMemberCell

                var inputMemberTel = document.querySelector("#inputMemberTel");
                var itiMemberTel = window.intlTelInput(inputMemberTel, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiMemberTel",
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
                window.itiMemberTel = itiMemberTel
            });
        },
        //--------------------------------------------------------------------------
        // private methods
        //--------------------------------------------------------------------------

        _renderCommitteeList: function () {
            var self = this;
            let members = getMembers();
           
            var $lines = $(qweb.render('theme_inseta.training_committee_lines', {
                widget: self,
                childs: members || [],
            }));
            if ($lines) {
                self.$el.find('#member-list').html("");
                self.$el.find('#member-list').append($lines);
            }
            
        },
        events: {
            //multi step
            'blur input, select, textarea': function (ev) {
                let input = $(ev.target)
                if (input.is(":required") && input.val() !== '') {
                    input.removeClass('is-invalid').addClass('is-valid')
                } else if (input.is(":required") && input.val() == '') {
                    input.addClass('is-invalid')
                }
            },
            'click .next': function (ev) {

                current_fs = $(ev.target).parent();
                next_fs = $(ev.target).parent().next();

                var next_step = true;
                let validEmail = false
                let validCell = false

                current_fs.find('input:required, select:required, textarea:required').each(function (ev) {
                    console.log('Required Fields')
                    if ($(this).val() == "") {
                        $(this).addClass('is-invalid');
                        next_step = false;
                    } else {
                        $(this).removeClass('is-invalid').addClass('is-valid')
                    }
                });

                let inputCellPhone = $("#inputCellPhone");
                if(!validatePhone(inputCellPhone.val())){
                    inputCellPhone.addClass("is-invalid")
                }else{
                    inputCellPhone.removeClass('is-invalid').addClass("is-valid")
                    validCell = true
                }

                //validate email and cell phone
                let inputEmail = $("#inputEmail");
                if(!validateEmail(inputEmail.val())){
                    inputEmail.addClass("is-invalid")
                }else{
                    inputEmail.removeClass('is-invalid').addClass("is-valid")
                    validEmail= true
                }
                if(validEmail && validCell && next_step){
                    next_step = true
                }else{
                    next_step = false
                }

                if (next_step) {
                    //if the next button is submit, then submit the form before showing next fieldset
                    if ($(ev.target).val() == "Confirm") {

                        //ensure user checks the confirmation checkbox
                        const checkConfirm = $("#checkConfirm")
                        if (!checkConfirm.is(":checked")) {
                            checkConfirm.addClass("is-invalid")
                            return false
                        } else {
                            checkConfirm.removeClass("is-invalid").addClass('is-valid')
                        }

                        const trainingCommitteeMembers = getMembers();

                        //medium/large organisation must submit training committee
                        const orgSizeSaqaCode  = $("#orgSizeSaqacode").val();
                        if(orgSizeSaqaCode !== "small_nonlevy" && trainingCommitteeMembers == null){
                            showAlertDialog('Validation Error!', 
                                'Medium/Large Organisation are required to submit Training Committee. '+
                                'Please add training committee member and try again') 
                            return false;
                        }

                        //check if user uploads mandatoruy docs
                        var payrollUpload = $('#fileAnnualPayroll').val(); 
                        if(payrollUpload =='') 
                        { 
                            showAlertDialog("Validation Error", "Please upload Annual Payroll")
                            return false; 
                        } 

                        // Get form
                        var form = $('#msform')[0];
                        // FormData object 
                        var formData = new FormData(form);
                        //append extra data to form
                        if($("#inputTel").val() !== "") formData.append('inputTelDialCode', itiTel.getSelectedCountryData().dialCode);
                        if($("#inputCellPhone").val() !== "") formData.append('inputCellDialCode', itiCell.getSelectedCountryData().dialCode);
                        if($("#inputFax").val() !== "") formData.append('inputFaxDialCode', itiFax.getSelectedCountryData().dialCode);
                        //contact
                        if($("#inputContactTel").val() !== "") formData.append('inputContactTelDialCode', itiContactTel.getSelectedCountryData().dialCode);
                        if($("#inputContactCellPhone").val() !== "") formData.append('inputContactCellDialCode', itiContactCell.getSelectedCountryData().dialCode);
                        //ceo
                        if($("#inputCeoTel").val() !== "") formData.append('inputCeoTelDialCode', itiCeoTel.getSelectedCountryData().dialCode);
                        if($("#inputCeoCellPhone").val() !== "") formData.append('inputCeoCellDialCode', itiCeoCell.getSelectedCountryData().dialCode);
                        //cfo
                        if($("#inputCfoTel").val() !== "") formData.append('inputCfoTelDialCode', itiCfoTel.getSelectedCountryData().dialCode);
                        if($("#inputCfoCellPhone").val() !== "") formData.append('inputCfoCellDialCode', itiCfoCell.getSelectedCountryData().dialCode);

                        let members = getMembers()
                        if(members) formData.append('training_committee', JSON.stringify(members));

                        let inputSubmit = $(ev.target)
                        let btnPreloader = $("#btn-preloader");
                        console.log('Sending request to server => '+ formData)
                        var xmlRequest = $.ajax({
                            type: "POST",
                            enctype: 'multipart/form-data',
                            url: "/nonlevy_registration_ajax",
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
            //set sic code desc on changes of sic code select
            'change select[name=selectSicCode]': function(ev){
                let elm = $(ev.target)
                $("#inputSicCodeDesc").val(''); //clear the previously set sic code desc
                if(elm.val() !== ''){
                    // sic code is displayed on the UI in format 008876 - Reinsurance
                    //we will split the string and take the item at index 1
                    let selectedSicText = $("select[name=selectSicCode] option:selected").text();
                    console.log(selectedSicText)
                    let data = selectedSicText.split("|");
                    let sicDesc = data[1].trim();
                    $("#inputSicCodeDesc").val(sicDesc);
                }
            
            },
            'change #inputNoEmployees': function(ev){
                let elm = $(ev.target)
                let noEmployees = elm.val();
                let orgSizes = $("input[name=orgSizesList]").val();
                let size = null
                if(orgSizes != ''){
                    
                    if(noEmployees > 49){
                        showAlertDialog("Validation Error", "Organisations with no employees greater than 49 are not allowed to register online.")
                        elm.val('') //reset the value
                        return
                    }

                    //TODO: Refactor Code below to consider only small organisation
                    let orgSizesArray = JSON.parse(orgSizes)
                    console.log(orgSizesArray)
                    if(noEmployees <= 49 ){
                        size = orgSizesArray.find(item => item.saqacode === "small_nonlevy" )
                    }
                    if(size !== null || size != undefined){
                        $("#selectOrgSize").val(size.id)
                        $("#selectOrgSize option:selected").text(size.name)
                        $("#orgSizeSaqacode").val(size.saqacode)
                    }
                }

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
            'blur input[name=inputPhysicalCode]': function (ev) {
                ev.preventDefault()
                let inputPhyiscalCode = $(ev.target)
                if (inputPhyiscalCode.val() !== '') {
                    console.log("Calling check physical code ...")
                    this._rpc({
                        route: `/sdf/check_physical_code/${inputPhyiscalCode.val()}`,
                        params: {},
                    }).then(function (data) {
                        console.log("PHY CODE DATA " + JSON.stringify(data))
                        console.log("Setting Physical address ...")
                        let selectProvince = $("#selectPhysicalProvince option:selected")
                        let selectCity = $("#selectPhysicalCity option:selected")
                        let municipality = $("#selectPhysicalMunicipality option:selected")
                        let suburb = $("#selectPhysicalSuburb option:selected")
                        let urbanRual = $("#selectPhysicalUrbanRural option:selected")
                        if (data.status) {
                            selectProvince.val(data.province.id).text(data.province.name).removeClass('is-invalid').addClass('is-valid')
                            selectCity.val(data.city.id).text(data.city.name).removeClass('is-invalid').addClass('is-valid')
                            municipality.val(data.municipality.id).text(data.municipality.name).removeClass('is-invalid').addClass('is-valid')
                            suburb.val(data.suburb.id).text(data.suburb.name).removeClass('is-invalid').addClass('is-valid')
                            urbanRual.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                        } else {
                            selectProvince.val('').text('').addClass('is-valid')
                            selectCity.val('').text('').addClass('is-valid')
                            municipality.val('').text('').addClass('is-valid')
                            suburb.val('').text('').addClass('is-valid')
                            urbanRual.val('').text('').addClass('is-valid')
                        }
                    }).guardedCatch(function (data) {
                        console.log(JSON.stringify(data))
                        let msg = data && data.message && data.message.message;
                        console.log(`Error checking physical code ${msg}`)
                        //showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            'click input[name=checkUsePhysicalForPostal]': function (ev) {
                let checkbox = $(ev.target)
                //physical fields
                let inputPhyCode = $("#inputPhysicalCode")
                let inputPhyAddr1 = $("#inputPhysicalAddr1")
                let inputPhyAddr2 = $("#inputPhysicalAddr2")
                let inputPhyAddr3 = $("#inputPhysicalAddr3")

                let selectPhyProvince = $("#selectPhysicalProvince option:selected")
                let selectPhyCity = $("#selectPhysicalCity option:selected")
                let selectPhyMunicipality = $("#selectPhysicalMunicipality option:selected")
                let selectPhySuburb = $("#selectPhysicalSuburb option:selected")
                let selectPhyUrbanRural = $("#selectPhysicalUrbanRural option:selected")
                //postal fields
                let inputPostalCode = $("#inputPostalCode")
                let inputPostalAddr1 = $("#inputPostalAddr1")
                let inputPostalAddr2 = $("#inputPostalAddr2")
                let inputPostalAddr3 = $("#inputPostalAddr3")

                let selectPoProvince = $("#selectPostalProvince option:selected")
                let selectPoCity = $("#selectPostalCity option:selected")
                let selectPoMunicipality = $("#selectPostalMunicipality option:selected")
                let selectPoSuburb = $("#selectPostalSuburb option:selected")
                let selectPoUrbanRural = $("#selectPostalUrbanRural option:selected")

                if (checkbox.is(":checked")) {
                    inputPostalCode.val(inputPhyCode.val())
                    inputPostalAddr1.val(inputPhyAddr1.val())
                    inputPostalAddr2.val(inputPhyAddr2.val())
                    inputPostalAddr3.val(inputPhyAddr3.val())

                    selectPoProvince.val(selectPhyProvince.val()).text(selectPhyProvince.text())
                    selectPoCity.val(selectPhyCity.val()).text(selectPhyCity.text())
                    selectPoMunicipality.val(selectPhyMunicipality.val()).text(selectPhyMunicipality.text())
                    selectPoSuburb.val(selectPhySuburb.val()).text(selectPhySuburb.text())
                    selectPoUrbanRural.val(selectPhyUrbanRural.val()).text(selectPhyUrbanRural.text())
                } else {
                    inputPostalCode.val('')
                    inputPostalAddr1.val('')
                    inputPostalAddr2.val('')
                    inputPostalAddr3.val('')

                    selectPoProvince.val('').text('')
                    selectPoCity.val('').text('')
                    selectPoMunicipality.val('').text('')
                    selectPoSuburb.val('').text('')
                    selectPoUrbanRural.val('').text('')
                }
            },
            'blur input[name=inputPostalCode]': function (ev) {
                ev.preventDefault()
                let inputPostalCode = $(ev.target)
                if (inputPostalCode.val() !== '') {
                    console.log("Calling check postal code ...")
                    this._rpc({
                        route: `/sdf/check_physical_code/${inputPostalCode.val()}`,
                        params: {},
                    }).then(function (data) {
                        console.log("Postal Code Data " + JSON.stringify(data))
                        console.log("Setting Postal address ...")
                        let selectProvince = $("#selectPostalProvince option:selected")
                        let selectCity = $("#selectPostalCity option:selected")
                        let municipality = $("#selectPostalMunicipality option:selected")
                        let suburb = $("#selectPostalSuburb option:selected")
                        let urbanRual = $("#selectPostalUrbanRural option:selected")
                        if (data.status) {
                            selectProvince.val(data.province.id).text(data.province.name).removeClass('is-invalid').addClass('is-valid')
                            selectCity.val(data.city.id).text(data.city.name).removeClass('is-invalid').addClass('is-valid')
                            municipality.val(data.municipality.id).text(data.municipality.name).removeClass('is-invalid').addClass('is-valid')
                            suburb.val(data.suburb.id).text(data.suburb.name).removeClass('is-invalid').addClass('is-valid')
                            urbanRual.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                        } else {
                            selectProvince.val('').text('').addClass('is-valid')
                            selectCity.val('').text('').addClass('is-valid')
                            municipality.val('').text('').addClass('is-valid')
                            suburb.val('').text('').addClass('is-valid')
                            urbanRual.val('').text('').addClass('is-valid')
                        }
                    }).guardedCatch(function (data) {
                        console.log(JSON.stringify(data))
                        let msg = data && data.message && data.message.message;
                        console.log(`Error checking postal code ${msg}`)

                        //showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            'blur input[name=inputCfoFname]': function (ev) {
                //auto populate CFO initials and change field to readonly
                ev.preventDefault()
                let inputCfoFname = $(ev.target)
                let inputInitials = $("#inputCfoInitials")
                let fname = inputCfoFname.val()
                if (fname !== '') {
                    inputInitials.val(fname.charAt(0))
                    inputInitials.attr("readonly",true)
                }else{
                    inputInitials.val('')
                }
            },
            'blur input[name=inputCeoFname]': function (ev) {
                //auto populate CFO initials and change field to readonly
                ev.preventDefault()
                let inputCeoFname = $(ev.target)
                let inputInitials = $("#inputCeoInitials")
                let fname = inputCeoFname.val()
                if (fname !== '') {
                    inputInitials.val(fname.charAt(0))
                    inputInitials.attr("readonly",true)
                }else{
                    inputInitials.val('')
                }
            },
            'blur input[name=inputContactFname]': function (ev) {
                //auto populate CFO initials and change field to readonly
                ev.preventDefault()
                let inputContactFname = $(ev.target)
                let inputInitials = $("#inputContactInitials")
                let fname = inputContactFname.val()
                if (fname !== '') {
                    inputInitials.val(fname.charAt(0))
                    inputInitials.attr("readonly",true)
                }else{
                    inputInitials.val('')
                }
            },
            'submit #add-member-form': function (ev) {
                ev.preventDefault();
                console.log("Submit triggered")

                var self = this;            
                if (!validatePhone($("#inputMemberCellPhone").val())) {
                    return;
                }

                let members = getMembers();
                if (!members || members == undefined) {
                    members = []
                }
                let form_data = $(ev.target).serializeJSON();
                form_data['sn'] = getNextSn()
                members.push(form_data);
                setMember(members);
                setTimeout(function () {
                    $('#add-member-modal').modal('hide');
                    self._renderCommitteeList();
                }, 10);
                
                return false;
            },
            'shown.bs.modal #add-member-modal': function (ev) {
                $('#add-member-form')[0].reset();
            },
            'shown.bs.modal #remove-member-modal': function (ev) {

                let self = this;
                ev.preventDefault();
                let button = $(ev.relatedTarget) // Button that triggered the modal
                let sn = button.data('sn')
                let firstname = button.data("firstname")
                $("#rm-name").text(firstname)

                self.$el.find("#remove-member").click(function(ev){
                    ev.preventDefault();
                    let members = getMembers();
                    var itemIndex = members.findIndex(v => v.sn === sn)
    
                    members.splice(itemIndex, 1);
                    setMember(members);
                    setTimeout(function () {
                        $('#remove-member-modal').modal('hide');
                        self._renderCommitteeList();
                    }, 10);
                })
            },
        },

    })

})