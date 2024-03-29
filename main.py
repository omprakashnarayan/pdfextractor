import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from tkinter import Tk, Button, Label, filedialog, Canvas, Text, Scrollbar
import camelot
from PIL import Image, ImageTk

class PDFPreview:
    def __init__(self, parent):
        self.parent = parent
        self.canvas = Canvas(parent, width=400, height=400)
        self.canvas.pack()

    def load_pdf(self, pdf_path):
        self.document = fitz.open(pdf_path)
        self.page_num = 0
        self.show_page()

    def show_page(self):
        page = self.document.load_page(self.page_num)
        pix = page.get_pixmap()
        img = fitz.Pixmap(pix)
        img = np.frombuffer(img.samples, dtype=np.uint8).reshape(img.h, img.w, 4)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        img = cv2.resize(img, (400, 400))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        self.img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.img)

    def next_page(self):
        self.page_num = min(self.page_num + 1, len(self.document) - 1)
        self.show_page()

    def prev_page(self):
        self.page_num = max(self.page_num - 1, 0)
        self.show_page()

def extract_text_and_images(pdf_path, output_folder):
    # Get PDF file name
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create output folder with PDF file name
    pdf_output_folder = os.path.join(output_folder, pdf_filename)
    os.makedirs(pdf_output_folder, exist_ok=True)

    # Create subfolders for text, images, and tables
    text_folder = os.path.join(pdf_output_folder, 'text')
    image_folder = os.path.join(pdf_output_folder, 'images')
    table_folder = os.path.join(pdf_output_folder, 'tables')
    os.makedirs(text_folder, exist_ok=True)
    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(table_folder, exist_ok=True)

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Extract text, images, and tables
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        images = page.get_images(full=True)

        # Save text
        text_output_path = os.path.join(text_folder, f'page_{page_num + 1}.txt')
        with open(text_output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(text)

        # Save images
        for img_index, img_info in enumerate(images):
            xref = img_info[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_output_path = os.path.join(image_folder,f'page_{page_num + 1}_img_{img_index + 1}.{image_ext}')
            with open(image_output_path, 'wb') as image_file:
                image_file.write(image_bytes)

        # Extract tables using camelot
        tables = camelot.read_pdf(pdf_path, pages=str(page_num + 1))
        for idx, table in enumerate(tables):
            table.to_csv(os.path.join(table_folder, f'page_{page_num + 1}_table_{idx + 1}.csv'))

    pdf_document.close()
    print("Extraction complete.")

def open_pdf():
    global pdf_preview
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        lbl_input_dir.config(text=file_path)
        pdf_preview.load_pdf(file_path)

def open_directory():
    file_path = filedialog.askdirectory()
    if file_path:
        lbl_output_dir.config(text=file_path)

def extract_pdf():
    input_dir = lbl_input_dir.cget("text")
    output_dir = lbl_output_dir.cget("text")
    if input_dir and output_dir:
        extract_text_and_images(input_dir, output_dir)
        lbl_status.config(text="Extraction complete.")
    else:
        lbl_status.config(text="Please select input and output directories.")

# UI setup
root = Tk()
root.title("PDF Data Extractor")

pdf_preview = PDFPreview(root)
pdf_preview.canvas.pack()

lbl_input_dir_text = Label(root, text="Input Directory:")
lbl_input_dir_text.pack()

lbl_input_dir = Label(root, text="")
lbl_input_dir.pack()

btn_open_pdf = Button(root, text="Open PDF", command=open_pdf)
btn_open_pdf.pack()

lbl_output_dir_text = Label(root, text="Output Directory:")
lbl_output_dir_text.pack()

lbl_output_dir = Label(root, text="")
lbl_output_dir.pack()

btn_open_directory = Button(root, text="Browse", command=open_directory)
btn_open_directory.pack()

btn_extract = Button(root, text="Extract", command=extract_pdf)
btn_extract.pack()

lbl_status = Label(root, text="")
lbl_status.pack()

root.mainloop()
