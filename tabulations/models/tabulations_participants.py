from odoo import models, fields, api

class Participants(models.Model):
    _name = 'tabulation.participants'
    _description = 'Event Participants'
    _rec_name = 'participant_name'
    
    is_whole_team = fields.Boolean()
    participant_name = fields.Char(string="Participant Name")
    
    team_id = fields.Many2one('tabulation.teams', string="Team Name")
    event_ids = fields.Many2many('tabulation.events', string="Events")
    scorecard_line_id = fields.One2many('tabulation.scorecard.participant', 'event_id')
    session_id = fields.Many2many('tabulation.sessions', string="Session")
    scorecard_id = fields.Many2many('tabulation.scorecard', string="Scorecard")
    
    @api.onchange('is_whole_team', 'team_id')
    def _onchange_team_logic(self):
        if self.is_whole_team and self.team_id:
            self.participant_name = self.team_id.display_name
        elif not self.is_whole_team:
            self.participant_name = False