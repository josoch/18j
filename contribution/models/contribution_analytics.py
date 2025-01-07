# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd

class ContributionAnalytics(models.Model):
    _name = 'contribution.analytics'
    _description = 'Contribution Analytics'
    _rec_name = 'goal_id'

    goal_id = fields.Many2one('contribution.goal', string='Goal', required=True)
    analysis_date = fields.Datetime(string='Analysis Date', default=fields.Datetime.now)
    prediction_type = fields.Selection([
        ('completion_date', 'Goal Completion Date'),
        ('monthly_target', 'Recommended Monthly Target'),
        ('success_probability', 'Success Probability')
    ], string='Prediction Type', required=True)
    
    predicted_value = fields.Float(string='Predicted Value', readonly=True)
    confidence_score = fields.Float(string='Confidence Score', readonly=True)
    recommendation = fields.Text(string='AI Recommendation', readonly=True)
    
    feature_importance = fields.Text(string='Feature Importance', readonly=True)
    model_metrics = fields.Text(string='Model Metrics', readonly=True)

    def _prepare_contribution_data(self, goal):
        """Prepare historical contribution data for analysis"""
        contributions = self.env['contribution.installment'].search([
            ('goal_id', '=', goal.id),
            ('state', '=', 'paid')
        ], order='date asc')
        
        if not contributions:
            return None, None
            
        dates = [(c.date - goal.start_date).days for c in contributions]
        amounts = [c.amount for c in contributions]
        
        return np.array(dates).reshape(-1, 1), np.array(amounts)

    def _analyze_contribution_pattern(self, goal):
        """Analyze contribution patterns and return key metrics"""
        contributions = self.env['contribution.installment'].search([
            ('goal_id', '=', goal.id),
            ('state', '=', 'paid')
        ])
        
        if not contributions:
            return {
                'avg_contribution': 0,
                'frequency': 0,
                'consistency': 0
            }
            
        amounts = [c.amount for c in contributions]
        dates = [c.date for c in contributions]
        
        avg_contribution = sum(amounts) / len(amounts)
        
        # Calculate average days between contributions
        date_diffs = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        frequency = sum(date_diffs) / len(date_diffs) if date_diffs else 0
        
        # Calculate consistency (coefficient of variation)
        std_dev = np.std(amounts) if len(amounts) > 1 else 0
        consistency = 1 - (std_dev / avg_contribution) if avg_contribution else 0
        
        return {
            'avg_contribution': avg_contribution,
            'frequency': frequency,
            'consistency': consistency
        }

    def predict_completion_date(self, goal):
        """Predict the goal completion date based on current progress"""
        X, y = self._prepare_contribution_data(goal)
        if X is None or len(X) < 2:
            return None, 0
            
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate remaining amount
        remaining = goal.target_amount - goal.total_contributed
        
        # Predict days needed for remaining amount
        if model.coef_[0] <= 0:
            return None, 0
            
        days_needed = remaining / model.coef_[0]
        predicted_date = goal.start_date + timedelta(days=int(days_needed))
        
        # Calculate confidence based on R-squared score
        confidence = max(0, min(1, model.score(X, y)))
        
        return predicted_date, confidence

    def recommend_monthly_target(self, goal):
        """Recommend monthly contribution target based on goal and timeline"""
        pattern = self._analyze_contribution_pattern(goal)
        remaining_amount = goal.target_amount - goal.total_contributed
        remaining_months = (goal.end_date - fields.Date.today()).days / 30
        
        if remaining_months <= 0:
            return 0, 0
            
        base_monthly_target = remaining_amount / remaining_months
        
        # Adjust based on historical pattern
        if pattern['consistency'] > 0.8:
            # If contributions are very consistent, stick close to historical average
            adjusted_target = (base_monthly_target + pattern['avg_contribution']) / 2
        else:
            # Add buffer for inconsistent contributions
            adjusted_target = base_monthly_target * (1 + (1 - pattern['consistency']))
            
        confidence = pattern['consistency'] * 0.7 + 0.3
        
        return adjusted_target, confidence

    def calculate_success_probability(self, goal):
        """Calculate the probability of achieving the goal on time"""
        pattern = self._analyze_contribution_pattern(goal)
        predicted_date, completion_confidence = self.predict_completion_date(goal)
        
        if not predicted_date:
            return 0.5, 0
            
        # Base probability on multiple factors
        factors = {
            'timeline': 1 if predicted_date <= goal.end_date else 0,
            'consistency': pattern['consistency'],
            'progress': goal.progress / 100,
            'frequency': 1 if pattern['frequency'] > 0 else 0
        }
        
        # Weight the factors
        weights = {
            'timeline': 0.4,
            'consistency': 0.3,
            'progress': 0.2,
            'frequency': 0.1
        }
        
        probability = sum(factors[k] * weights[k] for k in factors)
        confidence = completion_confidence * 0.7 + pattern['consistency'] * 0.3
        
        return probability, confidence

    @api.model
    def generate_insights(self, goal_id):
        """Generate AI-powered insights for a goal"""
        goal = self.env['contribution.goal'].browse(goal_id)
        
        # Create analytics record
        analytics = self.create({
            'goal_id': goal.id,
            'prediction_type': 'success_probability',
            'analysis_date': fields.Datetime.now(),
        })
        
        # Generate predictions
        completion_date, completion_confidence = analytics.predict_completion_date(goal)
        monthly_target, target_confidence = analytics.recommend_monthly_target(goal)
        probability, prob_confidence = analytics.calculate_success_probability(goal)
        
        # Generate recommendations
        recommendations = []
        if completion_date and completion_date > goal.end_date:
            recommendations.append(_(
                "Current contribution rate suggests completion by %s, which is after the target date. "
                "Consider increasing monthly contributions.") % completion_date.strftime('%Y-%m-%d'))
            
        if monthly_target:
            recommendations.append(_(
                "Recommended monthly contribution: %s %s to stay on track.") % (
                round(monthly_target, 2), goal.currency_id.symbol))
            
        if probability < 0.5:
            recommendations.append(_(
                "Goal at risk. Consider adjusting target or increasing contribution frequency."))
        
        analytics.write({
            'predicted_value': probability,
            'confidence_score': prob_confidence,
            'recommendation': '\n'.join(recommendations),
        })
        
        return analytics.id
