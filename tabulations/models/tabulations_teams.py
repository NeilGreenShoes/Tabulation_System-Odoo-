from odoo import models, fields, api
from odoo.exceptions import UserError


class Teams(models.Model):
    _name = 'tabulation.teams'
    _description = 'Event Teams'
    _rec_name = 'team_name'

    team_name = fields.Char(string="Team Name", required=True)
    team_leader = fields.Many2one('res.partner', string="Team Leader")
    member_ids = fields.Many2many('res.partner', string="Members")
    score = fields.Float(string="Current Score", compute='_compute_current_event_scores', store=True)
    total_event_scores = fields.Float(string="Total Event Scores", compute='_compute_total_event_scores', store=True)
    active = fields.Boolean(string="is Active?", store=True, default="True")
    team_banner = fields.Binary(string="Team Banner", store=True)
    
    event_ids = fields.Many2many('tabulation.events', string="Events")
    session_id = fields.Many2many('tabulation.sessions', string="Sessions")
    scorecard_id = fields.Many2many('tabulation.scorecard', string="Scorecards")
    scorecard_line_id = fields.One2many('tabulation.scorecard.participant', 'team_id', string="Scorecard Lines")
    # dashboard_id = fields.Many2many('tabulation.dashboard', string="Dashboard")

    @api.constrains('team_leader', 'member_ids')
    def _check_team_members_exist_in_team(self):
        for team in self:
            members = set(team.member_ids.ids)
            if team.team_leader:
                members.add(team.team_leader.id)
            if not members:
                continue

            existing_member = self.search([('id', '!=', team.id), ('member_ids', 'in', members)], limit=1)

            if existing_member:
                conflicting_people = existing_member.member_ids.filtered(lambda p: p.id in members)
                names = ", ".join(conflicting_people.mapped('name'))
                
                raise UserError(
                    f"The team member/leader must not already be in a different team. " 
                    f"Conflict found with: {names} (from team '{existing_member.team_name}')"
                )

            existing_leader = self.search([('id', '!=', team.id), ('team_leader', 'in', members)], limit=1)

            if existing_leader:
                name = existing_leader.team_leader
                
                raise UserError(
                    f"The team member/leader must not already be in a different team. " 
                    f"Conflict found with: {name} (from team '{existing_leader.team_leader}')"
                )

    @api.depends('scorecard_line_id.total_score', 'event_ids.is_weighted', 'event_ids.weight')
    def _compute_current_event_scores(self):
        for team in self:
            current_score = 0.0
            weighted_score_sum = 0.0
            total_event_weight = 0.0

            scores_by_event = {line.event_id.id: line.total_score for line in team.scorecard_line_id if line.event_id}

            for event in team.event_ids:
                actual_score = scores_by_event.get(event.id, 0.0)
                
                if event.is_weighted:
                    if event.max_points > 0:
                        weighted_contribution = actual_score * event.weight
                        weighted_score_sum += weighted_contribution
                        total_event_weight += event.weight
                else:
                    current_score += actual_score

            if total_event_weight > 0:
                final_weighted_score = weighted_score_sum / total_event_weight
                current_score += final_weighted_score

            team.score = current_score
            
    @api.depends('event_ids.max_points', 'event_ids.is_weighted', 'event_ids.weight')
    def _compute_total_event_scores(self):
        for team in self:
            total_max = 0.0
            weighted_max_sum = 0.0
            total_event_weight = 0.0

            for event in team.event_ids:
                if event.is_weighted:
                    if event.max_points > 0:
                        weighted_max_contribution = event.max_points * event.weight
                        weighted_max_sum += weighted_max_contribution
                        total_event_weight += event.weight
                else:
                    total_max += event.max_points

            if total_event_weight > 0:
                final_weighted_max = weighted_max_sum / total_event_weight
                total_max += final_weighted_max

            team.total_event_scores = total_max