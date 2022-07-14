"""
World module.
"""
from . import polity, terrain, period, default_parameters
from .community import Community, DIRECTIONS, LittoralNeighbour
from numpy import sqrt
from numpy.random import random, permutation
import yaml

#LEV
from .Leviathan import Paradigm, Agriculture
import random as rnd

_START_YEAR = -1500
_YEARS_PER_STEP = 2


class World(object):
    """
    World class, a container for all polities, communities and methods relating
    to them.

    Args:
        xdim (int): The x dimension of the world in communities.
        ydim (int): The y dimension of the world in communities.
        communities (list[Community]): The list of communities in the world.
            This is a one dimensional list. Communities are arranged by their
            coordinates in the list in a column-major fashion, _i.e._ [(0,0),
            (0,1), (0,2)].
        params (Parameters, default=guard.default_paramters): The simulation
            parameter set to use.

    Attributes:
        xdim (int): The x dimension of the world in communities.
        ydim (int): The y dimension of the world in communities.
        params (Parameters): The simulation parameter set.
        step_number (int): The current step number.
        tiles (list[Community]): A list of communities in the world.
        polities (list[Polity]): A list of polities in the world.
    """
    def __init__(self, xdim, ydim, communities, params=default_parameters):
        self.params = params

        self.xdim = xdim
        self.ydim = ydim
        self.total_tiles = xdim*ydim
        self.tiles = communities

        # Initialise neighbours and littoral neighbours
        self.set_neighbours()
        if params.sea_attacks:
            self.set_littoral_tiles()
            self.set_littoral_neighbours()

        # Each agricultural tile is its own polity, set step number to zero
        self.reset()
        
        #LEV TRACKING THAT SHOULD BE SOMEWHERE ELSE...
        self.polity_sizes = []

    def __str__(self):
        string = 'World:\n'
        string += '\t- Tiles: {0}\n'.format(self.total_tiles)
        string += '\t- Dimensions: {0}x{1}\n'.format(self.xdim, self.ydim)
        string += '\t- Number of polities: {0}'.format(
            self.number_of_polities())

        return string

    def number_of_polities(self):
        """
        Calculate the number of polities in the world.

        Returns:
            (int): The number of polities.
        """
        return len(self.polities)

    def index(self, x, y):
        """
        Return the tile at coordinates (x,y).

        Returns:
            (Community): The community at coordinate (x,y).
            (None): If there is no such tile.
        """
        if any([x < 0, x >= self.xdim, y < 0, y >= self.ydim]):
            return None
        return self.tiles[self._index(x, y)]

    def _index(self, x, y):
        """
        Return the position in the tiles list of the tile at coordinates
        (x,y).
        """
        return x + y*self.xdim

    def year(self):
        """
        Return the current year.

        Returns:
            (int): The current year. Years BC are negative.
        """
        return self.step_number*_YEARS_PER_STEP + _START_YEAR

    def sea_attack_distance(self):
        """
        Determine maximum sea attack distance at current step.

        Returns:
            (float): The maximum sea attack distance.
        """
        return (self.params.base_sea_attack_distance
                + self.step_number * self.params.sea_attack_increment)

    def set_neighbours(self):
        """
        Assign tiles their neighbours.
        """
        for x in range(self.xdim):
            for y in range(self.ydim):
                tile = self.index(x, y)
                tile.position = (x, y)
                tile.neighbours['left'] = self.index(x-1, y)
                tile.neighbours['right'] = self.index(x+1, y)
                tile.neighbours['up'] = self.index(x, y+1)
                tile.neighbours['down'] = self.index(x, y-1)

    def set_littoral_tiles(self):
        """
        Assign littoral tiles the littoral flag.
        """
        for tile in self.tiles:
            # Don't set littoral status for sea or desert tiles
            if not tile.terrain.polity_forming:
                continue

            for direction in DIRECTIONS:
                neighbour = tile.neighbours[direction]
                # Ensure there is a neighour
                if neighbour is None:
                    continue
                # Check if neighbour is a sea tile
                if neighbour.terrain is terrain.sea:
                    tile.littoral = True
                    # Break here as only one neighbour needs to be sea for tile
                    # to be littoral
                    break

    def set_littoral_neighbours(self):
        """
        Assign littoral tiles their lists of littoral neighbours.
        """
        littoral_tiles = [tile for tile in self.tiles if tile.littoral is True]
        n_littoral = len(littoral_tiles)

        for tile in littoral_tiles:
            # Add self as a littoral neighbour with 0 distance, this is
            # important in order to reproduce Turchin's results
            tile.littoral_neighbours.append(LittoralNeighbour(tile, 0))

        for i in range(n_littoral-1):
            itile = littoral_tiles[i]
            for j in range(i+1, n_littoral):
                jtile = littoral_tiles[j]

                # Calculate euclidean distance between tiles in tile dimension
                # units
                distance = sqrt((itile.position[0]-jtile.position[0])**2 +
                                (itile.position[1]-jtile.position[1])**2)

                # Add neighbour and the symmetric entry
                itile.littoral_neighbours.append(
                    LittoralNeighbour(jtile, distance))
                jtile.littoral_neighbours.append(
                    LittoralNeighbour(itile, distance))

    @classmethod
    def from_file(cls, yaml_file, params=default_parameters):
        """
        Read a world from a YAML file.

        Args:
            yaml_file (str): Path to the file containing a YAML definition of
                the world.
            params (Parameters, default=guard.default_paramters): The
                simulation parameter set.

        Returns:
            (World): The world object specified by the YAML file

        Raises:
            (MissingYamlKey): Raised if a required key is not present in the
                YAML file.
        """
        # Parse YAML file
        with open(yaml_file, 'r') as infile:
            world_data = yaml.load(infile, Loader=yaml.FullLoader)
        try:
            xdim = world_data['xdim']
        except KeyError:
            raise MissingYamlKey('xdim', yaml_file)
        try:
            ydim = world_data['ydim']
        except KeyError:
            raise MissingYamlKey('ydim', yaml_file)

        # Determine total number of tiles and assign list
        total_communities = xdim*ydim
        communities = [None]*total_communities

        # Enter world data into tiles list
        try:
            community_data = world_data['communities']
        except KeyError:
            raise MissingYamlKey('communities', yaml_file)
        for community in community_data:
            x, y = community['x'], community['y']

            assert community['terrain'] in ['agriculture', 'steppe',
                                            'desert', 'sea']
            if community['terrain'] == 'agriculture':
                landscape = terrain.agriculture
            elif community['terrain'] == 'steppe':
                landscape = terrain.steppe
            elif community['terrain'] == 'desert':
                landscape = terrain.desert
            elif community['terrain'] == 'sea':
                landscape = terrain.sea

            if landscape.polity_forming:
                elevation = community['elevation'] / 1000.
                agricultural_period = community['activeFrom']

                if agricultural_period == 'agri1':
                    active_from = period.agri1
                elif agricultural_period == 'agri2':
                    active_from = period.agri2
                elif agricultural_period == 'agri3':
                    active_from = period.agri3

                communities[x + y*xdim] = Community(params, landscape,
                                                    elevation, active_from)
            else:
                communities[x + y*xdim] = Community(params, landscape)

        return cls(xdim, ydim, communities, params)

    def reset(self):
        """
        Reset the world by returning all polities to single communities and
        setting the step number to 0.
        """
        self.step_number = 0
        
        #LEV Reset tiles (communities)--seems like these should have been reset before...
        # Otherwise ultrasociety and military techs carried over between tests
        for tile in self.tiles:
            tile.paradigm = Paradigm.Paradigm(tile)
            tile.icono.comfort = rnd.random()
            tile.agri = Agriculture.Agriculture(tile)
            tile.sea_attack_distance = 0
            
            tile.ultrasocietal_traits = [False]*self.params.n_ultrasocietal_traits
            if self.params.military_technology_seed == 'steppes':
                # Steppe communities start with all military technologies
                if tile.terrain == terrain.steppe:
                    tile.military_techs = [True]*self.params.n_military_techs
                else:
                    tile.military_techs = [False]*self.params.n_military_techs
            elif self.params.military_technology_seed == 'uniform':
                # 4.34% chance of starting with all military technologies In the
                # original simulation there are 115 steppes tiles out of 2647
                # polity supporting (steppe or agricultural) tiles making 4.34% of
                # the communities begining with all miliatry technologies
                if random() < 0.0434:
                    if tile.terrain in [terrain.steppe, terrain.agriculture]:
                        tile.military_techs = [True]*self.params.n_military_techs
                else:
                    tile.military_techs = [False]*self.params.n_military_techs
        
        self.polities = [polity.Polity([tile])
                         for tile in self.tiles]#if tile.terrain.polity_forming] #for display--should not be used anywhere but polity forming
        #TODO--change analysis so don't need to create polities on all tiles?
        

    def cultural_shift(self):
        """
        Attempt cultural shift in all communities.
        """
        for tile in self.tiles:
            if tile.terrain.polity_forming:
                tile.cultural_shift(self.params, self.step_number) #LEV added step number so can check if active

    def disintegration(self):
        """
        Attempt disintegration of all polities
        """
        new_states = []
        for state in self.polities:
            # Skip single community polities
            if state.size() == 1:
                continue
            if state.disintegrate_probability(self.params) > random():
                # Create a new set of polities, one for each of the communities
                
                #LEV--TRACKING FOR POWERLAWS
                self.polity_sizes.append(state.max_size)
                
                new_states += state.disintegrate()

        # Delete the now empy polities
        self.prune_empty_polities()

        # Append new polities from disintegrated old polities to list
        self.polities += new_states

    def attack(self, callback=None):
        """
        Attempt an attack from all communities.

        Args:
            callback (function, default=None): A callback function invoked if
                an attack is successful. Used to record attack events.
        """
        # Generate a random order for communities to attempt attacks in
        attack_order = permutation(self.total_tiles)
        for tile_no in attack_order:
            tile = self.tiles[tile_no]
            if tile.can_attack(self.step_number):
                tile.attempt_attack(self.params, self.step_number,
                                    self.sea_attack_distance(), callback)

        self.prune_empty_polities()

    def prune_empty_polities(self):
        """
        Prune polities with zero communities.
        """
        self.polities = [state for state in self.polities
                         if state.size() != 0]

    def step(self, attack_callback=None):
        """
        Conduct a simulation step

        Args:
            attack_callback (function, default=None): A callback function
                invoked if an attack is successful. Used to record attack
                events.
        """
        # Attacks
        self.attack(attack_callback)

        # Cultural shift
        self.cultural_shift()

        # Disintegration
        self.disintegration()

        # Increment step counter
        self.step_number += 1
        
        #LEV--POWER LAW TESTING OF POLITIES--SHOULD PROBABLY BE IN ANALYSIS INSTEAD?
        #CURRENTLY OUTPUTS MAX ON DISINTEGRATION AND AT END
        for polity in self.polities:
            if polity.max_size < len(polity.communities):
                polity.max_size = len(polity.communities)
    
    def end(self):
        for polity in self.polities:
            self.polity_sizes.append(polity.max_size)
        
        return self.polity_sizes
            


class MissingYamlKey(Exception):
    """
    Exception raised when a necessary key is missing from the world YAML file.
    """
    def __init__(self, key, filename):
        super().__init__(
            'Required key "{}" missing from the world definition'
            ' file "{}".'.format(key, filename)
            )
