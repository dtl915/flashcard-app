# Flashcard App

A desktop flashcard application for vocabulary review built with Python, Tkinter, and MySQL.

## Features

- Review words by category/tag
- Track review progress (remember/forget counts)
- Import words from XML files
- Move words between groups
- Select all/individual categories for review
- Keyboard shortcuts for quick review

## Requirements

- Python 3.14+
- MySQL Server
- MySQL Workbench (optional, for database management)

## Installation

1. **Clone the repository**
   ```
   git clone <repository-url>
   cd flashcard-app
   ```

2. **Install Python dependencies**
   ```
   pip install sqlalchemy pymysql
   ```

3. **Set up MySQL database**

   Open MySQL Workbench and run:
   ```sql
   CREATE DATABASE flashcard_db;

   USE flashcard_db;

   CREATE TABLE words (
       word VARCHAR(60) PRIMARY KEY,
       `explain` TEXT,
       needreview BOOLEAN,
       tag VARCHAR(50),
       hide BOOLEAN,
       reviewTimes SMALLINT,
       forgetTimes SMALLINT,
       lastForgetTime DATETIME,
       lastReviewTime DATETIME
   );
   ```

4. **Configure database connection**

   Edit `flashcard.py` line 19 with your MySQL credentials:
   ```python
   DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost/flashcard_db"
   ```

## Usage

Run the application:
```
python flashcard.py
```

### Main Window
- Select word categories to review using checkboxes
- Click **Start Review** to begin reviewing selected words
- Click **Import Data** to import words from an XML file
- Right-click a category to move words to a different group

### Review Window
- Press **Down Arrow** or click button to show word explanation
- Press **Left Arrow** to mark word as remembered
- Press **Right Arrow** to mark word as forgotten
- Press **Up Arrow** to go back to previous word

## XML Import Format

```xml
<words>
    <item>
        <word>example</word>
        <phonetic>/ɪɡˈzæmpəl/</phonetic>
        <trans>n. an instance serving as a model</trans>
        <tags>vocabulary</tags>
    </item>
</words>
```

## License

MIT License
