from src.cfg import CFG
from src.cky import CKY
from src.functions import split_input
import os

def main(input_text: str, file_name: str) -> None:
	"""
	Function to process the input text, splitting it into the rules and words, and then parsing the words using the CKY algorithm.

	Parameters
	----------
	input_text (str): The input text of the file to be processed.
	file_name (str): The name of the file being processed.
	"""
	rules_text, words = split_input(file_text=input_text)
	cfg = CFG(from_text=rules_text)

	# Parse the words using the CKY algorithm
	cky = CKY(cfg)

	results = []
	for word in words:
		if cfg.is_probabilistic():
			result = cky.parse(word=word, round_probabilities=True)
		else:
			result = cky.parse(word=word)
		results.append(result)

	# Save the results to a file
	save_path = f"./results/results_{file_name}"

	save_file = open(save_path, 'w', encoding='utf-8')

	save_file.write(f"{cfg}\n")
	save_file.write(f"{'#' * 50}\n\n")

	# Write the results to the file
	for result, word in zip(results, words):
		if cfg.is_probabilistic():
			parsed, prob, tree = result
			if parsed:
				save_file.write(f"{word} -> {parsed} [{prob}]\nTREE -> {tree}\n")
			else:
				save_file.write(f"{word} -> {parsed}\n")
		else:
			parsed, tree = result
			if parsed:
				save_file.write(f"{word} -> {parsed}\nTREE -> {tree}\n")
			else:
				save_file.write(f"{word} -> {parsed}\n")

		save_file.write('\n')

	save_file.close()

	print(f"Results saved to '{save_path}'.")

if __name__ == '__main__':
	# Ask the user for the file to process
	all_files = False
	first_n_files = None
	while True:
		file_names = input("Input file [file name | all | help]: ").strip()
		file_names = [f.strip() for f in file_names.split(',')]
		if not file_names:
			print("Please provide a valid file name.")
			continue

		if len(file_names) > 1:
			if all(os.path.isfile(os.path.join('./tests', f)) for f in file_names):
				break
			else:
				for f in file_names:	
					if not os.path.isfile(os.path.join('./tests', f)):
						print(f"File '{f}' not found. Please provide a valid file names in the folder './tests'.")
						
				continue
		
		elif len(file_names) == 1:
			if file_names[0].lower() == 'help':
				print("You can input the following commands:")
				print("\t* A file name to process a specific file in the folder './tests'.")
				print("\t* Multiple file names separated by commas to process multiple files in the folder './tests'.")
				print("\t* Introduce 'all' to process all files in the folder './tests'.")
				continue
			
			elif file_names[0].lower() == 'all':
				all_files = True
				break
			
			elif not os.path.isfile(os.path.join('./tests', file_names[0])):
				print(f"File '{file_names}' not found. Please provide a valid file name in the folder './tests'.")
				continue
			else:
				break

	# Get the list of files to process
	if all_files:
		file_names = os.listdir('./tests')

	total_files = len(file_names)

	# Process the files
	errors = 0
	for file_name in file_names:
		print(f"\n{'#'*25} RUNNING FILE '{file_name}' {'#'*25}")

		# Open the file
		with open(os.path.join('./tests', file_name), 'r', encoding='utf-8') as file:
			input_text = file.read()

			# Process the file
			try:
				main(input_text=input_text, file_name=file_name)
			except Exception as e:
				print(f"Error processing file '{file_name}'. Error message: {e}.\n\nIgnoring file and continuing to the next one.")
				errors += 1
				continue

	print(f"\n{'#'*25} ALL {total_files} FILES PROCESSED [{errors} ERRORS] {'#'*25}\n")
