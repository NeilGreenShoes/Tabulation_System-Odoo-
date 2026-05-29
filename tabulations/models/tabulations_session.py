from odoo import models, fields, api

class Sessions(models.Model):
    _name = 'tabulation.sessions'
    _description = 'Tabulation Sessions'
    _order = 'sequence, id'

    name = fields.Char(string="Session Name", required=True)
    date = fields.Date(string="Date")
    
    event_id = fields.Many2one('tabulation.events', string="Event")
    sequence = fields.Integer(string="Sequence", default=10)
    stage_id = fields.Many2one('tabulation.session.stage',string="Stage",group_expand='_read_group_stage_ids',default=lambda self: self.env['tabulation.session.stage'].search([], limit=1).id)
    scorecard_ids = fields.One2many('tabulation.scorecard', 'session_id', string="Scorecards")
    team_id = fields.Many2many('tabulation.teams', compute='_compute_team_id', store=False, readonly=True)
    participant_id = fields.Many2many('tabulation.participants')

    start_date = fields.Date(related='event_id.start_date', store=True)
    end_date = fields.Date(related='event_id.end_date', store=True)
    
    session_wizard_id = fields.One2many('tabulation.session.wizard', 'session_id', string="Wizards")

    @api.model
    def create(self, vals_list):
        sessions = super().create(vals_list)

        for sesh in sessions:
            sesh._notify_dashboard()

        return sessions

    def write(self, vals):
        result = super().write(vals)

        for sesh in self:
            sesh._notify_dashboard()

        return result

    def _notify_dashboard(self):
        for record in self:
            self.env['bus.bus']._sendone(
                "tabulation_dashboard_channel",  
                "dashboard_refresh",             
                {                               
                    "model": record._name,
                    "ids": record.ids,
                    "message": "Dashboard updated",
                }
            )

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        return self.env['tabulation.session.stage'].search([], order=order)
    
    @api.depends('event_id', 'event_id.team_id')
    def _compute_team_id(self):
        for record in self:
            if record.event_id and record.event_id.team_id:
                record.team_id = record.event_id.team_id
            else:
                record.team_id = False
    
    def action_open_calculator(self):
        self.ensure_one()

        scorecard = self.env['tabulation.scorecard'].search([('session_id', '=', self.id)], limit=1)

        if not scorecard:
            participant_lines = []

            for team in self.event_id.team_id:
                score_lines = []

                for c in self.event_id.criteria_ids:
                    score_lines.append((0, 0, {
                        'criteria_id': c.id,
                        'score': 0.0,
                    }))

                participant_lines.append((0, 0, {
                    'team_id': team.id,
                    'event_id': self.event_id.id,
                    'score_entry_ids': score_lines,
                }))

            scorecard = self.env['tabulation.scorecard'].create({
                'session_id': self.id,
                'participant_line_ids': participant_lines,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Tabulation',
            'res_model': 'tabulation.scorecard',
            'res_id': scorecard.id,
            'view_mode': 'form',
            'target': 'current',
        }

class SessionStage(models.Model):
    _name = 'tabulation.session.stage'
    _description = 'Session Stage'
    _order = 'sequence'

    name = fields.Char(string="Stage Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    fold = fields.Boolean(string="Folded in Kanban")
    active = fields.Boolean(string="Is Active", default="True")