from odoo import fields, models, api

class Events(models.Model):
    _name = 'tabulation.events'
    _description = 'Tabulation Events'

    name = fields.Char(required=True)
    description = fields.Text()
    start_date = fields.Date()
    end_date = fields.Date()
    is_weighted = fields.Boolean(string="Is Weighted", default=False)
    weight = fields.Float(string="Weight", default=1.0, digits=(10, 2))
    max_points = fields.Float(compute="_compute_max_points", store=True)

    event_type_id = fields.Many2one('tabulation.event.type', string="Event Type")
    criteria_ids = fields.One2many('tabulation.criteria', 'event_id')
    participant_ids = fields.Many2many('tabulation.participants',string="Participants")
    judge_id = fields.Many2many('tabulation.judges')
    scorecard_id = fields.One2many('tabulation.scorecard', 'event_id', string="Scorecards")
    scorecard_line_id = fields.One2many('tabulation.scorecard.participant', 'event_id')
    team_id = fields.Many2many('tabulation.teams', store="True")
    # dashboard = fields.Many2many('tabulation.events', string="Dashboard")

    @api.depends('criteria_ids.points', 'is_weighted')
    def _compute_max_points(self):
        for event in self:
            if event.is_weighted:
                event.max_points = sum(event.criteria_ids.mapped('weighted')) * 100
            else:
                event.max_points = sum(event.criteria_ids.mapped('points'))

class EventType(models.Model):
    _name = 'tabulation.event.type'
    _description = 'Event Type'

    name = fields.Char(string="Name", required=True)
    event_id = fields.One2many('tabulation.events', 'event_type_id', string="Events")