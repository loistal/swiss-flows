import itertools
from node import Node

class Flow:
    """
    Represents a flow.

    Parameters:
        src the source Node
        dst the destination Node
        directed True if the flow is directed
        weight the importance of the flow.
    """

    WEIGHT_IDX = 'weight'
    START_IDX = 'start'
    END_IDX = 'end'
    INTRVL_IDX = 'intervals'

    def __init__(self, src, dst, directed=False):
        self.src = src
        self.dst = dst
        self.directed = directed
        self.weight = 0
        self.start_date = None
        self.end_date = None

        # Avoid symmetrical undirected flows
        if not directed and src.name > dst.name:
                self.src = dst
                self.dst = src

    @staticmethod
    def infer_flows(user_id, tweets, nodes, delta_t, directed):
        """
        Infer the flows for one user.
        See notebooks/detection.ypnb for more details.

        Parameters:
            user_id     The user ID.
            tweets      The tweets of the user.
            nodes       The list of nodes used to generate the flows.
            delta_t     The length of the interval to consider to detect flows.
            directed    Choice to detect directed or undirected flows.

        Returns:
            Tuple (user_id, flows) with flows a dictionnary of the following
            form :
            {Flow: {weight: ...,
                    start: ...,
                    end: ...,
                    intervals: ...}}

            Note: the result is returned as a dictionnary in the notebook.
            The tuple form is just a convenience for Spark adaptation.
        """
        # Generate all possible pairs of tweet sorted by interval length
        pairs = sorted(list(itertools.combinations(tweets, 2)),
                       key=Flow._by_interval_len)

        # {f1 : {weight:1, intervals:[interval1, interval2...]}}
        flows = {}
        for id_pair in pairs:

            # [id, Timestamp, lon, lat]
            t1 = id_pair[0]
            t2 = id_pair[1]

            # Nodes corresponding to the tweets
            n1 = Node.locate_point((t1[3], t1[2]), nodes)
            n2 = Node.locate_point((t2[3], t2[2]), nodes)

            # Time interval condition
            time1 = t1[1].to_pydatetime()
            time2 = t2[1].to_pydatetime()
            ts1 = time1 if time1 < time2 else time2
            ts2 = time2 if time1 < time2 else time1
            tweet_interval = (ts1, ts2)
            time_cond = (ts2 - ts1).days <= delta_t

            # Node conditions
            geo_cond = n1 and n2 and (n1 != n2)

            if time_cond and geo_cond:
                # Build the flow
                src = n1
                dst = n2

                if directed:
                    if time1 < time2 and time1.time() < time2.time():
                        src = n1
                        dst = n2
                    elif time2 < time1 and time2.time() < time1.time():
                        src = n2
                        dst = n1
                    else:
                        # Cannot conclude
                        continue

                flow = Flow(src=src, dst=dst, directed=directed)

                overlap = False
                if flow in flows:
                    # Look for overlapping flows
                    for interval in flows[flow][Flow.INTRVL_IDX]:
                        if Flow.is_overlapping(tweet_interval, interval):
                            overlap = True
                            break

                else:
                    # Add the initial values if it's a new flow
                    flows[flow] = {Flow.WEIGHT_IDX: 1,
                                   Flow.INTRVL_IDX: [],
                                   Flow.START_IDX:ts1,
                                   Flow.END_IDX:ts2}

                # If no overlap, then it's not the exact same flow
                if not overlap:
                    # Update start date
                    flows[flow][Flow.START_IDX] = min(ts1, flows[flow][Flow.START_IDX])

                    # Update end date
                    flows[flow][Flow.END_IDX] = max(ts2, flows[flow][Flow.END_IDX])

                    # Update weight
                    flows[flow][Flow.WEIGHT_IDX] += 1

                # In any case, add the interval we just found for later use
                flows[flow][Flow.INTRVL_IDX].append(tweet_interval)

        return (user_id, flows)

    @staticmethod
    def agg_flows(user_flows):
        """
        Aggregate flows. See notebooks/detection.ypnb for more details.

        Paramters:
            user_flows List of tuple (user_id, flows)

        Returns:
            Sorted list of flows.
        """
        agg_flows = {}

        for user, flows in user_flows:
            for flow, attr in flows.items():
                if flow not in agg_flows:
                    agg_flows[flow] = {Flow.WEIGHT_IDX: attr[Flow.WEIGHT_IDX],
                                       Flow.START_IDX: attr[Flow.START_IDX],
                                       Flow.END_IDX: attr[Flow.END_IDX]}
                else:
                    agg_flows[flow][Flow.WEIGHT_IDX] += attr[Flow.WEIGHT_IDX]
                    agg_flows[flow][Flow.START_IDX] = min(agg_flows[flow][Flow.START_IDX],
                                                          attr[Flow.START_IDX])
                    agg_flows[flow][Flow.END_IDX] = min(agg_flows[flow][Flow.END_IDX],
                                                        attr[Flow.END_IDX])


        final_flows = []
        for flow, attr in agg_flows.items():
            flow.weight = attr[Flow.WEIGHT_IDX]
            flow.start_date = attr[Flow.START_IDX]
            flow.end_date = attr[Flow.END_IDX]
            final_flows.append(flow)

        # Sort it by weight
        final_flows.sort(key=lambda x: x.weight, reverse=True)

        return final_flows

    @staticmethod
    def is_overlapping(i1, i2):
        """
        Returns True if the intervals are overlapping.
        Need strict inequalities : A-B-A should count as (A-B) and (B-A), so
        they should not be detected as overlapping.

        Parameters:
            i1 Interval as tuple
            i2 Interval as tuple
        """
        return (i1[0] < i2[0] < i1[1]) or (i2[0] < i1[0] < i2[1])

    @property
    def symmetrical(self):
        """
        Return the symetrical flow
        """
        return Flow(src=self.dst, dst=self.src, directed=self.directed)

    @staticmethod
    def _by_interval_len(tweet_tuple):
        tmp1 = tweet_tuple[0]
        tmp2 = tweet_tuple[1]

        # Order the tweet by timestamp
        t1 = tmp1 if tmp1[1].to_pydatetime() < tmp2[1].to_pydatetime() else tmp2
        t2 = tmp2 if tmp1[1].to_pydatetime() < tmp2[1].to_pydatetime() else tmp1

        # Return the length of the interval
        return t2[1].to_pydatetime() - t1[1].to_pydatetime()

    def __str__(self):
        link = '-->' if self.directed else '<-->'
        template = '[Flow] {} {} {} (weight: {}, start: {}, end: {}).'
        return template.format(self.src.name,
                               link,
                               self.dst.name,
                               self.weight,
                               self.start_date,
                               self.end_date)

    def __eq__(self, other):
        cond = (self.src == other.src and
                self.dst == other.dst and
                self.directed == other.directed)

        return isinstance(other, type(self)) and cond

    def __lt__(self, other):
        return self.src.name < other.src.name

    def __gt__(self, other):
        return not self.__lt__(other)

    def __hash__(self):
        mod = 1231 if self.directed else 1237
        return (hash(self.src) ^ hash(self.dst)) % mod
