from odoo import fields, models, api
from odoo.exceptions import ValidationError
import io
import base64
import xlsxwriter

class Scorecard(models.Model):
    _name = 'tabulation.scorecard'
    _description = 'Final Tabulation Scorecard'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    session_id = fields.Many2one('tabulation.sessions', string="Session")
    event_id = fields.Many2one('tabulation.events', related='session_id.event_id', store=True)
    team_id = fields.Many2many('tabulation.teams', compute='_compute_event_data', string="Event Teams")
    participant_ids = fields.Many2many('tabulation.participants', compute='_compute_event_data', string="Event Participants")
    participant_line_ids = fields.One2many('tabulation.scorecard.participant', 'scorecard_id')

    def action_generate_scorecards(self):
        for record in self:
            if not record.session_id:
                raise ValidationError("Please select a Session first.")
            event = record.session_id.event_id
            if not event:
                raise ValidationError(
                    "The selected session has no event linked to it."
                )
            teams = event.team_id

            if not teams:
                raise ValidationError(
                    "The event '%s' has no teams assigned." % event.name
                )

            existing_team_ids = record.participant_line_ids.mapped('team_id.id')

            new_participant_lines = []

            for team in teams:
                if team.id in existing_team_ids:
                    continue

                score_lines = []

                if event.criteria_ids:
                    for c in event.criteria_ids:
                        score_lines.append((0, 0, {
                            'criteria_id': c.id,
                            'score': 0.0,
                        }))

                new_participant_lines.append((0, 0, {
                    'team_id': team.id,
                    'score_entry_ids': score_lines,
                }))

            if new_participant_lines:
                record.write({
                    'participant_line_ids': new_participant_lines
                })

        return True

    @api.depends('session_id', 'event_id')
    def _compute_event_data(self):
        for record in self:
            event = record.session_id.event_id or record.event_id
            record.team_id = event.team_id if event else False
            record.participant_ids = event.participant_ids if event else False

    @api.onchange('session_id')
    def _onchange_session_id(self):
        if self.session_id and self.session_id.team_id:
            lines = []
            for team in self.session_id.team_id:
                score_lines = []
                if self.session_id.event_id:
                    for c in self.session_id.event_id.criteria_ids:
                        score_lines.append((0, 0, {
                            'criteria_id': c.id,
                            'score': 0.0
                        }))

                lines.append((0, 0, {
                    'team_id': team.id,
                    'score_entry_ids': score_lines,
                }))
            
            self.participant_line_ids = [(5, 0, 0)] + lines
        else:
            self.participant_line_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'session_id' in vals and not vals.get('participant_line_ids'):
                session = self.env['tabulation.sessions'].browse(vals['session_id'])
                event = session.event_id
                if session.team_id:
                    participant_lines = []
                    for team in session.team_id:
                        score_lines = []
                        if event:
                            for c in event.criteria_ids:
                                score_lines.append((0, 0, {'criteria_id': c.id, 'score': 0.0}))
                        participant_lines.append((0, 0, {
                            'team_id': team.id,
                            'score_entry_ids': score_lines
                            }))
                    vals['participant_line_ids'] = participant_lines
        return super().create(vals_list)

class ScorecardParticipant(models.Model):
    _name = 'tabulation.scorecard.participant'
    _description = 'Participant Score Line'

    name = fields.Char(compute='_compute_name', store=True)
    total_score = fields.Float(compute='_compute_total_score', store=True, string="Total Score")

    scorecard_id = fields.Many2one('tabulation.scorecard', ondelete='cascade')
    participant_id = fields.Many2one('tabulation.participants', string="Participant")
    team_id = fields.Many2one('tabulation.teams', string="Team")
    event_id = fields.Many2one('tabulation.events', related='scorecard_id.event_id', store=True)
    score_entry_ids = fields.One2many('tabulation.score.entry', 'participant_line_id')

    def export_excel(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.team_id.team_name or "Scorecard")

        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        bold_format = workbook.add_format({'bold': True, 'align': 'right'})
        body_format = workbook.add_format({'align': 'center', 'text_wrap': True})
        total_format = workbook.add_format({'bold': True, 'align': 'right'})

        sheet.set_row(0, 20)
        sheet.set_row(1, 20)
        sheet.set_row(2, 30)
        sheet.set_row(3, 30)
        
        sheet.set_column(0, 4, 20)

        sheet.merge_range(0, 0, 0, 4, "PARTICIPANT SCORECARD", header_format)

        sheet.write(1, 0, "Event:", header_format)
        sheet.merge_range(1, 1, 1, 2, self.event_id.name or "N/A", body_format)
        sheet.write(1, 3, "Team:", header_format)
        sheet.write(1, 4, self.team_id.team_name or "N/A", body_format)

        sheet.write(2, 0, "Criteria", header_format)
        sheet.write(2, 1, "Max Points", header_format)
        sheet.write(2, 2, "Weight", header_format)
        sheet.write(2, 3, "Remarks", header_format)
        sheet.write(2, 4, "Score", header_format)

        start_row = 3

        for index, entry in enumerate(self.score_entry_ids, start=start_row):
            sheet.write(index, 0, entry.criteria_id.name, body_format)
            sheet.write(index, 1, entry.criteria_points, body_format)
            sheet.write(index, 2, entry.criteria_weight or "", body_format)
            sheet.write(index, 3, entry.remarks or "", body_format)
            sheet.write(index, 4, entry.score, body_format)

        total_row = start_row + len(self.score_entry_ids)
        sheet.set_row(total_row, 20)

        sheet.write(total_row, 0, "Total Score:", total_format)
        sheet.merge_range(total_row, 1, total_row, 4, self.total_score or 0.0, total_format)

        total_row += 1
        sheet.write(total_row, 0, "Judge Name:", bold_format)
        sheet.merge_range(total_row, 1, total_row, 4, "", body_format)
        total_row += 1
        sheet.write(total_row, 0, "Judge Signature:", bold_format)
        sheet.merge_range(total_row, 1, total_row, 4, "", body_format)

        sheet.set_column(5, 16383, None, None, {'hidden': True})
        for row in range(total_row + 1, 1048576):
            sheet.set_row(row, None, None, {'hidden': True})

        for sheet in workbook.worksheets():
            sheet.protect()

        workbook.close()

        output.seek(0)
        file_data = output.getvalue()

        attachment = self.env['ir.attachment'].create({
            'name': 'scorecard.xlsx',
            'type': 'binary',
            'raw': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.depends('participant_id', 'team_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.team_id.team_name or rec.participant_id.participant_name or "New Entry"

    @api.depends('score_entry_ids.score','score_entry_ids.criteria_points','score_entry_ids.criteria_weight')
    def _compute_total_score(self):

        for rec in self:
            total = 0.0

            for line in rec.score_entry_ids:
                if line.criteria_is_weighted and line.criteria_points > 0:
                    total += ((line.score / line.criteria_points)* line.criteria_weight)
                else:
                    total += line.score

            rec.total_score = round(total, 2) * 100 if round(total, 2) <= 1 else round(total, 2)

class ScoreEntry(models.Model):
    _name = 'tabulation.score.entry'

    criteria_points = fields.Float(related='criteria_id.points', store=True)
    criteria_weight = fields.Float(related='criteria_id.weighted', store=True)
    criteria_is_weighted = fields.Boolean(related='criteria_id.is_weighted', store=True)
    score = fields.Float()
    remarks = fields.Text()

    participant_line_id = fields.Many2one('tabulation.scorecard.participant', ondelete='cascade')
    criteria_id = fields.Many2one('tabulation.criteria') 