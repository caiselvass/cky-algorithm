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
		result = cky.parse(word=word, round_probabilities=True)
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
		file_name = input("Input file: ")
		if not file_name:
			print("Please provide a valid file name.")
			continue

		if file_name.lower() == 'help':
			print("You can input the following commands:")
			print("\t- A file name to process a specific file in the folder './tests'.")
			print("\t- 'all' to process all files in the folder './tests'.")
			continue
		
		elif file_name.lower() == 'all':
			all_files = True
		
		elif not os.path.isfile(os.path.join('./tests', file_name)):
			print(f"File '{file_name}' not found. Please provide a valid file name in the folder './tests'.")
			continue
		
		break

	# Get the list of files to process
	files_list = os.listdir('./tests') if all_files else [file_name]

	for file_name in files_list:
		with open(os.path.join('./tests', file_name), 'r', encoding='utf-8') as file:
			input_text = file.read()

			# Process the file
			main(input_text=input_text, file_name=file_name)

	print("\nAll files processed successfully!")
