import os
import numpy as np
import matplotlib.pyplot as plt

def visualize_npz_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".npz"):
            filepath = os.path.join(directory, filename)
            if os.path.getsize(filepath) > 0:
                data = np.load(filepath)
                matrix_Flir = data['arr_0']
                matrix_AMG = data['arr_1']
                print(f"File: {filename}")
                print("Matrix Flir:")
                print(matrix_Flir)
                print("Matrix AMG:")
                print(matrix_AMG)
                print("\n")

                # Display Flir and AMG images side by side
                fig, axs = plt.subplots(1, 2)
                axs[0].imshow(matrix_Flir, cmap='gray')
                axs[0].set_title('Flir')
                axs[0].axis('off')
                axs[1].imshow(matrix_AMG, cmap='gray')
                axs[1].set_title('AMG')
                axs[1].axis('off')
                plt.show()

                data.close()
            else:
                print(f"File '{filename}' is empty.")

# Call this function at the end of your main function
visualize_npz_files("paired_images")
