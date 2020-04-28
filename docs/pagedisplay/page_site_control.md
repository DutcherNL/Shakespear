Page Site Control
=================

A simple Page Site
-------------------

A `PageSite` allows for displaying and editing your pages. By default a PageSite is available that allows any logged-in
user to view and edit any PageDisplay. This is possibly not what you want. In that case you want to create a subclass
of it. For instance, if you want to have a `PageSite` that only displays pages to everyone, but not allow editing:

``` python
from PageDisplay.sites import PageSite

class GeneralPageSite(PageSite):
    namespace = "general_pages"
    can_be_edited = False
    view_requires_login = False
```

The `namespace` attribute defines the namespace in the urls. More on this later.  
`can_be_edited` allows access to Page Editing or whether it is for displaying only.

To limit access you can set various settings:  
`[view/edit]_requires_login` is a boolean to limit access for logged in/non-logged in users  
`[view/edit]_requires_permissions` allows a _list_ of permissions that need to be valid for access
`use_overview` allows access to a listview of all Pages
> Note: In the future get_queryset() will be implemented for both the overview and the views created from standard
> ids. However, this is not yet implemented.

set `breadcrumb_trail_template` to a html template that calls the 'django_bootstrap_breadcrumbs' tags to set-up the
breadcrumb trail. This will automatically be pre-fixed before the local breadcrumb trail. For instance if your html
file defines:   
``Home / Control / Pages``   
The site will display:   
``Home / Control / Pages / Edit Page / Edit Module``   
when editing a module on a page.

With the `extends_template` you can define the template to extend. In order to extend the layout you need to have
a block called "body", as it needs to use the entire width of the screen to render the page_site. If left empty it will
default to a default layout. The block "nav-bar-options" is used to add additional options (currently only buttons) in
the navigation bar.  
The block "breadcrumbs" adds breadcrumbs through the 'django_bootstrap_breadcrumbs' module.

URL referencing
---------------
The `PageSite` architecture has been set up to allow insertion in various places in your url schema without throwing
errors. As a result you can add it to your root (as you would do with e.g. the admin) or further down the line.

Let's take an example for an online blog site where users can maintain a blog. You have a general page site for
generic pages about the site. And a personal_blog_site where you try to create a layout for your blog posts.

``` python
# your_project.urls.py

urlpatterns = [
    path('general/', general_page_site.urls),
    path('personal/blog/<slug:blog_slug>', personal_blog_site.urls),
]
```
>Note that the sites are _instances_ of the class and not the class themselves. Make sure you create your site objects.
``` python
from PageDisplay.sites import PageSite

class GeneralPageSite(PageSite):
    namespace = "general_pages"
    can_be_edited = False
    view_requires_login = False

general_page_site = GeneralPageSite()
    
class PersonalBlogPageSite(PageSite):
    namespace = "personal_blog_site"
    use_overview = False
    use_page_keys = False
personal_blog_site = PersonalBlogPageSite()
```
The `namespace` attribute defines the namespace in the urls. So to view the page you can simply do:

`` reverse('general_pages:view_page', page_id=4) ``  yields `` /general/4/ ``
`` reverse('personal_blog_site:view_page', page_id=7 blog_slug='my_blog') ``  yields `` /personal/blog/my_blog/2/ ``

##### Fixing local url links
In PageDisplay there are quite a few urls to adjust modules/ page settings etc. This however is not aware that,
in the case of the personal blog post, an additional keyword argument was given (blog_slug='my_blog'). Informing this
however is simple and done in two **static** methods:  
- init_view_params(view_obj, **kwargs)
- get_url_kwargs(view_obj)

By overwriting `init_view_params()` in your pagesite you can set certain parameters in the view object. This method
is triggered early at the start of the dispatch before anything else is taken. Even before any permission check
`get_url_kwargs(view_obj)` in turn is triggered during context_data creation and returns the keyword pairs needed
to revert an url. So in the case of personal_blog_site:
```
class PersonalBlogPageSite(PageSite):
    (...)
    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ Seeks the related objects from the keyword arguments """
        view_obj.blog = get_object_or_404(Blog, slug=kwargs['blog_slug'])
        super(PersonalBlogPageSite).init_view_params(view_obj, **kwargs)

    @staticmethod
    def get_url_kwargs(view_obj):
        """ Get the keyword args for reverting urls """
        kwargs = super(PersonalBlogPageSite).get_url_kwargs(view_obj)
        kwargs['blog_slug'] = view_obj.blog.slug
        return kwargs
```

Right now, there is still double information as both the Blog and the Page are referenced (assuming that a blog only
has a single Page). This can easily be solved by setting `use_page_keys = False` in the site
and adding `view_obj.page = view_obj.blog.page` in the `init_view_params` method

Advanced Access control
-----------------------

This still needs some work as the method is set up in the, I realise now, wrong place :)


Selecting modules to use
------------------------
Depending on the use, you may want to include and/or exclude certain modules to be able to be added.
This can be set with the `include_modules` and `exclude_modules` option. `include_modules` limits the modules that can be added
to only the modules set. This ignores any default set for the modules.
`ezclude_modules` removes modules from the default available modules


   





