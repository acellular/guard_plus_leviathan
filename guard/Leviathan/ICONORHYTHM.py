import random as rnd
from .. import terrain
from numpy.random import random, randint

#paradigm shifts via comfort and expectations
class ICONORHYTHM:

    def __init__(self, community):
        self.community = community
        self.comfort = rnd.random()
        self.counterParadigms = []

    def Run(self):
        
        #if simple contagion paradigm spread
        if self.community.params.contagion is not None:
            #only checking if meeting ultrasociety needs
            self.comfort = (self.community.agri.yields-sum(self.community.ultrasocietal_traits)) / 10
            self.contagion_response()
            return
        
        # update comfort
        self.UpdateComfort()

        # then using comfort, continue with status quo, mitigate, copy or mutate?
        self.Response()

    def UpdateComfort(self):  

        # are yields getting better?
        gettingBetter = self.community.agri.yields - self.community.agri.yields_prev

        # how do expectations and reality compare? (including saved surplusses)
        expectsVsReal = ((self.community.agri.yields + self.community.paradigm.expectations)
            / self.community.paradigm.expectations) - 2
        
        # are yields high enough to support societal level?
        #TODO PARAMERETIZE BOTH SO MATCH NUM ULTRA TO NUM YEILDS
        meetingNeeds = self.community.agri.yields - sum(self.community.ultrasocietal_traits) - 1 

        # add thus
        howAreThingsGoing = ((expectsVsReal + gettingBetter  + meetingNeeds)
                                * self.community.paradigm.sensitivity)

        self.AdjustComfort(howAreThingsGoing)


    def contagion_response(self):
                
        self.community.paradigm.UpdateExpectations(self.community)#move to community?

        newPara = False
        # MIMESIS -- should community adopt a known counter paradigm?
        for ct in self.counterParadigms: #TODO probably should suffle first?
            # what are the expected returns pitched by other known paradigms?
            # Are they a certain amount better than what the current paradigm offer's?
            if ct.Compare(self.community) > self.community.paradigm.threshold:
                self.community.paradigm = ct
                newPara = True
                break

        # MUTATE!!! (via current paradigm's rules on mutation)
        if not newPara and rnd.random() < self.community.paradigm.mutation_rate:
            p = self.community.paradigm.Mutate(self.community)
            self.community.paradigm = p
            newPara = True
            
        # word spreads of the current paradigm to neighbours
        if not newPara:
            #spread current paradigm to neighbouring communities
            for n in self.community.neighbours:
                if (self.community.neighbours[n].terrain.polity_forming):
                    self.community.neighbours[n].icono.counterParadigms.append(self.community.paradigm)
            for n in self.community.littoral_neighbours_in_range(self.community.sea_attack_distance):
                if (n.neighbour.terrain.polity_forming):
                     n.neighbour.icono.counterParadigms.append(self.community.paradigm)
            
            self.counterParadigms.clear()  # no memory of paradigms never adopted
            #TODO--LONGER MEMORIES?
        else:
            self.counterParadigms.clear()


    def Response(self):
        
        self.community.paradigm.UpdateExpectations(self.community)#move to community?
        
        discomfort = 1 - self.comfort

        #COMPLACENCY AND MITIGATION
        if (self.comfort > .75 ):#TODO--should threshold affect?
            self.community.agri.workrate -= self.community.paradigm.workrate_change
        elif (self.comfort < .25):
            self.community.agri.workrate += self.community.paradigm.workrate_change
        
        if (self.community.agri.workrate > 1): self.community.agri.workrate = 1
        elif (self.community.agri.workrate < 0): self.community.agri.workrate  = 0

        newPara = False
        # MIMESIS -- should community adopt a known counter paradigm?
        for ct in self.counterParadigms: #TODO probably should suffle first?
            # what are the expected returns pitched by other known paradigms?
            # Are they a certain amount better than what the current
            # paradigm offer's? (relative to the community's current comfort)
            if ct.Compare(self.community) > self.community.paradigm.threshold * self.comfort:
                self.community.paradigm = ct
                newPara = True
                if self.community.params.mil_spread:
                    self.diffuse_military_tech(self.community, self.community.params, ct.military_techs)
                break


        # MUTATE!!! (via current paradigm's rules on mutation)
        if not newPara and rnd.random() < (discomfort * discomfort * discomfort
                                            * self.community.paradigm.mutation_rate):
            p = self.community.paradigm.Mutate(self.community)
            self.community.paradigm = p
            newPara = True
            
        # word spreads of the current paradigm to neighbours
        if not newPara:
            #spread current paradigm to neighbouring communities
            for n in self.community.neighbours:
                if (self.community.neighbours[n].terrain.polity_forming):
                    self.community.neighbours[n].icono.counterParadigms.append(self.community.paradigm)
            for n in self.community.littoral_neighbours_in_range(self.community.sea_attack_distance):
                if (n.neighbour.terrain.polity_forming):
                     n.neighbour.icono.counterParadigms.append(self.community.paradigm)
            
            self.counterParadigms.clear()  # no memory of paradigms never adopted
            #TODO--LONGER MEMORIES?
        else:
            self.counterParadigms.clear()
    

    def AdjustComfort(self, adjust):
        self.comfort += adjust
        if self.comfort < 0:
            self.comfort = 0
        elif self.comfort > 1:
            self.comfort = 1


    # for spreading military techs with paradigm mimesis, copied from community
    def diffuse_military_tech(self, target, params, military_techs):
        # Select a tech to share
        selected_tech = randint(params.n_military_techs)
        if military_techs[selected_tech] is True:
            if params.military_tech_spread_probability > random():
                # Share this tech with the target
                target.military_techs[selected_tech] = True


