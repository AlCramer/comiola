import re

# colors for gui & components
col_display_bg = '#454545'

col_cntrl_bg = '#303030'
col_cntrltext = '#DEDEDE'
col_cntrltext_dis = '#808080'
col_cntrlheader = '#A0A0A0'
col_cntrllabel = '#808080'
col_cntrl_entrybg = '#f0f0f0'
col_cntrl_entryfg = '#000000'

col_tabbar = col_display_bg
col_tabselected = col_cntrl_bg
col_tabunselected = col_display_bg

col_dropdownbg = col_cntrl_bg
col_dropdownfg = col_cntrltext

def isHexColor(color):
    return re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color) is not None

