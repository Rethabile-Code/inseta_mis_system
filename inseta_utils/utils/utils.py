from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import ValidationError

class insetaWizard(models.Model):
    _name = 'inseta.utils'
    _description = "INSETA Utils"
    
    subject = fields.Text('Subject', required=False)
    model_ref = fields.Char('Model')
    name = fields.Text('Message/Reason', required=True)
    date = fields.Datetime('Date') 
    resp = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user.id)
    reference = fields.Integer('Reference ID', default=False, readonly=True)
    follower_ids = fields.Many2many(
        'res.users', string='Add followers', required=False)
    action = fields.Selection([('refusal', 'Refusal'),('rework', 'Rework'),('query', 'Query'), ('mass', 'Mass Notification')], 
    default='refusal', string="Action", help="Action to perform. Set to refusal if you want to refuse a record")
    
    def send_mail(self, email_from, mail_to_list, body, subject=None, attachment=None):
        """Can be used to send simple mail
        Args: mail_to_list Accepts list of mail addresses to send message to"""
        mail_to = ','.join([mail for mail in mail_to_list])
        subject = "Notification Message" if not subject else subject
        mail_data = {
            'email_from': email_from,
            'subject': subject,
            'email_to': mail_to,
            'reply_to': email_from,
            # 'recipient_ids': [(6, 0, [rec.partner_id.id for rec in recipients])] if recipients else False,
            'body_html': body,
        }
        mail_id = self.env['mail.mail'].create(mail_data)
        return mail_id

    def email_generator(self, email_to, email_from=None, body=None, subject=None, 
    with_template_id=False, model_name=False, ids=False, address_to=None, contexts=None): 
        '''Email_to = [lists of emails], Contexts = Dictionary '''
        for rec in self:
            ids = rec.id if not ids else ids
            subject = subject if subject else 'Notification Message'
            try:
                email_to = (','.join([m for m in email_to]))
                if with_template_id and model_name:
                    
                    ctx = dict()
                    ctx.update({
                        'default_model': 'oeh.medical.lab.test',
                        'default_res_id': ids,
                        'default_use_template': bool(with_template_id),
                        'default_template_id': with_template_id,
                        'default_composition_mode': 'comment',
                        # 'email_to': email if email else partner_mails
                        'subject': subject
                        # used this to pass a context that corrects the redundant tests word
                    })
                    if email_from:
                        ctx['email_from'] = email_from

                    if body:
                        ctx['body_context'] = body

                    if address_to:
                        ctx['address_to'] = address_to 
                    template_rec = self.env['mail.template'].browse(with_template_id)
                    template_rec.write({'email_to': email_to})
                    template_rec.with_context(ctx).send_mail(ids, True)
                else:
                    rec.send_mail(email_from, email_to, body, subject)
            except Exception as e:
                pass

    def email_generator_method(self, email_items, email_from, contexts, ids=False, with_template_id=None,model_name=None): 
        '''Email_to = [lists of emails], Contexts = {Dictionary} '''
        for rec in self:
            ids = rec.id if not ids else ids
            subject = contexts.get('subject', '')
            body = contexts.get('body_context', '')
            email_from = contexts.get('email_from', '') if not email_from else email_from
            addressed_to = contexts.get('addressed_to', '')
            subject = subject if subject else 'Notification Message'
            email_to = (','.join([m for m in email_items]))
            try:
                if with_template_id and model_name:
                    
                    ctx = dict()
                    ctx.update({
                        'default_model': model_name,
                        'default_res_id': ids,
                        'default_use_template': bool(with_template_id),
                        'default_template_id': with_template_id,
                        'default_composition_mode': 'comment',
                        # 'email_to': email if email else partner_mails
                        'subject': subject
                        # used this to pass a context that corrects the redundant tests word
                    })
                    if email_from:
                        ctx['email_from'] = email_from

                    if body:
                        ctx['body_context'] = body

                    if addressed_to:
                        ctx['addressed_to'] = addressed_to 
                    template_rec = self.env['mail.template'].browse(with_template_id)
                    template_rec.write({'email_to': email_to})
                    template_rec.with_context(ctx).send_mail(ids, True)
                else:
                    rec.send_mail(email_from, email_to, body, subject)
                
            except Exception as e:
                raise ValidationError(e)

    def post_action(self):
        sdf_reg = self.env['inseta.sdf.register'].browse([self.reference])
        if sdf_reg:
            if self.action == "refusal":
                sdf_reg.write({'refusal_comments': self.name})
                sdf_reg.action_send_workflows(False)
            elif self.action == "rework":
                # sdf_reg.update_followers() 
                mail_items = [sdf_reg.employee_id, sdf_reg.email_address]
                ir_model_data = self.env['ir.model.data']
                template_id = ir_model_data.get_object_reference('inseta_skills', 'email_template_notify_employee_rework_sdf')[1] 
                follower_emails = [mail.login for mail in self.follower_ids]
                email_to = mail_items + follower_emails
                self.email_generator(email_to, self.env.user.email, None, None, template_id, sdf_reg._name, sdf_reg.id)
                sdf_reg.write({'refusal_comments': self.name, 'state': 'rework'})
                # sdf_reg.action_send_workflows(False)

        return{'type': 'ir.actions.act_window_close'}
        
    def popup_wizard(self, name, model, context, option=False): 
        return {
            'name': name,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': model,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,    
        }

    def mail_send_with_attachment(self, email_from, email_to=False, group_user_id=None, body=None, subject=None, filename = False, followers_mail_list=[], model=None, id=None):
        attach_lists = []
        email_from = self.env.user.email if not email_from else email_from
        # save pdf as attachment 
        attachment_name = "Attachment.pdf"
        attachid = None
        groupObj = self.env['res.groups']
        for order in self:
            if filename:
                attachid = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'type': 'binary',
                    'datas': filename,
                    'datas_fname': filename,
                    'store_fname': attachment_name,
                    'res_model': model,
                    'res_id': id,
                    'mimetype': 'application/x-pdf'
                })
                attach_lists.append(attachid.id)
            email_list = [] 
            if group_user_id:
                group_users = groupObj.search([('id', '=', group_user_id)])
                if not group_users.users:
                    raise ValidationError("There is no user assigned to '{}' group".format(group_users.name))
                group_emails = group_users.mapped('users')
                for gec in group_emails:
                    email_list.append(gec.login)
            if followers_mail_list:
                email_list += followers_mail_list
            mails = (','.join(str(item) for item in email_list))
            # odoo v12 ensures no space is added @ " <"
            formatted_email_from = "{}".format(self.env.user.name) + "<" + str(email_from) + ">"
            subject = subject
            mail_data = {
                'email_from': formatted_email_from,
                'subject': subject,
                'email_to': email_to if email_to else mails if mails else False,
                'reply_to': formatted_email_from,
                'email_cc': mails,
                'auto_delete': False,
                'attachment_ids': [(6, 0, attach_lists)] if attach_lists else False,
                'body_html': body,
                        }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
