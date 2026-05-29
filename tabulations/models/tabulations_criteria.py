from odoo import fields, models, api

class Criteria(models.Model):
    _name = 'tabulation.criteria'
    _description = 'Event Criteria'

    name = fields.Char(required=True)
    points = fields.Float(required=True)
    is_weighted = fields.Boolean()
    weighted = fields.Float()
    sequence = fields.Integer(default=10)
    
    scorecard_line_id = fields.Many2many('tabulation.scorecard.participant')
    event_id = fields.Many2one('tabulation.events',ondelete='cascade',required=True)