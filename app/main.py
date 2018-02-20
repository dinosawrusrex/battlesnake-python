import bottle
import os
import random

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#00FF00',
        'taunt': 'hissss...sss',
        'head_url': head_url,
        'name': 'our-snake',
        'head_type': 'pixel',
        'tail_type': 'pixel',
    }


##############

class Cell:
    def __init__(self):
        self.is_it = {'snakehead': False, 'snakebody': False, 'food': False}
        self.symbol = {'snakehead': 's', 'snakebody': 'b', 'food': 'f', 'cell': '_'}
    
    def to_symbol(self):
        if self.is_it['snakehead'] == True:
            return(self.symbol['snakehead'])
        elif self.is_it['food'] == True:
            return(self.symbol['food'])
        elif self.is_it['snakebody'] == True:
            return(self.symbol['snakebody'])
        else:
            return(self.symbol['cell'])

class Grid:
    def __init__(self, prepend):
        self.coord = [[Cell() for col in range(prepend['width'])] for row in range(prepend['height'])]

    def print(self):
        for row in self.coord:
            for cell in row:
                print(cell.to_symbol(), end=" ")
            print("")

    def placer(self, coordinates, obj, status=False):
        self.coord[coordinates[0]][coordinates[1]].is_it[obj] = status
        

class Food:
    def __init__(self, prepend):
        self.coord = [prepend['y'], prepend['x']]

class Snake:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][i]['y'], prepend['body']['data'][i]['x']] for i in range(len(prepend['body']['data']))]
        self.length = prepend['length']
        # distance to food
        # distance to me


#########

@bottle.post('/move')
def move():
    data = bottle.request.json

    directions = ['up', 'down', 'left', 'right']
    
    grid = Grid(data)
    food = [Food(data['food']['data'][i]) for i in range(len(data['food']['data']))]
    snakes = [Snake(data['snakes']['data'][i]) for i in range(len(data['snakes']['data']))]

    grid.placer(food[0].coord, 'food', True)
    grid.print()
'''
    return {
        'move': random.choice(directions),
        'taunt': 'python!'
    }
'''

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
