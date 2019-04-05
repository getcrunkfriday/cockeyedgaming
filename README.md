# cockeyedgaming
Repository for streaming tools used on twitch.tv/cockeyedgaming for duo-streaming chat bot, song request service, and viewer interaction utilities. Full stack app is written in Flask, though is under construction. 

## crunkybot/
Contains backend files for the CrunkyBot chatbot, including Twitch and Discord APIs, as well as live overlays for responding to chat activity.

### crunkybot/twitch
Required backend files for Twitch chatbot and distributed song request service (uses ices, icecast2, and sqlite for song requests and radio station). 

### crunkybot/discord
Required backend files for Discord chatbot. Allows song requests through Discord server; will eventually contain social data collection methods.
