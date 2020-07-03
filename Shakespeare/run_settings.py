
# Show inquiry answer related classes in the admin panel
SHOW_DEBUG_CLASSES = True

# Display the actual progress scores in the view
DISPLAY_TECH_SCORES_IN_VIEW = False

DOMAIN_NAME = ""

# Sessions settings
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# The display name on the site
SITE_DISPLAY_NAME = "ENLEB BE"

# User authentication
LOGIN_URL = 'general:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# A correction on the font size when rendering a page (to correct for different layouts on different OS
# WkhtmlToPdf renders font size slightly larger on Ubuntu machines vs Windows machines
# Value is interpreted as percentage so it can possibly interact with other set values
PDF_BASE_FONT_SIZE = 85

# An e-mail that will be displayed as contact point when an error occurs
MAIN_CONTACT_EMAIL = "klimaat-menukaart@gmail.com"

PRIVACY_DOCUMENT_URL = None

ENABLE_STAP_3 = False