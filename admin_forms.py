from flask_wtf import FlaskForm

class AdminForm(FlaskForm):
    """Flask-WTF CSRF plus Flask-Admin's object-aware uniqueness validation."""
    def __init__(self,formdata=None,obj=None,prefix='',**kwargs):
        self._obj=obj
        super().__init__(formdata=formdata,obj=obj,prefix=prefix,**kwargs)
