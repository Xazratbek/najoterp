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
        self.cur.execute("SELECT oqituvchilar.id FROM oqituvchilar JOIN profiles ON oqituvchilar.profil_id=profiles.id WHERE telefon=%s",(telefon_raqam,))
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

    def create_profile(self) -> int:
        ism = input_nonempty("Ismingizni kiriting: ")
        familiya = input("Familiyangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
        telefon_raqam = input_nonempty("Telefon raqamingizni kiriting\nNamuna 998939498849: ")
        email  = input("Emailingizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi): ") or None
        parol = getpass.getpass("Parolni kiriting: ")
        birth = input("Tug'ilgan sanangizni kiriting (Bo'sh bo'lishi mumkin Enter: O'tkazib yuborsangiz bo'ladi)\nFormat Yil-Oy-Kun: ") or None
        role = role
        hashlangan_parol = hash_password(parol)
        self.cur.execute("INSERT INTO profiles(ism,familiya,telefon,email,parol_hash,tugilgan_sana,role) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id",(ism,familiya,telefon_raqam,email,hashlangan_parol,birth,role))
        profil_id = self.cur.fetchone()[0]
        self.conn.commit()
        return profil_id

    def add_talaba(self,profil_id: int, talaba_kodi: int, qabul_qilingan_sana) -> int:
        self.cur.execute("INSERT INTO talabalar(profil_id,talaba_kodi,qabul_qilingan_sana) VALUES(%s,%s,%s) RETURNING id;",(profil_id,talaba_kodi,qabul_qilingan_sana))
        talaba_id = self.cur.fetchone()[0]
        self.conn.commit()
        return talaba_id

    def add_teacher(self,profil_id: int, mutaxassislik: str, tajriba_yillari: int, ish_boshlagan_sana) -> int:
        self.cur.execute("INSERT INTO oqituvchilar(profil_id,mutaxassislik,tajriba_yillari, ish_boshlagan_sana) VALUES(%s,%s,%s,%s) RETURNING id;",(profil_id,mutaxassislik,tajriba_yillari,ish_boshlagan_sana))
        teacher_id = self.cur.fetchone()[0]
        self.conn.commit()
        return teacher_id

    def get_student_groups(self,student_id: int):
        self.cur.execute("SELECT guruhlar.nomi AS guruh_nomi, guruhlar.boshlanish_sanasi AS boshlanish_vaqti, guruhlar.tugash_sanasi AS tugash_sanasi, kurslar.nomi AS kurs_nomi, profiles.ism AS oqituvchi_ismi FROM guruh_talabalari JOIN talabalar ON guruh_talabalari.talaba_id=talabalar.id JOIN guruhlar ON guruh_talabalari.guruh_id=guruhlar.id JOIN kurslar ON guruhlar.kurs_id=kurslar.id JOIN oqituvchilar on guruhlar.asosiy_oqituvchi_id=oqituvchilar.id JOIN profiles ON oqituvchilar.profil_id=profiles.id WHERE guruh_talabalari.talaba_id=%s",(student_id,))
        my_groups = self.cur.fetchone()
        return my_groups

    def add_guruh(self,teacher_id: int):
        kurslar = self.get_courses()
        kurs_id = input_nonempty(f"Mavjud kurslar:\n{kurslar}\nKurs idsini tanlang: ")
        nomi = input_nonempty("Kurs nomini kiriting: ")
        boshlanish_sanasi = input_nonempty("Kurs boshlanish sanasini kiriting(Format: Yil-oy-kun): ")
        tugash_sanasi = input_nonempty("Tugash sanasini kiriting(Format: Yil-oy-kun): ")
        support_teacher_id = input_nonempty("Support teacher ID sini kiriting: ")
        self.cur.execute("INSERT INTO guruhlar(kurs_id,nomi,boshlanish_sanasi,tugash_sanasi,asosiy_oqituvchi_id,yordamchi_oqituvchi_id) VALUES(%s,%s,%s,%s,%s,%s,) RETURNING id",(kurs_id,nomi,boshlanish_sanasi,tugash_sanasi,teacher_id,support_teacher_id))
        guruh_id = self.cur.fetchone()[0]
        self.conn.commit()
        print("Guruh muvaffaqiyatli yaratildi")
        return guruh_id

    def get_student_homeworks(self,student_id: int):
        self.cur.execute("SELECT uy_vazifalar.sarlavha, uy_vazifalar.tavsif, uy_vazifalar.video_url,uy_vazifalar.muddati FROM vazifa_topshiriqlari JOIN uy_vazifalar ON vazifa_topshiriqlari.uy_vazifa_id=uy_vazifalar.id WHERE is_tugatilgan=False AND student_id=%s;",(student_id))
        homeworks = self.cur.fetchall()
        table.clear()
        table.field_names = [vazifa.name for vazifa in self.cur.description]
        table.add_rows(homeworks)

        return table

    def add_homework(self,teacher_id: int):
        guruhlarim = self.get_teacher_courses_by_id(teacher_id)
        guruh_id = input_nonempty(f"{guruhlarim}\nQaysi guruhga vazifa bermoqchisiz: ")
        sarlavha = input_nonempty("Sarlavhani kiriting: ")
        tavsif = input("Vazifa tavsifini kiriting (Majburiy emas, Skip: Enter): ") or None
        video_url = input("Video urlni kiriting: (Majburiy emas, Skip: Enter): ") or None
        muddati = input_nonempty("Vazifa muddatini kiriting (Format: Yil-oy-kun): ")
        maksimal_xp = input("Vazifa uchun maksimal XP (Majburiy emas, Skip: Enter): ") or None
        maksimal_kumush = input("Vazifa uchun maksimal kumush: (Majburiy emas, Skip: Enter): ") or None

        self.cur.execute("INSERT INTO uy_vazifalar(guruh_id,oqituvchi_id,sarlavha,tavsif,video_url,muddati,maksimal_xp,maksimal_kumush) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,) RETURNING id",(guruh_id,teacher_id,sarlavha,tavsif,video_url,muddati,maksimal_xp,maksimal_kumush))
        homework_id = self.cur.fetchone()[0]
        self.conn.commit()
        return homework_id

    def get_teacher_courses(self,teacher_id: int):
        self.cur.execute("SELECT kurslar.id AS kurs_id, kurslar.nomi AS kurs_nomi, guruhlar.nomi AS guruh_nomi, guruhlar.boshlanish_sanasi AS boshlanish_sanasi, guruhlar.tugash_sanasi AS tugash_sanasi, guruhlar.yordamchi_oqituvchi_id AS support_teacher_id FROM guruhlar JOIN kurslar ON guruhlar.kurs_id=kurslar.id WHERE guruhlar.asosiy_oqituvchi_id=%s", (teacher_id,))
        teacher_courses = self.cur.fetchall()
        table.clear()
        table.field_names = [guruh.name for guruh in self.cur.description]
        for guruh in teacher_courses:
            table.add_row(guruh)
        return table

    def get_courses(self):
        self.cur.execute("SELECT * FROM kurslar")
        kurslar =  self.cur.fetchall()
        table.clear()
        table.field_names = [kurs.name for kurs in self.cur.description]
        for kurs in kurslar:
            table.add_row(kurs)
        return table

    def add_kurs(self):
        nomi = input_nonempty("Kurs nomini kiriting: ")
        narxi = input_nonempty("Kurs narxini kiriting: ")
        kurs_turi = input_nonempty("Kurs turini tanlang:\n1.Standart\n2.Bootcamp\nTanlang: ")
        davomiyligi = input_nonempty("Kurs davomiyligi haftada kiriting: ")
        self.cur.execute("INSERT INTO kurslar(nomi,narxi,kurs_turi,davomiyligi_hafta) VALUES(%s,%s,%s,%s) RETURNING id",(nomi,narxi,kurs_turi,davomiyligi))
        kurs_id = self.cur.fetchone()[0]
        self.conn.commit()
        return kurs_id

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
                is_staff = True
                break
            else:
                print("Login yoki parol xato Iltimos tekshirib qaytadan kiriting\n")
                continue

        elif menu == 2:
            if choose == 2:
                profil_id = erp_tizimi.create_profile()
                talaba_kodi = generate_talaba_kodi()
                qabul_qilingan_sana = datetime.now()
                student_id = erp_tizimi.add_talaba(int(profil_id),int(talaba_kodi),qabul_qilingan_sana)
                print(student_id)
                saqlangan_profil_id = profil_id
                talaba_id = student_id
                print(f"Sizning talaba kodingiz: {talaba_kodi}\nIltimos talaba kodingizni yoddan chiqarmang u login uchun kerak bo'ladi\n")
                print("Muvaffaqiyatli ro'yxatdan o'tdingiz :)")
                break

            elif choose == 1:
                profil_id = erp_tizimi.create_profile()
                mutaxassislik = input_nonempty("Mutaxassisligingizni kiriting: ")
                tajriba_yillari = input_nonempty(f"Necha yillik tajribaga egasiz {mutaxassislik}-sohasida: ")
                ish_boshlagan_sana = datetime.now()
                teacher_id = erp_tizimi.add_teacher(profil_id,mutaxassislik,tajriba_yillari,ish_boshlagan_sana)
                teacher_id = teacher_id
                print(f"Muvaffaqiyatli ro'yxatdan o'tdingiz :). Sizning id: {teacher_id}")
                is_staff = True
                break

        elif menu == 0:
            print("Dasturdan foydalanganingiz uchun rahmat :)")
            break

    except KeyboardInterrupt:
        print("\nDasturdan foydalanganingiz uchun rahmat :)")
        break

student_menu = "1.Mening Guruhlarim\n2.Uyga Vazifalar\n3.To'lovlarim\n4. Ko'rsatgichlarim\n5. Rating\n6.Do'kon\n7.Qo'shimcha darslar\n8.Sozlamalar"
teacher_menu = "1.Mening Guruhlarim\n2.Uyga vazifa berish\n3.Guruh qo'shish\n4.Kurs qo'shish\n5.Sozlamalar"

while True:
    try:
        if not is_staff:
            student_menu = int(input(f"{student_menu}\nTanlang: "))
            if student_menu == 1:
                erp_tizimi.get_student_groups(talaba_id)

            elif student_menu == 2:
                erp_tizimi.get_student_homeworks(talaba_id)

            elif student_menu == 3:
                pass

            elif student_menu == 4:
                pass

            elif student_menu == 5:
                pass

            elif student_menu == 6:
                pass

            elif student_menu == 7:
                pass

            elif student_menu == 8:
                pass

        else:
            teacher_menu = int(input(f"{teacher_menu}" + "\nTanlang: "))
            if teacher_menu == 1:
                print(erp_tizimi.get_teacher_courses(teacher_id))

            elif teacher_menu == 2:
                print(erp_tizimi.add_homework(teacher_id))

            elif teacher_menu == 3:
                print(erp_tizimi.add_guruh(teacher_id))

            elif teacher_menu == 4:
                print(erp_tizimi.add_kurs())
                continue

    except KeyboardInterrupt:
        print("Dasturdan foydalanganingiz uchun rahmat :) ")
        break
