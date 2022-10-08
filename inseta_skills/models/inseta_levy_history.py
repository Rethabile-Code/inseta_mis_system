import json
import logging
from odoo import fields, api, models, _
from ..services import  sage

_logger = logging.getLogger(__name__)


# class InsetaGrantHistory(models.Model):
#     _name = "inseta.grant.history"
#     _description = "INSETA Grant History"
#     _order="posting_date desc"

#     date_posted = fields.Date('Date Posted')
#     fiscal_year = fields.Char('Fiscal Year')
#     payment_amount =  fields.Float(string='Amount')
#     description = fields.Char()

#     def _scheduler_sync_grant_history(self):
#         """
#             Fetch all posted payments
#         """
#         res = sage._get_all_mandatory_grant_payment()
#         if res.get("error"):
#             error = res.get("error")
#             _logger.error(error)
#         else:
#             payments = res.get('value')
#             _logger.info(f"Mandatory Grant Payments => {payments}")
#             vals = []
#             for payment in payments:
#                 date = fields.Date.from_string(payment.get('PostingDate'))
#                 amount = payment.get('PaymentAmount')
#                 vals.append(dict(
#                     date_posted = date,
#                     payment_amount = amount,
#                     fiscal_year = payment.get('FiscalYear'),
#                     description = "Mandatory Grant"
#                 ))
#             self.create(vals)


class InsetaLevyHistory(models.Model):
    _name = "inseta.levy.history"
    _description = "INSETA Levy History"
    _order="sars_arrival_date desc"

    batch_no = fields.Integer(index=True)
    entry_no = fields.Integer(index=True, help="Indicates the entry no of the item in the batch")
    period = fields.Char(string='Period')
    levy_month = fields.Char(string='Levy Month')
    scheme_year = fields.Char('Scheme Year')
    mand_grant_amt = fields.Float(string='Mandatory Levy (20%)')
    desc_grant_amt = fields.Float(string='Descretionary Levy (49.5%)')
    admn_grant_amt = fields.Float(string='Admin (10.5%)')
    penalties = fields.Float(string='Penalty (80%)')
    interest = fields.Float(string='Interest (80%)')
    total_amt = fields.Float(string='Total received by SETA (80%)')
    stakeholder_levy_cal = fields.Float(string='Stakeholders Levy Calculated (100%)')
    nsf_cal = fields.Float(string='NSF Calculation(20%)')
    date_posted = fields.Date('Date Posted')
    sars_arrival_date = fields.Date('SARS Arrival Date')

    organisation_id = fields.Many2one('inseta.organisation', string='Organnisation')

    def _scheduler_sync_levy_history(self):
        """
            Fetch batch no of all posted documents of type debit note
            Fetch all synced Batch number
            Remove the synced batch numbers from the list
            Then take one
            Call get_levy_invoices api with batch no as arg

        """
        SyncTrack = self.env["inseta.levy.sync.track"]
        GLAccount = self.env['inseta.levy.glaccount']
        ADMIN_GLACCOUNT = GLAccount.search([('account_group_code','=','970')]).mapped('account_no')
        DISCRETIONARY_LEVY_GLACCOUNT =  GLAccount.search([('account_group_code','=','980')]).mapped('account_no')
        MANDATORY_LEVY_GLACCOUNT = GLAccount.search([('account_group_code','=','990')]).mapped('account_no')

        glaccounts = GLAccount.search([('account_group_code','=','1000')]) #Penalty - 1000 & interest
        #both penalty and interest account use same account code group. We need to filter
        # digits 20 occur in penalty accounts while
        #digits 25 occur in interest accounts
        PENALTY_GLACCOUNT = glaccounts.filtered(lambda x: 'penalties' in x.account_desc.lower()).mapped('account_no')
        INTEREST_GLACCOUNT = glaccounts.filtered(lambda x: 'interest' in x.account_desc.lower()).mapped('account_no')

        _logger.info(f"PENALTY {PENALTY_GLACCOUNT}")
        _logger.info(f"INTEREST {INTEREST_GLACCOUNT}")

        all_batches = sage._get_all_posted_documents()
        _logger.info(f"All Batches => {all_batches}")

        synced_batches = SyncTrack.search([]).mapped("batch_no")
        _logger.info(f"Synced Batches => {synced_batches}")

        #filter the batches that have not been synced and take one
        #We will sync one batch at a time
        not_synced = list(set(all_batches) - set(synced_batches))
        _logger.info(f"Batches To Sync => {not_synced}")

        batches_to_sync = not_synced[:1] if not_synced else [] #take 2. 

        for batch in batches_to_sync: 
            
            _logger.info(f"Batch {batch}")
            response = sage._get_levy_invoices_by_batch(batch)
            #_logger.info(json.dumps(response, indent = 4))
            invoices = response.get("Invoices",[]) if response else []

            for invoice in invoices:

                """
                    #AmountDue
                    "BatchNumber": 3,
                    "EntryNumber": 1,
                    "CustomerNumber": "L000746414",
                    "DocumentNumber": "SCHEME2000/1",
                    "ShipToLocationCode": "",
                    "SpecialInstructions": "",
                    "DocumentType": "DebitNote",
                    "DocumentDate": "2000-04-01T00:00:00Z",
                    "AsOfDate": "2000-04-01T00:00:00Z",
                    "DueDate": "2000-04-01T00:00:00Z",
                    "FiscalYear": "2000",
                    "FiscalPeriod": "01",
                """
                

                organsation = self.env["inseta.organisation"].search([("sdl_no","=", invoice.get("CustomerNumber"))],limit=1)

                #invoice details
                details = invoice.get("InvoiceDetails")

                fee_type = {
                    "mand_grant_amt": 0.00, 
                    "desc_grant_amt": 0.00,
                    "admn_grant_amt": 0.00,
                    "penalties": 0.00,
                    "interest": 0.00,
                }
                scheme_year = ""
                for detail in details:
                    """
                    "BatchNumber": 3,
                    "EntryNumber": 1,
                    "LineNumber": 20,
                    "Description": "L000746414",
                    "RevenueAccount": "10005-301",
                    "ExtendedAmountWithTIP": 15964.34,
                    "COGSAmount": 0.0,
                    "ExtendedAmountWithoutTIP": 15964.34,
                    """                    
                    if detail.get("RevenueAccount") in MANDATORY_LEVY_GLACCOUNT:
                        fee_type["mand_grant_amt"] = detail.get("ExtendedAmountWithoutTIP")
                    elif detail.get("RevenueAccount") in DISCRETIONARY_LEVY_GLACCOUNT:
                        fee_type["desc_grant_amt"] = detail.get("ExtendedAmountWithoutTIP")
                    elif detail.get("RevenueAccount") in ADMIN_GLACCOUNT:
                        fee_type["admn_grant_amt"] = detail.get("ExtendedAmountWithoutTIP")
                    elif detail.get("RevenueAccount") in PENALTY_GLACCOUNT:
                        fee_type["penalties"] = detail.get("ExtendedAmountWithoutTIP")
                    elif detail.get("RevenueAccount") in INTEREST_GLACCOUNT:
                        fee_type["interest"] = detail.get("ExtendedAmountWithoutTIP")

                    optional_fields = detail.get("InvoiceDetailOptionalFields")
                    for field in optional_fields:
                        if field.get("OptionalField") == "SCHEMEYR":
                            scheme_year = field.get("Value")

                posting_date = invoice.get("PostingDate","").split("-")
                val = dict(
                    batch_no = invoice.get("BatchNumber"),
                    entry_no = invoice.get("EntryNumber"),
                    period = invoice.get("FiscalPeriod"),
                    levy_month = posting_date[1] if posting_date else "",
                    scheme_year = scheme_year,
                    mand_grant_amt = fee_type["mand_grant_amt"],
                    desc_grant_amt = fee_type["desc_grant_amt"],
                    admn_grant_amt = fee_type["admn_grant_amt"],
                    penalties = fee_type["penalties"],
                    interest = fee_type["interest"],
                    total_amt = invoice.get("AmountDue"),
                    nsf_cal  = fee_type["mand_grant_amt"], #NSF is always same amount as mandatory grant
                    stakeholder_levy_cal = invoice.get("AmountDue") + fee_type["mand_grant_amt"], # Amount received by SETA + NSF
                    organisation_id = organsation and organsation.id or False,
                    sars_arrival_date = str(fields.Date.from_string(invoice.get("DocumentDate",""))),
                    date_posted = str(fields.Date.from_string(invoice.get("PostingDate","")))
                )

                #_logger.info(f"VAL => {json.dumps(val)}")

                if not self.search([("batch_no","=",val.get('batch_no')), ("entry_no","=",val.get('entry_no'))]):
                    self.create(val)
            #ensure that records are synced before tracking is created
            if invoices:
                self.env["inseta.levy.sync.track"].create({"batch_no": batch, "is_synced": True})
            _logger.info(f"Total Invoices Synced => {len(invoices)}")


class InsetaLevyGLAccount(models.Model):
    """This table holds the details of the various accounts for the levy payment
        Description,AccountType,Status,AccountNumber
    """
    _name = "inseta.levy.glaccount" 
    _description = "INSETA Levy GL Accounts"


    account_no = fields.Char(index=True)
    account_desc = fields.Char(index=True)
    account_type = fields.Char()
    account_group_code = fields.Char(index=True)
    status = fields.Char()

    def _scheduler_sync_glaccounts(self):
        """
            sync GL accounts so that we can use it for mapping when generating the levy income history report
        """
        accounts = sage._get_gl_accounts()
        _logger.info(f"accounts {json.dumps(accounts, indent=4)}")
        vals = []
        # if response and response.get("value"):
        #     accounts = response.get("value")
        for account in accounts:
            if not self.search([('account_no','=',account.get('AccountNumber'))]):
                vals.append(dict(
                    account_no = account.get('AccountNumber'),
                    account_desc = account.get('Description'),
                    account_type = account.get('AccountType'),
                    status = account.get('Status'),
                    account_group_code = account.get('AccountGroupCode'),
                ))

        if vals:
            self.create(vals)



class InsetaLevySyncTrack(models.Model):
    _name = "inseta.levy.sync.track"
    _description = "INSETA Levy History Sync Track"


    batch_no = fields.Integer()
    is_synced = fields.Boolean(help="Indicates if a batch has been synced")



