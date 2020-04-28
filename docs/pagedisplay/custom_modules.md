Creating Custom Modules
======================

To create a custom module one needs to create two classes:
- The Database representation of the module (Module)
- The displayed representation of the module (ModuleWidget)

The Module
----------
The Module extends on the `django Model` class and can be handled as such. As a result, make sure that Modules
are either defined in `models.py` or import the modules in the file accordingly.

A `Module` has similarities with the `django Field` in the way that they both use a widget to render it's content.
As such each Module must define a default widget that it will use to render itself. However, in the render method
one can give a widget to use instead. This is used to replace widgets in the various `Renderers`


> Note: At this point the attribute `_type` needs to contain an integer value that does not conflict with
any of the other modules. It is used to quickly retrieve the right module. There are plans to use
`django.content_types` in the future instead.

Basic Module
------------

A Basic Module has some reduced render options. It is meant for modules that contain no other modules (i.e. no chians).
It should generally be the Module you want to add so extend using the `BasicModuleMixin` (for now) 
The primary change is that it limits the template context given to the `Widget`. When the widget wants to use
certain keyword arguments it should be defined in `Widget` `use_from_context`. These attributes will be included in the
Widget `render` method call. Any keyword given in the Widgets render call will also end up in the Widgets context

``` python
class MyBasicWidget(BaseModuleWidget):
   use_from_context = ['attribute_1', 'some_object_ref']
   
   def render(self, request=None, attribute_1=None, some_object_ref=None, **kwargs):
      # Insert whatever you want to do
      return super.render(request=request,
                          attribute_1=attribute_1,
                          some_object_ref=some_object_ref,
                          **kwargs)
   
```

This implementation is used to prevent accidental corruption or misuse in some of the context attributes when rendering
the Widget.


> The Renderer can set certain Modules to render a different Widget instead of the default. This is done through the
render_module template tag. As such the Module itself is not aware of the Renderer in the same way that a
`django Field` is not aware of the Form in which it is contained. 
