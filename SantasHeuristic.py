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
        duration_log_granularity = 0.00005;
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
           toy_baskets[duration_interval.begin:duration_interval.end] = duration_interval.data + [(toy.id, toy.duration)];

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


        temp = []
        for elf in self.elves:
            avg_duration = 0;
            for toy in self.elves[elf][1]:
                avg_duration += toy[1]
            temp.append(str(avg_duration/float(len(self.elves[elf][1]))))
        print(temp[1:900])





    def start_work(self):
        toy_baskets = self.create_toy_baskets();
        self.allocate_baskets_to_elf(toy_baskets);












                                    
            

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
    
