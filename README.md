# Siptrack

Siptrack is the client library and stconnect utility for Siptrack. To make documentation easier all docs are found in the [siptrackweb repo](https://github.com/sii/siptrackweb).

# Quickstart

This shortly describes using the client against an existing siptrackd API backend at localhost:9242 without ssl.

    $ git clone https://github.com/sii/siptrack
    $ cd siptrack
    $ virtualenv .venv
    $ source .venv/bin/activate
    (.venv) $ python setup.py install
    (.venv) $ cp docs/sample-siptrack-rc.conf ~/.siptrackrc
    (.venv) $ siptrack ping           
    Password for admin@localhost:      
    Server said: 1516133721.83         

That means it's alive and you can try another command.