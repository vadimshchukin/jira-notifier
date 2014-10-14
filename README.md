jira-notifier
=========

jira-notifier is an Ubuntu notification application for a JIRA bug tracker.

  - Performs JIRA authorization.
  - Gets activity streams in Atom format and parses it.
  - Gets issue lists by input JQL queries and creates an indicator applet with menu of issues.

In order to use it you should specify:
  - -l option. It's a JIRA bug tracker URL.
  - -u option. JIRA username.
  - -p option. JIRA password.
  - -k option. List of project keys separated by comma.
  - -q option. Input JQL queries file. One line corresponds to one query.
  - -i option. Timer interval in seconds.

Example:
```sh
jira-notifier.py -l'https://www.bugtracker.net' -u'username' -p'password' -k'KEY1,KEY2' -q'queries.jql' -i60
```

Application tries to log in JIRA using your credentials, then gets an activity stream feed for each project key every -i seconds - you'll be notified of new activity events through standard Ubuntu NotifyOSD notifications (notification will contain event's author's avatar image, title and summary). Simultaneously application gets an issue list executing JQL queries and shows that list in an indicator menu with links that are leading you to an issue tracker page.

Packages
-----------

jira-notifier depends on the following commonly used python packages:

* [gtk] - GTK bindings.
* [gobject] - GObject library.
* [appindicator] - GNOME indicators.
* [pynotify] - Ubuntu NotifyOSD.
* [feedparser] - Atom feed parser.
* [pyquery] - jQuery-like library for Python.

[gtk]:http://www.pygtk.org/
[gobject]:https://pypi.python.org/pypi/PyGObject/
[appindicator]:http://developer.ubuntu.com/api/devel/ubuntu-12.04/c/appindicator/
[pynotify]:http://www.galago-project.org/news/index.php
[feedparser]:https://pypi.python.org/pypi/feedparser
[pyquery]:https://pypi.python.org/pypi/pyquery
