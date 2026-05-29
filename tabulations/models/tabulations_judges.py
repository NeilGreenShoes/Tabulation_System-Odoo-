from odoo import fields, models, api
from odoo.exceptions import UserError

class Judges(models.Model):
    _name = 'tabulation.judges'
    _description = 'Tabulation Judges'

    name = fields.Many2one('res.users', string="Judge Name", required=True)
    description = fields.Text(string="Description")
    
    event_id = fields.Many2many('tabulation.events')
    # scorecard_line_id = fields.Many2many('tabulation.scorecard.line')

    @api.constrains('name')
    def check_judge(self):
        for judge in self:
            existing_judge = self.search([('id', '!=', judge.id), ('name', '=', judge.name.id)], limit=1)
            if existing_judge:
                raise UserError(f"The judge '{judge.name.name}' already exists.")
    