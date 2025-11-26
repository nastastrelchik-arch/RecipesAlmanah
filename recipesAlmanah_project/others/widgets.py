from django import forms


class MultipleFileInput(forms.Widget):
    template_name = 'widgets/multiple_file_input.html'

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        value = files.get(name)
        if value:
            return [value]
        return []

    def value_omitted_from_data(self, data, files, name):
        return name not in files