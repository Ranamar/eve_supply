eve_supply - A python script to help track your market supplies
===============================================================

Usage
-----
In order to get things working, you need to install evelink (see dependencies) and edit your API key, vcode, and character name into eve_supply.py
Be careful if you decide to submit a pull request to remove them!  My first checkin had an API I had to revoke as a result.

While it can be run in a basic sense on a command line, I usually run it in an interactive Python session.
This allows me to use some of the other utility functions, generally to decide what I should be doing if I discover I either have extra market orders or need to free up an order or two for more important stuff.

Dependencies
------------
Requires the [evelink](https://github.com/eve-val/evelink) library to function.
