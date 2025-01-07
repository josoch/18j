# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import requests
from datetime import datetime

class ContributionPayment(models.Model):
    _name = 'contribution.payment'
    _description = 'Contribution Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, default=lambda self: _('New'))
    installment_id = fields.Many2one('contribution.installment', string='Installment',
        required=True, ondelete='restrict')
    goal_id = fields.Many2one('contribution.goal', related='installment_id.goal_id',
        string='Goal', store=True)
    
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='installment_id.currency_id', store=True)
    
    payment_method = fields.Selection([
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('manual', 'Manual Payment')
    ], string='Payment Method', required=True, default='stripe')
    
    payment_token = fields.Char(string='Payment Token', readonly=True)
    payment_date = fields.Datetime(string='Payment Date', readonly=True)
    transaction_id = fields.Char(string='Transaction ID', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('done', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    payment_url = fields.Char(string='Payment URL', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    
    # Payment Gateway Configuration
    stripe_public_key = fields.Char(
        related='company_id.stripe_public_key', string='Stripe Public Key')
    stripe_secret_key = fields.Char(
        related='company_id.stripe_secret_key', string='Stripe Secret Key')
    paypal_client_id = fields.Char(
        related='company_id.paypal_client_id', string='PayPal Client ID')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('contribution.payment') or _('New')
        return super(ContributionPayment, self).create(vals)

    def action_create_stripe_session(self):
        """Create Stripe payment session"""
        self.ensure_one()
        if not self.stripe_secret_key:
            raise UserError(_('Stripe secret key is not configured.'))

        try:
            # This is a placeholder for the actual Stripe API call
            # In production, you would use the stripe library
            headers = {
                'Authorization': f'Bearer {self.stripe_secret_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'amount': int(self.amount * 100),  # Convert to cents
                'currency': self.currency_id.name.lower(),
                'payment_method_types': ['card'],
                'metadata': {
                    'payment_id': self.id,
                    'installment_id': self.installment_id.id,
                    'goal_id': self.goal_id.id
                }
            }
            
            # Simulate Stripe API response
            response = {
                'id': f'cs_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'url': f'https://stripe.com/pay/{self.id}'
            }
            
            self.write({
                'payment_token': response['id'],
                'payment_url': response['url'],
                'state': 'pending'
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': response['url'],
                'target': 'new'
            }
            
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': str(e)
            })
            raise UserError(_('Failed to create Stripe payment session: %s') % str(e))

    def action_create_paypal_order(self):
        """Create PayPal payment order"""
        self.ensure_one()
        if not self.paypal_client_id:
            raise UserError(_('PayPal client ID is not configured.'))

        try:
            # This is a placeholder for the actual PayPal API call
            # In production, you would use the paypalrestsdk library
            data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': self.currency_id.name,
                        'value': str(self.amount)
                    },
                    'custom_id': self.id
                }]
            }
            
            # Simulate PayPal API response
            response = {
                'id': f'PAY-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'links': [{
                    'href': f'https://paypal.com/checkout/{self.id}',
                    'rel': 'approve'
                }]
            }
            
            self.write({
                'payment_token': response['id'],
                'payment_url': response['links'][0]['href'],
                'state': 'pending'
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': response['links'][0]['href'],
                'target': 'new'
            }
            
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': str(e)
            })
            raise UserError(_('Failed to create PayPal order: %s') % str(e))

    def action_confirm_manual_payment(self):
        """Confirm manual payment"""
        self.ensure_one()
        self.write({
            'state': 'done',
            'payment_date': fields.Datetime.now(),
            'transaction_id': f'MANUAL-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        })
        self.installment_id.action_mark_paid()

    def action_cancel_payment(self):
        """Cancel payment"""
        self.write({
            'state': 'cancelled'
        })

    def process_payment_webhook(self, data):
        """Process payment gateway webhook"""
        payment_id = data.get('metadata', {}).get('payment_id')
        if not payment_id:
            return False
            
        payment = self.browse(int(payment_id))
        if not payment:
            return False
            
        if data.get('status') == 'succeeded':
            payment.write({
                'state': 'done',
                'payment_date': fields.Datetime.now(),
                'transaction_id': data.get('id')
            })
            payment.installment_id.action_mark_paid()
        else:
            payment.write({
                'state': 'failed',
                'error_message': data.get('error', {}).get('message', 'Payment failed')
            })
            
        return True

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('Payment amount must be greater than zero.'))
