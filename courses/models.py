from django.db import models
from django.utils import timezone

# جدول الأقسام
class Section(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sections'

    def __str__(self):
        return self.name


# جدول الطلاب
class Student(models.Model):
    id_student = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='students')
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.id_student})"


# جدول المواد
class Material(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    hours = models.IntegerField(default=3)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'materials'
        verbose_name = "مادة"
        verbose_name_plural = "المواد"

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_prerequisites(self):
        """ترجع كل المواد المطلوبة قبل هذه المادة"""
        return Material.objects.filter(is_prerequisite_of__material=self)


# تنزيل المواد (Enrollment)
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.CharField(max_length=20, null=True, blank=True)  # مثال: "السمستر الأول"
    year = models.CharField(max_length=10, null=True, blank=True)      # مثال: "2025"
    date_registered = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'enrollments'
        verbose_name = "تنزيل مادة"
        verbose_name_plural = "تنزيل المواد"
        unique_together = ('student', 'material', 'semester', 'year')

    def __str__(self):
        return f"{self.student.name} - {self.material.name} ({self.semester} {self.year})"
    




class GradeRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grade_records')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='grade_records')
    semester = models.CharField(max_length=20, null=True, blank=True)  # مثال: "السمستر الأول"
    year = models.CharField(max_length=10, null=True, blank=True)      # مثال: "2025"

    grade = models.FloatField(null=True, blank=True)                  # درجة المادة النهائية
    semester_gpa = models.FloatField(null=True, blank=True)           # معدل السمستر الحالي
    cumulative_gpa = models.FloatField(null=True, blank=True)         # المعدل التراكمي حتى الآن

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grade_records'
        verbose_name = "رصد درجة"
        verbose_name_plural = "رصد الدرجات"
        unique_together = ('student', 'material', 'semester', 'year')

    def __str__(self):
        return f"{self.student.name} - {self.material.name} ({self.semester} {self.year})"

    def save(self, *args, **kwargs):
        """
        نحسب المعدل الفصلي والمعدل التراكمي تلقائيًا
        """
        super().save(*args, **kwargs)

        # بعد حفظ الدرجة نحسب المعدلات
        self.update_gpas()

    def update_gpas(self):
        from django.db.models import Avg

        # نحسب معدل السمستر الحالي
        semester_avg = GradeRecord.objects.filter(
            student=self.student,
            semester=self.semester,
            year=self.year
        ).aggregate(Avg('grade'))['grade__avg'] or 0

        # نحسب المعدل التراكمي لكل الفصول السابقة
        cumulative_avg = GradeRecord.objects.filter(
            student=self.student
        ).aggregate(Avg('grade'))['grade__avg'] or 0

        # نحفظهم
        GradeRecord.objects.filter(pk=self.pk).update(
            semester_gpa=round(semester_avg, 2),
            cumulative_gpa=round(cumulative_avg, 2)
        )




class MaterialPrerequisite(models.Model):
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='prerequisites_for',
    )
    prerequisite = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='is_prerequisite_of',
        null=True, blank=True  # <=== السماح بعدم وجود أسبقية
    )

    class Meta:
        db_table = 'material_prerequisites'
        unique_together = ('material', 'prerequisite')
        verbose_name = "أسبقية مادة"
        verbose_name_plural = "أسبقيات المواد"

    def __str__(self):
        if self.prerequisite:
            return f"{self.prerequisite.name} → {self.material.name}"
        return f"لا توجد أسبقية → {self.material.name}"
    






class Lecture(models.Model):
    material = models.ForeignKey(
        'Material',
        on_delete=models.CASCADE,
        related_name='lectures',
        verbose_name="المادة"
    )
    group = models.CharField(max_length=50, verbose_name="المجموعة")
    room = models.CharField(max_length=50, verbose_name="القاعة")
    
    # اليوم: 1=السبت ... 6=الخميس
    day = models.PositiveSmallIntegerField(choices=[
        (1, 'السبت'),
        (2, 'الأحد'),
        (3, 'الاثنين'),
        (4, 'الثلاثاء'),
        (5, 'الأربعاء'),
        (6, 'الخميس')
    ], verbose_name="اليوم")
    
    # الوقت: 0=08-10 ... 4=16-18
    time = models.PositiveSmallIntegerField(choices=[
        (0, '08:00 - 10:00'),
        (1, '10:00 - 12:00'),
        (2, '12:00 - 14:00'),
        (3, '14:00 - 16:00'),
        (4, '16:00 - 18:00')
    ], verbose_name="الوقت")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lectures'
        verbose_name = "محاضرة"
        verbose_name_plural = "المحاضرات"
        unique_together = ('material', 'group', 'day', 'time')  # منع ازدواجية المحاضرة لنفس الوقت والمجموعة

    def __str__(self):
        return f"{self.material.name} - مجموعة {self.group} ({self.get_day_display()} {self.get_time_display()})"