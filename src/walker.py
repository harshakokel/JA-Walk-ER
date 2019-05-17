from DEUtils import remove_double_quote
import itertools

import random

class BuildDictionaries:
    ENTITY_SHAPE = '\"box\"'
    RELATION_SHAPE = '\"polygon\"'
    ATTRIBUTE_SHAPE = '\"ellipse\"'
    IMPORTANT_COLOR = '\"red\"'
    TARGET_COLOR = '\"blue\"'
    EG_NODE_IGNORE  = 'node'
    EG_EDGE_IGNORE = 'edge'
    ATTRIBUTE_EDGE = '\"blue\"'
    WHITE = '\"white\"'

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
