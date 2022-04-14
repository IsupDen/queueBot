import datetime
import pymysql


def connect():
    global conn
    conn = pymysql.connect(host='5.181.76.76', user='isupden',
                       password='Denar332347..', db='queuebot')
    global cur
    cur = conn.cursor()


def create_db():
    cur.execute('CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY, name VARCHAR(50))')
    cur.execute('CREATE TABLE IF NOT EXISTS subjects(lab_id INTEGER NOT NULL AUTO_INCREMENT, '
                'subject VARCHAR(20), number INTEGER, PRIMARY KEY(lab_id))')
    cur.execute('CREATE TABLE IF NOT EXISTS queue(id INTEGER, lab_id INTEGER, date DATETIME, PRIMARY KEY(id, lab_id), '
                'FOREIGN KEY (id) REFERENCES students(id), FOREIGN KEY (lab_id) REFERENCES subjects(lab_id))')
    conn.commit()


def add_lab(id, subject, number):
    cur = conn.cursor()
    cur.execute('SELECT * FROM queue JOIN subjects ON queue.lab_id = subjects.lab_id WHERE id=%s AND '
                'subject=%s AND number=%s', (id, subject, number))
    if not cur.fetchone():
        current_date = datetime.datetime.now()
        current_date_string = current_date.strftime('%y/%m/%d %H:%M:%S')
        cur.execute('INSERT INTO queue VALUES (%s, (SELECT lab_id FROM subjects WHERE subject=%s AND '
                    'number=%s), %s)', (id, subject, number, current_date_string))
        conn.commit()
        return True
    else:
        return False


def remove_lab(id, subject, number):
    cur = conn.cursor()
    cur.execute('DELETE FROM queue WHERE id=%s AND lab_id=(SELECT lab_id FROM subjects WHERE subject=%s AND number=%s)',
                (id, subject, number))
    conn.commit()
    return 'Вы успешно удалены из очереди!'


def show(subject):
    cur = conn.cursor()
    cur.execute('SELECT name, number from students JOIN queue ON students.id=queue.id JOIN subjects ON '
                'queue.lab_id=subjects.lab_id WHERE subject=%s ORDER BY date', (subject,))
    return cur.fetchall()


def register(id, name):
    cur = conn.cursor()
    cur.execute('SELECT * from students WHERE id=%s;', (id,))
    if not cur.fetchall():
        cur.execute('INSERT INTO students VALUES (%s, %s)', (id, name))
        conn.commit()
        return 'Вы успешно зарегистрированы!'
    else:
        cur.execute('UPDATE students SET name=%s WHERE id=%s', (name, id))
        conn.commit()
        return 'Вы успешно сменили имя!'


def show_records(id):
    cur = conn.cursor()
    cur.execute('SELECT subject, number from students JOIN queue ON students.id=queue.id JOIN subjects ON '
                'queue.lab_id=subjects.lab_id WHERE students.id=%s', (id,))
    return cur.fetchall()


def add_by_name(name, subject, number):
    cur = conn.cursor()
    cur.execute('SELECT * from students JOIN queue ON students.id=queue.id JOIN subjects ON '
                'queue.lab_id=subjects.lab_id WHERE name=%s AND subject=%s AND number=%s', (name, subject, number))
    if not cur.fetchone():
        current_date = datetime.datetime.now()
        current_date_string = current_date.strftime('%d/%m/%y %H:%M:%S')
        cur.execute('INSERT INTO queue VALUES ((SELECT id FROM students WHERE name=%s), (SELECT lab_id FROM subjects '
                    'WHERE subject=%s AND number=%s), %s)', (name, subject, number, current_date_string))
        conn.commit()
        return 'Вы успешно добавлены в очередь!'
    else:
        return 'Вы уже находитесь в очереди на эту лабораторную работу!'


def get_name(id):
    cur = conn.cursor()
    cur.execute('SELECT name from students WHERE id=%s', (id,))
    return cur.fetchone()


if __name__ == '__main__':
    create_db()
