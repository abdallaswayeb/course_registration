from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from courses.models import Lecture, Student, Section, Material, Enrollment , GradeRecord , MaterialPrerequisite    
from django.contrib import messages
from django.db import IntegrityError
from datetime import date
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json



# --- صفحة رئيسية
def root_redirect(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashbord')
    return redirect('login')


# --- تسجيل الدخول
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashbord')
        return render(request, 'login.html', {'error': 'بيانات الدخول غير صحيحة أو ليس لديك صلاحية.'})
    return render(request, 'login.html')


# --- تسجيل الخروج
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# --- لوحة تحكم الادمن
@login_required
def admin_dashbord(request):
    if not request.user.is_staff:
        return redirect('login')
    return render(request, 'admin_dashbord.html')


# --- صفحة المواد
@login_required
def materials_page(request):
    if not request.user.is_staff:
        return redirect('login')

    materials = Material.objects.all()

    code = request.GET.get('code', '').strip()
    name = request.GET.get('name', '').strip()
    hours = request.GET.get('hours', '').strip()

    if code:
        materials = materials.filter(code__icontains=code)
    if name:
        materials = materials.filter(name__icontains=name)
    if hours:
        materials = materials.filter(hours=hours)

    return render(request, 'materials.html', {'materials': materials})


# --- صفحة الطلاب
@login_required
def students_page(request):
    if not request.user.is_staff:
        return redirect('login')

    students = Student.objects.all()

    # قراءة الفلاتر
    id_student = request.GET.get('id_student', '').strip()
    name = request.GET.get('name', '').strip()
    section = request.GET.get('section', '').strip()

    # تطبيق الفلاتر بطريقة ديناميكية فقط إذا القيم موجودة
    if id_student:
        try:
            students = students.filter(id_student=int(id_student))
        except ValueError:
            students = students.none()  # إدخال غير صالح
    if name:
        students = students.filter(name__icontains=name)
    if section:
        try:
            students = students.filter(section_id=int(section))
        except ValueError:
            pass  # إذا القيمة غير صالحة نتجاهلها

    sections = Section.objects.all()  # لملء dropdown
    return render(request, 'students.html', {'students': students, 'sections': sections})


# --- صفحة الأقسام
def sections_page(request):
    if not request.user.is_staff:
        return redirect('login')

    sections = Section.objects.all()

    # قراءة الفلاتر
    id_section = request.GET.get('id_section', '').strip()
    name = request.GET.get('name', '').strip()
    description = request.GET.get('description', '').strip()

    # تطبيق الفلاتر
    if id_section:
        try:
            sections = sections.filter(id=int(id_section))
        except ValueError:
            sections = sections.none()

    if name:
        sections = sections.filter(name__icontains=name)

    if description:
        sections = sections.filter(description__icontains=description)

    return render(request, 'sections.html', {'sections': sections})

# --- صفحة التقارير
@login_required
def reports_page(request):
    if not request.user.is_staff:
        return redirect('login')
    return render(request, 'reports.html')


# --- صفحة تفاصيل الطالب
@login_required
def student_detail(request, student_id):
    if not request.user.is_staff:
        return redirect('login')

    student = get_object_or_404(Student, id_student=student_id)
    sections = Section.objects.all()

    # حفظ تعديل البيانات الشخصية أو الدرجات
    if request.method == 'POST':
        student.name = request.POST.get('name', student.name)
        section_id = request.POST.get('section')
        student.section = Section.objects.get(id=section_id) if section_id else student.section
        student.email = request.POST.get('email', student.email)
        student.save()

        for key, value in request.POST.items():
            if key.startswith('grade_'):
                enrollment_id = key.split('_')[1]
                try:
                    enrollment = Enrollment.objects.get(id=enrollment_id)
                    enrollment.grade = float(value) if value else None
                    enrollment.save()
                except Enrollment.DoesNotExist:
                    pass
        return redirect('student_detail', student_id=student.id_student)

    # جلب جميع التنزيلات للطالب
    enrollments = Enrollment.objects.filter(student=student).select_related('material').order_by('year', 'semester')

    # تنظيم المواد حسب السمستر
    semesters = {}
    for e in enrollments:
        sem_name = f"{e.semester} ({e.year})"
        if sem_name not in semesters:
            semesters[sem_name] = []
        semesters[sem_name].append(e)

    # حساب المعدل لكل سمستر والمعدل التراكمي
    semester_gpa = {}
    total_points = 0
    total_hours = 0
    for sem, courses in semesters.items():
        sem_points = sum([c.grade * c.material.hours for c in courses if c.grade is not None])
        sem_hours = sum([c.material.hours for c in courses if c.grade is not None])
        semester_gpa[sem] = round(sem_points / sem_hours, 2) if sem_hours > 0 else 0
        total_points += sem_points
        total_hours += sem_hours

    cumulative_gpa = round(total_points / total_hours, 2) if total_hours > 0 else 0

    context = {
        'student': student,
        'sections': sections,
        'semesters': semesters,
        'semester_gpa': semester_gpa,
        'cumulative_gpa': cumulative_gpa
    }

    return render(request, 'student_detail.html', context)


@login_required
def add_student(request):
    sections = Section.objects.all()
    if request.method == 'POST':
        id_student = request.POST.get('id_student')
        name = request.POST.get('name')
        section_id = request.POST.get('section')
        email = request.POST.get('email')
        password = request.POST.get('password')

        section = Section.objects.get(id=section_id)
        Student.objects.create(
            id_student=id_student,
            name=name,
            section=section,
            email=email,
            password=password
        )
        return redirect('students_page')

    return render(request, 'student_add.html', {'sections': sections})





def add_section(request):
    if request.method == "POST":
        section_id = request.POST.get("id")
        name = request.POST.get("name")
        
        if section_id and name:
            Section.objects.create(id=section_id, name=name)
            return redirect('sections_page') 
    return render(request, 'add_section.html')  



def add_material_page(request):
    if not request.user.is_staff:
        return redirect('login')

    sections = Section.objects.all()
    field_errors = {}  # لتخزين الأخطاء الخاصة بكل حقل

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        section_id = request.POST.get('section')
        hours = request.POST.get('hours', '').strip()
        description = request.POST.get('description', '').strip()

        # التحقق من الحقول الفارغة
        if not code:
            field_errors['code'] = " يرجى إدخال رمز المادة"
        elif Material.objects.filter(code=code).exists():
            field_errors['code'] = " رمز المادة موجود مسبقًا"

        if not name:
            field_errors['name'] = " يرجى إدخال اسم المادة"

        if not section_id:
            field_errors['section'] = " يرجى اختيار القسم"

        if not hours:
            field_errors['hours'] = " يرجى إدخال عدد الساعات"

        # إذا فيه أخطاء
        if field_errors:
            return render(request, 'add_material.html', {
                'sections': sections,
                'field_errors': field_errors,
                'form_data': request.POST
            })

        # إنشاء المادة الجديدة
        section = Section.objects.get(id=section_id)
        Material.objects.create(
            code=code,
            name=name,
            section=section,
            hours=hours or 0,
            description=description
        )

        messages.success(request, f"تمت إضافة المادة ({name}) بنجاح ✅")
        return redirect('materials_page')

    return render(request, 'add_material.html', {'sections': sections})



def edit_section(request, id):
    section = get_object_or_404(Section, pk=id)

    if request.method == 'POST':
        new_id = request.POST.get('id')
        name = request.POST.get('name')

        # لو المستخدم غيّر رمز القسم
        if str(section.id) != new_id:
            # نتحقق إذا الرقم الجديد محجوز
            if Section.objects.filter(pk=new_id).exclude(pk=section.id).exists():
                return render(request, 'section_detail.html', {
                    'section': section,
                    'error': ' رمز القسم موجود مسبقًا، يرجى اختيار رقم آخر.'
                })
            else:
                # نحذف القديم وننشئ الجديد بنفس البيانات (لأن الـ PK ما يتغير)
                Section.objects.filter(pk=section.id).delete()
                Section.objects.create(id=new_id, name=name, is_active=section.is_active)
                return redirect('sections_page')
        else:
            # تعديل الاسم فقط
            section.name = name
            section.save()
            return redirect('sections_page')

    return render(request, 'section_detail.html', {'section': section})




def material_detail(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    sections = Section.objects.all()
    field_errors = {}
    form_data = {}

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        section_id = request.POST.get("section", "")
        hours = request.POST.get("hours", "").strip()
        description = request.POST.get("description", "").strip()

        form_data = {"code": code, "name": name, "section": section_id, "hours": hours, "description": description}

        if Material.objects.exclude(id=material.id).filter(code=code).exists():
            field_errors["code"] = "رمز المادة موجود مسبقًا."
        if not name:
            field_errors["name"] = "اسم المادة مطلوب."

        if not field_errors:
            material.code = code
            material.name = name
            material.section_id = section_id if section_id else None
            material.hours = hours
            material.description = description
            material.save()
            return redirect("materials_page")

    return render(request, "material_detail.html", {
        "material": material,
        "sections": sections,
        "field_errors": field_errors,
        "form_data": form_data,
    })





@login_required
def grades_entry(request):
    # نجيب كل الطلاب اللي لهم سجلات رصد درجات
    students_with_grades = Student.objects.filter(grade_records__isnull=False).distinct()

    grade_data = []

    for student in students_with_grades:
        # نجيب السمسترات اللي رصد فيها الطالب درجاته
        semesters = GradeRecord.objects.filter(student=student)\
            .values_list('semester', flat=True).distinct()

        grade_data.append({
            'student': student,
            'semesters': semesters,
        })

    context = {
        'grade_data': grade_data
    }
    return render(request, 'grades_entry.html', context)


def add_grade_entry(request):
    student = None
    materials = []

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            # نجيب الطالب حسب رقم القيد
            student = Student.objects.get(id_student=student_id)
            # نجيب المواد اللي مسجلها الطالب
            materials = Enrollment.objects.filter(student=student)

            # لما المستخدم يحفظ الدرجات
            if 'save_grades' in request.POST:
                for enrollment in materials:
                    grade_value = request.POST.get(f'grade_{enrollment.id}')
                    if grade_value:
                        grade_value = float(grade_value)

                        GradeRecord.objects.update_or_create(
                            student=student,
                            material=enrollment.material,
                            semester=enrollment.semester,
                            year=enrollment.year,
                            defaults={'grade': grade_value}
                        )

                messages.success(request, "تم حفظ الدرجات وحساب المعدلات بنجاح ✅")
                return redirect('add_grade_entry')

        except Student.DoesNotExist:
            messages.error(request, "رقم القيد غير موجود ❌")
            student = None
            materials = []

    context = {
        'student': student,
        'materials': materials
    }
    return render(request, 'add_grade_entry.html', context)


def procedures_page(request):
    return render(request, 'Procedures.html')



@login_required
def materials_download_page(request):
    if not request.user.is_staff:
        return redirect('login')

    # جلب كل التنزيلات
    # نرتبها حسب الطالب والسمستر والسنة
    enrollments = Enrollment.objects.select_related('student', 'material').order_by('student__id_student', 'year', 'semester')

    # تنظيم البيانات: لكل طالب نعرض السمستر والسنة وعدد المواد
    downloads = {}
    for e in enrollments:
        key = (e.student.id_student, e.semester, e.year)
        if key not in downloads:
            downloads[key] = {
                'student': e.student,
                'semester': e.semester,
                'year': e.year,
                'materials_count': 0
            }
        downloads[key]['materials_count'] += 1

    context = {
        'downloads': downloads.values()
    }

    return render(request, 'materials_download.html', context)




@login_required
def student_material_download(request):
    student = None
    materials = Material.objects.all()

    # البحث عن الطالب
    student_id = request.GET.get('student_id')
    if student_id:
        student = get_object_or_404(Student, id_student=student_id)

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student, id_student=student_id)
        selected_materials = request.POST.getlist('materials')

        today = datetime.today().date()  # التاريخ الكامل
        current_year = today.year
        current_month = today.month

        for material_id in selected_materials:
            material = Material.objects.get(id=material_id)

            # تحقق إذا الطالب لم ينزل المادة في نفس الشهر
            exists = Enrollment.objects.filter(
                student=student,
                material=material,
                date_registered__year=current_year,
                date_registered__month=current_month
            ).exists()

            if not exists:
                Enrollment.objects.create(
                    student=student,
                    material=material,
                    semester=f"{current_month}/{current_year}",  # يمكنك تعديل الصياغة حسب رغبتك
                    year=current_year,
                    date_registered=today
                )

    return render(request, 'student_material_download.html', {
        'student': student,
        'materials': materials,
        'now': datetime.today(),
    })




def edit_student_downloads(request):
    student = None
    materials = Material.objects.all()
    enrollments = []

    # جلب الطالب
    student_id = request.GET.get('student_id')
    if student_id:
        student = get_object_or_404(Student, id_student=student_id)
        enrollments = Enrollment.objects.filter(student=student)

    # تنزيل مواد جديدة
    if request.method == 'POST' and 'download_materials' in request.POST:
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student, id_student=student_id)
        selected_materials = request.POST.getlist('materials')

        today = datetime.today().date()
        current_year = today.year
        current_month = today.month

        for material_id in selected_materials:
            material = Material.objects.get(id=material_id)

            # منع تنزيل نفس المادة أكثر من مرة في نفس الشهر
            exists = Enrollment.objects.filter(
                student=student,
                material=material,
                date_registered__year=current_year,
                date_registered__month=current_month
            ).exists()

            if not exists:
                Enrollment.objects.create(
                    student=student,
                    material=material,
                    semester=f"{current_month}/{current_year}",
                    year=current_year,
                    date_registered=today
                )
        return redirect(f"{request.path}?student_id={student.id_student}")

    # حذف مادة
    if request.method == 'POST' and 'delete_enrollment' in request.POST:
        enrollment_id = request.POST.get('enrollment_id')
        enrollment = Enrollment.objects.get(id=enrollment_id)
        enrollment.delete()
        return redirect(f"{request.path}?student_id={student.id_student}")

    return render(request, 'edit_student_downloads.html', {
        'student': student,
        'materials': materials,
        'enrollments': enrollments,
        'now': datetime.today()
    })



@login_required
def manage_material_prerequisites(request):
    if not request.user.is_staff:
        return redirect('login')

    all_materials = Material.objects.all()
    all_material_names = list(all_materials.values_list('name', flat=True))

    if request.method == 'POST':
        material_names = request.POST.getlist('material_name[]')
        prerequisites_lists = request.POST.getlist('prerequisites[]')

        for mat_name, prereq_name in zip(material_names, prerequisites_lists):
            mat_name = mat_name.strip()
            prereq_name = prereq_name.strip()

            if not mat_name:
                continue

            try:
                material = Material.objects.get(name=mat_name)
            except Material.DoesNotExist:
                continue

            # نحذف الأسبقيات القديمة لنفس المادة
            MaterialPrerequisite.objects.filter(material=material).delete()

            if prereq_name == "" or prereq_name == "لا يوجد":
                MaterialPrerequisite.objects.create(material=material, prerequisite=None)
            else:
                try:
                    prereq_material = Material.objects.get(name=prereq_name)
                    if prereq_material != material:
                        MaterialPrerequisite.objects.create(material=material, prerequisite=prereq_material)
                except Material.DoesNotExist:
                    continue

        messages.success(request, "✅ تم حفظ أسبقيات المواد بنجاح!")
        return redirect('manage_material_prerequisites')

    # 🔹 بعد الحفظ أو عند الدخول، نعرض البيانات الحالية
    prerequisites_data = []
    for p in MaterialPrerequisite.objects.select_related('material', 'prerequisite'):
        prerequisites_data.append({
            'material': p.material.name,
            'prerequisite': p.prerequisite.name if p.prerequisite else "لا يوجد"
        })

    context = {
        'all_material_names': all_material_names,
        'prerequisites_data': prerequisites_data
    }
    return render(request, 'manage_material_prerequisites.html', context)




@login_required
def timetable_page(request):
    lectures = Lecture.objects.select_related('material').all()
    lectures = sorted(lectures, key=lambda x: (x.time, x.day))

    materials = Material.objects.all()  # جلب جميع المواد

    time_slots = [0, 1, 2, 3, 4]
    days = [1, 2, 3, 4, 5, 6]

    context = {
        'lectures': lectures,
        'colors': ["#ef4444","#3b82f6","#10b981","#f59e0b","#6366f1","#06b6d4","#8b5cf6"],
        'rows': time_slots,
        'days': days,
        'materials': materials,  # إرسال المواد للـ template
    }
    return render(request, 'timetable.html', context)



@csrf_exempt
def save_lecture(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lecture_id = data.get("id")
            material_id = data.get("material_id")  # استلمنا id المادة
            group = data.get("group")
            room = data.get("room")
            day = int(data.get("day"))
            time = int(data.get("time"))

            material = Material.objects.get(id=material_id)  # جلب المادة من قاعدة البيانات

            if lecture_id and int(lecture_id) > 0:
                lecture = Lecture.objects.get(id=lecture_id)
                lecture.material = material
                lecture.group = group
                lecture.room = room
                lecture.day = day
                lecture.time = time
                lecture.save()
            else:
                Lecture.objects.create(
                    material=material,
                    group=group,
                    room=room,
                    day=day,
                    time=time
                )
            return JsonResponse({"success": True})
        except Exception as e:
            print(e)
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False})