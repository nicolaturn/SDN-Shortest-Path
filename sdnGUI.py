''' Graphic User Interface for the SDN '''

import tkinter as tk
from tkinter import ttk
import os

import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import networkx

def launch_xterm(wid, width, height):
    os.system(f'xterm -fa "Monospace" -fs 13 -into {wid} -geometry {width}x{height} -sb &')


# Keeping the text box for the Ryu output disable for the user, so it's a read-only logger
def add_log(outputTextBox, outputLog):
    outputTextBox.configure(state='normal')  # Enable the text box temporarily for modification
    outputTextBox.insert('end', outputLog + '\n')
    outputTextBox.configure(state='disabled')  # Disable the text box again
    outputTextBox.see('end')  # Scroll to the end to show the latest log entry

# Function to change the graph displayer
def create_graph_image(netGraph, graphLabel):
    pos = nx.spring_layout(netGraph)
    
    nx.draw(netGraph, pos, with_labels=True, node_size=500, font_size=10, font_color='black')
    
    # Create a Matplotlib figure and draw the graph on it
    fig = plt.figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    nx.draw(netGraph, pos, ax=ax, with_labels=True, node_size=500, font_size=10, font_color='black')
    
    # Save the figure to an image file
    image_path = "graph_image.png"
    canvas.print_png(image_path)
    
    # Load the image using PIL
    image = Image.open(image_path)
    photo = ImageTk.PhotoImage(image)
    
    # Update the label with the image
    graphLabel.config(image=photo)
    graphLabel.image = photo

#Main function to execute the SDN GUI
def main():

    ### Creating the main window
    window = tk.Tk()
    window.title("SDN viewer and tester")

    # Edit the dimensions of the main window
    new_width = 1600
    new_height = 1000
    window.geometry(f"{new_width}x{new_height}")

    # The main window is not resizable and is not opened fullscreen
    window.resizable(width = False, height = False)

    # Create the style for the rounded frames
    style = ttk.Style()
    style.configure('RoundedFrame.TFrame', borderwidth=5, relief='raised', padding=5, background='lightgray')

    # Create a custom style for the rounded buttons
    styleButton = ttk.Style()
    styleButton.configure("RoundedButton.TButton",
                        borderwidth=10,
                        focuscolor="red",
                        bordercolor="black",
                        relief="flat",
                        background="#007acc",
                        foreground="white",
                        padding=(10, 5),  # Set padding for button size
                        font=("Helvetica", 10))

    # Change the hover color for the buttons
    styleButton.map("RoundedButton.TButton",
                     background=[("active", "#0055a0")])

    


    ### Top left corner
    graphFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 800)
    graphFrame.grid(row = 0, column = 0, sticky = 'nw')

    # The title of graph section
    titleLabelGraph = ttk.Label(graphFrame, text="Network Graph", background = "lightgray", font=("Helvetica", 14))
    titleLabelGraph.pack(side='top', padx = 10, pady = 5, fill = 'none', expand = False)

    graphLabel = tk.Label(graphFrame, bg = "#C2C2A3", height = 400, width = 800)
    graphLabel.pack(side = 'top', fill = 'none', expand = False)

    graphFrame.propagate(False)



    ### Top right corner
    outputRyuFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 800)
    outputRyuFrame.grid(row = 0, column = 1, sticky = 'ne')

    # The title of the outputTextBox of Ryu
    titleLabelOutput = ttk.Label(outputRyuFrame, text="Output Logger for Ryu controller", background = "lightgray", font=("Helvetica", 14))
    titleLabelOutput.pack(side='top', fill = 'none', expand = False, padx = 10, pady = 5)

    outputRyuText = tk.Text(outputRyuFrame, bg = "#C2C2A3", state = 'disabled', height = 400, width = 800)
    outputRyuText.pack(side = "top", fill = 'none', expand = False)
    #add_log(outputRyuText, "Prova inserimento testo in text box")

    #stop the propagation of pack() because the outputRyuFrame resize itself as it wants. It doesn't listen to my will
    outputRyuFrame.propagate(False)


    
    ### Bottom left corner
    buttonFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 800)
    buttonFrame.grid(row = 1, column = 0, sticky = 'sw')

    # The title of button section
    titleLabelGraph = ttk.Label(buttonFrame, text="Testing button panel", background = "lightgray", font=("Helvetica", 14))
    titleLabelGraph.pack(side='top', padx = 10, pady = 5, fill = 'none', expand = False)

    # Frame for the buttons
    buttonFrameNested = ttk.Frame(buttonFrame, style = 'RoundedFrame.TFrame', height = 150, width = 500)
    buttonFrameNested.pack(side = 'top', expand = True, fill = 'both', anchor = 'center')

    buttonTest1 = ttk.Button(buttonFrameNested, text = "Load topology #1", style = "RoundedButton.TButton")
    buttonTest1.pack(side = 'top', padx=10, pady=5, fill='x', anchor = 'center', expand=False)

    buttonTest2 = ttk.Button(buttonFrameNested, text = "Load topology #2", style = "RoundedButton.TButton")
    buttonTest2.pack(side = 'top', padx=10, pady=5, fill='x', anchor = 'center', expand=False)

    buttonTest3 = ttk.Button(buttonFrameNested, text = "Load topology #3", style = "RoundedButton.TButton")
    buttonTest3.pack(side = 'top', padx=10, pady=5, fill='x', expand=False)

    buttonFrameNested.propagate(False)
    buttonFrame.propagate(False)



    ### Bottom right corner
    #Create frame that contains titleLabelTerminal for the terminal and the xterm terminal
    termFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 800)
    termFrame.grid(row = 1, column = 1, sticky = 'se')

    # The actual frame of the terminal
    termf = ttk.Frame(termFrame, height=400, width=800)
    termf.pack(side = 'bottom')

    # The title of the terminal
    titleLabelTerminal = ttk.Label(termFrame, text="Terminal for Mininet CLI", background = "lightgray", borderwidth = 10, font=("Helvetica", 13))
    titleLabelTerminal.pack(side='top', fill = 'none', expand = False, padx = 10, pady = 5)

    wid = termf.winfo_id()

    # Launch xterm with specified font size and dimensions
    window.after(700, lambda: launch_xterm(wid, 800, 400))     #With the method after() we can delay the starting of the xterminal, so the dimensions of xterm are written and the terminal can take the right size
    print(f"Questo è il PID di termf: {wid})")

    termFrame.propagate(False)



    '''# Bind the window resize event to the on_resize function
    window.bind("<Configure>", lambda event: on_resize(event, graphLabel, outputRyuText))
    window.bind("<Configure>", lambda event: resize_terminal(event, wid, termf))'''
    
    window.mainloop()

if __name__ == '__main__':
    main()