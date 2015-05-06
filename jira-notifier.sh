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
