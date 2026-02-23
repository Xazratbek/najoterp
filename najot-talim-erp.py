import psycopg2
from prettytable import PrettyTable
import getpass
import bcrypt
from datetime import datetime
import random


from prettytable import PrettyTable
table = PrettyTable()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        stored_hash.encode()
    )

def input_nonempty(msg):
    while True:
        s = input(msg).strip()
        if s:
            return s
        print("Bo'sh bo'lmasin.")

def generate_talaba_kodi() -> int:
    return random.randint(1111,99999)

class Database:
    def __init__(self, dbname: str, user: str, password: str, host: str, port: int):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def get_db(self):
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }


class NajotTalimErp:
    def __init__(self, database: Database, name: str):
        self.database = database
        self.name = name
        self.conn = psycopg2.connect(**database.get_db())
        self.cur = self.conn.cursor()

    def __str__(self):
        return f"{self.name.title()}-tizimiga xush kelibsiz"

    def check_teacher_login(self, telefon: str, password: str) -> bool:
        self.cur.execute("SELECT profiles.parol_hash FROM profiles WHERE telefon=%s",(telefon,))
        row =  self.cur.fetchone()
        if not row:
            return False

        stored_hash = row[0]
        return bcrypt.checkpw(password.encode(),stored_hash.encode())

    def get_teacher_id_by_telefon(self,telefon_raqam: str) -> int | None:
        self.cur.execute("SELECT oqituvchilar.id FROM oqituvchilar JOIN profiles ON oqituvchilar.profil_id=profiles.id WHERE telefon_raqam=%s",(telefon_raqam,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def check_student_login(self,talaba_kodi: int, parol: str) -> bool:
        self.cur.execute("SELECT profiles.parol_hash FROM profiles JOIN talabalar ON profiles.id=talabalar.profil_id WHERE talaba_kodi=%s",(talaba_kodi,))
        row = self.cur.fetchone()
        if not row:
            return False

        stored_hash = row[0]

        return bcrypt.checkpw(
            parol.encode(),
            stored_hash.encode()
        )

    def create_profile(self,ism: str,familiya: str,telefon_raqam: str, email: str,hashlangan_parol: str, birth,role: str) -> int:
        self.cur.execute("INSERT INTO profiles(ism,familiya,telefon,email,parol_hash,tugilgan_sana,role) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id",(ism,familiya,telefon_raqam,email,hashlangan_parol,birth,role))
        profil_id = self.cur.fetchone()[0]
        self.conn.commit()
        return profil_id

    def add_talaba(self,profil_id: int, talaba_kodi: int, qabul_qilingan_sana) -> int:
        self.cur.execute("INSERT INTO talabalar(profil_id,talaba_kodi,qabul_qilingan_sana) VALUES(%s,%s,%s) RETURNING id;",(profil_id,talaba_kodi,qabul_qilingan_sana))
        talaba_id = self.cur.fetchone()[0]
        self.conn.commit()
        return talaba_id


database = Database("najottalimerp","xazratbek","1967","localhost",5432)
erp_tizimi = NajotTalimErp(database,"Najot ta'lim ERP")

saqlangan_profil_id = 0
talaba_kodi = 0
talaba_id = 0
teacher_id = 0
is_staff = False

while True:
    try:
        choose = int(input("1.O'qituvchi\n2.O'quvchi\nRolingizni tanlang: "))
        menu = int(input("1. Tizimga kirish\n2. Ro'yxatdan o'tish\nTanlang: "))

        if menu == 1 and choose == 2:
            talaba_kodi  = input_nonempty("Talaba kodingizni kiriting: ")
            parol = getpass.getpass("Parolni kiriting: ")
            if erp_tizimi.check_student_login(talaba_kodi,parol):
                print("Tizimga muvaffaqiyatli kirdingiz\n")
                talaba_kodi = talaba_kodi
                break
            else:
                print("Login yoki parol xato Iltimos tekshirib qaytadan kiriting\n")
                continue

        elif menu == 1 and choose == 1:
            telefon_raqam = input_nonempty("Telefon raqamingizni kiriting: ")
            parol = getpass.getpass("Parolingizni kiriting: ")
            if erp_tizimi.check_teacher_login(telefon_raqam,parol):
                teacher_id = erp_tizimi.get_teacher_id_by_telefon(telefon_raqam)
                print("Tizimga muvaffaqiyatli kirdingiz\n")
                break
            else:
                print("Login yoki parol xato Iltimos tekshirib qaytadan kiriting\n")
                continue

        elif menu == 2:
            if choose == 2:
                ism = input_nonempty("Ismingizni kiriting: ")
                familiya = input("Familiyangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
                telefon_raqam = input_nonempty("Telefon raqamingizni kiriting\nNamuna 998939498849: ")
                email  = input("Emailingizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
                parol = getpass.getpass("Parolni kiriting: ")
                birth = input("Tug'ilgan sanangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi)\nFormat Yil-Oy-Kun: ") or None
                role = "student"
                hashlangan_parol = hash_password(parol)
                profil_id = erp_tizimi.create_profile(ism,familiya,telefon_raqam,email,hashlangan_parol,birth,role)
                talaba_kodi = generate_talaba_kodi()
                qabul_qilingan_sana = datetime.now()
                student_id = erp_tizimi.add_talaba(int(profil_id),int(talaba_kodi),qabul_qilingan_sana)
                print(student_id)
                saqlangan_profil_id = profil_id
                talaba_id = student_id
                print(f"Sizning talaba kodingiz: {talaba_kodi}\nIltimos talaba kodingizni yoddan chiqarmang u login uchun kerak bo'ladi\n")

            elif choose == 1:
                ism = input_nonempty("Ismingizni kiriting: ")
                familiya = input("Familiyangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
                telefon_raqam = input_nonempty("Telefon raqamingizni kiriting\nNamuna 998939498849: ")
                email  = input("Emailingizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
                parol = getpass.getpass("Parolni kiriting: ")
                birth = input("Tug'ilgan sanangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi)\nFormat Yil-Oy-Kun: ") or None
                role = "teacher"
                hashlangan_parol = hash_password(parol)
                profil_id = erp_tizimi.create_profile(ism,familiya,telefon_raqam,email,hashlangan_parol,birth,role)
                mutaxassislik = input_nonempty("Mutaxassisligingizni kiriting: ")
                tajriba_yillari = input_nonempty(f"Necha yillik tajribaga egasiz {mutaxassislik}-sohasida: ")
                ish_boshlagan_sana = datetime.now()
                teacher_id = erp_tizimi.add_teacher(profil_id,mutaxassislik,tajriba_yillari,ish_boshlagan_sana)

        elif menu == 0:
            print("Dasturdan foydalanganingiz uchun rahmat :)")
            break

    except KeyboardInterrupt:
        print("\nDasturdan foydalanganingiz uchun rahmat :)")
        break

student_menu = "1.Mening Guruhlarim\n2.Uyga Vazifalar\n3.To'lovlarim\n4. Ko'rsatgichlarim\n5. Rating\n6.Do'kon\n7.Qo'shimcha darslar\n8.Sozlamalar"
teacher_menu = "1.Mening Guruhlarim\n2.Uyga vazifa berish\n3.Sozlamalar"

while True:
    try:
        if is_staff:
            student_menu = int(input(student_menu + "\nTanlang: "))

        else:
            teacher_menu = int(input(teacher_menu + "\nTanlang: "))

    except KeyboardInterrupt:
        print("Dasturdan foydalanganingiz uchun rahmat :) ")
        break
