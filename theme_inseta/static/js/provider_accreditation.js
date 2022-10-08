odoo.define('theme_inseta.ProviderAccreditation', function (require) {
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

    function buildFormData(formData, data, parentKey) {
        if (data && typeof data === 'object' && !(data instanceof Date) && !(data instanceof File)) {
          Object.keys(data).forEach(key => {
            buildFormData(formData, data[key], parentKey ? `${parentKey}[${key}]` : key);
          });
        } else {
          const value = data == null ? '' : data;
      
          formData.append(parentKey, value);
        }
      }

    function showModal(title, msg) {
        var wizard = $(qweb.render('process.modal', {
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

    publicWidget.registry.ProviderAccreditationPage = publicWidget.Widget.extend({
        selector: '.provider-accreditation',
        start: function () {
            var self = this;
            let items = [];
            $('#provider_quality_assurance_id').prop('readonly', true);

            localStorage.setItem('progData', JSON.stringify(items))
            localStorage.setItem('campus', JSON.stringify([]))

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
                // var inputTel = document.querySelector("#inputTel");
                // var itiTel = window.intlTelInput(inputTel,{
                //   initialCountry: "auto",
                //   hiddenInput:"inputItiTel",
                //   placeholderNumberType:"MOBILE",
                //   preferredCountries: ["za"],
                //   geoIpLookup: function(callback) {
                //     $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                //         console.log("IP DATA "+ JSON.stringify(resp))
                //         var countryCode = (resp && resp.country) ? resp.country : "za";
                //         callback(countryCode);
                //     });
                //   },
                //   utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                // });
                // window.itiTel = itiTel

                // var inputCellPhone = document.querySelector("#inputCellPhone");
                // var itiCell = window.intlTelInput(inputCellPhone, {
                //   initialCountry: "auto",
                //   hiddenInput:"inputItiCell",
                //   placeholderNumberType:"MOBILE",
                //   preferredCountries: ["za"],
                //   geoIpLookup: function(callback) {
                //     $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                //         console.log("IP DATA "+ JSON.stringify(resp))
                //         var countryCode = (resp && resp.country) ? resp.country : "za";
                //         callback(countryCode);
                //     });
                //   },
                //   utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                // });
                // window.itiCell = itiCell

                // var inputTel = document.querySelector("#inputTel");
                // var itiTel = window.intlTelInput(inputTel,{
                //   initialCountry: "auto",
                //   hiddenInput:"inputItiTel",
                //   placeholderNumberType:"MOBILE",
                //   preferredCountries: ["za"],
                //   geoIpLookup: function(callback) {
                //     $.get('https://ipinfo.io?token=88bbeaa3c8a6a7', function() {}, "jsonp").always(function(resp) {
                //         console.log("IP DATA "+ JSON.stringify(resp))
                //         var countryCode = (resp && resp.country) ? resp.country : "za";
                //         callback(countryCode);
                //     });
                //   },
                //   utilsScript: "/theme_inseta/static/plugins/intl-tel-input/build/js/utils.js" // just for formatting/placeholders etc
                // });
                // window.itiTel = itiTel

                var inputCampusCellPhone = document.querySelector("#inputCampusCell");
                $('#provider_quality_assurance_id').prop('readonly', true);

                var itiCampusCell = window.intlTelInput(inputCampusCellPhone, {
                  initialCountry: "auto",
                  hiddenInput:"inputItiCampusCell",
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
                window.itiCampusCell = itiCampusCell

                var inputFax = document.querySelector("#inputCampusFax");
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

                current_fs.find('input:required, select:required, textarea:required').each(function (ev) {
                    if ($(this).val() == "") {
                        // console.log('Required Fields')
                        console.log(`Required Fields ==> ${$(this)}`)

                        console.log('Is Required Fields')
                        $(this).addClass('is-invalid');
                        next_step = false;
                    } else {
                        $(this).removeClass('is-invalid').addClass('is-valid')
                        console.log('No Required Fields')
                        next_step = true;

                    }
                });

                let inputCampusCell = $("#inputCampusCell");

                // if(!validatePhone(inputCampusCell.val())){
                //     inputCampusCell.addClass("is-invalid")
                //     next_step = false
                // }else{
                //     inputCampusCell.removeClass('is-invalid').addClass("is-valid")
                //    //next_step = true
                // }

                //validate email and cell phone
                // let inputEmail = $("#modalCampusEmail");
                // if(!validateEmail(inputEmail.val())){
                //     inputEmail.addClass("is-invalid")
                //     next_step = false
                //     alert("Invalid mail!")
                // }else{
                //     inputEmail.removeClass('is-invalid').addClass("is-valid")
                //     next_step = true
                //     console.log("valid mail!")

                // }
                // if(validatePhone(inputCampusCell.val()) && validateEmail(inputCampusEmail.val())){
                //     next_step = true
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
                        let progStorage = JSON.parse(localStorage.getItem('progData')) // [{}, {}, {}, ]
                        let campusData = JSON.parse(localStorage.getItem('campus')) // [{}, {}, {}, ]
                        console.log(`Form ${form} , Type = ${typeof(formData)} and campus = ${campusData}`)
                        console.log(`Campus details: ${$('#inputCampusDetails').val()}`)
                        let inputSubmit = $(ev.target)
                        let btnPreloader = $("#btn-preloader");

                        Object.keys(campusData).forEach(key => {
                                console.log('Data is ==>', campusData)
                                console.log('Data Key is ==>', campusData[key])
 
                          });

                        formData.append('campusDetails', JSON.stringify(campusData));
                        // for (var key in campusData){
                            
                        // }
                        formData.append('programme_details', progStorage);
                        console.log('Sending request to server => '+ formData) // .update({'programme_details': progStorage}))
                        var xmlRequest = $.ajax({
                            type: "POST",
                            enctype: 'multipart/form-data',
                            url: "/provider_accreditation_ajax",
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
                            console.log(`Provider Accreditation. TextStatus: ${textStatus}. Statuscode:  ${jqXHR.status}`);
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

            // $("#resend_otp").click(function(ev){
            //     ev.preventDefault();
            //     let coupon_code = localStorage.getItem('partner_coupon_code')
            //     let sendAgainLabel = $("#resend_otp");
            //     sendAgainLabel.html('<i class="fa fa-spinner fa-spin"> </i>Sending otp...');
            //     _verifyCouponAndsendOTPCode(coupon_code, false);
            // });
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

            'click .addModAssessor': function(ev){
                ev.preventDefault();
                $('#ProcessModal').modal("show")
                console.log('MODAL SHOWING')
                // let msg = 'Enter Assessor / Moderator SDL No to verify and also provide the programme code.';
                // let title = 'Add';
                // showModal(title, msg);
            },

            'click .addCampusbtn': function(ev){
                ev.preventDefault();
                $('#CampusProcessModal').modal("show")
                console.log('Campus MODAL SHOWING')
            },

            'click .remCampusbtn': function(ev){
                ev.preventDefault();
                let campusStore = JSON.parse(localStorage.campus) // gets a list 
                campusStore.pop()
                localStorage.setItem('campus', JSON.stringify(campusStore));

                console.log('Remain ===> ',campusStore.pop())
                let campusName = $('#modalCampusName').val()
                let campusphone = $('#campusPhoneModal').val()
                let contactperson = $('#modalCampusContactName').val()
                let campusEmail = $('#modalCampusEmail').val()
                let campusAddr = $('#modalCampusAddr').val()
                let contactphone = $('#modalContactPersonPhone').val()
                let contactcell = $('#modalContactPersoncell').val()
                let details = {
                    'campusName':campusStore.campusName, 
                    'campusphone': campusStore.campusphone, 
                    'campusEmail': campusStore.campusEmail, 
                    'campusAddr': campusStore.campusAddr,
                    'contactperson': campusStore.contactperson, 
                    'contactphone': campusStore.contactphone, 
                    'contactcell': campusStore.contactcell
                }
                $("#divCampus").empty();
                let campusStoreNew = JSON.parse(localStorage.campus) // gets a list 

                for(let key in campusStoreNew){
                    $("#divCampus").append(`<p>Campus Name: ${campusStoreNew[key].campusName},<br/>Campus Email: - ${campusStoreNew[key].campusEmail}<br/>Contact person: - ${campusStoreNew[key].contactperson} <br/>Contact person: - ${campusStoreNew[key].contactphone}</p>`) 
                }
                let campusDetails = $('#inputCampusDetails')
                campusDetails.val(campusStoreNew)
            },

            'click .btnConfirmCampus': function (ev) {
                console.log('confirmed ')
                ev.preventDefault();
                let campusStore = JSON.parse(localStorage.getItem('campus')) // gets a list 
                let campusName = $('#modalCampusName').val()
                let details = {
                    'campusName': $('#modalCampusName').val(), 
                    'campusphone': $('#campusPhoneModal').val(), 
                    'campusEmail': $('#modalCampusEmail').val(), 
                    'campusAddr': $('#modalCampusAddr').val(),
                    'contactperson': $('#modalCampusContactName').val(), 
                    'contactpersonSurname': $('#modalCampusContactSurName').val(), 
                    'contactphone': $('#modalContactPersonPhone').val(), 
                    'contactcell': $('#modalContactPersoncell').val(), 
                }
                campusStore.push(details)
                localStorage.setItem('campus', JSON.stringify(campusStore));
                console.log('Added campus ...')
                //divProFileList
                $("#divCampus").append(`<p> Name: "${campusName}"<br/>Contact person: - ${$('#modalCampusContactName').val()} ${$('#modalCampusContactSurName').val()}<br/>Contact Phone: - ${$('#campusPhoneModal').val()}</p>`) 
                let campusStoreNew = JSON.parse(localStorage.campus) // gets a list 
                let campusDetails = $('#inputCampusDetails')
                campusDetails.val(campusStoreNew)
                $('#modalCampusName').val('')
                $('#campusPhoneModal').val('')
                $('#modalCampusEmail').val('')
                $('#modalCampusAddr').val('')
                $('#modalCampusContactName').val('')
                $('#modalCampusContactSurName').val('')
                $('#modalContactPersonPhone').val('')
                $('#modalContactPersoncell').val('')
                $('#CampusProcessModal').modal("hide")
            },

            '.click .addQual': function(ev){
                ev.preventDefault();
                $('#proList').val('')
                console.log('Qualification added')
            },

            'click .button_confirm_programme': function (ev) {
                console.log('popopo')
                ev.preventDefault();
                let items = []
                let assessorInput = $("input[name=assessorInput]")
                let moderatorInput = $("input[name=moderatorInput]")
                let programmeCodeInput = $("input[name=programmeCodeInput]")
                let AsssdlNo = assessorInput.val()
                let ModsdlNo = moderatorInput.val()
                let programmeCode = programmeCodeInput.val()
                let isValid = true
                if (AsssdlNo.trim() == '') {
                    // displayErrorMsg('Please provide employer SLD no and try again')
                    isValid = false
                    assessorInput.addClass('is-invalid')
                }
                else {
                    isValid = true
                    assessorInput.removeClass('is-invalid').addClass('is-valid')
                }

                if (ModsdlNo.trim() == ""){
                    isValid = false
                    moderatorInput.addClass('is-invalid')
                }
                else {
                    isValid = true
                    moderatorInput.removeClass('is-invalid').addClass('is-valid')
                }

                if (programmeCode.trim() == ""){
                    isValid = false
                    programmeCodeInput.addClass('is-invalid')
                }
                else {
                    isValid = true
                    programmeCodeInput.removeClass('is-invalid').addClass('is-valid')
                } 

                
                if (isValid) {
                    let btn = $(ev.target)
                    let btnHtml = btn.html() // cache the original content
                    btn.html("<i class='fa fa-spinner fa-spin'></i> working...")
                    btn.attr("disabled", true)
                    this._rpc({
                        route: `/assessor-moderator/${programmeCode}/${AsssdlNo}/${ModsdlNo}`, 
                        params: {},
                    }).then(function (data) {
                        btn.html(btnHtml)
                        btn.attr("disabled", false)
                        console.log('STATUS ', data.status)
                        console.log('Main data ', data.data)
                        if (data.status === "None") {
                            assessorInput.val('')
                            assessorInput.addClass('is-invalid')
                            moderatorInput.val('')
                            moderatorInput.addClass('is-invalid')
                            showAlertDialog(`Error Found:  ${data.status}`)
                            // showAlertDialog("Assessor SDL Not Found!", `Programme with code ${programmeCode} Assessor / Moderator With SDL No ${AsssdlNo} / ${ModsdlNo} Not Found!`)
                        } else {
                            assessorInput.removeClass('is-invalid').addClass('is-valid')
                            moderatorInput.removeClass('is-invalid').addClass('is-valid')
                            console.log(data.data.programme_codes.programme_code)
                            $('select[name="proList"]')
                                .append(`<option selected="selected" value="${data.data.programme_codes.programme_code}-${assessorInput.val()}-${moderatorInput.val()}">${data.data.programme_codes.programme_name}</option>`)
                                .removeClass('is-invalid').addClass('is-valid')
                            let progStorage = JSON.parse(localStorage.getItem('progData'))
                            console.log('LIST XXXX ', progStorage)

                            let progObj = {
                                'programmeId': data.data.programme_codes.programme_id,
                                'programmeName': data.data.programme_codes.programme_code,
                                'programmeType': data.data.programme_codes.programme_type,
                                'moderatorNo': AsssdlNo,
                                'assessorNo': ModsdlNo,
                                'assessorId': data.data.assessor_search_id,
                                'moderatorId': data.data.moderator_search_id,
                            }
                            progStorage.push(progObj)

                            console.log('LIST XXXX 222', progStorage)
                            let fx = localStorage.setItem('progData', JSON.stringify(progStorage));
                            console.log('New localxx storage is ', fx)

                            $("#divProFileList").append(`<input type="file" name="${data.data.programme_codes.programme_name}_document" 
                                class="form-control-file form-control-sm" 
                                required="required" accept="image/*,application/pdf"/> 
                                <div class="invalid-feedback">Upload SLA document</div>`) 

                            assessorInput.val('')
                            moderatorInput.val('')
                            programmeCodeInput.val('')
                            $('#ProcessModal').modal("hide")

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

            'blur input[name=inputlearn]': function (ev) {
                ev.preventDefault()
                let inputProg = $(ev.target)
                let progCode = inputProg.val()
                if (progCode.trim() !== '') {
                    $('select[name="inputlearn"] option').each(function () {
                        if ($(this).val() == progCode) {
                            showAlertDialog("Programme Already Selected", "Please provide a Unique Programme code.")
                        }
                    })
                    this._rpc({
                        route: `/get-programme/${progCode}/learnership`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            inputProg.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="provider_learning_programme"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputProg.val('')
                        } else {
                            showAlertDialog("Invalid Programme !", `Programme with code ${progCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            'blur input[name=inputSkillProg]': function (ev) {
                ev.preventDefault()
                let inputProg = $(ev.target)
                let progCode = inputProg.val()

                if (progCode.trim() !== '') {
                    // check existing SDL list to ensure sdl no is unique
                    $('select[name="inputSkillProg"] option').each(function () {
                        if ($(this).val() == progCode) {
                            showAlertDialog("Programme Already Selected", "Please provide a Unique Programme code.")
                        }
                    })
                    this._rpc({
                        route: `/get-programme/${progCode}/skill`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            inputProg.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="provider_skill_programme"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputProg.val('')
                            
                        } else {
                            showAlertDialog("Invalid Programme !", `Programme with code ${progCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            'blur input[name=inputUnitProg]': function (ev) {
                ev.preventDefault()
                let inputProg = $(ev.target)
                let progCode = inputProg.val()

                if (progCode.trim() !== '') {
                    // check existing SDL list to ensure sdl no is unique
                    $('select[name="inputUnitProg"] option').each(function () {
                        if ($(this).val() == progCode) {
                            showAlertDialog("Programme Already Selected", "Please provide a Unique Unit Standard Programme code.")
                        }
                    })
                    this._rpc({
                        route: `/get-programme/${progCode}/unitstandard`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            inputProg.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="provider_unit_standard_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputProg.val('')
                            
                        } else {
                            showAlertDialog("Invalid Programme !", `Unit standard with code ${progCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            // here2

            'blur input[name=inputFac]': function (ev) {
                ev.preventDefault()
                let inputOption = $(ev.target)
                let OptionCode = inputOption.val()
                if (OptionCode.trim() !== '') {
                    $('select[name="inputFac"] option').each(function () {
                        if ($(this).val() == OptionCode) {
                            showAlertDialog("Facilitator SDL No already selected", "Please provide a Unique SDL No.")
                        }
                    })
                    this._rpc({
                        route: `/get-assessor-moderator/${OptionCode}/facilitator`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            // progCode.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="facilitator_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputOption.val('')
                            $("#divImageFacilitator").append(`<input type="file" name="${data.data.name}_document" id="name="${data.data.id}"
                                class="form-control-file form-control-sm" 
                                required="required" accept="image/*,application/pdf"/> 
                                <div class="invalid-feedback">Upload SLA document</div>`) 
                            
                        } else {
                            showAlertDialog("Invalid ID !", `Facilitator with code ${OptionCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = "Error occurred";
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            'blur input[name=inputAsses]': function (ev) {
                ev.preventDefault()
                let inputOption = $(ev.target)
                let OptionCode = inputOption.val()
                if (OptionCode.trim() !== '') {
                    $('select[name="inputAsses"] option').each(function () {
                        if ($(this).val() == OptionCode) {
                            showAlertDialog("Assessor SDL No already selected", "Please provide a Unique SDL No.")
                        }
                    })
                    this._rpc({
                        route: `/get-assessor-moderator/${OptionCode}/assessor`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            // progCode.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="assessor_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputOption.val('')
                            $("#divImageAssessor").append(`<input type="file" name="${data.data.name}_document" id="name="${data.data.id}"
                                class="form-control-file form-control-sm" 
                                required="required" accept="image/*,application/pdf"/> 
                                <div class="invalid-feedback">Upload SLA document</div>`) 
                            
                        } else {
                            showAlertDialog("Invalid Assessor !", `Assessor with code ${OptionCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = "Error occurred";
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },

            'blur input[name=inputModer]': function (ev) {
                ev.preventDefault()
                let inputOption = $(ev.target)
                let OptionCode = inputOption.val()
                if (OptionCode.trim() !== '') {
                    $('select[name="inputModer"] option').each(function () {
                        if ($(this).val() == OptionCode) {
                            showAlertDialog("Duplicate SDL No", "Please provide a Unique SDL No.")
                        }
                    })
                    this._rpc({
                        route: `/get-assessor-moderator/${OptionCode}/moderator`,
                        params: {},
                    }).then(function (data) {
                        if (data.status) {
                            // progCode.removeClass('is-invalid').addClass('is-valid')
                            $('select[name="moderator_ids"]')
                                .append(`<option selected="selected" value="${data.data.id}">${data.data.code} - ${data.data.name}</option>`)
                                // .removeClass('is-invalid').addClass('is-valid')
                                inputOption.val('')
                                $("#divImageModerator").append(`<input type="file" name="${data.data.name}_document" id="name="${data.data.id}"
                                class="form-control-file form-control-sm" 
                                required="required" accept="image/*,application/pdf"/> 
                                <div class="invalid-feedback">Upload SLA document</div>`)
                            
                        } else {
                            showAlertDialog("Invalid Moderator !", `Moderator with code ${OptionCode} not existing in the system!`)
                        }
                    }).guardedCatch(function (data) {
                        var msg = "Error occurred";
                        showAlertDialog("Unexpected Server Error", msg)
                    });
                }
            },
            
            'blur input[name=inputCampusEmail]': function (ev) {
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
            'blur input[name=inputPhysicalAddr1]': function(ev){
                ev.preventDefault();
                let inputPhysicalAddr1 = $(ev.target);
                let inputPhyiscalCode = $('#inputPhysicalCode') 
                let selectProvince = $("#selectPhysicalProvince option:selected")
                let selectCity = $("#selectPhysicalCity option:selected")
                let nationality = $("#selectPhysicalNationality option:selected")
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
                let nationality = $("#selectPhysicalNationality option:selected")
                let suburb = $("#selectPhysicalSuburb option:selected")
                let municipality = $("#selectPhysicalMunicipality option:selected")
                let urbanrural = $("#selectPhysicalUrbanRural option:selected")

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
                                nationality.val(data.nationality.id).text(data.nationality.name).removeClass('is-invalid').addClass('is-valid')
                                suburb.val(data.suburb.id).text(data.suburb.name).removeClass('is-invalid').addClass('is-valid')
                                municipality.val(data.municipality.id).text(data.municipality.name).removeClass('is-invalid').addClass('is-valid')
                                urbanrural.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                                console.log('URN / RURAL REGISTERS  ===>', data.urban_rural)
                            } else {
                                selectProvince.val('').text('').addClass('is-valid')
                                selectCity.val('').text('').addClass('is-valid')
                                nationality.val('').text('').addClass('is-valid')
                                suburb.val('').text('').addClass('is-valid')
                                municipality.val('').text('').addClass('is-valid')
                                urbanrural.val('').text('').addClass('is-valid')

                            }
                        }).guardedCatch(function (data) {
                            console.log(JSON.stringify(data))
                            var msg = data && data.message && data.message.message;
                            showAlertDialog("Unexpected Server Error", msg)
                        });
                    }
                }else{
                    $('#inputPhysicalCode').removeClass('is-valid').addClass("is-invalid")
                    $('#inputPhysicalCode').val("")
                    selectProvince.val('').text('').addClass('is-valid')
                    selectCity.val('').text('').addClass('is-valid')
                    nationality.val('').text('').addClass('is-valid')
                    suburb.val('').text('').addClass('is-valid')
                    municipality.val('').text('').addClass('is-valid')
                    urbanrural.val('').text('').addClass('is-valid')
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
                let urbanrural = $("#selectPostalUrbanRural option:selected")

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
                                urbanrural.val(data.urban_rural).text(data.urban_rural).removeClass('is-invalid').addClass('is-valid')
                            
                            } else {
                                selectProvince.val('').text('').addClass('is-valid')
                                selectCity.val('').text('').addClass('is-valid')
                                municipality.val('').text('').addClass('is-valid')
                                suburb.val('').text('').addClass('is-valid')
                                urbanrural.val('').text('').addClass('is-valid')
                            }
                        }).guardedCatch(function (data) {
                            console.log(JSON.stringify(data))
                            var msg = data && data.message && data.message.message;
                            showAlertDialog("Unexpected Server Error", msg)
                        });
                    }
                }else {
                    $('#inputPostalCode').val("")
                    $('#inputPostalCode').removeClass('is-valid').addClass("is-invalid")
                    selectProvince.val('').text('').addClass('is-valid')
                    selectCity.val('').text('').addClass('is-valid')
                    suburb.val('').text('').addClass('is-valid')
                    municipality.val('').text('').addClass('is-valid')
                    urbanrural.val('').text('').addClass('is-valid')
                    showAlertDialog("Validation Message", "Postal Code must not be more than 4 character")
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
                        } 
                    }).guardedCatch(function (error) {
                        let msg = error.message.message
                        console.log(msg)
                        showAlertDialog("Server Error!", msg)
                    });
                }
            },
             
        },
        
    })

})