import warnings
from itertools import combinations

class CFG:
	"""
	A class to represent a Context-Free Grammar (CFG) and provide methods to work with it.
	"""
	
	EPSILON = 'ε'

	def __init__(self, rules: dict, start_symbol: str|None=None) -> None:
		"""
		Initializes the CKY parser with a given Context-Free Grammar (CFG).

		The CFG is stored in Chomsky Normal Form (CNF) internally, so the rules are converted to CNF if they are not already in CNF.

		The symbols must be single characters (strings of length 1): uppercase for non-terminal symbols and lowercase for terminal symbols.

		Parameters
		----------
		rules (dict): A dictionary of rules in the form of {Symbol: [Production1, Production2, ...], ...}.
		start_symbol (str, optional): The start symbol of the grammar. 
			If not provided, the first symbol is inferred checking all the productions generated by each symbol.
		"""
		self.rules: dict = rules

		self.assert_valid_format()
		self.replace_epsilon()

		self.terminals, self.non_terminals = self.find_symbols(start_symbol=start_symbol)

		self.start_symbol: str = start_symbol if start_symbol is not None else self.find_start_symbol()

		self.available_non_terminals = sorted(list(set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - self.non_terminals), reverse=True)

		print("Initial CFG:", self)

		if not self.check_cnf():
			warnings.warn("The provided CFG is not in CNF. Converting to CNF. Some productions and symbols may change.", UserWarning)
			self.to_cnf()

	def __call__(self, symbol: str) -> list:
		"""
		Allows the CFG object to be called as a function to get the productions for a given symbol.

		Parameters
		----------
		symbol (str): The symbol for which to get the productions.

		Returns
		-------
		list
			List of productions for the given symbol.
		"""
		return self.get_productions(symbol)
	
	def assert_valid_format(self) -> None:
		"""
		Asserts that the format of the grammar is valid.

		The grammar must be in the form of a dictionary with the keys as symbols and the values as lists of productions.
		Each symbol must be a string and each production must be a string of symbols.

		Raises
		------
		ValueError
			If the grammar is not in the correct format.
		"""
		if not isinstance(self.rules, dict):
			raise ValueError("The grammar must be provided as a dictionary of rules in the form of {Symbol: [Production1, Production2, ...], ...}.")
		
		for symbol, productions in self.rules.items():
			if not isinstance(symbol, str):
				raise ValueError("All symbols must be strings.")
			if len(symbol) != 1:
				raise ValueError("All symbols must be single characters (strings of length 1).")
			
			if not isinstance(productions, list|set|tuple):
				raise ValueError("The set of productions for each symbol must be a list, set, or tuple of strings.")
			
			for production in productions:
				if not isinstance(production, str):
					raise ValueError("All individual productions must be strings.")

	def replace_epsilon(self) -> None:
		"""
		Replaces empty strings with the epsilon symbol (ε) in the grammar rules.
		"""
		for symbol, productions in self.rules.items():
			self.rules[symbol] = [prod if prod else self.EPSILON for prod in productions]

	def find_symbols(self, start_symbol: str|None) -> tuple[set, set]:
		"""
		Finds the terminal and non-terminal symbols in the grammar, checks if they are in the correct format, and returns them.

		The terminal symbols are the ones that are only produced and never produce any other symbol,
		while the non-terminal symbols are the ones that produce other symbols and can be produced by other symbols.

		Parameters
		----------
		start_symbol (str, None): The start symbol specified by the user.

		Returns
		-------
		tuple[set, set]
			A tuple containing the terminal and non-terminal symbols.

		Raises
		------
		ValueError
			If the terminal symbols are not lowercase or the non-terminal symbols are not uppercase.
		ValueError
			If there are symbols that produce other symbols but are not produced by any other symbol (cannot be reached).
		"""
		non_terminals = set(char for char in self.rules.keys())

		if any(not symbol.isupper() for symbol in non_terminals):
			raise ValueError("The grammar is not correct. All non-terminal symbols must be uppercase.")

		terminals = set()
		for productions in self.rules.values():
			for production in productions:
				for char in production:
					if char not in non_terminals:
						terminals.add(char)

		if any(not symbol.islower() for symbol in terminals):
			raise ValueError("The grammar is not correct. All terminal symbols must be lowercase.")

		if start_symbol is not None:
			if non_terminals - self.__get_reachable_non_terminals(start_symbol=start_symbol, non_terminals=non_terminals):
				raise ValueError("The grammar is not correct. Some symbols produce other symbols but are not produced by any other symbol (cannot be reached).")

		return terminals, non_terminals
	
	def find_start_symbol(self) -> str:
		"""
		Finds the start symbol of the grammar.

		Returns
		-------
		str
			The start symbol of the grammar.

		Raises
		------
		ValueError
			If the start symbol cannot be inferred from the grammar rules.
		"""
		produced_symbols = set()
		for productions in self.rules.values():
			for production in productions:
				for char in production:
					produced_symbols.add(char)

		candidates = self.non_terminals - produced_symbols

		if not candidates or len(candidates) > 1:
			raise ValueError("Could not infer the start symbol, more than 1 candidate found. Please provide the start symbol explicitly and ensure that the grammar is correct.")

		start_symbol = candidates.pop() # Get the non-terminal symbol that is not produced by any other symbol

		return start_symbol
	
	def check_cnf(self) -> bool:
		"""
		Checks if the grammar is in Chomsky Normal Form (CNF).

		A CFG is in CNF if all its rules are of the form:
		- A -> a, where A is a non-terminal symbol and a is a terminal symbol.
		- A -> BC, where A, B, and C are non-terminal symbols.

		Returns
		-------
		bool
			True if the grammar is in CNF, False otherwise.
		"""
		for symbol, productions in self.rules.items():
			for production in productions:
				if len(production) == 1:
					if not self.is_terminal(production):
						return False
				
				elif len(production) == 2:
					if any(not self.is_non_terminal(char) for char in production):
						return False
				
				else:
					return False
		
		return True
	
	def to_cnf(self) -> None:
		"""
		Converts the grammar to Chomsky Normal Form (CNF).

		A CFG is in CNF if all its rules are of the form:
		- A -> a, where A is a non-terminal symbol and a is a terminal symbol.
		- A -> BC, where A, B, and C are non-terminal symbols.
		"""
		self.create_new_start_symbol()
		self.remove_null_productions()
		self.remove_unit_productions()
		self.__remove_unreachable_productions()
		self.convert_to_binary_and_terminal_productions()

		print("Converted to CNF:", self)

		try:
			self.assert_valid_format()
		except ValueError:
			raise ValueError("The CFG could not be converted to CNF. Please check the grammar and try again.")
		self.replace_epsilon()

		self.terminals, self.non_terminals = self.find_symbols(start_symbol=self.start_symbol)
		self.start_symbol = self.find_start_symbol()

	def create_new_start_symbol(self) -> None:
		"""
		Step 1 to convert CFG to CNF: 
		Creates a new symbol that only produces the original start symbol and adds it to the grammar rules.
		"""
		new_start_symbol = self.create_non_terminal()
		self.rules[new_start_symbol] = [self.start_symbol]
		self.non_terminals.add(new_start_symbol)

	def remove_null_productions(self) -> None:
		"""
		Step 2 to convert CFG to CNF: 
		Identify all nullable non-terminals (non-terminals that derive epsilon). 
		Remove the null productions and adjust other productions accordingly.
		"""
		if self.EPSILON in self.terminals:

			self.is_nullable_dict = {}

			# Find all nullable symbols and remove the epsilon from the productions
			nullable = self.__get_nullable_symbols()
			# non_nullable = self.non_terminals - nullable

			new_rules = {}

			# Add all combinations of nullable symbols to the productions of the non-nullable symbols
			for symbol in self.non_terminals:
				new_productions = set()
				productions = self.rules[symbol]
				for production in productions:
					if production != self.EPSILON:
						new_productions.add(production)
						nullable_positions = [i for i, char in enumerate(production) if char in nullable]
						for i in range(1, len(nullable_positions) + 1):
							for combination in combinations(nullable_positions, i):
								new_production = ''.join(
									char for idx, char in enumerate(production) if idx not in combination
								)
								if new_production:
									new_productions.add(new_production)
				new_rules[symbol] = list(new_productions)

			self.terminals.remove(self.EPSILON)

			self.rules = new_rules

	def __get_nullable_symbols(self):
		"""
		Identifies all nullable symbols (non-terminals that derive epsilon).
		"""
		nullable = set()
		changed = True

		while changed:
			changed = False
			for nt in self.non_terminals:
				if nt not in nullable:
					for production in self.rules[nt]:
						if all(char in nullable or char == self.EPSILON for char in production):
							nullable.add(nt)
							changed = True
							break
		return nullable

	def remove_unit_productions(self) -> None:
		"""
		Step 3 to convert CFG to CNF: 
		Remove all unit productions from the grammar.
		"""
		new_rules = {nt: set() for nt in self.non_terminals}

		# Step 1: Propagate rules
		for nt in self.non_terminals:
			to_process = [nt]
			visited = set()
			while to_process:
				current = to_process.pop()
				if current in visited:
					continue
				visited.add(current)
				for production in self.rules[current]:
					if len(production) == 1 and production in self.non_terminals:
						to_process.append(production)
					else:
						new_rules[nt].add(production)

		# Step 2: Remove unit productions that map a non-terminal to another non-terminal
		for nt in self.non_terminals:
			new_rules[nt] = {prod for prod in new_rules[nt] if not (len(prod) == 1 and prod in self.non_terminals)}

		self.rules = {nt: list(productions) for nt, productions in new_rules.items()}

	def __remove_unreachable_productions(self) -> None:
		"""
		Step 4 to convert CFG to CNF:
		Remove all unreachable productions from the grammar.
		"""
		reachable = self.__get_reachable_non_terminals(start_symbol=self.start_symbol, non_terminals=self.non_terminals)
		self.rules = {nt: prods for nt, prods in self.rules.items() if nt in reachable}
		self.non_terminals = reachable

	def __get_reachable_non_terminals(self, start_symbol: str, non_terminals: set):
		"""
		Identifies all reachable non-terminals in the grammar.

		Parameters
		----------
		start_symbol (str): The start symbol of the grammar.
		non_terminals (set): The set of non-terminal symbols in the grammar.

		Returns
		-------
		set
			Set of reachable non-terminal symbols.
		"""
		reachable = set()
		to_process = [start_symbol]
		while to_process:
			current = to_process.pop()
			if current not in reachable:
				reachable.add(current)
				for production in self.rules.get(current, []):
					for symbol in production:
						if symbol in non_terminals:
							to_process.append(symbol)
		return reachable

	def convert_to_binary_and_terminal_productions(self) -> None:
		"""
		Step 5 to convert CFG to CNF:
		Convert all productions to binary and terminal productions.
		"""
		self.__convert_long_productions()
		self.__convert_binary_productions()

	def __convert_long_productions(self):
		"""
		Converts long productions to binary productions.
		"""
		new_rules = {}

		for symbol, productions in self.rules.items():
			new_productions = set()
			for production in productions:
				if len(production) <= 2:
					new_productions.add(production)
				else:
					while len(production) > 2:		
						new_production = ''

						# Split long production into binary productions
						production_pairs = [production[i:i+2] for i in range(0, len(production), 2)] # The last pair may have a single symbol if the length is odd

						# Create new non-terminal symbols for the pairs
						for pair in production_pairs:
							if len(pair) == 1:
								new_production += pair
							else:
								new_nt = self.get_or_create_non_terminal([pair], rules=new_rules)
								new_production += new_nt

								new_rules[new_nt] = [pair]

						# Update the production to the new production
						production = new_production

					new_productions.add(new_production)

			new_rules[symbol] = list(new_productions)

		self.rules = new_rules

	def __convert_binary_productions(self):
		"""
		Converts binary productions with terminals to binary productions with non-terminals.
		"""
		new_rules = {}
		for symbol, productions in self.rules.items():
			updated_productions = set()
			for production in productions:
				if len(production) == 2:
					
					# Handle t-t combinations
					if self.is_terminal(production[0]) and self.is_terminal(production[1]):
						first_new_nt = self.get_or_create_non_terminal([production[0]], rules=new_rules)
						second_new_nt = self.get_or_create_non_terminal([production[1]], rules=new_rules)
						updated_productions.add(first_new_nt + second_new_nt)

						new_rules[first_new_nt] = [production[0]]
						new_rules[second_new_nt] = [production[1]]
					
					# Handle t-nt combinations
					elif self.is_terminal(production[0]) and self.is_non_terminal(production[1]):
						new_nt = self.get_or_create_non_terminal([production[0]], rules=new_rules)
						updated_productions.add(new_nt + production[1])

						new_rules[new_nt] = [production[0]]

					# Handle nt-t combinations
					elif self.is_non_terminal(production[0]) and self.is_terminal(production[1]):
						new_nt = self.get_or_create_non_terminal([production[1]], rules=new_rules)
						updated_productions.add(production[0] + new_nt)

						new_rules[new_nt] = [production[1]]
					
					# Handle nt-nt combinations (correct format)
					else:
						updated_productions.add(production)
				else:
					updated_productions.add(production)
			
			new_rules[symbol] = list(updated_productions)
		
		self.rules = new_rules

	def create_non_terminal(self) -> str:
		"""
		Helper function to create a new non-terminal symbol.
		"""
		assert self.available_non_terminals, "The grammart has run out of non-terminal symbols. It cannot be converted to CNF."
		
		new_nt = self.available_non_terminals.pop()
		self.non_terminals.add(new_nt)
		return new_nt
	
	def get_or_create_non_terminal(self, rhs: list, rules: dict|None=None) -> str:
		"""
		Helper function to get an existing non-terminal symbol or create a new one if it does not exist.

		Parameters
		----------
		rhs (list): The right-hand side of the production.
		rules (dict, optional): The rules of the grammar. If not provided, the rules of the current grammar are used.

		Returns
		-------

		"""
		existing_nt = self.get_symbol(rhs, rules)
		
		if existing_nt is None:
			new_nt = self.create_non_terminal()
			return new_nt
		
		return existing_nt
	
	def is_terminal(self, symbol: str) -> bool:
		"""
		Checks if a given symbol is a terminal symbol in the grammar.

		Parameters
		----------
		symbol (str): The symbol to check.

		Returns
		-------
		bool
			True if the symbol is a terminal symbol, False otherwise.
		"""
		return symbol in self.terminals
	
	def is_non_terminal(self, symbol: str) -> bool:
		"""
		Checks if a given symbol is a non-terminal symbol in the grammar.

		Parameters
		----------
		symbol (str): The symbol to check.

		Returns
		-------
		bool
			True if the symbol is a non-terminal symbol, False otherwise.
		"""
		return symbol in self.non_terminals
	
	def get_start_symbol(self) -> str:
		"""
		Returns the start symbol of the grammar.

		Returns
		-------
		str
			The start symbol of the grammar.
		"""
		return self.start_symbol

	def get_terminal_symbols(self) -> set:
		"""
		Returns the set of terminal symbols in the grammar.

		Returns
		-------
		set
			Set of terminal symbols.
		"""
		return self.terminals
	
	def get_non_terminal_symbols(self) -> set:
		"""
		Returns the set of non-terminal symbols in the grammar.

		Returns
		-------
		set
			Set of non-terminal symbols.
		"""
		return self.non_terminals
	
	def get_productions(self, symbol: str) -> list:
		"""
		Returns the list of productions for a given symbol.

		Parameters
		----------
		symbol (str): The symbol for which to get the productions.

		Returns
		-------
		list
			List of productions for the given symbol.
		"""
		return self.rules.get(symbol, [])
	
	def get_symbol(self, rhs: list, rules: dict|None=None) -> None|str:
		"""
		Returns the symbol exactly produces the given production.

		Parameters
		----------
		production (list): The production to find the symbol for.
		rules (dict): The rules of the grammar. If not provided, the rules of the current grammar are used.

		Returns
		-------
		None|str
			The symbol that produces the given production. None if the production is not found.
		"""
		rules = rules if rules is not None else self.rules
		for symbol, productions in rules.items():
			if rhs == productions:
				return symbol
		
		return None
	
	def get_rules(self) -> dict:
		"""
		Returns the rules of the grammar.

		Returns
		-------
		dict
			Dictionary of rules in the form of {Symbol: [Production1, Production2, ...], ...}.
		"""
		return self.rules
	
	def set_rules(self, rules: dict) -> None:
		"""
		Sets the rules of the grammar.

		Parameters
		----------
		rules (dict): A dictionary of rules in the form of {Symbol: [Production1, Production2, ...], ...}.
		"""
		self.__init__(rules)

	def __str__(self) -> str:
		"""
		Returns a string that represents the CFG object in a readable format.

		Returns
		-------
		str
			String showing the CFG object in a readable format.
		"""
		non_terminals_order = [self.start_symbol] + list(sorted(self.non_terminals - {self.start_symbol}))
		terminals_string = ', '.join(sorted(self.terminals))
		non_terminals_string = ', '.join(non_terminals_order)
		dict_string = '\n'.join(f"\t{key} --> {' | '.join(sorted(value))}" for key, value in zip(non_terminals_order, [self.rules[symbol] for symbol in non_terminals_order]))
		
		return f"CFG(\n{dict_string}\n)\n" \
			f"\n* Start Symbol: {self.start_symbol}" \
			f"\n* Terminal Symbols: {{{terminals_string}}}" \
			f"\n* Non-Terminal Symbols: {{{non_terminals_string}}}"
	

class PCFG:
    """
    A class to represent a Probabilistic Context-Free Grammar (PCFG) and provide methods to work with it.
    """
    
    EPSILON = 'ε'

    def __init__(self, rules: dict, start_symbol: str|None=None) -> None:
        """
        Initializes the PCFG parser with a given Probabilistic Context-Free Grammar (PCFG).

        The PCFG is stored in Chomsky Normal Form (CNF) internally, so the rules are converted to CNF if they are not already in CNF.

        The symbols must be single characters (strings of length 1): uppercase for non-terminal symbols and lowercase for terminal symbols.

        Parameters
        ----------
        rules (dict): A dictionary of rules in the form of {Symbol: [(Production1, Probability1), (Production2, Probability2), ...], ...}.
        start_symbol (str, optional): The start symbol of the grammar. 
            If not provided, the first symbol is inferred checking all the productions generated by each symbol.
        """
        self.rules: dict = rules

        self.assert_valid_format()
        self.replace_epsilon()

        self.terminals, self.non_terminals = self.find_symbols(start_symbol=start_symbol)

        self.start_symbol: str = start_symbol if start_symbol is not None else self.find_start_symbol()

        print("Initial PCFG:", self)

    def __call__(self, symbol: str) -> list:
        """
        Allows the PCFG object to be called as a function to get the productions for a given symbol.

        Parameters
        ----------
        symbol (str): The symbol for which to get the productions.

        Returns
        -------
        list
            List of productions for the given symbol.
        """
        return self.get_productions(symbol)
    
    def assert_valid_format(self) -> None:
        """
        Asserts that the format of the grammar is valid.

        The grammar must be in the form of a dictionary with the keys as symbols and the values as lists of (productions, probability) tuples.
        Each symbol must be a string and each production must be a string of symbols.

        Raises
        ------
        ValueError
            If the grammar is not in the correct format.
        """
        if not isinstance(self.rules, dict):
            raise ValueError("The grammar must be provided as a dictionary of rules in the form of {Symbol: [(Production1, Probability1), (Production2, Probability2), ...], ...}.")
        
        for symbol, productions in self.rules.items():
            if not isinstance(symbol, str):
                raise ValueError("All symbols must be strings.")
            if len(symbol) != 1:
                raise ValueError("All symbols must be single characters (strings of length 1).")
            
            if not isinstance(productions, list|set|tuple):
                raise ValueError("The set of productions for each symbol must be a list, set, or tuple of (production, probability) tuples.")
            
            for production, probability in productions:
                if not isinstance(production, str):
                    raise ValueError("All individual productions must be strings.")
                if not isinstance(probability, float):
                    raise ValueError("All probabilities must be floats.")

    def replace_epsilon(self) -> None:
        """
        Replaces empty strings with the epsilon symbol (ε) in the grammar rules.
        """
        for symbol, productions in self.rules.items():
            self.rules[symbol] = [(prod if prod else self.EPSILON, prob) for prod, prob in productions]

    def find_symbols(self, start_symbol: str|None) -> tuple[set, set]:
        """
        Finds the terminal and non-terminal symbols in the grammar, checks if they are in the correct format, and returns them.

        The terminal symbols are the ones that are only produced and never produce any other symbol,
        while the non-terminal symbols are the ones that produce other symbols and can be produced by other symbols.

        Parameters
        ----------
        start_symbol (str, None): The start symbol specified by the user.

        Returns
        -------
        tuple[set, set]
            A tuple containing the terminal and non-terminal symbols.

        Raises
        ------
        ValueError
            If the terminal symbols are not lowercase or the non-terminal symbols are not uppercase.
        ValueError
            If there are symbols that produce other symbols but are not produced by any other symbol (cannot be reached).
        """
        non_terminals = set(char for char in self.rules.keys())

        if any(not symbol.isupper() for symbol in non_terminals):
            raise ValueError("The grammar is not correct. All non-terminal symbols must be uppercase.")

        terminals = set()
        for productions in self.rules.values():
            for production, _ in productions:
                for char in production:
                    if char not in non_terminals:
                        terminals.add(char)

        if any(not symbol.islower() for symbol in terminals):
            raise ValueError("The grammar is not correct. All terminal symbols must be lowercase.")

        if start_symbol is not None:
            if non_terminals - self.__get_reachable_non_terminals(start_symbol=start_symbol, non_terminals=non_terminals):
                raise ValueError("The grammar is not correct. Some symbols produce other symbols but are not produced by any other symbol (cannot be reached).")

        return terminals, non_terminals
    
    def find_start_symbol(self) -> str:
        """
        Finds the start symbol of the grammar.

        Returns
        -------
        str
            The start symbol of the grammar.

        Raises
        ------
        ValueError
            If the start symbol cannot be inferred from the grammar rules.
        """
        produced_symbols = set()
        for productions in self.rules.values():
            for production, _ in productions:
                for char in production:
                    produced_symbols.add(char)

        candidates = self.non_terminals - produced_symbols

        if not candidates or len(candidates) > 1:
            raise ValueError("Could not infer the start symbol, more than 1 candidate found. Please provide the start symbol explicitly and ensure that the grammar is correct.")

        start_symbol = candidates.pop() # Get the non-terminal symbol that is not produced by any other symbol

        return start_symbol
    
    def __get_reachable_non_terminals(self, start_symbol: str, non_terminals: set):
        """
        Identifies all reachable non-terminals in the grammar.

        Parameters
        ----------
        start_symbol (str): The start symbol of the grammar.
        non_terminals (set): The set of non-terminal symbols in the grammar.

        Returns
        -------
        set
            Set of reachable non-terminal symbols.
        """
        reachable = set()
        to_process = [start_symbol]
        while to_process:
            current = to_process.pop()
            if current not in reachable:
                reachable.add(current)
                for production, _ in self.rules.get(current, []):
                    for symbol in production:
                        if symbol in non_terminals:
                            to_process.append(symbol)
        return reachable
    
    def get_productions(self, symbol: str) -> list:
        """
        Returns the list of productions for a given symbol.

        Parameters
        ----------
        symbol (str): The symbol for which to get the productions.

        Returns
        -------
        list
            List of productions for the given symbol.
        """
        return self.rules.get(symbol, [])
    
    def get_rules(self) -> dict:
        """
        Returns the rules of the grammar.

        Returns
        -------
        dict
            Dictionary of rules in the form of {Symbol: [(Production1, Probability1), (Production2, Probability2), ...], ...}.
        """
        return self.rules
    
    def get_start_symbol(self) -> str:
        """
        Returns the start symbol of the grammar.

        Returns
        -------
        str
            The start symbol of the grammar.
        """
        return self.start_symbol

    def get_terminal_symbols(self) -> set:
        """
        Returns the set of terminal symbols in the grammar.

        Returns
        -------
        set
            Set of terminal symbols.
        """
        return self.terminals
    
    def get_non_terminal_symbols(self) -> set:
        """
        Returns the set of non-terminal symbols in the grammar.

        Returns
        -------
        set
            Set of non-terminal symbols.
        """
        return self.non_terminals
    
    def __str__(self) -> str:
        """
        Returns a string that represents the PCFG object in a readable format.

        Returns
        -------
        str
            String showing the PCFG object in a readable format.
        """
        non_terminals_order = [self.start_symbol] + list(sorted(self.non_terminals - {self.start_symbol}))
        terminals_string = ', '.join(sorted(self.terminals))
        non_terminals_string = ', '.join(non_terminals_order)
        dict_string = '\n'.join(f"\t{key} --> {' | '.join(f'{prod} [{prob}]' for prod, prob in sorted(value))}" for key, value in zip(non_terminals_order, [self.rules[symbol] for symbol in non_terminals_order]))
        
        return f"PCFG(\n{dict_string}\n)\n" \
            f"\n* Start Symbol: {self.start_symbol}" \
            f"\n* Terminal Symbols: {{{terminals_string}}}" \
            f"\n* Non-Terminal Symbols: {{{non_terminals_string}}}"

