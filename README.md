jira-notifier
=========

jira-notifier is a notification application for a JIRA bug tracker for Ubuntu.

  - JIRA authorization
  - Activity streams Atom feed parsing
  - Indicator applet with menu of issues

In order to use it you should specify:
  - -l option. It's a JIRA bug tracker URL.
  - -u option. JIRA username.
  - -p option. JIRA password.
  - -k option. List of project keys separated by comma.
  - -q option. Input JQL queries file. One line of this file should contain one query.

Example:
```sh
jira-notifier.py -l'https://www.bugtracker.net' -u'username' -p'password' -k'KEY1,KEY2' -qqueries.jql >log.txt
```

Firstly application tries to log in JIRA using your credentials, after that it'll try to get activity stream feed for each project key every minute - you'll be notified of new activity events using standard Ubuntu NotifyOSD (application tries to load user avatars in 'avatars' directory). Simultaneously applications tries to get an issue list from JQL query and show it in an indicator menu with links leading you to an issue tracker page.

Version
----

0.1

Tech
-----------

jira-notifier depends on the following commonly used python packages:

* [gtk] - GTK bindings
* [gobject] - GObject library
* [appindicator] - great UI boilerplate for modern web apps
* [pynotify] - evented I/O for the backend
* [feedparser] - fast node.js network app framework [@tjholowaychuk]
* [pyquery] - awesome keyboard handler lib by [@thomasfuchs]

License
----

GNU GPL 2


**Free Software, Hell Yeah!**

[gtk]:http://www.pygtk.org/
[gobject]:https://pypi.python.org/pypi/PyGObject/
[appindicator]:http://developer.ubuntu.com/api/devel/ubuntu-12.04/c/appindicator/
[pynotify]:http://www.galago-project.org/news/index.php
[feedparser]:https://pypi.python.org/pypi/feedparser
[pyquery]:https://pypi.python.org/pypi/pyquery
