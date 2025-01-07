# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ContributionInstallment(models.Model):
    _name = 'contribution.installment'
    _description = 'Contribution Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', readonly=True, default=lambda self: _('New'))
    goal_id = fields.Many2one('contribution.goal', string='Goal', required=True)
    contributor_id = fields.Many2one('res.users', string='Contributor',
        default=lambda self: self.env.user, required=True)
    
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='goal_id.currency_id', store=True, readonly=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('online', 'Online Payment')
    ], string='Payment Method', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    payment_reference = fields.Char(string='Payment Reference')
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('contribution.installment') or _('New')
        return super(ContributionInstallment, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'pending'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    @api.constrains('amount')
    def _check_amount(self):
        for installment in self:
            if installment.amount <= 0:
                raise ValidationError(_("Amount must be greater than zero."))
