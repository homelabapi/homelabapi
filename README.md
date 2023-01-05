HomelabAPI
----------
Project Home: <https://homelabapi.org>  
Project Demo: <https://demo.homelabapi.org>  
Source Code: <https://homelabapi.org/source/>

What is HomelabAPI?
-------------------
HomelabAPI is a self-hosted API that you can use to consolidate all of your homelab notifications and other outputs. This allows you to use HomelabAPI as your central input/output hub, and if you ever want to change where your homelab outputs go, it's just a matter of updating your HomelabAPI configuration.

For example, let's say that you have all of your Home Assistant, Synology, and Tailscale notifications routed through HomelabAPI, and you have HomelabAPI configured to send all notifications to Pushover. Now let's say that you want to move your notifications from Pushover to Telegram. Instead of having to go into each of your homelab services and reconfigure where notifications get sent, all you have to do is update HomelabAPI to send to Telegram instead of Pushover, and that's it. One single update and you're done!

If you don't have many outputs being sent from your homelab, HomelabAPI may not be for you. However, if you're like me and have dozens of homelab outputs, you may want to give it a try. Plus it's another service to host in your homelab, how great is that?

Demo
----
Due to the nature of HomelabAPI, a fully functional demo is a bit tricky, however I do have a copy installed on the below URL so that people can check the system out and look through the API documentation.

<https://demo.homelabapi.org>

[![HomelabAPI](https://raw.githubusercontent.com/homelabapi/homelabapi/main/screenshot.png)](https://raw.githubusercontent.com/homelabapi/homelabapi/main/screenshot.png)

Supported Inputs
----------------
Headphones, HealthChecks, Home Assistant, LazyLibrarian, Radarr, Monit, SmokePing, Sonarr, Synology, Tailscale, UptimeRobot, Any POST Webhook that allows you to specify a request body

Supported Outputs
-----------------
Email, Pushbullet, Pushover, Telegram, Any POST Webhook

Installation
------------
Getting HomelabAPI up-and-running is as easy as cloning a git repository, updating a configuration file (see below), and starting a docker container.

    git clone https://github.com/homelabapi/homelabapi.git
    cd homelabapi
    (configure HomelabAPI here, see below)
    docker-compose up
    Open HomelabAPI in a web browser and you'll be presented with the full API documentation

Configuration
-------------
- Copy the docker-compose.yml.sample file to docker-compose.yml and update it accordingly
- Copy the config.yaml.sample file to config.yaml and update it accordingly
  - In the "application" section, you need to specify a completely random string of text for the "api_key" variable. This is the API key you'll use to connect to HomelabAPI.
- You can send to multiple outputs by modifying the "current_outputs" variable. Separate multiple outputs by commas, or use "all" to send to every configured output.
- Certain services require a script to run in order to send information to HomelabAPI, such as Monit and SmokePing. Some fully functional example scripts can be found in the "helper_scripts" folder. 

Contributing
------------
Please see CONTRIBUTING.md for our contributing guidelines.

Support
-------
If you have any questions, comments, or bugs to report, please visit <http://homelabapi.org>.

Changelog
---------
Please see the CHANGELOG file that came with HomelabAPI.

License
-------
Copyright (c) 2023 Greg Chetcuti <greg@chetcuti.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
