odoo.define('theme_inseta.SdfRegistration', function (require) {
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

    publicWidget.registry.SdfRegistrationPage = publicWidget.Widget.extend({
        selector: '.sdf-registration',
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
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
            });
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

                current_fs.find('input:required, select:required, textarea:required, file:required').each(function (ev) {
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

                        // Get form
                        var form = $('#msform')[0];
                        // FormData object 
                        var formData = new FormData(form);
                        //append extra data to form
                        if($("#inputTel").val() !== "") formData.append('inputTelDialCode', itiTel.getSelectedCountryData().dialCode);
                        if($("#inputCellPhone").val() !== "") formData.append('inputCellDialCode', itiCell.getSelectedCountryData().dialCode);
                        if($("#inputFax").val() !== "") formData.append('inputFaxDialCode', itiFax.getSelectedCountryData().dialCode);
                        
                        let inputSubmit = $(ev.target)
                        let btnPreloader = $("#btn-preloader");
                        console.log('Sending request to server => '+ formData)
                        var xmlRequest = $.ajax({
                            type: "POST",
                            enctype: 'multipart/form-data',
                            url: "/sdf_registration_ajax",
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
            'click button[name=addEmployer]': function (ev) {
                ev.preventDefault();
                let inputSdlNo = $("input[name=inputSdfNo]")
                let sdlNo = inputSdlNo.val()
                let isValid = true
                if (sdlNo.trim() == '') {
                    // displayErrorMsg('Please provide employer SLD no and try again')
                    isValid = false
                    inputSdlNo.addClass('is-invalid')
                } else {
                    isValid = true
                    inputSdlNo.removeClass('is-invalid').addClass('is-valid')
                }
                //check existing SDL list to ensure sdl no is unique
                $('select[name="sdlNoList"] option').each(function () {
                    if ($(this).val() == sdlNo) {
                        isValid = false
                        showAlertDialog("Duplicate SDL No", "Please provide a Unique SDL No.")
                    }
                })
                //check if employer with SDL exists
                if (isValid) {
                    let btn = $(ev.target)
                    let btnHtml = btn.html() // cache the original content
                    btn.html("<i class='fa fa-spinner fa-spin'></i> working...")
                    btn.attr("disabled", true)
                    this._rpc({
                        route: `/organisation/${sdlNo}`,
                        params: {},
                    }).then(function (data) {
                        btn.html(btnHtml)
                        btn.attr("disabled", false)
                        if (!data.status) {
                            inputSdlNo.val('')
                            inputSdlNo.addClass('is-invalid')
                            showAlertDialog("SDL Not Found!", `Organsation With SDL No ${sdlNo} Not Found!`)
                        } else {
                            inputSdlNo.removeClass('is-invalid').addClass('is-valid')
                            //append SDL no to SDL select
                        
                            $('select[name="sdlNoList"]')
                                .append(`<option selected="selected" style="margin-bottom:10px" value="${sdlNo}">[${sdlNo}] ${data.name}</option>`)
                                .removeClass('is-invalid').addClass('is-valid')
                            //append input file for application letter
                            $("#divSdlFileList").append(`
                            <label style="font-size:9px" name="${sdlNo}">Appointment Letter<input type="file" name="${sdlNo}_sdf_appointment_letter" 
                                class="form-control-file form-control-sm" 
                                required="required" accept="image/*,application/pdf"/></label>
                                <div class="invalid-feedback">Upload Appointment Letter</div>`)
                            //increase employer count
                        }
                    }).guardedCatch(function (data) {
                        btn.html(btnHtml)
                        btn.attr("disabled", false)
                        console.log("Failed!");
                        isValid = false
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            'click button[name=removeEmployer]': function (ev) {
                ev.preventDefault();
                let selectedSdl = $('select[name="sdlNoList"] option:selected')
                let sdlNo = selectedSdl.val()
                //remove the SDL and corresponding input File
                selectedSdl.remove()
                $(`input[name=${sdlNo}_sdf_appointment_letter]`).remove()
                $(`label[name=${sdlNo}]`).remove()

                let sdlOptions = $('select[name="sdlNoList"] option')
                console.log("OPTION LEN " + sdlOptions.length)
                if (sdlOptions.length < 1) {
                    $('select[name="sdlNoList"]').removeClass("is-valid")
                }
            },
            'change select[name=selectSdfRole]': function(ev){
                let selectedRole = $(ev.target).val()
                let sdl_nos = []
                $('select[name="sdlNoList"] option').each(function () {
                    sdl_nos.push($(this).val())
                })
                console.log(`Selected SDL NOs ${sdl_nos}`)
                if(selectedRole !== ''){
                    this._rpc({
                        route: `/organisation/check_sdf_role`,
                        params: {"role": selectedRole, "sdl_nos": sdl_nos},
                    }).then(function (data) {
                        console.log('RESPONSE '+ JSON.stringify(data))
                        if (!data.status) {
                            $(ev.target).val('')
                            showAlertDialog("Validation Error!", `${data.message}`)
                        } 
                    }).guardedCatch(function (error) {
                        let msg = error.message.message
                        console.log(msg)
                        showAlertDialog("Server Error!", msg)
                    });
                }
            },
            'blur input[name=inputFname]': function (ev) {
                //auto populate SDF initials and change field to readonly
                ev.preventDefault()
                let inputFname = $(ev.target)
                let inputInitials = $("#inputInitials")
                let fname = inputFname.val()

                if (fname !== '') {
                    inputInitials.val(fname.charAt(0))
                    inputInitials.attr("readonly",true)
                }else{
                    inputInitials.val('')
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
                        var msg = data && data.message && data.message.message;
                        showAlertDialog("Unexpected Server Error", msg)
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
                        var msg = data && data.message && data.message.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            'change #selectAlternateIDtype': function (ev) {
                // If one of the options on the dropdown has been selected on the Alternate ID Type, 
                //then the RSA identification No must not be mandatory 
                //but the system must require the applicant to upload the selected document.
                
                let alternateID = $(ev.target).val()
                let elmIdproof = $("#divIdProof")
                let fileIdProof = $("#fileIdProof")
                let labelIdProof = $("label[for='fileIdProof']")
                let originalLabelIdProof = labelIdProof.html()

                let inputIdNo = $("#inputIdNo")
                let labelInputIdNo = $("label[for='inputIdNo']")
                let originalLabelIdNo = labelInputIdNo.html()

                if (alternateID === "") {

                    elmIdproof.addClass('d-none')
                    fileIdProof.attr("required", false)
                    labelIdProof.html(originalLabelIdProof)

                    inputIdNo.attr("required", true)
                    labelInputIdNo.html(originalLabelIdNo)

                } else {
                    elmIdproof.removeClass('d-none')
                    fileIdProof.attr("required", true)
                    labelIdProof.html('Upload Alternate ID Type Proof <span class="text-warning">*</span>')

                    inputIdNo.attr("required", false)
                    labelInputIdNo.html('R.S.A Identification No')
                    inputIdNo.removeClass('is-invalid')
                }
            },
            'blur input[name=inputIdNo]': function(ev){
                console.log('Validation RSA ID  ... ')
                let idNo = $(ev.target).val()
       
                if(idNo !== ''){
                    this._rpc({
                        route: `/check_sa_idno/${idNo}`,
                        params: {},
                    }).then(function (data) {
                        console.log('RSA ID No check response => '+ JSON.stringify(data))
                        if (!data.status) {
                            $(ev.target).val('')
                            showAlertDialog("Validation Error!", `${data.message}`)
                        }else{
                            //update gender and dob with identity data
                            $("#inputGender").val(data.data.gender)
                            $("#inputDob").val(formatToDatePicker(data.data.dob))
                            $("#inputDob").trigger("change")
                        } 
                    }).guardedCatch(function (error) {
                        let msg = error.message.message
                        console.log(msg)
                        showAlertDialog("Server Error!", msg)
                    });
                }
            },
            'click #checkCompletedSDFtraining': function (ev) {
                let checkCompletedTraining = $(ev.target)
                let inputTrainer = $("#inputAccreditedTrainer")
                let divTrainer = $("#divAccreditedTrainer")
                if (checkCompletedTraining.is(":checked")) {
                    divTrainer.removeClass('d-none')
                    inputTrainer.attr("required", true)
                } else {
                    divTrainer.addClass('d-none')
                    inputTrainer.attr("required", false)
                }
            }
        },

    })

})