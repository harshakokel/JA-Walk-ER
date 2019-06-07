from DEUtils import remove_double_quote
import itertools
import argparse
import ExtParser
import os
import itertools
import random
import re

# Define a short class for raising exceptions to help with debugging.

class ExceptionCase(Exception):
    def handle(self):
        print(self.message)

# Setup: parse the commandline input, perform checks, and import/parse the specified file.

class Setup:

    def __init__(self):

        self.diagram = None # The diagram we're walking.
        self.verbose = False     # -v, --verbose
        self.nowalk = False      # -n, --nowalk
        self.walk = True         # -w, --walk
        self.shortest = False    # -s, --shortest
        self.exhaustive = False  # -e, --exhaustive
        self.random = False      # -r, --random
        self.randomwalk = False  # -rw, --randomwalk
        self.Nfeatures = None    # -n, --number
        self.dot = False  # -d, --dot

        # Start by creating an argument parser to help with user input.
        parser = argparse.ArgumentParser(description="Walk-ER: a system for walking the paths in an entity-relational diagram."\
                                         " Written by Alexander L. Hayes (Alexander.Hayes@utdallas.edu))"\
                                         " and Mayukh Das. University of Texas at Dallas. STARAI Lab (dir. Professor Natarajan).",
                                         epilog="Copyright 2017 Free Software Foundation, Inc."\
                                         " License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>."\
                                         " This is free software: you are free to change and redistribute it."\
                                         " There is NO WARRANTY, to the extent permitted by law.")
        # Add the arguments.
        walk = parser.add_mutually_exclusive_group()
        parser.add_argument("diagram_file")
        parser.add_argument("-v", "--verbose",
                            help="Increase verbosity to help with debugging.",
                            action="store_true")
        parser.add_argument("--number",
                            type=int,
                            help="Select number of features to walk to (assumes that Important features are ordered from most important to least important). Defaults to number_attributes + number_relations if chosen number is greater than both.")
        #parser.add_argument('Nfeatures')
        walk.add_argument("-w", "--walk",
                          help="[Default] Walk graph from target to features.",
                          action="store_true")
        walk.add_argument("-s", "--shortest",
                          help="Walk the graph from target to features. If there are multiple paths, take the shortest. If the shortest are equal lengths, walk both.",
                          action="store_true")
        walk.add_argument("-n", "--nowalk",
                          help="[Not implemented] Instantiate variables without walking.",
                          action="store_true")
        walk.add_argument("-e", "--exhaustive",
                          help="Walk graph from every feature to every feature.",
                          action="store_true")
        walk.add_argument("-r", "--random",
                          help="Ignore features the user selected and walk (-w) from the target to random features.",
                          action="store_true")
        walk.add_argument("-rw", "--randomwalk",
                          help="Walk a random path from the target until reaching a depth limit (specified with --number).",
                          action="store_true")
        parser.add_argument("-d", "--dot",
                          help="Graph provided in dot format.",
                          action="store_true")
        # Get the args.
        args = parser.parse_args()

        # Make sure the diagram_file is valid.
        if not os.path.isfile(args.diagram_file):
            raise ExceptionCase('Error [1]: Could not find file: "' + args.diagram_file + '"')


        # Import the diagram:
        self.dot = args.dot
        if self.dot:
            self.diagram = ExtParser.parse_file(args.diagram_file)
        else:
            '''Reads the contents of 'file_to_read', raises an exception if it cannot be read.'''
            try:
                diagram = open(args.diagram_file).read()
            except:
                raise ExceptionCase('Error [1]: Could not read the file: "' + args.diagram_file + '"')
            if len(diagram.splitlines()) == 6:
                self.diagram = diagram
            else:
                raise ExceptionCase('Error [1]: File opened successfully, but has the wrong number of lines.')

        # Since the files exist, we can go ahead and set the rest of the parameters, starting with verbose
        self.verbose = args.verbose

        if (args.number != None):
            if (args.number >= 0):
                self.Nfeatures = args.number
            else:
                raise(ExceptionCase('Error [1]: Cannot have negative features.'))

        # Check the rest of the parameters, update if necessary.
        if not (args.walk or args.nowalk or args.exhaustive or args.random or args.shortest or args.randomwalk):
            # If this occurs, no flags were specified, so keep defaults (default: self.walk=True).
            print('[Default] "Walk Mode": Walk graph from target to features.')
            pass
        else:
            self.nowalk = args.nowalk
            self.walk = args.walk
            self.shortest = args.shortest
            self.exhaustive = args.exhaustive
            self.random = args.random
            self.randomwalk = args.randomwalk

        if self.verbose:
            print('Imported Diagram File:\n')
            print(diagram)


class BuildDictionaries:

    def __init__(self, diagram, verbose=False):
        self.verbose = verbose
        self.diagram = diagram
        '''Takes the diagram file passed as an input and turns it into dictionaries that can be used over the next few sections:
        Nodes: {Student=EntityNodeStyle, Professor=EntityNodeStyle, Rating=AttributeNodeStyle, Teach=RelationNodeStyle}
        Edges : {publish|paper=RelationEdge, Course|Rating=AttributeEdge}
        Important: [publish, Rating]
        Target: Rating
        RelatedEntities : {publish=[Student, Professor, paper], Teach=[Professor, Course]}
        AttributeEntityMapping : {Rating=[Course], yearsinprogram=[Student, yearsinprogram]}
        '''
        self.entities = []
        self.relations = []
        self.attributes = []
        # importants = []
        # target = ''
        self.Graph = {}
        self.relations_dict = {}
        self.attribute_dict = {}
        self.multi_value_attributes = {}

        for line in self.diagram.splitlines():

            # First line: all nodes in the graph: {Student=EntityNodeStyle, Rating=AttributeNodeStyle, Teach=RelationNodeStyle}
            if line[:6] == 'Nodes:':
                # Get the items between the { }
                nodes = line[line.find('{') + 1:line.find('}')].replace(',', '').split()
                for node in nodes:
                    current = node.split('=')

                    if current[1] == 'EntityNodeStyle':
                        self.entities.append(current[0])
                    elif current[1] == 'AttributeNodeStyle':
                        self.attributes.append(current[0])
                    elif current[1] == 'RelationNodeStyle':
                        self.relations.append(current[0])
                    else:

                        raise ExceptionCase(
                            'Error [2]: During BuildDictionaries/parse, found something that was not an entity, relation, or attribute.')

            # Second: all edges between nodes: {publish|paper=RelationEdge, Course|Rating=AttributeEdge}
            elif line[:5] == 'Edges':

                # Get the items between the { }
                edges = line[line.find('{') + 1:line.find('}')].replace(',', '').split()

                for edge in edges:

                    current = edge.split('=')
                    if current[1] == 'AttributeEdge':
                        current = current[0].split('|')
                        if current[0] in self.attributes:
                            self.attribute_dict[current[0]] = current[1]
                        elif current[1] in self.attributes:
                            self.attribute_dict[current[1]] = current[0]

                    '''
                    if current[1] == 'RelationEdge':
                        current = current[0].split('|')

                        if current[0] in self.entities:
                            # do stuff
                            continue
                        if current[1] in self.entities:
                            # do stuff
                            continue
                        if current[0] in self.relations:
                            # do stuff
                            continue
                        if current[1] in self.relations:
                            # do stuf
                            continue
                    '''

                    current = edge.split('=')[0].split('|')  # 'publish|paper=RelationEdge'

                    # Rebuild the Graph

                    src = current[0]
                    dest = current[1]

                    if src in self.Graph:
                        self.Graph[src].append(dest)
                    else:
                        self.Graph[src] = [dest]

                    if dest in self.Graph:
                        self.Graph[dest].append(src)
                    else:
                        self.Graph[dest] = [src]

            elif line[:9] == 'Important':

                self.importants = line[line.find('[') + 1:line.find(']')].replace(' ', '').split(',')

            elif line[:6] == 'Target':

                self.target = line.replace(' ', '').split(':')[1]

            # There are some problems with this, the order they appear is not always
            # consistent with how they need to be ordered. (Look at the order of edges instead)
            elif line[:15] == 'RelatedEntities':

                relations = line[line.find('{') + 1:line.find('}')].replace(' ', '')
                relations = [item.replace('[', '').replace(']', '') for item in relations.split('],')]

                for relation in relations:
                    current = relation.split('=')
                    self.relations_dict[current[0]] = current[1].split(',')

            elif line[:22] == 'AttributeEntityMapping':
                # handle multivalue attributes

                multi_value_attributes = line[line.find('{') + 1:line.find('}')].replace(' ', '')
                multi_value_attributes = [item.replace('[', '').replace(']', '') for item in
                                          multi_value_attributes.split(']')]

                for attr in multi_value_attributes:
                    current = attr.split('=')
                    if len(current) == 2:
                        if ',' in current[1]:
                            # print(current)
                            self.multi_value_attributes[current[0].replace(',', '')] = current[1].split(',')

            else:
                raise ExceptionCase('Error: did not recognize an item in the diagram file: ' + str(line))

        if self.verbose:
            print('Entities:', self.entities)
            print('Graph:', self.Graph)
            print('Relations:', self.relations_dict)
            print('Attributes:', self.attribute_dict)
            print('Multi-Value Attributes:', self.multi_value_attributes)
            print('Important:', self.importants)
            print('Target:', self.target)



class BuildDictionariesFromDOT(BuildDictionaries):
    ENTITY_SHAPE = '\"box\"'
    RELATION_SHAPE = '\"polygon\"'
    ATTRIBUTE_SHAPE = '\"ellipse\"'
    IMPORTANT_COLOR = '\"red\"'
    TARGET_COLOR = '\"cyan\"'
    TARGET_COLOR_BK = '\"blue\"'
    EG_NODE_IGNORE  = 'node'
    EG_EDGE_IGNORE = 'edge'
    ATTRIBUTE_EDGE = '\"blue\"'
    TARGET_FONT_COLOR = '\"black\"'

    def __init__(self, diagram, verbose=False):
        self.verbose = verbose
        self.diagram = diagram
        '''Takes the dot graph as input'''
        self.entities = []
        self.importants = []
        self.relations = []
        self.attributes = []
        self.Graph = {}
        self.target=None
        self.relations_dict = {}
        self.attribute_dict = {}
        self.multi_value_attributes = {}


        for n in diagram.get_nodes():
            if n.get_name() == self.EG_NODE_IGNORE or n.get_name() == self.EG_EDGE_IGNORE:
                continue
            if n.get_shape() == self.ENTITY_SHAPE:
                self.entities.append(remove_double_quote(n.get_name()))
            elif n.get_shape() == self.RELATION_SHAPE:
                self.relations.append(remove_double_quote(n.get_name()))
            else:
                self.attributes.append(remove_double_quote(n.get_name()))
                if n.get_peripheries():
                    self.multi_value_attributes[remove_double_quote(n.get_name())] = list()

            if n.get_fillcolor() == self.IMPORTANT_COLOR:
                self.importants.append(remove_double_quote(n.get_name()))
            elif n.get_fillcolor() == self.TARGET_COLOR:
                self.target = remove_double_quote(n.get_name())
            elif n.get_fillcolor() == self.TARGET_COLOR_BK:
                self.target = remove_double_quote(n.get_name())
        for edge in diagram.get_edges():
            src = remove_double_quote(edge.get_source())
            dest = remove_double_quote(edge.get_destination())
            if edge.get_color() == self.ATTRIBUTE_EDGE:
                self.attribute_dict[src] = remove_double_quote(dest)
                if src in self.multi_value_attributes.keys():
                    self.multi_value_attributes[src] = [dest,src]
            if src in self.Graph:
                self.Graph[src].append(dest)
            else:
                self.Graph[src] = [dest]
            if dest in self.Graph:
                self.Graph[dest].append(src)
            else:
                self.Graph[dest] = [src]
                # IF Relation is destination add it in relations_dict with 1st attribute.
            if diagram.get_node(edge.get_destination())[0].get_shape() == self.RELATION_SHAPE:
                if dest in self.relations_dict:
                    self.relations_dict[dest].append(src)
                else:
                    self.relations_dict[dest] =  [src]
        for edge in diagram.obj_dict['edges'].keys():
            src= remove_double_quote(edge[0])
            if remove_double_quote(edge[0]) in self.relations_dict:
                dest = remove_double_quote(edge[1])
                if dest not in self.relations_dict[src]:
                    self.relations_dict[src].append(dest)

        if self.verbose:
            print('Entities:', self.entities)
            print('Graph:', self.Graph)
            print('Relations:', self.relations_dict)
            print('Attributes:', self.attribute_dict)
            print('Multi-Value Attributes:', self.multi_value_attributes)
            print('Important:', self.importants)
            print('Target:', self.target)



class Networks:

    def __init__(self, target, features, dictionaries, verbose=False):
        self.verbose = verbose
        self.entities = dictionaries.entities
        self.relations = dictionaries.relations
        self.attributes = dictionaries.attributes
        self.multi_value_attributes = dictionaries.multi_value_attributes
        self.importants = features
        self.target = target
        self.Graph = dictionaries.Graph
        self.relations_dict = dictionaries.relations_dict
        self.attribute_dict = dictionaries.attribute_dict

        if self.verbose:
            print('\nWalk Mode:')

    def find_all_paths(self, graph, start, end, path=[]):
        # https://www.python.org/doc/essays/graphs/
        path = path + [start]
        if start == end:
            return [path]
        if start not in graph:
            # if not graph.has_key(start):
            return []
        paths = []
        for node in graph[start]:
            if node not in path:
                newpaths = self.find_all_paths(graph, node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths

    def random_walk(self, graph, start, depth):
        path = [start]

        # Randomly walk to nodes in the graph while length is less than maximum depth.
        while len(path) < depth:
            current_node = graph[start]
            next_node = random.choice(current_node)

            path.append(next_node)
            start = next_node

        # If we walk to an entity, pop items off the stack and put the entity on the stack.
        # Instantiate -/+ based on what is currently on the stack.
        stack = []
        final_set = []

        # Add the target to the final_set:
        if self.target in self.attribute_dict:
            final_set.append(self.target + '(+' + self.attribute_dict[self.target] + ').')
        elif self.target in self.relations_dict:
            if (len(self.relations_dict[self.target]) == 1):
                # Reflexive
                final_set.append(
                    self.target + '(+' + self.relations_dict[self.target][0] + ',+' + self.relations_dict[self.target][
                        0] + ').')
            else:
                final_set.append(self.target + '(+' + ',+'.join(self.relations_dict[self.target]) + ').')

        # Handle everything that occurs after that target
        path = path[1:]
        for node in path:
            if node in self.entities:
                stack = [node]
            elif node in self.relations:
                out = []
                if (len(self.relations_dict[node]) == 1):
                    # Reflexive.
                    out.append("+%s" % self.relations_dict[node][0])
                    out.append("-%s" % self.relations_dict[node][0])
                    final_set.append(node + '(' + ','.join(out) + ').')
                    outrev = reversed(out)
                    final_set.append(node + '(' + ','.join(outrev) + ').')
                else:
                    # Not reflexive.
                    for var in self.relations_dict[node]:
                        if var in stack:
                            out.append("+%s" % var)
                        else:
                            out.append("-%s" % var)
                    final_set.append(node + '(' + ','.join(out) + ').')
            # I'm skipping attributes because they'll be instantiated with + regardless of whether they're explored or not.

        # Instantiate '+' for nodes that were not explored when walking.
        unexplored = list((set(self.relations_dict.keys()) - set(path)).union(set(self.attribute_dict.keys())))

        for predicate in unexplored:
            if predicate in self.attribute_dict:

                # Note: multivalued attributes need to be handled as #, while non-multivalued need nothing.
                if predicate in self.multi_value_attributes:
                    multi = ',#' + predicate.lower()
                else:
                    multi = ''

                final_set.append(str(predicate +
                                     '(+' + self.attribute_dict[predicate] + multi +
                                     ').'))

            elif predicate in self.relations_dict:
                out = []

                variables = self.relations_dict[predicate]
                # reverse the order of the variables for correct predicate logic format:
                # variables = list(reversed(variables))

                for var in variables:
                    out.append("+%s" % var)
                    # A small fix for reflexive relationships:
                    if len(variables) == 1:
                        out.append("+%s" % var)
                final_set.append(str(predicate + '(' + ','.join(out) + ').'))

        self.all_modes = ['mode: ' + element for element in sorted(list(set(final_set)))]
        # print('\n//background')
        # print('//target is', target)
        # for mode in self.all_modes:
        #    print(mode)

        return path

    def paths_from_target_to_features(self):
        graph = self.Graph
        all_paths = []
        if self.verbose:
            print('\nAll paths from target to features:')
        for feature in self.importants:
            p = self.find_all_paths(graph, self.target, feature)
            all_paths.append(p)
        return all_paths

    def path_powerset(self, graph):
        pass

    def walkFeatures(self, all_paths, shortest=False):
        '''
        Use user-selected features to construct background/modes.
        Input: [target], [list of features]
        Output: (print modes to terminal or write to a file)
        '''
        graph = self.Graph
        target = self.target
        features = self.importants

        # First, instantiate entity variables that appear in the target.
        if target in self.attribute_dict:
            target_variables = [self.attribute_dict[target]]
        elif target in self.relations_dict:
            target_variables = self.relations_dict[target]
        # print(target_variables)

        final_set = []

        if shortest:
            # Prefer the shortest paths between the target and features.
            new_all_paths = []
            for lsa in all_paths:
                shortest_len = min([len(x) for x in lsa])
                new_all_paths.append([y for y in lsa if len(y) == shortest_len])
            all_paths = new_all_paths

        merged = list(itertools.chain(*all_paths))
        merged = list(itertools.chain(*merged))

        # Some predicates will not be explored, store them in a list.
        unexplored = list(set(self.relations_dict.keys()).union(set(self.attribute_dict.keys())) - set(merged))

        if self.verbose:
            print('\nTarget and Features:', str(target), str(features))
            print('Predicates explored by walking:', str(list(set(merged))))
            print('Predicates not explored by walking:', str(unexplored))

        for lsa in all_paths:
            for lsb in lsa:

                instantiated_variables = set(target_variables)
                for predicate in lsb:
                    if predicate in self.attribute_dict:
                        out = []

                        # Note: multivalued attributes need to be handled as #, while non-multivalued need nothing.
                        if predicate in self.multi_value_attributes:
                            multi = ',#' + predicate.lower()
                        else:
                            multi = ''

                        if self.attribute_dict[predicate] in instantiated_variables:
                            out.append("+%s" % self.attribute_dict[predicate])
                        else:
                            out.append("-%s" % self.attribute_dict[predicate])
                        final_set.append(str(predicate +
                                             '(' + ','.join(out) +
                                             multi + ').'))
                        instantiated_variables = instantiated_variables.union(set(self.attribute_dict[predicate]))

                    elif predicate in self.relations_dict:
                        # Note: needs a check for whether the relationship is reflexive. (e.g. FatherOf Relationship)
                        REFLEXIVE = False
                        out = []

                        variables = self.relations_dict[predicate]
                        # reverse the order of the variables for correct predicate logic format:
                        # variables = list(reversed(variables))

                        for var in variables:
                            if var in instantiated_variables:
                                out.append("+%s" % var)
                            else:
                                out.append("-%s" % var)

                        if len(variables) == 1:
                            REFLEXIVE = True
                            if (predicate == target):
                                out.append("+%s" % var)
                            else:
                                out.append("-%s" % var)
                        final_set.append(str(predicate + '(' + ','.join(out) + ').'))

                        if REFLEXIVE:
                            outrev = list(reversed(out))
                            final_set.append(str(predicate + '(' + ','.join(outrev) + ').'))

                        instantiated_variables = instantiated_variables.union(set(self.relations_dict[predicate]))

                    else:
                        # Predicate is an entity and we can skip it.
                        continue

        # Handle "Unexplored" attributes, relations, and entities
        for predicate in unexplored:
            if predicate in self.attribute_dict:

                # Note: multivalued attributes need to be handled as #, while non-multivalued need nothing.
                if predicate in self.multi_value_attributes:
                    multi = ',#' + predicate.lower()
                else:
                    multi = ''

                final_set.append(str(predicate +
                                     '(+' + self.attribute_dict[predicate] + multi +
                                     ').'))

            elif predicate in self.relations_dict:
                out = []

                variables = self.relations_dict[predicate]
                # reverse the order of the variables for correct predicate logic format:
                # variables = list(reversed(variables))

                for var in variables:
                    out.append("+%s" % var)
                    # A small fix for reflexive relationships:
                    if len(variables) == 1:
                        out.append("+%s" % var)
                final_set.append(str(predicate + '(' + ','.join(out) + ').'))

        self.all_modes = ['mode: ' + element for element in sorted(list(set(final_set)))]
        self.all_modes_boostsrl = [element for element in sorted(list(set(final_set)))]
        # print('\n//background')
        # print('//target is', target)
        # for mode in self.all_modes:
        #    print(mode)

class UnitTests:

    def __init__(self):
        pass

    def run_unit_tests(self):
        pass

class walker:

    """
    "Main" class to run WalkER with the assumption that it was imported as a package.
        - diagram_file -> a string
        - method -> a string
    """

    def __init__(self, diagram_file_string, algo, shortest=False, verbose=False, n=10000):
        pass

if __name__ == '__main__':

    '''Parse the commandline input, import the file. Contents are stored in setup.diagram_file.'''
    setup = Setup()
    diagram = setup.diagram

    '''Turn turn the file into dictionaries and lists.'''
    if setup.dot:

        dictionaries = BuildDictionariesFromDOT(diagram , verbose=setup.verbose)
    else:
        dictionaries = BuildDictionaries(diagram, verbose=setup.verbose)

    if (setup.walk or setup.shortest):
        target = dictionaries.target
        all_features = list(set(dictionaries.relations).union(set(dictionaries.attributes)) - set([target]))

        if (setup.Nfeatures == None):
            features = dictionaries.importants
        elif (setup.Nfeatures > len(dictionaries.importants)):
            features = dictionaries.importants
        else:
            features = dictionaries.importants[:setup.Nfeatures]

        networks = Networks(target, features, dictionaries, verbose=setup.verbose)

        all_paths = networks.paths_from_target_to_features()

        if setup.shortest:
            networks.walkFeatures(all_paths, shortest=True)
        else:
            networks.walkFeatures(all_paths)

    elif (setup.random or setup.exhaustive):
        # User-selected target
        target = dictionaries.target
        # Features not including the target
        #all_features = list(set(dictionaries.Graph.keys()) - set([target]))
        all_features = list(set(dictionaries.relations).union(set(dictionaries.attributes)) - set([target]))
        # Select a random set of features from all_features

        if setup.random:
            print('"Random Mode": Ignore features the user selected and walk from the target to random features.')

            if (setup.Nfeatures == None):
                features = random.sample(all_features, random.randint(1, len(all_features)))
            elif (setup.Nfeatures > len(all_features)):
                features = random.sample(all_features, len(all_features))
            else:
                features = random.sample(all_features, setup.Nfeatures)

            print(features, '/', all_features)

        elif setup.exhaustive:
            print('"Exhaustive Mode": Walk the graph from the target to every feature.')
            features = all_features

        networks = Networks(target, features, dictionaries, verbose=setup.verbose)
        all_paths = networks.paths_from_target_to_features()
        networks.walkFeatures(all_paths)

    elif setup.randomwalk:
        print('"Random Walk Mode": Randomly choose the next node to walk to.')

        target = dictionaries.target
        features = []
        Graph = dictionaries.Graph

        networks = Networks(target, features, dictionaries, verbose=setup.verbose)

        if (setup.Nfeatures == None):
            print('Warning: depth limit was not specified (use --number), defaulting to 10,000 [Exhaustive Search].')
            depth_limit = 10000
        else:
            depth_limit = setup.Nfeatures

        path = networks.random_walk(Graph, target, depth_limit)


    elif setup.nowalk:
        print('"No-Walk Mode": Instantiate variables without walking.')
        print('This is not currently implemented.')

    print('//target is', networks.target)
    for mode in networks.all_modes:
        print(mode)
