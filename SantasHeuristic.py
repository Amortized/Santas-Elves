__author__ = 'Rahul'
__date__ = 'Dec 21, 2014'

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
from random import shuffle;
from random import randint;
import random;
from multiprocessing.dummy import Pool;


class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file):
        self.hrs = Hours()
        self.NUM_ELVES                = NUM_ELVES;
        self.ref_time                 = datetime.datetime(2014, 1, 1, 0, 0);
        self.toy_baskets              = dict();
        self.max_duration_log         = 11.0;  #Predetermined from analysis

        #Toys sorted based on arrival time
        self.create_toy_baskets(toy_file);

        self.elves                    = dict(); #elf_id -> (elf Object, list of allocated toys, optimimum toy workflow)
        #Every elf maintains list of toys which it has to optically work on
        for i in xrange(1, NUM_ELVES+1):
            elf = Elf(i)
            self.elves[elf.id]  = (elf, [], []);



    def create_toy_baskets(self, toy_file):
        '''
        :Builds toy_baskets where each basket is granularized based on log(duration)
        :return : Final structure has the ids of the toys belonging to that duration bucket
        '''
        #Create baskets of toys where the granularity of log(duration) = 0.01
        self.toy_baskets = dict();
        i = 1;
        duration_log_granularity = 0.0005;
        while i <= int(self.max_duration_log/duration_log_granularity):
            self.toy_baskets[i] = [] # A list of toys
            i += 1;

        i = 0;
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row

            for row in toysfile:
              i = i + 1;
              if i % 10000 == 0:
                  print("Reading # " + str(i))
              current_toy       = Toy(row[0], row[1], row[2]);
              #Find the right bucket no
              bucket                   = 1 + int(round(math.log(current_toy.duration), 4) / duration_log_granularity); #Rounded to log_granularity decimal places
              self.toy_baskets[bucket].append(current_toy);




    def allocate_baskets_to_elf(self):
        '''
        :return: allocates toys from various baskets to various elves
        '''
        for bucket in self.toy_baskets:
            toys  = self.toy_baskets[bucket]
            shuffle(toys); #Shuffle toys
            toys_per_elf = int(len(toys) / self.NUM_ELVES);

            current_elf_id = 1;
            for i in range(0, (toys_per_elf*self.NUM_ELVES)):
                self.elves[current_elf_id][1].append(toys[i]);
                current_elf_id += 1;
                if current_elf_id > self.NUM_ELVES:
                    current_elf_id = 1;

            #For remaining toys, randomly pick an elf and assign
            for i in range((toys_per_elf*self.NUM_ELVES), len(toys)):
                self.elves[randint(1, self.NUM_ELVES)][1].append(toys[i]);


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
                                
    def objective_earliest_completion(self,prev_time,next_time,temperature):
        if next_time < prev_time:
            #Elf finishes earlier
            return 1.0
        else:
            return math.exp( -abs(next_time-prev_time)/temperature );

    def objective_increase_health(self, prev_rating, next_rating, temperature):
        if next_rating > prev_rating:
            #Elf is more healtheir
            return 1.0
        else:
            return math.exp( -abs(next_rating-prev_rating)/temperature );
            
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
    
    def evaluate(self, elf, toys, do_io=0, file_handler=None):
        #Create a copy of elf
        copy_elf                     = Elf(elf.id);
        copy_elf.rating              = elf.rating;
        copy_elf.next_available_time = elf.next_available_time;
        copy_elf.no_toys_completed   = elf.no_toys_completed;
        
        for current_toy in toys:
            elf_available_time = copy_elf.next_available_time;
            work_start_time    = elf_available_time;
            if current_toy.arrival_minute > elf_available_time:
                work_start_time = current_toy.arrival_minute;
                
            copy_elf.next_available_time, work_duration = \
                    self.assign_elf_to_toy(work_start_time, copy_elf, current_toy, self.hrs);
            copy_elf.update_elf(self.hrs, current_toy, work_start_time, work_duration);

            if do_io == 1:
                #Write it to the file handler
                tt = self.ref_time + datetime.timedelta(seconds=60*work_start_time)
                time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])
                file_handler.write( str(current_toy.id) + "," + str(copy_elf.id) + "," + str(time_string) + "," + str(work_duration) + "\n");

        #Earliest time elf finishes the task.
        return copy_elf;
    
            
            
        
        
        
        
        
        
                
                    
    def do_simulatedAnnealing(self, current_toy_list, current_elf, obj):
        start_temp       = 1e+10;
        alpha            = 0.99;
        end_temp         = 1e-3;
        no_iterations    = 100;
        current_temp     = start_temp;

        #Store a copy of the elf
        prev_elf                     = Elf(current_elf.id);
        prev_elf.rating              = current_elf.rating;
        prev_elf.next_available_time = current_elf.next_available_time;
        prev_elf.no_toys_completed   = current_elf.no_toys_completed;


        processed_elf                = self.evaluate(current_elf, current_toy_list);
        current_elf                  = processed_elf; #Update elf as the first solution is always accepted

        while current_temp > end_temp:
            #Generate a list of possible neighbours at this temperature
            current_itr = 1;
            while current_itr <= no_iterations:
                #Genearate a neighbour
                next_neighbour    = self.generate_neighbour(current_toy_list);
                processed_elf     = self.evaluate(current_elf, next_neighbour);

                if obj == 0:
                    p = self.objective_earliest_completion(current_elf.next_available_time, processed_elf.next_available_time, current_temp);
                else:
                    p = self.objective_increase_health(current_elf.rating, processed_elf.rating, current_temp);

                if random.random() < p:
                    #Take the Step
                    current_toy_list = next_neighbour;
                    current_elf      = processed_elf;

                    if obj == 0:
                        print( "Elf : " + str(current_elf.id) + " Temp :" + str(current_temp) + "  Completion Time : " +str(current_elf.next_available_time))
                    else:
                        print( "Elf : " + str(current_elf.id) + " Temp :" + str(current_temp) + "  Rating : " +str(current_elf.rating))

                    break;
                current_itr +=1;

            #Decrease the temperature
            current_temp = current_temp * alpha;
        
        #Now, that best ordering is found out; exceute it on the elf
        return self.evaluate(prev_elf, current_toy_list) , current_toy_list;

    def optimize_elf(self, elf_id):
        toy_list         = self.elves[elf_id][1];
        current_elf      = self.elves[elf_id][0];
        toy_batch_sz     = 5;
        counter          = 0;
        obj              = 0; #Possible values 0 - decreased completion time, 1 - increase health

        #Shuffle the toys
        shuffle(toy_list);
        while counter < len(toy_list):
            #Pick batch
            current_toy_list                   = toy_list[counter:(counter+toy_batch_sz)];
            current_elf, optimum_toy_list      = self.do_simulatedAnnealing(current_toy_list, current_elf, obj);
            counter                           += toy_batch_sz;

            #Add the optimum toy_list in that order
            for ot in optimum_toy_list:
                self.elves[elf_id][2].append(ot);

            #Change the objective goal
            if obj == 0 :
                obj = 1;
            else:
                obj = 0;


    def start_work(self):
        self.allocate_baskets_to_elf();

        elf_ids = list(xrange(1, self.NUM_ELVES+1));
        pool    = Pool(12);
        pool.map(self.optimize_elf, elf_ids);
        pool.close();
        pool.join();



    def write(self, elf_id, fh):
        current_elf         = self.elves[elf_id][0];
        optimum_toy_list    = self.elves[elf_id][2];
        self.evaluate(current_elf, optimum_toy_list, 1, fh);



# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':

    start = time.time()

    NUM_ELVES = 900;
    toy_file  = os.path.join(os.getcwd(), 'data/toys_rev22_.csv');
    soln_file = os.path.join(os.getcwd(), 'data/sampleSubmission_rev2.csv')
    santa     = Santas_lab(NUM_ELVES, toy_file)
    santa.start_work()

    fh           = open(soln_file, "w");
    fh.write('ToyId,ElfId,StartTime,Duration\n');
    for elf_id in xrange(1, NUM_ELVES+1):
        santa.write(elf_id, fh);
    fh.close();


    print 'total runtime = {0}'.format(time.time() - start)
    
