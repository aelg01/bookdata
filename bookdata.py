import sqlite3
import json
import csv
import datetime

VERSION = 1
LAYOUT = ""

conn = sqlite3.connect('bookdata.db')
cursor = conn.cursor()

flag = True
fields = ["ID","Title","Author","Date","Experience","Topic","Category","Acquisition","Priority"]
lowerFields = [i.lower() for i in fields]

def columnWidths(data):
    column_widths: list[int] = []
    if data is None:
        return column_widths
    multi = any(isinstance(x, tuple) for x in data)
    for col in range(len(fields)):
        if multi:    
            max_len = max(len(str(row[col])) for row in data)
        else:
            max_len = len(str(data[col]))
        max_len = max(max_len, len(fields[col]))  # ensure header fits
        column_widths.append(max_len)
    
    return column_widths

def addBook():
    title = input("What is the book called: ")
    author = input("Who is the author: ")
    print("0 - None\n1 - Partially read it\n2 - Read it online\n3 - Read it physically in the past\n4 - Digitally own it\n5 - Currently own it")
    experience = int(input("Which number best matches the book: "))
    topic = input("What topic does it fall under: ")
    category = input("What type of book is it: ")
    acquisition = float(input("How likely are you to get it, as a decimal: "))
    priority = float(input("How important is it for you to get it, as a decimal: "))
    cursor.execute("INSERT OR IGNORE INTO books (title, author, experience, topic, category, acquisition, priority, date) VALUES(?, ?, ?, ?, ?, ?, ?, date())",(title, author, experience, topic, category, acquisition, priority))
    conn.commit()
    print("Record added")

def searchBook():
    searchColumn = input("What field do you want to search by: ").strip().lower()
    if searchColumn not in lowerFields:
        print("Invalid field")
        return
    searchTerm = input("What book do you want to search for: ")
    cursor.execute(f"SELECT * FROM books WHERE {searchColumn} = ?",(searchTerm,))
    row = cursor.fetchall()
    if len(row) == 0:
        print("Sorry, this record isn't present")
    else:
        columnData = columnWidths(row)
        global LAYOUT
        LAYOUT = " | ".join("{:<" + str(w) + "}" for w in columnData)
        print(LAYOUT.format(*fields))
        for x in row:
            print(LAYOUT.format(*x))

def printall():
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    columnData = columnWidths(rows)
    global LAYOUT
    LAYOUT = " | ".join("{:<" + str(w) + "}" for w in columnData)
    print(LAYOUT.format(*fields))
    for row in rows:
        print(LAYOUT.format(*row))

def options():
    print("0 - exit")
    print("1 - add a new record")
    print("2 - search records")
    print("3 - print all records")
    print("4 - update a record")
    print("5 - export data")
    print("6 - load new data")
    print("7 - delete book")
    enter = int(input("What do you pick? "))
    return enter

def updateBook():
    idNum = 0
    idKnown = input("If you know the ID for your book, enter it, otherwise press enter: ")
    while not idKnown.isnumeric():
        print("Search for the book by title to find its ID")
        searchBook()
        idKnown = input("Now you have the ID, please enter it: ")
    
    idNum = int(idKnown)
    cursor.execute("SELECT * FROM books WHERE id = ?",(idNum,))
    record = cursor.fetchone()
    newRecord = []
    
    for i in range(len(record)):
        t = type(record[i])
        if fields[i] != "ID" and fields[i] != "Date":
            print(f"This is the value of {fields[i].lower()}: {record[i]}")
            newVal = input("Type a value to update or leave it blank to maintain: ")
        else:
            newVal = ""
        
        if fields[i] == "Date":
            newRecord.append("date")
        elif newVal != "":
            newRecord.append(t(newVal))
        else:
            newRecord.append(record[i])
        
    del newRecord[0]
    newRecord.remove("date")
    
    cursor.execute("""UPDATE books SET (title, author, experience, topic, category, acquisition, priority, date) = (?, ?, ?, ?, ?, ?, ?, date()) WHERE id = ?""", newRecord + [idNum])
    conn.commit()
    print("Update finished")
        
def exportData():
    print("Which one of these use-cases suits why you're exporting?")
    print("1 - exporting to another device")
    print("2 - exporting for a spreadsheet")
    form = int(input())
    
    filename = input("What do you want to name the file (defaults to bookdata): ")
    if filename == "":
        filename = "bookdata"
    
    if form == 1:
        exportJSON(filename)
    elif form == 2:
        exportCSV(filename)
    

def exportJSON(pathname):
    date = str(datetime.datetime.now())
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    exportDict = {"meta":
                  {"app": "bookdata",
                   "version": VERSION,
                   "export_date": date},
                  "data":
                  rows}
    with open(pathname+".json",'w', encoding="utf-8") as f:
        json.dump(exportDict, f)
    print("File created")

def exportCSV(pathname):
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    with open(pathname+".csv", "w", newline='', encoding="utf-8") as f:
        datawrite = csv.writer(f)
        datawrite.writerow(fields)
        datawrite.writerows(rows)
    print("File created")

def loadJSON():
    pathname = input("What name is the file: ")
    print("What do you want to happen when books in the database and file have the same title?")
    print("0 - cancel file")
    print("1 - replace the original record")
    print("2 - keep the original record")
    disambig = int(input("Enter the number corresponding to your preference: "))
    if disambig == 0:
        return
    try:
        with open(pathname+".json","r", encoding="utf-8") as f:
            importDict = json.load(f)
            if importDict["meta"]["version"] != VERSION:
                print("Version error - you might need to contact the developer to resolve")
            else:
                data = importDict["data"]
                for x in data:
                    x[0] = None
                    if disambig == 1:
                        cursor.execute("INSERT OR REPLACE INTO books VALUES(?,?,?,?,?,?,?,?,?)", x)
                    elif disambig == 2:
                        cursor.execute("INSERT OR IGNORE INTO books VALUES(?,?,?,?,?,?,?,?,?)", x)
                    else:
                        print("Error - you did not type 1 or 2")
                conn.commit()
    except FileNotFoundError:
        print("Error - file not found")

def deleteBook():
    idNum = 0
    idKnown = input("If you know the ID for your book, enter it, otherwise press enter: ")
    while not idKnown.isnumeric():
        print("Search for the book by title to find its ID")
        searchBook()
        idKnown = input("Now you have the ID, please enter it: ")
    
    idNum = int(idKnown)
    cursor.execute("DELETE FROM books WHERE id = ?",(idNum,))
    conn.commit()
    print("Book deleted")

cursor.execute("""CREATE TABLE IF NOT EXISTS books
(id INTEGER PRIMARY KEY, title TEXT UNIQUE, author TEXT, date TEXT, experience INTEGER, topic TEXT, category TEXT, acquisition REAL, priority REAL)""")

print("Welcome to the BookData app, a database to store your book wishlist!")

while flag:
    print("="*60)
    choice = options()
    if choice == 0:
        flag = False
    elif choice == 1:
        addBook()
    elif choice == 2:
        searchBook()
    elif choice == 3:
        printall()
    elif choice == 4:
        updateBook()
    elif choice == 5:
        exportData()
    elif choice == 6:
        loadJSON()
    elif choice == 7:
        deleteBook()
    else:
        print("Invalid option, sorry")


conn.commit()
conn.close()
