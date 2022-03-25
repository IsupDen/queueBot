import datetime
import sqlite3

conn = sqlite3.connect('queue.db')
cur = conn.cursor()


def create_db():
    cur.execute('PRAGMA foreign_keys=on')
    cur.execute('CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS subjects(lab_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL , subject TEXT, '
                'number INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS queue(id INTEGER, lab_id INTEGER, date TEXT, PRIMARY KEY(id, lab_id), '
                'FOREIGN KEY (id) REFERENCES students(id), FOREIGN KEY (lab_id) REFERENCES subjects(lab_id))')
    conn.commit()


def add_lab(id, subject, number):
    record = cur.execute('SELECT * FROM queue WHERE id=? AND lab_id=(SELECT lab_id FROM subjects WHERE subject=? AND '
                         'number=?)', (id, subject, number))
    if not record.fetchone():
        current_date = datetime.datetime.now()
        current_date_string = current_date.strftime('%y/%m/%d %H:%M:%S')
        cur.execute('INSERT INTO queue VALUES (?, (SELECT lab_id FROM subjects WHERE subject=? AND '
                    'number=?), ?)', (id, subject, number, current_date_string))
        conn.commit()
        return 'Вы успешно добавлены в очередь!'
    else:
        return 'Вы уже находитесь в очереди на эту лабораторную работу!'


def remove_lab(id, subject, number):
    cur.execute('DELETE FROM queue WHERE id=? AND lab_id=(SELECT lab_id FROM subjects WHERE subject=? AND number=?)',
                (id, subject, number))
    conn.commit()
    return 'Вы успешно удалены из очереди!'


def show(subject):
    cur.execute('SELECT name, number from students JOIN queue ON students.id=queue.id JOIN subjects ON '
                'queue.lab_id=subjects.lab_id WHERE subject=? ORDER BY date', (subject,))
    return cur.fetchall()


def register(id, name):
    cur.execute('INSERT INTO students VALUES (?, ?)', (id, name))
    conn.commit()
    return 'Вы успешно зарегистрированы!'


def show_records(id):
    cur.execute('SELECT subject, number from students JOIN queue ON students.id=queue.id JOIN subjects ON '
                'queue.lab_id=subjects.lab_id WHERE students.id=?', (id,))
    return cur.fetchall()


if __name__ == '__main__':
    create_db()

