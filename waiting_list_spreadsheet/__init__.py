# -*- coding: utf-8 -*-

from . import models

def post_init_hook(env):
    """Create default spreadsheet template after module installation"""
    env['waiting.list.spreadsheet']._create_default_template()
