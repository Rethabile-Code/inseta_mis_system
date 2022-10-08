odoo.define('inseta_skills.dhet_import_button', function (require) {

    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var ListController = require('web.ListController');

    ListController.include({

        renderButtons: function ($node) {
            this.ksIsAdmin = odoo.session_info.is_admin;
            this._super.apply(this, arguments);
            //On Click on our custom import button, call custom import function
            var self = this;

            if (this.$buttons) {
                var import_button = this.$buttons.find('.dhet_import_button');
                import_button.click(function (ev) {
                    ev.preventDefault();

                    self._rpc({
                        // Get view id 
                        model: 'ir.model.data',
                        method: 'xmlid_to_res_model_res_id',
                        args: ['inseta_skills.employer_update_wizard_view_form'],
                    }).then(function (data) {
                        // Open view 
                        self.do_action({
                            name: 'Import DHET Employer file',
                            type: 'ir.actions.act_window',
                            res_model: 'inseta.employer.update.wizard',
                            target: 'new',
                            views: [
                                [data[1], 'form']
                            ], // data [1] variable contains the view id 
                        }, {
                            on_reverse_breadcrumb: function () {
                                self.update_control_panel({
                                    clear: true,
                                    hidden: true
                                });
                            }
                        });
                    });

                });
            }
        },
    });
    core.action_registry.add('inseta_skills.dhet_import_button', ListController);
    return ListController;
});