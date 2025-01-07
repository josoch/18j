# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    # Stripe Configuration
    stripe_public_key = fields.Char(string='Stripe Public Key', groups='base.group_system')
    stripe_secret_key = fields.Char(string='Stripe Secret Key', groups='base.group_system')
    stripe_webhook_key = fields.Char(string='Stripe Webhook Key', groups='base.group_system')
    
    # PayPal Configuration
    paypal_client_id = fields.Char(string='PayPal Client ID', groups='base.group_system')
    paypal_secret_key = fields.Char(string='PayPal Secret Key', groups='base.group_system')
    paypal_webhook_id = fields.Char(string='PayPal Webhook ID', groups='base.group_system')
    
    # Bank Transfer Configuration
    bank_account_number = fields.Char(string='Bank Account Number')
    bank_account_holder = fields.Char(string='Bank Account Holder')
    bank_name = fields.Char(string='Bank Name')
    bank_swift_code = fields.Char(string='SWIFT/BIC Code')
    bank_iban = fields.Char(string='IBAN')
