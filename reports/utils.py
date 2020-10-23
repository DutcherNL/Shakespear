from django.template import Context, Template, Engine

def full_render_layout(layout_html, context):
    template = Template(layout_html)
    print(context)

    context = Context(context)
    result = template.render(context)

    print(context)

    return result