# -*- coding: utf-8 -*-
# from odoo import http


# class InsetaDg(http.Controller):
#     @http.route('/inseta_dg/inseta_dg/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inseta_dg/inseta_dg/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inseta_dg.listing', {
#             'root': '/inseta_dg/inseta_dg',
#             'objects': http.request.env['inseta_dg.inseta_dg'].search([]),
#         })

#     @http.route('/inseta_dg/inseta_dg/objects/<model("inseta_dg.inseta_dg"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inseta_dg.object', {
#             'object': obj
#         })
