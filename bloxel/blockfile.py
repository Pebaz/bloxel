import random

class BlockFile:
    """
    For batch processing of an entire texture map into many scalar bloxels.
    
    Not to be confused with a way to store the individual cornerstones that
    make up a given composite block.
    """

    def __init__(self, filename, num_across, num_down):
        self.num_across = num_across
        self.num_down = num_down
        self.total = num_across * num_down
        self.coordinates = dict()
        self.num_instructions = self.load(filename)

    def get_all(self):
        for name in self.coordinates:
            yield name, self.coordinates[name]

    def load(self, filename):
        """
        Obtain the texture index and name from each line in the blockfile.
        """

        characters = (
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '1234567890'
        )
        invalid = '^%$#@!~`()[]\{\}*&+=?><,\'\"'

        # TODO: Validate based on texture index (is it inside 16x16?)
        # TODO: Validate 1-6 numbers, but not more
        # TODO: Validate index has to be less than across * down
        # TODO: Everything minus one space after the # is the filename
        # TODO: Trello comment parser?

        #parser = parse.OneOrMore(parse.nums) + parse.Keyword('#') + parse.Word(parse.alphanums + '_-.') + parse.lineEnd
        
        with open(filename) as file:
            count = 0
            for line in file:
                count += 1

                # Named bloxel
                if '#' in line:
                    indexes, name = line.split('#')
                    name = name.strip()

                # Unnamed bloxel
                else:
                    indexes, name = line, ''

                # Parse out indexes
                indexes = [int(i.strip()) for i in indexes.split(' ') if i]

                # Validate here

                if name != '':
                    if any(i in name for i in invalid):
                        raise Exception(
                            f'Instruction on line {count} in "{filename}" '
                            f'has an invalid block name that contains one of: '
                            f'{invalid}'
                        )
                else:
                    name = ''.join(
                        [random.choice(characters) for i in range(8)]
                    )

                for coor in indexes:
                    if coor >= self.total:
                        raise Exception(
                            f'Instruction on line {count} in "{filename}" '
                            'contains index that lies outside texture bounds.'
                        )

                # Now identify the X/Y texture that they are
                
                indexes = [
                    (i % self.num_across, i // self.num_down)
                    for i in indexes
                ]
                
                self.coordinates[name] = indexes
        return count
