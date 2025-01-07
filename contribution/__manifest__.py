# -*- coding: utf-8 -*-
{
    'name': 'Contribution Management',
    'version': '18.0.1.0.0',
    'category': 'Finance',
    'summary': 'Manage Individual and Group Contributions with AI Insights',
    'description': """
Contribution Management System
============================
A comprehensive system for managing financial contributions with smart features:

Key Features:
------------
* Goal Setting and Management
* Installment Contribution Tracking
* Smart AI-Powered Recommendations
* Group Collaboration Tools
* Payment Integration
* Automated Reminders
* Detailed Analytics and Reports
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'account',
        'web',
        'calendar',
    ],
    'data': [
        # Security
        'security/contribution_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_sequence_data.xml',
        
        # Views
        'views/contribution_goal_views.xml',
        'views/contribution_installment_views.xml',
        'views/contribution_payment_views.xml',
        'views/contribution_analytics_views.xml',
        'views/contribution_dashboard_views.xml',
        'views/contribution_menus.xml',
        'views/contribution_templates.xml',
    ],
    'demo': [
        'demo/contribution_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'contribution/static/src/scss/contribution_dashboard.scss',
            'contribution/static/src/js/contribution_dashboard.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': [
            'numpy',
            'pandas',
            'scikit-learn',
        ],
    },
}
