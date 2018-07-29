import markdown

from markdown.extensions.toc import TocExtension

from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.utils.text import slugify
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.contrib import messages

from comments.forms import CommentForm
from .models import Post, Category, Tag

from .forms import ContactForm

"""
def index(request):
    return HttpResponse("welcome")
"""

"""

def index(request):
    return render(request, 'blog/index.html', context={
        'title': 'my home',
        'welcome': 'welcome'
    })
"""


def index(request):
    post_list = Post.objects.all()
    return render(request, 'blog/index.html', context={'post_list': post_list})


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """
            """


        context = super(IndexView, self).get_context_data(**kwargs)


        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')


        pagination_data = self.pagination_data(paginator, page, is_paginated)


        context.update(pagination_data)


        return context

    def pagination_data(self, paginator, page, is_paginated):
        if not is_paginated:

            return {}


        left = []


        right = []


        left_has_more = False


        right_has_more = False


        first = False


        last = False


        page_number = page.number


        total_pages = paginator.num_pages


        page_range = paginator.page_range

        if page_number == 1:

            right = page_range[page_number:page_number + 2]


            if right[-1] < total_pages - 1:
                right_has_more = True


            if right[-1] < total_pages:
                last = True

        elif page_number == total_pages:

            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]


            if left[0] > 2:
                left_has_more = True


            if left[0] > 1:
                first = True
        else:

            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            right = page_range[page_number:page_number + 2]


            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True


            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True

        data = {
            'left': left,
            'right': right,
            'left_has_more': left_has_more,
            'right_has_more': right_has_more,
            'first': first,
            'last': last,
        }

        return data


"""

def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])
    return render(request, 'blog/detail.html', context={'post': post})
"""


def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)


    post.increase_views()

    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])

    form = CommentForm()

    comment_list = post.comment_set.all()


    context = {'post': post,
               'form': form,
               'comment_list': comment_list
               }
    return render(request, 'blog/detail.html', context=context)



class PostDetailView(DetailView):

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):

        response = super(PostDetailView, self).get(request, *args, **kwargs)


        self.object.increase_views()


        return response

    def get_object(self, queryset=None):

        post = super(PostDetailView, self).get_object(queryset=None)
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            TocExtension(slugify=slugify),
        ])
        post.body = md.convert(post.body)
        post.toc = md.toc
        return post

    def get_context_data(self, **kwargs):

        context = super(PostDetailView, self).get_context_data(**kwargs)
        form = CommentForm()
        comment_list = self.object.comment_set.all()
        context.update({
            'form': form,
            'comment_list': comment_list
        })
        return context


def archives(request, year, month):
    post_list = Post.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    )
    return render(request, 'blog/index.html', context={'post_list': post_list})


class ArchivesView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return super(ArchivesView, self).get_queryset().filter(created_time__year=year,
                                                               created_time__month=month
                                                               )


def category(request, pk):
    cate = get_object_or_404(Category, pk=pk)
    post_list = Post.objects.filter(category=cate)
    return render(request, 'blog/index.html', context={'post_list': post_list})


class CategoryView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super(CategoryView, self).get_queryset().filter(category=cate)


class TagView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super(TagView, self).get_queryset().filter(tags=tag)
    
def aboutUs(request):
    return render(request, 'blog/about.html')


def contact(request):
    form_class = ContactForm


    if request.method == 'POST':
        form = form_class(data=request.POST)

        if form.is_valid():
            contact_name = request.POST.get(
                'contact_name'
            , '')
            contact_email = request.POST.get(
                'contact_email'
            , '')
            form_content = request.POST.get('content', '')

            # Add contact information in email
            template = get_template('blog/contact_template.txt')
            context = {
                'contact_name': contact_name,
                'contact_email': contact_email,
                'form_content': form_content,
            }
            content = template.render(context)

            email = EmailMessage(
                "New contact form submission",
                content,
                "Your website" +'',
                ['youremail@gmail.com'],
                headers = {'Reply-To': contact_email }
            )
            email.send()
            
            messages.success(request, 'Your message has been sent to us!') 
            
            return redirect('blog:contact')
        else:
            messages.warning(request, 'Your message is not valid. Please try again.')
            
    return render(request, 'blog/contact.html', {
        'form': form_class,
    })


"""
def search(request):
    q = request.GET.get('q')
    error_msg = ''
    if not q:
        error_msg = "input key word"
        return render(request, 'blog/index.html', {'error_msg': error_msg})
    post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    return render(request, 'blog/index.html', {'error_msg': error_msg,
                                               'post_list': post_list})
"""
