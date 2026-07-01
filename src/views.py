from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from .forms import UserRegisterForm, PaperCreationForm
from .models import Users, Papers, PaperQuestion
from .llm import create, process_query
from asgiref.sync import async_to_sync

# or wrap your own helper:

# Create your views here.

class Index(TemplateView):
    template_name = 'index.html'

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        user_info = request.user
        is_teacher = user_info.account_type == user_info.AccountType.TEACHER
        items = user_info.saved_papers.all() if is_teacher else Papers.objects.all()

        print(user_info)

        return render(request, 'dashboard.html', {'items': items[:20],'is_teacher': is_teacher})

class PaperCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = PaperCreationForm()
        return render(request, 'teacher/add_item.html', {'form':form})

    def post(self, request):
        form = PaperCreationForm(request.POST)
        if form.is_valid() :

            sections = {
                count + 1: [int(value), int(marks)]
                for count, (value, marks) in enumerate(zip(request.POST.getlist(f'value'), request.POST.getlist(f'marks_value')))
    		}
            links = form.clear_external_links()
            user = request.user

            result = async_to_sync(create)(links)
            json_info = process_query(result, form.cleaned_data['topics'] , sections)

            if json_info:
                paper = form.save(json_info, user.username, form.cleaned_data['paper_name'], sections)
                # Show the saved paper so the user can edit every detail.
                return redirect("edit_paper", pk=paper.pk)

            form.add_error(None, "Could not generate any questions from the provided links.")

        return render(request, 'teacher/add_item.html', {'form':form})

class EditPaperView(View):
    template_name = "teacher/edit_paper.html"

    def get(self, request, pk):
        paper = get_object_or_404(Papers.objects.prefetch_related("questions__question"), pk=pk)
        print(paper)
        return render(request, self.template_name, {"paper": paper})

    def post(self, request, pk):
        paper = get_object_or_404(Papers.objects.prefetch_related("questions__question"), pk=pk)
        paper.paper_name = request.POST.get("paper_name", paper.paper_name)
        paper.save()

        for pq in paper.questions.all():
            pq.section = int(request.POST.get(f"section_{pq.id}", pq.section))
            pq.marks = int(request.POST.get(f"marks_{pq.id}", pq.marks))
            pq.difficulty = PaperQuestion.Difficulty.from_label(
                request.POST.get(f"difficulty_{pq.id}", pq.get_difficulty_display())
            )
            pq.save()

            # Question text and answer live on the related QuestionBank row.
            bank = pq.question
            bank.question = request.POST.get(f"question_{pq.id}", bank.question)
            bank.answer = request.POST.get(f"answer_{pq.id}", bank.answer)
            bank.save()

        return redirect("edit_paper", pk=paper.pk)

class LogInView(LoginView): 
    def form_valid(self, form):
        _try_get_user(form.cleaned_data['username'])
        return super().form_valid(form)


class SignUpView(View):
    template_name = "auth/signup.html"

    def get(self, request):
        return render(request, self.template_name, {"form": UserRegisterForm()})

    def post(self, request):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return redirect("index")

        return render(request, self.template_name, {
            "form": form
        })
    
#region HELPER FUNCTIONS

def _try_get_user(_username: str = "", _account_type: int = 1):
    user, created = Users.objects.get_or_create(
        username = _username,
        defaults = {
            "username": _username,
            "account_type": Users.AccountType(_account_type),
            "preferences": {},
        })
    print(created, user)
    return user

#endregion