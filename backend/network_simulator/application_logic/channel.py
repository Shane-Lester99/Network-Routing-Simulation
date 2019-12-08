import numpy
from decorators import validate_amount, validate_path
from collections import namedtuple
import priority_queue

blocked_channel_entry = namedtuple("BlockedChannel", "chan_coor chan_used")

def get_weight(index_list, channels):
    summ = 0
    for i in index_list:
        summ += channels[i]
    return summ

class Channels:
    """
    This module models network channels that are exponentially distributed in
    interarrival rates. Given channel interference from the system and a path 
    to query between nodes, it can also return the best channel allocation by
    assigning ids to the path such that it has the lowest summed interarrival
    rate
    """
    
    @validate_amount
    def __init__(self, amount, transmission_radius):
        self.transmission_radius = transmission_radius
        self.channels = [numpy.random.exponential() for _ in range(amount)]
        
    def __repr__(self):
        chan_str = str(["Channel {}: {}".format(i, exp) for i, exp in enumerate(self.channels)])
        return "Channels({})".format(chan_str)
    
    @validate_path   
    def find_cheapest_channels_for_path(self, global_interference, coor_path):
        """
        This will return the cheapest channel combination for a given path subject
        to interference globally and from the path.
        
        It uses backtracking by enumerating the search space of mapping channel
        index values to edges to the coordinate path. An example is that the edge
        from node 1 to node 2 can get assgined channel 0 at index 0. An example of
        a forest of trees generated by this backtracking algorithm:
        
        say we have channels [0,1,2,3] and we have 3 nodes on our route (2 edges).
        We will generate a tree of height 2 (we need to assign two channels to the
        edges) and it would look like this:
        
        0 -> (2, 3) 1 -> (3), 2 -> (0), 3 -> (0, 1) as a forest of 4 trees.
        We would then have enumerated all these channel_id assignments:
        [0,2   0,3   1,3   3,2   2,0   3,0   3,1]
        Notice how we didn't assign channels subject to interference.
        
        Because we must choose from these paths, we store each path in a priority
        queue and choose the channel allocation with the minimum weight.
        
        Weight here is the lowest sum of exponentially distributed channel 
        interarrival rates. Low interarrival weights signify that the channel
        has the least likely chance of being occupied and therefore is the best choice
        
        We prune the search space by eliminating all the channels that have interference.
        Interference here is defined as  channels that are used within the 
        transmission radius of another node and the two adjacent channels to that
        used channel. 
        
        We then store each path candidate in a priority queue and return the top
        value, which is the cheapest path.
        """
        def find_paths(coor_path, curr, output, blocked_channels):
            if len(curr) == len(coor_path) - 1:
                weight = get_weight(curr, self.channels)
                output.add_task((weight, curr.copy()))
                return
            for chan_num, _ in enumerate(self.channels):
                available_channels = self._check_available_channels(blocked_channels,
                                                                    coor_path[len(curr)])
                if chan_num in available_channels:
                    blocked_channels.append(blocked_channel_entry(coor_path[len(curr)],
                                                                  chan_num))
                    curr.append(chan_num)
                    find_paths(coor_path, curr, output, blocked_channels)
                    blocked_channels.pop()
                    curr.pop()
        output = priority_queue.PriorityQueue()
        find_paths(coor_path, [], output, global_interference)
        return output[0]
    
    def _check_available_channels(self, blocked_channels, curr_coor):
        """
        This returns a list of available channels when given a cooridinate
        """
        dont_use_channels = set()
        for blocked_chan in blocked_channels:
            curr_coor_x, curr_coor_y = curr_coor
            block_coor_x, block_coor_y = blocked_chan.chan_coor
            if (abs(curr_coor_x - block_coor_x) <= self.transmission_radius and
                abs(curr_coor_y - block_coor_y) <= self.transmission_radius):
                    # If we find a channel with interference we don't use the
                    # adjaceny channels either
                    dont_use_channels.add(blocked_chan.chan_used)
                    dont_use_channels.add(blocked_chan.chan_used - 1)
                    dont_use_channels.add(blocked_chan.chan_used + 1)
        channels_total = set(i for i, _ in enumerate(self.channels))
        return list(channels_total - dont_use_channels)
        
if __name__ == "__main__":
    sys_channels = Channels(5, 2)
    path = [(0,2), (2,3), (3,5)]
    global_intf = []
    x = sys_channels.find_cheapest_channels_for_path(global_intf, path)
    print(x)