#!/usr/bin/python

import requests # for all API requests
import json # for reading API request responses

# setting the initial token URL and base URLs for our GET and POST requests
SESSION_URL = "http://ec2-34-216-8-43.us-west-2.compute.amazonaws.com/session"
POST_BASEURL = "http://ec2-34-216-8-43.us-west-2.compute.amazonaws.com/game?token="
GET_BASEURL = "http://ec2-34-216-8-43.us-west-2.compute.amazonaws.com/game?token="

# use UID as payload for the session POST request
payload = {"uid": "404925279"}
headers = {"content-type": "application/x-www-form-urlencoded"}
res_session = requests.post(SESSION_URL, payload, headers)
# parse the response to find that the "token" field contains our access token
ACCESS_TOKEN = json.loads(res_session.text)["token"]

# setting up the directions we can travel
directions = ["LEFT", "RIGHT", "UP", "DOWN"]
# making sure we have a way to figure which direction to travel in
# while backtracking
def backtracked(d):
    if d == directions[0]:
        return directions[1]
    elif d == directions[1]:
        return directions[0]
    elif d == directions[2]:
        return directions[3]
    elif d == directions[3]:
        return directions[2]

# return the current location at the beginning of every maze,
# otherwise known as the starting location
def getStartingLocation():
    res_get = requests.get(GET_BASEURL + ACCESS_TOKEN, headers)
    startinglocation = json.loads(res_get.text)["current_location"]
    return startinglocation[0], startinglocation[1]

# return the dimensions of the current maze
def getDimensions():
    res_get = requests.get(GET_BASEURL + ACCESS_TOKEN, headers)
    return json.loads(res_get.text)["maze_size"]

# return the status of the game at the end of solveLevel's execution
# so that we can track and if we failed or succeeded
def getStatus():
    res_get = requests.get(GET_BASEURL + ACCESS_TOKEN, headers)
    return json.loads(res_get.text)["status"]

# return the number of total levels
def getN_Levels():
    res_get = requests.get(GET_BASEURL + ACCESS_TOKEN, headers)
    return json.loads(res_get.text)["total_levels"]

# used for scooching the x and y one direction in location
def shiftLocation(x, y, direction):
    # move to the previous index in the current row
    if direction == "LEFT":
        return x - 1, y
    # move to the next index in the current row
    elif direction == "RIGHT":
        return x + 1, y
    # move to the previous horizontal list
    elif direction == "UP":
        return x, y - 1
    # move to next horizontal list
    elif direction == "DOWN":
        return x, y + 1

# Perform an action and return the result of the move
def postMove(direction):
    payload = {'action': direction}
    res_post = requests.post(POST_BASEURL + ACCESS_TOKEN, payload, headers)
    return json.loads(res_post.text)["result"]

def canMove(x, y, xdim, ydim, breadcrumbs):
    # first check if the passed-in coordinate is in bounds
    if x > -1 and x < xdim and y > -1 and y < ydim:
        # now check if it's 'O' for OPEN
        if breadcrumbs[x][y] == 'O':
            return True
        return False
    return False

# Solve a level of the maze using recursion
def levelSolved(x, y):
    if breadcrumbs[x][y] == 'O':
        breadcrumbs[x][y] = 'V'
        for d in directions:
            # setting up a new set of coordinates that represent the next move
            new_x, new_y = shiftLocation(x, y, d)
            # checking that we're in bounds
            if canMove(new_x, new_y, dim_x, dim_y, breadcrumbs):
                # POST the move and then analyze the response
                res_move = postMove(d)
                if res_move == "OUT_OF_BOUNDS" or res_move == "WALL":
                    # if we hit a wall or some other situation, mark it down
                    # as something other than 'O'
                    breadcrumbs[new_x][new_y] = 'W'
                # if we're at the goal location, return True so the preceding
                # recursive calls know it's eventually successful
                if res_move == "END":
                    return True
                if res_move == "SUCCESS":
                    # if the next move is True, keep cascading the value back to the previous
                    # recursive function calls
                    if levelSolved(new_x, new_y):
                        return True
                    else:
                        postMove(backtracked(d)) # move in the backtracked direction
        return False
    return False

status = getStatus()
# print(status) # debug
dimensions = getDimensions()
dim_x = dimensions[0]
dim_y = dimensions[1]
n_levels = getN_Levels()
level_num = 1

# execute this loop exactly n_levels times
while status != "FINISHED":
    breadcrumbs = [['O' for i in range(dim_y)] for j in range(dim_x)]
    start_x, start_y = getStartingLocation()
    res = levelSolved(start_x, start_y)
    # print(res) # debug
    dimensions = getDimensions()
    # edge case for the end of all the levels
    if dimensions is not None:
        dim_x = dimensions[0]
        dim_y = dimensions[1]
    status = getStatus()
    print("level " + str(level_num) + " successful")
    level_num += 1

if status == "FINISHED":
    print("0") # get it lmao
elif status == "GAME_OVER" or status == "NONE":
    print("1")
