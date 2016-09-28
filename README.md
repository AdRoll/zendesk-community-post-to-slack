# Zendesk Community Post To Slack Bot

This is a little tiny slack script that goes to Zendesk and sees if
there have been any new posts on a community topic.  If there have
been, it publishes them to slack and keeps track of all the ones it's
previously seen.

## Setup
To get this up and running edit
`fetch_posts_and_update_slack_for_unseen_ones.py` and setup the proper
constants for your application at the top of the file(s3 bucket, user
accounts, etc.).

You'll also need to alter the `s3keyring.ini` so it has the correct
s3keyring setup for you.  Otherwise, you'll have to hack the code
slightly to store the file locally.

Then you can either build a lambda package and set it up as a timed
event or you can set it up on a server as a cronjob somewhere.
