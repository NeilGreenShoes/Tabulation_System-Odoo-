{
    'name': "tabulations",
    'summary': "Tabulation",
    'description': "Long description of module's purpose",
    'category': 'Tools',
    'version': '0.1',
    'depends': ['base', 'contacts', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/tabulation_events.xml',
        'views/tabulation_teams.xml',
        'views/tabulation_scorecard.xml',
        'views/tabulation_sessions.xml',
        'views/tabulation_judges.xml',
        'views/tabulation_dashboard.xml',
        'views/tabulation_config.xml',
        'views/tabulation_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/web/static/lib/Chart/Chart.js',
            'tabulations/static/src/css/tabulation_dashboard.css',
            'tabulations/static/src/js/tabulation_dashboard.js',
            # 'tabulations/static/src/xml/tabulation_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}
