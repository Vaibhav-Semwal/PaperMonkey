from django import forms
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import QuestionBank, Papers, PaperQuestion


class UserRegisterForm(UserCreationForm):
	email = forms.EmailField()
	user_type = forms.ChoiceField(initial=2,choices=( 
		(1,'Student'),
		(2,'Teacher')
    ))

	class Meta:
		model = get_user_model()
		fields = ['username','user_type', 'email', 'password1', 'password2']



class PaperCreationForm(forms.Form): 
	paper_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Enter paper name'})
    )
    
	topics = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Enter topics'})
    )
    
	external_links = forms.CharField(
        widget = forms.Textarea(attrs={
            'placeholder': 'Paste one link per line',
            'rows': 4,
        }),
        help_text="Enter one URL per line."
    )

	count = forms.IntegerField(
		initial= 1,
        min_value=1,
        max_value=5,
        label="Number of Sections (max 5)",
        widget=forms.NumberInput(attrs={"id": "id_count"}),
    )

	def __init__(self, *args, num_fields=0, **kwargs):
		super().__init__(*args, **kwargs)
		# Create one IntegerField per requested slot
		for i in range(1, num_fields + 1):
			self.fields[f"value_{i}"] = forms.IntegerField( label=f"Number {i}",widget=forms.NumberInput(attrs={"class": "value-field"}))

	def save(self, json_data, creator_name, paper_name, section_plan=None):
		paper = Papers.objects.create(
			creator_name = creator_name,
			paper_name = paper_name
		)
		_get_question_list(json_data, paper, section_plan or {})
		return paper

	def clear_sections_dict(self):
		cleaned = getattr(self, "value", {})
		print(f"cleaned list: {cleaned.items()}")
		return {
			int(name.split("_")[1]): value
			for name, value in cleaned.items() if name.startswith(f"value")
		}
      
	def clear_external_links(self):
		raw = self.cleaned_data['external_links']
		links = [line.strip() for line in raw.splitlines() if line.strip()]
	
		url_validator = URLValidator()
		for link in links:
			try:
				url_validator(link)
			except forms.ValidationError:
				raise forms.ValidationError(f"'{link}' is not a valid URL.")

		print("links:", links)	
		return links

#region HELPER FUNCTION

def _get_question_list(json_data: dict, paper_model, section_plan: dict):
	for index, section in enumerate(json_data.get("sections", []), start=1):
		section_number = _coerce_int(section.get("section_number"), index)

		# The teacher's requested marks-per-question for this section, used as a
		# fallback when the model omits a per-question "marks" value.
		plan = section_plan.get(section_number)
		default_marks = _coerce_int(plan[1], 0) if plan else 0

		for question_data in section.get("questions", []):
			_paper_question_save({
				"ques_obj": _question_bank_save(question_data),
				"marks": _coerce_int(question_data.get("marks"), default_marks) or default_marks,
				"section": section_number,
				"difficulty": PaperQuestion.Difficulty.from_label(str(question_data.get("difficulty", ""))),
				"paper": paper_model,
			})


def _question_bank_save(data):
	print(f"[FORM DEBUG] created question: {data}")
	return QuestionBank.objects.create(
		question = data.get("question", ""),
		answer = data.get("answer", "")
	)

def _paper_question_save(data):
	print(f"[FORM DEBUG] created paper question: {data}")
	return PaperQuestion.objects.create(
		question = data.get("ques_obj"),
		marks = _coerce_int(data.get("marks"), 0),
		section = _coerce_int(data.get("section"), 1),
		difficulty = data.get("difficulty", PaperQuestion.Difficulty.UNKNOWN),
		paper = data.get("paper"),
	)

def _coerce_int(raw, fallback):
	"""Best-effort int() that tolerates strings/None/floats from the model JSON."""
	try:
		return int(float(raw))
	except (TypeError, ValueError):
		return fallback

#endregion