cd `dirname $0`
./jira-notifier.py -l'https://www.jira.net' -u'username' -p'password' -k'KEY1,KEY2' -qqueries.jql >log.txt