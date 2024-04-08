import os
import numpy as np

def read_and_print_npz_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".npz"):
            filepath = os.path.join(directory, filename)
            data = np.load(filepath)
            matrix_Flir = data['arr_0']
            matrix_AMG = data['arr_1']
            print(f"File: {filename}")
            print("Matrix Flir:")
            print(matrix_Flir)
            print("Matrix AMG:")
            print(matrix_AMG)
            print("\n")
            data.close()

# Add this function call at the end of your main function
read_and_print_npz_files("paired_images")
