odoo.define('theme_inseta.AssessorModeratorModule', function (require) {
    "use strict";

    require('web.dom_ready');
    var utils = require('web.utils');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    //multi step vars
    var current_fs, next_fs, previous_fs; //fieldsets
    var opacity;
    var host = window.location.origin;
    var url = window.location.href;
    var moderatorPage = host + "/moderator-registration";
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

    publicWidget.registry.AssessorModeratorPage = publicWidget.Widget.extend({
        selector: '.assessor-moderator-register',
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                $('.datepicker').datepicker('destroy').datepicker({
                    onSelect: function(ev) {
                        $('.datepicker').trigger('blur')
                      },
                    dateFormat: 'dd/mm/yy',
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
                //using the same js file for both moderator and assessor page
                // is the register_type checkbox is true, it indicates that a moderator 
                // registration page else assessor registration page

                var regType = $("#reqister_type");
                var checkIsassessor = $("#is_assessor_box");
                var progDiv = $("#progDiv");
                var idDiv = $("#idDiv"); 
        
                var InputAssessorNo = $("#InputAssessorNo");
                if (url.indexOf(moderatorPage) != -1){
                    regType.prop('checked', true);
                    checkIsassessor.removeClass('d-none')
                    InputAssessorNo.addClass('is-invalid').removeClass('is-valid')
                    $('#register_label').text('Moderator Registration')
                    // progDiv.addClass('d-none')
                    $('#inputIdNo').removeClass('is-invalid').addClass('is-valid')
                    // $('#unit_standard_ids').removeClass('is-invalid').addClass('is-valid')
                    // $('#qualification_ids').removeClass('is-invalid').addClass('is-valid')
                    idDiv.addClass('d-none')
                    $('#inputFname').prop('readonly', true);
                    $('#inputMname').prop('readonly', true);
                    // $('#unit_standard_ids').prop('required', false);
                    // $('#qualification_ids').prop('required', false);
                    // $('#unit_standard_ids').removeClass('is-invalid').addClass('is-valid')
                    // $('#qualification_ids').removeClass('is-invalid').addClass('is-valid')
                    // $('#scope-warning').removeClass('d-none')
                }else{
                    regType.prop('checked', false);
                    $('#register_label').text('Assessor Registration')
                    InputAssessorNo.prop('required', false);
                    checkIsassessor.addClass('d-none')
                    InputAssessorNo.removeClass('is-invalid').addClass('is-valid')
                    // progDiv.removeClass('d-none')
                }
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
                    // showAlertDialog('Validation Error!', 'Please provide all valid fields')
                }
            },
 

            'click .next': function (ev) {
                current_fs = $(ev.target).parent();
                next_fs = $(ev.target).parent().next();
                var next_step = true;
                let requiredItems = []

                current_fs.find('input:required, select:required, textarea:required').each(function (ev) {
                    if ($(this).val() == "") {
                        $(this).addClass('is-invalid');
                        console.log('Required - Fields == > ', $(this).attr('name'))
                        next_step = false;
                        requiredItems.push($(this).attr('name'))

                    } else {
                        $(this).removeClass('is-invalid').addClass('is-valid')
                    }
                });
                if (requiredItems.length > 0){
                    alert(`Required fields ==> ${requiredItems.join()}`)
                }

                let inputCellPhone = $("#inputCellPhone");
                if(!validatePhone(inputCellPhone.val())){
                    inputCellPhone.addClass("is-invalid")
                    next_step = false
                }else{
                    inputCellPhone.removeClass('is-invalid').addClass("is-valid")
                   //next_step = true
                }

                //validate email and cell phone and required fields
                let inputEmail = $("#inputEmail");
                if(!validateEmail(inputEmail.val())){
                    inputEmail.addClass("is-invalid")
                    next_step = false
                }else{
                    inputEmail.removeClass('is-invalid').addClass("is-valid")
                    //next_step = true
                }

                // if(validatePhone(inputCellPhone.val()) && validateEmail(inputEmail.val())){
                //     next_step = true
                // }

                // if(!validateFields($("#inputFname").val())){
                //     $("#inputFname").addClass("is-invalid")
                //     next_step = false
                // }
                // else{
                //     $("#inputFname").removeClass('is-invalid').addClass("is-valid")
                //     //next_step = true
                // }

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
                            url: "/moderator_assessor_registration_ajax",
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
                            console.log(`Registration. TextStatus: ${textStatus}. Statuscode:  ${jqXHR.status}`);
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

            // here
            'blur input[name=inputQual]': function (ev) {
                ev.preventDefault()
                let inputQual = $(ev.target)
                let progCode = inputQual.val()
                if (progCode.trim() !== '') {
                    $('select[name="inputQual"] option').each(function () {
                        if ($(this).val() == progCode) {
                            showAlertDialog("Programme Already Selected", "Please provide a Unique Programme code.")
                        }
                    })
                    this._rpc({
                        route: `/get-programme/${progCode}/qualification`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            // progCode.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="qualification_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputQual.val('')
                            
                        } else {
                            showAlertDialog("Invalid Programme !", `Programme with code ${progCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            'blur input[name=InputAssessorNo]': function (ev) {
                ev.preventDefault()
                let inputQual = $(ev.target)
                let progCode = inputQual.val()
                if (progCode.trim() !== '') {
                    this._rpc({
                        route: `/get-assessor-moderator/${progCode}/assessor`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            inputQual.removeClass('is-invalid').addClass('is-valid')
                            $('#updatedetails').removeClass('d-none')
                             
                        } else {
                            inputQual.val('')
                            inputQual.addClass('is-invalid').removeClass('is-valid')
                            showAlertDialog("Invalid Assessor !", `Please note that only a valid Assessor can register as a moderator`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
                else{
                    $('#updatedetails').addClass('d-none')
                }
            },

            'click .updatedetails': function (ev) {
                ev.preventDefault()
                let AssNo = $('#InputAssessorNo').val()
                this._rpc({
                    route: `/get-assessor-moderator/${AssNo}/assessor`,
                    params: {},
                }).then(function (data) {
                    if (data.status) {
                        // render programme scope of assessor
                        let UnitStandardprogrammeData = data.udata
                        let QualificationprogrammeData = data.qdata
                        if (UnitStandardprogrammeData){
                            $('select[name="unit_standard_ids"]').empty()
                            UnitStandardprogrammeData.forEach((object) => {
                                $('select[name="unit_standard_ids"]')
                                .append(`<option selected="selected" value="${object['id']}">[${object['code']}] - ${object['name']}</option>`)
                            })
                        }
                        if (QualificationprogrammeData){
                            $('select[name="qualification_ids"]').empty()
                            QualificationprogrammeData.forEach((object) => {
                                $('select[name="qualification_ids"]')
                                .append(`<option selected="selected" value="${object['id']}">[${object['code']}] - ${object['name']}</option>`)
                            })
                        }
                        
                        // Making scope readonly and not required 
                        $('#unit_standard_ids').attr('required', false);
                        $('#qualification_ids').attr('required', false);
                        $('#unit_standard_ids').attr('disabled', true);
                        $('#qualification_ids').attr('disabled', true);
                        $('#qualification_ids').removeClass('is-invalid').addClass('is-valid')
                        $('#scope-warning').removeClass('d-none')
                        //
                        $("#inputTitle").val(data.data.title_id) //.id).text(data.data.title_id.name)
                        $("#inputFname").val(data.data.first_name ? data.data.first_name  : '')
                        $("#inputLname").val(data.data.last_name ? data.data.last_name  : '')
                        $("#inputMname").val(data.data.middle_name ? data.data.middle_name  : '')
                        $("#inputEmail").val(data.data.email ? data.data.email  : '')
                        $("#inputTel").val(data.data.telephone_number ? data.data.telephone_number.slice(-10) : '') 
                        $("#inputCellPhone").val(data.data.cell_phone_number ? data.data.cell_phone_number.slice(-10) : '')
                        $("#inputFax").val(data.data.fax_number)
                        $("#inputPassportNo").val(data.data.passport_no)
                        $("#inputIdNo").val(data.data.id_no)
                        $("#inputGender").val(data.data.gender_id)
                        $("#inputDob").val(data.data.birth_date)
                        $("#inputInitials").val(data.data.initials)
                         
                        $("#popi_act_status_id").val(data.data.popi_act_status_id) //.id).text(data.data.nationality_id.name)
                        $("#school_emis_id").val(data.data.school_emis_id) //.id).text(data.data.nationality_id.name)
                        $("#latitude_degree").val(data.data.latitude_degree) //.id).text(data.data.nationality_id.name)
                        $("#statssa_area_code_id").val(data.data.statssa_area_code_id) //.id).text(data.data.nationality_id.name)
                        
                        $("#selectNationality").val(data.data.nationality_id) //.id).text(data.data.nationality_id.name)
                        $("#selectHomeLanguage").val(data.data.home_language_id) //.id).text(data.data.home_language_id.name)
                        $("#selectAlternativeType").val(data.data.alternateid_type_id)//.id).text(data.data.home_language_id.name)
                        $("#selectEquity").val(data.data.equity_id) //.id).text(data.data.equity_id.name)
                        $("#selectDisabilityStatus").val(data.data.disability_id) //.id).text(data.data.disability_id.name)
                        $("#is_permanent_consultant").val(data.data.is_permanent_consultant) 

                        $("#job_title").val(data.data.job_title)
                        $("#inputPhysicalCode").val(data.data.physical_code)
                        $("#inputPhysicalAddr1").val(data.data.physical_address1)
                        $("#inputPhysicalAddr2").val(data.data.physical_address2)
                        $("#inputPhysicalAddr3").val(data.data.physical_address3)
                        $("#selectPhysicalProvince").val(data.data.physical_province_id) //.id).text(data.data.physical_province_id.name)
                        $("#selectPhysicalCity").val(data.data.physical_city_id) //.id).text(data.data.physical_city_id.name)
                        $("#selectPhysicalMunicipality").val(data.data.physical_municipality_id) //.id).text(data.data.physical_municipality_id.name)
                        $("#selectPhysicalSuburb").val(data.data.physical_suburb_id) //.id).text(data.data.physical_suburb_id.name)
                        $("#selectPhysicalUrbanRural").val(data.data.physical_urban_rural)
                        $("#inputPostalCode").val(data.data.postal_code)
                        $("#inputPostalAddr1").val(data.data.postal_address1)
                        $("#inputPostalAddr2").val(data.data.postal_address2)
                        $("#inputPostalAddr3").val(data.data.postal_address3)
                        $("#selectPostalProvince").val(data.data.postal_province_id) // .id).text(data.data.postal_province_id.name)
                        $("#selectPostalCity").val(data.data.postal_city_id) //.id).text(data.data.postal_city_id.name)
                        $("#selectPostalMunicipality").val(data.data.postal_municipality_id) //.id).text(data.data.postal_municipality_id.name)
                        $("#selectPostalSuburb").val(data.data.postal_suburb_id) //.id).text(data.data.postal_suburb_id.name)
                        $("#selectPostalUrbanRural").val(data.data.postal_urban_rural)
                             
                    } else {
                        $('#InputAssessorNo').val('')
                        $('#InputAssessorNo').addClass('is-invalid').removeClass('is-valid')
                        $('#unit_standard_ids').prop('required', true);
                        $('#qualification_ids').prop('required', true);
                        $('#unit_standard_ids').prop('readonly', false);
                        $('#qualification_ids').prop('readonly', false);
                        $('#qualification_ids').removeClass('is-valid').addClass('is-invalid')
                        $('#scope-warning').addClass('d-none')
                        showAlertDialog("Invalid Assessor Identification / Reg No.!", `Please note that only a valid Assessor can register as a moderator`)
                    }
                }).guardedCatch(function (data) {
                    var msg = data && data.data && data.data.message;
                    showAlertDialog("Unexpected Server Error", msg)
                });
            },

            'change input[name=is_assessorid]': function(ev){
                let is_assessorid = $(ev.target)
                if (is_assessorid.is(":checked")) {
                    console.log("is checked")
                    $('#assessordiv').removeClass("d-none")
                    // $('#InputAssessorNo').removeClass("is-valid").addClass('is-invalid')
                    // return false
                } else {
                    $('#assessordiv').addClass("d-none")
                    console.log("is not checked")
                    // $('#InputAssessorNo').addClass("is-valid").removeClass('is-invalid')
                }

            },

            'change select[name=selectAlternativeType]': function(ev){
                let selectAlternativeType = $(ev.target).val()
                if(selectAlternativeType === "" || selectAlternativeType === '10'){
                    console.log('SET NO IDXXX')
                    $('#inputIdNo').removeClass('d-none')
                    $('#inputIdNo').addClass('is-invalid').removeClass('is-valid')
                    $('#inputPassportNo').addClass('d-none')
                    $('#inputPassportNo').removeClass('is-invalid').addClass('is-valid')
                    $('#inputPassportNo').val('')
                    
                }
                else{
                    console.log('SET IDCCC')
                    console.log(selectAlternativeType)
                    $('#inputIdNo').val('')
                    $('#inputIdNo').addClass('d-none')
                    $('#inputIdNo').removeClass('is-invalid').addClass('is-valid')
                    $('#inputpasspartdiv').removeClass('d-none')
                    $('#inputPassportNo').addClass('is-invalid').removeClass('is-valid')
                    $('#inputPassportNo').removeClass('d-none')
                }
            },
            'blur input[name=inputPassportNo]': function(ev){
                let idNo = $(ev.target)
                $('#inputPassportNo').removeClass('is-invalid').addClass('is-valid')
            },

            'blur input[name=inputMname]': function(ev){
                let middlename = $(ev.target)
                let Lname = $('#inputLname')
                let Fname = $('#inputFname')
                if (middlename.val() !== "" && Fname.val() !== ""){
                    let fname = Fname.val()[0]
                    let mname = middlename.val()[0]
                    let initial = `${fname}${mname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
                else if (middlename.val() == "" && $('#inputFname').val() !== "" || $('#inputLname').val() !== "")
                {
                    let fname = Fname.val() !== "" ? Fname.val()[0] : ""
                    let lname = Lname.val() !== "" ? Lname.val()[0] : ""
                    let initial = `${fname}${lname}`.toUpperCase()
                    $('#inputInitials').val(initial)

                }
            },

            'blur input[name=inputFname]': function(ev){
                let firstname = $(ev.target)
                let Mname = $('#inputMname')
                let Lname = $('#inputLname')
                if (firstname.val() !== "" && Mname.val() !== ""){
                    let fname = firstname.val()[0]
                    let mname = Mname.val()[0]
                    let initial = `${fname}${mname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
                // else if (firstname.val() == "" && Mname.val() !== "" || Lname.val() !== "")
                // {
                // console.log('nooo')

                //     let mname = Mname.val() !== "" ? Mname.val()[0] : ""
                //     let lname = Lname.val() !== "" ? Lname.val()[0] : ""
                //     let initial = `${mname}${lname}`.toUpperCase()
                //     $('#inputInitials').val(initial)
                // }
                else if (firstname.val() !== "" && Lname.val() !== "")
                {
                    let fname = firstname.val() !== "" ? firstname.val()[0] : ""
                    let lname = Lname.val() !== "" ? Lname.val()[0] : ""
                    let initial = `${fname}${lname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
            },
            
            'blur input[name=inputLname]': function(ev){
                let Lname = $(ev.target)
                let Mname = $('#inputMname')
                let Fname = $('#inputFname')
                if (Lname.val() !== "" && Mname.val() !== ""){
                    let fname = Fname.val()[0]
                    let mname = Mname.val()[0]
                    let initial = `${fname}${mname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
                else if (Lname.val() !== "" && Fname.val() !== ""){
                    let fname = Fname.val()[0]
                    let lname = Lname.val()[0]
                    let initial = `${fname}${lname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
                else if (Lname.val() == "" && Mname.val() !== "" || Fname.val() !== "")
                {
                    let mname = Mname.val() !== "" ? Mname.val()[0] : ""
                    let fname = Fname.val() !== "" ? Fname.val()[0] : ""
                    let initial = `${fname}${mname}`.toUpperCase()
                    $('#inputInitials').val(initial)
                }
            },

            'blur input[name=inputIdNo]': function(ev){
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
                            $('#inputIdNo').removeClass('is-invalid').addClass('is-valid')
                        } 
                    }).guardedCatch(function (error) {
                        let msg = error.message.message
                        console.log(msg)
                        showAlertDialog("Server Error!", msg)
                    });
                }
            },

            'blur input[name=inputUnitStandard]': function (ev) {
                ev.preventDefault()
                let inputQual = $(ev.target)
                let progCode = inputQual.val()
                if (progCode.trim() !== '') {
                    $('select[name="inputUnitStandard"] option').each(function (v) {
                        if ($(v).val() == progCode) {
                            showAlertDialog("Programme Already Selected", "Please provide a Unique Programme code.")
                        }
                    })
                    this._rpc({
                        route: `/get-programme/${progCode}/unitstandard`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            // progCode.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="unit_standard_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">[${data.data.code}] - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputQual.val('')
                            
                        } else {
                            showAlertDialog("Invalid Programme !", `Programme with code ${progCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
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

            'blur input[name=inputsdl]': function (ev) {
                ev.preventDefault()
                let inputsdl = $(ev.target)
                let sdlNo = inputsdl.val()
                if (sdlNo !== '') {
                    this._rpc({
                        route:`/organisation/${sdlNo}`,
                        params: {},
                    }).then(function (data) {
                        if (!(data.status)) {
                            inputsdl.val('')
                            inputsdl.addClass('is-invalid')
                            showAlertDialog("SDL Not Found!", `Organsation With approved SDL No ${sdlNo} Not Found!`)
                            
                        } else {
                            inputsdl.removeClass('is-invalid').addClass('is-valid')
                        }
                        console.log(`sdl ${data.status}`)
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            'blur input[name=inputPhysicalAddr1]': function(ev){
                ev.preventDefault();
                let inputPhysicalAddr1 = $(ev.target);
                let inputPhyiscalCode = $('#inputPhysicalCode') 
                let selectProvince = $("#selectPhysicalProvince option:selected")
                let selectCity = $("#selectPhysicalCity option:selected")
                let nationality = $("#selectNationality option:selected")
                let numeric_alpha = /^(?=.*[a-zA-Z])(?=.*[0-9])/;
                if (inputPhysicalAddr1.val().match(numeric_alpha)) {
                    console.log('pass')
                    $('#inputPhysicalAddr1').removeClass('is-invalid').addClass("is-valid")
                    this._rpc({
                        route: `/get_geolocation/${inputPhysicalAddr1.val()}/${inputPhyiscalCode.val()}/${selectCity.val()}/${selectProvince.val()}/${nationality.val()}`,
                        params: {},
                    }).then(function (data) {
                        console.log('LATITUDE  ', data);
                        if (data.status){
                            $('#inputLatitude').val(data.latitude_degree).text(data.latitude_degree);
                            $('#inputLongtitude').val(data.longitude_degree).text(data.longitude_degree);
                        console.log(data.latitude_degree);
                        }else{
                            console.log("No data");
                            $('#inputLatitude').val("");
                            $('#inputLongtitude').val("");
                        }
                    })
                }else{
                    inputPhysicalAddr1.val("")
                    $('#inputPhysicalAddr1').removeClass('is-valid').addClass("is-invalid")
                    $('#inputLatitude').val("");
                    $('#inputLongtitude').val("");
                    showAlertDialog("Validation Message", "Physical Address must contain alphanumeric values eg. 34 Maduka Street")
                }
            },

            'blur input[name=inputPhysicalCode]': function (ev) {
                ev.preventDefault()
                let inputPhyiscalCode = $(ev.target)
                let selectProvince = $("#selectPhysicalProvince option:selected")
                let selectCity = $("#selectPhysicalCity option:selected")
                let municipality = $("#selectPhysicalMunicipality option:selected")
                let suburb = $("#selectPhysicalSuburb option:selected")
                let urbanRural = $("#selectPhysicalUrbanRural option:selected")
                let nationality = $("#selectNationality option:selected")
                
                if (inputPhyiscalCode.val().length === 4) {
                    if (inputPhyiscalCode.val() !== '') {
                        console.log("Calling check physical code ...")
                        this._rpc({
                            route: `/sdf/check_physical_code/${inputPhyiscalCode.val()}`,
                            params: {},
                        }).then(function (data) {
                            console.log("PHY CODE DATA " + JSON.stringify(data))
                            console.log("Setting Physical address ...")
                            if (data.status) {
                                selectProvince.val(data.province.id).text(data.province.name).removeClass('is-invalid').addClass('is-valid')
                                selectCity.val(data.city.id).text(data.city.name).removeClass('is-invalid').addClass('is-valid')
                                municipality.val(data.municipality.id).text(data.municipality.name).removeClass('is-invalid').addClass('is-valid')
                                urbanRural.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                                // nationality.val(data.nationality.id).text(data.nationality.name).removeClass('is-invalid').addClass('is-valid')
                                suburb.val(data.suburb.id).text(data.suburb.name).removeClass('is-invalid').addClass('is-valid')
                            } else {
                                selectProvince.val('').text('').addClass('is-valid')
                                selectCity.val('').text('').addClass('is-valid')
                                municipality.val('').text('').addClass('is-valid')
                                suburb.val('').text('').addClass('is-valid')
                                urbanRural.val('').text('').addClass('is-valid')
                                // nationality.val('').text('').addClass('is-valid')
                            }
                        }).guardedCatch(function (data) {
                            console.log(JSON.stringify(data))
                            var msg = data && data.message && data.message.message;
                            showAlertDialog("Unexpected Server Error", msg)
                        });
                    }
                }
                else{
                    $('#inputPhysicalCode').val("")
                    $('#inputPhysicalCode').removeClass('is-valid').addClass("is-invalid")
                    selectProvince.val('').text('').addClass('is-valid')
                    selectCity.val('').text('').addClass('is-valid')
                    suburb.val('').text('').addClass('is-valid')
                    municipality.val('').text('').addClass('is-valid')
                    urbanRural.val('').text('').addClass('is-valid')
                    showAlertDialog("Validation Message", "Physical Code must not be more than 4 character")
                }
            },
            'blur input[name=inputPostalCode]': function (ev) {
                ev.preventDefault()
                let inputPostalCode = $(ev.target)
                let selectProvince = $("#selectPostalProvince option:selected")
                let selectCity = $("#selectPostalCity option:selected")
                let municipality = $("#selectPostalMunicipality option:selected")
                let suburb = $("#selectPostalSuburb option:selected")
                let urbanRural = $("#selectPostalUrbanRural option:selected")
                let nationality = $("#selectNationality option:selected")
                if (inputPostalCode.val().length === 4) {
                    if (inputPostalCode.val() !== '') {
                        console.log("Calling check physical code ...")
                        this._rpc({
                            route: `/sdf/check_physical_code/${inputPostalCode.val()}`,
                            params: {},
                        }).then(function (data) {
                            // console.log("PHY CODE DATA " + JSON.stringify(data))
                            // console.log("Setting Physical address ...") 
                            if (data.status) {
                                selectProvince.val(data.province.id).text(data.province.name).removeClass('is-invalid').addClass('is-valid')
                                selectCity.val(data.city.id).text(data.city.name).removeClass('is-invalid').addClass('is-valid')
                                municipality.val(data.municipality.id).text(data.municipality.name).removeClass('is-invalid').addClass('is-valid')
                                suburb.val(data.suburb.id).text(data.suburb.name).removeClass('is-invalid').addClass('is-valid')
                                nationality.val(data.nationality.id).text(data.nationality.name).removeClass('is-invalid').addClass('is-valid')
                                urbanRural.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                            
                            } else {
                                selectProvince.val('').text('').addClass('is-valid')
                                selectCity.val('').text('').addClass('is-valid')
                                municipality.val('').text('').addClass('is-valid')
                                suburb.val('').text('').addClass('is-valid')
                                urbanRural.val('').text('').addClass('is-valid')
                                nationality.val('').text('').addClass('is-valid')

                            }
                        }).guardedCatch(function (data) {
                            console.log(JSON.stringify(data))
                            var msg = data && data.message && data.message.message;
                            showAlertDialog("Unexpected Server Error", msg)
                        });
                    }
                }
                else{
                    $('#inputPostalCode').val("")
                    $('#inputPostalCode').removeClass('is-valid').addClass("is-invalid")
                    selectProvince.val('').text('').addClass('is-valid')
                    selectCity.val('').text('').addClass('is-valid')
                    suburb.val('').text('').addClass('is-valid')
                    municipality.val('').text('').addClass('is-valid')
                    urbanRural.val('').text('').addClass('is-valid')
                    showAlertDialog("Validation Message", "Postal Code must not be more than 4 character")
                }
            },

            'blur input[name=inputPostalAddr1]': function(ev){
                ev.preventDefault();
                let inputPostalAddr1 = $(ev.target);  
                let numeric_alpha = /^(?=.*[a-zA-Z])(?=.*[0-9])/;
                if (inputPostalAddr1.val().match(numeric_alpha)) {
                    console.log('pass')
                    $('#inputPostalAddr1').removeClass('is-invalid').addClass("is-valid")
                 
                }else{
                    inputPostalAddr1.val("")
                    $('#inputPhysicalAddr1').removeClass('is-valid').addClass("is-invalid")
                    showAlertDialog("Validation Message", "Postal Address must contain alphanumeric values eg. 34 Maduka Street")
                }
            },
            // 'blur input[name=inputIdNo]': function(ev){
            //     let idNo = $(ev.target).val()
       
            //     if(idNo !== ''){
            //         this._rpc({
            //             route: `/check_sa_idno/${idNo}`,
            //             params: {},
            //         }).then(function (data) {
            //             console.log('RSA ID No check response => '+ JSON.stringify(data))
            //             if (!data.status) {
            //                 $(ev.target).val('')
            //                 showAlertDialog("Validation Error!", `${data.message}`)
            //             }else{
            //                 //update gender and dob with identity data
            //                 $("#inputGender").val(data.data.gender)
            //                 $("#inputDob").val(formatToDatePicker(data.data.dob))
            //                 $("#inputDob").trigger("change")
            //             } 
            //         }).guardedCatch(function (error) {
            //             let msg = error.message.message
            //             console.log(msg)
            //             showAlertDialog("Server Error!", msg)
            //         });
            //     }
            // },
             
        },
    })

})