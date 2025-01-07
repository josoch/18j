# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import hmac
import hashlib

class PaymentWebhook(http.Controller):
    
    @http.route('/contribution/webhook/stripe', type='json', auth='public', csrf=False)
    def stripe_webhook(self):
        """Handle Stripe webhook notifications"""
        event = None
        payload = request.httprequest.data
        sig_header = request.httprequest.headers.get('Stripe-Signature')
        
        try:
            # Verify webhook signature
            webhook_secret = request.env['res.company'].sudo().search([], limit=1).stripe_webhook_key
            if not webhook_secret:
                return {'status': 'error', 'message': 'Webhook secret not configured'}
                
            try:
                # This is a placeholder for Stripe signature verification
                # In production, you would use stripe.Webhook.construct_event
                event = json.loads(payload)
            except ValueError as e:
                return {'status': 'error', 'message': 'Invalid payload'}
                
            if event['type'] == 'payment_intent.succeeded':
                payment = request.env['contribution.payment'].sudo().process_payment_webhook(event['data']['object'])
                if payment:
                    return {'status': 'success'}
                    
            return {'status': 'ignored'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/contribution/webhook/paypal', type='json', auth='public', csrf=False)
    def paypal_webhook(self):
        """Handle PayPal webhook notifications"""
        event = None
        payload = request.httprequest.data
        
        try:
            # Verify webhook authenticity
            webhook_id = request.env['res.company'].sudo().search([], limit=1).paypal_webhook_id
            if not webhook_id:
                return {'status': 'error', 'message': 'Webhook ID not configured'}
                
            try:
                # This is a placeholder for PayPal webhook verification
                # In production, you would verify the webhook signature
                event = json.loads(payload)
            except ValueError as e:
                return {'status': 'error', 'message': 'Invalid payload'}
                
            if event['event_type'] == 'PAYMENT.CAPTURE.COMPLETED':
                payment = request.env['contribution.payment'].sudo().process_payment_webhook(event['resource'])
                if payment:
                    return {'status': 'success'}
                    
            return {'status': 'ignored'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/contribution/payment/return/<string:provider>', type='http', auth='public', website=True)
    def payment_return(self, provider, **kwargs):
        """Handle payment return URLs"""
        if provider == 'stripe':
            # Handle Stripe return
            session_id = kwargs.get('session_id')
            if session_id:
                payment = request.env['contribution.payment'].sudo().search([('payment_token', '=', session_id)], limit=1)
                if payment:
                    return request.render('contribution.payment_success_template', {
                        'payment': payment
                    })
                    
        elif provider == 'paypal':
            # Handle PayPal return
            token = kwargs.get('token')
            if token:
                payment = request.env['contribution.payment'].sudo().search([('payment_token', '=', token)], limit=1)
                if payment:
                    return request.render('contribution.payment_success_template', {
                        'payment': payment
                    })
                    
        # If something goes wrong, show error page
        return request.render('contribution.payment_error_template', {})
