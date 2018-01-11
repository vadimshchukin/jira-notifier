# jira-notifier
## Overview
jira-notifier is a Linux desktop notifier for the [JIRA issue tracker].

The scripts logs into JIRA with your credentials, then fetches an activity stream feed for each project key specified every -i seconds - you'll be notified of new activity events through standard [NotifyOSD] notifications (the notification will contain event's author's avatar image, title and summary). Simultaneously the script fetches an issue list executing [JQL] queries and shows that list in an indicator menu with links leading to the issue's page in JIRA.
## Features
  - Fetches activity streams and shows desktop notifications for new events.
  - Fetches issue lists using JQL queries and shows them in an indicator menu.

## Command line arguments
  - -j option. It's a JIRA issue tracker URL.
  - -u option. JIRA username. Optional parameter.
  - -p option. JIRA password. Optional parameter.
  - -k option. List of project keys separated by comma.
  - -q option. JQL issue queries file. One line corresponds to one query.
  - -i option. Timer interval in seconds. The default value is 60.
  - -a option. JIRA avatars directory name. The default is jira-avatars.
  - -c option. Indicator icon file name. The default is jira-notifier.png.

## Examples
Example:
```sh
trackerURL='https://jira.atlassian.com'
username='' # optional
password='' # optional
projectKeys='JRA,CONF,STASH'
queriesFile='jira-notifier.jql'
updateInterval=60
avatars='jira-avatars'
icon='jira-notifier.png'
logFile='jira-notifier.txt'

cd `dirname "$0"`
./jira-notifier.py >"$logFile" \
    -j"$trackerURL" \
    -k"$projectKeys" -q"$queriesFile" -i"$updateInterval" \
    -a"$avatars" -c"$icon"
# uncomment the next line in order to use authorization
#    -u"$username" -p"$password"
```

## Dependencies
jira-notifier depends on the following Python packages:

 - [gtk] - GTK bindings.
 - [gobject] - GObject library.
 - [appindicator] - GNOME indicators.
 - [pynotify] - Ubuntu NotifyOSD.
 - [feedparser] - Atom feed parser.
 - [pyquery] - jQuery-like library for Python.

[JIRA issue tracker]:https://www.atlassian.com/software/jira
[NotifyOSD]:https://wiki.ubuntu.com/NotifyOSD
[JQL]:https://confluence.atlassian.com/jirasoftwarecloud/advanced-searching-764478330.html
[gtk]:http://www.pygtk.org/
[gobject]:https://pypi.python.org/pypi/PyGObject/
[appindicator]:http://developer.ubuntu.com/api/devel/ubuntu-12.04/c/appindicator/
[pynotify]:http://www.galago-project.org/news/index.php
[feedparser]:https://pypi.python.org/pypi/feedparser
[pyquery]:https://pypi.python.org/pypi/pyquery
