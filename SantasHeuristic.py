__author__ = 'Rahul'
__date__ = 'November 27, 2014'

import os
import csv
import math
import heapq
import time
import datetime
import operator
from hours import Hours
from toy import Toy
from elf import Elf
import numpy as np;
from intervaltree import Interval, IntervalTree;
from random import shuffle;
from random import randint;
import random;

class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file, soln_file):
        self.hrs = Hours()
        self.NUM_ELVES                = NUM_ELVES;
        self.ref_time                 = datetime.datetime(2014, 1, 1, 0, 0);
        self.max_duration_log         = 0;

        #Toys sorted based on arrival time
        self.toys                     = self.read(toy_file);

        self.elves                    = dict(); #elf_id -> (elf Object, list of allocated toys)
        #Every elf maintains list of toys which it has to optically work on
        for i in xrange(1, NUM_ELVES+1):
            elf = Elf(i)
            self.elves[elf.id]  = (elf, []);

    def read(self, toy_file):
        toys = []
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row
            
            for row in toysfile:
                current_toy = Toy(row[0], row[1], row[2]);
                if math.log(current_toy.duration) > self.max_duration_log:
                    self.max_duration_log = math.log(current_toy.duration)
                toys.append(current_toy)
        return  toys;
                

    def create_toy_baskets(self):
        '''
        :Builds toy_baskets where each basket is granularized based on log(duration)
        :return : Final structure has the ids of the toys belonging to that duration bucket
        '''
        #Create baskets of toys where the granularity of log(duration) = 0.01
        toy_baskets = IntervalTree();
        i = 0;
        duration_log_granularity = 0.0005;
        while i <= self.max_duration_log:
            toy_baskets[i: (i+duration_log_granularity)] = [] # A list of toys
            i += duration_log_granularity;

        i = 0;
        for toy in self.toys:
           i = i + 1;
           if i % 10000 == 0:
               print("Interval search at " + str(i))
           duration_log      = math.log(toy.duration);
           duration_interval = list(toy_baskets.search(duration_log))[0];
           #Remove the current interval and reinsert with updated count -- HACK
           toy_baskets.remove(duration_interval);
           toy_baskets[duration_interval.begin:duration_interval.end] = duration_interval.data + [(toy)];

        return toy_baskets;

    def allocate_baskets_to_elf(self, toy_baskets):
        '''
        :param toy_baskets: Interval.begin, Interval.end, List of toy_ids
        :return: allocates toys from various baskets to various elves
        '''
        for tb in toy_baskets:
            toys     = tb.data
            shuffle(toys); #Shuffle toys
            current_elf_id = 1;
            for toy in toys:
                self.elves[current_elf_id][1].append(toy);
                current_elf_id += 1;
                if current_elf_id > self.NUM_ELVES:
                    current_elf_id = 1;
        
    
    def assign_elf_to_toy(self, input_time, current_elf, current_toy, hrs):
        """ Given a toy, assigns the next elf to the toy. Computes the elf's updated rating,
        applies the rest period (if any), and sets the next available time.
        :param input_time: list of tuples (next_available_time, elf)
        :param current_elf: elf object
        :param current_toy: toy object
        :param hrs: hours object
        :return: list of elves in order of next available
        """
        start_time = hrs.next_sanctioned_minute(input_time)  # double checks that work starts during sanctioned work hours
        duration = int(math.ceil(current_toy.duration / current_elf.rating))
        sanctioned, unsanctioned = hrs.get_sanctioned_breakdown(start_time, duration)

        if unsanctioned == 0:
            return hrs.next_sanctioned_minute(start_time + duration), duration
        else:
            return hrs.apply_resting_period(start_time + duration, unsanctioned), duration    
                                
    def P(self,prev_score,next_score,temperature):
        if next_score > prev_score:
            return 1.0
        else:
            return math.exp( -abs(next_score-prev_score)/temperature );
            
            
    def generate_neighbour(self, toys):
        start       = 0;
        end         = len(toys) - 1;
        #Swap;
        rand1       = randint(start, end);
        rand2       = randint(start, end);
        temp        = toys[rand2];
        toys[rand2] = toys[rand1];
        toys[rand1] = temp;
        return toys;
    
    def evaluate(self, elf, toys):
        #Create a copy of elf
        copy_elf                     = Elf(elf.id);
        
        for current_toy in toys:
            elf_available_time = copy_elf.next_available_time;
            work_start_time    = elf_available_time;
            if current_toy.arrival_minute > elf_available_time:
                work_start_time = current_toy.arrival_minute;
                
            copy_elf.next_available_time, work_duration = \
                    self.assign_elf_to_toy(work_start_time, copy_elf, current_toy, self.hrs);
            copy_elf.update_elf(self.hrs, current_toy, work_start_time, work_duration);
        
        #Earliest time elf finishes the task.
        return copy_elf.next_available_time;
    
            
            
        
        
        
        
        
        
                
                    
    def do_simulatedAnnealing(self, elf_id):
        start_temp       = 1e+01;
        alpha            = 0.99;
        end_temp         = 1e-3;
        
        no_iterations    = 10000;
        
        current_temp     = start_temp;
        current_toy_list = self.elves[elf_id][1];
        current_elf      = self.elves[elf_id][0];
        
        current_score    = self.evaluate(current_elf, current_toy_list);
        
        while current_temp > end_temp:
            #Generate a list of possible neighbours at this temperature
            current_itr = 1;
            while current_itr <= no_iterations:
                #Genearate a neighbour
                next_neighbour = self.generate_neighbour(current_toy_list);
                next_score     = self.evaluate(current_elf, next_neighbour);
                
                p = self.P(current_score, next_score, current_temp);
                if random.random() < p:
                    #Take the Step
                    current_toy_list = next_neighbour;
                    current_score    = next_score;
                    break;
                current_itr +=1; 
            print(" Temp :" + str(current_temp) + "  Score : " +str(current_score))
            #Decrease the temperature
            current_temp = current_temp * alpha;
        
        for toy in current_toy_list:
            print(str(toy.id) + "  " + str(toy.duration));
            

        
        
        


    def start_work(self):
        toy_baskets = self.create_toy_baskets();
        self.allocate_baskets_to_elf(toy_baskets);
        self.do_simulatedAnnealing(1);
        
        












                                    
            

# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':

    start = time.time()

    NUM_ELVES = 900;
    toy_file  = os.path.join(os.getcwd(), 'data/toys_rev22_.csv');
    soln_file = os.path.join(os.getcwd(), 'data/sampleSubmission_rev2.csv')
    santa     = Santas_lab(NUM_ELVES, toy_file, soln_file)
    santa.start_work()

    print 'total runtime = {0}'.format(time.time() - start)
    
