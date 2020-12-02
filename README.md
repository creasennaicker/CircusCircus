# CircusCircus
This is a minimal forum written in python with Flask. It supports only the bare minumum of features to allow discussions, including user accounts, threads, and comments.

On first run, the default subforums will be created. Although custom subforums are not supported through any user interface, it is possible to modify forum/setup.py to create custom subforums.

## Changes in 2020

I had to make a bunch of changes in this code to get it running. Took far longer than it should.
But now, if I have it right, you need to clone this and then

This currently puts a sqlite3 db in the /tmp directory.

```
$ python3.9 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ ./run.sh
```

and it should appear on port 5000

`http://0.0.0.0:5000`
