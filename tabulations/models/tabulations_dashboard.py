import base64
from odoo import models, fields, api


class TabulationDashboard(models.Model):
    _name = "tabulation.dashboard"
    _description = "Tabulation Dashboard"

    name = fields.Char(default="Dashboard")

class TabulationDashboardReport(models.AbstractModel):
    _name = "report.tabulation.dashboard"
    _description = "Tabulation Dashboard Report"

    @api.model
    def get_dashboard_data(self):

        teams = self.env['tabulation.teams'].search([])
        events = self.env['tabulation.events'].search([])
        standings = sorted(teams,key=lambda t: t.score or 0,reverse=True)
        sessions = self.env["tabulation.sessions"].search([])
        session_data = []

        if not sessions:
            return session_data

        for s in sessions:
            session_data.append({
                'id': s.id,
                'name': s.name,
                'event': {'id': s.event_id.id, 'name': s.event_id.name} if s.event_id else False,
                'stage': s.stage_id.name,
            })

        def format_banner(banner_bytes):
            if banner_bytes:
                if isinstance(banner_bytes, bytes):
                    b64_string = base64.b64encode(banner_bytes).decode('utf-8')
                    return f"data:image/jpeg;base64,{b64_string}"
                return str(banner_bytes)
            return "No Photo Found!"

        return {

            "teams": [
                {
                    "id": t.id,
                    "team_name": t.team_name,
                    "score": round(t.score, 2),
                    "team_banner": format_banner(t.team_banner),
                }
                for t in teams
            ],

            "events": [
                {
                    "id": e.id,
                    "name": e.name,
                    "start_date": str(e.start_date or ""),
                    "end_date": str(e.end_date or ""),
                    "max_points": e.max_points,
                    "is_weighted": e.is_weighted,
                    "weight": e.weight,
                }
                for e in events
            ],

            "standings": [
                {
                    "id": s.id,
                    "team_name": s.team_name,
                    "score": round(s.score),
                }
                for s in standings
            ],

            "sessions": session_data,
        }

class TabulationSessionWizard(models.TransientModel):
    _name = 'tabulation.session.wizard'
    _description = 'Tabulation Session Wizard'

    session_id = fields.Many2one('tabulation.sessions')

    name = fields.Char(related='session_id.name', readonly=True)
    
    event_id = fields.Many2one(related='session_id.event_id', readonly=True)
    stage_id = fields.Many2one(related='session_id.stage_id', readonly=True)
    judge_id = fields.Many2many(related='session_id.event_id.judge_id', readonly=True)