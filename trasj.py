
        # self.diagonal_path(top)
        # curr = ArrayBuilder.get_hierarchical_root(context.top, Position(7, 7),corner = 3)

        # for x in range(top.width):   
        #     for y in range(top.height):
        #         print(x,y)
        #         print(ArrayBuilder.get_hierarchical_root(context.top, Position(x, y),corner = 0))
        #         print(ArrayBuilder.get_hierarchical_root(context.top, Position(x, y),corner = 1))
        #         print(ArrayBuilder.get_hierarchical_root(context.top, Position(x, y),corner = 2))
        #         print(ArrayBuilder.get_hierarchical_root(context.top, Position(x, y),corner = 3))
        #         print(ArrayBuilder.get_hierarchical_root(context.top, Position(x, y)))
        #         print()
        tile_66 = [ArrayBuilder.get_hierarchical_root(top, Position(6,6),corner = 0),ArrayBuilder.get_hierarchical_root(top, Position(6,6),corner = 2),
                    ArrayBuilder.get_hierarchical_root(top, Position(6,6),corner = 1),ArrayBuilder.get_hierarchical_root(top, Position(6,6),corner = 3),
                    ArrayBuilder.get_hierarchical_root(top, Position(6,6))]
        tile_55 = [ArrayBuilder.get_hierarchical_root(top, Position(5,5),corner = 0),ArrayBuilder.get_hierarchical_root(top, Position(5,5),corner = 2),
                    ArrayBuilder.get_hierarchical_root(top, Position(5,5),corner = 1),ArrayBuilder.get_hierarchical_root(top, Position(5,5),corner = 3),
                    ArrayBuilder.get_hierarchical_root(top, Position(5,5))]
        tile_64 = [ArrayBuilder.get_hierarchical_root(top, Position(6,4),corner = 0),ArrayBuilder.get_hierarchical_root(top, Position(6,4),corner = 2),
                    ArrayBuilder.get_hierarchical_root(top, Position(6,4),corner = 1),ArrayBuilder.get_hierarchical_root(top, Position(6,4),corner = 3),
                    ArrayBuilder.get_hierarchical_root(top, Position(6,4))]
        while None in tile_66:
            tile_66.remove(None)
        while None in tile_55:
            tile_55.remove(None)
        while None in tile_64:
            tile_64.remove(None)    

        tile_66_pins = []
        tile_55_pins = []
        tile_64_pins = []
        for x in tile_66:
            for k,v in iteritems(x.pins):
                if v.model.direction.is_input and not v.is_clock:
                    for net in v:
                        tile_66_pins.append(NetUtils._reference(net))
                        # print(net)
        # print()

        for x in tile_55:
            for k,v in iteritems(x.pins):
                if v.model.direction.is_output and not v.is_clock:
                    for net in v:
                        tile_55_pins.append(NetUtils._reference(net))
        
        for x in tile_64:
            for k,v in iteritems(x.pins):
                if v.model.direction.is_output and not v.is_clock:
                    for net in v:
                        tile_64_pins.append(NetUtils._reference(net))
                        # print(net)
        
        G = self.graphs['top']['graph']
        # for x in G.nodes:
        #     print(NetUtils._dereference(top, x))
        # print(tile_64_pins[1])
        # print(len(tile_64_pins[1]))
        for node in G.nodes:
            print("NODE",NetUtils._dereference(top, node))
            for x in nx.shortest_path(G,source=node):
                print(NetUtils._dereference(top, x))
            print()

        # for u,v in G.edges:
        #     print(NetUtils._dereference(top, u),NetUtils._dereference(top, v))
        # for src in tile_55_pins:
        #     for sink in tile_66_pins:
        #         # try:
        #         print(nx.has_path(G, source=src,target=sink))
        #         # except:
        #         #     x=0+0
        #     print()