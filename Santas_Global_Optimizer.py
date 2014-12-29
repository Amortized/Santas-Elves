
import os
import csv
import time
import math
import datetime
import heapq

from hours import Hours
from toy import Toy
from elf import Elf
import time;

def assign_elf_to_toy(input_time, current_elf, toy_duration, hrs):
    """ Given a toy, assigns the next elf to the toy. Computes the elf's updated rating,
        applies the rest period (if any), and sets the next available time.
        :param input_time: list of tuples (next_available_time, elf)
        :param current_elf: elf object
        :param current_toy: toy object
        :param hrs: hours object
        :return: list of elves in order of next available
    """
    start_time = hrs.next_sanctioned_minute(input_time)  # double checks that work starts during sanctioned work hours
    duration = int(math.ceil(toy_duration / current_elf.rating))
    sanctioned, unsanctioned = hrs.get_sanctioned_breakdown(start_time, duration)

    if unsanctioned == 0:
        return hrs.next_sanctioned_minute(start_time + duration), duration
    else:
        return hrs.apply_resting_period(start_time + duration, unsanctioned), duration

def read_toys(toy_file, num_toys):
    """ Reads the toy file and returns a dictionary of Toys.
    Toy file format: ToyId, Arrival_time, Duration
        ToyId: toy id
        Arrival_time: time toy arrives. Format is: YYYY MM DD HH MM (space-separated)
        Duration: duration in minutes to build toy
    :param toy_file: toys input file
    :param hrs: hours object
    :param num_toys: total number of toys to build
    :return: Dictionary of toys
    """
    toy_dict = {}
    with open(toy_file, 'rb') as f:
        fcsv = csv.reader(f)
        fcsv.next()  # header row
        for row in fcsv:
            toy_dict[int(row[0])] = int(row[2])
    if len(toy_dict) != num_toys:
        print '\n ** Read a file with {0} toys, expected {1} toys. Exiting.'.format(len(toy_dict), num_toys)
        exit(-1)
    return toy_dict


def global_optimizer(sub_file, myToys, hrs, NUM_ELVES, output):
    """ Score the submission file, performing constraint checking. Returns the time (in minutes) when
    final present is complete.
    :param sub_file: submission file name. Headers: ToyId, ElfId, Start_Time, Duration
    :param myToys: toys dictionary
    :param hrs: hours object
    :return: time (in minutes) when final present is complete
    """
    file_handler         = open(output, "wb");

    hrs                  = Hours();
    ref_time             = datetime.datetime(2014, 1, 1, 0, 0)
    threshold_minute     = hrs.convert_to_minute('2450 1 1 0 0');

    basket_toys_above_th = [];
    basket_toys_below_th = []; #Unchanged

    elf_availability     = {}; #Maintains the earliest time when elves finish their last jobs
    for i in range(1, NUM_ELVES+1):
        elf_availability[i] = [0,0] 

    row_count = 0

    with open(sub_file, 'rb') as f:
        fcsv = csv.reader(f)
        fcsv.next()  # header
        for row in fcsv:
            row_count += 1
            if row_count % 50000 == 0:
                print 'Starting toy: {0}'.format(row_count)

            current_toy   = int(row[0])
            current_elf   = int(row[1])
            start_minute  = hrs.convert_to_minute(row[2])
            duration      = int(row[3])

            if start_minute > threshold_minute:
                basket_toys_above_th.append(current_toy);
            else:
                basket_toys_below_th.append((row[0], row[1], row[2], row[3]));

            
            if elf_availability[current_elf][0] < start_minute:
                elf_availability[current_elf][0] = start_minute;
                elf_availability[current_elf][1] = duration;

    myelves = []
    for i in elf_availability.keys():
        elf                     = Elf(i);
        elf.rating              = 0.25;
        elf.next_available_time = elf_availability[current_elf][0] + int(math.ceil(elf_availability[current_elf][1]/elf.rating)); 
        heapq.heappush(myelves, (elf.next_available_time, elf))

    while len(basket_toys_above_th) > 0:

        #Retrive the toy object
        current_toy_duration  =  myToys[basket_toys_above_th[0]];

        #Pick the next available elf and execute it
        elf_available_time, current_elf = heapq.heappop(myelves)
        work_start_time                 = elf_available_time
        
        current_elf.next_available_time, work_duration = \
                    assign_elf_to_toy(work_start_time, current_elf, current_toy_duration, hrs)



 
        current_elf.update_elf(hrs, Toy(basket_toys_above_th[0], '2014 01 01 01 01' ,current_toy_duration), \
            work_start_time, work_duration);


        # put elf back in heap
        heapq.heappush(myelves, (current_elf.next_available_time, current_elf))

        tt = ref_time + datetime.timedelta(seconds=60*work_start_time)
        time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])

        #Add it to the basket below the threshold
        basket_toys_below_th.append((basket_toys_above_th[0], current_elf.id, time_string, work_duration));

        del basket_toys_above_th[0];

    basket_toys_below_th = sorted(basket_toys_below_th, key=lambda element: hrs.convert_to_minute(element[2]));

    file_handler.write("ToyId,ElfId,StartTime,Duration\n");
    for obj in basket_toys_below_th:
        file_handler.write(str(obj[0]) + "," + str(obj[1]) + "," +  str(obj[2]) + "," +  str(obj[3]) + "\n" );
    file_handler.close();


    





# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':
    """ Evaluation script for Helping Santa's Helpers, the 2014 Kaggle Holiday Optimization Competition. """

    start = time.time()

    NUM_TOYS = 10000000
    NUM_ELVES = 900

    toy_file = os.path.join(os.getcwd(), 'data/toys_rev2.csv')
    myToys   = read_toys(toy_file, NUM_TOYS)
    print ' -- All toys read. Starting to score submission. '

    sub_file = os.path.join(os.getcwd(), 'data/finalSubmission1.csv')
    output   = os.path.join(os.getcwd(), 'data/finalModifiedSubmission1.csv')
    
    hrs = Hours()
    global_optimizer(sub_file, myToys, hrs, NUM_ELVES, output)

    print 'total time = {0}'.format(time.time() - start)




