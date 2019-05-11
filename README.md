# ChatApp

## Installing Dependencies
>pip install opencv-python
>pip install flask 
>pip install flask-socketio
>pip install flask-mysql
>pip install PyQt5

## Setup Database
Create Database in MYSQL
Database: Work
Host: localhost ( Default)
Password: '' ( Empty String Default)
User: 'root' (Default)
1. Table: log
Column: Eventlog
2. Table: Users
Column: Username Password


## Running Server
Go to server folder.
Run command : python app.py

To run a separate window: python front.py
Or Open localhost:5000 on Browser window

## In Video-Streaming Demonstration Section

First, login or Signup on the website
Then, Go to path '/stream'
Type the number of the player:
Streaming of the video from the current session starts and is broadcasted to the '/stream' path.
