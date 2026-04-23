from django.utils.html import format_html

BADGE_STYLE = '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>'
BOLD_FORMAT = '<b>{}</b>'


def active_badge(obj):
    color = 'green' if obj.is_active else 'red'
    label = 'Active' if obj.is_active else 'Inactive'
    return format_html(BADGE_STYLE, color, label)


def color_badge(color, label):
    return format_html(BADGE_STYLE, color, label)
