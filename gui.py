import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from PIL import Image, ImageTk
import threading
import io
from bhcard import BahrainIDCard  # Import the new BahrainIDCard class

# Libraries for proper Arabic text display
import arabic_reshaper
from bidi.algorithm import get_display

class BahrainIDViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Bahrain ID Card Viewer")
        self.geometry("900x750")
        
        self.card = BahrainIDCard()  # Use the new class
        self.card_data = None
        
        # Create main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add buttons
        self.read_button = ttk.Button(button_frame, text="Read Card", command=self.read_card)
        self.read_button.pack(side=tk.LEFT, padx=5)
        
        self.dump_button = ttk.Button(button_frame, text="Dump Data", command=self.dump_data)
        self.dump_button.pack(side=tk.LEFT, padx=5)
        
        # Add status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create content frame with scrollbar
        content_outer_frame = ttk.Frame(main_frame)
        content_outer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add Canvas for scrolling
        self.canvas = tk.Canvas(content_outer_frame)
        scrollbar = ttk.Scrollbar(content_outer_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add content to scrollable frame
        self.create_content()
    
    def create_content(self):
        """Create all the content widgets"""
        
        # Card information section
        card_frame = ttk.LabelFrame(self.scrollable_frame, text="Card Information", padding=10)
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(card_frame, text="Card Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.card_type_label = ttk.Label(card_frame, text="N/A")
        self.card_type_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(card_frame, text="Card Serial:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.card_serial_label = ttk.Label(card_frame, text="N/A")
        self.card_serial_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(card_frame, text="Expiry Date:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.expiry_date_label = ttk.Label(card_frame, text="N/A")
        self.expiry_date_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(card_frame, text="Issue Date:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.issue_date_label = ttk.Label(card_frame, text="N/A")
        self.issue_date_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(card_frame, text="Issuing Authority:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.issuing_authority_label = ttk.Label(card_frame, text="N/A")
        self.issuing_authority_label.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Personal information section
        personal_frame = ttk.LabelFrame(self.scrollable_frame, text="Personal Information", padding=10)
        personal_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(personal_frame, text="ID Number:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.id_number_label = ttk.Label(personal_frame, text="N/A")
        self.id_number_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(personal_frame, text="Full Name (EN):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.full_name_en_label = ttk.Label(personal_frame, text="N/A")
        self.full_name_en_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(personal_frame, text="Full Name (AR):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Special handling for Arabic text - using a frame with right alignment
        ar_name_frame = ttk.Frame(personal_frame)
        ar_name_frame.grid(row=2, column=1, sticky=tk.E, padx=5, pady=2)
        
        # Use a variable with Arabic text for easy updating
        self.arabic_name_var = tk.StringVar()
        self.arabic_name_var.set("N/A")
        
        # Configure a label with right alignment for Arabic text
        self.full_name_ar_label = ttk.Label(ar_name_frame, textvariable=self.arabic_name_var,
                                           justify=tk.RIGHT, anchor=tk.E)
        self.full_name_ar_label.pack(side=tk.RIGHT)
        
        ttk.Label(personal_frame, text="Gender:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.gender_label = ttk.Label(personal_frame, text="N/A")
        self.gender_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(personal_frame, text="Date of Birth:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.birth_date_label = ttk.Label(personal_frame, text="N/A")
        self.birth_date_label.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(personal_frame, text="Blood Group:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.blood_group_label = ttk.Label(personal_frame, text="N/A")
        self.blood_group_label.grid(row=5, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Contact & Address information section
        address_frame = ttk.LabelFrame(self.scrollable_frame, text="Contact & Address Information", padding=10)
        address_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Contact information
        ttk.Label(address_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.email_label = ttk.Label(address_frame, text="N/A")
        self.email_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Contact No:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.contact_no_label = ttk.Label(address_frame, text="N/A")
        self.contact_no_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Residence No:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.residence_no_label = ttk.Label(address_frame, text="N/A")
        self.residence_no_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Building information
        ttk.Label(address_frame, text="Flat/Villa No:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.flat_no_label = ttk.Label(address_frame, text="N/A")
        self.flat_no_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Building No:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.building_no_label = ttk.Label(address_frame, text="N/A")
        self.building_no_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Road information
        ttk.Label(address_frame, text="Road No:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.road_no_label = ttk.Label(address_frame, text="N/A")
        self.road_no_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Road Name:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.road_name_label = ttk.Label(address_frame, text="N/A")
        self.road_name_label.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Block information
        ttk.Label(address_frame, text="Block No:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=2)
        self.block_no_label = ttk.Label(address_frame, text="N/A")
        self.block_no_label.grid(row=3, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Block Name:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=2)
        self.block_name_label = ttk.Label(address_frame, text="N/A")
        self.block_name_label.grid(row=4, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Arabic address 
        ttk.Label(address_frame, text="Block Name (AR):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.arabic_block_var = tk.StringVar()
        self.arabic_block_var.set("N/A")
        
        ar_block_frame = ttk.Frame(address_frame)
        ar_block_frame.grid(row=5, column=1, sticky=tk.E, padx=5, pady=2)
        
        self.block_name_ar_label = ttk.Label(ar_block_frame, textvariable=self.arabic_block_var,
                                           justify=tk.RIGHT, anchor=tk.E)
        self.block_name_ar_label.pack(side=tk.RIGHT)
        
        ttk.Label(address_frame, text="Road Name (AR):").grid(row=5, column=2, sticky=tk.W, padx=5, pady=2)
        self.arabic_road_var = tk.StringVar()
        self.arabic_road_var.set("N/A")
        
        ar_road_frame = ttk.Frame(address_frame)
        ar_road_frame.grid(row=5, column=3, sticky=tk.E, padx=5, pady=2)
        
        self.road_name_ar_label = ttk.Label(ar_road_frame, textvariable=self.arabic_road_var,
                                            justify=tk.RIGHT, anchor=tk.E)
        self.road_name_ar_label.pack(side=tk.RIGHT)
        
        # Governorate information
        ttk.Label(address_frame, text="Governorate:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        self.governorate_label = ttk.Label(address_frame, text="N/A")
        self.governorate_label.grid(row=6, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(address_frame, text="Governorate (AR):").grid(row=6, column=2, sticky=tk.W, padx=5, pady=2)
        self.arabic_gov_var = tk.StringVar()
        self.arabic_gov_var.set("N/A")
        
        ar_gov_frame = ttk.Frame(address_frame)
        ar_gov_frame.grid(row=6, column=3, sticky=tk.E, padx=5, pady=2)
        
        self.governorate_ar_label = ttk.Label(ar_gov_frame, textvariable=self.arabic_gov_var,
                                              justify=tk.RIGHT, anchor=tk.E)
        self.governorate_ar_label.pack(side=tk.RIGHT)
        
        # Photo and signature section
        photo_frame = ttk.LabelFrame(self.scrollable_frame, text="Photo & Signature", padding=10)
        photo_frame.pack(fill=tk.X, padx=5, pady=5)
        
        photo_inner_frame = ttk.Frame(photo_frame)
        photo_inner_frame.pack(fill=tk.X)
        
        self.photo_label = ttk.Label(photo_inner_frame, text="No Photo")
        self.photo_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.signature_label = ttk.Label(photo_inner_frame, text="No Signature")
        self.signature_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Dump information section
        dump_frame = ttk.LabelFrame(self.scrollable_frame, text="Dump Information", padding=10)
        dump_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dump_frame, text="Dump Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.dump_dir_label = ttk.Label(dump_frame, text="N/A")
        self.dump_dir_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(dump_frame, text="Dump Time:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.dump_time_label = ttk.Label(dump_frame, text="N/A")
        self.dump_time_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(dump_frame, text="Files:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.files_label = ttk.Label(dump_frame, text="N/A")
        self.files_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Result text area
        result_frame = ttk.LabelFrame(self.scrollable_frame, text="Raw Data Output", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def format_arabic_text(self, text):
        """Format Arabic text properly for display with proper shaping and direction"""
        if not text or text == "N/A":
            return text
            
        try:
            # Reshape the Arabic text to connect the letters properly
            reshaped_text = arabic_reshaper.reshape(text)
            # Apply bidirectional algorithm to handle right-to-left text
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            print(f"Error formatting Arabic text: {e}")
            return text
    
    def read_card(self):
        """Read card information using BahrainIDCard"""
        self.status_var.set("Connecting to card reader...")
        self.update_idletasks()
        
        # Start in a separate thread to avoid freezing UI
        threading.Thread(target=self._read_card_thread, daemon=True).start()
    
    def _read_card_thread(self):
        """Thread function for reading card"""
        try:
            if self.card.find_and_connect_reader():
                self.status_var.set("Connected! Reading card data...")
                self.update_idletasks()
                
                # Use the get_card_data method to retrieve all card data
                self.card_data = self.card.get_card_data()
                
                # Update UI with card data
                self.after(100, self.update_ui_with_card_data)
                
                # Show the data in the text area
                self.after(100, lambda: self.update_result_text(json.dumps(self.card_data, indent=2, ensure_ascii=False)))
                self.after(100, lambda: self.status_var.set("Card read successfully"))
            else:
                self.after(100, lambda: self.status_var.set("Failed to connect to a card reader"))
                self.after(100, lambda: messagebox.showerror("Error", "Failed to connect to a card reader with a valid card"))
        except Exception as e:
            error_msg = f"Error reading card: {str(e)}"
            self.after(100, lambda: self.status_var.set(error_msg))
            self.after(100, lambda: messagebox.showerror("Error", error_msg))
            self.after(100, lambda: self.update_result_text(error_msg))
        finally:
            # Make sure to disconnect
            if hasattr(self.card, 'connection') and self.card.connection:
                self.card.disconnect()
    
    def dump_data(self):
        """Dump all card data to files using BahrainIDCard"""
        self.status_var.set("Connecting to card reader...")
        self.update_idletasks()
        
        # Start in a separate thread to avoid freezing UI
        threading.Thread(target=self._dump_data_thread, daemon=True).start()
    
    def _dump_data_thread(self):
        """Thread function for dumping data"""
        try:
            if self.card.find_and_connect_reader():
                self.status_var.set("Connected! Dumping all card data...")
                self.update_idletasks()
                
                # Dump all data to files
                result = self.card.dump_card()
                
                if result:
                    # Get the dump directory
                    self.card_data = self.card.read_card_data(save_files=False)
                    
                    # Update UI with data
                    self.after(100, self.update_ui_with_card_data)
                    
                    # Update dump information
                    if hasattr(self.card, 'output_dir') and self.card.output_dir:
                        self.after(100, lambda: self.dump_dir_label.config(text=self.card.output_dir))
                        self.after(100, lambda: self.dump_time_label.config(text=self.card_data.get("dump_time", "Unknown")))
                        
                        files_list = ", ".join(self.card_data.get("files", {}).keys())
                        self.after(100, lambda: self.files_label.config(text=files_list))
                        
                        # Load photos if available
                        self.after(100, lambda: self.load_images_from_files(self.card.output_dir))
                    
                    # Display raw data in text area
                    self.after(100, lambda: self.update_result_text(json.dumps(self.card_data, indent=2, ensure_ascii=False)))
                    
                    # Update status
                    self.after(100, lambda: self.status_var.set(f"Data dumped successfully to {self.card.output_dir}"))
                else:
                    self.after(100, lambda: self.status_var.set("Failed to dump card data"))
                    self.after(100, lambda: messagebox.showerror("Error", "Failed to dump card data"))
            else:
                self.after(100, lambda: self.status_var.set("Failed to connect to a card reader"))
                self.after(100, lambda: messagebox.showerror("Error", "Failed to connect to a card reader with a valid card"))
        except Exception as e:
            error_msg = f"Error dumping card: {str(e)}"
            self.after(100, lambda: self.status_var.set(error_msg))
            self.after(100, lambda: messagebox.showerror("Error", error_msg))
            self.after(100, lambda: self.update_result_text(error_msg))
        finally:
            # Make sure to disconnect
            if hasattr(self.card, 'connection') and self.card.connection:
                self.card.disconnect()
    
    def update_ui_with_card_data(self):
        """Update UI with card data from self.card_data"""
        if not self.card_data:
            return
            
        # Card information
        self.card_type_label.config(text=self.card_data.get("card_type", "N/A"))
        self.card_serial_label.config(text=self.card_data.get("card_serial", "N/A"))
        
        # Card details
        if "card" in self.card_data:
            card_info = self.card_data["card"]
            self.expiry_date_label.config(text=card_info.get("expiry_date", "N/A"))
            self.issue_date_label.config(text=card_info.get("issue_date", "N/A"))
            self.issuing_authority_label.config(text=card_info.get("issuing_authority", "N/A"))
        
        # Personal information
        if "personal" in self.card_data:
            personal = self.card_data["personal"]
            self.id_number_label.config(text=personal.get("id_number", "N/A"))
            self.full_name_en_label.config(text=personal.get("full_name_en", "N/A"))
            
            # Format Arabic name properly
            ar_name = self.format_arabic_text(personal.get("full_name_ar", "N/A"))
            self.arabic_name_var.set(ar_name)
            
            gender_code = personal.get("gender", "N/A")
            gender_text = "Male" if gender_code == "M" else "Female" if gender_code == "F" else gender_code
            self.gender_label.config(text=gender_text)
            
            self.birth_date_label.config(text=personal.get("birth_date", "N/A"))
            self.blood_group_label.config(text=personal.get("blood_group", "N/A"))
        
        # Address information
        if "address" in self.card_data:
            address = self.card_data["address"]
            self.email_label.config(text=address.get("email", "N/A"))
            self.contact_no_label.config(text=address.get("contact_no", "N/A"))
            self.residence_no_label.config(text=address.get("residence_no", "N/A"))
            self.flat_no_label.config(text=address.get("flat_no", "N/A"))
            self.building_no_label.config(text=address.get("building_no", "N/A"))
            self.road_no_label.config(text=address.get("road_no", "N/A"))
            self.road_name_label.config(text=address.get("road_name", "N/A"))
            self.block_no_label.config(text=address.get("block_no", "N/A"))
            self.block_name_label.config(text=address.get("block_name", "N/A"))
            
            # Format Arabic block and road names
            block_ar = self.format_arabic_text(address.get("block_name_arabic", "N/A"))
            road_ar = self.format_arabic_text(address.get("road_name_arabic", "N/A"))
            self.arabic_block_var.set(block_ar)
            self.arabic_road_var.set(road_ar)
            
            # Add governorate information
            if "governorate_name_en" in address and "governorate_name_ar" in address:
                self.governorate_label.config(text=address.get("governorate_name_en", "N/A"))
                gov_ar = self.format_arabic_text(address.get("governorate_name_ar", "N/A"))
                self.arabic_gov_var.set(gov_ar)
        
        # Load photo and signature if available in memory
        if "photo_data" in self.card_data and "signature_data" in self.card_data:
            self.load_images_from_memory(
                self.card_data["photo_data"],
                self.card_data["signature_data"]
            )
    
    def load_images_from_memory(self, photo_data, signature_data):
        """Load photo and signature from memory data"""
        try:
            # Load photo
            photo = Image.open(io.BytesIO(bytes(photo_data)))
            photo = photo.resize((150, 200), Image.LANCZOS)
            photo_tk = ImageTk.PhotoImage(photo)
            
            # Store reference to prevent garbage collection
            self.photo_image = photo_tk
            self.photo_label.config(image=photo_tk, text="")
            
            # Load signature
            signature = Image.open(io.BytesIO(bytes(signature_data)))
            signature = signature.resize((200, 100), Image.LANCZOS)
            signature_tk = ImageTk.PhotoImage(signature)
            
            # Store reference to prevent garbage collection
            self.signature_image = signature_tk
            self.signature_label.config(image=signature_tk, text="")
            
        except Exception as e:
            print(f"Error loading images from memory: {e}")
            self.photo_label.config(text="Error loading photo")
            self.signature_label.config(text="Error loading signature")
    
    def load_images_from_files(self, directory):
        """Load photo and signature from files in the dump directory"""
        if not directory:
            return
            
        try:
            # Load photo
            photo_path = os.path.join(directory, "photo.jpg")
            if os.path.exists(photo_path):
                photo = Image.open(photo_path)
                photo = photo.resize((150, 200), Image.LANCZOS)
                photo_tk = ImageTk.PhotoImage(photo)
                
                # Store reference to prevent garbage collection
                self.photo_image = photo_tk
                self.photo_label.config(image=photo_tk, text="")
            
            # Load signature
            signature_path = os.path.join(directory, "signature.jpg")
            if os.path.exists(signature_path):
                signature = Image.open(signature_path)
                signature = signature.resize((200, 100), Image.LANCZOS)
                signature_tk = ImageTk.PhotoImage(signature)
                
                # Store reference to prevent garbage collection
                self.signature_image = signature_tk
                self.signature_label.config(image=signature_tk, text="")
                
        except Exception as e:
            print(f"Error loading images from files: {e}")
            self.photo_label.config(text="Error loading photo")
            self.signature_label.config(text="Error loading signature")
    
    def update_result_text(self, text):
        """Update the result text area"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = BahrainIDViewer()
    app.mainloop()
