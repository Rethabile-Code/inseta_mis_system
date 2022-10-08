odoo.define('mis_popi_act.popiact', function (require) {
    "use strict";

    require('web.dom_ready');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');

    publicWidget.registry.POPIAct = publicWidget.Widget.extend({
        selector: '.popiact',
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                //hide application navbar by removing the elements
                $(".o_main_navbar").html(" ")
                //initialize modal
                self.$el.find("#popiactModal").modal('show');
            });
        },
        events: {
            'shown.bs.modal #popiactModal': function (ev) {
                let self = this;
       
                self.$el.find("#buttonDoNotAgree").click(function(ev){
                    ev.preventDefault();
                    console.log("I disagree")
                    //logout
                    window.location.href = "/web/session/logout"
                })

                self.$el.find("#buttonAgree").click(function(ev){
                    ev.preventDefault();
                    let iAgree = self.$el.find("#checkboxAgree")
                    if (!iAgree.is(":checked")){
                        return alert("Please place a tick in the POPI Act Consent check-box indicating your agreement to the above conditions.")
                    }
                    self._rpc({
                        route: "/popiact_update",
                        params: {"checkboxAgree":true}
                    }).then(function (data) {
                        //redirect user to /web
                        console.log("POPI Act Update success")
                        window.location.href = "/web"
                    }).guardedCatch(function (data) {
                        var msg = data && data.data && data.data.message;
                        console.log(`POPI Act Update error =>  ${msg}`)
                        alert("Unexpected Error:\nPlease try again")
                    });
                })
            },
        }
    })

})