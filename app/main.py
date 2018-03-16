import bottle
import os

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    print('game id: %s' % (game_id)) # For log purposes, to indicate which game log is showing.

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#00FF00',
        'taunt': 'A dog. Slitheratively speaking.',
        'head_url': head_url,
        'name': 'Dentis Kanasaw',
        'head_type': 'pixel',
        'tail_type': 'pixel',
    }


################################################################################

SYMBOL = {'snakehead': 's',
          'snakenemy': 'e', # enemies' heads
          'snakebody': 'b',
          'snaketail': 't',
          'food': 'f',
          'empty': '_',
         }

class Cell:
    def __init__(self, row, column):
        self.state = 'empty'
        self.safe = True
        self.snake_id = None
        self.coord = [row, column]

    def to_symbol(self):
        return(SYMBOL[self.state])


class Grid:
    def __init__(self, prepend):
        self.height = prepend['height']
        self.width = prepend['width']
        self.grid = [[Cell(row, col)
                       for col in range(self.width)]
                       for row in range(self.height)]

    def print(self):
        """Print grid
        """
        for row in self.grid:
            for cell in row:
                print(cell.to_symbol(), end=" ")
            print("")

    def cell_at(self, coord):
        y, x = coord
        return(self.grid[y][x])

    def set_at(self, coord, state, snake_id=None, safe=True):
        self.cell_at(coord).state = state
        self.cell_at(coord).snake_id = snake_id
        self.cell_at(coord).safe = safe

    def place_food(self, food_list):
        for food in food_list:
            self.set_at(food.coord, 'food')

    def place_enemy(self, enemy_list):
        for enemy in enemy_list:
            self.set_at(enemy.tail, 'snaketail', enemy.id, not
                    enemy.dist_nearest_food==1)
            for body in enemy.body:
                self.set_at(body, 'snakebody', enemy.id, False)
            self.set_at(enemy.head, 'snakenemy', enemy.id, False)

            if enemy.longer_than_me is True:
                for i in range(-1,2):
                    if 0 <= enemy.head[0]+i < self.height:
                        self.grid[enemy.head[0]+i][enemy.head[1]].safe = False
                    if 0 <= enemy.head[1]+i < self.width:
                        self.grid[enemy.head[0]][enemy.head[1]+i].safe = False

    def place_me(self, me):
        self.set_at(me.head, 'snakehead', me.id)
        self.set_at(me.tail, 'snaketail', me.id, not me.dist_nearest_food==1)
        for body in me.body:
            self.set_at(body, 'snakebody', me.id, False)


class Food:
    def __init__(self, prepend):
        self.coord = [prepend['y'], prepend['x']]


class Snake:
    def __init__(self, prepend, food_list):
        self.head = [prepend['body']['data'][0]['y'],
                     prepend['body']['data'][0]['x']]
        self.tail = [prepend['body']['data'][-1]['y'],
                     prepend['body']['data'][-1]['x']]
        self.body = [[prepend['body']['data'][j]['y'],
                      prepend['body']['data'][j]['x']]
                      for j in range(1, len(prepend['body']['data'])-1)]
        self.length = prepend['length']
        self.id = prepend['id']
        self.nearest_food = nearest(self, food_list)
        self.dist_nearest_food = distance(self, self.nearest_food.coord)

class Enemy(Snake):
    def __init__(self, prepend, me, food_list):
        super().__init__(prepend, food_list)
        self.longer_than_me = self.length >= me.length

class Me(Snake):
    def __init__(self, prepend, food_list):
        super().__init__(prepend, food_list)
        self.health = prepend['health']


################################################################################

def nearest(snake, obj_list):
    return(sorted(obj_list, key=lambda obj: distance(snake, obj.coord))[0])

def distance(snake, to):
    total = abs(snake.head[0] - to[0]) + abs(snake.head[1] - to[1])
    return(total)

def path(me, to):
    """ Creates a list of directions to a destination
    """
    directions = []

    if me.head[0] < to[0]:
        directions.append('down')
    elif me.head[0] > to[0]:
        directions.append('up')

    if me.head[1] < to[1]:
        directions.append('right')
    elif me.head[1] > to[1]:
        directions.append('left')

    return(directions)

def set_goal(me):
    if me.health <= 30:
        log = 'food'
    log = 'floodfill'
    return(log)


'''
def set_goal(me, enemy_list, grid):
    if me.health <= 30:
        goal = me.nearest_food.coord
        log = "food"
    else:
        goal = target_tail(enemy_list, me, grid)
        log = "tail"

    return(goal, log)
'''

def safe_directions(me, enemy_list, grid):
    """Creates two lists of safe directions based on two separate criteria.
    Safe contains directions where next space is safe whereas backup contains
    directions where next space does not contain snake head, body, or tail if
    head is one step from food.
    """
    directions = {
            'up': [me.head[0]-1, me.head[1]],
            'down': [me.head[0]+1, me.head[1]],
            'left': [me.head[0], me.head[1]-1],
            'right': [me.head[0], me.head[1]+1],
            }

    space = []
    backup_space = []

    for key in directions:
        if (0 <= directions[key][0] < grid.height and
                0 <= directions[key][1] < grid.width and
                grid.cell_at(directions[key]).safe is True):
            space.append(key)

    for key in directions:
        if (0 <= directions[key][0] < grid.height and
                0 <= directions[key][1] < grid.width and
                grid.cell_at(directions[key]).state not in
                        ['snakenemy', 'snakebody']):
            if (grid.cell_at(directions[key]).state is 'snaketail' and
                    grid.cell_at(directions[key]).safe is True):
                # place_me and place_enemy already set tail to not be safe if
                # dist_nearest_food is 1
                backup_space.append(key)
            else:
                backup_space.append(key)

    return(space, backup_space)





'''
def target_tail(me, enemy_list, grid):
    target = nearest(me, enemy_list)

    if target.length > 3:
        segment = -2 if target.tail is target.body[1] else -1

        output = [target.tail]

        if target.tail[0] is target.body[segment][0]:
            if target.tail[1] < target.body[segment][1]:
                for i in range(-1, -3, -1):
                    if (target.tail[1]+i >= 0 and
                            grid.grid[target.tail[0]][target.tail[1]+i].\
                            safe is True):
                        output.append((target.tail[0], target.tail[1]+i))

            elif target.tail[1] > target.body[segment][1]:
                for i in range(-1, -3, -1):
                    if (target.tail[1]-i < agrid.width and
                            grid.grid[target.tail[0]][target.tail[1]-i].\
                            safe is True):
                        output.append((target.tail[0], target.tail[1]-i))

        elif target.tail[1] is target.body[segment][1]:
            if target.tail[0] < target.body[segment][0]:
                for i in range(-1, -3, -1):
                    if (target.tail[0]+i >= 0 and
                            grid.grid[target.tail[0]+i][target.tail[1]].\
                            safe is True):
                        output.append((target.tail[0]+i, target.tail[1]))

            elif target.tail[0] > target.body[segment][0]:
                for i in range(-1, -3, -1):
                    if (target.tail[0]-i < agrid.height and
                            grid.grid[target.tail[0]-i][target.tail[1]].\
                            safe is True):
                        output.append((target.tail[0]-i, target.tail[1]))

        return(output[-1])
'''
## Floodfill materials ##

def check(direction, y, x, grid):
    """ Counts empty spaces until it hits an enemy head or bodies.
    given a specific direction.
    """
    change = {'up': [-1, 0],
              'down': [1, 0],
              'left': [0, -1],
              'right': [0, 1]}

    y += change[direction][0]
    x += change[direction][1]

    count = 0
    while(0 <= y < grid.height and 0 <= x < grid.width and
              grid.cell_at((y, x)).state not in ['snakenemy', 'snakebody']):
        count += 1
        y += change[direction][0]
        x += change[direction][1]

    return(count)

def floodfill(key, me, grid):
    """ Count empty spaces of a direction and the perpendicular
    using the check function.
    """
    y = me.head[0]
    x = me.head[1]

    direction_parameter = {'vertical': ['left', 'right'],
                           'horizontal': ['up', 'down']}
    parameter = {'up': -1, 'down': 1,
                 'left': -1, 'right': 1}

    sum = 0

    if key is 'up' or key is 'down':
        size = check(key, y, x, grid)
        sum += size
        for dir in direction_parameter['vertical']:
            for i in range(1, size+1):
                sum += check(dir, y+(i*parameter[key]), x, grid)

    if key is 'left' or key is 'right':
        size = check(key, y, x, grid)
        sum += size
        for dir in direction_parameter['horizontal']:
            for i in range(1, size+1):
                sum += check(dir, y, x+(i*parameter[key]), grid)

    return(sum)

def reorder_by_floodfill(me, direction_list, grid):
    """ Reorder a list of directions
    (space and backup space) based on floodfill spaces.
    """
    return(sorted([direction for direction in direction_list],
                  key=lambda direction: floodfill(direction, me, grid),
                  reverse=True))

## Route setter ##

def set_output(me, enemy_list, grid, data):
    safety, backup_safety = safe_directions(me, enemy_list, grid)
    safe_flooded = reorder_by_floodfill(me, safety, grid)
    backup_safe_flooded = reorder_by_floodfill(me, backup_safety, grid)
    output_log = set_goal(me)
    food_route = path(me, me.nearest_food.coord)
    route_flooded = reorder_by_floodfill(me, food_route, grid)
    print('Floodfill Up: %s' % (floodfill('up', me, grid)))
    print('Floodfill Down: %s' % (floodfill('down', me, grid)))
    print('Floodfill Left: %s' % (floodfill('left', me, grid)))
    print('Floodfill Right: %s' % (floodfill('right', me, grid)))
    print('Health: %s' % (me.health))
    print('Currently targeting: %s' % output_log)
    print("Turn: %s" % (data['turn']))
    print('Flooded food route: %s' % (route_flooded))
    print('Safety: %s' % (safety))
    print('Flood Safe: %s' % (safe_flooded))
    print('Backup: %s' % (backup_safety))
    print('Flood backup: %s' % (backup_safe_flooded))
    print('Nearest food is: %s' % (me.nearest_food.coord))
    for direction in safe_flooded:
        if output_log is 'food':
            if direction in route_flooded:
                return(direction)
        else:
                return(safe_flooded[0])
    else:
        return(backup_safe_flooded[0])


###############################################################################

class Game:
    def __init__(self, data):
        self.grid = Grid(data)

        self.food_list = [Food(foods) for foods in data['food']['data']]
        self.grid.place_food(self.food_list)

        self.me = Me(data['you'], self.food_list)
        self.grid.place_me(self.me)

        self.enemies = [Enemy(enemy, self.me, self.food_list)
               for enemy in data['snakes']['data']
               if enemy['id'] != self.me.id]
        self.grid.place_enemy(self.enemies)

        self.grid.print()

@bottle.post('/move')
def move():
    # Initialise board and stuff on board
    data = bottle.request.json
    game = Game(data)
    output = set_output(game.me, game.enemies, game.grid, data)

    return {
        'move': output,
        'taunt': 'A dog. Slitheratively speaking.'
    }

'''
    me = Me(data['you'], foods)

    enemies = [Enemy(data['snakes']['data'][i], me, foods)
               for i in range(len(data['snakes']['data']))
               if data['snakes']['data'][i]['id'] != me.id]

    # Grid for log purposes
    grid.food_place(foods)
    for enemoir in enemies: grid.enemy_place(enemoir)
    grid.me_place(me)
    grid.print()

    # Route setter
    safety, backup_safety = safe(grid, me, enemies, data)
    flooding_safe = floodfill_reorder(safety, me, grid)
    flooding_backup = floodfill_reorder(backup_safety, me, grid)
    goal, output_log = goal_set(me, enemies, grid)
    route = path(me, goal, grid)
    flooding_route = floodfill_reorder(route, me, grid)

    output = None
    if flooding_safe: #If safety is not empty
        for item in flooding_safe:
            if output_log == 'food':
                if item in flooding_route:
                    output = item
            elif output_log == 'tail':
                output = flooding_safe[0]
        if output == None:
            output = flooding_safe[0]
    else:
        output = flooding_backup[0]

    target_practice = target_tail(enemies, me, grid)


    # Info for current turn, for log purposes
    print('Floodfill Up: %s' % (floodfill('up', me, grid)))
    print('Floodfill Down: %s' % (floodfill('down', me, grid)))
    print('Floodfill Left: %s' % (floodfill('left', me, grid)))
    print('Floodfill Right: %s' % (floodfill('right', me, grid)))
    print('Health: %s' % (me.health))
    print('Currently targeting: %s' % output_log)
    print("Turn: %s" % (data['turn']))
    print('Route: %s' % (route))
    print('Flood route: %s' % (flooding_route))
    print('Safety: %s' % (safety))
    print('Flood Safe: %s' % (flooding_safe))
    print('Backup: %s' % (backup_safety))
    print('Flood backup: %s' % (flooding_backup))
    print('Target tail is: %s' % (target_practice))
    print('Target food is: %s' % (me.nearest_food.coord))
    print('Goal is: %s' % (goal))
    print('output: %s' % (output))
'''



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
