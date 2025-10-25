from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')

def admin_dashbord(request):  
    return render(request, 'admin_dashbord.html')

def materials_page(request):
    return render(request, 'materials.html')

def students_page(request):
    return render(request, 'students.html')

def sections_page(request):
    return render(request, 'sections.html')

def reports_page(request):
    return render(request, 'reports.html')