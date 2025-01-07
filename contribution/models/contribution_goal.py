# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ContributionGoal(models.Model):
    _name = 'contribution.goal'
    _description = 'Contribution Goal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Goal Name', required=True, tracking=True)
    code = fields.Char(string='Reference', readonly=True, default=lambda self: _('New'))
    goal_type = fields.Selection([
        ('individual', 'Individual'),
        ('group', 'Group')
    ], string='Goal Type', required=True, default='individual', tracking=True)
    
    target_amount = fields.Monetary(string='Target Amount', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, default=lambda self: self.env.company.currency_id)
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date(string='End Date', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    description = fields.Text(string='Description')
    owner_id = fields.Many2one('res.users', string='Owner',
        default=lambda self: self.env.user, required=True)
    member_ids = fields.Many2many('res.users', string='Members')
    
    installment_ids = fields.One2many('contribution.installment', 'goal_id', string='Installments')
    total_contributed = fields.Monetary(string='Total Contributed',
        compute='_compute_total_contributed', store=True)
    progress = fields.Float(string='Progress (%)', compute='_compute_progress', store=True)
    
    reminder_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Reminder Frequency', default='monthly')
    
    next_reminder_date = fields.Date(string='Next Reminder Date',
        compute='_compute_next_reminder_date', store=True)
    
    # AI Insights Fields
    predicted_completion_date = fields.Date(string='Predicted Completion Date', readonly=True)
    recommended_monthly_contribution = fields.Monetary(string='Recommended Monthly Contribution',
        currency_field='currency_id', readonly=True)
    success_probability = fields.Float(string='Success Probability', readonly=True)
    ai_recommendation = fields.Text(string='AI Recommendation', readonly=True)
    last_analysis_date = fields.Datetime(string='Last Analysis Date', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('contribution.goal') or _('New')
        return super(ContributionGoal, self).create(vals)

    @api.depends('installment_ids.amount', 'installment_ids.state')
    def _compute_total_contributed(self):
        for goal in self:
            goal.total_contributed = sum(goal.installment_ids.filtered(
                lambda x: x.state == 'paid').mapped('amount'))

    @api.depends('total_contributed', 'target_amount')
    def _compute_progress(self):
        for goal in self:
            goal.progress = (goal.total_contributed / goal.target_amount * 100) if goal.target_amount else 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for goal in self:
            if goal.start_date and goal.end_date and goal.start_date > goal.end_date:
                raise ValidationError(_("End date must be greater than start date."))

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_send_reminder(self):
        """Send reminder to all members about their pending contributions"""
        self.ensure_one()
        template = self.env.ref('contribution.contribution_reminder_email_template')
        for member in self.member_ids:
            template.send_mail(self.id, force_send=True, email_values={'email_to': member.email})

    @api.depends('reminder_frequency', 'start_date')
    def _compute_next_reminder_date(self):
        for goal in self:
            if not goal.start_date or not goal.reminder_frequency:
                goal.next_reminder_date = False
                continue
            
            today = fields.Date.today()
            if goal.reminder_frequency == 'daily':
                goal.next_reminder_date = today + timedelta(days=1)
            elif goal.reminder_frequency == 'weekly':
                goal.next_reminder_date = today + timedelta(days=7)
            else:  # monthly
                goal.next_reminder_date = today + timedelta(days=30)

    def action_analyze_goal(self):
        """Generate AI-powered insights for the goal"""
        self.ensure_one()
        analytics_id = self.env['contribution.analytics'].generate_insights(self.id)
        analytics = self.env['contribution.analytics'].browse(analytics_id)
        
        # Update goal with insights
        completion_date, _ = analytics.predict_completion_date(self)
        monthly_target, _ = analytics.recommend_monthly_target(self)
        probability, _ = analytics.calculate_success_probability(self)
        
        self.write({
            'predicted_completion_date': completion_date,
            'recommended_monthly_contribution': monthly_target,
            'success_probability': probability,
            'ai_recommendation': analytics.recommendation,
            'last_analysis_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('AI Analysis Complete'),
                'message': _('Goal insights have been updated.'),
                'sticky': False,
                'type': 'success',
            }
        }

    @api.model
    def _update_all_goals_analysis(self):
        """Cron job to update AI analysis for all active goals"""
        active_goals = self.search([('state', '=', 'active')])
        for goal in active_goals:
            goal.action_analyze_goal()
