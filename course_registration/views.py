from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from courses.models import Student


def signup_view(request):
    # Public signup: creates Student and Django User (if password provided)
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if student_id and first_name and last_name and email:
            student, created = Student.objects.get_or_create(
                student_id=student_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if not created:
                student.first_name = first_name
                student.last_name = last_name
                student.email = email
                student.save()

            if password and not User.objects.filter(username=student_id).exists():
                User.objects.create_user(username=student_id, password=password, email=email,
                                         first_name=first_name, last_name=last_name)

            # after signup, redirect to login so user can sign in
            return redirect('login')

    return render(request, 'signup.html')


def root_redirect(request):
    # If user is authenticated, go to dashboard, otherwise go to login
    if request.user.is_authenticated:
        return redirect('admin_dashbord')
    return redirect('login')


def login_view(request):
    # Login form expects 'student_id' and 'password'
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        password = request.POST.get('password')
        user = authenticate(request, username=student_id, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashbord')
        # Invalid credentials - re-render with an error
        return render(request, 'login.html', {'error': 'بيانات الدخول غير صحيحة'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def admin_dashbord(request):
    return render(request, 'admin_dashbord.html')


@login_required
def materials_page(request):
    return render(request, 'materials.html')


@login_required
def students_page(request):
    # Handle POST to create a student (front-end form submits to this same URL)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        student_id = request.POST.get('student_id')
        password = request.POST.get('password')

        if student_id and first_name and last_name and email:
            # Create Student record if not exists
            student, created = Student.objects.get_or_create(
                student_id=student_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if not created:
                # update fields if student already exists
                student.first_name = first_name
                student.last_name = last_name
                student.email = email
                student.save()

            # Optionally create a Django User for authentication if password provided
            if password:
                if not User.objects.filter(username=student_id).exists():
                    User.objects.create_user(username=student_id, password=password, email=email,
                                             first_name=first_name, last_name=last_name)

        return redirect('students_page')

    # Show students from the auth_user table (non-staff, non-superuser users)
    auth_users = User.objects.filter(is_staff=False, is_superuser=False).order_by('-date_joined')

    # Normalize auth users to the shape the template expects (student_id, first_name, last_name, section)
    students = []
    for u in auth_users:
        students.append({
            'student_id': u.username,
            'first_name': u.first_name or '',
            'last_name': u.last_name or '',
            'section': None,
        })

    return render(request, 'students.html', {'students': students})


@login_required
def sections_page(request):
    return render(request, 'sections.html')


@login_required
def reports_page(request):
    return render(request, 'reports.html')