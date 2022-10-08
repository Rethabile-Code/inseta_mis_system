import logging
import odoo
from odoo.tools.translate import _
from odoo.addons.web.controllers.main import Home, ensure_db
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang'}

class HomeExtension(Home):

    @http.route('/popiact', type='http', auth="user", website=True)
    def popiact(self, **kw):
        return http.request.render('mis_popi_act.consent')

    @http.route(['/popiact_update'], type='json',  methods=['POST'],  website=True, auth="public", csrf=False)
    def popiact_update(self,**post):
        if post.get('checkboxAgree'):
            uid = request.session.uid
            user = request.env['res.users'].browse([uid])
            if user:
                user.write({"has_agreed_popiact": True, "has_agreed_yes_no": "Yes", "popiact_date": fields.Date.today()})


    # @http.route()
    # def web_login(self, *args, **kw):
    #     ensure_db()
    #     response = super(HomeExtension, self).web_login(*args, **kw)
    #     response.qcontext.update(self.get_auth_signup_config())
    #     uid = request.uid
    #     user = request.env['res.users'].browse([uid])
    #     if user.has_agreed_popiact:
    #         if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
    #             # Redirect if already logged in and redirect param is present
    #             return request.redirect(request.params.get('redirect'))
    #     else:
    #         return request.redirect(self._login_redirect(uid, redirect='/popiact'))

    #     return response


    @http.route()
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        #values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                request.params['login_success'] = True
                user = request.env['res.users'].browse([uid])

                if user.has_agreed_popiact:
                    return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
                else:
                    return request.redirect(self._login_redirect(uid, redirect='/popiact'))
                
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        values['debug'] = []
        #_logger.info(f"VALS => {debug}")
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        response.qcontext.update(self.get_auth_signup_config())
        return response

