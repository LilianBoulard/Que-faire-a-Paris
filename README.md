# Que-faire-a-Paris
Repository for our NoSQL university project.

## Technical information

This project uses a NoSQL database to get the ParisOpenData `que-faire-a-paris-` dataset.  
Source: https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/information/

Note: due to privacy concerns, the server's address is not hard-coded, but referenced by the environment variable `QFAP_SERVER`.

It uses Flask for the front-end, which uses another environment variable named `QFAP_SECRET`.

## Requirements

In order to launch the project, you will need Python >= 3.6.

You will also need to install the dependencies with

    pip install -r requirements.txt

**It is strongly advised to use a virtual environment.**

Next, add `QFAP_SERVER` and `QFAP_SECRET` to your environment.

On Windows (10):

    setx QFAP_SERVER "server_address"
    setx QFAP_SECRET "secret"

On Linux (e.g Ubuntu):

Modify your `~/.bashrc` or `~/.bash_profile`, by adding

    export QFAP_SERVER="server_address"
    export QFAP_SECRET="secret"

Note: on both, you need to reboot your IDE / CLI afterwards

## Build

Use 

    git clone https://github.com/Phaide/Que-faire-a-Paris

To copy the sources on your computer.
