from django.db import connections, DEFAULT_DB_ALIAS


connection = connections[DEFAULT_DB_ALIAS]

schema_editor = connection.schema_editor(atomic=True)

migration = None # future object

#migration.apply(project_state, schema_editor)