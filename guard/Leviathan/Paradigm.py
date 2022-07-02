import random as rnd

# the paradigm defining agricultural rules and depletion rates
# including expectations based on follower return
class Paradigm():

    def __init__(self, community):
        
        self.community = community
        self.name = rnd.random()
        self.latitude = 0
        self.maxlat = 100
        
        #basic parameters
        self.mut_amount = community.params.mut_amount
        self.num_starting_rules = 0 #TODO--parameterized?
        
        #CULTURAL PARAMETERS
        self.sensitivity = community.params.sensitivity
        self.mutation_rate = community.params.mutation_rate
        self.threshold = community.params.threshold
        self.workrate_change = community.params.workrate_change
        
        #variables
        self.followers = []
        self.followers.append(community)
        self.expectations = rnd.random()*100
        self.depletion_rules = [0] * 10 #TODO PARAMETERS FOR NUMBER OF RULES?
        self.yield_rules = [0] * 10
        
        for i in range(self.num_starting_rules):
            rndnum = rnd.randint(0,9)
            self.depletion_rules[rndnum] = ((rnd.random()*2) -1) *.05
            self.yield_rules[rndnum] = rnd.random()

    # compare expectations of this paradigm for communitys considering
    # adopting it, relative to the community the paradigm already follows
    def Compare(self, community):
        if community.params.contagion == 'Perfect':
            returns = sum(self.yield_rules) - (sum(self.depletion_rules)*10)
            comm_returns = sum(community.paradigm.yield_rules) - (sum(community.paradigm.depletion_rules)*10)
            return returns / (comm_returns + 0.001)
        elif community.params.contagion == 'FutureDiscounted':
            returns = sum(self.yield_rules) - (sum(self.depletion_rules)*10)
            comm_returns = sum(community.paradigm.yield_rules) - sum(community.paradigm.depletion_rules)
            return returns / (comm_returns + 0.001)
        else:
            return self.expectations / community.paradigm.expectations


    # create new para by modifying this paradigm by removing and adding rules
    def Mutate(self, community):
        
        p = Paradigm(community)
        p.depletion_rules = self.depletion_rules
        p.yield_rules = self.yield_rules
        p.expectations = self.expectations #FROM TEST-F.4
        
        # for diminishing returns when applying paradigm to
        # communities at other latitudes
        p.latitude = community.position[1]
        
        for i in range(self.mut_amount):
            rndnum = rnd.randint(0,9)
            #100 CYCLES TO DEPLETE --TODO--parameterize?
            p.depletion_rules[rndnum] = ((rnd.random()*1.5) -1) *.01
            p.yield_rules[rndnum] = rnd.random()
        
        return p
    

    # adjust expectations-->accessed by all communities
    # using this paradigm creating "word of mouth"
    def UpdateExpectations(self, community):
        self.expectations += (((community.icono.comfort - .5) * 0.02) + ((community.agri.yields - self.expectations) * 0.02)) / len(self.followers)
        
        #bounds
        if self.expectations <= 0:
            self.expectations = .0000001