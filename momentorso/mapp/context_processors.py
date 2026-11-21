from .models import Story

def stories_context(request):
    """
    Context processor to make currently active stories available in frontend templates.
    A story is active if it is published (or scheduled past its schedule time) and
    its 24-hour expiration window has not passed.
    """
    try:
        active_stories = Story.get_active_stories()
    except Exception:
        active_stories = []
    return {
        'active_stories': active_stories
    }
