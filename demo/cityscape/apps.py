from moose.apps import AppConfig

# from cityscape import actions

class CityscapeConfig(AppConfig):
    name = 'cityscape'

    def ready(self):
        self.register('Upload', 'upload', default=True)
        self.register('Export', 'export')
