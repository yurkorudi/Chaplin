class SessionView(ModelView):
    form_columns = [
        'film',     
        'cinema',      
        'hall',       
        'session_datetime',
        'session_duration'
    ]
    column_list = form_columns

    form_args = {
        'film': {
            'query_factory': lambda: Film.query.all(),
            'get_label': 'name'
        },
        'cinema': {
            'query_factory': lambda: Cinema.query.all(),
            'get_label': 'name'
        },
        'hall': {
            'query_factory': lambda: Hall.query.all(),
            'get_label': lambda h: f"{h.name} ({h.cinema.name})"
        }
    }
    form_ajax_refs = {
        'film':   {'fields': ['name']},
        'cinema': {'fields': ['name']},
        'hall':   {'fields': ['name']}
    }