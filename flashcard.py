import random
import os

#import tkinter widgets
from tkinter import Tk, Button, Label, Checkbutton, IntVar, StringVar, Frame, Scrollbar, Canvas, RIGHT, Y, LEFT, TOP,BOTH, LabelFrame, Toplevel, messagebox, Text, BOTTOM, filedialog, Menu, OptionMenu, simpledialog

#import database library
from sqlalchemy.sql import text  # Import the text function
from sqlalchemy import create_engine, Column, String, Boolean, SmallInteger, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

from datetime import datetime
import xml.etree.ElementTree as ET



# Database connection configuration
DATABASE_URL = "mssql+pyodbc://Harry-Duan/Word?driver=SQL+Server&trusted_connection=yes&charset=utf8"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Define the database model
Base = declarative_base()


class Word(Base):
    __tablename__ = 'words1'
    word = Column(String(60), primary_key=True)
    explain = Column(String)
    needreview = Column(Boolean)
    tag = Column(String(50))
    hide = Column(Boolean)
    reviewTimes = Column(SmallInteger)
    forgetTimes = Column(SmallInteger)
    lastForgetTime = Column(DateTime)
    lastReviewTime = Column(DateTime)


# Create Tkinter GUI
class WordApp:
    def __init__(self, root):
        #initialize the main window
        self.root = root
        self.root.title("Daily Word Review")
        self.root.geometry("600x400")

        # Main frame and layout setup
        main_frame = Frame(root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
        #initialize a canvas and a scrollbar for checkbox_frame
        group_lst_canvas=Canvas(main_frame)
        scrollbar = Scrollbar(group_lst_canvas, orient="vertical",command=group_lst_canvas.yview)        
        group_lst_canvas.configure(yscrollcommand=scrollbar.set)
        group_lst_canvas.pack(side=LEFT,fill=BOTH,expand=True)
        scrollbar.pack(side=RIGHT,fill="y")


        # Left bordered frame with Checkbutton list
        checkbox_frame = LabelFrame(
            group_lst_canvas, text="Word Categories", padx=5, pady=5)

        #bind the scrollbar to checkbox_frame
        group_lst_canvas.create_window((0,0),window=checkbox_frame,anchor='nw')
        checkbox_frame.pack(side=LEFT, fill=BOTH, expand=True)

        #initialize a checkbox_container to contain a list of word groups
        self.checkbox_container = Frame(checkbox_frame)
        self.checkbox_container.pack(fill=BOTH, expand=True)
        
        #Set function for the context menu showed up when right click on the groups listed in checkbox_frame
        self.context_menu = Menu(checkbox_frame, tearoff=0)
        self.context_menu.add_command(
            label="Change Grouping", command=lambda: self.start_change_grouping())

        self.checkbox_vars = []  # Stores Checkbutton states

        # A frame to contain the buttons on the right
        button_frame = Frame(main_frame)
        button_frame.pack(side=LEFT, fill=Y, padx=10)

        # Review button, to launch a review window
        self.review_button = Button(
            button_frame, text="Start Review", state="disabled", command=self.start_review, width=15)
        self.review_button.pack(pady=5)

        # Import data button, to import words from an xml file
        self.refresh_button = Button(
            button_frame, text="Import Data", command=self.import_data, width=15)
        self.refresh_button.pack(pady=5)

        # A button to quit the program
        self.exit_button = Button(
            button_frame, text="Exit", command=root.quit, width=15)
        self.exit_button.pack(pady=5)

        # Bottom section with select all checkbox button and label showing amount of words selected
        self.main_page_select_all_var = IntVar()
        self.select_all_check = Checkbutton(
            root, text="Select All", variable=self.main_page_select_all_var, command=self.select_all_groups)
        self.select_all_check.pack(side=LEFT, padx=10, pady=5)

        self.word_count_label = Label(root, text="Selected Word Count: 0")
        self.word_count_label.pack(side=LEFT, padx=10)

        # Initialize the main window
        self.load_categories()

    def start_change_grouping(self):

        #set up window
        self.root.withdraw()
        self.change_group_window = Toplevel(self.root)
        self.change_group_window.title("Change Grouping")
        self.change_group_window.geometry("800x400")  # Adjust window size
        self.change_group_window.protocol("WM_DELETE_WINDOW", self.exit_change_grouping)

        #access words/categories

        self.change_grouping_word_lst =  session.query(Word).filter((Word.tag==self.change_from_group)).all()


        self.categories = session.query(Word.tag).filter(Word.tag != self.change_from_group).all()

        if self.categories==[]:
            messagebox.showinfo("Add A New Group Before Moving Words!")
            self.exit_change_grouping()

        top_button_frame=Frame(self.change_group_window)
        top_button_frame.pack(side=TOP,fill=BOTH,padx=20,pady=5)

        # put buttons
        self.change_target_group = StringVar()
        self.target_group_lst = OptionMenu(
            top_button_frame, self.change_target_group, "Move to a New Group", *[category[0] for category in self.categories])
        self.target_group_lst.pack(side=LEFT,padx=30,pady=5)
        
        self.change_target_group.set("Click to Select Group")
        self.change_target_group.trace_add("write",lambda read, write, unset :self.add_new_group())

        self.change_group_select_all_var = IntVar()
        change_group_select_all_button = Checkbutton(
            top_button_frame, text="Select All", 
            variable=self.change_group_select_all_var, command=self.change_group_select_all)
        change_group_select_all_button.pack(side=LEFT,padx=30,pady=5)
        
        self.change_group_word_count_label=Label(top_button_frame,text='0')
        self.change_group_word_count_label.pack(side=LEFT,padx=30,pady=5)
        
        #Canvas for scrollbar and list of words

        self.change_group_canvas=Canvas(self.change_group_window)
        self.change_group_scrollbar=Scrollbar(self.change_group_canvas,orient="horizontal",command=self.change_group_canvas.xview)
        self.change_group_canvas.configure(xscrollcommand=self.change_group_scrollbar.set)
        self.change_group_canvas.pack(side=TOP,fill=BOTH,expand=True)
        self.change_group_scrollbar.pack(side=BOTTOM,fill='x')

        self.selected_words = []
        
        change_group_containter = LabelFrame(self.change_group_canvas,text="Select Words")
        self.change_group_canvas.create_window((0,0),window=change_group_containter,anchor='nw')
        change_group_containter.pack(side=TOP,fill=BOTH, padx=20, pady=5)


        for id, word in enumerate(self.change_grouping_word_lst):
            var = IntVar()
            checkbox = Checkbutton(
                change_group_containter, text=word.word, variable=var, command=self.update_change_group_word_count)
                
            checkbox.grid(column=id//15, row=id%15, sticky='w')
            
            self.selected_words.append(var)

        
        
        
        bot_button_frame=Frame(self.change_group_window)
        bot_button_frame.pack(side=TOP,fill=BOTH,padx=20,pady=5)



        change_group_button=Button(bot_button_frame,text="Change",command=self.change_group)
        change_group_button.pack(side=LEFT, padx=50, pady=0, anchor="center")

        exit_change_button=Button(bot_button_frame,text="Cancel",command=self.exit_change_grouping)
        exit_change_button.pack(side=LEFT, padx=50, pady=5)

    def add_new_group(self):
        if (self.change_target_group.get()=="Move to a New Group"):
            temp=simpledialog.askstring("Group Name","Enter the Name of New Group")
            if temp=="":
                messagebox.showinfo("Please Enter a Name")
            elif temp in self.categories or temp=="Click to Select Group" or temp == "Move to a New Group" or temp == self.change_from_group:
                messagebox.showinfo("This Name is Used")
            else:
                self.change_target_group.set(temp)
            return


    def change_group(self):
        if self.change_target_group.get()=="Click to Select Group" or self.change_target_group.get() is None:
            messagebox.showinfo("Please Choose a Group")
            return
        for ind,word in enumerate(self.change_grouping_word_lst):
            if self.selected_words[ind].get():
                word.tag=self.change_target_group.get()
                session.commit()
        self.exit_change_grouping()

    

    def update_change_group_word_count(self):
        cnt=0
        for word in self.selected_words:
            cnt+=word.get()
        self.change_group_word_count_label['text']=str(cnt)

        

    def exit_change_grouping(self):
        
        self.change_group_window.destroy()
        self.root.deiconify()
        self.load_categories()


    def change_group_select_all(self):
        for var in self.selected_words:
            var.set(self.change_group_select_all_var.get())

    # Method to import data

    def import_data(self):
        # Clear the words table
        # session.query(Word).delete()
        # session.commit()

        # Path to the XML file
        xml_path = filedialog.askopenfilename()

        if xml_path is None or xml_path == "":
            return

        if not os.path.exists(xml_path):
            messagebox.showerror("Error", f"XML file not found: {xml_path}")
            return

        # Parse the XML file and extract data
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for xmlnode in root:
            word_text = xmlnode.find("word").text.strip()
            phonetic_element = xmlnode.find("phonetic")
            phonetic_text = phonetic_element.text.strip(
            ) if phonetic_element is not None and phonetic_element.text else ""
            trans_text = xmlnode.find("trans").text.strip(
            ) if xmlnode.find("trans") is not None else ""
            tags_text = xmlnode.find("tags").text.strip() if xmlnode.find(
                "tags") is not None else "Uncategorized"

            explain_text = f"{phonetic_text}\n{trans_text}".strip()

            # Insert query
            insert_query = text("""
            INSERT INTO words1 (word, explain, needreview, tag, hide, reviewTimes, forgetTimes) 
            VALUES (:word, :explain, :needreview, :tag, :hide, :reviewTimes, :forgetTimes)
            """)
            values = {
                'word': word_text,
                'explain': explain_text,
                'needreview': True,
                'tag': tags_text,
                'hide': False,
                'reviewTimes': 0,
                'forgetTimes': 0
            }

            try:
                if session.query(Word).filter(Word.word == values["word"]).first() is None:
                    session.execute(insert_query, values)

            except Exception as e:
                print(f"Error inserting data: {e}")

        session.commit()  # Commit transaction

        messagebox.showinfo(
            "Import Complete", "Data successfully refreshed and imported into the database.")
        self.load_categories()  # Refresh category display

    def show_context_box(self, event, tag):
        self.change_from_group = tag
        self.context_menu.post(event.x_root, event.y_root)

    def load_categories(self):
        # Clear existing Checkbuttons
        for widget in self.checkbox_container.winfo_children():
            widget.destroy()

        # Query and group
        try:
            categories = session.query(Word.tag, func.count(
                Word.tag)).group_by(Word.tag).all()
            self.checkbox_vars.clear()  # Clear variable list

            for tag, count in categories:
                tag_display = f"{tag} ({count})"
                var = IntVar()
                checkbox = Checkbutton(
                    self.checkbox_container, text=tag_display, variable=var, command=self.update_word_count)
                checkbox.pack(anchor="w")
                self.checkbox_vars.append(var)
                checkbox.bind("<Button-3>", lambda event,
                              tag=tag: self.show_context_box(event, tag))

            # Reset button and label
            self.word_count_label.config(text="Selected Word Count: 0")
            self.review_button.config(state="disabled")
        except Exception as e:
            print("Error loading categories:", e)

    def start_review(self):
        # hide root
        self.root.withdraw()

        # Get selected categories
        selected_tags = [self.checkbox_container.winfo_children()[i].cget("text").split(" (")[0]
                         for i, var in enumerate(self.checkbox_vars) if var.get() == 1]

        if not selected_tags:
            messagebox.showwarning(
                "Notice", "Please select at least one category for review.")
            return

        # Query all words in selected categories
        self.words_to_review = session.query(Word).filter(
            Word.tag.in_(selected_tags)).all()
        self.word_review_status = [None]*len(self.words_to_review)

        # Shuffle the words
        random.shuffle(self.words_to_review)

        if not self.words_to_review:
            messagebox.showinfo(
                "Notice", "No words available for review in the selected categories.")
            return

        self.current_word_index = 0
        self.review_window = Toplevel(self.root)
        self.review_window.title("Review Words")
        self.review_window.geometry("600x400")  # Adjust window size
        self.review_window.protocol("WM_DELETE_WINDOW", self.exit_review)
        self.progress_label = Label(self.review_window, text="")
        self.progress_label.pack(anchor="n")

        # Initialize and display the first word
        self.show_word()

    def show_word(self):
        if self.current_word_index >= len(self.words_to_review):
            messagebox.showinfo("Review Complete",
                                "All selected words have been reviewed!")
            self.exit_review()
            return

        current_word = self.words_to_review[self.current_word_index]

        # Clear the review window content
        for widget in self.review_window.winfo_children():
            widget.destroy()

        # Display review progress and word
        self.progress_label = Label(self.review_window, text=f"{
                                    self.current_word_index + 1}/{len(self.words_to_review)}", font=("Times New Roman", 12))
        self.progress_label.pack(anchor="ne", padx=10, pady=5)

        # Show word on the top of the page
        Label(self.review_window, text=current_word.word, font=(
            "Times New Roman", 20)).pack(anchor="n", padx=0, pady=8)

        # Create explanation box, initially hidden, below the word
        self.explain_text = Text(self.review_window, height=15, width=65,
                                 wrap="word", state="disabled", font=("Times New Roman", 12))
        # Center alignment with padding
        self.explain_text.pack(pady=10, padx=10, anchor="center")
        self.explain_text.pack_forget()  # Initially hide explanation box

        # Button to show explanation, centered above explanation box
        self.show_meaning_btn = Button(
            self.review_window, text="Click to Show Explanation", command=lambda: self.show_meaning())
        self.show_meaning_btn.pack(anchor="center", pady=80)
        # self.show_meaning_btn.focus_set()  # Set focus to "Show Explanation" button
        self.review_window.bind("<Down>", lambda event: self.show_meaning())

        # Bottom buttons
        button_frame = Frame(self.review_window)
        button_frame.pack(side=BOTTOM, pady=10)

        # Create bottom buttons and save them as instance variables

        self.last_button = Button(
            button_frame, text="Last Word", command=lambda: self.last_word(), width=10)
        self.last_button.pack(side=LEFT, padx=30)
        self.review_window.bind("<Up>", lambda event: self.last_word())

        self.remember_button = Button(
            button_frame, text="Remember", command=lambda: self.remember_word(current_word), width=10)
        self.remember_button.pack(side=LEFT, padx=30)
        self.review_window.bind(
            "<Left>", lambda event: self.remember_word(current_word))

        self.forget_button = Button(
            button_frame, text="Forgot", command=lambda: self.forget_word(current_word), width=10)
        self.forget_button.pack(side=LEFT, padx=30)
        self.review_window.bind(
            "<Right>", lambda event: self.forget_word(current_word))

        self.exit_button = Button(
            button_frame, text="Exit Review", command=lambda: self.exit_review(), width=10)
        self.exit_button.pack(side=LEFT, padx=30)

        # Button list for focus switching
        self.buttons = [self.show_meaning_btn, self.remember_button,
                        self.forget_button, self.exit_button]

        # Bind left and right arrow key events
        # self.review_window.bind("<Left>", lambda event: self.switch_focus(-1))
        # self.review_window.bind("<Right>", lambda event: self.switch_focus(1))
    def last_word(self):
        if (self.current_word_index <= 0):
            return
        self.current_word_index -= 1
        self.show_word()

    def exit_review(self):
        self.root.deiconify()
        self.update_word_status()
        self.review_window.destroy()

    def show_meaning(self):
        # Hide "Show Explanation" button, display explanation box content
        self.show_meaning_btn.pack_forget()
        self.explain_text.config(state="normal")
        self.explain_text.delete("1.0", "end")
        self.explain_text.insert(
            "1.0", self.words_to_review[self.current_word_index].explain)
        self.explain_text.config(state="disabled")
        self.explain_text.pack()  # Display explanation box

        # Update button list to remove "Show Explanation" button
        self.buttons = [self.remember_button,
                        self.forget_button, self.exit_button]
        self.remember_button.focus_set()  # Set focus to "Remember" button

    def switch_focus(self, direction):
        # Find the index of the currently focused button
        focused_widget = self.review_window.focus_get()
        if focused_widget in self.buttons:
            current_index = self.buttons.index(focused_widget)
            # Calculate the index of the next focused button based on direction
            next_index = (current_index + direction) % len(self.buttons)
            # Set focus to the next button
            self.buttons[next_index].focus_set()

    def remember_word(self, word):
        self.word_review_status[self.current_word_index] = True
        self.current_word_index += 1
        self.show_word()

    def forget_word(self, word):
        self.word_review_status[self.current_word_index] = False
        self.current_word_index += 1
        self.show_word()

    def select_all_groups(self):
        select_all = self.main_page_select_all_var.get() == 1
        for var in self.checkbox_vars:
            var.set(1 if select_all else 0)
        self.update_word_count()

    def update_word_count(self):
        count = 0
        for i, var in enumerate(self.checkbox_vars):
            if var.get() == 1:
                text = self.checkbox_container.winfo_children()[i].cget("text")
                num = int(text.split("(")[1][:-1])
                count += num
        self.word_count_label.config(text=f"Selected Word Count: {count}")
        self.review_button.config(state="normal" if count > 0 else "disabled")

    def update_word_status(self):
        for i in range(len(self.words_to_review)):
            current_word = self.words_to_review[i]
            if (self.word_review_status[i] is True):
                current_word.reviewTimes += 1
                current_word.lastReviewTime = datetime.now()
            elif (self.word_review_status[i] is False):
                current_word.forgetTimes += 1
                current_word.lastForgetTime = datetime.now()
            else:
                break
            session.commit()

# Launch Tkinter application
root = Tk()
app = WordApp(root)
root.mainloop()
