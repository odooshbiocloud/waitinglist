# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    waiting_list_default_survey_id = fields.Many2one(
        'survey.survey',
        string='Default Feedback Survey',
        config_parameter='waiting_list.default_survey_id',
        help='Default survey to send to customers after their visit'
    )
