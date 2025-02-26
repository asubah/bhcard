import sys
import time
import binascii
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import CardConnectionException, NoCardException
from PIL import Image
import io
import os
import json

class BahrainIDCard:
    def __init__(self):
        """Initialize the BahrainIDCard class"""
        self.connection = None
        self.card_type = None
        self.data = {}
        self.output_dir = None
        
        # Define all APDUs in a flat dictionary with meaningful names
        self.apdu_commands = {
            # Main applet selection
            "SELECT_MAIN_APPLET": "00A404000DD4990000010101000100000001",
            
            # Card management
            "GET_SERIAL_V1": "D0020000 09",
            "GET_SERIAL_V2": "80B80000 08",
            "GET_SERIAL_V4": "80CA0101 13",
            "SELECT_V2_SERIAL_APPLET": "00A4040010A0000000183003010000000000000000",
            
            # Directory selection
            "SELECT_CPR_DIR_V1": "00A404000BF000000078010001435052",
            "SELECT_IMM_DIR_V1": "00A404000BF000000078010002494D4D",
            "SELECT_CPR_DIR_V2": "00A4000C020101",
            "SELECT_IMM_DIR_V2": "00A4000C020301",
            
            # File selection commands
            "SELECT_PERSONAL_INFO_V1": "80A40804020001",
            "SELECT_PERSONAL_INFO_V2": "00A4020C020001",
            "SELECT_CARD_INFO_V2": "00A4020C020002",
            "SELECT_PHOTO_SIG_V1": "80A40804020002",
            "SELECT_PHOTO_SIG_V2": "00A4020C020003",
            "SELECT_ADDRESS_V1": "80A40804020003",
            "SELECT_ADDRESS_V2": "00A4020C020005",
            "SELECT_EMPLOYMENT_V2": "00A4020C020006",
            "SELECT_IMM_BASIC_V1": "80A40804020001",
            "SELECT_IMM_BASIC_V2": "00A4020C020001",
            "SELECT_IMM_DETAILS_V1": "80A40804020002", 
            "SELECT_IMM_DETAILS_V2": "00A4020C020002",
            "SELECT_IMM_ADDITIONAL_V1": "80A40804020003",
            "SELECT_IMM_ADDITIONAL_V2": "00A4020C020003"
        }
        
        # Add governorate lookup
        self.add_governorate_lookup()
    
    def add_governorate_lookup(self):
        """Create an efficient lookup system for governorate names by block ID ranges"""
        # Define the governorate data with block ID ranges
        self.governorate_ranges = [
            {
                "name_en": "CAPITAL", 
                "name_ar": "العاصمة",
                "ranges": [
                    (301, 369),  # Main Capital blocks
                    (380, 382),  # Additional Capital blocks
                    (401, 438),  # Northern Capital areas
                    (601, 634),  # Southern Capital areas
                    (701, 713),  # Eastern Capital regions
                    (816, 816),  # Special Capital area
                    (729, 729),  # Special Capital area
                    (733, 733),  # Special Capital area
                    (743, 745)   # Special Capital areas
                ]
            },
            {
                "name_en": "NORTHERN", 
                "name_ar": "الشمالية",
                "ranges": [
                    (431, 465),  # Main Northern region
                    (469, 481),  # Northern suburbs
                    (502, 590),  # Central Northern region
                    (702, 714),  # Northern industrial area
                    (730, 744),  # Northern residential areas
                    (752, 762),  # Northern coastal areas
                    (1001, 1046),  # Northern new developments
                    (1203, 1218)   # Northern expansion projects
                ]
            },
            {
                "name_en": "MUHARRAQ", 
                "name_ar": "المحرق",
                "ranges": [
                    (101, 128),  # Main Muharraq island
                    (201, 269)   # Muharraq extensions
                ]
            },
            {
                "name_en": "SOUTHERN", 
                "name_ar": "الجنوبية",
                "ranges": [
                    (613, 616),  # Southern border area
                    (635, 636),  # Southern industrial zone
                    (643, 646),  # Southern special economic zone
                    (718, 720),  # Southern coastal area
                    (746, 748),  # Southern development area
                    (801, 816),  # Main Southern region
                    (901, 943),  # Southern suburbs
                    (944, 986),  # Southern expansion
                    (997, 999),  # Southern new projects
                    (1051, 1070),  # Southern satellite developments
                    (1101, 1113)   # Southern future expansion
                ]
            }
        ]
        
        # Special cases for blocks that don't fit in ranges
        self.special_blocks = {
            591: ("NORTHERN", "الشمالية"),
            592: ("CAPITAL", "العاصمة"),
            644: ("CAPITAL", "العاصمة"),
            625: ("CAPITAL", "العاصمة"),
            626: ("CAPITAL", "العاصمة"),
            815: ("CAPITAL", "العاصمة")
        }
        
        print("Loaded optimized governorate lookup data")
    
    def get_governorate_names(self, block_id):
        """Get governorate names for a block ID using range-based lookup"""
        if not hasattr(self, 'governorate_ranges'):
            self.add_governorate_lookup()
        
        try:
            # Convert block_id to integer for range comparison
            block_num = int(block_id.strip())
            
            # Check special blocks first
            if block_num in self.special_blocks:
                return self.special_blocks[block_num]
            
            # Check each governorate's ranges
            for gov in self.governorate_ranges:
                for start, end in gov["ranges"]:
                    if start <= block_num <= end:
                        return gov["name_en"], gov["name_ar"]
                
            return None, None
            
        except (ValueError, TypeError):
            # If block_id is not a valid number
            return None, None
        
    def find_and_connect_reader(self):
        """Find and connect to the first available reader with a card"""
        reader_list = readers()
        if not reader_list:
            print("No smart card readers found.")
            return False
            
        print(f"Found {len(reader_list)} readers: {reader_list}")
        
        for reader in reader_list:
            try:
                connection = reader.createConnection()
                connection.connect()
                print(f"Connected to: {reader}")
                self.connection = connection
                
                # Identify card type by ATR
                atr = toHexString(connection.getATR()).replace(" ", "")
                print(f"Card ATR: {atr}")
                
                if atr.startswith("3B670000A81041"):
                    self.card_type = "V1"
                elif atr.startswith("3B7A9600008065A2010101") or atr == "3B888001E1F35E1177":
                    # Check for V2.1
                    if self.check_v21_structure():
                        self.card_type = "V2.1"
                    else:
                        self.card_type = "V2"
                elif atr.startswith("3B7F"):
                    self.card_type = "V4"
                else:
                    self.card_type = "Unknown"
                
                print(f"Identified card type: {self.card_type}")
                return True
                
            except (CardConnectionException, NoCardException):
                print(f"No card in reader: {reader}")
                continue
                
        print("No card available in any reader.")
        return False
    
    def check_v21_structure(self):
        """Check if card has V2.1 structure"""
        try:
            # Select CIO Applet
            self.transmit(toBytes(self.apdu_commands["SELECT_MAIN_APPLET"]))
            
            # Select MF
            self.transmit(toBytes("00a40004023f00"))
            
            # Select EF-DIR
            response, sw1, sw2 = self.transmit(toBytes("00A40204022F00"))
            
            if (sw1 == 0x61 and sw2 == 0x15) or (sw1 == 0x90 and sw2 == 0x00):
                # Read EF-DIR
                data = self.read_binary_data(0, 335)
                data_hex = binascii.hexlify(bytes(data)).decode('ascii')
                
                if "3F0001019F08020311" in data_hex or "3F0001019F0803030101" in data_hex:
                    return True
            return False
            
        except Exception as e:
            print(f"Error checking V2.1 structure: {e}")
            return False
    
    def transmit(self, command):
        """Send command to card and return response"""
        response, sw1, sw2 = self.connection.transmit(command)
        return response, sw1, sw2
    
    def get_low_high_bytes(self, offset):
        """Get low and high bytes for offset"""
        return [(offset & 0xFF), ((offset >> 8) & 0xFF)]
    
    def read_binary_data(self, offset, length):
        """Read binary data from current file at offset"""
        result = []
        remaining = length
        current_offset = offset
        
        while remaining > 0:
            # Determine length to read (max 255)
            read_length = min(255, remaining)
            
            # Get offset bytes in correct order for command
            p2, p1 = self.get_low_high_bytes(current_offset)
            
            # Create command based on card type
            if self.card_type == "V1":
                command = [0x80, 0xB0, p1, p2, read_length]
            else:
                command = [0x00, 0xB0, p1, p2, read_length]
                
            # Send command
            response, sw1, sw2 = self.transmit(command)
            
            if sw1 != 0x90 or len(response) == 0:
                print(f"Error reading binary data at offset {current_offset}, length {read_length}")
                break
                
            # Append data
            result.extend(response)
            
            # Update counters
            current_offset += read_length
            remaining -= read_length
            
        return result
    
    def extract_string(self, data, offset, length):
        """Extract string from data buffer, removing null bytes"""
        string_bytes = data[offset:offset+length]
        # Remove null bytes and non-printable characters
        filtered_bytes = bytearray([b for b in string_bytes if b > 0 and b < 127])
        return filtered_bytes.decode('utf-8', errors='ignore').strip()
    
    def extract_utf8_string(self, data, offset, length):
        """Extract UTF-8 string from data buffer"""
        string_bytes = bytes(data[offset:offset+length])
        try:
            # Try utf-8 first
            result = string_bytes.decode('utf-8', errors='ignore').strip()
            # Remove null bytes representation
            result = result.replace('\x00', '').strip()
            return result
        except UnicodeDecodeError:
            try:
                # Try utf-16 for Arabic text
                result = string_bytes.decode('utf-16', errors='ignore').strip()
                return result
            except UnicodeDecodeError:
                # Fall back to latin-1
                return string_bytes.decode('latin-1', errors='ignore').strip()
    
    def read_card_data(self, save_files=False, output_dir=None):
        """
        Read all data from the card. This is the common method used by both dump_card and get_card_data.
        
        Args:
            save_files (bool): Whether to save files to disk
            output_dir (str): Directory to save files if save_files is True
            
        Returns:
            dict: Card data
        """
        try:
            # Initialize data dictionary
            card_data = {
                "card_type": self.card_type,
                "dump_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "files": {}
            }
            
            # Create output directory if saving files
            if save_files:
                if output_dir is None:
                    output_dir = f"bahrain_id_dump_{time.strftime('%Y%m%d_%H%M%S')}"
                os.makedirs(output_dir, exist_ok=True)
                self.output_dir = output_dir
                print(f"\nReading card data and saving files to {output_dir}...")
            else:
                print("\nReading card data...")
            
            # Select main applet
            self.transmit(toBytes(self.apdu_commands["SELECT_MAIN_APPLET"]))
            
            # --- Get card serial number ---
            if self.card_type == "V1":
                # V1 card serial number
                response, sw1, sw2 = self.transmit(toBytes(self.apdu_commands["GET_SERIAL_V1"]))
                if sw1 == 0x90:
                    serial = ''.join([chr(b) for b in response if b > 0 and b < 127]).strip()
                    card_data["card_serial"] = serial
                    
            elif self.card_type in ["V2", "V2.1"]:
                # V2/V2.1 card serial number
                self.transmit(toBytes(self.apdu_commands["SELECT_V2_SERIAL_APPLET"]))
                response, sw1, sw2 = self.transmit(toBytes(self.apdu_commands["GET_SERIAL_V2"]))
                if sw1 == 0x90:
                    serial = ''.join([chr(b) for b in response if b > 0 and b < 127]).strip()
                    card_data["card_serial"] = serial
                    
            elif self.card_type == "V4":
                # V4 card serial number
                response, sw1, sw2 = self.transmit(toBytes(self.apdu_commands["GET_SERIAL_V4"]))
                if sw1 == 0x90:
                    serial = ''.join([chr(b) for b in response[3:11] if b > 0 and b < 127]).strip()
                    card_data["card_serial"] = serial
            
            # --- Personal and Card Information ---
            if self.card_type == "V1":
                # V1 cards use different directory structures
                self.transmit(toBytes(self.apdu_commands["SELECT_CPR_DIR_V1"]))
                
                # Read Personal Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_PERSONAL_INFO_V1"]))
                personal_info_data = self.read_binary_data(0, 610)
                if save_files:
                    self.save_file(output_dir, "PersonalInfo.bin", personal_info_data)
                card_data["files"]["PersonalInfo"] = {
                    "size": len(personal_info_data),
                    "description": "Basic personal information (name, ID, etc.)"
                }
                self.extract_personal_info_v1(personal_info_data, card_data)
                
                # Read Photo and Signature file
                self.transmit(toBytes(self.apdu_commands["SELECT_PHOTO_SIG_V1"]))
                photo_sig_data = self.read_binary_data(0, 6006)
                if save_files:
                    self.save_file(output_dir, "PhotoSignature.bin", photo_sig_data)
                    self.extract_photo_signature_v1(output_dir, photo_sig_data)
                else:
                    # Just store the data for later use
                    card_data["photo_data"] = photo_sig_data[6:4006]
                    card_data["signature_data"] = photo_sig_data[4006:6006]
                
                card_data["files"]["PhotoSignature"] = {
                    "size": len(photo_sig_data),
                    "description": "Photo and signature images"
                }
                
                # Read Address Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_ADDRESS_V1"]))
                address_data = self.read_binary_data(0, 711)
                if save_files:
                    self.save_file(output_dir, "AddressInfo.bin", address_data)
                card_data["files"]["AddressInfo"] = {
                    "size": len(address_data),
                    "description": "Residential address and contact information"
                }
                # Extract address info (if implementing a V1-specific address parser)
                
                # Read Immigration files
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_DIR_V1"]))
                
                # Immigration Basic Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_BASIC_V1"]))
                imm_basic_data = self.read_binary_data(0, 72)
                if save_files:
                    self.save_file(output_dir, "ImmigrationBasic.bin", imm_basic_data)
                card_data["files"]["ImmigrationBasic"] = {
                    "size": len(imm_basic_data),
                    "description": "Basic immigration information"
                }
                
                # Immigration Details Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_DETAILS_V1"]))
                imm_details_data = self.read_binary_data(0, 53)
                if save_files:
                    self.save_file(output_dir, "ImmigrationDetails.bin", imm_details_data)
                card_data["files"]["ImmigrationDetails"] = {
                    "size": len(imm_details_data),
                    "description": "Detailed immigration status and information"
                }
                
                # Immigration Additional Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_ADDITIONAL_V1"]))
                imm_additional_data = self.read_binary_data(0, 39)
                if save_files:
                    self.save_file(output_dir, "ImmigrationAdditional.bin", imm_additional_data)
                card_data["files"]["ImmigrationAdditional"] = {
                    "size": len(imm_additional_data),
                    "description": "Additional immigration-related data"
                }
                
            else:  # V2, V2.1, V4
                # Select CPR Directory
                self.transmit(toBytes(self.apdu_commands["SELECT_CPR_DIR_V2"]))
                
                # Read Personal Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_PERSONAL_INFO_V2"]))
                personal_info_data = self.read_binary_data(0, 597)
                if save_files:
                    self.save_file(output_dir, "PersonalInfo.bin", personal_info_data)
                card_data["files"]["PersonalInfo"] = {
                    "size": len(personal_info_data),
                    "description": "Basic personal information (name, ID, etc.)"
                }
                self.extract_personal_info(personal_info_data, card_data)
                
                # Read Card Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_CARD_INFO_V2"]))
                card_info_data = self.read_binary_data(0, 36)
                if save_files:
                    self.save_file(output_dir, "CardInfo.bin", card_info_data)
                card_data["files"]["CardInfo"] = {
                    "size": len(card_info_data),
                    "description": "Card issuance and expiry information"
                }
                self.extract_card_info(card_info_data, card_data)
                
                # Read Photo and Signature file
                self.transmit(toBytes(self.apdu_commands["SELECT_PHOTO_SIG_V2"]))
                photo_sig_data = self.read_binary_data(0, 6000)
                if save_files:
                    self.save_file(output_dir, "PhotoSignature.bin", photo_sig_data)
                    self.extract_photo_signature(output_dir, photo_sig_data)
                else:
                    # Just store the data for later use
                    card_data["photo_data"] = photo_sig_data[0:4000]
                    card_data["signature_data"] = photo_sig_data[4000:6000]
                
                card_data["files"]["PhotoSignature"] = {
                    "size": len(photo_sig_data),
                    "description": "Photo and signature images"
                }
                
                # Read Address Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_ADDRESS_V2"]))
                address_data = self.read_binary_data(0, 512)
                if save_files:
                    self.save_file(output_dir, "AddressInfo.bin", address_data)
                card_data["files"]["AddressInfo"] = {
                    "size": len(address_data),
                    "description": "Residential address and contact information"
                }
                self.extract_address_info(address_data, card_data, save_files, output_dir)
                
                # Read Employment Information file
                self.transmit(toBytes(self.apdu_commands["SELECT_EMPLOYMENT_V2"]))
                employment_data = self.read_binary_data(0, 1590)
                if save_files:
                    self.save_file(output_dir, "EmploymentInfo.bin", employment_data)
                card_data["files"]["EmploymentInfo"] = {
                    "size": len(employment_data),
                    "description": "Employment and occupation details"
                }
                
                # Read Immigration files
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_DIR_V2"]))
                
                # Immigration Basic Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_BASIC_V2"]))
                imm_basic_data = self.read_binary_data(0, 6)
                if save_files:
                    self.save_file(output_dir, "ImmigrationBasic.bin", imm_basic_data)
                card_data["files"]["ImmigrationBasic"] = {
                    "size": len(imm_basic_data),
                    "description": "Basic immigration information"
                }
                
                # Immigration Details Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_DETAILS_V2"]))
                imm_details_data = self.read_binary_data(0, 47)
                if save_files:
                    self.save_file(output_dir, "ImmigrationDetails.bin", imm_details_data)
                card_data["files"]["ImmigrationDetails"] = {
                    "size": len(imm_details_data),
                    "description": "Detailed immigration status and information"
                }
                
                # Immigration Additional Information
                self.transmit(toBytes(self.apdu_commands["SELECT_IMM_ADDITIONAL_V2"]))
                imm_additional_data = self.read_binary_data(0, 33)
                if save_files:
                    self.save_file(output_dir, "ImmigrationAdditional.bin", imm_additional_data)
                card_data["files"]["ImmigrationAdditional"] = {
                    "size": len(imm_additional_data),
                    "description": "Additional immigration-related data"
                }
            
            # Save metadata if requested
            if save_files:
                with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
                    json.dump(card_data, f, indent=2, ensure_ascii=False)
                print(f"\nCard dump completed successfully. Files saved to {output_dir}")
            
            # Return the data
            return card_data
            
        except Exception as e:
            print(f"Error reading card data: {e}")
            return {"error": str(e)}
    
    def dump_card(self):
        """
        Dump all card data to files. This calls read_card_data with save_files=True.
        
        Returns:
            bool: True if successful, False otherwise
        """
        result = self.read_card_data(save_files=True)
        return "error" not in result
    
    def get_card_data(self):
        """
        Get all card data as a dictionary. This calls read_card_data with save_files=False.
        
        Returns:
            dict: Card data
        """
        return self.read_card_data(save_files=False)
    
    def save_file(self, directory, filename, data):
        """Save data to a file"""
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(bytes(data))
        print(f"Saved {filename} ({len(data)} bytes)")
    
    def extract_personal_info(self, data, card_data):
        """Extract personal information from Personal Information file"""
        card_data["personal"] = {
            "id_number": self.extract_string(data, 0, 9).zfill(9),
            "first_name_en": self.extract_string(data, 9, 32),
            "middle_name1_en": self.extract_string(data, 41, 32),
            "middle_name2_en": self.extract_string(data, 73, 32),
            "middle_name3_en": self.extract_string(data, 105, 32),
            "middle_name4_en": self.extract_string(data, 137, 32),
            "last_name_en": self.extract_string(data, 169, 32),
            "first_name_ar": self.extract_utf8_string(data, 201, 64),
            "middle_name1_ar": self.extract_utf8_string(data, 265, 64),
            "middle_name2_ar": self.extract_utf8_string(data, 329, 64),
            "middle_name3_ar": self.extract_utf8_string(data, 393, 64),
            "middle_name4_ar": self.extract_utf8_string(data, 457, 64),
            "last_name_ar": self.extract_utf8_string(data, 521, 64),
            "gender": self.extract_string(data, 585, 1),
            "blood_group": self.extract_string(data, 594, 3)
        }
        
        # Format birth date
        dob = self.extract_string(data, 586, 8)
        if len(dob) == 8:
            card_data["personal"]["birth_date"] = f"{dob[6:8]}/{dob[4:6]}/{dob[0:4]}"
        else:
            card_data["personal"]["birth_date"] = dob
        
        # Build full names
        en_name_parts = [
            card_data["personal"]["first_name_en"],
            card_data["personal"]["middle_name1_en"],
            card_data["personal"]["middle_name2_en"],
            card_data["personal"]["middle_name3_en"],
            card_data["personal"]["middle_name4_en"],
            card_data["personal"]["last_name_en"]
        ]
        card_data["personal"]["full_name_en"] = ' '.join([p for p in en_name_parts if p])
        
        ar_name_parts = [
            card_data["personal"]["first_name_ar"],
            card_data["personal"]["middle_name1_ar"],
            card_data["personal"]["middle_name2_ar"],
            card_data["personal"]["middle_name3_ar"],
            card_data["personal"]["middle_name4_ar"],
            card_data["personal"]["last_name_ar"]
        ]
        card_data["personal"]["full_name_ar"] = ' '.join([p for p in ar_name_parts if p])
    
    def extract_personal_info_v1(self, data, card_data):
        """Extract personal information from Personal Information file (V1 cards)"""
        card_data["personal"] = {
            "id_number": self.extract_string(data, 8, 9).zfill(9),
            "first_name_en": self.extract_string(data, 17, 32),
            "middle_name1_en": self.extract_string(data, 49, 32),
            "middle_name2_en": self.extract_string(data, 81, 32),
            "middle_name3_en": self.extract_string(data, 113, 32),
            "middle_name4_en": self.extract_string(data, 145, 32),
            "last_name_en": self.extract_string(data, 177, 32),
            "first_name_ar": self.extract_utf8_string(data, 209, 64),
            "middle_name1_ar": self.extract_utf8_string(data, 273, 64),
            "middle_name2_ar": self.extract_utf8_string(data, 337, 64),
            "middle_name3_ar": self.extract_utf8_string(data, 401, 64),
            "middle_name4_ar": self.extract_utf8_string(data, 465, 64),
            "last_name_ar": self.extract_utf8_string(data, 529, 64),
            "gender": self.extract_string(data, 593, 1),
            "blood_group": self.extract_string(data, 594, 3)
        }
        
        # Card expiry date (for V1 it's in Personal Information file)
        expiry = self.extract_string(data, 602, 8)
        if len(expiry) == 8:
            card_data["card"] = {
                "expiry_date": f"{expiry[6:8]}/{expiry[4:6]}/{expiry[0:4]}"
            }
        
        # Format birth date
        dob = self.extract_string(data, 594, 8)
        if len(dob) == 8:
            card_data["personal"]["birth_date"] = f"{dob[6:8]}/{dob[4:6]}/{dob[0:4]}"
        else:
            card_data["personal"]["birth_date"] = dob
        
        # Build full names
        en_name_parts = [
            card_data["personal"]["first_name_en"],
            card_data["personal"]["middle_name1_en"],
            card_data["personal"]["middle_name2_en"],
            card_data["personal"]["middle_name3_en"],
            card_data["personal"]["middle_name4_en"],
            card_data["personal"]["last_name_en"]
        ]
        card_data["personal"]["full_name_en"] = ' '.join([p for p in en_name_parts if p])
        
        ar_name_parts = [
            card_data["personal"]["first_name_ar"],
            card_data["personal"]["middle_name1_ar"],
            card_data["personal"]["middle_name2_ar"],
            card_data["personal"]["middle_name3_ar"],
            card_data["personal"]["middle_name4_ar"],
            card_data["personal"]["last_name_ar"]
        ]
        card_data["personal"]["full_name_ar"] = ' '.join([p for p in ar_name_parts if p])
    
    def extract_card_info(self, data, card_data):
        """Extract card information from Card Information file"""
        card_data["card"] = {}
        
        # Card expiry date
        expiry = self.extract_string(data, 0, 8)
        if len(expiry) == 8:
            card_data["card"]["expiry_date"] = f"{expiry[6:8]}/{expiry[4:6]}/{expiry[0:4]}"
        else:
            card_data["card"]["expiry_date"] = expiry
            
        # Card issue date
        issue = self.extract_string(data, 8, 8)
        if len(issue) == 8:
            card_data["card"]["issue_date"] = f"{issue[6:8]}/{issue[4:6]}/{issue[0:4]}"
        else:
            card_data["card"]["issue_date"] = issue
            
        card_data["card"]["issuing_authority"] = self.extract_string(data, 16, 20)
    
    def extract_photo_signature(self, output_dir, data):
        """Extract photo and signature from Photo and Signature file"""
        # Extract photo (first 4000 bytes)
        photo_data = data[0:4000]
        self.save_file(output_dir, "photo.jpg", photo_data)
        
        # Extract signature (next 2000 bytes)
        signature_data = data[4000:6000]
        self.save_file(output_dir, "signature.jpg", signature_data)
    
    def extract_photo_signature_v1(self, output_dir, data):
        """Extract photo and signature from Photo and Signature file (V1 cards)"""
        # Extract photo (first 4000 bytes after offset 6)
        photo_data = data[6:4006]
        self.save_file(output_dir, "photo.jpg", photo_data)
        
        # Extract signature (next 2000 bytes)
        signature_data = data[4006:6006]
        self.save_file(output_dir, "signature.jpg", signature_data)
    
    def extract_address_info(self, address_data, card_data, save_files=False, output_dir=None):
        """Extract address information from Address Information file"""
        # Parse the address data using the exact offsets from the C# code
        card_data["address"] = {
            "email": self.extract_utf8_string(address_data, 0, 64),
            "contact_no": self.extract_utf8_string(address_data, 64, 12),
            "residence_no": self.extract_utf8_string(address_data, 76, 12),
            "flat_no": self.extract_utf8_string(address_data, 105, 4),
            "building_no": self.extract_utf8_string(address_data, 109, 4),
            "building_alpha": self.extract_utf8_string(address_data, 113, 1),
            "building_alpha_arabic": self.extract_utf8_string(address_data, 114, 2),
            "road_no": self.extract_utf8_string(address_data, 116, 4),
            "road_name": self.extract_utf8_string(address_data, 120, 64),
            "road_name_arabic": self.extract_utf8_string(address_data, 184, 128),
            "block_no": self.extract_utf8_string(address_data, 312, 4),
            "block_name": self.extract_utf8_string(address_data, 316, 64),
            "block_name_arabic": self.extract_utf8_string(address_data, 380, 128),
            "governorate_no": self.extract_utf8_string(address_data, 508, 4)
        }
        
        # Add governorate information if block number exists
        block_id = card_data["address"]["block_no"].strip()
        if block_id:
            gov_name_en, gov_name_ar = self.get_governorate_names(block_id)
            if gov_name_en and gov_name_ar:
                card_data["address"]["governorate_name_en"] = gov_name_en
                card_data["address"]["governorate_name_ar"] = gov_name_ar
        
    def disconnect(self):
        """Disconnect from the card"""
        if self.connection:
            self.connection.disconnect()
            print("Disconnected from card.")


def main():
    print("="*50)
    print("Bahrain ID Card Dumper")
    print("="*50)
    
    bhcard = BahrainIDCard()
    
    if bhcard.find_and_connect_reader():
        # Example 1: Dump all card data to files
        print("\nExample 1: Dump all card data to files")
        bhcard.dump_card()
        
        # Example 2: Get card data as a dictionary
        print("\nExample 2: Get card data as a dictionary")
        card_data = bhcard.get_card_data()
        
        # Print some information from the card data
        if "personal" in card_data:
            print(f"Card Holder: {card_data['personal']['full_name_en']}")
            print(f"ID Number: {card_data['personal']['id_number']}")
        
        bhcard.disconnect()
    else:
        print("Failed to connect to a card reader with a valid card.")


if __name__ == "__main__":
    main()
