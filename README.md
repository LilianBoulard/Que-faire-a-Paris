# Que-faire-a-Paris
Repository for our NoSQL university project.

## Technical information

This project uses a NoSQL database to get the ParisOpenData `que-faire-a-paris-` dataset.  
Source: https://opendata.paris.fr/explore/dataset/que-faire-a-paris-/information/

Note: due to privacy concerns, the server's address is not hard-coded, but referenced by the environment variable `QFAP_SERVER`.

It uses Flask for the front-end, which uses another environment variable named `QFAP_SECRET`.

## Build

Use 

    git clone https://github.com/Phaide/Que-faire-a-Paris

To copy the sources on your computer.

In order to launch the project, you will need to install the dependencies with

    pip install -r requirements.txt
    
**It is strongly advised to use a virtual environment.**
