import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            new_domain = self.domains[var].copy()
            for x in self.domains[var]:
                if len(x) != var.length:
                    new_domain.remove(x)
            self.domains[var] = new_domain


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        if (x, y) in self.crossword.overlaps and self.crossword.overlaps[x, y] is not None:
            intersection = self.crossword.overlaps[x, y]
            y_char = []
            new_domain = self.domains[x].copy()
            for word in self.domains[y]:
                y_char.append(word[intersection[1]])
            for word in self.domains[x]:
                if word[intersection[0]] not in y_char:
                    new_domain.remove(word)
            self.domains[x] = new_domain    
            return False
        return True


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = []
        for var in self.domains:
           if self.crossword.neighbors(var):
                edge = self.crossword.neighbors(var)
                edge1 = list(edge)
                for i in range(len(edge)):
                    queue.append(edge1[i])
                while len(queue) > 0:
                    x = var
                    y = queue[0]
                    if self.revise(x, y):
                        if len(self.domains[var]) == 0:
                            return False
                    queue.remove(y)
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        is_complete =  True
        if len(assignment) != len(self.domains):
            is_complete = False
        for row in assignment:
            if len(assignment[row]) != 1:
                is_complete = False
        return is_complete

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        is_consistent = True
        values = []
        variables = []
        for row in assignment:
            values.append(assignment[row])
            if row.length != len(assignment[row]):
                is_consistent = False

        set_values = set()
        for x in values:
            if x in set_values:
                is_consistent = False
            else:
                set_values.add(x)

        for row1 in assignment:
            for row2 in assignment:
                if (row1, row2) in self.crossword.overlaps and self.crossword.overlaps[row1, row2] is not None:
                    word1 = assignment[row1]
                    word2 = assignment[row2]
                    a = self.crossword.overlaps[row1, row2]
                    if word1[a[0]] != word2[a[1]]:
                        is_consistent = False
                                

        return is_consistent
            
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Need to add LCV heuristic
        possible_words = []
        ranked_words = []
        lcv_words = []
        for word in self.domains[var]:
            possible_words.append(word)
        neighb = self.crossword.neighbors(var)
        for x in neighb:
            if self.crossword.overlaps[var, neighb] is not None:
                intersection = self.crossword.overlaps[var, neighb]
                for i in range(len(possible_words)):
                    for word2 in self.domains[neighb]:
                        count = 0
                        word1 = possible_words[i]
                        if word1[intersection[0]] != word2[intersection[1]]:
                            count += 1
                    rank = (possible_words[i], count)
                    ranked_words.append(rank)
        ranked_words = sorted(ranked_words, key = lambda x: x[1])
        for i in range(ranked_words):
            lcv_words.append(ranked_words[0])
        return lcv_words


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        mrv = []
        mrv_dict = {}
        for var in self.domains:
            pair = (var, self.domains[var])
            mrv.append(pair)
            mrv = sorted(mrv, key=lambda x: x[1])
            for i in range(len(mrv) - 1):
                if mrv[i][1] == mrv[i + 1][1]:
                    x = mrv[i][0]
                    y = mrv[i + 1][0]
                    x_neighb = self.crossword.neighbors(x)
                    y_neighb = self.crossword.neighbor(y)
                    if len(y_neighb) > len(x_neighb):
                        a = mrv[i + 1]
                        mrv[i + 1] = mrv[i]
                        mrv[i] = a
            for i in range(len(mrv)):
                mrv_dict[mrv[i][0]] = mrv[i][1]
            for var in mrv_dict:        
                if var not in assignment:
                    return var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if len(assignment) == len(self.domains):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.domains[var]:
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if self.consistent(new_assignment):
                result = self.backtrack(new_assignment)
                if result is not None:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
