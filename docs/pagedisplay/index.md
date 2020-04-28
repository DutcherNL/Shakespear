PageDisplay
========

The Page Display module is a core module that supports user-ended creation of visual pages.
These pages are created from entries in the database and are thus flexible and adjustable during deployment.

Pages created can be, with the use of other modules, be used to:

- Construct general information pages (e.g. about us, contact, privacy regulations...)
- Construct e-mail layouts
- Construct layouts for reports

Architecture
------------

#### Page Rendering
There is a bridge between the model classes and the classes that control the way the contents in those classes
are rendered. The `Page` and `Module` classes are derivatives of `django Model` class and contain the data the user
defined. The `renderer` and `widget` classes control the way they are rendered respectively.

The relation between a `Module` and a `Widget` is similar to a `django Field` and its `Widget`. The widget renders
the content of the Module.    
A `Module` can contain/nest other Modules.

Because a `Page` is more of a broader scope, it's functionality is as a result also a bit more broad. Similarly how a
type of book (novel, cook-book, self-help book) defines the way all pages are displayed a `Page` can define how all
modules are displayed. This is done by selecting `Renderer` in the `Page` class (although this can be overwritten in
the `.render()` method). In the `Renderer` one can assign different `Widgets` to the `Modules` instead of their default
ones.


#### The PageSite

The `PageSite` allows users to add/change and remove modules on the pages. It can filter on who has what access as well
as which Pages can be viewed / edited. Internal URL's have been set up in such a way that the site can be inserted into
any point in your urls without conflicts. E.g. Urls such as:
- `path('/', my_page_site.urls)`
- `path('/show_me/', my_page_site.urls)`
- `path('/<slug:some_object_slug>/', page_site.urls)`
- `path('/<int:some_alue>/<slug:some_object_slug>/', page_site.urls)`

This results in functionality where you can limit the editable Pages to the one referenced in 'some_object'


Documentation
-------------

#### Usage
[Page Site Control](./page_site_control.md)

#### Development
TODO

Installation
------------

This is currently not stand-alone so clear installations are not possible yet.


Wishlist
---------


- [] Module unremovable options
- [] ContainerModule insertion/deletion
- [] Improved Access Control






