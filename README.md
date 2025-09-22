# HOW TO MAKE EXE:
pyinstaller --onefile --noconsole scan_and_print.py

# Tardy Pass Automation System  
An automated **Tardy Pass Generator** built with Python that replaces manual handwritten tardy passes with a fast, reliable GUI and printing workflow.  

## Overview  
This project allows school staff to quickly generate and print tardy passes for students by scanning a student’s ID barcode. The system retrieves student information from a database, adds the current date and time, and previews the pass on a GUI before printing.  

- Generates a pass in less than 10 seconds (compared to about 1 minute manually)  
- Designed for schools with 3,200+ students  
- Eliminates manual data entry — staff only need to scan and print  

---

## Features  
- Barcode scanner input to capture Student ID  
- Database lookup for student first name, last name, and grade  
- Local system date and time integration  
- GUI preview before printing  
- Automatic printing with a single click  
- Saves significant staff time compared to manual processes  

---

## Technology Stack  
- **Language:** Python  
- **GUI Framework:** Tkinter / PyQt (depending on implementation)  
- **Database:** SQLite / MySQL (configurable)  
- **Packaging:** PyInstaller for `.exe` deployment  
- **Barcode Input:** Standard USB barcode scanner  
