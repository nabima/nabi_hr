# -*- coding: utf-8 -*-
from openerp import api,fields,models


class HrMission(models.Model):
    _inherit = 'hr.employee.mission'
    budget = fields.Float(store=True)
