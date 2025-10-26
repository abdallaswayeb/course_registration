from django.db import models

# Create your models here.


class Student(models.Model):
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	student_id = models.CharField(max_length=32, unique=True)
	department = models.CharField(max_length=100, null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		# Store student records in a dedicated table separate from auth_user
		db_table = 'auth_students'

	def __str__(self):
		return f"{self.first_name} {self.last_name} ({self.student_id})"
