import sqlite3
from datetime import datetime, timedelta
import os

class LibrarySystem:
    def __init__(self):
        self.conn = sqlite3.connect('library.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create Books table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            quantity INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1
        )
        ''')
        
        # Create Members table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            join_date DATE DEFAULT CURRENT_DATE
        )
        ''')
        
        # Create Borrowings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowings (
            borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            member_id INTEGER,
            borrow_date DATE DEFAULT CURRENT_DATE,
            due_date DATE,
            return_date DATE,
            FOREIGN KEY (book_id) REFERENCES books (book_id),
            FOREIGN KEY (member_id) REFERENCES members (member_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_book(self, title, author, isbn, quantity=1):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO books (title, author, isbn, quantity, available)
            VALUES (?, ?, ?, ?, ?)
            ''', (title, author, isbn, quantity, quantity))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Error: ISBN already exists")
            return False
    
    def add_member(self, name, email, phone):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO members (name, email, phone)
            VALUES (?, ?, ?)
            ''', (name, email, phone))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Error: Email already exists")
            return False
    
    def borrow_book(self, book_id, member_id, days=14):
        cursor = self.conn.cursor()
        
        # Check if book is available
        cursor.execute('SELECT available FROM books WHERE book_id = ?', (book_id,))
        available = cursor.fetchone()[0]
        
        if available > 0:
            # Update book availability
            cursor.execute('''
            UPDATE books SET available = available - 1
            WHERE book_id = ?
            ''', (book_id,))
            
            # Create borrowing record
            borrow_date = datetime.now()
            due_date = borrow_date + timedelta(days=days)
            
            cursor.execute('''
            INSERT INTO borrowings (book_id, member_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
            ''', (book_id, member_id, borrow_date, due_date))
            
            self.conn.commit()
            return True
        return False
    
    def return_book(self, book_id, member_id):
        cursor = self.conn.cursor()
        
        # Update book availability
        cursor.execute('''
        UPDATE books SET available = available + 1
        WHERE book_id = ?
        ''', (book_id,))
        
        # Update borrowing record
        cursor.execute('''
        UPDATE borrowings 
        SET return_date = CURRENT_DATE
        WHERE book_id = ? AND member_id = ? AND return_date IS NULL
        ''', (book_id, member_id))
        
        self.conn.commit()
        return True
    
    def search_books(self, query):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM books 
        WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        return cursor.fetchall()
    
    def get_overdue_books(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT b.title, m.name, br.due_date
        FROM borrowings br
        JOIN books b ON br.book_id = b.book_id
        JOIN members m ON br.member_id = m.member_id
        WHERE br.return_date IS NULL AND br.due_date < CURRENT_DATE
        ''')
        return cursor.fetchall()
    
    def get_member_borrowings(self, member_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT b.title, br.borrow_date, br.due_date, br.return_date
        FROM borrowings br
        JOIN books b ON br.book_id = b.book_id
        WHERE br.member_id = ?
        ORDER BY br.borrow_date DESC
        ''', (member_id,))
        return cursor.fetchall()

def main():
    library = LibrarySystem()
    
    while True:
        print("\n=== Library Management System ===")
        print("1. Add Book")
        print("2. Add Member")
        print("3. Borrow Book")
        print("4. Return Book")
        print("5. Search Books")
        print("6. View Overdue Books")
        print("7. View Member Borrowings")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            title = input("Enter book title: ")
            author = input("Enter author name: ")
            isbn = input("Enter ISBN: ")
            quantity = int(input("Enter quantity: "))
            if library.add_book(title, author, isbn, quantity):
                print("Book added successfully!")
        
        elif choice == '2':
            name = input("Enter member name: ")
            email = input("Enter email: ")
            phone = input("Enter phone: ")
            if library.add_member(name, email, phone):
                print("Member added successfully!")
        
        elif choice == '3':
            book_id = int(input("Enter book ID: "))
            member_id = int(input("Enter member ID: "))
            if library.borrow_book(book_id, member_id):
                print("Book borrowed successfully!")
            else:
                print("Book not available for borrowing")
        
        elif choice == '4':
            book_id = int(input("Enter book ID: "))
            member_id = int(input("Enter member ID: "))
            if library.return_book(book_id, member_id):
                print("Book returned successfully!")
        
        elif choice == '5':
            query = input("Enter search query: ")
            results = library.search_books(query)
            print("\nSearch Results:")
            for book in results:
                print(f"ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, ISBN: {book[3]}, Available: {book[5]}")
        
        elif choice == '6':
            overdue = library.get_overdue_books()
            print("\nOverdue Books:")
            for book in overdue:
                print(f"Title: {book[0]}, Member: {book[1]}, Due Date: {book[2]}")
        
        elif choice == '7':
            member_id = int(input("Enter member ID: "))
            borrowings = library.get_member_borrowings(member_id)
            print("\nMember Borrowings:")
            for borrow in borrowings:
                print(f"Book: {borrow[0]}, Borrowed: {borrow[1]}, Due: {borrow[2]}, Returned: {borrow[3]}")
        
        elif choice == '8':
            print("Thank you for using the Library Management System!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 
